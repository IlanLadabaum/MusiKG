"""Check whether the 500 input nominations are structurally queryable.

This intentionally does not require ISRCs or prior recording verification.
It makes no network requests and does not authorize starting the benchmark.
"""

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent
BOUNDS = {"E1": (0, 1949), "E2": (1950, 1969), "E3": (1970, 1989),
          "E4": (1990, 2009), "E5": (2010, 2026)}


def main() -> None:
    with (ROOT / "500-recording-candidates.tsv").open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    problems = []
    ids = [row["candidate_id"] for row in rows]
    if len(rows) != 500 or len(set(ids)) != 500:
        problems.append("Expected 500 rows with unique IDs")
    keys = Counter((row["artist_hint"].strip().casefold(),
                    row["title_hint"].strip().casefold()) for row in rows)
    if any(count > 1 for count in keys.values()):
        problems.append("Repeated artist/title input")
    cohorts = Counter((row["era"], row["cohort"]) for row in rows)
    for era in BOUNDS:
        if cohorts[(era, "general")] != 90 or cohorts[(era, "hard")] != 10:
            problems.append(f"{era}: expected 90 general and 10 hard")
    for row in rows:
        candidate_id = row["candidate_id"]
        for field in ("artist_hint", "title_hint", "year_hint", "origin_hint", "genre_hint"):
            if not row[field].strip():
                problems.append(f"{candidate_id}: missing {field}")
        try:
            low, high = BOUNDS[row["era"]]
            year = int(row["year_hint"])
            if not low <= year <= high:
                problems.append(f"{candidate_id}: year outside {row['era']}")
        except (KeyError, ValueError):
            problems.append(f"{candidate_id}: invalid era or year")
    print(f"Queryable input rows: {len(rows)}")
    print("Cohorts:", dict(sorted(cohorts.items())))
    if problems:
        print("Structural problems:")
        for problem in problems[:30]:
            print("-", problem)
        raise SystemExit(1)
    print("Structural checks pass. Membership review and freeze are still pending.")


if __name__ == "__main__":
    main()
