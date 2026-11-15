---
title: "Telemetrijski snimači"
nav_order: 3
lang: "bs"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetrijski snimači {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` snima svaki kanal koji igra šalje, dijeli tok na krugove ili dionice i
zapisuje jednu [`heat3d-lap`](lap-format.md) JSON datoteku po krugu u folder. Kartica Analiza utrke u pregledniku
čita te datoteke. Snimanje traje dok ne pritisnete **Ctrl+C**; krug ili dionica
koji su u tom trenutku otvoreni zapisuju se ako su dovoljno dugi da se zadrže (pogledajte
[Dijeljenje na krugove i dionice](lap-splitting.md)).

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
i moduli u [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opcije {#options}

| Opcija | Zadano | Značenje |
|---|---|---|
| `--game` | `forza` | Jedno od `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Folder u koji se zapisuju datoteke krugova. Kreira se ako ne postoji. Ignoriše ga `trackmania`, čiji dodatak sam zapisuje datoteke. |
| `--port` | `5300` | UDP port na kojem se sluša. **Za svaku igru osim Forze vrijednost 5300 znači "zadani port same igre"**: 20777 za `wrc` i DiRT igre, 6776 za `rbr`, 4460 za `beamng`. Dajte bilo koji drugi broj da ga zamijenite. Ne koriste ga Assetto Corsa igre (dijeljena memorija) ni Trackmania (datoteke). |
| `--forward` | nema | Samo Forza: `host:port` na koji se svaki primljeni paket prosljeđuje, nepromijenjen. `127.0.0.1:5301` za FH Companion. Goli `:5301` znači `127.0.0.1:5301`. |
| `--install` | isključeno | `beamng`: prvo kopira protokol mod u BeamNG-ove raspakirane modove. `trackmania`: kopira Openplanet dodatak u Openplanetov folder dodataka. Ignorišu ga ostale igre. |
| `--configure` | nema | Samo `wrc`: putanja do telemetrijskog `config.json` igre EA SPORTS WRC; prije snimanja uključuje zadani `wrc` paket (prvo se pravi rezervna kopija). |
| `--surface` | nema | Reli igre (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ili `mixed`, zapisano u `meta.surface` datoteke kruga. Bez njega se površina ne zapisuje. |

## Igre ukratko {#the-games-at-a-glance}

| `--game` | Igra | Izvor | Zadani port | Dijeljenje | `game` u datoteci | Stranica |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (uklj. 2023) | Data Out UDP | 5300 | brojač krugova igre (`LapSplitter`) | `forza-horizon`, `forza-motorsport` ili `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | dijeljena memorija `acpmf_*` | - | brojač krugova (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | dijeljena memorija `acpmf_*` | - | brojač krugova (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | dijeljena memorija `acevo_pmf_*` | - | startna linija (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | dijeljena memorija `acpmf_*` | - | startna linija / zaustavljanje (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc` struktura | 20777 | sat dionice (`StageSplitter`) | `ea-sports-wrc` | [Reli igre](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | sat dionice (`StageSplitter`) | `dirt-rally-2` | [Reli igre](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | sat dionice (`StageSplitter`) | `dirt-rally` | [Reli igre](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | sat dionice (`StageSplitter`) | `dirt-4` | [Reli igre](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | sat dionice (`StageSplitter`) | `richard-burns-rally` | [Reli igre](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d` protokol mod, UDP | 4460 | startna linija (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet dodatak, CSV datoteke | - | po vožnji, u dodatku | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | vlastite `.ibt` datoteke, čita ih preglednik | - | brojač krugova simulatora | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

Forza snimač je onaj koji se najviše koristi. Kunos, reli, BeamNG i Trackmania
snimači izgrađeni su prema objavljenim rasporedima i testirani na sintetičkim paketima i
stranicama izgrađenim iz tih rasporeda (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`); **nijedan od njih još nije pokrenut protiv žive igre**.
Snimači koji mogu provjeriti svoj ulaz to rade dok paketi stižu i jednom ispišu `note:` kada
se nešto ne poklapa (EA WRC i DiRT porede svjetsku brzinu s iznosom brzine;
EA WRC također prijavljuje paket kraći od zadane strukture od 237 bajta). [Igre](games.md) navodi izvore
i šta još nije potvrđeno po igri.

## Dok radi {#while-it-runs}

- **Forza** ispisuje statusnu liniju jednom u sekundi: primljeni paketi, te broj otvorenog kruga,
  broj uzoraka i metri, ili `waiting for a race`. Svaki završeni krug ispisuje `wrote <file>`.
- **Assetto Corsa igre** ispisuju ime svake datoteke kruga dok se zapisuje.
- **Reli igre** ispisuju `listening for <game> on port <port>`, zatim `stage written: <file>`;
  na Ctrl+C otvorena dionica dovoljno duga da se zadrži zapisuje se kao `partial stage written: <file>`.
- **BeamNG** ispisuje `lap written: <file>`, a na Ctrl+C `run written: <file>`.
- **Trackmania** ne ispisuje ništa po vožnji: dodatak sam zapisuje svoje CSV datoteke.
- Na kraju svaki snimač ispisuje koliko je datoteka zapisao.

Forza snimanje, ovdje napajano sintetičkim Data Out paketima automobila koji vozi dva kruga
kružnice od 150 m (datoteke krugova, sirova prateća datoteka i sažetak autoprovjere koje ostavlja):

![telemetrija snima dva kruga sintetičkog Forza feeda](../assets/img/telemetry-run.svg)

## Imena datoteka {#file-names}

| Snimač | Obrazac |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa igre | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Reli igre, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, gdje je `<game>` dugo ime (`ea-sports-wrc`, `beamng`, ...), `stage` za reli i `lap` za BeamNG |
| Trackmania dodatak | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` naspram `run` (Forza, Assetto Corsa) i sufiks `_partial` (reli, BeamNG) označavaju
je li krug ili dionica završen. Vremenska oznaka je kada je datoteka zapisana, a ne
kada je krug počeo.

Pored datoteka krugova svaki snimač zapisuje `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - svaki
paket ili stranicu koja je stigla, cijelu, i u menijima i između krugova - te
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, autoprovjeru: po tipu paketa koliko ih je stiglo, koliko je
otišlo u datoteke krugova, i `lost`, što je 0. Preglednik preskače oboje kada se učitava folder.
Pogledajte [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) u README-u.

## Podstranice ove stranice {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa igre](telemetry-assetto-corsa.md)
- [Reli igre](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Dijeljenje na krugove i dionice](lap-splitting.md)
- [Klizanje, zanošenje i izvedeni kanali](slip-and-drift.md)
- [Datoteka heat3d-lap](lap-format.md)
