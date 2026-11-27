"""Tester mot sparade utdrag av operahusens sidor (struktur från november 2026).
Kör: python -m pytest scraper/tests  (eller python scraper/tests/test_parsers.py)"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "sources"))

from bs4 import BeautifulSoup  # noqa: E402

import folkoperan, goteborgsoperan, kungliga_operan, malmo_opera  # noqa: E402,E401
import norrlandsoperan, nortic, wermland_opera  # noqa: E402,E401
import kgl_teater, den_norske_opera, bergen_nasjonale_opera, tso, jyske_opera  # noqa: E402,E401
from datetime import date  # noqa: E402
import small_operas  # noqa: E402
import nordic_text  # noqa: E402
from datetext import find_dates  # noqa: E402
from common import normalize_genre  # noqa: E402

FIX = HERE / "fixtures"


def fin(perfs):
    return [p.finalize().to_dict() for p in perfs]


def test_kungliga_operan():
    perfs = [
        {"performanceId": 9936, "productionId": 1030, "performanceDate": "2026-11-27T18:00:00+00:00", "availability": 0},
        {"performanceId": 10159, "productionId": 130, "performanceDate": "2026-12-02T17:00:00+00:00", "availability": 0},
        {"performanceId": 10076, "productionId": 10016, "performanceDate": "2026-11-27T18:00:00+00:00", "availability": 714},
        {"performanceId": 1, "productionId": 999, "performanceDate": "2026-11-27T18:00:00+00:00", "availability": 5},
    ]
    content = {
        "1030": {"name": "Tosca", "url": "/forestallningar/tosca", "genres": ["Opera"], "hideSeatInformation": False},
        "130": {"name": "Nötknäpparen", "url": "/forestallningar/notknapparen", "genres": ["Balett/dans"], "hideSeatInformation": True,
                "performanceOverrides": [{"performanceId": 10159, "hideSeatInformation": True,
                                          "bookingLinkHtml": '<a href="https://biljetter.cirkus.se/sv/buyingflow/tickets/30891/125935/">Biljetter p&#xE5; cirkus.se</a>'}]},
        "10016": {"name": "Läderlappen", "url": "/forestallningar/laderlappen", "genres": ["Operett"]},
    }
    out = fin(kungliga_operan.parse(perfs, content))
    assert len(out) == 3  # produktion 999 saknar innehåll
    tosca = out[0]
    assert (tosca["title"], tosca["date"], tosca["time"], tosca["genre"], tosca["status"]) == ("Tosca", "2026-11-27", "19:00", "Opera", "utsalt")
    nk = out[1]
    assert nk["venue"] == "Cirkus" and nk["ticketUrl"].startswith("https://biljetter.cirkus.se") and nk["status"] == "" and nk["genre"] == "Balett/dans"
    assert out[2]["genre"] == "Operett" and out[2]["status"] == ""


def _gbg_html(events):
    payload = '5:["$","div",null,' + json.dumps({"calendar": {"days": [{"__typename": "calendarDay", "events": events}]}}, ensure_ascii=False, separators=(",", ":")) + ']\n'
    half = len(payload) // 2
    pushes = [json.dumps([1, payload[:half]], ensure_ascii=False), json.dumps([1, payload[half:]], ensure_ascii=False)]
    return "<html><body>" + "".join(f"<script>self.__next_f.push({p})</script>" for p in pushes) + "</body></html>"


def test_goteborgsoperan():
    ev = {"__typename": "event", "id": "135519", "eventGroupId": 32941, "eventGroupTitle": "See you Sunday & We made a mess",
          "title": "See you Sunday & We made a mess", "location": "GöteborgsOperan", "scene": "Stora scenen",
          "additionalInfo": "Premiär", "url": "/forestallningar/sasong-2026-2027/see-you-sunday-we-made-a-mess/", "tag": "dans",
          "date": {"__typename": "eventDate", "day": "Sön", "dayMonth": "29/11", "formatted": "2026-11-29", "time": "18:00"},
          "cancelled": "$undefined",
          "cta": {"__typename": "CtaGraphType", "label": "Köp", "url": "https://biljett.opera.se/sv/buyingflow/tickets/32941/135519/", "disabled": False},
          "ticketInformation": "$undefined"}
    cancelled = {**ev, "id": "129282", "eventGroupTitle": "Jakten på den magiska nyckeln", "title": "Jakten på den magiska nyckeln - INSTÄLLD",
                 "tag": "barn", "cancelled": True, "additionalInfo": "$undefined", "url": "",
                 "cta": {"__typename": "CtaGraphType", "label": "Inställt", "url": None, "disabled": True},
                 "date": {"__typename": "eventDate", "formatted": "2027-01-08", "time": "18:00"}}
    tour = {**ev, "id": "1", "eventGroupTitle": "Julglädje", "location": "Skövde Kulturhus", "scene": "Stadsteatern", "tag": "konsert",
            "additionalInfo": "Biljetter säljs av arrangören", "date": {"formatted": "2026-12-12", "time": "17:00"}}
    out = fin(goteborgsoperan.parse(_gbg_html([ev, cancelled, tour, ev])))
    assert len(out) == 3, out
    a, b, c = out
    assert a["title"] == "See you Sunday & We made a mess" and a["genre"] == "Balett/dans" and a["venue"] == "Stora scenen, GöteborgsOperan"
    assert a["url"].startswith("https://www.opera.se/forestallningar/") and a["note"] == "premiere" and a["city"] == "Göteborg"
    assert b["status"] == "installt" and b["title"] == "Jakten på den magiska nyckeln" and b["genre"] == "Barn & unga"
    assert c["city"] == "" and c["genre"] == "Konsert"


def test_malmo():
    soup = BeautifulSoup((FIX / "malmo_page.html").read_text(encoding="utf-8"), "lxml")
    genres = malmo_opera.parse_genres(soup)
    assert genres == {"joyride-musical": "Musikal", "kvarteret-korpen": "Opera"}
    rows, year = malmo_opera.parse_calendar(soup)
    assert year == 2027 and len(rows) == 4
    for r in rows:
        r.genre = genres.get(r.url.rsplit("/", 1)[-1], r.genre)
    out = fin(rows)
    assert out[0]["date"] == "2026-12-30" and out[0]["time"] == "19:00" and out[0]["status"] == "utsalt" and out[0]["genre"] == "Musikal"
    assert out[1]["status"] == "fa-biljetter" and out[1]["ticketUrl"].endswith("29702?lang=sv") and out[1]["genre"] == "Opera"
    assert out[2]["date"] == "2027-01-02" and out[2]["status"] == ""
    assert out[3]["title"] == "Julgransplundring med Tomtemor"
    # sida utan månadsrubrik ärver året från föregående sida
    soup2 = BeautifulSoup('<div class="mo-instances__calendar"><div data-instance-id="9" class="mo-instance"><div><span class="tag">fre 8 jan 19.00</span>'
                          '<a href="/forestallningar/rusalka"><div>Rusalka</div></a></div></div></div>', "lxml")
    rows2, _ = malmo_opera.parse_calendar(soup2, 2027)
    assert rows2[0].date == "2027-01-08"


def test_norrlandsoperan():
    sessions = [{"id": 26310, "title": {"rendered": "Mozarts Zaïde"}, "meta": {
        "event": 26092, "session_date": "2027-05-08", "session_time": "19:00",
        "session_ticket_link": "https://biljett.norrlandsoperan.se/sv/buyingflow/tickets/34213/138320/",
        "session_location": "Black Box, onum", "session_status": "buy_ticket", "session_manual_name": ""}}]
    events = {26092: {"id": 26092, "title": {"rendered": "Mozarts Za&#239;de"}, "link": "https://norrlandsoperan.se/forestallningar/mozarts-zaide/",
                      "meta": {"event_primary_category": "opera"}}}
    out = fin(norrlandsoperan.parse(sessions, events, {"opera": "Opera"}))
    assert out[0]["title"] == "Mozarts Zaïde" and out[0]["genre"] == "Opera" and out[0]["venue"] == "Black Box, onum" and out[0]["city"] == "Umeå"


def test_folkoperan():
    html = """<ol class="c-event-list__list">
    <li class="c-event-list__item"><div class="c-event-list__item__left"><h3 class="c-heading">Falstaff PREMIÄR</h3>
      <h4 class="c-heading -eta">fredag 22 januari 2027</h4><span class="u-small-text">19:00</span></div>
      <div class="c-event-list__item__right"><a href="https://biljetter.folkoperan.se/sv/buyingflow/tickets/1/2/" class="c-button">Köp biljett</a></div></li>
    <li class="c-event-list__item"><div class="c-event-list__item__left"><h3 class="c-heading">Folkoperan Foajé: Gunilla Backman sjunger Sondheim</h3>
      <h4 class="c-heading -eta">söndag 6 december 2026</h4><span class="u-small-text">15:00</span></div>
      <div class="c-event-list__item__right"><a href="https://biljetter.folkoperan.se/sv/buyingflow/tickets/3/4/">Köp</a></div></li>
    <li class="c-event-list__item"><div class="c-event-list__item__left"><h3 class="c-heading">Falstaff PREMIÄR</h3>
      <h4 class="c-heading -eta">fredag 22 januari 2027</h4><span class="u-small-text">19:00</span></div>
      <div class="c-event-list__item__right"><a href="https://biljetter.folkoperan.se/sv/buyingflow/tickets/1/2/">Köp</a></div></li></ol>"""
    out = fin(folkoperan.parse(html))
    assert len(out) == 2
    assert out[0]["title"] == "Falstaff" and out[0]["note"] == "premiere" and out[0]["date"] == "2027-01-22" and out[0]["genre"] == "Opera"
    assert out[1]["genre"] == "Konsert"


def test_wermland():
    html = """<article class="calendar__event" data-place="25" data-category="6"><div class="calendar__event-when">
      <time class="calendar__event-time" datetime="2026-11-27T18:00">18:00</time><span class="calendar__event-place">Bageriet</span></div>
      <div class="calendar__event-body"><span class="calendar__event-category">Konsert</span><h3 class="calendar__event-title">
      <a href="https://www.wermlandopera.com/evenemang/konsert/kizelo-mleko-bubblor-pa-bageriet/">Kizelo Mleko – Bubblor på Bageriet</a></h3></div>
      <div class="calendar__event-actions"><a class="calendar__button calendar__button--tickets" href="https://secure.tickster.com/lc7njg0117cu6l9">Biljetter</a></div></article>
      <article class="calendar__event"><div class="calendar__event-when"><time datetime="2026-11-27T19:00">19:00</time>
      <span class="calendar__event-place">På turné</span></div><div class="calendar__event-body"><span class="calendar__event-category">På turné</span>
      <h3 class="calendar__event-title"><a href="https://www.wermlandopera.com/evenemang/turne/en-sagolik-jul/">En sagolik jul</a></h3></div></article>"""
    out = fin(wermland_opera.parse(html))
    assert out[0]["genre"] == "Konsert" and out[0]["venue"] == "Bageriet" and out[0]["ticketUrl"].startswith("https://secure.tickster.com")
    assert out[1]["city"] == "" and out[1]["ticketUrl"] == ""


def test_nortic():
    ld = [{"@context": "http://www.schema.org", "@type": "Event", "name": "Macbeth 2027", "description": "[Opera]    ",
           "startDate": "2027-07-31T15:00", "endDate": "2027-07-31",
           "location": {"@type": "Place", "name": "Stora Scenen - Kopparberg"},
           "offers": {"@type": "Offer", "url": "https://tickets.nortic.se/dagny/show/357392", "availability": "https://schema.org/InStock"}},
          {"@type": "Event", "name": "Gåva till bevarandefonden 2027", "startDate": "2027-07-31T15:00"}]
    html = "<script>var x = undefined;</script>\n<script type='application/ld+json'>\n\n  " + json.dumps(ld, indent=4) + "\n</script>"
    out = fin(nortic.parse_event_page(html, "opera-pa-skaret", "Kopparberg", "https://www.nortic.se/ticket/event/85865"))
    assert len(out) == 1
    assert (out[0]["title"], out[0]["date"], out[0]["time"], out[0]["genre"]) == ("Macbeth", "2027-07-31", "15:00", "Opera")
    assert nortic._EVENT_LINK_RE.findall('href="https://www.nortic.se/ticket/event/85865" x https://tickets.nortic.se/ticket/event/88540') == ["85865", "88540"]


def test_kgl_teater():
    base = {"startDate": "2026-11-27T19:30:00", "showName": "George Balanchines Nøddeknækkeren",
            "showUrl": "https://www.kglteater.dk/ballet/2627/noeddeknaekkeren/", "category": "Ballet",
            "canceled": False, "tixlyEventId": "90001", "tixlyBuyLink": "https://billet.kglteater.dk/da/buyingflow/tickets/1/90001/",
            "fullHouse": False, "tixlySoldOut": False, "tixlySaleStatusText": "FewTickets", "location": "Gamle Scene", "label": None}
    items = [base,
             {**base, "category": "Skuespil", "showName": "De små synger", "tixlyEventId": "2"},
             {**base, "category": "Rundvisning", "showName": "Rundvisning i Operaen", "tixlyEventId": "3"},
             {**base, "category": "Musical", "showName": "Evita", "location": "Operaen", "tixlyEventId": "4",
              "tixlySaleStatusText": "SoldOut", "startDate": "2026-11-27T19:00:00"}]
    out = fin(kgl_teater.parse(items))
    assert [o["title"] for o in out] == ["George Balanchines Nøddeknækkeren", "Evita"]
    assert out[0]["genre"] == "Balett/dans" and out[0]["status"] == "fa-biljetter" and out[0]["time"] == "19:30" and out[0]["city"] == "København"
    assert out[1]["genre"] == "Musikal" and out[1]["status"] == "utsalt"


def test_den_norske_opera():
    days = [{"date": "2026-12-01T00:00:00+01:00", "events": [
        {"time": "2026-12-01T18:00:00+01:00", "name": "Nøtteknekkeren", "scene": "Hovedscenen", "genres": ["ballett"],
         "buyLink": "https://billett.operaen.no/nb/buyingflow/tickets/45790/93189/", "buyButtonText": "Utsolgt",
         "productionPageLink": "/forestillinger/notteknekkeren-ballett/", "salesStatus": "SoldOut"},
        {"time": "2026-12-03T19:00:00+01:00", "name": "Orfeus i underverdenen", "scene": "Hovedscenen", "genres": ["opera"],
         "buyLink": "x", "buyButtonText": "Kjøp", "productionPageLink": "/forestillinger/orfeus/", "salesStatus": "FewTickets"},
        {"time": "2026-12-05T12:00:00+01:00", "name": "Drosselmeyers verksted", "scene": "Formidlingssenteret",
         "genres": ["ballett", "formidling"], "buyLink": "y", "salesStatus": "Normal"},
        {"time": "2026-12-05T12:00:00+01:00", "name": "Omvisning", "genres": ["omvisning"], "salesStatus": "Normal"}]}]
    out = fin(den_norske_opera.parse(days))
    assert len(out) == 3
    assert out[0]["status"] == "utsalt" and out[0]["genre"] == "Balett/dans" and out[0]["url"] == "https://www.operaen.no/forestillinger/notteknekkeren-ballett/"
    assert out[1]["genre"] == "Opera" and out[1]["status"] == "fa-biljetter" and out[1]["time"] == "19:00"
    assert out[2]["genre"] == "Balett/dans"


def test_tso():
    items = [{"t": "Opera: Ridder Blåskjeggs borg", "u": "https://www.tso.no/program/konserter/opera-ridder-blaskjeggs-borg",
              "d": "4. mars 2027", "p": "Olavshallen", "ct": "Opera", "so": False, "ts": "OnSale",
              "tl": "https://billetter.tso.no/nb/buyingflow/tickets/46383/94161/"},
             {"t": "TSOs julekonsert", "u": "https://www.tso.no/program/konserter/tsos-julekonsert", "d": "16. desember 2026",
              "p": "Olavshallen", "ct": "Populær", "so": True, "ts": "SoldOut", "tl": None},
             {"t": "Bach: Juleoratoriet", "u": "u3", "d": "3. desember 2026", "p": "Nidarosdomen", "ct": "", "so": False, "ts": None, "tl": None}]
    times = {items[0]["u"]: tso.times_from_page("<main>Kjøp billett 04 mar. 2027 Kl 19:00 Opera Varer i ca. 1,5 time</main>")}
    out = fin(tso.parse(items, times))
    assert (out[0]["title"], out[0]["date"], out[0]["time"], out[0]["genre"]) == ("Ridder Blåskjeggs borg", "2027-03-04", "19:00", "Opera")
    assert out[1]["date"] == "2026-12-16" and out[1]["status"] == "utsalt" and out[1]["genre"] == "Konsert"
    assert out[2]["genre"] == "Konsert"


def test_bergen():
    prog = BeautifulSoup("""<article class="performance fade-in"><figure class="image"><a href="https://bno.no/forestillinger/2026/x"></a></figure>
      <div class="body"><span>Spilleperiode: 13-18/03</span><h2>Barbereren i Sevilla</h2><div class="border-box">
      <a href="https://bno.no/forestillinger/2026/2027-barbereren-i-sevilla" class="button">Les mer</a>
      <a href="https://tix.no/nb/bno/specialoffer/uf5rltp6nwtnk" class="button ticket">Kjøp billetter</a></div></div></article>""", "lxml")
    prods = bergen_nasjonale_opera.parse_program(prog)
    assert prods[0]["title"] == "Barbereren i Sevilla" and prods[0]["period"] == "Spilleperiode: 13-18/03"
    today = date(2026, 11, 27)
    prose = """<main><p>Bergen Filharmoniske Orkester Edvard Grieg Kor Synges på norsk, tekstes på norsk og engelskVarighet ca. 3 timer,
      inkludert 30 minutter pause Premiere lørdag 13. mars 2027 kl. 18 Spilles også 15., 17. og 18. mars kl. 19
      </p><p>Innledning ved Gunnar Danbolt</p></main>"""
    out = fin(bergen_nasjonale_opera.parse_production(prose, prods[0], today))
    assert [(o["date"], o["time"]) for o in out] == [("2027-03-13", "18:00"), ("2027-03-15", "19:00"), ("2027-03-17", "19:00"), ("2027-03-18", "19:00")]
    assert out[0]["note"] == "premiere" and out[1]["ticketUrl"].startswith("https://tix.no")
    table = """<div class="table-container"><div class="table-row"><span class="details"><span class="date">23/01</span>
      <span class="day">Lørdag</span><span class="time">14.00</span><span class="venue">Operaen / Scene 2</span>
      <span class="mobile-ticket-info"><a href="https://billett.operaen.no/nb/buyingflow/tickets/45822/93308/#tixsp">Kjøp</a></span></span></div></div>"""
    out2 = fin(bergen_nasjonale_opera.parse_production(table, {**prods[0], "title": "Nattfolket / Oslo"}, today))
    assert out2[0]["date"] == "2027-01-23" and out2[0]["time"] == "14:00" and out2[0]["city"] == ""
    out3 = fin(bergen_nasjonale_opera.parse_production("<main>Ingen datoer</main>", {**prods[0], "period": "Spilleperiode: 09/12"}, today))
    assert out3[0]["date"] == "2026-12-09"


def test_jyske_opera():
    data = [{"dates": [
        {"id": 4564, "title": "Carmen", "ticketurl": "https://billet.musikhuset.dk/da/buyingflow/tickets/30422/",
         "url": "https://jyske-opera.dk/forestillinger/carmen/", "buytext": "Køb billet", "datetime": "2026-11-27T19:30:00",
         "location": {"name": "Musikhuset Aarhus", "zip": 8000}, "alttitle": "", "arrangement": "show", "text": "Aarhus Symfoniorkester"},
        {"id": 5026, "title": "Carmen", "alttitle": "Rappernes Bogklub læser Carmen", "ticketurl": "x", "url": "u",
         "buytext": "Adgang ved køb af billet", "datetime": "2026-11-30T16:00:00", "location": {"name": "Musikhuset Aarhus", "zip": 8000},
         "arrangement": "event", "text": "livepodcast"},
        {"id": 7, "title": "Julesang og Messingklang", "alttitle": "", "ticketurl": "y", "url": "v", "buytext": "Udsolgt",
         "datetime": "2026-12-08T19:30:00", "location": {"name": "Vejle Musikteater", "zip": 7100}, "arrangement": "show", "text": ""}]}]
    out = fin(jyske_opera.parse(data))
    assert (out[0]["title"], out[0]["time"], out[0]["genre"], out[0]["city"]) == ("Carmen", "19:30", "Opera", "Aarhus")
    assert out[1]["title"] == "Rappernes Bogklub læser Carmen" and out[1]["genre"] == "Övrigt"
    assert out[2]["genre"] == "Konsert" and out[2]["city"] == "" and out[2]["status"] == "utsalt" and out[2]["venue"] == "Vejle Musikteater"


def test_billetto_ld():
    ld = {"@context": "http://schema.org", "@type": "Event", "name": "Nuckan, Haggan, Änkan!",
          "startDate": "2027-02-04T19:00:00+01:00", "endDate": "2027-02-04T20:00:00+01:00",
          "location": {"@type": "Place", "name": "Rönnells Antikvariat", "address": {"addressLocality": "Stockholm"}},
          "offers": [{"@type": "Offer", "availability": "http://schema.org/SoldOut", "url": "https://billetto.se/e/nuckan-1677503"},
                     {"@type": "Offer", "availability": "http://schema.org/SoldOut", "url": "https://billetto.se/e/nuckan-1677503"}]}
    html = '<script type="application/ld+json">{"@type":"Organization","name":"Billetto"}</script>\n<script type="application/ld+json">' + json.dumps(ld) + "</script>"
    out = fin(nortic.parse_event_page(html, "den-andra-operan", "", "https://billetto.se/e/nuckan-1677503"))
    assert len(out) == 1 and out[0]["city"] == "Stockholm" and out[0]["status"] == "utsalt" and out[0]["time"] == "19:00"
    links = nortic._BILLETTO_RE.findall('href="https://billetto.se/e/nuckan-haggan-ankan-biljetter-1677503?utm_source=x"')
    assert links == [("se", "nuckan-haggan-ankan-biljetter-1677503")]


T0 = date(2026, 11, 27)


def test_datetext():
    assert find_dates('Verdis "Falstaff" den 7., 13. og 14. august 2027', T0) == [("2027-08-07", ""), ("2027-08-13", ""), ("2027-08-14", "")]
    assert [d for d, _ in find_dates("13.08.27 kl. 20.00 Premiere\n15-16. august kl. 20.00\n21-22 august kl. 20.00", T0, 2027)] == \
        ["2027-08-13", "2027-08-15", "2027-08-16", "2027-08-21", "2027-08-22"]
    assert find_dates("22/04 | 24/04", T0) == [("2027-04-22", ""), ("2027-04-24", "")]
    assert find_dates("Fredag 11. desember kl. 19.30", T0) == [("2026-12-11", "19:30")]
    assert find_dates("Vi ses 13.-22. august 2027", T0) == [("2027-08-13", "")]  # lång period: bara första dagen
    assert find_dates("Ingen datoer her, men 2027 og 25 år", T0) == []


def test_hedeland():
    html = """<html><body><nav>FORESTILLINGER</nav><div><p>Verdis "Falstaff" den 7., 13. og 14. august 2027</p><a>Læs mere</a>
      <a href="https://www.ticketmaster.dk/artist/verdi-falstaff-billetter/1510153">Køb</a></div></body></html>"""
    out = fin(small_operas.parse_hedeland(html, T0))
    assert [(o["title"], o["date"], o["time"]) for o in out] == [("Falstaff", "2027-08-07", "20:00"), ("Falstaff", "2027-08-13", "20:00"), ("Falstaff", "2027-08-14", "20:00")]
    assert out[0]["ticketUrl"].startswith("https://www.ticketmaster.dk")


def test_cph_festival():
    html = """<html><body><p>Vi ses 13.-22. august 2027</p><h2>2027</h2><p>En ny opera af Steingrimur Rohloff</p>
      <h3>DADA: X</h3><p>19. - 20. august 2027</p><p>En verden i opløsning. Kunst uden regler.</p></body></html>"""
    out = fin(small_operas.parse_cph(html, "https://www.operafestival.dk/", T0))
    assert [(o["title"], o["date"]) for o in out] == [("DADA: X", "2027-08-19"), ("DADA: X", "2027-08-20")]


def test_oscarsborg():
    html = """<p><strong>TURANDOT</strong></p><p>13.08.27 kl. 20.00 Premiere</p><p>15-16. august kl. 20.00</p>
      <p>18-19. august kl. 20.00</p><p>21-22 august kl. 20.00</p><p>Varighet forestilling: ca. 2 timer</p>
      <a href="https://www.ticketmaster.no/artist/turandot-oscarsborg-opera-billetter/1539153">Kjøp</a>"""
    out = fin(small_operas.parse_oscarsborg_post("Turandot 2027", "https://www.oscarsborgoperaen.no/2026/10/22/turandot-2027/", html, T0))
    assert [o["date"] for o in out] == ["2027-08-13", "2027-08-15", "2027-08-16", "2027-08-18", "2027-08-19", "2027-08-21", "2027-08-22"]
    assert out[0]["title"] == "Turandot" and out[0]["note"] == "premiere" and out[0]["time"] == "20:00" and out[1]["note"] == ""
    prog = "<h1>Program Oslofjord Operafestival 2027</h1><p>2.-4. august</p><p>Musica in Castello Les mer</p>"
    out2 = fin(small_operas.parse_oscarsborg_program(prog, T0))
    assert [(o["title"], o["date"]) for o in out2] == [("Musica in Castello", "2027-08-02"), ("Musica in Castello", "2027-08-03"), ("Musica in Castello", "2027-08-04")]


def test_trondelag():
    html = """<div data-elementor-type="jet-listing-items"><a href="https://www.operatrondelag.no/juleoperapub-pa-hjelseng-gard/" class="jet-listing-dynamic-link__link">UTSOLGT: Juleoperapub på Hjelseng gård</a>
      <div class="fdates"><span>10/12</span></div><a href="https://hjelseng-gard.hoopla.no/event/opera-pub">BILLETTER</a></div>
      <div data-elementor-type="jet-listing-items"><a href="https://www.operatrondelag.no/figaros-bryllup/" class="jet-listing-dynamic-link__link">Figaros Bryllup</a>
      <div class="fdates"><span>22/04</span><span>24/04</span></div><a href="https://tix.no/nb/kimenkulturhus/buyingflow/tickets/51639/">BILLETTER</a></div>"""
    out = fin(small_operas.parse_trondelag(html, T0))
    assert [(o["title"], o["date"], o["genre"], o["status"]) for o in out] == [
        ("Juleoperapub på Hjelseng gård", "2026-12-10", "Konsert", "utsalt"),
        ("Figaros Bryllup", "2027-04-22", "Opera", ""), ("Figaros Bryllup", "2027-04-24", "Opera", "")]
    assert out[1]["ticketUrl"].startswith("https://tix.no")


def test_nordfjord():
    html = """<div class="elementor-post__excerpt"><h3 class="movie-title"><a href="https://operahuset.no/hexe/">Hexe</a></h3><p class="movie-info">6 | 1 t</p>
      <div class="show"><date datetime="2026-11-27 17:30:00">27.11</date></div></div>
      <div class="elementor-post__excerpt"><h3><a href="https://operahuset.no/carmen/">Carmen</a></h3>
      <div class="show"><p class="show-date"><date datetime="2027-09-30 19:00:00">30.09</date></p><p class="show-location">Operasalen</p>
      <a href="https://checkout.ebillett.no/161/events/1/purchase" class="show-purchase">Kjøp billett</a></div></div>"""
    cards = small_operas.parse_nordfjord_cards(html)
    assert len(cards) == 1 and cards[0]["perfs"][0].date == "2027-09-30" and cards[0]["perfs"][0].time == "19:00"
    assert small_operas.is_opera_nordfjord_page("<header>Opera Nordfjord</header><main>Ylvis & Calle</main>") is False
    assert small_operas.is_opera_nordfjord_page("<main>Opera Nordfjord presenterer Carmen</main>") is True


def test_ringsaker_empty():
    html = """<div class="wp-block-group block-upcoming-events"><h2>Kommende arrangementer</h2><p>Ingen kommende arrangementer funnet.</p></div>"""
    assert small_operas.parse_ringsaker(html, T0) == []
    html2 = """<div class="block-upcoming-events"><div class="ev"><h3>Elskovsdrikken</h3><p>Lørdag 12. juni kl. 19.00, Moelv</p>
      <a href="https://www.ringsakeroperaen.no/begivenhet/elskovsdrikken/">Les mer</a></div></div>"""
    out = fin(small_operas.parse_ringsaker(html2, T0))
    assert [(o["title"], o["date"], o["time"]) for o in out] == [("Elskovsdrikken", "2027-06-12", "19:00")]


def test_reassign():
    import run
    import houses
    srcs = {s for s, _, _ in houses.REASSIGN}
    assert srcs <= set(run.FETCHERS)


def test_fnob():
    ev = [{"title": "Figaros bröllop", "link": "https://oopperabaletti.fi/sv/repertoar/figaros-brollop/", "meta": "Opera", "id": 321398,
           "location": "Huvudscenen", "status": "full", "buy_link": False, "title_override": "", "start_date": "2026-11-27 19:00:00"},
          {"title": "En magisk stund", "link": "l", "meta": "För barn", "id": 2, "location": "Almisalens foajé", "status": "some_left",
           "buy_link": "https://shop.oopperabaletti.fi/sv/select-your-own-seat/258417/", "title_override": "", "start_date": "2026-11-28 11:00:00"},
          {"title": "Gratis", "link": "l", "meta": "Gratisevenemang", "id": 3, "location": "", "status": "free", "buy_link": False,
           "title_override": "", "start_date": "2026-11-29 12:00:00"}]
    fi = [{**e, "title": t, "meta": m, "location": v, "link": l} for e, t, m, v, l in zip(ev,
          ["Figaron häät", "Taikatuokio", "Maksuton"], ["Ooppera", "Lapsille", "Maksuton tapahtuma"],
          ["Päänäyttämö", "Alminsalin lämpiö", ""], ["https://oopperabaletti.fi/ohjelmisto/figaron-haat/", "l", "l"])]
    en = [{**ev[0], "title": "Le nozze di Figaro", "location": "Main Stage", "link": "https://oopperabaletti.fi/en/repertoire/le-nozze-di-figaro/"}]
    out = fin(nordic_text.parse_fnob(fi, {"sv": ev, "en": en}))
    assert (out[0]["title"], out[0]["genre"], out[0]["status"], out[0]["time"]) == ("Figaron häät", "Opera", "utsalt", "19:00")
    assert out[0]["titles"] == {"fi": "Figaron häät", "sv": "Figaros bröllop", "en": "Le nozze di Figaro"}
    assert out[0]["venues"]["sv"] == "Huvudscenen" and out[0]["urls"]["en"].endswith("/le-nozze-di-figaro/")
    assert out[1]["genre"] == "Barn & unga" and out[1]["status"] == "fa-biljetter" and out[2]["genre"] == "Övrigt"
    assert "titles" in out[1] and set(out[1]["titles"]) == {"fi", "sv"}


def test_alternates():
    page = """<html><body><nav><a href="https://operafestival.fi/en/">EN</a></nav>
      <a href="https://operafestival.fi/en/ohjelmisto/themagicflute27/">EN</a></body></html>"""
    assert nordic_text.alternates(page, "https://operafestival.fi/ohjelmisto/taikahuilu27/") == {"en": "https://operafestival.fi/en/ohjelmisto/themagicflute27/"}
    hl = '<link rel="alternate" hreflang="sv-SE" href="https://x.fi/sv/a/"><link rel="alternate" hreflang="fi" href="https://x.fi/a/">'
    assert nordic_text.alternates(hl, "https://x.fi/a/") == {"sv": "https://x.fi/sv/a/"}


def test_event_page_savonlinna():
    html = """<html><head><meta property="og:title" content="Andrea Chénier - Savonlinnan Oopperajuhlat"></head><body><main>
      <p>Ensi-ilta9.7.2027 klo 19</p><h2>Esitykset Olavinlinnassa</h2><p>Liput alkaen 69,90 €</p>
      <p>Perjantai</p><p>9.7.2027 klo 19:00</p><a href="https://www.lippu.fi/event/123">Osta</a>
      <p>Tiistai</p><p>13.7.2027 klo 19:00</p><p>Lipunmyynti alkaa 1.12.2026 klo 10</p>
      <p>Ranskan vallankumous on saavuttamassa huippunsa. Runoilija Andrea Chénier rakastuu Maddalena di Coignyyn, nuoreen aatelisnaiseen, jolta vallankumous on riistänyt kaiken 1.1.2027.</p>
      </main></body></html>"""
    cfg = nordic_text.TEXT_SOURCES["savonlinna"]
    out = fin(nordic_text.parse_event_page(html, "https://operafestival.fi/ohjelmisto/andreachenier27/", "savonlinna", cfg, T0))
    assert [(o["title"], o["date"], o["time"]) for o in out] == [("Andrea Chénier", "2027-07-09", "19:00"), ("Andrea Chénier", "2027-07-13", "19:00")]
    assert out[0]["ticketUrl"] == "https://www.lippu.fi/event/123" and out[0]["venue"] == "Olavinlinna"


def test_event_page_ilmajoki_and_require():
    html = """<html><body><h1>Säröillä</h1><main><p>Uusi ooppera 10.-20.6.2027</p><p>Pe 11.6. klo 18 (kantaesitys)</p><p>La 12.6. klo 13</p></main></body></html>"""
    out = fin(nordic_text.parse_event_page(html, "https://www.musiikkijuhlat.fi/saroilla.html", "ilmajoki", nordic_text.TEXT_SOURCES["ilmajoki"], T0))
    assert [(o["date"], o["time"], o["genre"]) for o in out] == [("2027-06-11", "18:00", "Opera"), ("2027-06-12", "13:00", "Opera")]
    play = "<html><body><h1>Kaos</h1><main><p>04.12.26 kl. 20</p><p>Sjónleikur</p></main></body></html>"
    assert nordic_text.parse_event_page(play, "https://www.tjodpallur.fo/leikir/kaos", "tjodpallur-opera", nordic_text.TEXT_SOURCES["tjodpallur-opera"], T0) == []
    links = nordic_text.event_links('<a href="/saroilla.html">x</a><a href="/varaa-liput-813133.html">y</a>', "https://www.musiikkijuhlat.fi/",
                                    nordic_text.TEXT_SOURCES["ilmajoki"])
    assert links == ["https://www.musiikkijuhlat.fi/saroilla.html"]


def test_english_versions():
    # Kungliga Operan
    perfs = [{"performanceId": 1, "productionId": 130, "performanceDate": "2026-12-02T17:00:00+00:00", "availability": 5}]
    out = fin(kungliga_operan.parse(perfs, {"130": {"name": "Nötknäpparen", "url": "/forestallningar/notknapparen", "genres": ["Balett/dans"]}},
                                    {"130": {"name": "The Nutcracker", "url": "/en/productions/the-nutcracker"}}))
    assert out[0]["titles"] == {"sv": "Nötknäpparen", "en": "The Nutcracker"} and out[0]["urls"]["en"] == "https://www.operan.se/en/productions/the-nutcracker"
    # GöteborgsOperan: samma id på båda språken
    ev = {"__typename": "event", "id": "121191", "eventGroupTitle": "Trollflöjten", "title": "Trollflöjten", "location": "GöteborgsOperan",
          "scene": "Stora scenen", "url": "/forestallningar/sasong-2026-2027/trollflojten/", "tag": "opera",
          "date": {"formatted": "2026-12-18", "time": "19:00"}, "cta": {"label": "Köp", "url": "https://biljett.opera.se/sv/buyingflow/tickets/1/121191/"}}
    ev_en = {**ev, "eventGroupTitle": "The Magic Flute", "title": "The Magic Flute", "scene": "Main Stage",
             "url": "/en/what-s-on/season-2026-2027/the-magic-flute/", "date": {"formatted": "12/18/2026", "time": "19:00"}}
    out = fin(goteborgsoperan.parse(_gbg_html([ev]), _gbg_html([ev_en])))
    assert out[0]["titles"]["en"] == "The Magic Flute" and out[0]["venues"]["en"] == "Main Stage, GöteborgsOperan"
    assert out[0]["urls"]["en"] == "https://www.opera.se/en/what-s-on/season-2026-2027/the-magic-flute/" and out[0]["title"] == "Trollflöjten"
    # Det Kongelige Teater: kopplas via biljett-id + starttid
    da = {"startDate": "2026-11-27T19:30:00", "showName": "George Balanchines Nøddeknækkeren", "showUrl": "https://www.kglteater.dk/ballet/x/",
          "category": "Ballet", "tixlyEventId": "9", "tixlyBuyLink": "b", "location": "Gamle Scene"}
    en = {**da, "showName": "George Balanchine's The Nutcracker", "category": "Ballet", "location": "The Old Stage", "showUrl": "https://www.kglteater.dk/en/ballet/x/"}
    out = fin(kgl_teater.parse([da], [en]))
    assert out[0]["titles"]["en"] == "George Balanchine's The Nutcracker" and out[0]["venues"]["en"] == "The Old Stage" and out[0]["genre"] == "Balett/dans"
    # Den Norske Opera: kopplas via biljettlänkens föreställnings-id
    no = [{"events": [{"time": "2026-12-01T18:00:00+01:00", "name": "Nøtteknekkeren", "scene": "Hovedscenen", "genres": ["ballett"],
                       "buyLink": "https://billett.operaen.no/nb/buyingflow/tickets/45790/93189/", "productionPageLink": "/forestillinger/notteknekkeren-ballett/"}]}]
    en_days = [{"events": [{"time": "2026-12-01T18:00:00+01:00", "name": "The Nutcracker", "scene": "Main Stage", "genres": ["ballett"],
                            "buyLink": "https://billett.operaen.no/en/buyingflow/tickets/45790/93189/", "productionPageLink": "/en/Productions/the-nutcracker-ballet/"}]}]
    out = fin(den_norske_opera.parse(no, en_days))
    assert out[0]["titles"] == {"nb": "Nøtteknekkeren", "en": "The Nutcracker"} and out[0]["venues"]["en"] == "Main Stage"
    # Norrlandsoperan: kopplas via biljettsystemets id
    sessions = [{"id": 1, "title": {"rendered": "Mozarts Zaïde"}, "meta": {"event": 26092, "session_date": "2027-05-08", "session_time": "19:00"}}]
    events = {26092: {"id": 26092, "title": {"rendered": "Mozarts Zaïde"}, "link": "https://norrlandsoperan.se/forestallningar/mozarts-zaide/",
                      "meta": {"event_primary_category": "opera", "event_api_guid": "34213"}}}
    en_by_guid = {"34213": {"title": {"rendered": "Mozart&#8217;s *Zaïde*"}, "link": "https://norrlandsoperan.se/en/programme/mozarts-zaide/"}}
    out = fin(norrlandsoperan.parse(sessions, events, {"opera": "Opera"}, en_by_guid))
    assert out[0]["titles"]["en"] == "Mozart’s Zaïde" and out[0]["urls"]["en"].endswith("/en/programme/mozarts-zaide/")
    # utan engelsk version: bara originalspråket sparas
    out = fin(den_norske_opera.parse(no))
    assert out[0]["titles"] == {"nb": "Nøtteknekkeren"}


def test_genre_normalization():
    assert normalize_genre("Barn och familj") == "Barn & unga"
    assert normalize_genre("barn & unga") == "Barn & unga"
    assert normalize_genre("Visning") == "Övrigt"
    assert normalize_genre("", "Trettondagskonsert med bal") == "Konsert"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK", name)


def test_folkoperan_production_match():
    from sources import folkoperan as fo
    html = ('<a href="/uppsattningar/falstaff/"><h3>Falstaff</h3><p>Verdi</p></a>'
            '<a href="https://folkoperan.se/uppsattningar/nyarsgala/">Nyårsgala 2026</a>'
            '<a href="/uppsattningar/">Alla</a>')
    pages = fo.production_pages(html)
    assert fo.match_page("Falstaff", pages) == "https://folkoperan.se/uppsattningar/falstaff/"
    assert fo.match_page("Nyårsgala", pages) == "https://folkoperan.se/uppsattningar/nyarsgala/"
    assert fo.match_page("Något helt annat", pages) == ""
