"""Hämtar föreställningar från alla operahus och skriver data/forestallningar.json.

Körs en gång per dygn av GitHub Actions. Om ett operahus inte går att hämta
(webbplatsen nere eller ombyggd) behålls husets föreställningar från förra
körningen, så att appen inte plötsligt blir tom. Felet syns i "houses"-listan
i JSON-filen och i Actions-loggen.
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "sources"))

from common import STOCKHOLM, today_se  # noqa: E402
from houses import HOUSES, REASSIGN  # noqa: E402
import kungliga_operan, goteborgsoperan, malmo_opera, norrlandsoperan  # noqa: E402,E401
import folkoperan, wermland_opera, nortic  # noqa: E402,E401
import kgl_teater, den_norske_opera, bergen_nasjonale_opera, tso, jyske_opera  # noqa: E402,E401
import small_operas  # noqa: E402
import nordic_text  # noqa: E402

FETCHERS = {
    "kungliga-operan": kungliga_operan.fetch,
    "goteborgsoperan": goteborgsoperan.fetch,
    "malmo-opera": malmo_opera.fetch,
    "norrlandsoperan": norrlandsoperan.fetch,
    "folkoperan": folkoperan.fetch,
    "wermland-opera": wermland_opera.fetch,
    "lacko-slottsopera": lambda: nortic.fetch_house("lacko-slottsopera"),
    "vadstena-akademien": lambda: nortic.fetch_house("vadstena-akademien"),
    "opera-pa-skaret": lambda: nortic.fetch_house("opera-pa-skaret"),
    "kgl-teater": kgl_teater.fetch,
    "den-norske-opera": den_norske_opera.fetch,
    "bergen-nasjonale-opera": bergen_nasjonale_opera.fetch,
    "tso": tso.fetch,
    "jyske-opera": jyske_opera.fetch,
    "den-andra-operan": lambda: nortic.fetch_house("den-andra-operan"),
    "opera-hedeland": small_operas.fetch_hedeland,
    "cph-opera-festival": small_operas.fetch_cph,
    "oscarsborgoperaen": small_operas.fetch_oscarsborg,
    "opera-trondelag": small_operas.fetch_trondelag,
    "opera-nordfjord": small_operas.fetch_nordfjord,
    "ringsakeroperaen": small_operas.fetch_ringsaker,
    "suomen-kansallisooppera": nordic_text.fetch_fnob,
    **{hid: (lambda h=hid: nordic_text.fetch_text_house(h)) for hid in nordic_text.TEXT_SOURCES},
    # kongelig-sommeropera och opera-ved-fjorden får sina föreställningar via REASSIGN i houses.py
}

# Hus som normalt alltid har föreställningar. Ger de 0 räknas det som fel.
ALWAYS_ACTIVE = {"kungliga-operan", "goteborgsoperan", "malmo-opera", "norrlandsoperan", "folkoperan", "wermland-opera",
                 "kgl-teater", "den-norske-opera", "bergen-nasjonale-opera", "tso", "jyske-opera",
                 "suomen-kansallisooppera"}

# Biljettlänkar som pekar på en enskild föreställning (Tixly, Nortic)
_SHOW_LINK_RES = [re.compile(r"/buyingflow/tickets/\d+/(\d+)"), re.compile(r"nortic\.se/dagny/show/(\d+)")]


def ticket_key(p: dict) -> str | None:
    """Samma föreställning kan listas av två hus (t.ex. samproduktioner). Biljettlänkens
    event-id är unikt per föreställning, så den används för att ta bort dubbletter."""
    url = p.get("ticketUrl") or ""
    host = re.sub(r"^https?://([^/]+).*", r"\1", url).removeprefix("tickets.").removeprefix("www.")
    for rx in _SHOW_LINK_RES:
        m = rx.search(url)
        if m:
            return f"{host}:{m.group(1)}"
    return None

OUT = Path(__file__).resolve().parent.parent / "data" / "forestallningar.json"


def load_previous() -> dict:
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(only: list[str] | None = None) -> int:
    today = today_se().isoformat()
    prev = load_previous()
    prev_by_house: dict[str, list[dict]] = {}
    for p in prev.get("performances", []):
        prev_by_house.setdefault(p["house"], []).append(p)

    # 1) Hämta varje hus som har en egen hämtare
    results: dict[str, tuple[list[dict], str, str]] = {}
    failures = attempted = 0
    for h in HOUSES:
        hid = h["id"]
        if hid not in FETCHERS:
            continue  # hus som får sina föreställningar från ett annat hus (REASSIGN)
        if only and hid not in only:
            results[hid] = ([p for p in prev_by_house.get(hid, []) if p["date"] >= today], "ej-hamtad", "")
            continue
        attempted += 1
        try:
            perfs = [p.finalize().to_dict() for p in FETCHERS[hid]()]
            perfs = [p for p in perfs if p["date"] >= today]
            if not perfs and hid in ALWAYS_ACTIVE:
                raise RuntimeError("inga föreställningar hittades – har webbplatsen ändrats?")
            results[hid] = (perfs, "ok", "")
        except Exception as e:  # behåll gårdagens data för huset
            failures += 1
            error = f"{type(e).__name__}: {e}"
            print(f"[FEL] {h['name']}: {error}", file=sys.stderr)
            traceback.print_exc()
            results[hid] = ([p for p in prev_by_house.get(hid, []) if p["date"] >= today], "gammal-data", error)

    # 2) Flytta föreställningar till de hus de egentligen hör till (t.ex. Kongelig Sommeropera)
    for src, pattern, dst in REASSIGN:
        perfs, status, error = results.get(src, ([], "ok", ""))
        rx = re.compile(pattern, re.I)
        moved = [p for p in perfs if rx.search(p["title"])]
        keep = [p for p in perfs if not rx.search(p["title"])]
        for p in moved:
            p["house"] = dst
            p["id"] = dst + p["id"][len(src):] if p["id"].startswith(src) else f"{dst}:{p['id']}"
        if status == "gammal-data":
            moved += [p for p in prev_by_house.get(dst, []) if p["date"] >= today]
        results[src] = (keep, status, error)
        old = results.get(dst, ([], status, error))
        results[dst] = (old[0] + moved, status, error)

    # 3) Ta bort dubbletter (även mellan hus) och sammanställ
    all_perfs: list[dict] = []
    seen_tickets: set[str] = set()
    house_meta = []
    for h in HOUSES:
        hid = h["id"]
        perfs, status, error = results.get(hid, ([], "ok", ""))
        seen, uniq = set(), []
        for p in perfs:
            tk = ticket_key(p)
            if p["id"] in seen or (tk and tk in seen_tickets):
                continue
            seen.add(p["id"])
            if tk:
                seen_tickets.add(tk)
            uniq.append(p)
        print(f"{h['name']:<32} {len(uniq):>4} föreställningar  [{status}]")
        all_perfs += uniq
        house_meta.append({**h, "count": len(uniq), "status": status, "error": error})

    all_perfs.sort(key=lambda p: (p["date"], p["time"] or "99:99", p["house"], p["title"]))
    genres = sorted({p["genre"] for p in all_perfs},
                    key=lambda g: ["Opera", "Operett", "Balett/dans", "Musikal", "Konsert", "Barn & unga", "Övrigt"].index(g)
                    if g in ["Opera", "Operett", "Balett/dans", "Musikal", "Konsert", "Barn & unga", "Övrigt"] else 99)
    data = {
        "version": 1,
        "generated": datetime.now(STOCKHOLM).isoformat(timespec="seconds"),
        "houses": house_meta,
        "genres": genres,
        "performances": all_perfs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nTotalt {len(all_perfs)} föreställningar -> {OUT}")
    # Misslyckas bara om allt gick fel, så att en enskild trasig sida inte stoppar uppdateringen
    return 1 if attempted and failures == attempted else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
