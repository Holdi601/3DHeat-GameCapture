---
title: "Ograničenja i provjera"
nav_order: 9
lang: "bs"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Ograničenja i šta je provjereno {#limits-and-what-is-verified}

Iskren spisak: šta alati ne rade i šta nije provjereno na pokrenutoj igri.

## Telemetrija {#telemetry}

| Snimač | Stanje |
|---|---|
| Forza | Izgrađen prema službenoj dokumentaciji Data Out; raspored se otkriva iz samih paketa. Čitač `.tele.gz` datoteka FH Companion u pregledaču provjeren je na stvarnim krugovima. |
| AC, ACC, AC EVO, AC Rally | Testirano na sintetičkim stranicama izgrađenim prema objavljenim rasporedima. **Još nije pokrenuto na stvarnim igrama.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testirano na paketima izgrađenim prema dokumentiranim rasporedima. **Još nije pokrenuto na stvarnim igrama.** Ose, položaj i jedinice brzine u RBR-u nisu dokumentirani i obrađuju se iz podataka. |
| BeamNG.drive | Snimač je testiran na paketima izgrađenim iz structa moda. **Mod nije pokrenut u igri.** |
| Trackmania | Čitač CSV-a u pregledaču je testiran. **Dodatak nije pokrenut u igri.** Učitava se samo u Openplanetovom razvojnom načinu. |
| iRacing | Čitač `.ibt` datoteka u pregledaču testiran je na sintetičkoj datoteci. |

Ostala ograničenja telemetrije:

- Normalizacija proklizavanja u Forzi nije dokumentirana; Kunos proklizavanje se skalira tipičnim vrhom
  na asfaltu, što je aproksimacija.
- Smjer nekih bočnih osa u okviru automobila (Kunos, DiRT) dokumentiran je na oba načina; veličina
  ugla zanošenja je pouzdana, njegov predznak nije.
- Nijedna reli igra ne šalje proklizavanje guma; ono se izvodi u pregledaču. RBR ne šalje brzine točkova.
- Podloga reli etape zapisuje se samo kad je dat `--surface`; inače je datoteka ne navodi
  i pregledač je zaključuje (naziv etape ili događaja, zatim stil vožnje, po zadanom labavo).
- Otkrivanje krugova bez brojača krugova (AC EVO, AC Rally, BeamNG) koristi mjesto gdje je snimanje
  počelo kao liniju, pa počnite snimati na startnoj liniji.
- Reset vozila u BeamNG-u zatvara krug otvoren u tom trenutku: zapisuje se kao djelimična vožnja kad je
  prešla minimalnu udaljenost (300 m), a inače se odbacuje.
- `route` sprema otprilike svake 2 sekunde tokom vožnje; pad ili ubijen proces gubi najviše
  pozicije od posljednjeg spremanja.
- Forza Horizon ne šalje naziv staze, pa datoteke krugova iz Forze imaju `"track": null`; Forza Motorsport
  (2023) šalje samo broj, koji se čuva kao `lap.trackOrdinal`.

## Rekonstrukcija {#reconstruction}

- **Dubina se procjenjuje, ne čita.** Strop cijelog pristupa i cijena toga što se nikad
  ne dira proces igre.
- **Vidno polje se pretpostavlja, ne mjeri.** Preusko i nivo se rekonstruiše dublji nego
  što jest.
- **Globalna razmjera** dolazi iz pretpostavljene visine kamere (1,15 m u prozoru) ili iz
  telemetrije. Mjeri se na prvom ključnom kadru; kad on nema upotrebljivo tlo, probaju se sljedeći
  ključni kadrovi (do 30 kadrova), a razmjera pronađena kasnije primjenjuje se na cijeli nivo kad se
  zapisuje. Linija "Size:" u prozoru kaže šta se desilo; ako tlo uopće nije pronađeno,
  skeniranje ostaje bez jedinica. U tom slučaju je veličina voksela u jedinicama prvog kadra, pa se
  njegova veličina u metrima razlikuje od postavke. Offline rekonstrukcije su u vlastitim jedinicama rješenja.
- **Zatvaranje petlje je isključeno** i nije graf poza kad se uključi u kodu; drift je ograničen samo
  kvalitetom praćenja od kadra do kadra.
- **Prozorsko bundle podešavanje postoji, ali nije ugrađeno**; kolabiralo je na stvarnom snimku.
- **Površina je ponderirana zauzetost, a ne TSDF**: tanke strukture i slobodan prostor su gori nego
  što bi dobio TSDF.
- **Nema atlasa tekstura.** Boja je po vrhu (`COLOR_0`), miješana iz 4 najbolja pogleda među
  160 sačuvanih kadrova. Test zaklonjenosti je grub: testira se naspram vlastitih vrhova mreže u
  dubinskom baferu od 2 piksela, pa zaklon koji mreža ne sadrži (automobil u prolazu) nije uhvaćen.
- **Voda se nikad ne označava**; sve je tlo ili struktura.
- **Rješavanje unaprijed (feed-forward) nije uživo**: prvo treba snimak. Prilagodljivo ponovno rješavanje
  teških dionica nije napravljeno.
- **Poze iz telemetrije** postavljaju kameru na automobil (pomak kamere iza automobila nije poznat). Pozicije
  se uzimaju kako ih Forza šalje (Y gore, kao u datotekama krugova); smjerovi skretanja (yaw), nagiba (pitch) i valjanja (roll)
  očitani su sa snimljenih krugova (smjer kretanja, nagib, strana čiji se ovjes steže),
  a ne sa kamere pokrenute igre.
- Overlay ne može crtati preko **ekskluzivnog punog ekrana**; koristite prozor bez okvira (borderless windowed).
- Globalne prečice, overlay kroz koji se klika i snimanje uživo rade **samo na Windowsu**.
- Zatvaranje prozora ne nudi spremanje.

## Šta je izmjereno {#what-is-measured}

- `tests/test_accuracy.py`: sintetička soba sa poznatom putanjom i analitičkom dubinom - smješteni kadrovi,
  greška putanje, pređena udaljenost, veličina sobe, površina na zidovima ([Rekonstrukcija nivoa](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: put poznate širine vožen van sredine rekonstruiše svoju širinu.
- `tests/test_track_scale.py`: izdvajanje površine u razmjeri trkaće staze, memorija proporcionalna onome što
  je skenirano, blokovi koji se spajaju u jednu površinu.
- `tests/test_glb.py` plus testovi samog pregledača: `.glb` ugovor s obje strane.
- Kako se mreža za dubinu snalazi na stvarnoj igri ne može odgovoriti sintetička scena, i
  to testni paket ne mjeri.
