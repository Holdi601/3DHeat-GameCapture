---
title: "Telemetrioptagere"
nav_order: 3
lang: "da"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetrioptagere {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` optager alle kanaler, et spil sender, deler strømmen op i omgange eller etaper og skriver én [`heat3d-lap`](lap-format.md)-JSON-fil pr. omgang i en mappe. Fanen Løbsanalyse i viewer'en læser disse filer. Optagelsen kører, indtil du trykker **Ctrl+C**; den omgang eller etape, der er åben i det øjeblik, skrives, hvis den er lang nok til at blive gemt (se [Opdeling i omgange og etaper](lap-splitting.md)).

Kode: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py) og modulerne i [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Valgmuligheder {#options}

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `--game` | `forza` | En af `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mappen, omgangsfilerne skrives i. Oprettes, hvis den mangler. Ignoreres af `trackmania`, hvis plugin skriver filerne selv. |
| `--port` | `5300` | UDP-porten, der lyttes på. **For alle spil undtagen Forza betyder værdien 5300 "spillets egen standard"**: 20777 for `wrc` og DiRT-spillene, 6776 for `rbr`, 4460 for `beamng`. Giv et andet tal for at overskrive. Bruges ikke af Assetto Corsa-spillene (delt hukommelse) eller Trackmania (filer). |
| `--forward` | ingen | Kun Forza: `host:port`, som hver modtaget pakke sendes videre til, uændret. `127.0.0.1:5301` for FH Companion. Et nøgent `:5301` betyder `127.0.0.1:5301`. |
| `--install` | fra | `beamng`: kopierer protokolmodet ind i BeamNGs udpakkede mods først. `trackmania`: kopierer Openplanet-pluginet ind i Openplanets pluginmappe. Ignoreres af de andre spil. |
| `--configure` | ingen | Kun `wrc`: sti til EA SPORTS WRCs telemetri-`config.json`; slår standardpakken `wrc` til, før optagelsen starter (sikkerhedskopieres først). |
| `--surface` | ingen | Rallyspil (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` eller `mixed`, skrevet til omgangsfilens `meta.surface`. Uden den skrives intet underlag. |

## Spillene i oversigt {#the-games-at-a-glance}

| `--game` | Spil | Kilde | Standardport | Opdeling | `game` i filen | Side |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (inkl. 2023) | Data Out UDP | 5300 | spillets omgangstæller (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, eller `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | delt hukommelse `acpmf_*` | - | omgangstæller (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa-spillene](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | delt hukommelse `acpmf_*` | - | omgangstæller (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa-spillene](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | delt hukommelse `acevo_pmf_*` | - | startlinje (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa-spillene](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | delt hukommelse `acpmf_*` | - | startlinje / stop (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa-spillene](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc`-struktur | 20777 | etapeur (`StageSplitter`) | `ea-sports-wrc` | [Rallyspil](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | etapeur (`StageSplitter`) | `dirt-rally-2` | [Rallyspil](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | etapeur (`StageSplitter`) | `dirt-rally` | [Rallyspil](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | etapeur (`StageSplitter`) | `dirt-4` | [Rallyspil](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | etapeur (`StageSplitter`) | `richard-burns-rally` | [Rallyspil](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d`-protokolmod, UDP | 4460 | startlinje (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-plugin, CSV-filer | - | pr. kørsel, i pluginet | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | dets egne `.ibt`-filer, læst af viewer'en | - | simulatorens omgangstæller | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

Forza-optageren er den, der er afprøvet mest. Kunos-, rally-, BeamNG- og Trackmania-optagerne er bygget efter de offentliggjorte layouts og testet på syntetiske pakker og sider bygget efter disse layouts (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **ingen af dem er endnu kørt mod det live spil**. Optagerne, der kan kontrollere deres input, gør det, efterhånden som pakkerne kommer, og skriver én gang en `note:`, når noget ikke passer (EA WRC og DiRT sammenligner verdenshastigheden med farten; EA WRC melder også om en pakke kortere end de 237 bytes i standardstrukturen). [Spil](games.md) lister kilderne og det, der ikke er bekræftet endnu, pr. spil.

## Mens den kører {#while-it-runs}

- **Forza** skriver en statuslinje hvert sekund: modtagne pakker, og den åbne omgangs nummer, antal prøver og meter, eller `waiting for a race`. Hver færdig omgang skriver `wrote <file>`.
- **Assetto Corsa-spillene** skriver navnet på hver omgangsfil, når den skrives.
- **Rallyspil** skriver `listening for <game> on port <port>`, derefter `stage written: <file>`; ved Ctrl+C skrives en åben etape, der er lang nok, som `partial stage written: <file>`.
- **BeamNG** skriver `lap written: <file>`, og ved Ctrl+C `run written: <file>`.
- **Trackmania** skriver intet pr. kørsel: pluginet skriver sine CSV-filer selv.
- Til sidst skriver hver optager, hvor mange filer den skrev.

En Forza-optagelse, her mødt med syntetiske Data Out-pakker fra en bil, der kører to omgange af en 150 m cirkel (omgangsfilerne, den rå sidefil og selvkontrolsummen, den efterlader):

![telemetri, der optager to omgange af et syntetisk Forza-signal](../assets/img/telemetry-run.svg)

## Filnavne {#file-names}

| Optager | Mønster |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa-spillene | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallyspil, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, hvor `<game>` er det lange navn (`ea-sports-wrc`, `beamng`, ...), `stage` for rally og `lap` for BeamNG |
| Trackmania-pluginet | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` mod `run` (Forza, Assetto Corsa) og suffikset `_partial` (rally, BeamNG) viser, om omgangen eller etapen blev afsluttet. Tidsstemplet er, hvornår filen blev skrevet, ikke hvornår omgangen begyndte.

Ved siden af omgangsfilerne skriver hver optager `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - hver pakke eller side, der kom ind, uændret, også i menuerne og mellem omgangene - og `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, selvkontrollen: pr. pakketype hvor mange, der kom, hvor mange der gik ind i omgangsfilerne, og `lost`, som er 0. Viewer'en springer begge over, når en mappe indlæses. Se [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) i README'en.

## Undersider {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa-spillene](telemetry-assetto-corsa.md)
- [Rallyspil](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Opdeling i omgange og etaper](lap-splitting.md)
- [Slip, drift og afledte kanaler](slip-and-drift.md)
- [Filen `heat3d-lap`](lap-format.md)
