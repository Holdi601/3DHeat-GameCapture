---
title: Telemetrie-Recorder
nav_order: 3
lang: de
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetrie-Recorder {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` zeichnet jeden Kanal auf, den ein Spiel sendet, zerlegt den Strom in Runden oder Etappen und schreibt eine
[`heat3d-lap`](lap-format.md)-JSON-Datei pro Runde in einen Ordner. Der Tab Rennanalyse des Viewers liest diese
Dateien. Die Aufnahme läuft, bis du **Strg+C** drückst. Die Runde oder Etappe, die in diesem Moment offen ist, wird geschrieben,
wenn sie lang genug ist, um behalten zu werden (siehe [Runden- und Etappenteilung](lap-splitting.md)).

Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
und die Module in [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Optionen {#options}

| Option | Vorgabe | Bedeutung |
|---|---|---|
| `--game` | `forza` | Eines von `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Ordner, in den die Rundendateien geschrieben werden. Wird angelegt, falls er fehlt. Wird von `trackmania` ignoriert, dessen Plugin die Dateien selbst schreibt. |
| `--port` | `5300` | UDP-Port, auf dem gelauscht wird. **Für jedes Spiel außer Forza bedeutet der Wert 5300 „der Standardport des Spiels“**: 20777 für `wrc` und die DiRT-Spiele, 6776 für `rbr`, 4460 für `beamng`. Gib eine andere Zahl an, um ihn zu überschreiben. Nicht genutzt von den Assetto-Corsa-Spielen (gemeinsamer Speicher) oder Trackmania (Dateien). |
| `--forward` | keine | nur Forza: `host:port`, an das jedes empfangene Paket unverändert weitergegeben wird. `127.0.0.1:5301` für FH Companion. Ein nacktes `:5301` heißt `127.0.0.1:5301`. |
| `--install` | aus | `beamng`: kopiert die Protokoll-Mod zuerst in die entpackten Mods von BeamNG. `trackmania`: kopiert das Openplanet-Plugin in den Plugin-Ordner von Openplanet. Wird von den anderen Spielen ignoriert. |
| `--configure` | keine | nur `wrc`: Pfad zur `config.json` der Telemetrie von EA SPORTS WRC; schaltet das Standardpaket `wrc` vor der Aufnahme ein (vorher gesichert). |
| `--surface` | keine | Rallyespiele (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` oder `mixed`, geschrieben in `meta.surface` der Rundendatei. Ohne ihn wird kein Untergrund geschrieben. |

## Die Spiele auf einen Blick {#the-games-at-a-glance}

| `--game` | Spiel | Quelle | Standardport | Teilen | `game` in der Datei | Seite |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (inkl. 2023) | Data Out UDP | 5300 | der Rundenzähler des Spiels (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, oder `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | gemeinsamer Speicher `acpmf_*` | - | Rundenzähler (`CounterSplitter`) | `assetto-corsa` | [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | gemeinsamer Speicher `acpmf_*` | - | Rundenzähler (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | gemeinsamer Speicher `acevo_pmf_*` | - | Startlinie (`LineSplitter`) | `assetto-corsa-evo` | [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | gemeinsamer Speicher `acpmf_*` | - | Startlinie / Halt (`LineSplitter`) | `assetto-corsa-rally` | [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, Struct `wrc` | 20777 | Etappenuhr (`StageSplitter`) | `ea-sports-wrc` | [Rallyespiele](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | Etappenuhr (`StageSplitter`) | `dirt-rally-2` | [Rallyespiele](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | Etappenuhr (`StageSplitter`) | `dirt-rally` | [Rallyespiele](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | Etappenuhr (`StageSplitter`) | `dirt-4` | [Rallyespiele](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | Etappenuhr (`StageSplitter`) | `richard-burns-rally` | [Rallyespiele](telemetry-rally.md) |
| `beamng` | BeamNG.drive | Protokoll-Mod `heat3d`, UDP | 4460 | Startlinie (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-Plugin, CSV-Dateien | - | pro Lauf, im Plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | eigene `.ibt`-Dateien, vom Viewer gelesen | - | der Rundenzähler des Simulators | `iracing` | [iRacing](telemetry-iracing.md) |

## Stand {#status}

Der Forza-Recorder ist der, der am meisten erprobt ist. Die Recorder für Kunos, Rallye, BeamNG und Trackmania sind nach den veröffentlichten Layouts gebaut
und an synthetischen Paketen und Seiten getestet, die aus diesen Layouts entstehen (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`).
**Keiner davon ist bisher gegen das echte Spiel gelaufen.** Die Recorder, die ihre Eingabe prüfen können, tun das, sobald Pakete eintreffen, und melden einmal
eine `note:`, wenn etwas nicht passt (EA WRC und DiRT vergleichen die Weltgeschwindigkeit mit dem Tempo; EA WRC meldet außerdem ein Paket, das kürzer als
das 237-Byte-Standard-Struct ist). [Spiele](games.md) listet die Quellen und was je Spiel noch nicht bestätigt ist.

## Während der Aufnahme {#while-it-runs}

- **Forza** gibt jede Sekunde eine Statuszeile aus: empfangene Pakete und die Runde, die gerade offen ist, mit Nummer, Anzahl der Messpunkte und Metern,
  oder `waiting for a race`. Jede fertige Runde gibt `wrote <file>` aus.
- **Assetto-Corsa-Spiele** nennen den Namen jeder Rundendatei, sobald sie geschrieben wird.
- **Rallyespiele** geben `listening for <game> on port <port>` aus, dann `stage written: <file>`. Bei Strg+C wird eine offene Etappe, die lang genug
  zum Behalten ist, als `partial stage written: <file>` geschrieben.
- **BeamNG** gibt `lap written: <file>` aus, und bei Strg+C `run written: <file>`.
- **Trackmania** gibt pro Lauf nichts aus: Das Plugin schreibt seine CSV-Dateien selbst.
- Am Ende gibt jeder Recorder aus, wie viele Dateien er geschrieben hat.

Eine Forza-Aufnahme, hier mit synthetischen Data-Out-Paketen eines Autos gespeist, das zwei Runden auf einem 150-m-Kreis fährt (die Rundendateien, das
Roh-Beiblatt und die Selbstprüfung, die es hinterlässt):

![Telemetrie-Aufnahme von zwei Runden aus einem synthetischen Forza-Feed](../assets/img/telemetry-run.svg)

## Dateinamen {#file-names}

| Recorder | Muster |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto-Corsa-Spiele | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallyespiele, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, wobei `<game>` der lange Name ist (`ea-sports-wrc`, `beamng`, ...), `stage` für Rallye und `lap` für BeamNG |
| Trackmania-Plugin | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` gegenüber `run` (Forza, Assetto Corsa) und das Suffix `_partial` (Rallye, BeamNG) zeigen, ob die Runde oder Etappe beendet wurde. Der Zeitstempel
ist der Moment, in dem die Datei geschrieben wurde, nicht der Beginn der Runde.

Neben den Rundendateien schreibt jeder Recorder `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet`: jedes Paket und jede Seite, die ankam, vollständig, auch in den
Menüs und zwischen den Runden. Dazu `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, die Selbstprüfung: je Pakettyp, wie viele kamen, wie viele in
Rundendateien gingen, und `lost`, das 0 ist. Der Viewer überspringt beide, wenn ein Ordner geladen wird. Siehe
[Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) in der README.

## Unterseiten dieser Seite {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md)
- [Rallyespiele](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Runden- und Etappenteilung](lap-splitting.md)
- [Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md)
- [Die Datei heat3d-lap](lap-format.md)
