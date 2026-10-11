# Deviations from approved plans

## 2026-10-11 — benchmark engineering pilot composition

The [Benchmark Handoff](Plan/Benchmark%20Handoff.md) calls for a small engineering pilot spanning every era and difficult cases before a full route run. The first 10-row pilot for each implemented API instead used corpus rows MGG-001 through MGG-010, all from era E1. This was a convenience choice while checking parser behavior, response fields and rate limits, not a change to the frozen 500-song corpus.

After those pilots, the same query protocol was applied to all 500 rows, including every era and hard cohort. The first full MusicBrainz directory was started afresh with the title-only fallback included in its first 10 rows; the earlier strict-only pilot remains in a separate ignored directory and is excluded from the full run. The full outputs therefore have consistent per-route protocols, but the pilot did not provide early cross-era parser validation. A future route pilot should deliberately choose rows from all five eras and difficult cases before its full pass.
