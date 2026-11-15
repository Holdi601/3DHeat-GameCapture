---
title: Assetto-Corsa-Spiele
nav_order: 2
lang: "de"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO und AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Code: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tests: `tests/test_kunos.py` (synthetische Seiten). Noch nicht gegen die echten Spiele gelaufen.

## Woher die Daten kommen {#where-the-data-comes-from}

Die Spiele von Kunos veröffentlichen Telemetrie für Apps als **benannte gemeinsame Speicherseiten unter Windows**, die das Spiel schreibt
und die jeder lesen darf. Der Recorder öffnet sie nur lesend (`mmap` mit einem Markennamen). Er muss deshalb **auf dem PC laufen, auf dem das
Spiel läuft**, unter Windows. Anderswo beendet er sich mit einer Meldung. Die Seiten werden einmal geöffnet, wenn der Recorder startet.
Die sichere Reihenfolge ist: erst das Spiel starten und ins Auto steigen. Ob es auch umgekehrt geht, also den Recorder zuerst, ist nicht geprüft.

| `--game` | Physikseite | Grafikseite (Rundenzähler) | Statische Seite (Namen) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nicht genutzt | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nicht genutzt | `Local\acevo_pmf_static` |

Die Physikseite wird 200 Mal pro Sekunde gelesen (`hz=200`). Ein neuer Messpunkt wird nur genommen, wenn seine `packetId` sich geändert
hat und nicht null ist. Die ersten 800 Bytes der Physikseite haben in allen vier Spielen dasselbe Layout. Die Seite des ersten Spiels ist nur
580 Bytes sicher. Lässt sich eine 800-Byte-Zuordnung nicht öffnen, fällt der Recorder auf 580 zurück, und die Felder dahinter fehlen.

## Position {#position}

Keine der Seiten trägt eine Autoposition als solche. Die Physikseite enthält aber **den Aufstandspunkt jedes Reifens in Weltkoordinaten**
(Versatz 420, vier XYZ-Tripel). Die Position des Autos ist der Mittelwert der vier. Eine Seite, deren Aufstandspunkte alle null sind (Menü,
Garage), ergibt keinen Messpunkt.

## Kanäle {#channels}

| Kanal | Aus | Hinweise |
|---|---|---|
| `time` | die eigene Uhr des Recorders | Sekunden seit Beginn der Aufnahme, auf den ersten Messpunkt der Runde verschoben |
| `x`, `y`, `z` | mittlerer Reifen-Aufstandspunkt | Welt-Meter |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | die Einheiten des Spiels, pro Runde auf -1..1 skaliert, mit dem größten absoluten Wert, den die Runde nutzte, **nur wenn** dieser Wert 1,05 übersteigt (eine Eingabe, die schon in -1..1 liegt, bleibt unverändert) |
| `gear` | `gear - 1` | das Spiel zählt 0 Rückwärts, 1 Leerlauf, 2 erster Gang; geschrieben als -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, mal 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokale Geschwindigkeit bei Versatz 568 | Fahrzeugsystem; nur wenn nicht null. Auf welche Seite die x-Achse zeigt, ist in beiden Richtungen dokumentiert. Man liest deshalb die Größe des Driftwinkels, nicht sein Vorzeichen |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | Versatz 564 | nur 800-Byte-Seite |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: Versatz 204 und 252, als 1 geschrieben, wenn über 0; AC: `tcInAction`/`absInAction` aus der 800-Byte-Seite, wenn vorhanden | Hilfen greifen |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | abgeleitet | 0..1 des in dieser Runde genutzten Federwegs (Minimum bis Maximum von `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | Versatz 640, 656 (800-Byte-Seite) | durch einen typischen Spitzenwert geteilt, siehe unten |
| `slipRatioRaw.*`, `slipAngleRaw.*` | dasselbe | die physikalischen Werte, unskaliert |
| `padLife.*`, `discLife.*` | Versatz 740, 756 | nur 800-Byte-Seite |

AC Rally sendet seine Reifen- und Bremstemperaturen in Kelvin: Bei `--game acrally` wird von jedem dieser Werte über 200 273,15 abgezogen.

`wheelSlip` (Versatz 56) wird dekodiert, aber nicht geschrieben.

## Schlupf-Skalierung {#slip-scaling}

Forza sendet den Schlupf so normiert, dass 1 die Grenze des Grips ist. Kunos sendet das physikalische Schlupfverhältnis und den
Schlupfwinkel. Deshalb teilt der Recorder sie durch einen typischen Asphalt-Spitzenwert: **0,12** für das Schlupfverhältnis und **0,14 rad
(etwa 8 Grad)** für den Schlupfwinkel. So gilt die Lesart „über 1 heißt Rutschen“ der Anzeigen des Viewers näherungsweise. Die Rohwerte
bleiben daneben erhalten, und `"meta": {"slip": "scaled"}` wird geschrieben. Wo der Grip tatsächlich endet, misst der Viewer pro Auto aus
den Runden. Siehe [Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md).

## Runden {#laps}

- **AC und ACC** zählen Runden auf der Grafikseite (`completedLaps` bei Versatz 132, die Zeit der letzten Runde in Millisekunden bei 144).
  `CounterSplitter` schließt eine Runde, wenn der Zähler sich ändert. Sie wird nur dann als vollständig markiert, mit der Rundenzeit des Spiels,
  wenn der Zähler genau um eins gestiegen ist.
- **AC EVO und AC Rally** werden nicht auf Runden gelesen (die Grafikseite von EVO hat ein anderes, größeres Layout; AC Rally fährt Etappen).
  `LineSplitter` nutzt den Punkt, an dem die Aufnahme begann, als Linie: Eine Runde schließt sich, wenn das Auto die Linie das nächste Mal am
  nächsten passiert, in dieselbe Richtung. Eine Etappe oder ein beliebiger Lauf schließt sich, wenn das Auto 8 Sekunden lang stillsteht.

Details und Schwellen: [Runden- und Etappenteilung](lap-splitting.md).

## Namen von Strecke und Auto {#track-and-car-names}

Sie werden einmal gelesen, aus der statischen Seite, wenn der erste Messpunkt eintrifft: bei AC, ACC und AC Rally das Auto (UTF-16, Versatz 68)
und die Strecke (Versatz 134); bei AC EVO die Strecke und ihre Konfiguration (Ein-Byte-Text bei den Versatzen 136 und 169, mit einem Leerzeichen
verbunden) und kein Auto. Sie gehen in die Datei als `track` und `car: {"name": ...}`.

## Die Rundendatei {#the-lap-file}

`game` ist `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` oder `assetto-corsa-rally`. `meta` ist
`{"slip": "scaled", "discipline": "rally"}` für AC Rally und `{"slip": "scaled", "discipline": "circuit"}` für die anderen drei. Ein `surface`
wird nicht geschrieben.

## Quellen {#sources}

Der AC1-SDK für gemeinsamen Speicher; die Dokumentation des gemeinsamen Speichers von ACC (v1.8); das Layout von AC EVO, wie es in
`albertowd/live-telemetry-evo` gemessen wurde; das von AC Rally, wie es `LuizZak/AssettoCorsaRallyTelemetryReader` liest. Siehe [Spiele](games.md).
