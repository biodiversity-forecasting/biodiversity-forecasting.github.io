"""Hentar publikasjonar frå Nasjonalt vitenarkiv (NVA) for prosjekta i site.yaml.

Publikasjonane vert henta kvar gong sida vert bygd (i GitHub Actions). Går ikkje NVA å nå,
vert sida bygd utan publikasjonslista i staden for å feila.
"""
import json
import urllib.parse
import urllib.request

API = "https://api.nva.unit.no/search/resources"

TYPE_LABELS = {
    "AcademicArticle": ("Vitskapleg artikkel", "Journal article"),
    "AcademicLiteratureReview": ("Oversiktsartikkel", "Review article"),
    "AcademicChapter": ("Bokkapittel", "Book chapter"),
    "AcademicMonograph": ("Bok", "Book"),
    "ReportResearch": ("Rapport", "Report"),
    "ReportPolicy": ("Rapport", "Report"),
    "ReportWorkingPaper": ("Arbeidsnotat", "Working paper"),
    "ConferenceLecture": ("Foredrag", "Talk"),
    "ConferencePoster": ("Poster", "Poster"),
    "Lecture": ("Foredrag", "Talk"),
    "DegreePhd": ("Doktoravhandling", "PhD thesis"),
    "DegreeMaster": ("Masteroppgåve", "Master's thesis"),
    "DataSet": ("Datasett", "Dataset"),
    "Map": ("Kart", "Map"),
    "MediaFeatureArticle": ("Formidling", "Outreach"),
    "MediaInterview": ("Formidling", "Outreach"),
    "MediaParticipationInRadioTv": ("Formidling", "Outreach"),
    "PopularScienceArticle": ("Populærvitskap", "Popular science"),
    "PopularScienceChapter": ("Populærvitskap", "Popular science"),
    "JournalLeader": ("Leiarartikkel", "Editorial"),
    "JournalLetter": ("Innlegg", "Letter"),
}


def _fetch(project_id):
    hits, url = [], f"{API}?{urllib.parse.urlencode({'project': project_id, 'results': 100})}"
    while url:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "cbf-website"})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.load(r)
        hits += page.get("hits", [])
        url = page.get("nextResults") if len(hits) < page.get("totalHits", 0) else None
    return hits


def _normalize(hit):
    e = hit.get("entityDescription", {})
    ref = e.get("reference", {}) or {}
    d = e.get("publicationDate", {}) or {}
    ptype = (ref.get("publicationInstance") or {}).get("type", "")
    ctx = ref.get("publicationContext") or {}
    contributors = sorted(e.get("contributors", []), key=lambda c: int(c.get("sequence") or 999))
    authors = [c["identity"]["name"] for c in contributors
               if c.get("identity", {}).get("name") and (c.get("role") or {}).get("type") in ("Creator", None, "")]
    if not authors:  # t.d. kart med «RightsHolder»
        authors = [c["identity"]["name"] for c in contributors if c.get("identity", {}).get("name")]
    handle = next((i["value"] for i in hit.get("additionalIdentifiers", [])
                   if i.get("type") == "HandleIdentifier"), None)
    doi = ref.get("doi")
    link = doi if doi and "doi.org" in doi else handle or doi or f"https://nva.sikt.no/registration/{hit.get('identifier')}"
    labels = TYPE_LABELS.get(ptype, ("Anna", "Other"))
    return {
        "id": hit.get("identifier"),
        "title": e.get("mainTitle", "").strip(),
        "year": int(d["year"]) if str(d.get("year", "")).isdigit() else None,
        "sortkey": (int(d.get("year") or 0), int(d.get("month") or 0), int(d.get("day") or 0)),
        "authors": authors,
        "venue": ctx.get("name") if ctx.get("type") in ("Journal", "UnconfirmedJournal", "Event", "Book", "Anthology") else None,
        "type": {"nn": labels[0], "en": labels[1]},
        "link": link,
    }


def load(projects, sample_file=None):
    """Returnerer publikasjonar sorterte med nyaste fyrst. Tom liste om ingen prosjekt er sette opp."""
    raw = []
    if sample_file:
        with open(sample_file, encoding="utf-8") as f:
            raw = json.load(f).get("hits", [])
    else:
        for pid in projects or []:
            try:
                raw += _fetch(str(pid))
            except Exception as err:  # nettverk eller API nede: byggjer vidare utan lista
                print(f"Åtvaring: fekk ikkje henta publikasjonar for NVA-prosjekt {pid}: {err}")
    seen, pubs = set(), []
    for h in raw:
        if h.get("status") != "PUBLISHED" or h.get("identifier") in seen:
            continue
        seen.add(h.get("identifier"))
        pubs.append(_normalize(h))
    pubs.sort(key=lambda p: p["sortkey"], reverse=True)
    return pubs
