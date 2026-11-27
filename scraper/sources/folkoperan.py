"""Folkoperan – sidan "Köp biljetter" listar alla föreställningar som har
biljettsläpp (rubrik, datum, tid och biljettlänk)."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from common import Performance, get_text, month_from_sv, clean

HOUSE = "folkoperan"
BASE = "https://folkoperan.se"
LIST_URL = f"{BASE}/kop-biljetter/"

_DATE_RE = re.compile(r"(\d{1,2})\s+([a-zåäö]+)\s+(\d{4})", re.I)
_TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})")
_NOTE_RE = re.compile(r"\s+(PREMIÄR|URPREMIÄR|SVENSK PREMIÄR|SISTA FÖRESTÄLLNINGEN|UTSÅLT|INSTÄLLD)\s*$", re.I)


def fetch() -> list[Performance]:
    perfs = parse(get_text(LIST_URL))
    try:
        pages = production_pages(get_text(BASE + "/"))
    except Exception:
        pages = {}
    for p in perfs:
        p.url = match_page(p.title, pages) or LIST_URL
    return perfs


def _norm(s: str) -> str:
    return re.sub(r"[^a-zåäö0-9]+", " ", s.lower()).strip()


def production_pages(html: str) -> dict[str, str]:
    """Uppsättningssidor (/uppsattningar/<namn>/) med sin länktext."""
    soup = BeautifulSoup(html, "lxml")
    out: dict[str, str] = {}
    for a in soup.select('a[href*="/uppsattningar/"]'):
        href = a["href"]
        if href.startswith("/"):
            href = BASE + href
        if not re.search(r"/uppsattningar/[^/]+/?$", href):
            continue
        txt = _norm(a.get_text(" "))
        if txt:
            out.setdefault(txt, href)
        slug = re.search(r"/uppsattningar/([^/]+)", href).group(1)
        out.setdefault(_norm(slug.replace("-", " ")), href)
    return out


def match_page(title: str, pages: dict[str, str]) -> str:
    t = _norm(title)
    if not t:
        return ""
    if t in pages:
        return pages[t]
    for txt, href in pages.items():
        if len(txt) >= 4 and (txt.startswith(t) or t.startswith(txt) or f" {t} " in f" {txt} "):
            return href
    return ""


def _genre(title: str) -> str:
    t = title.lower()
    if "foajé" in t or "konsert" in t or "gala" in t or "live" in t or "sjunger" in t:
        return "Konsert"
    if "unga" in t or "barn" in t:
        return "Barn & unga"
    return "Opera"  # Folkoperans huvudscen spelar i första hand opera


def parse(html: str) -> list[Performance]:
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for li in soup.select("li.c-event-list__item"):
        h3, h4 = li.select_one("h3"), li.select_one("h4")
        if not h3 or not h4:
            continue
        m = _DATE_RE.search(clean(h4.get_text()))
        if not m:
            continue
        mon = month_from_sv(m.group(2))
        if not mon:
            continue
        date = f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(1)):02d}"
        time_el = li.select_one(".u-small-text")
        tm = _TIME_RE.search(clean(time_el.get_text())) if time_el else None
        time = f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else ""
        title = clean(h3.get_text())
        note = ""
        nm = _NOTE_RE.search(title)
        if nm:
            note = nm.group(1).capitalize()
            title = title[:nm.start()].strip()
        a = li.select_one("a[href]")
        ticket = a["href"] if a else ""
        key = ticket or f"{title}{date}{time}"
        if key in seen:
            continue
        seen.add(key)
        txt = clean(li.get_text()).lower()
        status = "utsalt" if "utsålt" in txt else ("installt" if "inställ" in txt else "")
        out.append(Performance(
            house_id=HOUSE, title=title, date=date, time=time, genre=_genre(title),
            venue="Folkoperan", city="Stockholm", url=LIST_URL, ticket_url=ticket,
            status=status, note=note if note.lower() not in ("utsålt", "inställd") else "",
        ))
    return out
