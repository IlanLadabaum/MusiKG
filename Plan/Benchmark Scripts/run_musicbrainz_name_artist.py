"""Resumable artist/title MusicBrainz benchmark route.

Searches all frozen input rows without ISRCs or IDs from other sources. Search
candidates and a conservative best-candidate expansion remain UNREVIEWED; this
script never claims a correct recording match. Uses only MusicBrainz core data.
"""

import argparse
import csv
import hashlib
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
DEFAULT_RUN = ROOT / "tmp" / "benchmark-name-artist-20261010"
API = "https://musicbrainz.org/ws/2"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def artist_credit(recording: dict) -> str:
    return "".join(part if isinstance(part, str) else part.get("name", "")
                   for part in recording.get("artist-credit", []))


def write_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        return {json.loads(line)["candidate_id"] for line in handle if line.strip()}


class Client:
    def __init__(self, contact: str, log_path: Path, spacing: float = 1.2):
        self.user_agent = f"MusicGraphGeneratorResearch/0.1 ({contact})"
        self.log_path = log_path
        self.spacing = spacing
        self.last_start = 0.0

    def get(self, candidate_id: str, phase: str, url: str) -> dict | None:
        for attempt in range(4):
            wait = max(0.0, self.spacing - (time.monotonic() - self.last_start))
            if wait:
                time.sleep(wait)
            self.last_start = time.monotonic()
            start = time.perf_counter()
            started_utc = now()
            status = "error"
            code = None
            error = ""
            payload = b""
            try:
                request = Request(url, headers={"User-Agent": self.user_agent,
                                                "Accept": "application/json"})
                with urlopen(request, timeout=30) as response:
                    code = response.status
                    payload = response.read()
                data = json.loads(payload)
                status = "ok"
            except HTTPError as exc:
                code = exc.code
                error = f"HTTP {exc.code}: {exc.reason}"
                data = None
                if exc.code in (429, 503):
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(min(60, int(retry_after)) if retry_after and retry_after.isdigit()
                               else 5 * (attempt + 1))
            except (URLError, TimeoutError, ValueError, OSError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                data = None
                if attempt < 3:
                    time.sleep(3 * (attempt + 1))
            write_jsonl(self.log_path, {
                "candidate_id": candidate_id, "route": "musicbrainz_api",
                "lookup_mode": "title_artist", "phase": phase, "url": url,
                "start_utc": started_utc, "end_utc": now(),
                "elapsed_s": round(time.perf_counter() - start, 3),
                "rate_wait_s": round(wait, 3), "attempt": attempt + 1,
                "status": status, "http_status": code, "bytes": len(payload),
                "response_received": bool(payload), "raw_retained": status == "ok",
                "error": error,
            })
            if status == "ok":
                return data
            if code not in (429, 503) and attempt == 3:
                break
        return None


def flatten_relations(candidate_id: str, recording_id: str, item: dict,
                      subject_type: str, source_path: str, output: Path) -> None:
    subject_name = item.get("title") or item.get("name") or ""
    for relation in item.get("relations", []):
        target_type = relation.get("target-type", "")
        target = relation.get(target_type, {}) or {}
        write_jsonl(output, {
            "candidate_id": candidate_id, "route": "musicbrainz_api",
            "candidate_recording_id": recording_id,
            "subject_type": subject_type, "subject_id": item.get("id", ""),
            "subject_name": subject_name, "source_scope": subject_type,
            "raw_role": relation.get("type", ""),
            "direction": relation.get("direction", ""),
            "attributes": relation.get("attributes", []),
            "target_type": target_type, "target_id": target.get("id", ""),
            "target_name": target.get("name") or target.get("title") or "",
            "source_path": source_path, "review_state": "unreviewed",
        })


def run(args: argparse.Namespace) -> None:
    contact = os.environ.get("MUSICGRAPH_CONTACT", "").strip()
    if not contact or not (contact.startswith("https://") or "@" in contact):
        raise SystemExit("Set MUSICGRAPH_CONTACT to a public maintainer URL or email")
    run_dir = args.run_dir
    input_path = run_dir / "input.tsv"
    with input_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 500:
        raise SystemExit(f"Expected 500 frozen rows, found {len(rows)}")
    raw_dir = run_dir / "raw" / "musicbrainz"
    raw_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "musicbrainz-query-log.jsonl"
    candidate_path = run_dir / "musicbrainz-candidates.jsonl"
    claims_path = run_dir / "musicbrainz-claims.jsonl"
    result_path = run_dir / "musicbrainz-results.jsonl"
    done = completed_ids(result_path)
    client = Client(contact, log_path)
    count = 0
    for row in rows:
        candidate_id = row["candidate_id"]
        if candidate_id in done:
            continue
        if args.limit and count >= args.limit:
            break
        title = row["title_hint"]
        artist = row["artist_hint"]
        query = f'recording:"{title.replace(chr(34), " ")}" AND artist:"{artist.replace(chr(34), " ")}"'
        url = API + "/recording/?" + urlencode({"query": query, "fmt": "json", "limit": 10})
        search = client.get(candidate_id, "search_strict", url)
        if search is None:
            write_jsonl(result_path, {"candidate_id": candidate_id, "status": "error",
                                      "search_candidates": 0, "expanded": False})
            count += 1
            continue
        search_path = raw_dir / f"{candidate_id}-search-strict.json"
        search_path.write_text(json.dumps(search, ensure_ascii=False), encoding="utf-8")
        candidates = search.get("recordings", [])
        search_mode = "title_artist_strict"
        if not candidates:
            fallback_query = f'recording:"{title.replace(chr(34), " ")}"'
            fallback_url = API + "/recording/?" + urlencode(
                {"query": fallback_query, "fmt": "json", "limit": 100})
            fallback = client.get(candidate_id, "search_title_fallback", fallback_url)
            if fallback is not None:
                fallback_path = raw_dir / f"{candidate_id}-search-title-fallback.json"
                fallback_path.write_text(json.dumps(fallback, ensure_ascii=False), encoding="utf-8")
                candidates = fallback.get("recordings", [])
                search_mode = "title_fallback"
        ranked = []
        for rank, item in enumerate(candidates, 1):
            credited = artist_credit(item)
            title_sim = similarity(title, item.get("title", ""))
            artist_sim = similarity(artist, credited)
            candidate = {
                "candidate_id": candidate_id, "route": "musicbrainz_api",
                "lookup_mode": "title_artist", "search_mode": search_mode, "rank": rank,
                "source_recording_id": item.get("id", ""),
                "source_url": "https://musicbrainz.org/recording/" + item.get("id", ""),
                "source_title": item.get("title", ""), "source_artist": credited,
                "source_first_release_date": item.get("first-release-date", ""),
                "source_duration_ms": item.get("length"),
                "source_disambiguation": item.get("disambiguation", ""),
                "source_search_score": item.get("score"),
                "title_similarity": round(title_sim, 3),
                "artist_similarity": round(artist_sim, 3),
                "review_state": "unreviewed",
            }
            write_jsonl(candidate_path, candidate)
            ranked.append(candidate)
        best = max(ranked, key=lambda c: (c["title_similarity"] * 0.65 +
                                           c["artist_similarity"] * 0.35,
                                           c["source_search_score"] or 0), default=None)
        expanded = False
        if best and best["title_similarity"] >= 0.72 and best["artist_similarity"] >= 0.45:
            recording_id = best["source_recording_id"]
            inc = "artist-credits+isrcs+artist-rels+work-rels+release-rels+work-level-rels"
            lookup_url = API + f"/recording/{recording_id}?" + urlencode({"inc": inc, "fmt": "json"})
            lookup = client.get(candidate_id, "candidate_lookup", lookup_url)
            if lookup:
                lookup_path = raw_dir / f"{candidate_id}-lookup.json"
                lookup_path.write_text(json.dumps(lookup, ensure_ascii=False), encoding="utf-8")
                flatten_relations(candidate_id, recording_id, lookup, "recording",
                                  str(lookup_path), claims_path)
                for relation in lookup.get("relations", []):
                    if relation.get("target-type") == "work":
                        work = relation.get("work") or {}
                        flatten_relations(candidate_id, recording_id, work, "work",
                                          str(lookup_path), claims_path)
                expanded = True
        write_jsonl(result_path, {
            "candidate_id": candidate_id, "status": "retrieved" if candidates else "no_candidates",
            "search_candidates": len(candidates), "best_candidate_id":
            best["source_recording_id"] if best else "",
            "best_candidate_review_state": "unreviewed" if best else "none",
            "expanded": expanded, "search_mode": search_mode,
        })
        count += 1
        if count % 10 == 0:
            print(f"MusicBrainz processed {count} new rows; latest {candidate_id}", flush=True)
    print(f"MusicBrainz complete: {count} new rows, {len(completed_ids(result_path))} total", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--limit", type=int, default=0)
    run(parser.parse_args())
