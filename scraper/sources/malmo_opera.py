"""Malmö Opera – startsidans kalendervy (Drupal) sidindelas med ?page=N.
Samma sidor innehåller också föreställningskorten med genre, som vi använder
för att ge varje kalenderrad rätt genre."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from common import Performance, get_text, month_from_sv, clean

HOUSE = "malmo-opera"
BASE = "https://www.malmoopera.se"
MAX_PAGES = 120

_TAG_RE = re.compile(r"(\d{1,2})\s+([a-zåäö]+)\.?\s+(\d{1,2})[.:](\d{2})", re.I)
_MONTH_HDR_RE = re.compile(r"([a-zåäö]+)\s+(\d{4})", re.I)


def fetch() -> list[Performance]:
    genres: dict[str, str] = {}
    pages = []
    year = None
    for n in range(MAX_PAGES):
        html = get_text(f"{BASE}/?page={n}")
        soup = BeautifulSoup(html, "lxml")
        genres.update(parse_genres(soup))
        rows, year = parse_calendar(soup, year)
        if not rows:
            break
        pages.append(rows)
    out = []
    for rows in pages:
        for p in rows:
            slug = p.url.rsplit("/", 1)[-1]
            p.genre = genres.get(slug, p.genre)
            out.append(p)
    missing = {p.url for p in out if not p.genre}
    for url in missing:  # fallback: läs genren från föreställningssidan
        g = genre_from_page(url)
        for p in out:
            if p.url == url:
                p.genre = g
    return out


def parse_genres(soup: BeautifulSoup) -> dict[str, str]:
    res = {}
    for art in soup.select("article.node a[href^='/forestallningar/']"):
        tag = art.select_one(".tag")
        if tag:
            res[art["href"].rsplit("/", 1)[-1]] = clean(tag.get_text())
    return res


def genre_from_page(url: str) -> str:
    try:
        soup = BeautifulSoup(get_text(url), "lxml")
    except Exception:
        return ""
    for t in soup.select(".tag"):
        txt = clean(t.get_text())
        if txt.lower() in ("opera", "musikal", "konsert", "barn och familj", "dans", "balett"):
            return txt
    return ""


def parse_calendar(soup: BeautifulSoup, year: int | None = None) -> tuple[list[Performance], int | None]:
    """Returnerar (föreställningar, senast sedda år) så att året kan följa med till nästa sida."""
    cal = soup.select_one(".mo-instances__calendar")
    if not cal:
        return [], year
    out = []
    for el in cal.find_all("div", recursive=False):
        classes = el.get("class") or []
        if "mo-instance" not in classes:
            m = _MONTH_HDR_RE.search(clean(el.get_text()))
            if m:
                year = int(m.group(2))
            continue
        tag = el.select_one(".tag")
        link = el.select_one("a[href^='/forestallningar/']")
        if not tag or not link or not year:
            continue
        m = _TAG_RE.search(clean(tag.get_text()))
        if not m:
            continue
        day, mon, hh, mm = int(m.group(1)), month_from_sv(m.group(2)), m.group(3), m.group(4)
        if not mon:
            continue
        avail = el.select_one("[class*='availability__']")
        avail_cls = " ".join(avail.get("class", [])) if avail else ""
        avail_txt = clean(el.get_text()).lower()
        if "utsålt" in avail_txt or "soldout" in avail_cls or "sold-out" in avail_cls:
            status = "utsalt"
        elif "inställ" in avail_txt:
            status = "installt"
        elif "få " in avail_txt or "few" in avail_cls:
            status = "fa-biljetter"
        else:
            status = ""
        buy = el.select_one("a.buy-button")
        out.append(Performance(
            house_id=HOUSE, title=link.get_text(), date=f"{year:04d}-{mon:02d}-{day:02d}",
            time=f"{int(hh):02d}:{mm}", genre="", venue="Malmö Opera", city="Malmö",
            url=BASE + link["href"], ticket_url=buy["href"] if buy else "",
            status=status,
            id=f"{HOUSE}:{el.get('data-instance-id', '')}" if el.get("data-instance-id") else "",
        ))
    return out, year
