"""Kungliga Operan – webbplatsens egna JSON-API.

webapi.operan.se/performances/ ger alla kommande föreställningar (id, produktion, tid, platser kvar).
/contentapi/sv/productions/content?productionIds=... ger namn, url och genre per produktion.
"""
from __future__ import annotations

import re

from common import Performance, get_json, iso_to_local

HOUSE = "kungliga-operan"
BASE = "https://www.operan.se"
API = "https://webapi.operan.se"
TICKET_URL = "https://www.operan.se/kassa"


def fetch() -> list[Performance]:
    perfs = get_json(f"{API}/performances/")
    prod_ids = sorted({p["productionId"] for p in perfs})
    content: dict = {}
    content_en: dict = {}
    for i in range(0, len(prod_ids), 30):
        chunk = prod_ids[i:i + 30]
        q = "&".join(f"productionIds={pid}" for pid in chunk)
        content.update(get_json(f"{BASE}/contentapi/sv/productions/content?{q}") or {})
        try:  # engelska versionen (namn och länk), finns för de flesta produktioner
            content_en.update(get_json(f"{BASE}/contentapi/en-GB/productions/content?{q}") or {})
        except Exception:
            pass
    return parse(perfs, content, content_en)


def parse(perfs: list[dict], content: dict, content_en: dict | None = None) -> list[Performance]:
    content_en = content_en or {}
    out = []
    for p in perfs:
        c = content.get(str(p["productionId"])) or content.get(p["productionId"])
        if not c or not c.get("name"):
            continue  # produktion utan publik sida (t.ex. intern eller borttagen)
        d, t = iso_to_local(p["performanceDate"])
        genres = c.get("genres") or []
        url = BASE + c["url"] if c.get("url", "").startswith("/") else c.get("url", "")

        ticket = url or TICKET_URL
        venue = ""
        hide_seats = bool(c.get("hideSeatInformation"))
        for ov in c.get("performanceOverrides") or []:
            if ov.get("performanceId") == p["performanceId"]:
                m = re.search(r'href="([^"]+)"', ov.get("bookingLinkHtml") or "")
                if m:
                    ticket = m.group(1)
                if "cirkus" in (ov.get("bookingLinkHtml") or "").lower():
                    venue = "Cirkus"
                hide_seats = bool(ov.get("hideSeatInformation", hide_seats))
        # Platser kvar visas bara när operan själv visar det (annat biljettsystem annars)
        status = "utsalt" if (not hide_seats and p.get("availability", 1) == 0) else ""
        en = content_en.get(str(p["productionId"])) or content_en.get(p["productionId"]) or {}
        en_url = BASE + en["url"] if (en.get("url") or "").startswith("/") else en.get("url", "")
        out.append(Performance(
            titles={"sv": c["name"], "en": en.get("name", "")},
            urls={"sv": url, "en": en_url},
            house_id=HOUSE, title=c["name"], date=d, time=t,
            genre=genres[0] if genres else "", venue=venue, city="Stockholm",
            url=url, ticket_url=ticket, status=status,
            id=f"{HOUSE}:{p['performanceId']}",
        ))
    return out
