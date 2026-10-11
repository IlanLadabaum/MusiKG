"""Summarize possible artist/title matches; does not verify recording identity."""

import csv
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).parent


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def similarity(left: str, right: str) -> float:
    a, b = norm(left), norm(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def main() -> None:
    with (ROOT / "500-recording-candidates.tsv").open(newline="") as handle:
        candidates = list(csv.DictReader(handle, delimiter="\t"))
    with (ROOT / "apple-identity-leads.tsv").open(newline="") as handle:
        leads = list(csv.DictReader(handle, delimiter="\t"))
    by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for lead in leads:
        by_id[lead["candidate_id"]].append(lead)
    fields = [
        "candidate_id", "status", "close_name_candidates", "best_rank",
        "best_artist", "best_title", "best_collection", "best_release_date",
        "best_duration_ms", "best_url", "review_warning",
    ]
    with (ROOT / "apple-lead-triage.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for candidate in candidates:
            rows = by_id.get(candidate["candidate_id"], [])
            matches = []
            for lead in rows:
                artist_score = similarity(candidate["artist_hint"], lead["apple_artist"])
                title_score = similarity(candidate["title_hint"], lead["apple_title"])
                if artist_score >= 0.72 and title_score >= 0.75:
                    matches.append((artist_score + title_score, lead))
            matches.sort(key=lambda pair: pair[0], reverse=True)
            best = matches[0][1] if matches else {}
            writer.writerow({
                "candidate_id": candidate["candidate_id"],
                "status": "no_query" if not rows else ("possible_match" if matches else "no_close_catalog_match"),
                "close_name_candidates": len(matches),
                "best_rank": best.get("rank", ""),
                "best_artist": best.get("apple_artist", ""),
                "best_title": best.get("apple_title", ""),
                "best_collection": best.get("apple_collection", ""),
                "best_release_date": best.get("apple_release_date", ""),
                "best_duration_ms": best.get("apple_duration_ms", ""),
                "best_url": best.get("apple_track_url", ""),
                "review_warning": "Name similarity only. Confirm original performance, version and date independently.",
            })
    print(f"Triaged {len(by_id)} queried IDs out of {len(candidates)} candidates")


if __name__ == "__main__":
    main()
