"""Wermland Opera – kalendariet har en <article class="calendar__event"> per
föreställning med datum/tid (time[datetime]), plats, kategori och biljettlänk."""
from __future__ import annotations

from bs4 import BeautifulSoup

from common import Performance, get_text, clean

HOUSE = "wermland-opera"
URL = "https://www.wermlandopera.com/kalendarium/"


def fetch() -> list[Performance]:
    return parse(get_text(URL))


def parse(html: str) -> list[Performance]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for art in soup.select("article.calendar__event"):
        t = art.select_one("time[datetime]")
        title_a = art.select_one(".calendar__event-title a") or art.select_one("a[href*='/evenemang/']")
        if not t or not title_a:
            continue
        dt = t["datetime"]
        date, _, time = dt.partition("T")
        place = art.select_one(".calendar__event-place")
        cat = art.select_one(".calendar__event-category")
        ticket = art.select_one("a.calendar__button--tickets")
        place_txt = clean(place.get_text()) if place else ""
        cat_txt = clean(cat.get_text()) if cat else ""
        on_tour = "turné" in place_txt.lower() or "turné" in cat_txt.lower()
        txt = clean(art.get_text()).lower()
        status = "utsalt" if "utsålt" in txt else ("installt" if "inställ" in txt else "")
        out.append(Performance(
            house_id=HOUSE, title=title_a.get_text(), date=date, time=time[:5],
            genre="" if on_tour else cat_txt, venue=place_txt,
            city="" if on_tour else "Karlstad", url=title_a["href"],
            ticket_url=ticket["href"] if ticket else "", status=status,
        ))
    return out
