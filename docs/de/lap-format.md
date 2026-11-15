---
title: Die Datei `heat3d-lap`
nav_order: 9
lang: "de"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Die Datei `heat3d-lap` {#the-heat3d-lap-file}

Jeder Telemetrie-Recorder in diesem Repository schreibt eine Datei pro Runde oder Etappe, in derselben
Form, egal für welches Spiel. Der Streckenexport in [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
liest sie wieder ein, um Spiel, Level und gefahrene Linie zu finden. Alles, was JSON lesen kann, kann
auch sie lesen.

![Die Felder und Kanäle einer Rundendatei, geschrieben aus einem synthetischen Forza-Datenstrom](../assets/img/lap-file.svg)

## Das Dokument {#the-document}

Ein JSON-Objekt. Kanäle sind als Spalten gespeichert: ein Array pro Kanal, alle gleich lang, ein Eintrag
pro Messpunkt.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Feld | Bedeutung |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | von welchem Spiel die Runde stammt; siehe die Liste unten |
| `track` | der Name der Strecke, Etappe oder Karte, wenn das Spiel ihn sendet |
| `layout` | nur Forza: welches Data-Out-Paketlayout dekodiert wurde |
| `car` | was das Spiel über das Auto sagt; frei formuliert |
| `lap` | die Rundennummer, ihre Zeit, wie das Spiel sie gezählt hat (oder die Spanne der Messpunkte), ob sie beendet wurde, ihre Länge |
| `meta` | wie die Zahlen zu lesen sind; siehe unten |
| `units` | die Einheit jedes vorhandenen Kanals, für einen Leser, der die Tabelle unten nicht kennt |
| `channels` | die Messpunkte |
| `unparsed` | nur Forza, wenn das Paket Bytes hat, denen kein Feld einen Namen gibt: `ranges` (ihre Byte-Bereiche `[Anfang, Ende)` im Paket) und `hex` (pro Messpunkt diese Bytes als Hex), damit die Datei allein das ganze Paket enthält |

`game` ist einer von `forza-horizon`, `forza-motorsport`, `forza` (Paketlayout nicht unterschieden),
`assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`,
`dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` sagt, was die Zahlen bedeuten, wo sich die Spiele unterscheiden:

- `slip`: was die Schlupfkanäle enthalten, wenn das Spiel welche sendet. `peak` (normiert, über 1
  verliert der Reifen die Haftung: Forza), `scaled` (ein physikalischer Schlupf, geteilt durch einen
  typischen Asphalt-Spitzenwert: die Assetto-Corsa-Spiele), `physical` (ein Bruchteil und Radiant),
  `index` (ein Gleitmaß von 0..1: Trackmania);
- `discipline`: `circuit` (Rundstrecke), `rally` oder `arcade`;
- `surface`: `tarmac` (Asphalt), `loose` (loser Untergrund), `snow`, `ice` oder `mixed`, wenn bekannt
  (die Rallye-Recorder übernehmen ihn aus `--surface`).

## Kanäle {#channels}

Ein Kanal, den ein Spiel nicht sendet, fehlt. Er wird nie mit Nullen gefüllt. Radbezogene Kanäle tragen
das Rad nach einem Punkt: `.FL`, `.FR`, `.RL`, `.RR`.

Positionen sind die Welt des Spiels in Metern, mit `y` nach oben. Ist die Welt eines Spiels Z-nach-oben,
dreht der Recorder sie auf Y-nach-oben. Sonst wird nichts verändert: Eine linkshändige Welt (Forza) bleibt
linkshändig.

| Kanal | Einheit | Bedeutung |
|---|---|---|
| `time` | s | seit dem ersten Messpunkt der Runde |
| `distance` | m | entlang des gefahrenen Weges seit dem ersten Messpunkt |
| `x`, `y`, `z` | m | Position; `y` ist die Höhe |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | Pedale und Hebel |
| `steer` | -1..1 | positiv nach rechts |
| `gear` | | wie das Spiel die Gänge zählt |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | Fahrzeugsystem |
| `yaw`, `pitch`, `roll` | rad | Richtung und Lage |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | Geschwindigkeit im Fahrzeugsystem: rechts, vorwärts, oben |
| `bodySlip` | rad | Driftwinkel, wenn das Spiel ihn sendet |
| `loose` | 0/1 | auf losem Untergrund (Trackmania) |
| `airborne` | 0/1 | kein Rad am Boden |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | wie das Spiel sie sendet |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | Hilfen greifen, Systeme eingeschaltet |
| `absLevel`, `tcLevel` | | Einstellungen der Hilfen |
| `brakeBias` | 0..1 | Anteil der Vorderachse |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | je Rad |
| `tirePressure` | psi | je Rad |
| `tireWear` | 0..1 | je Rad |
| `slipRatio`, `slipAngle`, `combinedSlip` | siehe `meta.slip` | je Rad |
| `slipIndex` | 0..1 | je Rad, Gleitmaß (Trackmania) |
| `camber` | rad | je Rad |
| `brakeTemp` | °C | je Rad |
| `padLife`, `discLife` | | je Rad |
| `suspensionM` | m | Federweg je Rad |
| `suspension` | 0..1 | Federweg je Rad, des in dieser Runde genutzten Bereichs |
| `wheelLoad` | N | je Rad |
| `wheelSpeed` | rad/s | Raddrehung je Rad |
| `wheelSurfaceSpeed` | m/s | Geschwindigkeit der Aufstandsfläche je Rad |
| `groundContact` | 0/1 | je Rad |
| `rumble`, `surfaceRumble` | | je Rad: auf einem Rumpelstreifen; das Rumpeln der Fahrbahn |
| `puddle` | | je Rad: Tiefe des stehenden Wassers |

Ein Recorder darf eigene Kanäle unter anderen Namen hinzufügen. Ein Leser behält, was er nicht kennt.

Keines der Rallyespiele sendet Reifenschlupf. Ein Leser kann ihn errechnen, aus der
Aufstandsflächen- oder Radoberflächengeschwindigkeit jedes Rades gegen die Geschwindigkeit des Autos,
`(Rad - Auto) / Auto`, oder aus der Drehung und einem Rollradius, der auf der Runde selbst gemessen
wird, wo nur die Drehung gesendet wird. Der Driftwinkel kommt aus der eigenen Geschwindigkeit des Autos
(`latVel`, `longVel`), wo sie gesendet wird, oder aus der Weltgeschwindigkeit, projiziert auf die
Achsen des Autos.

## Das CSV-Format {#the-csv-form}

Das Trackmania-Plugin schreibt stattdessen `heat3d-lap-csv`: eine erste Zeile mit `# ` und einem
JSON-Objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), eine Zeile mit den
Kanalnamen, dann eine Zeile pro Messpunkt. Die Kanalnamen sind dieselben wie oben.

## Was jeder Recorder tatsächlich schreibt {#what-each-recorder-actually-writes}

Das Format oben ist der Vertrag. Die Recorder füllen es leicht unterschiedlich aus. Ein Leser sollte
alle diese Varianten verkraften (geprüft am Code):

| Recorder | `track` | `layout` | `meta` | `units` | Kanäle über die Tabelle hinaus |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (die Streckennummer von Forza Motorsport 2023 steht in `lap.trackOrdinal`) | das erkannte Paketlayout | `slip: peak`, `discipline: circuit` | nur Einheiten vorhandener Kanäle | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, die Uhr des Spiels `timestampMs`, `raceTime`, `bestLap`, `lastLap`; die Geschwindigkeit im Fahrzeugsystem steht unter den einheitlichen Namen `latVel`, `vertVel`, `longVel`; `unparsed` neben den Kanälen |
| Assetto-Corsa-Spiele (`kunos.py`) | aus der statischen Seite, sonst `null` | fehlt | `slip: scaled`, `discipline: circuit` oder `rally` | eine feste Liste | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (wie gesendet), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rallyespiele (`rally.py` über `lapfile.py`) | `null` | fehlt | `discipline: rally`, `slip: null`, `surface` nur, wenn `--surface` angegeben war (sonst leitet der Viewer ihn ab) | nur Einheiten vorhandener Kanäle | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` für die Gleitkommazahlen ohne festen Namen; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` über `lapfile.py`) | `null` | fehlt | `discipline: circuit` | nur Einheiten vorhandener Kanäle | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-Plugin (CSV) | der Kartenname | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` ist der Fahrzeugblock von Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` für die Kunos-Spiele, wenn die statische Seite einen Namen nennt,
und sonst `{}`. `lap.metres` ist für Forza die Differenz des zurückgelegten Weges im Spiel und sonst die
summierte 3D-Strecke zwischen den Messpunkten. Werte werden beim Schreiben gerundet: `time` auf 4
Nachkommastellen, `distance` auf 3, andere Gleitkommazahlen auf 5. JSON wird kompakt geschrieben, ohne
Leerzeichen.

Jedes Paket und jede Seite, die der Recorder bekommen hat, nicht nur die der Runden, wird vollständig
neben den Rundendateien in `<stamp>_<game>.raw.parquet` aufbewahrt. Dazu kommt eine Selbstprüfung in
`<stamp>_<game>.summary.json` (der Abschnitt „Completeness“ in der README).

Ein Messpunkt, für den ein Kanal keinen Wert hat, weil er im Bild fehlt oder weil das Spiel keine endliche
Zahl gesendet hat, wird von jedem Recorder als `null` geschrieben (`lapfile.clean`). Der daraus
abgeleitete Federweg-Anteil ist ebenfalls `null`. `NaN` und `Infinity` werden nie geschrieben: Sie sind
kein JSON, und ein `JSON.parse` im Browser lehnt wegen einer davon die ganze Datei ab. Ein Leser muss
`null` im Array eines Kanals erwarten.

Die Forza-Dateien tragen `"game": "forza-horizon"`, `"forza-motorsport"` oder `"forza"`, je nach erkanntem
Layout. Der Viewer liest die `.tele.gz`-Dateien von FH Companion und erzeugt daraus Runden mit
`"game": "forza-horizon"` und `meta.slip = "peak"`. Dieser Leser steckt im Viewer, nicht hier.
iRacing-Runden (aus `.ibt` im Viewer gelesen) tragen `"game": "iracing"`. Das steht nicht in der Liste
der Recorder-Werte oben, weil kein Recorder es schreibt.

Wie `lap.number`, `lap.seconds` und `lap.complete` entschieden werden, steht unter
[Runden- und Etappenteilung](lap-splitting.md). Was der Viewer aus diesen Kanälen ableitet, steht unter
[Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md).
