---
title: "Ograničenja i provjere"
nav_order: 9
lang: "hr"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Ograničenja i što je provjereno {#limits-and-what-is-verified}

Iskren popis: što alati ne rade i što nije provjereno na pokrenutoj igri.

## Telemetrija {#telemetry}

| Snimač | Stanje |
|---|---|
| Forza | Izgrađen na službenoj dokumentaciji Data Out; raspored se prepoznaje iz samih paketa. Čitač FH Companion `.tele.gz` u pregledniku provjeren je na pravim krugovima. |
| AC, ACC, AC EVO, AC Rally | Testirano na sintetičkim stranicama izgrađenim iz objavljenih rasporeda. **Još nije pokrenuto na pravim igrama.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testirano na paketima izgrađenim iz dokumentiranih rasporeda. **Još nije pokrenuto na pravim igrama.** Osi, stav i jedinice brzine RBR-a nisu dokumentirani i obrađuju se iz podataka. |
| BeamNG.drive | Snimač je testiran na paketima izgrađenim iz strukture modifikacije. **Modifikacija nije pokrenuta u igri.** |
| Trackmania | Čitač CSV-a u pregledniku je testiran. **Dodatak nije pokrenut u igri.** Učitava se samo u razvojnom načinu Openplanet-a. |
| iRacing | Čitač `.ibt` datoteka u pregledniku testiran je na sintetičkoj datoteci. |

Druga ograničenja telemetrije:

- Forzina normalizacija klizanja nije dokumentirana; klizanje Kunosa skalirano je prema tipičnom
  vrhu za asfalt, što je aproksimacija.
- Smjer nekih bočnih osi u okviru automobila (Kunos, DiRT) dokumentiran je u oba smjera; veličina
  kuta driftanja je pouzdana, njezin predznak nije.
- Nijedna rally igra ne šalje klizanje guma; ono se izvodi u pregledniku. RBR ne šalje brzine kotača.
- Podloga rally etape zapisuje se samo kad je dan `--surface`; inače datoteka nijedne ne navodi i
  preglednik je zaključuje (naziv etape ili događaja, zatim stil vožnje, ohlapno po zadanom).
- Detekcija kruga bez brojača krugova (AC EVO, AC Rally, BeamNG) koristi točku na kojoj je snimanje
  počelo kao crtu, pa snimanje započnite na startnoj liniji.
- Reset vozila u BeamNG-u zatvara otvoreni krug u tom trenutku: zapisuje se kao djelomično
  izvođenje kad je prešao najmanju udaljenost (300 m), a inače se odbacuje.
- `route` sprema otprilike svake 2 sekunde dok se vozi; pad ili ubijeni proces gubi najviše pozicije
  od zadnjeg spremanja.
- Forza Horizon ne šalje naziv staze, pa Forza datoteke krugova imaju `"track": null`; Forza
  Motorsport (2023) šalje samo broj, zadržan kao `lap.trackOrdinal`.

## Rekonstrukcija {#reconstruction}

- **Dubina se procjenjuje, ne čita se.** Cijena toga je da se proces igre nikad ne dira
  igre.
- **Vidno polje se pretpostavlja, ne mjeri.** Preusko, i razina se rekonstruira dublje nego što jest.
- **Globalno mjerilo** dolazi iz pretpostavljene visine kamere (1,15 m u prozoru), ili iz
  telemetrije. Mjeri se na prvom ključnom kadru; kad on nema upotrebljivo tlo, pokušavaju se sljedeći
  ključni kadrovi (do 30 kadrova), a mjerilo nađeno kasnije primjenjuje se na cijelu razinu pri
  zapisivanju. Redak "Size:" u prozoru kaže što se dogodilo; kad nigdje nema tla, skeniranje ostaje
  bez jedinica. Veličina voksela je tada u jedinicama prvog kadra, pa se njezina veličina u metrima
  razlikuje od postavke. Rekonstrukcije izvan mreže su u vlastitim jedinicama rješavača.
- **Zatvaranje petlje je isključeno** i ne stvara graf pozicija ni kad se uključi u kodu; drift je ograničen
  samo kvalitetom praćenja od kadra do kadra.
- **Prilagodba snopa unutar prozora postoji, ali nije povezana**; na pravim snimkama se srušila.
- **Površina je ponderirana zauzetost, a ne TSDF**: tanke strukture i slobodan prostor lošiji su nego
  što bi dao TSDF.
- **Nema atlasa tekstura.** Boja je po vrhu (`COLOR_0`), miješa se iz 4 najbolja pogleda među 160
  sačuvanih kadrova. Test zaklona je grub: provjerava se protiv vlastitih vrhova mreže u dubinskom
  spremniku od 2 piksela, pa zaklon kojeg mreža ne sadrži (automobil koji prolazi) nije uhvaćen.
- **Voda se nikad ne označava**; sve je tlo ili struktura.
- **Rješavanje unaprijed nije uživo**: treba prvo snimka. Prilagodljivo ponovno rješavanje teških
  dijelova nije izgrađeno.
- **Položaji iz telemetrije** postavljaju kameru na automobil (pomak kamere iza vozila nije poznat).
  Pozicije se uzimaju kako ih Forza šalje (Y gore, kao u datotekama krugova); smjerovi yaw, pitch i
  roll očitani su iz snimljenih krugova (smjer vožnje, nagib, koja strana ovjesa se sabija), a ne iz
  kamere pokrenute igre.
- Prekrivni sloj ne može crtati preko **izvornog cijelog zaslona**; koristite bezrubi prozorski način.
- Globalne tipkovnice, prozirni prekrivni sloj koji propušta klikove i uživo snimanje rade **samo na
  Windowsu**.
- Zatvaranje prozora ne nudi spremanje.

## Što je izmjereno {#what-is-measured}

- `tests/test_accuracy.py`: sintetička soba s poznatom putanjom i analitičkom dubinom - smješteni
  kadrovi, pogreška putanje, prijeđena udaljenost, veličina sobe, površina na zidovima
  ([Rekonstrukcija razine](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: cesta poznate širine, prijeđena izvan središta, rekonstruira svoju
  širinu.
- `tests/test_track_scale.py`: izvlačenje površine na mjerilu staze, memorija proporcionalna onome
  što je skenirano, blokovi koji se spajaju u jednu površinu.
- `tests/test_glb.py` plus vlastiti testovi preglednika: ugovor `.glb` s obje strane.
- Kako mrežu dubine ide na pravom igranju nije nešto što sintetička scena može odgovoriti i nije
  mjereno skupom testova.
