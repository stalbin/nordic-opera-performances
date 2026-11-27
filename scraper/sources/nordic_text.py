"""Finland och Färöarna.

Finlands nationalopera har ett eget JSON-API. Övriga hus läses med en generell
metod: från en översiktssida följs länkarna till varje föreställningssida, och
där läses titeln (rubriken) och raderna som innehåller ett datum med år eller
klockslag (t.ex. "Perjantai 9.7.2027 klo 19:00", "Pe 11.6. klo 18", "04.12.26").
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common import Performance, clean, get_json, get_text, today_se
from datetext import find_dates

# --- Finlands nationalopera och -balett ------------------------------------

FNOB = "https://oopperabaletti.fi"


FNOB_LANGS = ("fi", "sv", "en")  # operan publicerar kalendern på finska, svenska och engelska


def _fnob_events(lang: str, start: str) -> list[dict]:
    events, page = [], 1
    while page <= 40:
        j = get_json(f"{FNOB}/wp-json/ooppera/events",
                     params={"perPage": 50, "page": page, "startDate": start, "hasMoreCheck": 1, "language": lang})
        events += j.get("events") or []
        if not j.get("hasMore"):
            break
        page += 1
    return events


def fetch_fnob() -> list[Performance]:
    start = today_se().isoformat()
    by_lang = {}
    for lang in FNOB_LANGS:
        try:
            by_lang[lang] = _fnob_events(lang, start)
        except Exception:
            if lang == "fi":
                raise
            by_lang[lang] = []
    return parse_fnob(by_lang["fi"], {k: v for k, v in by_lang.items() if k != "fi"})


def parse_fnob(events: list[dict], translations: dict[str, list[dict]] | None = None) -> list[Performance]:
    """events = finska versionen (originalet); translations = {"sv": [...], "en": [...]}.
    Samma föreställning har samma id och starttid på alla språk."""
    tr: dict[tuple, dict[str, dict]] = {}
    for lang, evs in (translations or {}).items():
        for e in evs:
            tr.setdefault((e.get("id"), (e.get("start_date") or "")[:16]), {})[lang] = e
    out = []
    for e in events:
        sd = e.get("start_date") or ""
        if not re.match(r"\d{4}-\d{2}-\d{2}", sd):
            continue
        st = (e.get("status") or "").lower()
        status = {"full": "utsalt", "some_left": "fa-biljetter", "cancelled": "installt"}.get(st, "")
        meta = e.get("meta") or ""
        genre = "Övrigt" if meta.lower().startswith("gratis") else meta  # "Opera", "Balett", "För barn", "Konsert" ...
        other = tr.get((e.get("id"), sd[:16]), {})
        versions = {"fi": e, **other}
        title_of = lambda x: x.get("title_override") or x.get("title")  # noqa: E731
        sv_meta = (other.get("sv") or {}).get("meta")  # genrer har svenska namn i den svenska versionen
        if sv_meta:
            meta = sv_meta
            genre = "Övrigt" if meta.lower().startswith("gratis") else meta
        out.append(Performance(
            titles={k: title_of(v) for k, v in versions.items()},
            urls={k: v.get("link") for k, v in versions.items()},
            venues={k: v.get("location") for k, v in versions.items()},
            house_id="suomen-kansallisooppera", title=clean(e.get("title_override") or e.get("title")),
            date=sd[:10], time=sd[11:16], genre=genre, venue=clean(e.get("location")), city="Helsingfors",
            url=e.get("link") or FNOB, ticket_url=e.get("buy_link") or e.get("link") or FNOB, status=status,
            id=f"suomen-kansallisooppera:{e.get('id')}:{sd[:16]}",
        ))
    return out


# --- Generell läsning av föreställningssidor -------------------------------

TICKET_HOSTS = r"lippu\.fi|tiketti\.fi|liveto\.io|ticketmaster\.|tix\.fo|billetlugen|nortic|tickster|billetto|ebillett"

# house_id: inställningar
TEXT_SOURCES = {
    "savonlinna": dict(index=["https://operafestival.fi/"], link=r"operafestival\.fi/ohjelmisto/[a-z0-9-]+/?$",
                       city="Savonlinna", venue="Olavinlinna", genre="Opera"),
    "tampereen-ooppera": dict(index=["https://www.tampere-talo.fi/tampereenooppera/"], link=r"tampere-talo\.fi/tapahtuma/[^/]+/?$",
                              city="Tampere", venue="Tampere-talo", genre="Opera", card_dates=True),
    "ilmajoki": dict(index=["https://www.musiikkijuhlat.fi/"], link=r"musiikkijuhlat\.fi/[a-z0-9_-]+\.html$",
                     city="Ilmajoki", venue="", genre="", exclude=r"/(varaa-liput|liput|lippuinfo|verkkokauppa|musiikkijuhlatverkkokauppa|ohjelmisto|muut_tapahtumat|info|saapuminen|katsomo"
                     r"|pieninvestointi|ryhmamatka|tarjoilut|ruokailu|majoitus|lahialueen|visit-|vuokraus|turvallisuus|ymparisto"
                     r"|yhteystiedot|hallitus|yhdistys|ajankohtaista|historia|media)[^/]*\.html$"),
    "helsingin-oopperakesa": dict(index=["https://www.oopperakesa.fi/"], link=r"oopperakesa\.fi/oopperakesa-\d{4}/[^/?#]+$",
                                  city="Helsingfors", venue="Aleksanterin teatteri", genre="Opera"),
    "oulun-ooppera": dict(index=["https://oulusinfonia.fi/konsertit/"], link=r"oulusinfonia\.fi/(?:en/)?konsertit/[^/]+/?$",
                          city="Uleåborg", venue="", genre="Opera", require=r"ooppera|opera"),
    "opera-fo": dict(index=["https://www.opera.fo/"], link=r"opera\.fo/[^#?]+$", city="Tórshavn", venue="", genre="Opera", lang="fo",
                     exclude=r"/(cart|account|search|contact|kontakt)"),
    "tjodpallur-opera": dict(index=["https://www.tjodpallur.fo/"], link=r"tjodpallur\.fo/leikir/[^/?#]+$", city="Tórshavn",
                             venue="Tjóðpallur Føroya", genre="Opera", require=r"ópera|opera|operu", lang="fo"),
}

MAX_PAGES = 30
# rader som innehåller datum men inte är speltillfällen (biljettsläpp, publiceringsdatum m.m.)
# "10.-20.6.2027" / "9.7. – 22.7.2027" = spelperiod, inte speldag
_PERIOD = re.compile(r"\d{1,2}\.(?:\d{1,2}\.)?\s*[-–]\s*\d{1,2}\.\d{1,2}\.")
_NOT_PERF = re.compile(r"myynti|alkaa|julkais|päivitetty|ilmoittau|salg|sale|published|updated|©|deadline|frist", re.I)


def _title(soup: BeautifulSoup) -> str:
    og = soup.find("meta", attrs={"property": "og:title"})
    t = clean(og["content"]) if og and og.get("content") else ""
    if not t:
        h1 = soup.find("h1")
        t = clean(h1.get_text()) if h1 else clean(soup.title.get_text() if soup.title else "")
    return re.split(r"\s+[|–—-]\s+", t)[0].strip()


def _lines(soup: BeautifulSoup) -> list[str]:
    for s in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        s.decompose()
    main = soup.select_one("main, article, #content, .site-main") or soup
    return [ln for ln in (re.sub(r"[ \t\xa0]+", " ", x).strip() for x in main.get_text("\n").split("\n")) if ln]


def _genre(default: str, text: str) -> str:
    t = text.lower()
    if default:
        return default
    if "ooppera" in t or "opera" in t:
        return "Opera"
    if "baletti" in t or "ballet" in t:
        return "Balett/dans"
    return "Konsert"


LANGS = ("sv", "en", "fi", "da", "nb", "nn", "no", "is", "fo")


def alternates(html: str, url: str) -> dict[str, str]:
    """Samma sida på andra språk: <link rel="alternate" hreflang="sv"> eller sidans språkväljare
    (en länk som /en/ohjelmisto/... när sidan själv är /ohjelmisto/...)."""
    soup = BeautifulSoup(html, "lxml")
    res = {}
    for l in soup.select("link[rel=alternate][hreflang]"):
        lang = l["hreflang"].split("-")[0].lower()
        if lang in LANGS and l.get("href") and l["href"].rstrip("/") != url.rstrip("/"):
            res[lang] = urljoin(url, l["href"])
    if res:
        return res
    m = re.match(r"(https?://[^/]+)/(?:(?:sv|en|fi|da|nb|no|is|fo)/)?([^/]+)/", url)
    if not m:
        return res
    host, section = m.group(1), m.group(2)
    for a in soup.select("a[href]"):
        href = urljoin(url, a["href"]).split("#")[0]
        mm = re.match(re.escape(host) + r"/(sv|en|fi|da|nb|no|is|fo)/" + re.escape(section) + r"/[^/?#]+/?$", href)
        if mm and mm.group(1) not in res:
            res[mm.group(1)] = href
    return res


def parse_event_page(html: str, url: str, house_id: str, cfg: dict, today=None, fallback_dates=None) -> list[Performance]:
    today = today or today_se()
    soup = BeautifulSoup(html, "lxml")
    title = _title(soup)
    ticket = next((a["href"] for a in soup.select("a[href]") if re.search(TICKET_HOSTS, a["href"], re.I)), url)
    lines = _lines(soup)
    full = " ".join(lines)
    if cfg.get("require") and not re.search(cfg["require"], full, re.I):
        return []
    yh = re.search(r"\b(20\d\d)\b", url + " " + full[:2000])
    year_hint = int(yh.group(1)) if yh else None
    found: dict[str, str] = {}
    for ln in lines:
        if len(ln) > 120 or _NOT_PERF.search(ln) or (_PERIOD.search(ln) and not re.search(r"\bkl|klo\b", ln, re.I)):
            continue  # löptext eller t.ex. "Lipunmyynti alkaa 1.12."; speldatum står på egna korta rader
        for d, t in find_dates(ln, today, year_hint):
            has_year = bool(re.search(r"\b20\d\d\b|\d{1,2}\.\d{1,2}\.\d{2}\b", ln))
            if t or has_year:
                if d not in found or (t and not found[d]):
                    found[d] = t
    if not found and fallback_dates:
        found = {d: "" for d in fallback_dates}
    status_txt = full.lower()
    return [Performance(house_id=house_id, title=title, date=d, time=t, genre=_genre(cfg.get("genre", ""), full[:3000]),
                        venue=cfg.get("venue", ""), city=cfg.get("city", ""), url=url, ticket_url=ticket,
                        status="installt" if "peruttu" in status_txt and len(found) == 1 else "")
            for d, t in sorted(found.items())]


def event_links(html: str, base: str, cfg: dict) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        href = urljoin(base, a["href"]).split("#")[0]
        if re.search(cfg["link"], href, re.I) and not (cfg.get("exclude") and re.search(cfg["exclude"], href, re.I)):
            if href.rstrip("/") not in (base.rstrip("/"),) and href not in links:
                links.append(href)
    return links[:MAX_PAGES]


def card_dates(html: str, today=None) -> dict[str, list[str]]:
    """Tampere-talo: datum som står på korten på översiktssidan (används om sidan själv saknar datum)."""
    today = today or today_se()
    soup = BeautifulSoup(html, "lxml")
    res: dict[str, list[str]] = {}
    for card in soup.select("article.event-card"):
        a = card.select_one("a[href]")
        t = card.select_one("time")
        if a and t:
            res[a["href"]] = [d for d, _ in find_dates(clean(t.get_text()), today)]
    return res


def fetch_text_house(house_id: str) -> list[Performance]:
    cfg = TEXT_SOURCES[house_id]
    out = []
    for index in cfg["index"]:
        html = get_text(index)
        fallback = card_dates(html) if cfg.get("card_dates") else {}
        base_lang = cfg.get("lang", "fi")
        for url in event_links(html, index, cfg):
            try:
                page = get_text(url)
                perfs = parse_event_page(page, url, house_id, cfg, fallback_dates=fallback.get(url))
                if perfs:
                    titles, urls = {base_lang: perfs[0].title}, {base_lang: url}
                    for lang, alt in alternates(page, url).items():
                        try:
                            t = _title(BeautifulSoup(get_text(alt), "lxml"))
                        except Exception:
                            continue
                        if t:
                            titles[lang], urls[lang] = t, alt
                    for p in perfs:
                        p.titles, p.urls = dict(titles), dict(urls)
                out += perfs
            except Exception as e:
                print(f"  [varning] {house_id}: {url}: {e}")
    seen, uniq = set(), []
    for p in out:
        k = (p.title.lower(), p.date, p.time)
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq
