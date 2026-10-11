"""Collect Apple catalog leads for independent corpus identity review.

This does not verify a recording or query any source scored by the benchmark.
It stores selected catalog fields, not response payloads, images, or previews.
Resumable and rate-limited to below Apple's approximate 20 calls/minute.
"""

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).parent
OUT = ROOT / "apple-identity-leads.tsv"
FIELDS = [
    "candidate_id", "queried_utc", "status", "result_count", "rank",
    "apple_track_id", "apple_artist", "apple_title", "apple_collection",
    "apple_release_date", "apple_duration_ms", "apple_track_url", "note",
]


def existing_ids() -> set[str]:
    if not OUT.exists():
        return set()
    with OUT.open(newline="") as handle:
        return {
            row["candidate_id"] for row in csv.DictReader(handle, delimiter="\t")
            if row["status"] in {"ok", "no_results"}
        }


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    with (ROOT / "500-recording-candidates.tsv").open(newline="") as handle:
        candidates = list(csv.DictReader(handle, delimiter="\t"))
    done = existing_ids()
    if not OUT.exists():
        with OUT.open("w", newline="") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t").writeheader()
    count = 0
    for candidate in candidates:
        if candidate["candidate_id"] in done:
            continue
        if count >= limit:
            break
        params = urlencode({
            "term": candidate["artist_hint"] + " " + candidate["title_hint"],
            "media": "music", "entity": "song", "country": "us", "limit": 10,
        })
        url = "https://itunes.apple.com/search?" + params
        status = "ok"
        results = []
        note = "Apple catalog is a lead only; releaseDate may describe a reissue."
        for attempt in range(3):
            try:
                request = Request(url, headers={"User-Agent": "MusicGraphGeneratorCorpusResearch/0.1"})
                with urlopen(request, timeout=20) as response:
                    data = json.load(response)
                results = data.get("results", [])
                status = "ok"
                break
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                status = "error"
                note = str(exc)[:150]
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
        if status == "ok" and not results:
            status = "no_results"
        now = datetime.now(timezone.utc).isoformat()
        with OUT.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
            if results:
                for rank, result in enumerate(results[:10], start=1):
                    writer.writerow({
                        "candidate_id": candidate["candidate_id"],
                        "queried_utc": now, "status": status,
                        "result_count": len(results), "rank": rank,
                        "apple_track_id": result.get("trackId", ""),
                        "apple_artist": result.get("artistName", ""),
                        "apple_title": result.get("trackName", ""),
                        "apple_collection": result.get("collectionName", ""),
                        "apple_release_date": result.get("releaseDate", ""),
                        "apple_duration_ms": result.get("trackTimeMillis", ""),
                        "apple_track_url": result.get("trackViewUrl", ""),
                        "note": note,
                    })
            else:
                writer.writerow({
                    "candidate_id": candidate["candidate_id"],
                    "queried_utc": now, "status": status,
                    "result_count": 0, "rank": "", "note": note,
                })
        count += 1
        if count % 10 == 0:
            print(f"Queried {count}; latest {candidate['candidate_id']}", flush=True)
        time.sleep(3.5)
    print(f"Completed {count} new queries; {len(existing_ids())} unique candidate IDs logged", flush=True)


if __name__ == "__main__":
    main()
