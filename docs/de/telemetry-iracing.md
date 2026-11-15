---
title: iRacing
nav_order: 6
lang: "de"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing braucht **keinen Recorder**. Die Simulation schreibt eigene Telemetriedateien, `.ibt`, wenn die Telemetrie-Protokollierung eingeschaltet ist (Alt+L im Auto): die ganze Sitzung mit 60 Hz, jeden Kanal, den die Simulation freigibt, mit der YAML-Beschreibung der Sitzung daneben. Ziehe die `.ibt`-Datei auf den Tab **Rennanalyse** des Viewers.

Der Leser steckt im Viewer, nicht in diesem Repository (`src/race/ibt.ts` im 3DHeat-Viewer). Er ist mit einer synthetischen Datei getestet; er wird hier dokumentiert, weil er die iRacing-Hälfte derselben Geschichte von der Rundenaufnahme ist.

## Was die Datei enthält und wie sie gelesen wird {#what-the-file-holds-and-how-it-is-read}

Die Datei ist das dokumentierte Speicherlayout der Simulation, auf die Festplatte geschrieben:

| Teil | Größe | Enthält |
|---|---|---|
| Kopf | 112 Byte | Version, Tickrate, wo YAML und Variablentabelle liegen, die Länge einer Sample-Zeile, wo die Zeilen beginnen |
| Datenträger-Unterkopf | 32 Byte | Startdatum und -uhrzeit, Rundenzahl, Zeilenzahl |
| Variablentabelle | 144 Byte je Kanal | Typ, Versatz in der Zeile, Anzahl, Name, Beschreibung, Einheit |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Zeilen | eine pro Tick | |

Eine Datei wird abgelehnt, wenn sie kürzer als 144 Byte ist, wenn ihr Kopf unplausibel ist (keine Variablen, eine Variablentabelle außerhalb der Datei, eine Zeilenlänge von null), wenn ihr eines von `SessionTime`, `Lap`, `Lat`, `Lon` fehlt, oder wenn kein Sample eine Positionsbestimmung hat.

## Position {#position}

iRacing meldet Breite, Länge und Höhe, nicht eine Position im eigenen Bezugssystem der Strecke. Die Positionen werden in Metern auf einer Ebene angelegt, die das erste Sample mit Positionsbestimmung berührt (Erdradius 6.371.008,8 m): `x` nach Osten, `z` nach Süden, `y` die Höhe - so dass von oben, mit der standardmäßigen Blickrichtung der Viewer-Kamera, Norden oben auf dem Bildschirm liegt.

## Runden {#laps}

Die Sitzung wird am Zähler `Lap` der Simulation aufgeteilt. Eine Runde bleibt nur, wenn sie mehr als 60 Samples hat, unter 5 % der Rundenstrecke (`LapDistPct`) beginnt und über 95 % endet - also Runden, die von Linie zu Linie gefahren werden. Qualifiziert sich keine Runde, wird die Datei mit einer Meldung abgelehnt, die die Streckenlänge aus der YAML nennt. `distance` ist `LapDist`, auf den Rundenstart bezogen, oder die gefahrene Strecke aus den Positionen, wenn `LapDist` fehlt; `time` ist `SessionTime` ab dem Rundenstart.

## Kanäle {#channels}

| iRacing | Kanal | Umrechnung |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | keine |
| `Clutch` | `clutch` | `1 - value` (iRacing zählt die Kupplung als eingerückt; der Kanal ist das Pedal) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (Radiant, gegen den Uhrzeigersinn positiv, auf -1..1 mit rechts positiv; pi, wenn das Maximum fehlt) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | keine |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | keine |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | Fahrhilfen-Einstellungen |
| `dcBrakeBias` | `brakeBias` | durch 100 geteilt, wenn über 1,5 (bei manchen Autos ein Prozentwert) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | Temperatur des Reifenkörpers in der Mitte |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa mal 0,145038, in psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Jeder andere Kanal mit einem Wert pro Sample (und nicht nur einem Byte) wird unter seinem eigenen Namen durchgereicht, wobei ein Radpräfix (`LF`, `RF`, `LR`, `RR`) zu einem Suffix wird (`.FL`, `.FR`, `.RL`, `.RR`), damit die Diagramme des Viewers ihn anbieten, ohne dass ihn jemand beschreiben muss.

Das Auto kommt aus `DriverInfo`: Der Eintrag, dessen `CarIdx` zu `DriverCarIdx` passt, liefert `CarScreenName`, `CarID` und `CarClassShortName`. Die Strecke ist `TrackDisplayName` (oder `TrackName`).

## Was iRacing nicht liefert {#what-iracing-does-not-give}

Kein Reifenschlupf wird protokolliert, daher gibt es keine Schlupf-Kanäle. Der Driftwinkel wird aus der Gierrate gegen den Pfad abgeleitet (siehe [Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md)). Streckenmodelle liegen in einem geschützten Format vor und sind kein Ziel für Dateiextraktion (siehe [Spiele](games.md)).
