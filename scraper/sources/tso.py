"""Trondheim Symfoniorkester & Opera – programmets JSON (datum, titel, genre,
biljettlänk). Klockslaget står bara på konsertsidan, så den läses också."""
from __future__ import annotations

import re

from common import Performance, get_json, get_text, month_from_sv, clean, today_se

HOUSE = "tso"
BASE = "https://www.tso.no"
API = f"{BASE}/actions/tso/consert/get-conserts"

_DATE_RE = re.compile(r"(\d{1,2})\.?\s+([a-zæøå]+)\.?\s+(\d{4})", re.I)
_DATE_TIME_RE = re.compile(r"(\d{1,2})\.?\s+([a-zæøå]+)\.?\s+(\d{4})\s*Kl\.?\s*(\d{1,2})[:.](\d{2})", re.I)


def _date(txt: str) -> str:
    m = _DATE_RE.search(txt or "")
    if not m:
        return ""
    mon = month_from_sv(m.group(2))
    return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(1)):02d}" if mon else ""


def times_from_page(html: str) -> dict[str, str]:
    """{'2027-03-04': '19:00', ...} från texten '04 mar. 2027 Kl 19:00' på konsertsidan."""
    txt = clean(re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html))
    res = {}
    for m in _DATE_TIME_RE.finditer(txt):
        mon = month_from_sv(m.group(2))
        if mon:
            res.setdefault(f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(1)):02d}", f"{int(m.group(4)):02d}:{m.group(5)}")
    return res


def fetch() -> list[Performance]:
    data = get_json(API)
    items = [x for v in (data.values() if isinstance(data, dict) else [data]) for x in (v or [])]
    today = today_se().isoformat()
    times: dict[str, dict[str, str]] = {}
    for url in {i.get("u") for i in items if i.get("u") and _date(i.get("d", "")) >= today}:
        try:
            times[url] = times_from_page(get_text(url))
        except Exception:
            times[url] = {}
    return parse(items, times)


def parse(items: list[dict], times: dict[str, dict[str, str]]) -> list[Performance]:
    out = []
    for i in items:
        d = _date(i.get("d", ""))
        if not d:
            continue
        title = clean(i.get("t"))
        genre = i.get("ct") or "Konsert"  # TSO är i grunden en orkester; tom genre = konsert
        if title.lower().startswith("opera:"):
            title, genre = title[6:].strip(), genre or "Opera"
        ts = (i.get("ts") or "").lower()
        status = "utsalt" if i.get("so") or ts == "soldout" else ("fa-biljetter" if ts == "fewleft" else "")
        if "avlys" in title.lower():
            status = "installt"
        out.append(Performance(
            house_id=HOUSE, title=title, date=d, time=times.get(i.get("u"), {}).get(d, ""),
            genre=genre, venue=clean(i.get("p")), city="Trondheim", url=i.get("u") or "",
            ticket_url=i.get("tl") or i.get("u") or "", status=status,
        ))
    return out
