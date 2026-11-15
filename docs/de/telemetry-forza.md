---
title: Forza
nav_order: 1
lang: de
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon und Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Code: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(Layouterkennung),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(alle Kanäle, Rundendateien, Weiterleitung).

## Im Spiel einschalten {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, Port `5300` (oder was du als `--port` übergibst). Forza Motorsport bietet außerdem
ein Paketformat: Es muss **Dash** sein, nicht Sled. Sled trägt gar keine Position, und der Recorder lehnt es ab.

Der Recorder bindet an `127.0.0.1`, also muss das Spiel auf demselben PC laufen.

## Was das Spiel sendet und wie das Layout gefunden wird {#what-the-game-sends-and-how-the-layout-is-found}

Data Out ist ein UDP-Paket pro Simulationstick (etwa 60 pro Sekunde), ein flaches Little-Endian-C-Struct in diesen Größen:

| Länge | Variante |
|---|---|
| 232 Bytes | Motorsport „Sled“: keine Position. Wird mit einer Meldung abgelehnt, die auf Dash umzustellen rät. |
| 311 Bytes | Motorsport „Dash“: Sled-Block plus der 79-Byte-Dash-Block |
| 324 Bytes | Horizon „Dash“: dasselbe mit Auffüllung zwischen den beiden Blöcken |
| 331 Bytes | Forza Motorsport (2023): Dash plus 20 Bytes Reifenverschleiß und die Strecken-ID |

Der Sled-Block (Versatz 0-231) ist stabil. Wo der Dash-Block in der Horizon-Variante beginnt, wird in veröffentlichten Quellen widersprüchlich
beschrieben. Falsch zu raten schlägt nicht fehl, sondern liefert plausible Gleitkommazahlen aus den falschen Feldern. Deshalb wird der Anfang
**ermittelt**:

1. Mögliche Anfänge werden der Reihe nach probiert: `Länge - 79` (der Dash-Block reicht in jeder dokumentierten Variante bis zum letzten Byte),
   232, 244, und 232 bis 260 in Schritten von 4.
2. Jeder Anfang wird an Paketen eines fahrenden Autos bewertet (eine Geschwindigkeitskomponente über 1 m/s). Der Geschwindigkeitsvektor des
   Sled-Blocks und der skalare Wert `Speed` des Dash-Blocks sind dieselbe Größe an zwei Stellen. Deshalb ist `| |Geschwindigkeit| - Speed |`
   nur für den richtigen Anfang nahe null.
3. Der Anfang mit der kleinsten schlimmsten Abweichung gewinnt, wenn diese höchstens **1 m/s** beträgt. Sonst wartet die Erkennung weiter.

Während das Auto geparkt steht, lesen alle Anfänge null und stimmen überein, was nichts beweist. Deshalb **wartet die Erkennung, bis das Auto
fährt**: Man muss ein paar Meter fahren, bevor man Ausgabe erwartet. Während des Wartens werden bis zu 600 Pakete gehalten (auf die letzten 300
gekürzt). Ist das Layout einmal bekannt, werden die gehaltenen Pakete ebenfalls dekodiert, damit der Anfang der ersten Runde nicht verloren geht.
Pakete einer anderen Länge als dem erkannten Layout, Pakete unter 311 Bytes und Pakete mit einer nicht endlichen Position oder Geschwindigkeit
werden für die Rundendateien ignoriert.

Welches Forza es ist, folgt aus dem Layout: Ein Horizon-Layout ergibt `"game": "forza-horizon"`, ein Motorsport- oder 331-Byte-Layout ergibt
`"forza-motorsport"`, alles andere `"forza"`. Der Name des erkannten Layouts (`Horizon dash`, `Motorsport dash`, `331-byte dash`) wird als `layout`
geschrieben.

## Aufgenommene Kanäle {#channels-recorded}

Jedes Feld des Pakets wird dekodiert (`decode_full`) und umgerechnet:

- Pedale `throttle`, `brake`, `clutch`, `handbrake` von 0..255 auf 0..1;
- `steer` von -127..127 auf -1..1; `drivingLine` und `aiBrakeDifference` ebenso durch 127 geteilt;
- `tireTemp.FL` ... `.RR` von Fahrenheit in Celsius;
- `latAcc`, `longAcc`, `vertAcc` und `yawRate` sind Kopien von `accelX`, `accelZ`, `accelY` und `angVelY` unter den einheitlichen Namen (Fahrzeugsystem:
  x rechts, y oben, z vorn);
- die Sled-Geschwindigkeit, die im Fahrzeugsystem des Autos liegt (x rechts, y oben, z vorn, nicht im System der Welt), wird direkt unter den einheitlichen
  Namen `latVel`, `vertVel` und `longVel` geschrieben. So liest der Viewer den Driftwinkel direkt ab, statt ihn aus Richtung und Weg zu schätzen.

Die Kanäle der Rundendatei sind alle diese außer den Feldern pro Runde:

| Gruppe | Kanäle |
|---|---|
| Zeit und Ort | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Bewegung | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Fahrer | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Je Rad (`.FL .FR .RL .RR`) | `suspension` (0 ausgefahren .. 1 eingefedert), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normiert: über 1 verliert der Reifen die Haftung), `wheelSpeed` (rad/s), `rumble` (auf einem Rumpelstreifen), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Nur Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` ist der Rundentimer des Spiels minus seinem Wert beim ersten Messpunkt der Runde. `distance` ist die zurückgelegte Strecke des Spiels minus
ihrem ersten Wert. Die Positionen sind die Weltkoordinaten von Forza in Metern, unverändert (y ist oben; die Welt ist linkshändig).

Einmal pro Runde statt pro Messpunkt, unter `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Die Strecken-ID
von FM2023 kommt ebenfalls einmal hinein, als `lap.trackOrdinal`. Nicht pro Messpunkt gespeichert wird `isRaceOn` (1 in jedem Bild einer Runde).
`timestampMs`, `raceTime`, `bestLap` und `lastLap` bleiben als Kanäle erhalten.

Der Rest der Datei wird wie bei jedem anderen Recorder gefüllt:

- `"track": null`: Forza Horizon nennt die Strecke nicht, und Forza Motorsport nummeriert sie nur;
- `"meta": {"slip": "peak", "discipline": "circuit"}`: Die Schlupfkanäle sind so normiert, dass über 1 der Reifen die Haftung verliert;
- `units` listet nur die Kanäle, die die Datei hat (radbezogene nach ihrem Grundnamen);
- ein Wert, der keine endliche Zahl ist, wird als `null` geschrieben, nie als `NaN`.

Siehe [Die Datei heat3d-lap](lap-format.md).

## Wie Runden geteilt werden {#how-laps-are-split}

`LapSplitter` (siehe [Runden- und Etappenteilung](lap-splitting.md)): Eine Runde schließt sich, wenn der Rundenzähler des Spiels weiterspringt. Ihre
Zeit ist dann das `lastLap` des Spiels selbst (das, was das Spiel anzeigt). Ein Rennen von Punkt zu Punkt oder eine Sitzung, die mitten in einer Runde
endet, schließt sich, wenn das Spiel das Rennen verlässt (`isRaceOn` fällt), wenn die Pakete 2 Sekunden lang ausbleiben, oder wenn der Zeitstempel des
Spiels zurückspringt. Sie wird als `run` behalten, wenn sie mindestens 400 m umfasst.

## Weiterleitung an FH Companion {#relaying-to-fh-companion}

Das Spiel sendet Data Out an nur eine Adresse. Mit `--forward host:port` gibt der Recorder **jedes empfangene Paket unverändert weiter**, bevor er
irgendetwas dekodiert. Das gilt auch, solange er noch auf die Layouterkennung wartet. So funktioniert eine andere App, die den Feed liest, weiter:
Man stellt das Spiel auf 5300, die andere App auf 5301 und startet mit `--forward 127.0.0.1:5301`.

FH Companion ist eine eigene App, nicht Teil von 3DHeat. Sie hält eine Runden-Bibliothek unter `%LOCALAPPDATA%\FHCompanion\laps`: einen Ordner pro
Strecke, eine Rundendatei pro Runde, etwa alle fünf Meter abgetastet, und neben jeder Rundendatei `<lap>.json.tele.gz`, das gesamte Data Out der Runde
mit der Rate des Spiels. 3DHeat liest beides:

- **Der Viewer liest `.tele.gz` direkt**, wenn du sie (mit oder ohne ihre Rundendatei) auf dem Tab Rennanalyse ablegst. Er ordnet Forzas
  eigene Feldnamen (`PositionX`, `VelocityX`, `TireSlipRatio` + Rad, ...) den einheitlichen Kanälen zu, macht aus den fahrzeuglokalen
  `VelocityX/Y/Z` die Kanäle `latVel`, `vertVel`, `longVel`, rechnet Reifentemperaturen von Fahrenheit um, verwirft Zeilen, die die vorherige nur durch
  den Takt des Recorders wiederholen, und markiert den Schlupf als `peak`. Liegt auch die Rundendatei dabei, übernimmt die Runde Auto und Rundenzeit von
  dort. Dieser Leser steckt im Viewer (`src/race/adapters.ts`, `readForzaTelemetry`), nicht in diesem Repository.
- **Der Befehl `laps`** liest die Runden-Bibliothek und schreibt die Route einer Strecke und eine CSV mit jedem Messpunkt; siehe
  [Befehlsreferenz](commands.md#laps).

## Andere Verwendungen desselben Feeds {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` zeichnet nur die Positionen auf, die beim Fahren alle paar Sekunden gespeichert werden; siehe
  [Befehlsreferenz](commands.md#route).
- Die Option „Renn-Telemetrie (Forza)“ des Scan-Fensters nutzt den Feed als exakte Kameraposen für die Rekonstruktion; siehe
  [Kamerapose und Skala](reconstruction-pose.md#telemetry-poses).

## Hinweise und Vorbehalte {#notes-and-caveats}

- Womit Forza seinen Schlupf normiert, ist nicht dokumentiert. `1` wird als Grenze des Grips gelesen, aber der Viewer misst, wo der Grip jedes
  Autos tatsächlich nachlässt.
- Die Sled-Geschwindigkeit ist fahrzeuglokal, wie es Forzas Data-Out-Dokumentation beschreibt und aufgezeichnete Runden bestätigen (ihr Vorwärtsanteil
  trägt die Geschwindigkeit, ihr seitlicher bleibt nahe null). Die Layouterkennung nutzt nur die Länge, die in jedem Bild gleich ist.
- Positionen sind die Welt des Spiels, y oben und linkshändig. Die Richtungen von `yaw`, `pitch` und `roll` wurden an aufgezeichneten Runden geprüft: Das
  Gieren ist gleich der Fahrtrichtung `atan2(dx, dz)`, ein positives Nicken ist Nase nach unten, und ein positives Rollen senkt die rechte Seite.
