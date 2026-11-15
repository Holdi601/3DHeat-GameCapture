---
title: Trackmania (2020)
nav_order: 5
lang: "de"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Code: das Openplanet-Plugin [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder) (`info.toml`, `main.as`). **Das Plugin wurde im Spiel noch nicht ausgeführt**; der CSV-Leser des Viewers ist getestet.

## Warum ein Plugin, das Dateien schreibt {#why-a-plugin-that-writes-files}

Trackmania hat keine eigene Telemetrie-Ausgabe. Openplanet, die Plugin-Plattform des Spiels, stellt den Fahrzeugzustand des angesehenen Autos Plugins zur Verfügung, aber Openplanet-Plugins können kein UDP senden. Deshalb schreibt das Plugin je Lauf eine CSV-Datei in seinen eigenen Speicherordner, und der Viewer liest diese Dateien so, wie sie sind. Es gibt keinen Recorder-Prozess: `telemetry --game trackmania` installiert nur das Plugin (mit `--install`) und gibt aus, wo die Dateien erscheinen.

## Installation und Laden {#installing-and-loading}

- `--install` kopiert `mods/trackmania/Heat3dRecorder` nach `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` und ersetzt eine ältere Kopie. Ohne `--install` wird nichts kopiert.
- Im Spiel: **Openplanet > Developer > Load plugin** wählen und `3DHeat recorder` auswählen.
- Das Plugin braucht das Openplanet-Plugin **VehicleState** (`dependencies = ["VehicleState"]` in `info.toml`).
- Unsignierte Plugins laden nur im **Entwicklermodus von Openplanet**, der das Online-Spiel einschränkt. Das Plugin kann auf openplanet.dev signiert werden; hier ist es nicht signiert.

Läufe werden nach `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder` geschrieben. Lade diese CSV-Dateien im Tab **Rennanalyse** des Viewers. `-o` und `--port` werden für Trackmania ignoriert.

## Was das Plugin aufzeichnet {#what-the-plugin-records}

Es liest nur, was Openplanet freigibt - den Fahrzeugzustand des angesehenen Autos (`VehicleState::ViewingPlayerState()`) und die Rundenzeit des Spielers sowie die Zahl der Respawns (`CSmScriptPlayer`) -, sendet nirgendwohin und verändert nichts im Spiel. Eine Zeile wird bei jedem Frame geschrieben (`Update`), daher ist die Samplerate die Framerate des Spiels.

| Spalte | Quelle |
|---|---|
| `time` | `CurrentRaceTime` / 1000, Sekunden |
| `x`, `y`, `z` | `Position` (Welt, Y nach oben) |
| `speed` | Länge von `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 oder 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | je Rad `SlipCoef` (ein Gleitmaß von 0 bis 1) |
| `loose` | 1, wenn das Bodenmaterial eines Rads Grass, Ice, Sand, Dirt, Green oder RoadIce ist |
| `airborne` | 1, wenn das Auto keinen Bodenkontakt hat |
| `respawns` | Respawns seit Beginn des Laufs |

## Läufe {#runs}

- Ein Lauf **beginnt** beim ersten Frame, in dem die Rundenzeit nicht negativ ist (der Countdown wird nicht aufgezeichnet).
- Er **endet**, wenn die UI-Sequenz des Playgrounds die Ziel-Sequenz ist (Wert 11): Die Datei wird als vollständig geschrieben, mit der letzten Rundenzeit als `seconds`.
- Er wird **abgebrochen** - geschrieben mit `_partial` im Namen und `"complete": false` -, wenn die Rennuhr um mehr als eine halbe Sekunde zurückspringt (ein Neustart) oder wenn der Spieler den Playground verlässt.
- Ein Lauf mit weniger als 20 Zeilen wird nicht geschrieben.

## Die Datei {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Benannt `run_<JJJJ-MM-TT_HH-MM-SS>[_partial].csv`. Der Kartenname hat Formatierungscodes entfernt, und doppelte Anführungszeichen sind durch einfache ersetzt. Werte werden mit vier Nachkommastellen geschrieben. Das Format steht in [Die heat3d-Rundendatei](lap-format.md#the-csv-form).

Das `meta` im Kopf trägt `"slip": "index"` - die `slipIndex.*`-Kanäle sind das eigene Gleitmaß von Trackmania von 0 bis 1, kein physikalischer Schlupf - und `"discipline": "arcade"`.
