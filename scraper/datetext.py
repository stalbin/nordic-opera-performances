"""Hittar datum och klockslag i löptext på svenska, danska och norska.

Små operor skriver ofta datumen i text i stället för i en kalender, t.ex.
  "Verdis Falstaff den 7., 13. og 14. august 2027"
  "13.08.27 kl. 20.00 Premiere 15-16. august kl. 20.00"
  "19. - 20. august 2027"   "22/04 | 24/04"
find_dates() returnerar en lista med (ISO-datum, "HH:MM" eller "") i textordning.
"""
from __future__ import annotations

import re
from datetime import date

from common import month_from_sv

_MONTH = (r"(jan(?:uar|uari)?|feb(?:ruar|ruari)?|mar(?:s|ts)?|apr(?:il)?|maj|mai|jun(?:i)?|jul(?:i)?|aug(?:ust|usti)?|"
          r"sep(?:t|tember)?|okt(?:ober)?|nov(?:ember)?|dec(?:ember)?|des(?:ember)?)\.?")
_TIME = r"(?:\s*,?\s*(?:kl\.?|klo\.?|klokka|klokken|kello|kl)\s*(\d{1,2})(?:[.:](\d{2}))?)?"
# efter ett siffer-datum kan klockslaget stå utan "kl": "Sat 17.01.2026 13.00"
_TIME_NUM = r"(?:\s*,?\s*(?:kl\.?|klo\.?|klokka|klokken|kello|kl)?\s*(\d{1,2})[.:](\d{2})(?![\d.]))?"
# "7., 13. og 14. august 2027 kl. 20" / "15-16. august" / "19. - 20. august 2027" / "21-22 august"
_DAYS_MONTH = re.compile(
    r"(?<![\d.])((?:\d{1,2}\.?\s*(?:,|og|och|&|-|–)\s*)*\d{1,2})\.?\s+" + _MONTH + r"(?:\s+(\d{4}))?" + _TIME, re.I)
# "13.08.27 kl. 20.00" / "13.08.2027"
_NUMERIC = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})(?![\d])" + _TIME_NUM, re.I)
# "Pe 11.6. klo 18" (finska, utan år – året tas från sidan eller närmaste kommande)
_NUMERIC_NOYEAR = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(?![\d])" + _TIME, re.I)
# "22/04" (utan år)
_SLASH = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?![\d/])" + _TIME)

MAX_RANGE_DAYS = 4  # "15-16. august" = två föreställningar; längre perioder är spelperioder, inte speldagar


def year_for(month: int, day: int, today: date) -> int:
    """Datum utan år: närmaste kommande (eller dagens)."""
    try:
        return today.year if date(today.year, month, day) >= today else today.year + 1
    except ValueError:
        return today.year


def _t(hh: str | None, mm: str | None) -> str:
    return f"{int(hh):02d}:{mm or '00'}" if hh and int(hh) < 24 else ""


def _valid(y: int, m: int, d: int) -> bool:
    try:
        date(y, m, d)
        return True
    except ValueError:
        return False


def find_dates(text: str, today: date, year_hint: int | None = None) -> list[tuple[str, str]]:
    found: list[tuple[int, str, str]] = []  # (position, iso, time)

    for m in _NUMERIC.finditer(text):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        if 1 <= mo <= 12 and _valid(y, mo, d):
            found.append((m.start(), date(y, mo, d).isoformat(), _t(m.group(4), m.group(5))))

    taken = [(m.start(), m.end()) for m in _NUMERIC.finditer(text)]

    for m in _NUMERIC_NOYEAR.finditer(text):
        if any(m.start() < e and s < m.end() for s, e in taken):
            continue
        d, mo = int(m.group(1)), int(m.group(2))
        if not (1 <= mo <= 12):
            continue
        y = year_hint if year_hint and _valid(year_hint, mo, d) else year_for(mo, d, today)
        if _valid(y, mo, d):
            found.append((m.start(), date(y, mo, d).isoformat(), _t(m.group(3), m.group(4))))
            taken.append((m.start(), m.end()))

    def overlaps(a: int, b: int) -> bool:
        return any(a < e and s < b for s, e in taken)

    for m in _DAYS_MONTH.finditer(text):
        if overlaps(m.start(), m.end()):
            continue
        mon = month_from_sv(m.group(2).rstrip("."))
        if not mon:
            continue
        days_txt = m.group(1)
        parts = re.split(r"\s*(,|og|och|&|-|–)\s*", days_txt)
        days: list[int] = []
        i = 0
        nums = [p for p in parts if re.fullmatch(r"\d{1,2}\.?", p or "")]
        seps = [p for p in parts if p in (",", "og", "och", "&", "-", "–")]
        nums = [int(n.rstrip(".")) for n in nums]
        if not nums:
            continue
        days.append(nums[0])
        for sep, n in zip(seps, nums[1:]):
            if sep in ("-", "–") and 0 < n - days[-1] <= MAX_RANGE_DAYS:
                days += list(range(days[-1] + 1, n + 1))
            elif sep in ("-", "–"):
                pass  # lång spelperiod: bara första dagen räknas
            else:
                days.append(n)
        y_explicit = int(m.group(3)) if m.group(3) else None
        t = _t(m.group(4), m.group(5))
        for d in days:
            y = y_explicit or (year_hint if year_hint and _valid(year_hint, mon, d) else year_for(mon, d, today))
            if _valid(y, mon, d):
                found.append((m.start(), date(y, mon, d).isoformat(), t))
        i += 1

    for m in _SLASH.finditer(text):
        if overlaps(m.start(), m.end()):
            continue
        d, mo = int(m.group(1)), int(m.group(2))
        if not (1 <= mo <= 12):
            continue
        y = year_hint if year_hint and _valid(year_hint, mo, d) else year_for(mo, d, today)
        if _valid(y, mo, d):
            found.append((m.start(), date(y, mo, d).isoformat(), _t(m.group(3), m.group(4))))

    found.sort()
    out, seen = [], set()
    for _, iso, t in found:
        if iso in seen:
            continue
        seen.add(iso)
        out.append((iso, t))
    return out
