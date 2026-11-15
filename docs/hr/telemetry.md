---
title: "Snimači telemetrije"
nav_order: 3
lang: "hr"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Snimači telemetrije {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` snima svaki kanal koji igra šalje, dijeli tok na krugove ili etape i
zapisuje po jednu [`heat3d-lap`](lap-format.md) JSON datoteku za svaki krug u mapu.
Kartica Analiza utrke u pregledniku čita te datoteke. Snimanje traje dok ne pritisnete
**Ctrl+C**. Krug ili etapa koji je tada otvoren zapisuje se ako je dovoljno dug da se
zadrži (vidi [Kako se krugovi i etape dijele](lap-splitting.md)).

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
i moduli u [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opcije {#options}

| Opcija | Zadano | Značenje |
|---|---|---|
| `--game` | `forza` | Jedna od vrijednosti: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mapa u koju se pišu datoteke krugova. Stvara se ako ne postoji. Ignorira je `trackmania`, čiji dodatak sam piše datoteke. |
| `--port` | `5300` | UDP port na kojem se sluša. **Za svaku igru osim Forze vrijednost 5300 znači „zadani port igre”**: 20777 za `wrc` i DiRT igre, 6776 za `rbr`, 4460 za `beamng`. Zadajte neki drugi broj za promjenu. Ne koristi se za Assetto Corsa igre (dijeljena memorija) ni za Trackmaniju (datoteke). |
| `--forward` | nema | Samo Forza: `host:port` na koji se svaki primljeni paket prosljeđuje nepromijenjen. `127.0.0.1:5301` za FH Companion. Samo `:5301` znači `127.0.0.1:5301`. |
| `--install` | isključeno | `beamng`: prije pokretanja kopira modul protokola u raspakirane modove BeamNG-a. `trackmania`: kopira Openplanet dodatak u mapu dodataka Openplanet-a. Ostale igre ga ignoriraju. |
| `--configure` | nema | Samo `wrc`: putanja do datoteke `config.json` telemetrije EA SPORTS WRC-a; uključuje zadani paket `wrc` prije snimanja (prvo se napravi sigurnosna kopija). |
| `--surface` | nema | Vozačke igre (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ili `mixed`, zapisano u `meta.surface` datoteke kruga. Bez toga se podloga ne zapisuje. |

## Igre na prvi pogled {#the-games-at-a-glance}

| `--game` | Igra | Izvor | Zadani port | Dijeljenje | `game` u datoteci | Stranica |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (uklj. 2023.) | Data Out UDP | 5300 | brojač krugova igre (`LapSplitter`) | `forza-horizon`, `forza-motorsport` ili `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | dijeljena memorija `acpmf_*` | - | brojač krugova (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | dijeljena memorija `acpmf_*` | - | brojač krugova (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | dijeljena memorija `acevo_pmf_*` | - | startna linija (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | dijeljena memorija `acpmf_*` | - | startna linija / zaustavljanje (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa igre](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struktura `wrc` | 20777 | brojač vremena etape (`StageSplitter`) | `ea-sports-wrc` | [Vozačke igre](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | brojač vremena etape (`StageSplitter`) | `dirt-rally-2` | [Vozačke igre](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | brojač vremena etape (`StageSplitter`) | `dirt-rally` | [Vozačke igre](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | brojač vremena etape (`StageSplitter`) | `dirt-4` | [Vozačke igre](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | brojač vremena etape (`StageSplitter`) | `richard-burns-rally` | [Vozačke igre](telemetry-rally.md) |
| `beamng` | BeamNG.drive | modul protokola `heat3d`, UDP | 4460 | startna linija (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020.) | Openplanet dodatak, CSV datoteke | - | po vožnji, u dodatku | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | vlastite `.ibt` datoteke, čita ih preglednik | - | brojač krugova simulatora | `iracing` | [iRacing](telemetry-iracing.md) |

## Stanje {#status}

Snimač Forze najviše je isproban. Snimači za Kunos, vozačke igre, BeamNG i Trackmaniju
izrađeni su prema objavljenim rasporedima podataka i isprobani na sintetičkim paketima
i stranicama izrađenima prema tim rasporedima (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`). **Nijedan još nije pokrenut uz pravu igru.** Snimači koji mogu
provjeriti svoj ulaz to rade dok paketi stižu i jednom ispišu `note:` kad nešto ne
odgovara (EA WRC i DiRT uspoređuju brzinu vozila s brzinom iz svijeta; EA WRC također
javlja paket kraći od zadane strukture od 237 bajtova). [Igre](games.md) navode izvore
i što još nije potvrđeno za svaku igru.

## Dok radi {#while-it-runs}

- **Forza** svake sekunde ispisuje redak stanja: koliko je paketa primljeno te broj
  otvorenog kruga, broj uzoraka i metre, ili `waiting for a race`. Svaki završeni krug
  ispisuje `wrote <file>`.
- **Assetto Corsa igre** ispisuju ime svake datoteke kruga kad se zapiše.
- **Vozačke igre** ispisuju `listening for <game> on port <port>`, zatim `stage written: <file>`;
  pri Ctrl+C otvorena etapa dovoljno duga za zadržavanje zapisuje se kao `partial stage written: <file>`.
- **BeamNG** ispisuje `lap written: <file>`, a pri Ctrl+C `run written: <file>`.
- **Trackmania** ne ispisuje ništa po vožnji: dodatak sam zapisuje CSV datoteke.
- Na kraju svaki snimač ispiše koliko je datoteka napisao.

Snimanje Forze, ovdje hranjeno sintetičkim Data Out paketima vozila dva kruga staze
dugačke 150 m (datoteke krugova, sirova prateća datoteka i sažetak provjere koji ostaje):

![snimanje telemetrije dva kruga sintetičke Forze](../assets/img/telemetry-run.svg)

## Nazivi datoteka {#file-names}

| Snimač | Uzorak |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa igre | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Vozačke igre, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, gdje je `<game>` dugo ime (`ea-sports-wrc`, `beamng`, ...), `stage` za vozačke igre, a `lap` za BeamNG |
| Dodatak Trackmanie | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` naspram `run` (Forza, Assetto Corsa) i nastavak `_partial` (vozačke igre, BeamNG)
pokazuju je li krug ili etapa završena. Vremenska oznaka je trenutak kad je datoteka
zapisana, a ne kad je krug počeo.

Uz datoteke krugova svaki snimač piše `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet`, svaki
paket ili stranicu koja je stigla, cijele, uključujući one u izbornicima i između krugova,
i `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, provjeru: po vrsti paketa koliko ih je
stiglo, koliko ih je ušlo u datoteke krugova i `lost`, koji je 0. Preglednik oboje
preskače kad se učita mapa. Vidi [Potpunost](https://github.com/Holdi601/3DHeat-GameCapture#completeness) u README-u.

## Podstranice ove stranice {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa igre](telemetry-assetto-corsa.md)
- [Vozačke igre](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Kako se krugovi i etape dijele](lap-splitting.md)
- [Klizanje, drift i izvedeni kanali](slip-and-drift.md)
- [Datoteka `heat3d-lap`](lap-format.md)
