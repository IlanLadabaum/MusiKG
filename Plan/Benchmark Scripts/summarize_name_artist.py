"""Summarize raw retrieval in an exploratory artist/title benchmark run.

These are discovery and throughput measures, not validated recording coverage.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def stats(values):
    values = sorted(values)
    if not values:
        return {"n": 0, "mean": None, "median": None, "p95": None}
    return {"n": len(values), "mean": round(sum(values) / len(values), 3),
            "median": values[len(values) // 2],
            "p95": values[min(len(values) - 1, int(len(values) * .95))]}


def summarize(run_dir):
    with (run_dir / "input.tsv").open(newline="", encoding="utf-8") as f:
        inputs = {row["candidate_id"]: row for row in csv.DictReader(f, delimiter="\t")}
    output = {"input_rows": len(inputs), "interpretation":
              "Unreviewed artist/title candidate retrieval; not verified recording coverage."}
    for route in ("musicbrainz", "wikidata", "discogs"):
        results = read_jsonl(run_dir / f"{route}-results.jsonl")
        logs = read_jsonl(run_dir / f"{route}-query-log.jsonl")
        latest = {row["candidate_id"]: row for row in results}
        route_out = {
            "processed": len(latest), "remaining": len(inputs) - len(latest),
            "result_status": dict(Counter(row["status"] for row in latest.values())),
            "requests": len(logs),
            "http_status": {str(k): v for k, v in Counter(row["http_status"] for row in logs).items()},
            "request_elapsed_seconds": stats([r["elapsed_s"] for r in logs]),
            "rate_wait_seconds": round(sum(r["rate_wait_s"] for r in logs), 3),
            "response_bytes": sum(r["bytes"] for r in logs),
            "strata": {},
        }
        for field in ("era", "cohort", "origin_hint", "genre_hint"):
            categories = defaultdict(lambda: Counter())
            for corpus_id, result in latest.items():
                value = inputs[corpus_id][field]
                tokens = value.split("|") if field == "genre_hint" else [value]
                for token in tokens:
                    categories[token.strip()][result["status"]] += 1
            route_out["strata"][field] = {k: dict(v) for k, v in sorted(categories.items())}
        if route == "musicbrainz":
            route_out["candidate_rows"] = len(read_jsonl(run_dir / "musicbrainz-candidates.jsonl"))
            route_out["extracted_relationship_rows_unreviewed"] = len(
                read_jsonl(run_dir / "musicbrainz-claims.jsonl"))
            route_out["expanded_rows"] = sum(bool(row.get("expanded")) for row in latest.values())
        elif route == "wikidata":
            route_out["candidate_rows"] = len(read_jsonl(run_dir / "wikidata-candidates.jsonl"))
            route_out["raw_statement_rows_unreviewed"] = len(
                read_jsonl(run_dir / "wikidata-statements.jsonl"))
        else:
            route_out["candidate_rows"] = len(read_jsonl(run_dir / "discogs-candidates.jsonl"))
            route_out["extracted_credit_rows_unreviewed"] = len(
                read_jsonl(run_dir / "discogs-claims.jsonl"))
            route_out["release_fetched_rows"] = sum(
                bool(row.get("release_fetched")) for row in latest.values())
            route_out["rows_with_similar_track_title"] = sum(
                bool(row.get("matching_track_count")) for row in latest.values())
        output[route] = route_out
    (run_dir / "retrieval-summary.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    data = summarize(args.run_dir)
    for route in ("musicbrainz", "wikidata", "discogs"):
        row = data[route]
        print(route, row["processed"], row["result_status"],
              f"{row['requests']} requests")
