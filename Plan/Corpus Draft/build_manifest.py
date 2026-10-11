"""Combine provisional nominations into a reviewable TSV; never queries sources."""

from collections import Counter
from pathlib import Path
import csv


ROOT = Path(__file__).parent
EVIDENCE = {
    ("Orquestra Típica Pixinguinha-Donga", "Carinhoso (Instrumental)"): "https://radiobatuta.ims.com.br/programas/ouve-essa/carinhoso",
    ("Orlando Silva", "Carinhoso"): "https://pixinguinha.com.br/discografia/carinhoso-2/",
    ("Carmen Miranda", "Ta-hi"): "https://artsandculture.google.com/asset/ta-h%C3%AD-pra-voc%C3%AA-gostar-de-mim-carmenmiranda-fc/zgF-gFn8O2PFow?hl=pt-BR",
    ("Sydney Simpson and His Wentworth Cafe Orchestra", "Freshie"): "https://www.nfsa.gov.au/sites/default/files/08-2017/sounds_of_australia_2017_short_list_-_briefing_notes.pdf",
    ("Peter Dawson", "Along the Road to Gundagai"): "https://www.nfsa.gov.au/collection/item/along-road-gundagai-0",
    ("Len Maurice", "Our Don Bradman"): "https://www.nfsa.gov.au/sites/default/files/08-2017/sounds_of_australia_2017_short_list_-_briefing_notes.pdf",
    ("Jack Lumsdaine", "Phar Lap: Farewell to You!"): "https://www.nfsa.gov.au/sites/default/files/08-2017/sounds_of_australia_2017_short_list_-_briefing_notes.pdf",
    ("Joy King", "The Aeroplane Jelly Song"): "https://www.nfsa.gov.au/collection/item/aeroplane-jelly-song-joy-king",
    ("Astor Piazzolla", "El desbande"): "https://inamu.musica.ar/primeravida-piazzolla",
    ("The Kumasi Trio", "Amponsah Part 1"): "https://afrodisc.com/west-africa/west-africa-zonophone/west-africa-zonophone-label-history-gallery/",
    ("Griffiths Motsieloa and Company", "Nkosi Sikelela i Afrika"): "https://www.flatinternational.org/template_volume.php?volume_id=269",
    ("City Deep Natives", "Uyeza"): "https://www.flatinternational.org/template_volume.php?volume_id=289",
    ("Caluza's Double Quartet", "Ixegwana"): "https://www.flatinternational.org/template_volume.php?volume_id=393",
    ("Siti binti Saad", "Kijiti"): "https://verbafricana.org/swahili/b-kijiti-author-and-context.htm",
    ("Madhumalati and Sneha Dhopeshwarkar", "Mangalagaur Arati"): "https://folkways.si.edu/madhumalati-and-sneha-dhopeshwarkar/marathi-songs-from-the-arnold-bake-collection/india-world/music/album/smithsonian",
    ("Noriko Awaya", "Wakare no Blues"): "https://soas-repository.worktribe.com/OutputFile/334446",
    ("Hibari Misora", "Kappa Boogie Woogie"): "https://columbia.jp/artist-info/hibari/discography/COCP-33949-50.html",
    ("Namiki Michiko", "Ringo no Uta"): "https://panasonic.net/history/timecapsule/3/art/A_4.html",
    ("Sabrina Carpenter", "Manchild"): "https://www.officialcharts.com/songs/sabrina-carpenter-manchild/",
    ("Chappell Roan", "The Subway"): "https://www.officialcharts.com/songs/chappell-roan-the-subway/",
    ("Bad Bunny", "DtMF"): "https://www.officialcharts.com/songs/bad-bunny-dtmf/",
    ("Hugh Masekela", "The Boy's Doin' It"): "https://hughmasekela.co.za/discography/",
    ("Miriam Makeba", "Soweto Blues"): "https://www.kvs.be/upload/media/default/deaf/45/86dba55157be619768fa8b847ca8ad630918fd3d.pdf",
    ("Salif Keita", "Soro (Afriki)"): "https://www.afrisson.com/soro-11039/",
}


def in_era(index: int, year: int) -> bool:
    bounds = [(0, 1949), (1950, 1969), (1970, 1989), (1990, 2009), (2010, 2026)]
    low, high = bounds[index - 1]
    return low <= year <= high


def main() -> None:
    rows: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    for index in range(1, 6):
        cohort_counts: Counter[str] = Counter()
        for line in (ROOT / f"era{index}.txt").read_text().splitlines():
            fields = line.split("|")
            cohort = "hard" if fields[0] == "HARD" else "general"
            if cohort == "hard":
                fields = fields[1:]
            if len(fields) != 5:
                raise ValueError(f"Era {index}: malformed row: {line}")
            artist, title, year, origin, genre = fields
            if not in_era(index, int(year)):
                raise ValueError(f"Era {index}: year outside range: {line}")
            key = (artist.casefold(), title.casefold())
            if key in seen:
                raise ValueError(f"Duplicate artist/title: {key}")
            seen.add(key)
            url = EVIDENCE.get((artist, title), "")
            rows.append([
                f"MGG-{len(rows) + 1:03}", f"E{index}", cohort, artist,
                title, year, origin, genre, "curated_preliminary", url,
                "evidence_linked_version_pending" if url else "needs_independent_evidence",
            ])
            cohort_counts[cohort] += 1
        if cohort_counts != {"general": 90, "hard": 10}:
            raise ValueError(f"Era {index}: wrong allocation: {cohort_counts}")
    if len(rows) != 500:
        raise ValueError(f"Expected 500 rows, got {len(rows)}")
    with (ROOT / "500-recording-candidates.tsv").open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow([
            "candidate_id", "era", "cohort", "artist_hint", "title_hint",
            "year_hint", "origin_hint", "genre_hint", "nomination_route",
            "independent_evidence_url", "status",
        ])
        writer.writerows(rows)
    print(f"{len(rows)} provisional rows; {sum(bool(row[9]) for row in rows)} evidence links")
    for index in range(1, 6):
        subset = [row for row in rows if row[1] == f"E{index}"]
        countries = Counter(row[6] for row in subset)
        print(f"E{index}: {len(countries)} country hints; US {countries['United States']}; UK {countries['United Kingdom']}")


if __name__ == "__main__":
    main()
