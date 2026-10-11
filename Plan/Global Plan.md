# Global Plan — Music Graph Generator

Top-level plan. Describes the project broadly and links to topic sub-plans as they are created. See `Coding_Agent_Skill.md` for how planning docs and status markers work.

Status markers used here: [DECIDED] user-approved · [OPEN] raised, not decided · [PROPOSED] agent suggestion · [IDEA] early developer idea, not yet decided · [BUILT] implemented.

## Vision

An app that builds a graph of a person's music taste from whatever data is available about what they listen to. The graph connects tracks to the people behind them (performers, session musicians, songwriters, producers, engineers, etc.). The goal is to surface people the listener likes without knowing it — for example a session musician or producer who appears across many of their favorite tracks and is a hidden influence on their taste.

- [DECIDED] The core is a song-list-to-graph engine: accept songs with optional per-song weights, enrich them from music databases, and build a typed graph. Keep the core input independent of any streaming service.
- [DECIDED] Initial inputs are songs. Artists, albums, labels, and other concepts may become inputs in a later version.
- [DECIDED] The app will be open source on GitHub and run locally on macOS, Windows, and Linux, with data and computation on the user's computer and no hosted application infrastructure.

## Inputs (listening data)

- [DECIDED] Weights are optional; their meaning depends on the input source. Play count is one example.
- [DECIDED] Prioritize Spotify import first. Consider other streaming services and Last.fm after Spotify works well.
- [DECIDED] Treat each input song as a specific sound recording. Different performances or recordings of the same composition can have different performer and production credits.
- [PROPOSED] Represent the underlying musical work separately when data is available, linked to its recording(s), so shared writing credits and cover relationships can be explored. An ISRC identifies a recording; an ISWC identifies a musical work.
- [DECIDED] When an ISRC is available, treat catalog tracks sharing it as one recording by default, while retaining their separate provider and release references; flag clear conflicting evidence for review. Use artist and title with version clues when an ISRC is unavailable.
- [OPEN] Exact core input contract and matching rules for records without identifiers, ambiguous matches, and erroneous or conflicting ISRC assignments.
- [OPEN] Spotify import methods and access limits: public playlist URL, account authorization, personal data export, or other methods. Determine which support playlists, listening history, and weights.
- [RESEARCHED] Spotify's 2026 Development Mode restrictions make a general public-playlist URL import and a shared sign-in app difficult; Extended Streaming History export contains full-lifetime streams and Spotify track URIs. See the research sub-plan. An export-based first adapter is proposed, not decided.
- [RESEARCHED] The developer's personal Spotify app credentials can support the private benchmark but are not a settled distribution mechanism. Spotify Development Mode currently limits authenticated users to five; Extended Quota Mode is intended for wider distribution, but current applications are limited to qualifying organizations. A distributable local app also cannot safely embed a Client Secret. [OPEN] Choose a compliant public import/identifier path after testing provider access and file-based fallbacks.

## Track credits / metadata

- [DECIDED] Enrich songs with as many useful links and credits as practical, including artists, albums, labels, producers, session musicians, songwriters, and other credited contributors.
- [DECIDED] Favor an accurate, information-rich graph during ingestion; preserve semantic edge types so users can filter or weight categories after enrichment. Decide what to prune after the source analysis.
- [DECIDED] Retain source facts at their stated scope, including release-level associations; do not infer that a release-wide credit proves participation in every recording. [OPEN] Decide the graph encoding (for example, a contributor linked to the album, then the album linked to its recordings) after source selection and concrete examples.
- [PROPOSED] Consider release year or month and other non-credit metadata as optional graph attributes or nodes.
- [OPEN] Which free, public databases provide this data, and how complete/accessible each is.
- [OPEN] How to combine database records, track provenance, manage sparse credits, and cache data locally.
- [RESEARCHED] No verified free industry-wide credits registry has been identified: DDEX standardizes credit exchange, IFPI's ISRC search focuses on recording identity, and Jaxsta offers a larger licensed commercial credits API. The developer has requested a source-neutral, multi-source benchmark before choosing any primary source; see the [Data Source R&D plan](Data%20Source%20R%26D.md).

## Graph and insights

- [DECIDED] Use semantic node and edge types; users can choose which types appear in the graph explorer.
- [DECIDED] Surface hub nodes and less obvious shared connections across input songs, such as a recurring session musician or label.
- [DECIDED] Lead the general user experience with a ranked discovery set that explains shared connections. Provide graph exploration as an additional mode for interested users.
- [DECIDED] Initial screen is a ranked list of entities. Selecting an entity opens its one-hop neighborhood. Each graph node can be selected to inspect its full available properties and has an explicit control to expand its neighborhood by one hop.
- [OPEN] Exact graph schema, representation of credits and releases, and how input weights propagate through the graph.
- [OPEN] Ranking methods and how to avoid obvious or misleading hubs. Candidate methods include degree-based ranking without weights and weighted graph methods when weights exist.
- [OPEN] Detailed explorer interaction and presentation of insights beyond the decided ranked-list, node-inspection, and one-hop expansion flow. The developer's existing explorer is unsuitable as a fork.
- [OPEN] Whether users can expand beyond the graph induced by their input songs to explore neighboring entities.

## Platform / stack

- [DECIDED] The app is local-first, cross-platform, and should remain lightweight and efficient.
- [DECIDED] Building or extending a graph may require internet access to retrieve external metadata.
- [OPEN] Whether completed graphs remain usable offline. Offline use is desirable but may be deferred if it prevents access to higher-value sources; settle storage and refresh behavior after source evaluation.
- [DECIDED] Version 0 includes an update mechanism that alerts users to new releases and allows installation from within the app.
- [OPEN] App packaging and stack, local storage and computation architecture, and a cross-platform update mechanism that meets the version 0 requirement.
- [OPEN] Practical graph-size limits and when to warn users about large inputs.
- [DECIDED] If graph building takes a meaningful wait (around 1–2 minutes or more), show a dedicated loading page stating that the graph is being built and estimating the remaining time. Base estimates on measured build times from real tests, updated as needed. The exact trigger, estimation method, and behavior when a reliable estimate is unavailable remain open until performance testing.

## Repository

- [DECIDED] Planning docs in `Plan/` are tracked in git, for backup and to keep a history of decisions.

- [DECIDED] Source code lives in this same repo as the plans, under `src/` (created once the stack is chosen). Rationale: plans track the code's build status and decisions, so a shared history ties each decision to its implementation.

## Sub-plans

- [Research: comparable projects and metadata sources](Research - Existing Projects and Data Sources.md)
- [Data source R&D: candidate inventory, benchmark and selection](Data Source R&D.md)
- [Source capability audit: documented fields, query granularity and provisional type map](Source Capability Audit.md)
- [Benchmark handoff: corpus gate, source eligibility, data contract and execution order](Benchmark Handoff.md)
- [Identifier access research: Spotify exports and recording IDs without a shared Spotify app](Identifier Access Research.md)
- [500-song artist/title benchmark run: completed retrievals and pending adjudication](Benchmark Run 2026-10-11.md)

## Current planning sequence

- [DECIDED] The high-level product goal emphasizes explainable discoveries, with graph exploration as a second mode; recording inputs and local computation remain the foundation. Source conflict policy awaits concrete source testing.
- [RESEARCHED] Initial survey of comparable open-source apps, reusable explorers, and feature ideas is in the linked research plan. The developer's own explorer remains to be inspected.
- [DECIDED] Audit candidate source capabilities and query granularity, then choose sources only after a like-for-like test across 500 tagged recordings spanning genre, country/region and era. Retain source-level results for detailed coverage analysis, measure unique and combined contributions, and create narrower follow-up sets where gaps appear. The 12-recording MusicBrainz probe is preliminary and does not settle source selection.
