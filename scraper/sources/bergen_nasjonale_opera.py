"""Bergen Nasjonale Opera – programsidan listar produktionerna. Varje
produktionssida har antingen en tabell med alla speldatum ("Samtlige
spilledatoer") eller bara löptext ("Premiere lørdag 13. mars 2027 kl. 18
Spilles også 15., 17. og 18. mars kl. 19"). Båda varianterna tolkas; finns
inget av det används spelperioden från programsidan."""
from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from common import Performance, get_text, month_from_sv, clean, today_se

HOUSE = "bergen-nasjonale-opera"
BASE = "https://www.bno.no"
PROGRAM_URL = f"{BASE}/program"

_MONTHS = r"(januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|desember)"
# "13. mars 2027 kl. 18" / "23. januar kl. 14"
_PREMIERE_RE = re.compile(r"(\d{1,2})\.\s*" + _MONTHS + r"(?:\s+(\d{4}))?\s+kl\.?\s*(\d{1,2})(?:[.:](\d{2}))?", re.I)
# "Spilles også 15., 17. og 18. mars kl. 19" / "Spelast også 25. januar kl. 18 og 30. januar kl. 14"
_ALSO_RE = re.compile(r"(?:spilles|spelast|spilt)\s+også\s+(.+?)(?:\n|$)", re.I)
_DAYLIST_RE = re.compile(r"((?:\d{1,2}\.,?\s*(?:og\s+)?)+)" + _MONTHS + r"(?:\s+(\d{4}))?(?:\s+kl\.?\s*(\d{1,2})(?:[.:](\d{2}))?)?", re.I)
_PERIOD_RE = re.compile(r"(\d{1,2})/(\d{1,2})(?:\s*-\s*(\d{1,2})/(\d{1,2}))?|(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})")


def _year_for(month: int, day: int, today: date) -> int:
    """Datum utan år: välj närmaste kommande (eller dagens) datum."""
    y = today.year
    try:
        return y if date(y, month, day) >= today else y + 1
    except ValueError:
        return y


def _iso(y: int, m: int, d: int) -> str:
    return f"{y:04d}-{m:02d}-{d:02d}"


def fetch() -> list[Performance]:
    from nordic_text import alternates, _title  # samma språkväljar-logik som för de finska husen
    soup = BeautifulSoup(get_text(PROGRAM_URL), "lxml")
    out = []
    for prod in parse_program(soup):
        try:
            html = get_text(prod["url"])
        except Exception:
            html = ""
        perfs = parse_production(html, prod)
        en_url = alternates(html, prod["url"]).get("en") if html else None
        if en_url and perfs:
            try:
                en_title = _title(BeautifulSoup(get_text(en_url), "lxml"))
            except Exception:
                en_title = ""
            for p in perfs:
                p.titles = {"nb": p.title, "en": en_title}
                p.urls = {"nb": prod["url"], "en": en_url if en_title else ""}
        out += perfs
    return out


def parse_program(soup: BeautifulSoup) -> list[dict]:
    res = []
    for art in soup.select("article.performance"):
        h2 = art.select_one("h2")
        link = art.select_one("a[href*='/forestillinger/']")
        if not h2 or not link:
            continue
        period = clean(art.select_one(".body > span").get_text()) if art.select_one(".body > span") else ""
        ticket = art.select_one("a.ticket")
        res.append({"title": clean(h2.get_text()), "url": link["href"], "period": period,
                    "ticket": ticket["href"] if ticket else ""})
    return res


def parse_production(html: str, prod: dict, today: date | None = None) -> list[Performance]:
    today = today or today_se()
    soup = BeautifulSoup(html or "<html></html>", "lxml")
    title = prod["title"]
    genre = "Opera"
    if "konsert" in title.lower() or "singalong" in title.lower() or "pub" in title.lower():
        genre = "Konsert"

    def perf(d: str, t: str = "", venue: str = "", ticket: str = "", note: str = "") -> Performance:
        return Performance(house_id=HOUSE, title=title, date=d, time=t, genre=genre, venue=venue,
                           city="" if "operaen" in venue.lower() else "Bergen", url=prod["url"],
                           ticket_url=ticket or prod["ticket"] or prod["url"], note=note)

    # 1) Tabell med alla speldatum
    rows = soup.select(".table-row")
    out = []
    for r in rows:
        dt, tm = r.select_one(".date"), r.select_one(".time")
        if not dt:
            continue
        m = re.match(r"(\d{1,2})/(\d{1,2})", clean(dt.get_text()))
        if not m:
            continue
        day, mon = int(m.group(1)), int(m.group(2))
        t = clean(tm.get_text()).replace(".", ":") if tm else ""
        venue = clean(r.select_one(".venue").get_text()) if r.select_one(".venue") else ""
        a = r.select_one("a[href]")
        out.append(perf(_iso(_year_for(mon, day, today), mon, day), t, venue, a["href"] if a else ""))
    if out:
        return out

    # 2) Löptext: "Premiere ... kl. 18 Spilles også 15., 17. og 18. mars kl. 19"
    for s in soup(["script", "style"]):
        s.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    venue_m = re.search(r"Sted\s*\n?\s*([^\n]+)", text)
    venue = clean(venue_m.group(1)) if venue_m else ""
    found: dict[str, str] = {}
    pm = re.search(r"Premiere[^\n]{0,40}?" + _PREMIERE_RE.pattern, text, re.I)
    year_hint = None
    if pm:
        g = pm.groups()
        mon = month_from_sv(g[1])
        year_hint = int(g[2]) if g[2] else None
        y = year_hint or _year_for(mon, int(g[0]), today)
        found[_iso(y, mon, int(g[0]))] = f"{int(g[3]):02d}:{g[4] or '00'}"
    for also in _ALSO_RE.finditer(text):
        for dm in _DAYLIST_RE.finditer(also.group(1)):
            days = [int(x) for x in re.findall(r"\d{1,2}", dm.group(1))]
            mon = month_from_sv(dm.group(2))
            hh, mm = dm.group(4), dm.group(5)
            for dd in days:
                y = int(dm.group(3)) if dm.group(3) else (year_hint or _year_for(mon, dd, today))
                found.setdefault(_iso(y, mon, dd), f"{int(hh):02d}:{mm or '00'}" if hh else "")
    if found:
        notes = {min(found): "premiere"} if pm else {}
        return [perf(d, t, venue, note=notes.get(d, "")) for d, t in sorted(found.items())]

    # 3) Bara spelperiod på programsidan ("09/12", "23-30/01", "13-18/03")
    p = prod.get("period", "")
    m = re.search(r"(\d{1,2})(?:\s*-\s*(\d{1,2}))?/(\d{1,2})", p)
    if not m:
        return []
    start, end, mon = int(m.group(1)), int(m.group(2) or m.group(1)), int(m.group(3))
    y = _year_for(mon, end, today)
    note = "" if start == end else f"period:{start}–{end}/{mon}"  # appen visar t.ex. "Spelas 13–18/3"
    return [perf(_iso(y, mon, start), venue=venue, note=note)]
