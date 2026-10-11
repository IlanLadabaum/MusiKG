"""Resumable Discogs release/track credit pilot using only CC0 fields.

The API response is not retained wholesale. Selected CC0 release facts, track
lists and credits are kept with their original release or track scope. A search
result or matching track title is not a verified recording match.
"""

import argparse
import csv
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN = ROOT / "tmp" / "benchmark-name-artist-full"
API = "https://api.discogs.com"


def now():
    return datetime.now(timezone.utc).isoformat()


def append(path, item):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")


def done_ids(path):
    if not path.exists():
        return set()
    return {json.loads(line)["candidate_id"] for line in path.read_text().splitlines() if line}


def norm(value):
    value = unicodedata.normalize("NFKD", str(value).casefold())
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        c for c in value if not unicodedata.combining(c))))


def similar(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


class Client:
    def __init__(self, contact, log_path, spacing=2.8):
        self.ua = f"MusiKGResearch/0.1 (+{contact})"
        self.log_path = log_path
        self.spacing = spacing
        self.last_start = 0.0

    def get(self, candidate_id, phase, url):
        for attempt in range(4):
            wait = max(0, self.spacing - (time.monotonic() - self.last_start))
            if wait:
                time.sleep(wait)
            self.last_start = time.monotonic()
            started, tick = now(), time.perf_counter()
            code, error, payload, data = None, "", b"", None
            try:
                with urlopen(Request(url, headers={"User-Agent": self.ua,
                                                   "Accept": "application/json"}), timeout=30) as response:
                    code = response.status
                    payload = response.read()
                    remaining = response.headers.get("X-Discogs-Ratelimit-Remaining")
                data = json.loads(payload)
            except HTTPError as exc:
                code, error = exc.code, f"HTTP {exc.code}: {exc.reason}"
                remaining = exc.headers.get("X-Discogs-Ratelimit-Remaining")
            except (URLError, TimeoutError, ValueError, OSError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                remaining = None
            append(self.log_path, {
                "candidate_id": candidate_id, "route": "discogs_api",
                "lookup_mode": "title_artist", "phase": phase, "url": url,
                "start_utc": started, "end_utc": now(),
                "elapsed_s": round(time.perf_counter() - tick, 3),
                "rate_wait_s": round(wait, 3), "attempt": attempt + 1,
                "status": "ok" if data is not None else "error",
                "http_status": code, "rate_remaining": remaining,
                "bytes": len(payload), "response_received": bool(payload),
                "raw_retained": False, "extracted_cc0_fields_retained": data is not None,
                "error": error,
            })
            if data is not None:
                return data
            if code not in (429, 500, 502, 503, 504) and code is not None:
                break
            if attempt < 3:
                time.sleep(60 if code == 429 else 5 * (attempt + 1))
        return None


def credit(item):
    return {key: item.get(key) for key in ("id", "name", "anv", "role", "tracks")
            if item.get(key) is not None}


def release_cc0(data):
    return {
        "id": data.get("id"), "title": data.get("title"),
        "year": data.get("year"), "released": data.get("released"),
        "country": data.get("country"), "uri": data.get("uri"),
        "artists": [credit(x) for x in data.get("artists", [])],
        "extraartists": [credit(x) for x in data.get("extraartists", [])],
        "labels": [{key: x.get(key) for key in ("id", "name", "catno") if x.get(key) is not None}
                   for x in data.get("labels", [])],
        "companies": [{key: x.get(key) for key in ("id", "name", "entity_type_name")
                       if x.get(key) is not None} for x in data.get("companies", [])],
        "identifiers": [{key: x.get(key) for key in ("type", "value", "description")
                         if x.get(key) is not None} for x in data.get("identifiers", [])],
        "tracklist": [{
            "position": t.get("position"), "title": t.get("title"),
            "duration": t.get("duration"), "type_": t.get("type_"),
            "artists": [credit(x) for x in t.get("artists", [])],
            "extraartists": [credit(x) for x in t.get("extraartists", [])],
        } for t in data.get("tracklist", [])],
    }


def write_credit_claims(path, corpus_id, release, scope, subject, artists):
    for artist in artists:
        append(path, {
            "candidate_id": corpus_id, "route": "discogs_api",
            "release_id": release["id"], "source_url": release.get("uri") or
            f"https://www.discogs.com/release/{release['id']}",
            "source_scope": scope, "subject": subject,
            "raw_role": artist.get("role") or "main artist",
            "target_id": artist.get("id"), "target_name": artist.get("name"),
            "qualifiers": {"anv": artist.get("anv"), "tracks": artist.get("tracks")},
            "review_state": "unreviewed",
        })


def run(args):
    contact = os.environ.get("MUSICGRAPH_CONTACT", "").strip()
    if not contact.startswith("https://"):
        raise SystemExit("Set MUSICGRAPH_CONTACT to a public maintainer URL")
    run_dir = args.run_dir
    with (run_dir / "input.tsv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 500:
        raise SystemExit(f"Expected 500 frozen rows, found {len(rows)}")
    cc0_dir = run_dir / "extracted_cc0" / "discogs"
    cc0_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "discogs-results.jsonl"
    candidates_path = run_dir / "discogs-candidates.jsonl"
    claims_path = run_dir / "discogs-claims.jsonl"
    client = Client(contact, run_dir / "discogs-query-log.jsonl")
    done = done_ids(result_path)
    count = 0
    for row in rows:
        corpus_id = row["candidate_id"]
        if corpus_id in done:
            continue
        if args.limit and count >= args.limit:
            break
        url = API + "/database/search?" + urlencode({
            "track": row["title_hint"], "artist": row["artist_hint"],
            "type": "release", "per_page": 20,
        })
        search = client.get(corpus_id, "search", url)
        if search is None:
            append(result_path, {"candidate_id": corpus_id, "status": "search_error",
                                 "candidate_count": 0, "release_fetched": False})
            count += 1
            continue
        candidates = search.get("results", [])
        hint_year = int(row["year_hint"][:4]) if row["year_hint"][:4].isdigit() else None
        for rank, item in enumerate(candidates, 1):
            append(candidates_path, {
                "candidate_id": corpus_id, "route": "discogs_api",
                "lookup_mode": "title_artist", "rank": rank,
                "release_id": item.get("id"),
                "source_url": f"https://www.discogs.com/release/{item.get('id')}",
                "release_title": item.get("title"), "release_year": item.get("year"),
                "label": item.get("label"), "catno": item.get("catno"),
                "review_state": "unreviewed",
            })
        dated = [x for x in candidates if isinstance(x.get("year"), int)]
        if hint_year and dated:
            best = min(dated, key=lambda x: (abs(x["year"] - hint_year),
                                              x["year"] < hint_year))
        else:
            best = candidates[0] if candidates else None
        release = None
        if best and best.get("id"):
            detail = client.get(corpus_id, "release_lookup",
                                API + f"/releases/{best['id']}")
            if detail is not None:
                release = release_cc0(detail)
                (cc0_dir / f"{corpus_id}-release.json").write_text(
                    json.dumps(release, ensure_ascii=False), encoding="utf-8")
                write_credit_claims(claims_path, corpus_id, release, "release",
                                    release.get("title"), release.get("artists", []))
                write_credit_claims(claims_path, corpus_id, release, "release",
                                    release.get("title"), release.get("extraartists", []))
                for label in release.get("labels", []):
                    append(claims_path, {
                        "candidate_id": corpus_id, "route": "discogs_api",
                        "release_id": release["id"], "source_url": release.get("uri"),
                        "source_scope": "release", "subject": release.get("title"),
                        "raw_role": "label", "target_id": label.get("id"),
                        "target_name": label.get("name"), "qualifiers": {"catno": label.get("catno")},
                        "review_state": "unreviewed",
                    })
                for track in release.get("tracklist", []):
                    if similar(row["title_hint"], track.get("title") or "") < .75:
                        continue
                    subject = {"position": track.get("position"), "title": track.get("title")}
                    write_credit_claims(claims_path, corpus_id, release, "track_in_release",
                                        subject, track.get("artists", []))
                    write_credit_claims(claims_path, corpus_id, release, "track_in_release",
                                        subject, track.get("extraartists", []))
        append(result_path, {
            "candidate_id": corpus_id,
            "status": "retrieved" if candidates else "no_candidates",
            "candidate_count": len(candidates),
            "selected_release_id": best.get("id") if best else None,
            "release_fetched": release is not None,
            "matching_track_count": sum(similar(row["title_hint"], t.get("title") or "") >= .75
                                        for t in release.get("tracklist", [])) if release else 0,
            "review_state": "unreviewed",
        })
        count += 1
        if count % 10 == 0:
            print(f"Discogs processed {count} new rows; latest {corpus_id}", flush=True)
    print(f"Discogs complete: {count} new rows, {len(done_ids(result_path))} total", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--limit", type=int, default=0)
    run(parser.parse_args())
