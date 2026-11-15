---
title: "Omejitve in preverjanje"
nav_order: 9
lang: "sl"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Omejitve in kaj je preverjeno {#limits-and-what-is-verified}

Iskren seznam: česa orodja ne počnejo in kaj ni bilo preverjeno z zagnano igro.

## Telemetrija {#telemetry}

| Snemalnik | Stanje |
|---|---|
| Forza | Zgrajeno na uradni dokumentaciji Data Out; postavitev se zazna iz samih paketov. Bralnik FH Companion `.tele.gz` v pregledovalniku je bil preverjen na pravih krogih. |
| AC, ACC, AC EVO, AC Rally | Preizkušeno na sintetičnih straneh, zgrajenih iz objavljenih postavitev. **Še ni zagnano proti živim igram.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Preizkušeno na paketih, zgrajenih iz dokumentiranih postavitev. **Še ni zagnano proti živim igram.** Osi, drža in enote hitrosti RBR-ja niso dokumentirane in se obravnavajo iz podatkov. |
| BeamNG.drive | Snemalnik je preizkušen na paketih, zgrajenih iz strukture modifikacije. **Modifikacija še ni bila zagnana v igri.** |
| Trackmania | Bralnik CSV-ja v pregledovalniku je preizkušen. **Vtičnik še ni bil zagnan v igri.** Naloži se samo v razvijalskem načinu Openplanet. |
| iRacing | Bralnik `.ibt` v pregledovalniku je preizkušen na sintetični datoteki. |

Druge omejitve telemetrije:

- Forzina normalizacija zdrsa ni dokumentirana; zdrs Kunosa je skaliran s tipično vrhunsko vrednostjo
  asfalta, kar je približek.
- Smer nekaterih bočnih osi okvirja avta (Kunos, DiRT) je dokumentirana na obe strani; velikost kota
  zdrsa je zanesljiva, njegov predznak ni.
- Nobena od reli iger ne pošilja zdrsa pnevmatik; izpelje se v pregledovalniku. RBR ne pošilja hitrosti koles.
- Površina reli etape se zapiše samo, kadar je dan `--surface`; sicer datoteka ne navede nobene in
  pregledovalnik jo sklepa (ime etape ali dogodka, nato slog vožnje, privzeto ohlapno).
- Zaznavanje kroga brez števca krogov (AC EVO, AC Rally, BeamNG) za črto uporabi točko, kjer se je snemanje
  začelo, zato začnite snemati na startni črti.
- Ponastavitev vozila BeamNG zapre krog v tistem trenutku: zapiše se kot delni tek, če je pokrival najmanjšo
  razdaljo (300 m), sicer se zavrže.
- `route` shranjuje približno na vsaki 2 sekundi med vožnjo; zrušitev ali ubita aplikacija izgubi največ
  položaje od zadnjega shranjevanja.
- Forza Horizon ne pošilja imena proge, zato imajo datoteke krogov Forze `"track": null`; Forza Motorsport
  (2023) pošilja samo številko, ohranjeno kot `lap.trackOrdinal`.

## Rekonstrukcija {#reconstruction}

- **Globina je ocenjena, ne prebrana.** Strop celotnega pristopa in cena tega, da se nikoli ne dotaknete
  procesa igre.
- **Vidno polje je predpostavljeno, ne izmerjeno.** Preozko in nivo se rekonstruira globlje, kot je.
- **Globalno merilo** pride iz predpostavljene višine kamere (1,15 m v oknu) ali iz telemetrije. Izmeri se na
  prvem ključnem okvirju; kadar ta nima uporabnih tal, se preizkusijo naslednji ključni okvirji (do 30
  okvirjev), najdeno kasneje pa se uporabi za celoten nivo, ko se zapiše. Vrstica »Size:« v oknu pove, kaj se
  je zgodilo; če tal ni najdenih sploh, skener ostane brez enot. Velikost voksla je takrat v enotah prvega
  okvirja, zato se njegova velikost v metrih razlikuje od nastavitve. Rekonstrukcije brez povezave so v
  lastnih enotah rešitve.
- **Zapiranje zanke je izklopljeno** in ni graf poze, kadar je vklopljeno v kodi; odmik je omejen samo s
  kakovostjo sledenja med sosednjimi okvirji.
- **Okensko prilagajanje snopa obstaja, vendar ni povezano**; na pravem posnetku se je sesulo.
- **Površina je utežena zasedenost, ne TSDF**: tanke strukture in prazen prostor sta slabša, kot bi bila
  pri TSDF.
- **Brez atlasa tekstur.** Barva je na oglišču (`COLOR_0`), zmešana iz 4 najboljših pogledov med 160
  shranjenimi okvirji. Test zakritja je grob: preizkuša proti lastnim ogliščem mreže v 2-pikslnem globinskem
  medpomnilniku, zato zakritje, ki ga mreža ne vsebuje (mimovozeč avto), ni ujeto.
- **Voda nikoli ni označena**; vse je tla ali struktura.
- **Reševanje po feed-forward ni živo**: potrebuje najprej posnetek. Prilagodljivo ponovno reševanje
  zahtevnih odsekov ni zgrajeno.
- **Poze iz telemetrije** postavijo kamero na avto (odmik kamere z zasledovanjem ni znan). Položaji se
  vzamejo tako, kot jih pošilja Forza (Y gor, kakor v datotekah krogov); smisel yaw, pitch in roll je bil
  prebran iz zabeleženih krogov (smer vožnje, naklon, katera stran vzmetenja se stisne), ne iz tekoče kamere
  igre.
- Prekrivanje ne more risati čez **celozaslonski ekskluzivni način**; uporabi brezrobo okno na celem zaslonu.
- Globalne bližnjice, prekrivanje, ki prepušča klike, in živo zajemanje so **samo za Windows**.
- Zapiranje okna ne ponudi shranjevanja.

## Kaj je izmerjeno {#what-is-measured}

- `tests/test_accuracy.py`: sintetična soba z znano potjo in analitično globino - okvirji postavljeni, napaka
  poti, prehojena razdalja, velikost sobe, površina na stenah ([Rekonstrukcija nivoja](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: cesta znane širine, vožena izven središča, se rekonstruira s svojo širino.
- `tests/test_track_scale.py`: izvleček površine pri merilu dirkališča, pomnilnik sorazmeren s tistim, kar je
  bilo skenirano, bloki se združijo v eno površino.
- `tests/test_glb.py` in lastni testi pregledovalnika: pogodba `.glb` z obeh strani.
- Kako se globinska mreža obnese na pravi igri ni nekaj, na kar lahko odgovori sintetični prizor, in ga
  testni paket ne meri.
