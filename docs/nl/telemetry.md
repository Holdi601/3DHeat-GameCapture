---
title: "Telemetrieopnemers"
nav_order: 3
lang: "nl"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetrieopnemers {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` neemt elk kanaal op dat een spel stuurt, splitst de stroom in ronden of etappes, en schrijft één [`heat3d-lap`](lap-format.md)-JSON-bestand per ronde in een map. Het tabblad Race-analyse van de viewer leest die bestanden. Opnemen gaat door tot je op **Ctrl+C** drukt; de ronde of etappe die dan open is, wordt geschreven als ze lang genoeg is om te bewaren (zie [Ronde- en etappesplitsing](lap-splitting.md)).

Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py) en de modules in [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opties {#options}

| Optie | Standaard | Betekenis |
|---|---|---|
| `--game` | `forza` | Een van `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Map waarin de rondenbestanden worden geschreven. Wordt aangemaakt als ze ontbreekt. Genegeerd door `trackmania`, waarvan de plugin de bestanden zelf schrijft. |
| `--port` | `5300` | UDP-poort om op te luisteren. **Voor elk spel behalve Forza betekent de waarde 5300 "de eigen standaardpoort van het spel"**: 20777 voor `wrc` en de DiRT-spellen, 6776 voor `rbr`, 4460 voor `beamng`. Geef een ander getal om dat te overschrijven. Niet gebruikt door de Assetto Corsa-spellen (gedeeld geheugen) of Trackmania (bestanden). |
| `--forward` | geen | Alleen Forza: `host:port` om elk ontvangen pakket ongewijzigd door te sturen. `127.0.0.1:5301` voor FH Companion. Een kale `:5301` betekent `127.0.0.1:5301`. |
| `--install` | uit | `beamng`: kopieer de protocolmod eerst naar de uitgepakte mods van BeamNG. `trackmania`: kopieer de Openplanet-plugin naar de pluginmap van Openplanet. Genegeerd door de andere spellen. |
| `--configure` | geen | Alleen `wrc`: pad naar het `config.json` voor telemetrie van EA SPORTS WRC; zet het standaardpakket `wrc` aan voordat wordt opgenomen (eerst wordt een back-up gemaakt). |
| `--surface` | geen | Rallyspellen (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` of `mixed`, geschreven naar `meta.surface` van het rondenbestand. Zonder deze optie wordt geen wegdek geschreven. |

## De spellen in het kort {#the-games-at-a-glance}

| `--game` | Spel | Bron | Standaardpoort | Splitsing | `game` in het bestand | Pagina |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (incl. 2023) | Data Out UDP | 5300 | de rondenteller van het spel (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, of `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | gedeeld geheugen `acpmf_*` | - | rondenteller (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa-spellen](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | gedeeld geheugen `acpmf_*` | - | rondenteller (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa-spellen](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | gedeeld geheugen `acevo_pmf_*` | - | startlijn (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa-spellen](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | gedeeld geheugen `acpmf_*` | - | startlijn / stop (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa-spellen](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, structuur `wrc` | 20777 | etappeklok (`StageSplitter`) | `ea-sports-wrc` | [Rallyspellen](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | etappeklok (`StageSplitter`) | `dirt-rally-2` | [Rallyspellen](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | etappeklok (`StageSplitter`) | `dirt-rally` | [Rallyspellen](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | etappeklok (`StageSplitter`) | `dirt-4` | [Rallyspellen](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | etappeklok (`StageSplitter`) | `richard-burns-rally` | [Rallyspellen](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d`-protocolmod, UDP | 4460 | startlijn (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-plugin, CSV-bestanden | - | per run, in de plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | de eigen `.ibt`-bestanden, gelezen door de viewer | - | de rondenteller van de sim | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

De Forza-opnemer is degene die het meest is getest. De opnemers voor Kunos, rally, BeamNG en Trackmania zijn gebouwd op de gepubliceerde indelingen en getest op synthetische pakketten en pagina's die uit die indelingen zijn gebouwd (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **geen ervan is tot nu toe tegen het echte spel gedraaid**. De opnemers die hun invoer kunnen controleren, doen dat zodra de pakketten binnenkomen en geven één keer een `note:` als iets niet klopt (EA WRC en DiRT vergelijken de wereldsnelheid met de snelheid; EA WRC meldt ook een pakket dat korter is dan de standaardstructuur van 237 bytes). [Spellen](games.md) geeft per spel de bronnen en wat nog niet is bevestigd.

## Tijdens het opnemen {#while-it-runs}

- **Forza** toont elke seconde een statusregel: ontvangen pakketten, en het nummer, het aantal metingen en de meters van de open ronde, of `waiting for a race`. Elke afgeronde ronde toont `wrote <file>`.
- **Assetto Corsa-spellen** tonen de naam van elk rondenbestand zodra het is geschreven.
- **Rallyspellen** tonen `listening for <game> on port <port>`, daarna `stage written: <file>`; bij Ctrl+C wordt een open etappe die lang genoeg is om te bewaren geschreven als `partial stage written: <file>`.
- **BeamNG** toont `lap written: <file>`, en bij Ctrl+C `run written: <file>`.
- **Trackmania** toont niets per run: de plugin schrijft zijn CSV-bestanden zelf.
- Aan het eind toont elke opnemer hoeveel bestanden hij heeft geschreven.

Een Forza-opname, hier gevoed met synthetische Data Out-pakketten van een auto die twee ronden rijdt van een cirkel van 150 m (de rondenbestanden, de ruwe bijlage en de zelfcontrole die het achterlaat):

![Telemetrie-opname van twee ronden uit een synthetische Forza-feed](../assets/img/telemetry-run.svg)

## Bestandsnamen {#file-names}

| Opnemer | Patroon |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa-spellen | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallyspellen, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, waarbij `<game>` de lange naam is (`ea-sports-wrc`, `beamng`, ...), `stage` voor rally en `lap` voor BeamNG |
| Trackmania-plugin | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` tegenover `run` (Forza, Assetto Corsa) en het achtervoegsel `_partial` (rally, BeamNG) laten zien of de ronde of etappe is afgemaakt. De tijdstempel is het moment waarop het bestand werd geschreven, niet waarop de ronde begon.

Naast de rondenbestanden schrijft elke opnemer `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - elk pakket of elke pagina die binnenkwam, heel bewaard, ook in de menu's en tussen de ronden door - en `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, de zelfcontrole: per pakkettype hoeveel er kwamen, hoeveel er in rondenbestanden terechtkwamen, en `lost`, wat 0 is. De viewer slaat beide over wanneer een map wordt geladen. Zie [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) in de README.

## Onderliggende pagina's {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa-spellen](telemetry-assetto-corsa.md)
- [Rallyspellen](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Ronde- en etappesplitsing](lap-splitting.md)
- [Slip, drifthoek en afgeleide kanalen](slip-and-drift.md)
- [Het `heat3d-lap`-bestand](lap-format.md)
