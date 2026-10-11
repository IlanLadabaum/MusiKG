# Recording identifiers without a shared Spotify developer app

Status: [RESEARCHED] distribution paths; [OPEN] product choice and measured match quality. This note separates a user's input import from the source-neutral 500-recording metadata benchmark.

## What Spotify's user export supplies

Spotify's [data export field guide](https://support.spotify.com/jm/article/understanding-my-data/) describes Extended Streaming History records with track name, artist, album, Spotify track URI, timestamp, duration played and playback flags. Its documented fields do **not** include an ISRC. The URI is still useful: it lets the app deduplicate the same Spotify catalog track and preserve provenance, but it cannot be assumed to resolve to an ISRC through a free public crosswalk. Export import needs no shared Spotify API credentials and can produce listening weights directly from the user's own history. It is a [PROPOSED] first Spotify adapter, not yet [DECIDED]. A user must request the export and import its files; it is less immediate than sign-in.

## Identifier resolution options

| Path | Input needed | Output | Distribution/access implication | Benchmark status |
| --- | --- | --- | --- | --- |
| [MusicBrainz search and lookup](https://musicbrainz.org/doc/MusicBrainz_API) | Artist/title; optionally album, version, date, duration | Candidate recording MBID; ISRC when present on a matched recording | Public noncommercial API with contact User-Agent and rate limit; candidate match must be reviewed or confidence-qualified | Artist/title route running; its own ISRCs cannot serve as independent ground truth for measuring that route |
| [ListenBrainz MBID Mapper](https://mapper.listenbrainz.org/docs) | Artist and recording name, optional release | Candidate MusicBrainz recording/release IDs and confidence | Potential public identity bridge; live endpoint/terms need verification | Initial endpoint probe had a TLS hostname error; record access failure, not zero matches |
| [Wikidata](https://www.wikidata.org/wiki/Property:P1243) | Matched item or search | ISRC statements on some items | Open CC0 structured data; sparsity and item-scope errors need measurement | Artist/title discovery route running; ISRC coverage pending |
| [AcoustID](https://acoustid.org/webservice) | Audio fingerprint or AcoustID ID | Candidate MBID/ISRC | Not usable from a Spotify history export alone; requires audio access, an application key, and noncommercial terms | Inapplicable to artist/title-only corpus |
| [Spotify Web API Get Track](https://developer.spotify.com/documentation/web-api/reference/get-track) | Spotify track ID and authorized API access | `external_ids.isrc` when available | Developer app access is gated; [Development Mode](https://developer.spotify.com/documentation/web-api/concepts/quota-modes) is capped at five users, and shared client secrets cannot ship in local open-source code | Possible private second run only; not assumed available to the released app |
| Apple Music catalog API | Apple catalog song ID and developer token | ISRC field | Requires a developer signing setup; no public user-independent credential is established for this app | Not available for current run |
| [Deezer public API](https://developers.deezer.com/termsofuse) | Artist/title query to `/search`; candidate Deezer track ID | ISRC appears directly in search results and track detail when present | A credential-free live probe succeeded on 2026-10-11. Developer terms allow free noncommercial personal applications but refer to developer account registration and permit Deezer to restrict access; current developer docs redirect to login. Public-app eligibility, rate limits, retention and matching quality remain [OPEN]. | Promising independent ISRC acquisition route for the separate second run; do not feed its ISRCs into the artist/title baseline |

## Five public ISRC finder sites (checked 2026-10-11)

These are useful **manual lookup tools**, but a free website form does not by itself grant an app a stable machine interface or reuse rights.

| Site | Verified source/function | App integration assessment |
| --- | --- | --- |
| [IFPI International ISRC Search](https://isrc.ifpi.org/) | IFPI states its database has over 150 million ISRCs; artist/title search and selected CSV export are free through the public site. Its [search page](https://isrc.ifpi.org/search) says it is powered by SoundExchange. | No documented open public API found. [SoundExchange's ISRC Search terms](https://www.soundexchange.com/terms-of-use/) prohibit systematic or automatic collection from its search site and redistribution of its content. Its [API is offered by request](https://www.soundexchange.com/service-provider/licensing-101/) for licensees/reporting vendors; this app's eligibility is unconfirmed. Do not automate the public form without explicit permission. Manual spot checks may help adjudicate difficult benchmark recordings. |
| [ISRC Finder](https://www.isrcfinder.com/) | Searches Spotify links or artist/title; its footer says it is built with the Spotify Web API. | No documented third-party API or permission to reuse it as this app's backend found. It does not remove Spotify access dependence; it shifts that dependence to another operator's website. |
| [Soundcharts ISRC Finder](https://soundcharts.com/en/isrc-finder) | Free human-facing form for Spotify links or artist/title, backed by Soundcharts data/API. | The [production API](https://help.soundcharts.com/en/articles/10091349-how-can-i-get-access-to-soundcharts-api) uses app/user credentials, offers a one-time 1,000-request trial, and then [paid plans](https://developers.soundcharts.com/pricing). It is not a durable free API for every user of this local open-source app. |
| [MusicDibs metadata finder](https://musicdibs.com/tools/metadata-finder) | Its own page says results are fetched live from MusicBrainz, with no sign-up or limits for the web form. | No independent ISRC coverage beyond MusicBrainz. Use the documented MusicBrainz API directly for reproducibility, provenance and query control. |
| [Soundplate ISRC Finder](https://soundplate.com/isrc-finder/) | Free human-facing lookup by Spotify URL or artist/title. | No documented public integration API or bulk-use permission found. Site terms acknowledge dependence on third-party music APIs; treat it as manual reference pending written access terms. |

The IFPI database is potentially valuable as **independent correctness evidence** for a stratified manual sample. It is not presently an approved automated acquisition route for the 500-song benchmark or released app. The five finder websites do not establish a reliable free URI-to-ISRC bridge. Deezer's public API is a separate promising artist/title-to-ISRC route, subject to terms and match-quality testing. Open-data matching (MusicBrainz/Wikidata and possibly the ListenBrainz mapper), user-supplied identifiers, and separately approved provider integrations remain options.

## Proposed local input and identity flow

1. Parse the user's Spotify Extended Streaming History files locally. Preserve track URI, displayed title/artist/album, timestamp and play-time evidence; aggregate weights with a user-visible rule still to be decided.
2. Search open recording sources using title, artist, and album/version clues; retain multiple candidates when ambiguous. Keep the original Spotify URI even if no enrichment match exists.
3. Use an independently supported MusicBrainz recording ID as an internal cross-source identifier only after matching. Retain ISRCs where a source supplies them, with provenance. Do not treat an ISRC from the source being scored as independent validation of that source's own resolution.
4. Compare artist/title versus independently obtained ISRC lookup in a later controlled run before making ISRC mandatory for users.

## Open tests

- How many export rows resolve to the intended recording with title/artist/album/version/duration clues, and how many remain ambiguous?
- Can a public URI-to-ISRC or URI-to-MBID bridge be found with sustainable rights and coverage? The documented export alone does not settle this.
- Does ISRC-first discovery materially improve source coverage or match correctness over title/artist for the 500-recording benchmark?
- Which Spotify export package(s) contain playlist membership? Extended Streaming History is suited to listening weights, not necessarily a user-selected playlist import.
