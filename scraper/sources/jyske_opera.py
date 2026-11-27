"""Den Jyske Opera (Aarhus + turné i hela Danmark) – kalenderns JSON-endpoint."""
from __future__ import annotations

from common import Performance, get_json, iso_to_local, clean

HOUSE = "jyske-opera"
API = "https://www.jyske-opera.dk/endpoints-niks-pille/getdates"


def fetch() -> list[Performance]:
    return parse(get_json(API, params={"show": "all"}))


def _genre(title: str, text: str, arrangement: str) -> str:
    t = f"{title} {text}".lower()
    if arrangement == "event":
        return "Övrigt"  # samtal, introduktioner, podcasts m.m.
    if any(w in t for w in ("koncert", "messingklang", "julesang", "gala")):
        return "Konsert"
    if any(w in t for w in ("børn", "familie", "lastbil")):
        return "Barn & unga"
    return "Opera"


def parse(data) -> list[Performance]:
    groups = data if isinstance(data, list) else [data]
    out = []
    for g in groups:
        for d in (g.get("dates") if isinstance(g, dict) else None) or []:
            if not d.get("datetime"):
                continue
            date, time = iso_to_local(d["datetime"])
            loc = d.get("location") or {}
            venue = clean(loc.get("name"))
            zip_code = loc.get("zip") or 0
            city = "Aarhus" if "aarhus" in venue.lower() or 8000 <= int(zip_code or 0) <= 8270 else ""
            title = clean(d.get("alttitle")) or clean(d.get("title"))
            buy = clean(d.get("buytext")).lower()
            status = "utsalt" if "udsolgt" in buy else ("installt" if "aflyst" in buy else "")
            out.append(Performance(
                house_id=HOUSE, title=title, date=date, time=time,
                genre=_genre(title, clean(d.get("text")), d.get("arrangement") or ""),
                venue=venue, city=city, url=d.get("url") or "",
                ticket_url=d.get("ticketurl") or d.get("url") or "", status=status,
                id=f"{HOUSE}:{d.get('id')}",
            ))
    return out
