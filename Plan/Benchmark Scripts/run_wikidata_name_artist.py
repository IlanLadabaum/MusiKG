"""Resumable, unreviewed Wikidata artist/title discovery benchmark.

Searches Wikidata without MusicBrainz IDs, then snapshots claims for returned
items. Candidate search is not evidence that an item is the intended recording.
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN = ROOT / "tmp" / "benchmark-name-artist-full"
API = "https://www.wikidata.org/w/api.php"


def now():
    return datetime.now(timezone.utc).isoformat()


def append(path, row):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def complete_ids(path):
    if not path.exists():
        return set()
    return {json.loads(line)["candidate_id"] for line in path.read_text().splitlines() if line}


class Client:
    def __init__(self, contact, log_path, spacing=1.2):
        self.ua = f"MusiKGResearch/0.1 ({contact})"
        self.log_path = log_path
        self.spacing = spacing
        self.last_start = 0.0

    def get(self, candidate_id, phase, params):
        url = API + "?" + urlencode({**params, "format": "json"})
        for attempt in range(4):
            wait = max(0.0, self.spacing - (time.monotonic() - self.last_start))
            if wait:
                time.sleep(wait)
            self.last_start = time.monotonic()
            started = now()
            tick = time.perf_counter()
            status, code, error, payload, data = "error", None, "", b"", None
            try:
                with urlopen(Request(url, headers={"User-Agent": self.ua,
                                                   "Accept": "application/json"}), timeout=30) as response:
                    code = response.status
                    payload = response.read()
                data = json.loads(payload)
                status = "ok"
            except HTTPError as exc:
                code, error = exc.code, f"HTTP {exc.code}: {exc.reason}"
            except (URLError, TimeoutError, ValueError, OSError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            append(self.log_path, {
                "candidate_id": candidate_id, "route": "wikidata",
                "lookup_mode": "title_artist", "phase": phase, "url": url,
                "start_utc": started, "end_utc": now(),
                "elapsed_s": round(time.perf_counter() - tick, 3),
                "rate_wait_s": round(wait, 3), "attempt": attempt + 1,
                "status": status, "http_status": code, "bytes": len(payload),
                "response_received": bool(payload), "raw_retained": status == "ok",
                "error": error,
            })
            if status == "ok":
                return data
            if code not in (429, 500, 502, 503, 504) and code is not None:
                break
            if attempt < 3:
                time.sleep(min(30, 5 * (attempt + 1)))
        return None


def scalar_value(statement):
    snak = statement.get("mainsnak", {})
    value = (snak.get("datavalue") or {}).get("value")
    if isinstance(value, dict):
        return value.get("id") or value.get("time") or value.get("text") or value
    return value


def run(args):
    contact = os.environ.get("MUSICGRAPH_CONTACT", "").strip()
    if not contact.startswith("https://"):
        raise SystemExit("Set MUSICGRAPH_CONTACT to a public maintainer URL")
    run_dir = args.run_dir
    with (run_dir / "input.tsv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 500:
        raise SystemExit(f"Expected 500 frozen rows, got {len(rows)}")
    raw_dir = run_dir / "raw" / "wikidata"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "wikidata-results.jsonl"
    candidates_path = run_dir / "wikidata-candidates.jsonl"
    claims_path = run_dir / "wikidata-statements.jsonl"
    client = Client(contact, run_dir / "wikidata-query-log.jsonl")
    done = complete_ids(results_path)
    count = 0
    for row in rows:
        corpus_id = row["candidate_id"]
        if corpus_id in done:
            continue
        if args.limit and count >= args.limit:
            break
        search = client.get(corpus_id, "title_search", {
            "action": "wbsearchentities", "search": row["title_hint"],
            "language": "en", "uselang": "en", "type": "item", "limit": 20,
        })
        if search is None:
            append(results_path, {"candidate_id": corpus_id, "status": "search_error",
                                  "candidate_count": 0, "detail_count": 0})
            count += 1
            continue
        (raw_dir / f"{corpus_id}-search.json").write_text(
            json.dumps(search, ensure_ascii=False), encoding="utf-8")
        candidates = search.get("search", [])
        for rank, candidate in enumerate(candidates, 1):
            append(candidates_path, {
                "candidate_id": corpus_id, "route": "wikidata",
                "lookup_mode": "title_artist", "rank": rank,
                "source_entity_id": candidate.get("id", ""),
                "source_url": candidate.get("concepturi", ""),
                "source_label": candidate.get("label", ""),
                "source_description": candidate.get("description", ""),
                "search_match": candidate.get("match", {}),
                "review_state": "unreviewed",
            })
        ids = [c["id"] for c in candidates if c.get("id")]
        detail = None
        if ids:
            detail = client.get(corpus_id, "candidate_details", {
                "action": "wbgetentities", "ids": "|".join(ids),
                "props": "labels|descriptions|claims", "languages": "en",
            })
        if detail is not None:
            (raw_dir / f"{corpus_id}-details.json").write_text(
                json.dumps(detail, ensure_ascii=False), encoding="utf-8")
            for qid, entity in detail.get("entities", {}).items():
                for prop, statements in entity.get("claims", {}).items():
                    for statement in statements:
                        append(claims_path, {
                            "candidate_id": corpus_id, "route": "wikidata",
                            "source_entity_id": qid, "source_scope": "wikidata_item",
                            "property_id": prop, "statement_id": statement.get("id", ""),
                            "rank": statement.get("rank", ""),
                            "value": scalar_value(statement),
                            "snaktype": statement.get("mainsnak", {}).get("snaktype", ""),
                            "source_path": str(raw_dir / f"{corpus_id}-details.json"),
                            "review_state": "unreviewed",
                        })
        append(results_path, {
            "candidate_id": corpus_id,
            "status": "retrieved" if candidates else "no_candidates",
            "candidate_count": len(candidates),
            "detail_count": len(detail.get("entities", {})) if detail else 0,
            "detail_status": "ok" if detail is not None else "not_requested" if not ids else "error",
        })
        count += 1
        if count % 10 == 0:
            print(f"Wikidata processed {count} new rows; latest {corpus_id}", flush=True)
    print(f"Wikidata complete: {count} new rows, {len(complete_ids(results_path))} total", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--limit", type=int, default=0)
    run(parser.parse_args())
