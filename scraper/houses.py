"""Operahusen som appen hämtar från. Ordningen här är ordningen i appens filter."""

HOUSES = [
    # Sverige
    {"id": "kungliga-operan", "name": "Kungliga Operan", "city": "Stockholm", "country": "SE", "web": "https://www.operan.se", "season": "året runt"},
    {"id": "goteborgsoperan", "name": "GöteborgsOperan", "city": "Göteborg", "country": "SE", "web": "https://www.opera.se", "season": "året runt"},
    {"id": "malmo-opera", "name": "Malmö Opera", "city": "Malmö", "country": "SE", "web": "https://www.malmoopera.se", "season": "året runt"},
    {"id": "norrlandsoperan", "name": "Norrlandsoperan", "city": "Umeå", "country": "SE", "web": "https://norrlandsoperan.se", "season": "året runt"},
    {"id": "folkoperan", "name": "Folkoperan", "city": "Stockholm", "country": "SE", "web": "https://folkoperan.se", "season": "året runt"},
    {"id": "wermland-opera", "name": "Wermland Opera", "city": "Karlstad", "country": "SE", "web": "https://www.wermlandopera.com", "season": "året runt"},
    {"id": "lacko-slottsopera", "name": "Läckö Slottsopera", "city": "Lidköping", "country": "SE", "web": "https://www.lackoslott.se/aktivitet/opera/", "season": "sommar"},
    {"id": "vadstena-akademien", "name": "Vadstena-Akademien", "city": "Vadstena", "country": "SE", "web": "https://www.vadstena-akademien.org", "season": "sommar"},
    {"id": "den-andra-operan", "name": "Den Andra Operan", "city": "Stockholm", "country": "SE", "web": "https://denandraoperan.se", "season": "projekt"},
    {"id": "opera-pa-skaret", "name": "Opera på Skäret", "city": "Kopparberg", "country": "SE", "web": "https://operapaskaret.se", "season": "sommar"},
    # Danmark
    {"id": "kgl-teater", "name": "Det Kongelige Teater", "city": "København", "country": "DK", "web": "https://www.kglteater.dk", "season": "året runt"},
    {"id": "opera-hedeland", "name": "Opera Hedeland", "city": "Hedehusene", "country": "DK", "web": "https://operahedeland.dk", "season": "sommar"},
    {"id": "cph-opera-festival", "name": "Copenhagen Opera Festival", "city": "København", "country": "DK", "web": "https://www.operafestival.dk", "season": "sommar"},
    {"id": "kongelig-sommeropera", "name": "Kongelig Sommeropera", "city": "", "country": "DK", "web": "https://www.kglteater.dk", "season": "sommar"},
    {"id": "jyske-opera", "name": "Den Jyske Opera", "city": "Aarhus", "country": "DK", "web": "https://www.jyske-opera.dk", "season": "året runt"},
    # Norge
    {"id": "den-norske-opera", "name": "Den Norske Opera & Ballett", "city": "Oslo", "country": "NO", "web": "https://www.operaen.no", "season": "året runt"},
    {"id": "bergen-nasjonale-opera", "name": "Bergen Nasjonale Opera", "city": "Bergen", "country": "NO", "web": "https://www.bno.no", "season": "året runt"},
    {"id": "oscarsborgoperaen", "name": "Oscarsborgoperaen", "city": "Drøbak", "country": "NO", "web": "https://www.oscarsborgoperaen.no", "season": "sommar"},
    {"id": "opera-ved-fjorden", "name": "Opera ved fjorden", "city": "Os", "country": "NO", "web": "https://www.bno.no", "season": "sommar"},
    {"id": "opera-trondelag", "name": "Opera Trøndelag (Steinvikholm)", "city": "Trøndelag", "country": "NO", "web": "https://www.operatrondelag.no", "season": "distrikt"},
    {"id": "opera-nordfjord", "name": "Opera Nordfjord", "city": "Nordfjordeid", "country": "NO", "web": "https://operahuset.no", "season": "distrikt"},
    {"id": "ringsakeroperaen", "name": "Ringsakeroperaen", "city": "Ringsaker", "country": "NO", "web": "https://www.ringsakeroperaen.no", "season": "distrikt"},
    {"id": "tso", "name": "Trondheim Symfoniorkester & Opera", "city": "Trondheim", "country": "NO", "web": "https://www.tso.no", "season": "året runt"},
]

HOUSES += [
    # Finland
    {"id": "suomen-kansallisooppera", "name": "Finlands nationalopera och -balett", "city": "Helsingfors", "country": "FI", "web": "https://oopperabaletti.fi", "season": "året runt"},
    {"id": "tampereen-ooppera", "name": "Tampereen Ooppera", "city": "Tammerfors", "country": "FI", "web": "https://www.tampere-talo.fi/tampereenooppera/", "season": "distrikt"},
    {"id": "oulun-ooppera", "name": "Opera i Uleåborg (Oulu Sinfonia)", "city": "Uleåborg", "country": "FI", "web": "https://oulusinfonia.fi", "season": "distrikt"},
    {"id": "savonlinna", "name": "Savonlinna Opera Festival", "city": "Nyslott", "country": "FI", "web": "https://operafestival.fi", "season": "sommar"},
    {"id": "ilmajoki", "name": "Ilmajoki Music Festival", "city": "Ilmajoki", "country": "FI", "web": "https://www.musiikkijuhlat.fi", "season": "sommar"},
    {"id": "helsingin-oopperakesa", "name": "Helsinki Contemporary Opera Festival", "city": "Helsingfors", "country": "FI", "web": "https://www.oopperakesa.fi", "season": "sommar"},
    # Färöarna
    {"id": "opera-fo", "name": "opera.fo", "city": "Tórshavn", "country": "FO", "web": "https://www.opera.fo", "season": "projekt"},
    {"id": "tjodpallur-opera", "name": "Tjóðpallur Føroya (opera)", "city": "Tórshavn", "country": "FO", "web": "https://www.tjodpallur.fo", "season": "projekt"},
]

HOUSE_BY_ID = {h["id"]: h for h in HOUSES}

# Föreställningar som ett annat hus publicerar men som visas som eget hus i appen:
# (hus som hämtar, mönster i titeln, hus som visas)
REASSIGN = [
    ("kgl-teater", r"sommeropera", "kongelig-sommeropera"),
    ("bergen-nasjonale-opera", r"opera ved fjorden", "opera-ved-fjorden"),
]

COUNTRIES = {"SE": "Sverige", "DK": "Danmark", "NO": "Norge", "FI": "Finland", "FO": "Färöarna"}
