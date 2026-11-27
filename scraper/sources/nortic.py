"""Mindre operor som säljer biljetter via Nortic eller Billetto.

Varje evenemangssida (nortic.se/ticket/event/<id>, billetto.se/e/<namn>-<id>)
har ett JSON-LD-block med en post per föreställning. Evenemangen hittas via
arrangörens sida hos biljettbolaget och/eller via länkar på operans egen
webbplats. Före biljettsläppet finns inga länkar och då blir resultatet tomt.
"""
from __future__ import annotations

import json
import re

from common import Performance, get_text, iso_to_local, clean

NORTIC = "https://www.nortic.se"
_EVENT_LINK_RE = re.compile(r"(?:tickets\.|www\.)?nortic\.se/ticket/event/(\d+)")
_BILLETTO_RE = re.compile(r"billetto\.(se|dk|no)/e/([a-z0-9-]+-\d+)", re.I)
_LD_RE = re.compile(r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>", re.S)
_SKIP_RE = re.compile(r"gåva|paket|operabuss|buss\b|presentkort|parkering|middag|lunch", re.I)
_GENRE_RE = re.compile(r"^\s*\[([^\]]+)\]")

SOURCES = {
    # house_id: (stad, Nortic-arrangörs-id eller None, sidor att leta länkar på)
    # En sida som slutar på /wp-json/ betyder: läs alla sidor och inlägg i WordPress-sajten.
    "opera-pa-skaret": ("Kopparberg", 455, ["https://operapaskaret.se/biljetter/"]),
    "lacko-slottsopera": ("Lidköping", None, [
        "https://www.lackoslott.se/aktivitet/opera/",
        "https://www.lackoslott.se/evenemang/les-genies/",
    ]),
    "vadstena-akademien": ("Vadstena", None, [
        "https://www.vadstena-akademien.org/biljetter",
        "https://www.vadstena-akademien.org/",
    ]),
    "den-andra-operan": ("", None, [
        "https://billetto.se/users/den-andra-operan",
        "https://denandraoperan.se/",
        "https://denandraoperan.se/wp-json/",
    ]),
}


def _wp_content(base: str) -> str:
    """Allt innehåll i en WordPress-sajts sidor och inlägg (där länkar till biljetter finns)."""
    parts = []
    for kind in ("pages", "posts"):
        try:
            items = json.loads(get_text(f"{base}wp/v2/{kind}", params={"per_page": 100, "_fields": "content", "orderby": "modified", "order": "desc"}))
        except Exception:
            continue
        parts += [(i.get("content") or {}).get("rendered", "") for i in items]
    if not parts:
        raise RuntimeError(f"kunde inte läsa {base}")
    return "\n".join(parts)


def event_urls(organizer: int | None, pages: list[str]) -> list[str]:
    ids: list[str] = []
    texts = []
    tried = errors = 0
    last_error: Exception | None = None
    if organizer:
        tried += 1
        try:
            texts.append(get_text(f"{NORTIC}/dagny/ajax/organizer/eventcards/{organizer}"))
            ids += re.findall(r'data-event="(\d+)"', texts[-1])
        except Exception as e:
            errors, last_error = errors + 1, e
    for p in pages:
        tried += 1
        try:
            texts.append(_wp_content(p) if p.endswith("/wp-json/") else get_text(p))
        except Exception as e:
            errors, last_error = errors + 1, e
    if tried and errors == tried and last_error:
        raise last_error  # inget gick att nå – rapportera som fel i stället för "0 föreställningar"
    urls = [f"{NORTIC}/ticket/event/{i}" for i in ids]
    for t in texts:
        urls += [f"{NORTIC}/ticket/event/{i}" for i in _EVENT_LINK_RE.findall(t)]
        urls += [f"https://billetto.{tld.lower()}/e/{slug.lower()}" for tld, slug in _BILLETTO_RE.findall(t)]
    return list(dict.fromkeys(urls))


def parse_event_page(html: str, house_id: str, city: str, event_url: str) -> list[Performance]:
    out = []
    for block in _LD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        items = [g for i in items for g in ((i.get("@graph") or [i]) if isinstance(i, dict) else [i])]
        for e in items:
            if not isinstance(e, dict) or not str(e.get("@type", "")).endswith("Event") or not e.get("startDate"):
                continue
            name = clean(e.get("name"))
            if _SKIP_RE.search(name):
                continue
            title = re.sub(r"\s+20\d\d$", "", name)  # "Macbeth 2027" -> "Macbeth"
            d, t = iso_to_local(e["startDate"])
            if "T" not in e["startDate"]:
                t = ""
            gm = _GENRE_RE.match(e.get("description") or "")
            genre = gm.group(1) if gm else "Opera"
            offers = e.get("offers") or {}
            offer_list = offers if isinstance(offers, list) else [offers]
            avails = [(o.get("availability") or "").lower() for o in offer_list if isinstance(o, dict)]
            if "cancel" in str(e.get("eventStatus", "")).lower():
                status = "installt"
            elif avails and all("soldout" in a for a in avails):
                status = "utsalt"
            else:
                status = ""
            first = next((o for o in offer_list if isinstance(o, dict)), {})
            loc = e.get("location") or {}
            loc = loc[0] if isinstance(loc, list) and loc else loc
            loc_city = ((loc.get("address") or {}).get("addressLocality") if isinstance(loc.get("address"), dict) else "") or ""
            out.append(Performance(
                house_id=house_id, title=title, date=d, time=t, genre=genre,
                venue=loc.get("name", ""), city=city or loc_city, url=event_url,
                ticket_url=first.get("url") or event_url, status=status,
            ))
    return out


def fetch_house(house_id: str) -> list[Performance]:
    city, organizer, pages = SOURCES[house_id]
    out = []
    for url in event_urls(organizer, pages):
        try:
            out += parse_event_page(get_text(url), house_id, city, url)
        except Exception as e:  # en enskild trasig/borttagen evenemangssida stoppar inte resten
            print(f"  [varning] {house_id}: {url}: {e}")
    return out
