"""Sommaroperor och distriktsoperor i Danmark och Norge.

Dessa har inga kalendrar med strukturerad data, så datumen läses ur texten på
webbplatsen med datetext.find_dates(). Före biljettsläppet står ofta inga
datum alls – då blir det 0 föreställningar tills de dyker upp.
"""
from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from common import Performance, clean, get_text, today_se
from datetext import find_dates


def page_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style", "noscript", "nav", "footer"]):
        s.decompose()
    txt = soup.get_text("\n")
    return [ln for ln in (re.sub(r"[ \t\xa0]+", " ", x).strip() for x in txt.split("\n")) if ln]


def _year_in(text: str) -> int | None:
    m = re.search(r"\b(20\d\d)\b", text)
    return int(m.group(1)) if m else None


def _first_link(html: str, pattern: str) -> str:
    m = re.search(r'https?://[^"\'\s<>]*(?:' + pattern + r')[^"\'\s<>]*', html, re.I)
    return m.group(0).replace("&amp;", "&") if m else ""


# --- Opera Hedeland ---------------------------------------------------------

HEDELAND = "https://operahedeland.dk/"


def fetch_hedeland() -> list[Performance]:
    html = get_text(HEDELAND)
    return parse_hedeland(html)


def parse_hedeland(html: str, today=None) -> list[Performance]:
    """Startsidan: 'Verdis "Falstaff" den 7., 13. og 14. august 2027'."""
    today = today or today_se()
    ticket = _first_link(html, r"ticketmaster\.")
    out = []
    for ln in page_lines(html):
        dates = find_dates(ln, today)
        if not dates or len(ln) > 160:
            continue
        q = re.search(r'["“”«»]([^"“”«»]{2,60})["“”«»]', ln)
        title = q.group(1) if q else clean(re.split(r"\s+den\s+\d", ln)[0])
        if not title or re.match(r"^\d", title):
            continue
        for d, t in dates:
            out.append(Performance(house_id="opera-hedeland", title=title, date=d, time=t or "20:00",
                                   genre="Opera", venue="Opera Hedeland", city="Hedehusene",
                                   url=HEDELAND, ticket_url=ticket or HEDELAND))
    return out


# --- Copenhagen Opera Festival ----------------------------------------------

CPH = "https://www.operafestival.dk/"
_PURE_DATE = re.compile(r"^(?:(?:man|tirs|ons|tors|fre|lør|søn)dag\s+)?[\d.\s,–\-og]+[a-zæøå.]+(?:\s+\d{4})?(?:\s*(?:kl\.?)\s*[\d.:]+)?$", re.I)


def fetch_cph() -> list[Performance]:
    t = today_se()
    pages = [CPH] + [f"{CPH}program-{y}/" for y in (t.year, t.year + 1)]
    out, seen = [], set()
    for url in pages:
        try:
            html = get_text(url)
        except Exception:
            if url == CPH:
                raise
            continue
        for p in parse_cph(html, url):
            if (p.title, p.date) not in seen:
                seen.add((p.title, p.date))
                out.append(p)
    return out


def parse_cph(html: str, url: str, today=None) -> list[Performance]:
    """Titelrad följd av en rad som bara är ett datum: 'DADA: X' / '19. - 20. august 2027'."""
    today = today or today_se()
    lines = page_lines(html)
    year_hint = _year_in(" ".join(lines[:40]))
    out = []
    for i, ln in enumerate(lines):
        if len(ln) > 60 or not _PURE_DATE.match(ln):
            continue
        dates = find_dates(ln, today, year_hint)
        if not dates:
            continue
        title = next((lines[j] for j in range(i - 1, max(-1, i - 4), -1)
                      if 2 < len(lines[j]) <= 80 and not find_dates(lines[j], today) and not re.fullmatch(r"\d{4}", lines[j])), "")
        if not title:
            continue
        for d, t in dates:
            out.append(Performance(house_id="cph-opera-festival", title=title, date=d, time=t, genre="Opera",
                                   venue="", city="København", url=url, ticket_url=url))
    return out


# --- Oscarsborgoperaen -------------------------------------------------------

OSCARSBORG = "https://www.oscarsborgoperaen.no"


def fetch_oscarsborg() -> list[Performance]:
    posts = json.loads(get_text(f"{OSCARSBORG}/wp-json/wp/v2/posts",
                                params={"per_page": 15, "_fields": "title,link,content"}))
    out = []
    for p in posts:
        out += parse_oscarsborg_post(clean((p.get("title") or {}).get("rendered")), p.get("link", ""),
                                     (p.get("content") or {}).get("rendered", ""))
    try:
        out += parse_oscarsborg_program(get_text(f"{OSCARSBORG}/festivalprogram/"))
    except Exception:
        pass
    seen, uniq = set(), []
    for p in out:
        if (p.title.lower(), p.date) not in seen:
            seen.add((p.title.lower(), p.date))
            uniq.append(p)
    return uniq


def parse_oscarsborg_post(title: str, link: str, html: str, today=None) -> list[Performance]:
    """Inlägg som 'Turandot 2027' med '13.08.27 kl. 20.00 Premiere / 15-16. august kl. 20.00'."""
    today = today or today_se()
    year = _year_in(title)
    if not year:
        return []
    lines = page_lines(html)
    out = []
    for ln in lines:
        for d, t in find_dates(ln, today, year):
            if not d.startswith(str(year)):
                continue
            out.append(Performance(house_id="oscarsborgoperaen", title=re.sub(r"\s*20\d\d\s*$", "", title),
                                   date=d, time=t, genre="Opera", venue="Oscarsborg festning", city="Drøbak",
                                   url=link, ticket_url=_first_link(html, r"ticketmaster\.") or link,
                                   note="premiere" if "premiere" in ln.lower() else ""))
    return out


def parse_oscarsborg_program(html: str, today=None) -> list[Performance]:
    """Festivalprogrammet: en datumrad ('2.-4. august') följd av titeln ('Musica in Castello')."""
    today = today or today_se()
    lines = page_lines(html)
    year = _year_in(" ".join(lines[:20]))
    out = []
    for i, ln in enumerate(lines[:-1]):
        if len(ln) > 40:
            continue
        dates = find_dates(ln, today, year)
        if not dates:
            continue
        title = re.sub(r"\s*Les mer\s*$", "", lines[i + 1]).strip()
        if not title or find_dates(title, today):
            continue
        for d, t in dates:
            out.append(Performance(house_id="oscarsborgoperaen", title=title, date=d, time=t,
                                   genre="Opera", venue="Oscarsborg festning", city="Drøbak",
                                   url=f"{OSCARSBORG}/festivalprogram/", ticket_url=f"{OSCARSBORG}/festivalprogram/"))
    return out


# --- Opera Trøndelag (Steinvikholm) -----------------------------------------

TRONDELAG = "https://www.operatrondelag.no/"


def fetch_trondelag() -> list[Performance]:
    return parse_trondelag(get_text(TRONDELAG))


def parse_trondelag(html: str, today=None) -> list[Performance]:
    """Startsidans lista: titel, datum som 22/04 | 24/04, biljettlänk."""
    today = today or today_se()
    soup = BeautifulSoup(html, "lxml")
    out = []
    for card in soup.select("[data-elementor-type='jet-listing-items']"):
        a = card.select_one("a.jet-listing-dynamic-link__link")
        dates_el = card.select_one(".fdates") or card
        if not a:
            continue
        raw_title = clean(a.get_text())
        status = "utsalt" if re.match(r"utsolgt", raw_title, re.I) else ""
        title = re.sub(r"^(utsolgt|få billetter|nyhet)\s*:\s*", "", raw_title, flags=re.I)
        ticket = next((x["href"] for x in card.select("a[href]") if "operatrondelag.no" not in x["href"]), a["href"])
        low = title.lower()
        genre = "Konsert" if any(w in low for w in ("konsert", "pub", "gala")) else "Opera"
        for d, t in find_dates(" | ".join(dates_el.stripped_strings), today):
            venue = "Steinvikholm" if "steinvik" in clean(card.get_text()).lower() else ""
            out.append(Performance(house_id="opera-trondelag", title=title, date=d, time=t, genre=genre,
                                   venue=venue, city="", url=a["href"], ticket_url=ticket, status=status))
    return out


# --- Ringsakeroperaen --------------------------------------------------------

RINGSAKER = "https://www.ringsakeroperaen.no/"


def fetch_ringsaker() -> list[Performance]:
    return parse_ringsaker(get_text(RINGSAKER))


def parse_ringsaker(html: str, today=None) -> list[Performance]:
    """Startsidans block 'Kommende arrangementer' – en länk per arrangemang med datum i texten."""
    today = today or today_se()
    soup = BeautifulSoup(html, "lxml")
    block = soup.select_one(".block-upcoming-events")
    if not block:
        return []
    out = []
    for a in block.select("a[href*='/begivenhet/']"):
        card = a
        for _ in range(4):
            if card.parent is not None and len(clean(card.parent.get_text(" "))) < 400:
                card = card.parent
        text = " \n ".join(card.stripped_strings)
        title = clean(a.get_text()) or clean(card.find(["h2", "h3", "h4"]).get_text() if card.find(["h2", "h3", "h4"]) else "")
        if not title or title.lower() in ("les mer", "billetter"):
            h = card.find(["h2", "h3", "h4"])
            title = clean(h.get_text()) if h else ""
        if not title:
            continue
        low = title.lower()
        genre = "Konsert" if "konsert" in low else "Opera"
        for d, t in find_dates(text, today):
            out.append(Performance(house_id="ringsakeroperaen", title=title, date=d, time=t, genre=genre,
                                   venue="", city="", url=a["href"], ticket_url=a["href"]))
    # samma arrangemang kan ha flera länkar i kortet
    seen, uniq = set(), []
    for p in out:
        if (p.title, p.date) not in seen:
            seen.add((p.title, p.date))
            uniq.append(p)
    return uniq


# --- Opera Nordfjord (Operahuset Nordfjord) ---------------------------------

NORDFJORD = "https://operahuset.no/program/"


def fetch_nordfjord() -> list[Performance]:
    html = get_text(NORDFJORD)
    cards = parse_nordfjord_cards(html)
    out = []
    # Operahuset har även kino och gästspel; bara Opera Nordfjords egna uppsättningar tas med.
    checked: dict[str, bool] = {}
    for c in cards:
        url = c["url"]
        if url not in checked:
            try:
                checked[url] = is_opera_nordfjord_page(get_text(url))
            except Exception:
                checked[url] = False
        if checked[url]:
            out += c["perfs"]
    return out


def is_opera_nordfjord_page(html: str) -> bool:
    """Står Opera Nordfjord som arrangör i själva sidinnehållet (inte bara i sidhuvud/sidfot)?"""
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style", "header", "footer", "nav"]):
        s.decompose()
    main = soup.select_one("main, article, .site-main, #content") or soup
    return "opera nordfjord" in clean(main.get_text(" ")).lower()


def parse_nordfjord_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    res = []
    for card in soup.select(".elementor-post__excerpt"):
        if card.select_one(".movie-info"):
            continue  # kino
        link = card.select_one("a[href*='operahuset.no/']")
        title_el = card.select_one(".movie-title a, h3 a, h2 a, h3, h2") or link
        if not link or not title_el:
            continue
        title = clean(title_el.get_text())
        perfs = []
        for show in card.select(".show"):
            dt = show.select_one("date[datetime]")
            if not dt:
                continue
            d, _, tm = dt["datetime"].partition(" ")
            loc = show.select_one(".show-location")
            buy = show.select_one("a.show-purchase")
            txt = clean(show.get_text()).lower()
            perfs.append(Performance(house_id="opera-nordfjord", title=title, date=d, time=tm[:5], genre="Opera",
                                     venue=clean(loc.get_text()) if loc else "Operahuset Nordfjord", city="Nordfjordeid",
                                     url=link["href"], ticket_url=buy["href"] if buy else link["href"],
                                     status="utsalt" if "utselt" in txt or "utsolgt" in txt else ""))
        if perfs:
            res.append({"url": link["href"], "perfs": perfs})
    return res
