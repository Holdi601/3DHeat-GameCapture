---
title: "Telemetriinspelare"
nav_order: 3
lang: "sv"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetriinspelare {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` spelar in varje kanal ett spel skickar, delar strömmen i varv eller etapper och skriver en [`heat3d-lap`](lap-format.md)-JSON-fil per varv till en mapp. Visarens flik Racinganalys läser de filerna. Inspelningen pågår tills du trycker på **Ctrl+C**. Det varv eller den etapp som är öppen i det ögonblicket skrivs om den är tillräckligt lång för att behållas (se [Hur varv och etapper delas](lap-splitting.md)).

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
och modulerna i [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Alternativ {#options}

| Alternativ | Standard | Betydelse |
|---|---|---|
| `--game` | `forza` | En av `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mappen varvfilerna skrivs till. Skapas om den saknas. Ignoreras av `trackmania`, vars plugin skriver filerna själv. |
| `--port` | `5300` | UDP-porten att lyssna på. **För alla spel utom Forza betyder värdet 5300 "spelets egen standard"**: 20777 för `wrc` och DiRT-spelen, 6776 för `rbr`, 4460 för `beamng`. Ange ett annat tal för att åsidosätta. Används inte av Assetto Corsa-spelen (delat minne) eller Trackmania (filer). |
| `--forward` | ingen | Endast Forza: `host:port` att vidarebefordra varje mottaget paket till, oförändrat. `127.0.0.1:5301` för FH Companion. Ett nakent `:5301` betyder `127.0.0.1:5301`. |
| `--install` | av | `beamng`: kopiera protokollmodden till BeamNGs uppackade mods först. `trackmania`: kopiera Openplanet-pluginet till Openplanets plugin-mapp. Ignoreras av de andra spelen. |
| `--configure` | ingen | Endast `wrc`: sökväg till EA SPORTS WRC:s telemetri-`config.json`. Slår på standardpaketet `wrc` innan inspelning (säkerhetskopieras först). |
| `--surface` | ingen | Rallyspel (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` eller `mixed`, skrivs till varvfilens `meta.surface`. Utan den skrivs ingen yta. |

## Spelen i korthet {#the-games-at-a-glance}

| `--game` | Spel | Källa | Standardport | Delning | `game` i filen | Sida |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (inkl. 2023) | Data Out UDP | 5300 | spelets varvräknare (`LapSplitter`) | `forza-horizon`, `forza-motorsport` eller `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | delat minne `acpmf_*` | - | varvräknare (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa-spelen](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | delat minne `acpmf_*` | - | varvräknare (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa-spelen](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | delat minne `acevo_pmf_*` | - | startlinje (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa-spelen](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | delat minne `acpmf_*` | - | startlinje / stopp (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa-spelen](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc`-struktur | 20777 | etappklocka (`StageSplitter`) | `ea-sports-wrc` | [Rallyspel](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | etappklocka (`StageSplitter`) | `dirt-rally-2` | [Rallyspel](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | etappklocka (`StageSplitter`) | `dirt-rally` | [Rallyspel](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | etappklocka (`StageSplitter`) | `dirt-4` | [Rallyspel](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | etappklocka (`StageSplitter`) | `richard-burns-rally` | [Rallyspel](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d`-protokollmod, UDP | 4460 | startlinje (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-plugin, CSV-filer | - | per körning, i pluginet | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | egna `.ibt`-filer, lästa av visaren | - | simulatorns varvräknare | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

Forza-inspelaren är den som använts mest. Kunos-, rally-, BeamNG- och Trackmania-inspelarna är byggda mot de publicerade layouterna och testade på syntetiska paket och sidor byggda från dessa layouter (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`). **Ingen av dem har ännu körts mot det riktiga spelet.** Inspelarna som kan kontrollera sin indata gör det när paketen kommer, och skriver en `note:` en gång när något inte stämmer. EA WRC och DiRT jämför världshastigheten mot farten, och EA WRC rapporterar också ett paket kortare än den 237 byte långa standardstrukturen. [Spel](games.md) listar källorna och vad som ännu inte är bekräftat per spel.

## Medan den körs {#while-it-runs}

- **Forza** skriver en statusrad varje sekund: mottagna paket, och det öppna varvets nummer, antal sampel och meter, eller `waiting for a race`. Varje avslutat varv skriver `wrote <file>`.
- **Assetto Corsa-spelen** skriver namnet på varje varvfil när den skrivs.
- **Rallyspelen** skriver `listening for <game> on port <port>`, sedan `stage written: <file>`. Vid Ctrl+C skrivs en öppen etapp som är tillräckligt lång som `partial stage written: <file>`.
- **BeamNG** skriver `lap written: <file>`, och vid Ctrl+C `run written: <file>`.
- **Trackmania** skriver ingenting per körning: pluginet skriver sina CSV-filer själv.
- Till slut skriver varje inspelare hur många filer den skrev.

En Forza-inspelning, här matad med syntetiska Data Out-paket av en bil som kör två varv på en 150 m cirkel (varvfilerna, råsidecar-filen och självkontrollsammanfattningen den lämnar):

![telemetri som spelar in två varv från ett syntetiskt Forza-flöde](../assets/img/telemetry-run.svg)

## Filnamn {#file-names}

| Inspelare | Mönster |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa-spelen | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallyspel, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, där `<game>` är det långa namnet (`ea-sports-wrc`, `beamng`, ...), `stage` för rally och `lap` för BeamNG |
| Trackmania-pluginet | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` mot `run` (Forza, Assetto Corsa) och suffixet `_partial` (rally, BeamNG) markerar om varvet eller etappen var avklarad. Tidsstämpeln är när filen skrevs, inte när varvet började.

Bredvid varvfilerna skriver varje inspelare `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet`: varje paket eller sida som kom, helt, även i menyerna och mellan varven. Den skriver också `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, självkontrollen: per pakettyp hur många som kom, hur många som gick in i varvfiler, och `lost`, som är 0. Visaren hoppar över båda när en mapp laddas. Se [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) i README:n.

## Undersidor till den här sidan {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa-spelen](telemetry-assetto-corsa.md)
- [Rallyspel](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Hur varv och etapper delas](lap-splitting.md)
- [Slip, drift och härledda kanaler](slip-and-drift.md)
- [heat3d-lap-filen](lap-format.md)
