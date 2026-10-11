"""Create an empty, ID-aligned independent recording review sheet; no network calls."""

import csv
from pathlib import Path


ROOT = Path(__file__).parent
HEADERS = [
    "candidate_id", "identity_state", "credited_performer", "recording_title",
    "version_cue", "date_value", "date_type", "release_or_format",
    "catalog_or_duration_clue", "independent_evidence_url", "evidence_scope",
    "evidence_note", "isrc", "isrc_evidence_url", "spotify_track_id",
    "spotify_track_url", "apple_music_song_id", "apple_music_song_url",
    "genre_tags", "cultural_origin_tags", "language_tags",
    "popularity_tier", "hard_case_reason", "reviewer", "review_date",
    "review_note",
]


def main() -> None:
    path = ROOT / "recording-review.tsv"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing reviews: {path}")
    with (ROOT / "500-recording-candidates.tsv").open(newline="") as source:
        candidates = list(csv.DictReader(source, delimiter="\t"))
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=HEADERS, delimiter="\t")
        writer.writeheader()
        for row in candidates:
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "identity_state": "unreviewed",
                "credited_performer": row["artist_hint"],
                "recording_title": row["title_hint"],
                "date_value": row["year_hint"],
                "independent_evidence_url": row["independent_evidence_url"],
                "genre_tags": row["genre_hint"],
                "cultural_origin_tags": row["origin_hint"],
                "review_note": "Prefilled from unverified nomination hints; confirm every value.",
            })
    print(f"Created {path} with {len(candidates)} unreviewed rows")


if __name__ == "__main__":
    main()
