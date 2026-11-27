"""Den Norske Opera & Ballett (Oslo) – kalenderns JSON-API, en månad i taget."""
from __future__ import annotations

import re

from common import Performance, get_json, iso_to_local, today_se

HOUSE = "den-norske-opera"
BASE = "https://www.operaen.no"
MONTHS_AHEAD = 18
EXCLUDE_GENRES = {"omvisning"}


def _days(lang: str) -> list[dict]:
    t = today_se()
    y, m = t.year, t.month
    days = []
    for _ in range(MONTHS_AHEAD):
        days += get_json(f"{BASE}/api/calendar/production/event/{y}/{m}", params={"language": lang}) or []
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return days


def fetch() -> list[Performance]:
    days = _days("no")
    try:
        en = _days("en")
    except Exception:
        en = []
    return parse(days, en)


def _key(e: dict) -> str:
    """Biljettlänkens föreställnings-id är samma på alla språk (.../tickets/45790/93189/)."""
    m = re.search(r"/tickets/\d+/(\d+)", e.get("buyLink") or "")
    return m.group(1) if m else f"{e.get('time')}|{e.get('productionPageLink')}"


def parse(days: list[dict], en_days: list[dict] | None = None) -> list[Performance]:
    en: dict[str, dict] = {}
    for day in en_days or []:
        for e in day.get("events") or []:
            en[_key(e)] = e
    out = []
    for day in days:
        for e in day.get("events") or []:
            genres = [g.lower() for g in e.get("genres") or []]
            if not e.get("time") or (genres and set(genres) <= EXCLUDE_GENRES):
                continue
            d, t = iso_to_local(e["time"])
            sale = (e.get("salesStatus") or "").lower()
            btn = (e.get("buyButtonText") or "").lower()
            if "cancel" in sale or "avlyst" in btn:
                status = "installt"
            elif sale == "soldout" or "utsolgt" in btn:
                status = "utsalt"
            elif sale == "fewtickets":
                status = "fa-biljetter"
            else:
                status = ""
            main_genre = next((g for g in genres if g != "formidling"), genres[0] if genres else "")
            link = e.get("productionPageLink") or ""
            ee = en.get(_key(e)) or {}
            en_link = ee.get("productionPageLink") or ""
            out.append(Performance(
                titles={"nb": e.get("name") or "", "en": ee.get("name") or ""},
                urls={"nb": BASE + link if link.startswith("/") else link, "en": BASE + en_link if en_link.startswith("/") else en_link},
                venues={"nb": e.get("scene") or "", "en": ee.get("scene") or ""},
                house_id=HOUSE, title=e.get("name") or "", date=d, time=t, genre=main_genre,
                venue=e.get("scene") or "", city="Oslo",
                url=BASE + link if link.startswith("/") else link,
                ticket_url=e.get("buyLink") or "", status=status,
            ))
    return out
