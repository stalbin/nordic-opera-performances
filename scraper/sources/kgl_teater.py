"""Det Kongelige Teater (Köpenhamn) – kalenderns JSON-API.

Teatret spelar också skådespel och har rundvisningar; de tas inte med.
Opera, balett, konserter, musikaler och dans på Operaen, Gamle Scene m.fl. tas med.
"""
from __future__ import annotations

from common import Performance, get_json, iso_to_local, clean

HOUSE = "kgl-teater"
API = "https://www.kglteater.dk/api/calendar/activities"
PAGE_SIZE = 100  # API:t ger högst 100 per sida
MAX_PAGES = 60

EXCLUDE_CATEGORIES = {"skuespil", "rundvisning", "foredrag og talks", "andre oplevelser"}


def _items(culture: str) -> list[dict]:
    items = []
    for page in range(1, MAX_PAGES + 1):
        j = get_json(API, params={"page": page, "pageSize": PAGE_SIZE, "culture": culture, "showCancelled": "true"})
        items += j.get("items") or []
        if not j.get("hasMore"):
            break
    return items


def fetch() -> list[Performance]:
    items = _items("da-dk")
    try:
        en = _items("en-gb")  # engelska titlar, scener och länkar
    except Exception:
        en = []
    return parse(items, en)


def _key(i: dict) -> tuple:
    return (i.get("tixlyEventId") or i.get("showId"), i.get("startDate"))


def parse(items: list[dict], en_items: list[dict] | None = None) -> list[Performance]:
    en = {_key(i): i for i in (en_items or [])}
    out = []
    for i in items:
        cat = (i.get("category") or "").strip()
        if cat.lower() in EXCLUDE_CATEGORIES or not i.get("startDate"):
            continue
        d, t = iso_to_local(i["startDate"])
        sale = (i.get("tixlySaleStatusText") or "").lower()
        if i.get("canceled"):
            status = "installt"
        elif i.get("tixlySoldOut") or i.get("fullHouse") or sale == "soldout":
            status = "utsalt"
        elif sale == "fewtickets":
            status = "fa-biljetter"
        else:
            status = ""
        label = clean(i.get("label"))
        genre = "Barn & unga" if label.lower() == "for børn" and cat.lower() not in ("opera", "ballet") else cat
        ie = en.get(_key(i)) or {}
        en_url = ie.get("showUrl") if (ie.get("showUrl") or "").startswith("http") else ""
        out.append(Performance(
            titles={"da": i.get("showName") or "", "en": ie.get("showName") or ""},
            urls={"da": i.get("showUrl") or "", "en": en_url},
            venues={"da": i.get("location") or "", "en": ie.get("location") or ""},
            house_id=HOUSE, title=i.get("showName") or "", date=d, time=t,
            genre=genre, venue=i.get("location") or "", city="København",
            url=i.get("showUrl") or "", ticket_url=i.get("tixlyBuyLink") or i.get("externalBuyLink") or i.get("showUrl") or "",
            status=status, note="other-organizer" if label.lower() == "anden arrangør" else "",
            id=f"{HOUSE}:{i.get('tixlyEventId') or i.get('showId')}:{d}{t}",
        ))
    return out
