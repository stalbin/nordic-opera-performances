"""Norrlandsoperan – WordPress REST-API. Posttypen "session" är en enskild
föreställning och pekar på sin "event" (produktionen) som har genre och länk."""
from __future__ import annotations

from common import Performance, get, get_json, today_se, clean

HOUSE = "norrlandsoperan"
API = "https://norrlandsoperan.se/wp-json/wp/v2"


def _all(endpoint: str, params: dict) -> list[dict]:
    out, page = [], 1
    while True:
        r = get(f"{API}/{endpoint}", params={**params, "per_page": 100, "page": page})
        items = r.json()
        out.extend(items)
        total_pages = int(r.headers.get("X-WP-TotalPages", "1") or 1)
        if page >= total_pages or not items:
            return out
        page += 1


def fetch() -> list[Performance]:
    sessions = _all("session", {"_fields": "id,title,meta", "orderby": "date", "order": "desc"})
    today = today_se().isoformat()
    sessions = [s for s in sessions
                if (s.get("meta") or {}).get("session_date", "") >= today
                and not (s.get("meta") or {}).get("archived_session")]
    event_ids = sorted({s["meta"]["event"] for s in sessions if s["meta"].get("event")})
    events = {}
    for i in range(0, len(event_ids), 100):
        chunk = event_ids[i:i + 100]
        for e in get_json(f"{API}/event", params={
                "include": ",".join(map(str, chunk)), "per_page": 100,
                "_fields": "id,title,link,meta,event_category"}):
            events[e["id"]] = e
    cats = {c["slug"]: c["name"] for c in get_json(f"{API}/event_category", params={"per_page": 100, "_fields": "slug,name"})}
    en_by_guid: dict[str, dict] = {}
    try:  # engelska versionerna av produktionerna; kopplas via biljettsystemets id
        for e in _all("event", {"lang": "en", "_fields": "id,title,link,meta", "orderby": "date", "order": "desc"})[:200]:
            g = (e.get("meta") or {}).get("event_api_guid")
            if g:
                en_by_guid.setdefault(str(g), e)
    except Exception:
        pass
    return parse(sessions, events, cats, en_by_guid)


def parse(sessions: list[dict], events: dict, cats: dict, en_by_guid: dict | None = None) -> list[Performance]:
    en_by_guid = en_by_guid or {}
    out = []
    for s in sessions:
        m = s.get("meta") or {}
        ev = events.get(m.get("event")) or {}
        em = ev.get("meta") or {}
        title = clean((ev.get("title") or {}).get("rendered")) or m.get("session_manual_name") or clean((s.get("title") or {}).get("rendered"))
        cat_slug = em.get("event_primary_category", "")
        genre = cats.get(cat_slug, cat_slug)
        st = (m.get("session_status") or "").lower()
        status = "utsalt" if "sold" in st or "utsal" in st else ("installt" if "cancel" in st or "install" in st else "")
        venue = m.get("session_location") or ""
        city = "Umeå" if (cat_slug != "pa-turne") else ""
        en = en_by_guid.get(str(em.get("event_api_guid") or "")) or {}
        en_title = clean((en.get("title") or {}).get("rendered")).replace("*", "")
        out.append(Performance(
            titles={"sv": title, "en": en_title},
            urls={"sv": ev.get("link", ""), "en": en.get("link", "")},
            house_id=HOUSE, title=title, date=m.get("session_date", ""), time=(m.get("session_time") or "")[:5],
            genre=genre, venue=venue, city=city, url=ev.get("link", ""),
            ticket_url=m.get("session_ticket_link") or em.get("event_ticket_link") or "",
            status=status, id=f"{HOUSE}:{s['id']}",
        ))
    return out
