---
title: "Telemetriopptakere"
nav_order: 3
lang: "no"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetriopptakere {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` tar opp hver kanal et spill sender, deler strømmen i runder eller etapper, og skriver én [`heat3d-lap`](lap-format.md)-JSON-fil per runde
i en mappe. Viewers fane Løp leser disse filene. Opptaket kjører til du trykker **Ctrl+C**; hvilken runde eller etappe som er åpen i det øyeblikket,
skrives hvis den er lang nok til å beholdes (se [Hvordan runder og etapper deles](lap-splitting.md)).

Kode: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
og modulene i [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Valg {#options}

| Valg | Standard | Betydning |
|---|---|---|
| `--game` | `forza` | En av `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mappen rundefilene skrives til. Opprettes hvis den mangler. Ignoreres av `trackmania`, hvis plugin skriver filene selv. |
| `--port` | `5300` | UDP-porten som lyttes på. **For hvert spill unntatt Forza betyr verdien 5300 "spillets egen standard"**: 20777 for `wrc` og DiRT-spillene, 6776 for `rbr`, 4460 for `beamng`. Gi et annet tall for å overstyre. Brukes ikke av Assetto Corsa-spillene (delt minne) eller Trackmania (filer). |
| `--forward` | ingen | Bare Forza: `host:port` å sende hver mottatt pakke videre til, uendret. `127.0.0.1:5301` for FH Companion. Et nakent `:5301` betyr `127.0.0.1:5301`. |
| `--install` | av | `beamng`: kopierer protokollmodden til BeamNGs upakkede mods først. `trackmania`: kopierer Openplanet-pluginen til Openplanets plugin-mappe. Ignoreres av de andre spillene. |
| `--configure` | ingen | Bare `wrc`: sti til EA SPORTS WRCs telemetri-`config.json`; slår standardpakken `wrc` på før opptak (sikkerhetskopieres først). |
| `--surface` | ingen | Rallyspill (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` eller `mixed`, skrevet til rundefilens `meta.surface`. Uten den skrives ingen underlag. |

## Spillene i korte trekk {#the-games-at-a-glance}

| `--game` | Spill | Kilde | Standardport | Deling | `game` i filen | Side |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (inkl. 2023) | Data Out UDP | 5300 | spillets rundeteller (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, eller `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | delt minne `acpmf_*` | - | rundeteller (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa-spill](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | delt minne `acpmf_*` | - | rundeteller (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa-spill](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | delt minne `acevo_pmf_*` | - | startlinje (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa-spill](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | delt minne `acpmf_*` | - | startlinje / stopp (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa-spill](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc`-struktur | 20777 | etappeklokke (`StageSplitter`) | `ea-sports-wrc` | [Rallyspill](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | etappeklokke (`StageSplitter`) | `dirt-rally-2` | [Rallyspill](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | etappeklokke (`StageSplitter`) | `dirt-rally` | [Rallyspill](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | etappeklokke (`StageSplitter`) | `dirt-4` | [Rallyspill](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | etappeklokke (`StageSplitter`) | `richard-burns-rally` | [Rallyspill](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d`-protokollmod, UDP | 4460 | startlinje (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-plugin, CSV-filer | - | per kjøring, i pluginen | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | egne `.ibt`-filer, lest av viewer | - | simulatorens rundeteller | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

Forza-opptakeren er den som er mest brukt. Kunos-, rally-, BeamNG- og Trackmania-opptakerne er bygget mot de publiserte oppsettene og testet på syntetiske pakker og
sider bygget etter disse oppsettene (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **ingen av dem er kjørt mot det levende spillet ennå**. Opptakerne
som kan sjekke sin inndata gjør det etter hvert som pakkene kommer, og skriver én `note:` når noe ikke stemmer (EA WRC og DiRT sammenligner verdenshastigheten med farten;
EA WRC rapporterer også en pakke kortere enn standardstrukturen på 237 byte). [Spill](games.md) lister kildene og hva som ikke er bekreftet per spill.

## Mens den kjører {#while-it-runs}

- **Forza** skriver en statuslinje hvert sekund: pakker mottatt, og den åpne rundens nummer, antall prøver og meter, eller `waiting for a race`. Hver ferdig runde skriver `wrote <file>`.
- **Assetto Corsa-spillene** skriver navnet på hver rundefil når den skrives.
- **Rallyspill** skriver `listening for <game> on port <port>`, deretter `stage written: <file>`; ved Ctrl+C skrives en åpen etappe som er lang nok til å beholdes som `partial stage written: <file>`.
- **BeamNG** skriver `lap written: <file>`, og ved Ctrl+C `run written: <file>`.
- **Trackmania** skriver ingenting per kjøring: pluginen skriver CSV-filene selv.
- Til slutt skriver hver opptaker hvor mange filer den skrev.

Et Forza-opptak, her matet med syntetiske Data Out-pakker fra en bil som kjører to runder av en 150 m sirkel (rundefilene, den rå sidefilen og egenkontrollsammendraget den etterlater):

![telemetriopptak av to runder fra en syntetisk Forza-strøm](../assets/img/telemetry-run.svg)

## Filnavn {#file-names}

| Opptaker | Mønster |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa-spill | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallyspill, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, der `<game>` er det lange navnet (`ea-sports-wrc`, `beamng`, ...), `stage` for rally og `lap` for BeamNG |
| Trackmania-plugin | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` mot `run` (Forza, Assetto Corsa) og suffikset `_partial` (rally, BeamNG) viser om runden eller etappen ble fullført. Tidsstemplet er når filen ble skrevet,
ikke når runden startet.

Ved siden av rundefilene skriver hver opptaker `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - hver pakke eller side som kom inn, beholdt hel, også i menyene og mellom runder -
og `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, egenkontrollen: per pakketype hvor mange som kom, hvor mange som gikk inn i rundefiler, og `lost`, som er 0. Viewer hopper over begge når en mappe lastes.
Se [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) i README-filen.

## Undersider {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa-spill](telemetry-assetto-corsa.md)
- [Rallyspill](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Hvordan runder og etapper deles](lap-splitting.md)
- [Skli, drift og avledede kanaler](slip-and-drift.md)
- [`heat3d-lap`-filen](lap-format.md)
