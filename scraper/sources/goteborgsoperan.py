"""GöteborgsOperan – kalendersidan är en Next.js-sida där varje föreställning
finns som ett JSON-objekt ({"__typename":"event", ...}) i sidans inbäddade data."""
from __future__ import annotations

import json
import re

from common import Performance, get_text

HOUSE = "goteborgsoperan"
BASE = "https://www.opera.se"
CAL_URL = f"{BASE}/forestallningar/kalender/"
CAL_URL_EN = f"{BASE}/en/what-s-on/calendar/"

_PUSH_RE = re.compile(r"self\.__next_f\.push\((\[.*?\])\)</script>", re.S)
_KEY_RE = re.compile(r'\{"__typename":\s*"event"\s*,')


def fetch() -> list[Performance]:
    try:
        en_html = get_text(CAL_URL_EN)
    except Exception:
        en_html = ""
    return parse(get_text(CAL_URL), en_html)


def _payload(html: str) -> str:
    parts = []
    for m in _PUSH_RE.finditer(html):
        try:
            arr = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if len(arr) > 1 and isinstance(arr[1], str):
            parts.append(arr[1])
    return "".join(parts)


def _events(payload: str):
    dec = json.JSONDecoder()
    i = 0
    seen = set()
    while (m := _KEY_RE.search(payload, i)):
        i = m.start()
        try:
            obj, end = dec.raw_decode(payload, i)
        except json.JSONDecodeError:
            i = m.end()
            continue
        i = end
        if obj.get("id") in seen:
            continue
        seen.add(obj.get("id"))
        yield obj


def _val(v):
    return "" if v in (None, "$undefined") else v


def parse(html: str, en_html: str = "") -> list[Performance]:
    en = {e.get("id"): e for e in _events(_payload(en_html))} if en_html else {}
    out = []
    for e in _events(_payload(html)):
        date = (e.get("date") or {})
        d = _val(date.get("formatted"))
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d or ""):
            continue
        cta = e.get("cta") or {}
        cancelled = _val(e.get("cancelled")) is True
        label = (_val(cta.get("label")) or "").lower()
        status = "installt" if cancelled or "inställ" in label else ("utsalt" if "utsål" in label else "")
        title = _val(e.get("eventGroupTitle")) or _val(e.get("title"))
        if cancelled:
            title = re.sub(r"\s*-\s*INSTÄLLD\s*$", "", title, flags=re.I)
        url = _val(e.get("url"))
        location = _val(e.get("location"))
        scene = _val(e.get("scene"))
        venue = ", ".join(x for x in (scene, location) if x)
        city = "Göteborg" if location in ("", "GöteborgsOperan") else ""
        ee = en.get(e.get("id")) or {}
        en_title = _val(ee.get("eventGroupTitle")) or _val(ee.get("title"))
        en_url = _val(ee.get("url"))
        en_scene = _val(ee.get("scene"))
        out.append(Performance(
            titles={"sv": title, "en": re.sub(r"\s*-\s*CANCELL?ED\s*$", "", en_title, flags=re.I)},
            urls={"sv": (BASE + url) if url.startswith("/") else url, "en": (BASE + en_url) if en_url.startswith("/") else en_url},
            venues={"sv": venue, "en": ", ".join(x for x in (en_scene, location) if x) if en_scene else ""},
            house_id=HOUSE, title=title, date=d, time=_val(date.get("time")),
            genre=_val(e.get("tag")), venue=venue, city=city,
            url=(BASE + url) if url.startswith("/") else url,
            ticket_url=_val(cta.get("url")) or "", status=status,
            note=_val(e.get("additionalInfo")),
            id=f"{HOUSE}:{e.get('id')}",
        ))
    return out
