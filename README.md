# Nordic Opera Performances

Föreställningar på operahus och sommaroperor i Sverige, Danmark, Norge, Finland och på Färöarna samlade i en Android-app, från idag och framåt.
(Under ikonen på hemskärmen står det kortare "Nordic Opera"; ändra i `android/app/src/main/res/values/launcher.xml`.)
Samma upplägg som konsertappen: GitHub hämtar spelschemat en gång per dygn och appen läser filen.

```
operahusens webbplatser ──(varje natt, GitHub Actions)──▶ data/forestallningar.json ──▶ appen
```

## Operahus som hämtas

| Operahus | Hur datan hämtas |
|---|---|
| Kungliga Operan | Operans eget JSON-API (webapi.operan.se) |
| GöteborgsOperan | Kalendersidan (data inbäddad i sidan) |
| Malmö Opera | Kalendervyn på startsidan, sida för sida |
| Norrlandsoperan | WordPress-API (en post per föreställning) |
| Folkoperan | Sidan "Köp biljetter" |
| Wermland Opera | Kalendariet |
| Läckö Slottsopera | Biljettsystemet Nortic (länkar från lackoslott.se) |
| Vadstena-Akademien | Nortic (länkar från vadstena-akademien.org) |
| Opera på Skäret | Nortic (arrangörens evenemangslista) |
| Den Andra Operan | Billetto/Nortic-länkar från denandraoperan.se och Billetto-arrangörssidan |
| Den Jyske Opera, Aarhus + turné | Operans kalender-JSON |
| Det Kongelige Teater, København | Teatrets kalender-API (opera, balett, konsert, musikal, dans – inte skådespel och rundvisningar) |
| Opera Hedeland | Datumen i texten på startsidan ("Falstaff den 7., 13. og 14. august 2027") |
| Copenhagen Opera Festival | Titel + datumrad på startsidan och programsidan för året |
| Kongelig Sommeropera | Kommer via Det Kongelige Teaters kalender (titlar med "sommeropera") |
| Den Norske Opera & Ballett, Oslo | Operans kalender-API, månad för månad (inte omvisningar) |
| Bergen Nasjonale Opera | Programsidan + varje produktionssida (datumtabell eller löptext) |
| Oscarsborgoperaen, Drøbak | Inläggen på webbplatsen (t.ex. "Turandot 2027" med alla datum) + festivalprogrammet |
| Opera ved fjorden, Os | Kommer via Bergen Nasjonale Operas program |
| Opera Trøndelag (Steinvikholm) | Listan på startsidan (titel, datum 22/04, biljettlänk) |
| Opera Nordfjord | Operahuset Nordfjords program – bara det som Opera Nordfjord själva sätter upp |
| Ringsakeroperaen | "Kommende arrangementer" på startsidan |
| Finlands nationalopera och -balett, Helsingfors | Operans eget kalender-API (titlar på svenska) |
| Savonlinna Opera Festival, Nyslott | Varje produktionssida ("Perjantai 9.7.2027 klo 19:00") |
| Tampereen Ooppera | Tampere-talos sida för operan + varje evenemangssida |
| Vaasan Ooppera | Produktionssidorna på vaasanooppera.fi |
| Opera i Uleåborg | Oulu Sinfonias konsertsidor som handlar om opera |
| Ilmajoki Music Festival | Produktionssidorna ("Pe 11.6. klo 18") |
| Helsinki Contemporary Opera Festival | Programsidorna på oopperakesa.fi |
| opera.fo, Tórshavn | Sidorna på opera.fo |
| Tjóðpallur Føroya | Föreställningssidor som nämner opera |
| Trondheim Symfoniorkester & Opera | Programmets JSON + konsertsidan för klockslag (både konserter och opera) |

De minsta operorna skriver bara datumen i löptext. Den gemensamma tolken (`scraper/datetext.py`)
klarar svenska, danska och norska skrivsätt, men saknas klockslag i texten visas föreställningen utan tid
(Opera Hedeland visas med 20:00, som är deras vanliga starttid).

Samproduktioner som listas av två hus (t.ex. Nattfolket, Bergen + Oslo) visas bara en gång,
under det hus som står först i listan. Dubbletter känns igen på biljettlänken.

Sommaroperorna och Den Andra Operan (fritt kompani som spelar i projekt) visar 0 föreställningar tills biljettsläppet: datumen dyker upp i appen automatiskt
när operan lägger ut biljetterna (Läckö har aviserat biljettsläpp 1 december).

Alla genrer är med (opera, operett, balett/dans, musikal, konsert, barn & unga, övrigt) och kan filtreras i appen.

## I appen

- **Ort:** skriv en ort (t.ex. Göteborg eller København – accenter behövs inte) så visas bara föreställningar där. Förslag dyker upp medan man skriver. Orten sparas till nästa gång.
- **Från datum:** välj ett valfritt framtida datum så börjar listan där.
- **Operahus och genre:** filterknapparna under.
- **Sök:** förstoringsglaset i titelraden söker på föreställning eller operahus.

## Språk

Appen finns på engelska, svenska, danska, norska (bokmål), nynorska, finska och isländska och följer telefonens språk.
På Android 13 och senare kan man också välja språk bara för appen: *Inställningar → Appar → Operaappen → Språk*.
Andra språk får engelska.

Texterna ligger i `android/app/src/main/res/values*/strings.xml` (engelska i `values/`).
När ett operahus publicerar sitt program på flera språk sparas titel, scen och länk på alla språken
(engelska finns för Kungliga Operan, GöteborgsOperan, Norrlandsoperan, Det Kongelige Teater, Den Norske Opera,
Bergen Nasjonale Opera, Finlands nationalopera – som också har svenska – och Savonlinna), och appen väljer
efter telefonens språk – annars närmaste språk (t.ex. svenska för danska och norska läsare), sedan engelska,
sedan originalet. Ortsrutan känner igen båda namnen på tvåspråkiga orter (Helsingfors/Helsinki, Vasa/Vaasa …).
Övrig data från operahusen (titlar, spelplatser, operahusens egna anteckningar) visas som operahusen skriver den;
genrer, statusar och vanliga anteckningar som "Premiär" översätts i appen.

I Play Console kan butikstexten läggas in på samma sju språk under *Butiksnärvaro → Huvudbutiksinfo → Hantera översättningar*.

## Kom igång

1. **Skapa ett publikt repo** på GitHub, t.ex. `operaappen`, och ladda upp innehållet i den här mappen.
   Repot måste vara publikt så att appen kan läsa datafilen utan inloggning.
2. **Kör första hämtningen:** fliken *Actions* → *Hämta föreställningar* → *Run workflow*.
   Efter någon minut finns `data/forestallningar.json` i repot. Sedan körs den automatiskt varje natt.
3. **Bygg appen:** *Actions* → *Bygg Android-appen* → *Run workflow*. Under körningen finns en
   APK att ladda ner och installera på en telefon för test. Datafilens adress sätts automatiskt
   utifrån repots namn.
4. **Google Play:** lägg upp signeringsnyckeln som hemligheter (se nedan), så bygger samma
   körning även en AAB-fil som laddas upp i Play Console som en ny app.

### Signering för Google Play

Använd en egen uppladdningsnyckel för operaappen (inte samma som konsertappen behöver användas,
men det går också bra). Skapa en med Android Studio (*Build → Generate Signed Bundle*) eller:

```
keytool -genkeypair -v -keystore operaappen-upload.jks -alias operaappen -keyalg RSA -keysize 2048 -validity 10000
```

Lägg sedan in under *Settings → Secrets and variables → Actions → Secrets*:

| Namn | Värde |
|---|---|
| `KEYSTORE_BASE64` | innehållet i `base64 -w0 operaappen-upload.jks` |
| `KEYSTORE_PASSWORD` | lösenordet till nyckelfilen |
| `KEY_ALIAS` | `operaappen` (eller det alias du valde) |
| `KEY_PASSWORD` | nyckelns lösenord |

Spara nyckelfilen och lösenorden säkert – de behövs för varje uppdatering av appen.
Versionsnumret (versionCode) räknas upp automatiskt för varje bygge.

### App-id

App-id:t är `se.operaappen.app` i `android/app/build.gradle.kts` (`applicationId`).
Byt gärna till något eget, t.ex. samma början som konsertappen, *innan* första uppladdningen till Play –
det går inte att ändra efteråt.

## Bygga lokalt i Android Studio

Öppna mappen `android/`. Byt `DITT-GITHUB-NAMN` i `android/gradle.properties` mot ditt GitHub-namn
så hämtar även lokala byggen rätt fil. För signerade byggen lokalt: skapa `android/keystore.properties`
med `storeFile`, `storePassword`, `keyAlias`, `keyPassword` (filen ignoreras av git).

## Om en webbplats ändras

Om ett operahus bygger om sin webbplats kan hämtningen för just det huset sluta fungera.
Då behåller appen husets föreställningar från förra lyckade hämtningen och de övriga husen
uppdateras som vanligt. I `data/forestallningar.json` står `"status": "gammal-data"` och
felet under `houses`, och i Actions-loggen syns `[FEL]` för huset.

Koden för varje operahus ligger i `scraper/sources/`. Tester mot sparade sidutdrag: `python -m pytest scraper/tests`.
Kör hämtningen lokalt: `pip install -r scraper/requirements.txt && python scraper/run.py`
(eller bara vissa hus: `python scraper/run.py malmo-opera folkoperan`).

## Lägga till fler operahus

1. Lägg till huset i `scraper/houses.py`.
2. Skriv en `fetch()` i `scraper/sources/` som returnerar `Performance`-objekt
   (eller lägg till huset i `nortic.py` om det säljer biljetter via Nortic).
3. Koppla in den i `FETCHERS` i `scraper/run.py`.
