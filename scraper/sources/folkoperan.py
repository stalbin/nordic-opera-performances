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
    return parse(get_text(LIST_URL))


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
