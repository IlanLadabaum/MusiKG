"""Report optional deep identity-review completion; not a benchmark gate."""

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    candidates = read_tsv(ROOT / "500-recording-candidates.tsv")
    reviews = read_tsv(ROOT / "recording-review.tsv")
    ids = [row["candidate_id"] for row in candidates]
    review_ids = [row["candidate_id"] for row in reviews]
    if len(ids) != 500 or len(ids) != len(set(ids)) or Counter(ids) != Counter(review_ids):
        raise SystemExit("FAIL: candidate/review IDs are missing, duplicated, or no longer aligned")
    required = [
        "credited_performer", "recording_title", "version_cue", "date_value",
        "date_type", "release_or_format", "independent_evidence_url",
        "evidence_scope", "evidence_note", "genre_tags", "cultural_origin_tags",
        "language_tags", "popularity_tier", "reviewer", "review_date",
    ]
    invalid: list[str] = []
    states = Counter(row["identity_state"] for row in reviews)
    for row in reviews:
        if row["identity_state"] != "verified":
            invalid.append(row["candidate_id"])
            continue
        if any(not row.get(field, "").strip() for field in required):
            invalid.append(row["candidate_id"])
        if row.get("evidence_scope") != "exact_recording":
            invalid.append(row["candidate_id"])
    print(f"Identity states: {dict(states)}")
    print(f"Rows requiring review or required fields: {len(set(invalid))}")
    if invalid:
        print("First unresolved IDs: " + ", ".join(list(dict.fromkeys(invalid))[:20]))
        raise SystemExit(1)
    print("Deep identity-review fields complete. This check is separate from structural query readiness.")


if __name__ == "__main__":
    main()
