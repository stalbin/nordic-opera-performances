"""Gemensamma hjälpfunktioner för alla operahus-skrapor."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests

STOCKHOLM = ZoneInfo("Europe/Stockholm")
USER_AGENT = "Operaappen/1.0 (+https://github.com; hamtar spelschema en gang per dygn)"
TIMEOUT = 30

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "sv-SE,sv;q=0.9"})


def get(url: str, **kwargs) -> requests.Response:
    resp = _session.get(url, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


def get_text(url: str, **kwargs) -> str:
    resp = get(url, **kwargs)
    resp.encoding = resp.encoding or "utf-8"
    if resp.encoding.lower() == "iso-8859-1":
        resp.encoding = "utf-8"
    return resp.text


def get_json(url: str, **kwargs):
    return get(url, headers={"Accept": "application/json"}, **kwargs).json()


@dataclass
class Performance:
    house_id: str          # t.ex. "kungliga-operan"
    title: str
    date: str              # YYYY-MM-DD (svensk lokal tid)
    time: str = ""         # HH:MM eller tomt
    genre: str = "Övrigt"
    venue: str = ""
    city: str = ""
    url: str = ""          # infosida om föreställningen
    ticket_url: str = ""   # direktlänk till biljettköp
    status: str = ""       # "", "utsalt", "installt", "fa-biljetter"
    note: str = ""         # t.ex. "Premiär"
    id: str = field(default="")
    # Samma föreställning på andra språk, när operahuset har det: {"sv": "...", "en": "..."}
    titles: dict = field(default_factory=dict)
    urls: dict = field(default_factory=dict)
    venues: dict = field(default_factory=dict)

    def finalize(self) -> "Performance":
        self.title = clean(self.title)
        self.venue = clean(self.venue)
        self.note = clean(self.note)
        # Kända anteckningar lagras som nycklar så att appen kan visa dem på användarens språk
        if self.note.lower() in ("premiär", "premiere", "premiär!"):
            self.note = "premiere"
        self.genre = normalize_genre(self.genre, self.title)
        self.titles = {k: clean(v) for k, v in self.titles.items() if clean(v)}
        self.venues = {k: clean(v) for k, v in self.venues.items() if clean(v)}
        self.urls = {k: v for k, v in self.urls.items() if v}
        if not self.id:
            slug = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")[:40]
            self.id = f"{self.house_id}:{self.date}:{self.time.replace(':', '')}:{slug}"
        return self

    def to_dict(self) -> dict:
        d = asdict(self)
        out = {
            "id": d["id"],
            "house": d["house_id"],
            "title": d["title"],
            "date": d["date"],
            "time": d["time"],
            "genre": d["genre"],
            "venue": d["venue"],
            "city": d["city"],
            "url": d["url"],
            "ticketUrl": d["ticket_url"],
            "status": d["status"],
            "note": d["note"],
        }
        for k in ("titles", "urls", "venues"):
            if d[k]:
                out[k] = d[k]
        return out


def clean(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("­", "")  # mjukt bindestreck
    return re.sub(r"\s+", " ", s).strip()


# Gemensamma genrer i appen
GENRES = ["Opera", "Operett", "Balett/dans", "Musikal", "Konsert", "Barn & unga", "Övrigt"]

# Svenska, danska och norska ord. Ordningen spelar roll vid delträffar (första träff vinner).
_GENRE_MAP = {
    "opera": "Opera",
    "operett": "Operett",
    "operette": "Operett",
    "balett": "Balett/dans",
    "balett/dans": "Balett/dans",
    "ballet": "Balett/dans",
    "ballett": "Balett/dans",
    "dans": "Balett/dans",
    "musikal": "Musikal",
    "musical": "Musikal",
    "konsert": "Konsert",
    "koncert": "Konsert",
    "klassisk symfoni": "Konsert",
    "kammermusikk": "Konsert",
    "kammermusik": "Konsert",
    "populær": "Konsert",
    "barn": "Barn & unga",
    "børn": "Barn & unga",
    "barn & unga": "Barn & unga",
    "barn och familj": "Barn & unga",
    "barn og unge": "Barn & unga",
    "familj": "Barn & unga",
    "familie": "Barn & unga",
    # finska / färöiska / isländska
    "ooppera": "Opera",
    "operetti": "Operett",
    "baletti": "Balett/dans",
    "tanssi": "Balett/dans",
    "musikaali": "Musikal",
    "konsertti": "Konsert",
    "konsertur": "Konsert",
    "tónleikar": "Konsert",
    "lapsille": "Barn & unga",
    "lapset": "Barn & unga",
    "perhe": "Barn & unga",
}


def normalize_genre(raw: str | None, title: str = "") -> str:
    key = clean(raw).lower()
    if key in _GENRE_MAP:
        return _GENRE_MAP[key]
    for k, v in _GENRE_MAP.items():
        if k in key:
            return v
    t = title.lower()
    if "konsert" in t or "gala" in t:
        return "Konsert"
    return "Övrigt"


SV_MONTHS = {
    "jan": 1, "januari": 1, "feb": 2, "februari": 2, "mar": 3, "mars": 3,
    "apr": 4, "april": 4, "maj": 5, "jun": 6, "juni": 6, "jul": 7, "juli": 7,
    "aug": 8, "augusti": 8, "sep": 9, "sept": 9, "september": 9,
    "okt": 10, "oktober": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    # danska/norska varianter
    "des": 12, "desember": 12, "mai": 5, "marts": 3, "januar": 1, "februar": 2, "august": 8,
}


def month_from_sv(name: str) -> int | None:
    return SV_MONTHS.get(name.lower().strip(". "))


def today_se() -> date:
    return datetime.now(STOCKHOLM).date()


def iso_to_local(iso: str) -> tuple[str, str]:
    """'2026-11-27T18:00:00+00:00' -> ('2026-11-27', '19:00') i svensk tid."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(STOCKHOLM)
    return dt.date().isoformat(), dt.strftime("%H:%M")
