# Exploratory 500-song artist/title benchmark — 2026-10-11

Status: [BUILT] three automated retrieval routes completed; [OPEN] recording/claim adjudication, additional source routes, and source selection. This is the first **name/artist-only** pass the developer authorized. It is an exploratory baseline, not a validated comparison of correct credit coverage. Read [Benchmark Handoff](Benchmark%20Handoff.md) for the data contract and decision boundary, and [Identifier Access Research](Identifier%20Access%20Research.md) for the separate future ISRC-assisted pass.

## Reproducible run state

- Public repo/contact: [IlanLadabaum/MusiKG](https://github.com/IlanLadabaum/MusiKG). The initial preparation commit `ba0a57c79c463b3d394988492f838a85562dc67d` was pushed to `main` on 2026-10-11. The benchmark runners were edited after that commit; their exact SHA-256 values are in the ignored run manifest.
- Frozen input: `tmp/benchmark-name-artist-full/input.tsv`, 500 rows, SHA-256 `604c3bc88749f6fc88c82d8a00fa421eafa1edd8f130dcbde52fe503b36f74a7`. The corpus is provisional, with 100 rows per era, 450 general and 50 hard rows. Artist/title queries do not require the 451 unreviewed recording identities or ISRCs. Input membership and tags were not fully independently adjudicated.
- Run artifacts: `tmp/benchmark-name-artist-full/` (ignored by git, currently about 187 MB). `run.json` records the corpus hash, runner hashes, request spans and retention policy; `retrieval-summary.json` has route and stratum counts. Query logs, result rows, candidate rows, extracted statements/credits, and permitted source snapshots are also there. **Do not delete or re-freeze this run.** Copy or archive it separately before changing machines; it is not on GitHub.
- All three result files have exactly 500 unique corpus IDs, with no missing or extra IDs. The runners are resumable and skip completed IDs. Rerunning them in this directory does nothing unless a result is removed; protocol revisions should use a new run directory to preserve comparison.
- Scripts: `Plan/Benchmark Scripts/run_musicbrainz_name_artist.py`, `run_wikidata_name_artist.py`, `run_discogs_name_artist.py`, and `summarize_name_artist.py`. Run with `MUSICGRAPH_CONTACT=https://github.com/IlanLadabaum/MusiKG`; Python 3 standard library only. The summaries can be regenerated with `python3 'Plan/Benchmark Scripts/summarize_name_artist.py' tmp/benchmark-name-artist-full`.

## Retrieval results (unreviewed)

| Route | Rows with >=1 search candidate | Rows with no search candidate | Requests incl. retries | UTC span | Unreviewed extracted data |
| --- | ---: | ---: | ---: | --- | --- |
| MusicBrainz API | 489 | 11 | 1,068 | 07:05:32–07:29:16 | 5,141 candidate rows; 473 selected candidate lookups; 2,773 relationship rows. 98 of 473 looked-up candidate recordings list >=1 ISRC. |
| Wikidata API | 455 | 45 | 955 | 07:07:39–07:26:57 | 5,005 candidate QID rows; 131,967 raw statement rows across **all** returned candidate items. 363 of those statements are P1243 (ISRC), which cannot be attributed to the target recordings without item review. |
| Discogs API | 446 | 54 | 946 | 07:11:20–07:55:37 | 7,782 release candidate rows; one selected release fetched for each retrieved row; 2,408 CC0 credit/label association rows; 375 selected releases have a similar track title. |

Raw search retrieval union is 493/500; 416 rows returned candidates from all three routes. Candidate-only exclusives are MusicBrainz 10, Wikidata 1, Discogs 1. **These are not unique correct matches or unique graph facts.** A same-title item or selected reissue may be unrelated to the intended recording. No candidate or claim has been independently adjudicated as correct, so validated coverage, marginal lift, and primary-source ranking are not yet available.

By era, candidate retrieval counts (each era has 100 input rows):

| Era | MusicBrainz | Wikidata | Discogs |
| --- | ---: | ---: | ---: |
| E1 | 93 | 80 | 83 |
| E2 | 100 | 97 | 95 |
| E3 | 100 | 92 | 96 |
| E4 | 99 | 96 | 89 |
| E5 | 97 | 90 | 83 |

## Protocol and limitations

- MusicBrainz: strict fielded recording title AND artist search (max 10 candidates), followed by exact title-only search (max 100) only when strict returns zero. One plausible candidate is expanded for recording/work relations and ISRCs, but always marked `unreviewed`. Core data is retained in `raw/musicbrainz`. There were 54 transient HTTP 503 attempts, all followed by successful retries; no rows ended in request error. The initial engineering pilot (first 10 rows) and continuation used the same two-step protocol in this run. One earlier strict-only pilot lives separately under `tmp/benchmark-name-artist-20261010/` and must not be mixed with this run.
- Wikidata: public `wbsearchentities` title search (max 20) followed by `wbgetentities` for every returned item. Search candidates and item statements are retained in `raw/wikidata`; **all** statements refer to candidate items, not necessarily the intended recordings. Zero HTTP errors were logged. This route is potentially useful for person/work/context and identifier crosswalks, but entity-scope and recording correctness need review.
- Discogs: public API search by track plus artist (max 20 release candidates), then one release selected mainly by proximity to the input year. This selection is a research heuristic and may choose a reissue or wrong release. Track and release credits remain separately scoped. Complete API payloads were **not** retained because Discogs distinguishes CC0 factual fields from restricted content; selected CC0 fields are in `extracted_cc0/discogs`, with response-received, bytes, timing and raw-retained flags in the query log. The 946 calls had no HTTP errors at 2.8 seconds spacing, below the observed 25 requests/minute anonymous limit. [API terms](https://support.discogs.com/hc/en-us/articles/360009334593-API-Terms-of-Use) also impose freshness/retention and attribution requirements on an eventual app.
- The three routes ran concurrently, so their times are per-route network/wait spans, not an end-to-end sequential app build time. Approximate response bytes: MusicBrainz 27.7 MB, Wikidata 90.3 MB, Discogs 9.4 MB. Rate-limit waits logged: 405 s, 789 s, 2,409 s, respectively. These are research request volumes; a production app could query fewer properties, use caching, or stop early after high-confidence matches.
- The scripts do not yet normalize semantic property names across sources, adjudicate candidate identities, validate claims, or measure correct credits per second. The 500 nominations are a diagnostic set, not a representative global random sample. The artist/title pass gives **no evidence yet** about how much ISRC-first queries improve matching.
- The first 10-row engineering pilots did not span all five eras as the handoff prescribed; this deviation and its effect are recorded in [DEVIATIONS.md](../DEVIATIONS.md).

## ISRC/access investigation state

- Spotify Extended Streaming History documents track URI, title, artist, album and play-time fields, but not ISRC. A local file import can therefore supply weighted inputs without a shared Spotify developer app; identity resolution remains necessary.
- Five public ISRC finder sites were checked in [Identifier Access Research](Identifier%20Access%20Research.md). IFPI claims >150 million searchable ISRCs and offers manual CSV export, but no documented open API was found; its SoundExchange-powered search has automation/redistribution restrictions. MusicDibs uses MusicBrainz data. ISRC Finder uses Spotify's API. Soundcharts has a one-time free API trial then paid access. Soundplate documents a free web form but no public integration API found.
- A new promising route was live-probed: `https://api.deezer.com/search?q=...` returned title, artist and ISRC for sample tracks without an app token; `https://api.deezer.com/track/3135556` also returned an ISRC. [Deezer developer terms](https://developers.deezer.com/termsofuse) describe free noncommercial personal applications but refer to developer registration and allow access restrictions. Public-app eligibility, rate limits, retention, and matching quality remain [OPEN]. **Do not use Deezer-derived ISRCs to alter this artist/title run.** Test them as independent provider candidates and, if terms permit, in a separate ISRC-assisted run.

## Next agent actions

1. Read required repo guidance, this report, the handoff, capability audit, source R&D plan and identifier research. Preserve the existing ignored run artifacts. Note that `Coding_Agent_Skill.md` has a separate user modification; do not edit or stage it without explicit approval.
2. Audit a stratified sample of target/candidate identity matches across eras, genres and regions, plus raw-source exclusives and conflicts. Verify the actual recording against independent evidence; record `correct`, `wrong`, `ambiguous`, or `unreviewed`. Only then compute validated coverage and unique graph-fact contribution. Avoid using MusicBrainz's own ISRC as independent proof of its candidate selection.
3. Review source permissions and usefulness for remaining candidates before deciding whether to add routes. In particular, evaluate Wikipedia section extraction, LoC historical records, ListenBrainz mapper access (previous TLS hostname failure), Open Opus's tiny/inapplicable classical denominator, DOREMUS availability, TheAudioDB retention rights, and Discogs CC0 dump feasibility. Do not assign zero coverage to routes held for access or applicability reasons.
4. Investigate Deezer's terms/support and measure artist/title-to-ISRC match quality on a stratified subset without feeding those IDs to this baseline; then design the separate ISRC-assisted benchmark if appropriate. A public Spotify URI-to-ISRC crosswalk remains unproven.
5. After matching and route analysis, report coverage by stratum, correctness, unique/combined validated facts, wall time/throughput, setup/rights issues, and non-graph fields. Present source recommendations for the developer's decision; do not mark a primary source [DECIDED] yet.
