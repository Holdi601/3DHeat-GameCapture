---
title: Schlupf, Drift und abgeleitete Kanäle
nav_order: 8
lang: "de"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Schlupf, Drift und abgeleitete Kanäle {#slip-drift-and-derived-channels}

Die Analyse der Fahrzeugkontrolle im Tab Rennanalyse des Viewers braucht von jedem Spiel dieselben wenigen Größen: wie stark
jeder Reifen rutscht, wie weit das Auto von seiner Fahrtrichtung abweicht (der Driftwinkel), ob es in der Luft ist, ob es auf losem
Untergrund fährt. Spiele senden diese in sehr unterschiedlicher Form oder gar nicht. Die Recorder hier schreiben, was jedes Spiel sendet,
unter einheitlichen Namen, dazu einen Hinweis `meta.slip`, was die Schlupfwerte bedeuten. Der Viewer leitet dann das Fehlende ab, einmal,
wenn er eine Runde lädt. **Der eigene Wert eines Spiels gewinnt immer gegen einen abgeleiteten.**

## Was die Recorder schreiben {#what-the-recorders-write}

| Spiel | Schlupfkanäle | `meta.slip` | Eingaben für den Driftwinkel |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` je Rad, wie gesendet | `peak` (vom Recorder geschrieben; der `.tele.gz`-Leser des Viewers setzt dasselbe) | `latVel`, `longVel` aus der Geschwindigkeit im Fahrzeugsystem |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, dazu `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` aus der Geschwindigkeit im Fahrzeugsystem |
| EA SPORTS WRC, DiRT-Spiele | keine; stattdessen `wheelSurfaceSpeed` je Rad | `null` | `latVel`, `longVel` = Weltgeschwindigkeit, projiziert auf die Achsen des Autos |
| Richard Burns Rally | keine; auch keine Radgeschwindigkeiten | keiner | `latVel`, `longVel` = die eigene Querbewegung (Sway) und Längsbewegung (Surge) des Autos |
| BeamNG.drive | keine; `wheelSurfaceSpeed` und `wheelSpeed` je Rad | keiner | `latVel`, `longVel` = Weltgeschwindigkeit, projiziert auf die Achsen des Autos |
| Trackmania | `slipIndex` je Rad (ein Gleitmaß von 0..1) | `index` | `latVel` (Seitengeschwindigkeit), `longVel` (Vorwärtsgeschwindigkeit) |
| iRacing | keine (nicht protokolliert) | keiner | `yaw` und der Weg, `yawRate` |

Die Werte von `meta.slip` sind in [Die Datei heat3d-lap](lap-format.md) definiert: `peak` (normiert, sodass über 1 der Reifen die
Haftung verliert), `scaled` (ein physikalischer Schlupf, geteilt durch einen typischen Asphalt-Spitzenwert), `physical` (ein Bruchteil und
Radiant), `index` (ein Gleitmaß von 0..1).

### Warum der Schlupf der Kunos-Spiele skaliert wird {#why-kunos-slip-is-scaled}

Forzas Schlupf ist so normiert, dass 1 die Grenze des Grips ist. Womit er normiert wird, ist nicht dokumentiert. Kunos sendet das
physikalische Schlupfverhältnis (ein Bruchteil) und den Schlupfwinkel (Radiant). Teilt man durch einen typischen Asphalt-Spitzenwert, also
0,12 für das Verhältnis und 0,14 rad (etwa 8 Grad) für den Winkel, wird „über 1 heißt Rutschen“ für beide Familien näherungsweise wahr. So
bleibt eine einzige Lesart für die Anzeigen des Viewers. Das ist eine Näherung: Echte Spitzenwerte hängen von Reifen und Untergrund ab.
Deshalb werden die Rohwerte neben den skalierten behalten, und deshalb misst der Viewer aus den Runden selbst, wo der Grip jedes Autos
tatsächlich nachlässt.

## Was der Viewer ableitet (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Diese Schritte laufen im Viewer (`src/race/derive.ts` im 3DHeat-Viewer), nicht in diesem Repository.

### Driftwinkel, `bodySlip` {#drift-angle-bodyslip}

- **Aus der Geschwindigkeit im Fahrzeugsystem**, wenn `latVel` und `longVel` vorhanden sind:
  `atan2(latVel, |longVel|)`, und 0 unter 3 m/s (ein seitlich stehendes Auto driftet nicht).
  Sein Vorzeichen folgt der Quergeschwindigkeit des Spiels, deren Richtung bei manchen Spielen in beiden Richtungen dokumentiert ist.
  Man liest die Größe.
- **Sonst aus der Richtung gegen den Weg**: Die Fahrtrichtung wird aus Positionen etwa 2 m vor und hinter jedem Messpunkt entnommen
  (`atan2(dx, dz)`). Das `yaw` des Spiels wird daran angepasst, mit Vorzeichen und Versatz (jedes Spiel hat seinen eigenen Nullpunkt und
  Drehsinn), anhand von Messpunkten über 10 m/s. Vertraut wird ihm nur, wenn er danach gut passt (zirkuläre Streuung höchstens 0,05,
  mindestens 20 Messpunkte). Der Driftwinkel ist die Differenz, 0 unter 3 m/s.

### Schlupfverhältnis aus den Rädern {#slip-ratio-from-the-wheels}

Hat eine Runde kein `slipRatio.*`, aber Radgeschwindigkeiten, ist das Schlupfverhältnis
`(Rad - Auto) / Auto` je Rad, aus:

- `wheelSurfaceSpeed.*` (Geschwindigkeit der Aufstandsfläche, m/s) direkt, wenn gesendet (EA WRC, DiRT, BeamNG);
- sonst `wheelSpeed.*` (Drehung, rad/s) mal einem **Rollradius, der auf der Runde gemessen wird**: der Median von `speed / |omega|`
  über Messpunkte, bei denen das Auto geradeaus rollt (über 10 m/s, nicht in der Luft, Gas unter 0,3, Bremse unter 0,05, Längsbeschleunigung
  unter 3 m/s²). Mit weniger als 20 solcher Messpunkte gilt jeder Messpunkt über 10 m/s. Ein Radius außerhalb von 0,1-1 m wird verworfen.

Nur wenn alle vier Räder abgeleitet werden können, wird `meta.slip` der Runde zu `physical`. Unter 3 m/s ist der Schlupf 0.

### In der Luft {#airborne}

`airborne` ist 1, wenn jedes Rad vom Boden weg ist. Beurteilt wird mit dem ersten der folgenden Kanäle, den die Runde für alle vier Räder hat:

1. `groundContact.*` (BeamNG): kein Rad über 0,5;
2. `wheelLoad.*` (AC-Spiele, RBR, BeamNG): kein Rad über 5 % seiner eigenen Median-Last;
3. `suspension.*` (0..1 des Federwegs): kein Rad über 0,02, also alle ganz ausgefahren.

Ein einzelner, isolierter Luft-Messpunkt wird gelöscht. Trackmania schreibt `airborne` selbst.

### Loser Untergrund {#loose-ground}

Hat eine Runde `surfaceRumble.*` (Forza), ist `loose` 1, wo mindestens zwei Räder mindestens eine drittel Sekunde Rumpeln melden. Lücken
von weniger als einer Sekunde werden überbrückt (ein glatter Abschnitt auf einer Schotterstraße ist trotzdem die Schotterstraße).
Trackmania schreibt `loose` selbst, aus den Materialien des Untergrunds unter den Rädern.

### Gierrate {#yaw-rate}

Hat eine Runde `yaw`, aber kein `yawRate`, ist sie die Änderung des Gierwinkels über die Nachbarmesspunkte.

## Was die Recorder selbst ableiten {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): Jeder Recorder außer Forza (das es sendet) schreibt es aus `suspensionM.*` als Position innerhalb des Bereichs,
  den die Runde genutzt hat (Minimum bis Maximum). Es dient den Federungsbalken des Autos und dem Erkennen eines Rades, das in der Luft hängt.
  Es ist kein absoluter Federwegsanteil.
- **`steer`** bei den Kunos-Spielen, pro Runde skaliert (siehe [Assetto-Corsa-Spiele](telemetry-assetto-corsa.md)).
- **Beschleunigungen** bei BeamNG, aus der Änderung der Weltgeschwindigkeit ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** und die Hochachse bei Richard Burns Rally, aus den Positionen ([Rallyespiele](telemetry-rally.md)).

## Händigkeit {#handedness}

Ist die Welt eines Spiels linkshändig, wie die von Forza, kommt eine Strecke in einem rechtshändigen Viewer gespiegelt heraus. Die
eigene Lenkung und Federung der Runden verrät das. Die Recorder ändern die Händigkeit nicht: Eine Z-oben-Welt (BeamNG) wird durch eine
Drehung auf Y-oben gebracht, was die Händigkeit erhält. Alles andere wird geschrieben, wie es gesendet wurde.
