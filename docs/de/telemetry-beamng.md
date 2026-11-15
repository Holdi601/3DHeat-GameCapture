---
title: BeamNG.drive
nav_order: 4
lang: de
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # den Mod kopieren, dann aufnehmen
python -m heat3d_capture telemetry --game beamng -o laps      # aufnehmen
```

Dann im Spiel: **Options > Other > Protocols** öffnen und **„others“** einschalten.

Code: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py) und der Mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tests: `tests/test_beamng.py`, auf Paketen, die aus der Struktur des Mods gebaut sind. **Der Mod wurde im Spiel noch nicht ausgeführt.**

## Warum ein Mod {#why-a-mod}

BeamNG sendet Telemetrie über „Protokolle“: Lua-Module im Fahrzeug, die die eigene `lua/vehicle/protocols.lua` des Spiels packt und per UDP aus dem Auto sendet, das der Spieler fährt. Die mitgelieferten enthalten nicht, was eine Fahrzeugsteuerungs-Analyse braucht: OutGauge hat keine Position, MotionSim keine Räder, und OutSim ist in aktuellen Versionen nur ein Platzhalter. Deshalb liefert dieses Projekt ein eigenes Protokoll mit, `heat3d`. Es berührt nichts außerhalb des eigenen Lua-Codes des Fahrzeugs.

## Installation {#installing}

`--install` kopiert `mods/beamng/heat3d` nach `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 und neuer halten Nutzer-Mods dort), löscht vorher eine ältere Kopie und gibt aus, wohin es kopiert hat. Ohne `LOCALAPPDATA` weicht es auf den Benutzerordner aus. Du kannst den Ordner auch von Hand kopieren.

Danach geht `--install` direkt in die Aufnahme über.

## Der Mod {#the-mod}

| Einstellung (in `heat3d.lua`) | Wert |
|---|---|
| Adresse | `127.0.0.1` |
| Port | `4460` - hier ändern und dem Recorder denselben `--port` übergeben |
| Höchste Aktualisierungsrate | 100 Hz |
| Physikschritt | genutzt (`isPhysicsStepUsed` liefert true) |

Jedes Paket besteht aus der 4-Byte-Kennung `H3D1`, gefolgt von 39 Little-Endian-Floats (insgesamt 160 Byte):

| Feld | Anzahl | Quelle im Fahrzeug-Lua |
|---|---|---|
| `time` | 1 | die eigene Uhr des Mods: Summe der Physikschritte, zurückgesetzt, wenn das Fahrzeug zurückgesetzt wird |
| Position | 3 | `obj:getPositionXYZ()` |
| Geschwindigkeit | 3 | `obj:getVelocityXYZ()` (Welt) |
| vorwärts | 3 | `obj:getDirectionVector()` |
| oben | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, und 1/0 aus `absActive` und `tcsActive` |
| `wheelSpeed` | 4 | jede Radgeschwindigkeit an der Oberfläche (m/s) |
| `wheelAngular` | 4 | Winkelgeschwindigkeit mal die Richtung des Rades (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1, wenn das Rad nicht am Boden ist |

Die vier Räder werden nach **ihrer Position am Auto** gewählt, nicht nach Namen (die Namen unterscheiden sich je nach Fahrzeug): vorne oder hinten nach der Position des Knotens entlang des Autos, links oder rechts quer dazu (Fahrzeugrahmen +X links, -Y vorwärts); je Ecke wird das Rad genommen, das am weitesten von der Mitte entfernt ist. Eine fehlende Ecke wird als Nullen mit Material -1 gesendet.

## Was der Recorder daraus macht {#what-the-recorder-does-with-it}

Die Welt von BeamNG hat Z nach oben, die des Viewers Y nach oben. Positionen und Vektoren werden um X gedreht, `(x, y, z) -> (x, z, -y)`, was die Händigkeit der Welt erhält. Danach:

| Kanal | Berechnet als |
|---|---|
| `x`, `y`, `z` | gedrehte Position |
| `speed` | Länge der gedrehten Geschwindigkeit |
| `longVel`, `latVel`, `vertVel` | Geschwindigkeit projiziert auf vorwärts, auf rechts = vorwärts x oben, auf oben |
| `longAcc`, `latAcc`, `vertAcc` | die Änderung der Weltgeschwindigkeit über ±2 Samples, auf dieselben Achsen projiziert (das eigene Sensorsystem des Autos ist nicht dokumentiert, deshalb werden sie nicht genutzt) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | wie gesendet |
| `absActive`, `tcActive` | die ABS- und TC-Lampen, wo das Auto sie hat |
| `wheelSurfaceSpeed.*` | Betrag der Radgeschwindigkeit an der Oberfläche |
| `wheelSpeed.*` | Drehung |
| `wheelLoad.*` | Last |
| `groundContact.*` | 0, wenn das Material negativ ist, sonst 1 |

Pakete ohne die Kennung oder kürzer als 160 Byte werden ignoriert.

## Runden {#laps}

`LineSplitter`, wie bei AC EVO: Der Punkt, an dem die Aufnahme begann, ist die Linie; eine Runde schließt sich dort, wo das Auto danach am nächsten an ihr vorbeifährt, in dieselbe Richtung, frühestens 300 m später; ein Lauf schließt sich, wenn das Auto 8 Sekunden lang steht. Eine Runde zählt nur als vollständig, wenn sie mit mehr als 5 m/s begann, sodass die erste Runde aus dem Stand eine Teilrunde ist. Wenn die Uhr des Mods um mehr als eine halbe Sekunde zurückspringt (das Auto wurde zurückgesetzt), wird der in diesem Moment offene Lauf zuerst geschlossen - als Teillauf geschrieben, wenn er mindestens 300 m abdeckte, wie am Ende einer Aufnahme - und danach beginnt der Splitter von vorn. Siehe [Runden- und Abschnittsaufteilung](lap-splitting.md).

## Die Rundendatei {#the-lap-file}

`game` ist `beamng`, `meta` ist `{"discipline": "circuit"}`, Dateien heißen `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Es wird kein Schlupf geschrieben; der Viewer leitet ihn aus den Radgeschwindigkeiten an der Oberfläche ab (siehe [Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md)). Die Positionen liegen im selben Bezugssystem, das der BeamNG-Streckenexport von GameFiles schreibt, sodass eine aufgezeichnete Runde auf einer exportierten Strecke liegt.
