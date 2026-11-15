---
title: Rallyespiele
nav_order: 3
lang: de
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # or dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Code: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tests: `tests/test_rally.py`, mit Paketen, die aus den dokumentierten Layouts gebaut wurden. **Noch nicht gegen die echten Spiele gelaufen.**

Alle senden UDP, das das Spiel über seine eigenen Einstellungsdateien einschaltet. Der Recorder lauscht auf allen Schnittstellen (`0.0.0.0`) am
Standardport des Spiels, außer `--port` gibt einen anderen an: **20777** für `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** für `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Einschalten {#switching-it-on}

Das Spiel liest `Documents\My Games\WRC\telemetry\config.json`. Das Standard-Struct `wrc` muss sein Paket `session_update` zu diesem PC hin eingeschaltet haben:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<Pfad zu config.json>"
```

`--configure` (Funktion `configure_wrc`):

- liest das JSON, findet `udp.packets` und den Eintrag mit `"structure": "wrc"` und `"packet": "session_update"`;
- ist er bereits auf `127.0.0.1` oder `localhost` am genutzten Port eingeschaltet, gibt er `already on` aus und ändert nichts;
- sonst setzt er `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` und behält das `frequencyHz` des Eintrags (oder `-1`, wenn keines da ist). Fehlt der Eintrag, hängt er einen an;
- schreibt den ursprünglichen Text nach `config.json.bak` daneben und dann die neue Datei (mit 4 Leerzeichen eingerückt).

Starte das Spiel nach einer Änderung der Datei neu, falls es sie nicht übernimmt (nicht geprüft).

### Was es sendet {#what-it-sends}

Das Standard-Struct `wrc` ist 237 Bytes lang, Little-Endian, ohne Kopf: Weltposition, Geschwindigkeit und Beschleunigung (X links, Y oben, Z vorwärts),
die Einheitsvektoren links, vorn und oben des Autos, je Rad (hinten links, hinten rechts, vorn links, vorn rechts) die Höhe der Nabe und ihre
vertikale Geschwindigkeit sowie die Vorwärtsgeschwindigkeit der Aufstandsfläche, Bremstemperaturen, Pedale nach Hilfen, Lenkung (-1 links, +1 rechts),
Handbremse, Drehzahl, Gang, und die Etappenuhr, Distanz und Länge. Ein Paket unter 237 Bytes wird ignoriert und einmal gemeldet.

| Kanal | Aus |
|---|---|
| `x`, `y`, `z` | Weltposition |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | Weltgeschwindigkeit, projiziert auf vorn, auf minus links (also positiv nach rechts), auf oben |
| `longAcc`, `latAcc`, `vertAcc` | Weltbeschleunigung, gleich projiziert |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | wie gesendet |
| `gear` | `gear_index`; -1, wenn er dem Rückwärtsindex gleicht, 0, wenn dem Leerlaufindex |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | Position der Nabe |
| `wheelSurfaceSpeed.*` | Vorwärtsgeschwindigkeit der Aufstandsfläche |
| `brakeTemp.*` | Bremstemperatur |

Prüfung: Ist `speed` über 10 und weicht die Länge der Weltgeschwindigkeit um mehr als 20 % davon ab, meldet der Recorder einmal, dass das Layout
vielleicht nicht das Standard-Struct `wrc` ist.

Eine Etappe ist **fertig**, wenn die Etappenlänge positiv ist und die Distanz die Länge minus 0,5 m erreicht hat. Die Uhr für das Teilen und für `time`
ist `stage_time`.

Quellen: EAs UDP Telemetry Guide v1.3; die Kanalliste, die das Spiel nach `readme/channels.json` schreibt; Offsets, wie sie nobonobo/obs-codemasters-telemetry
und SpaceMonkey dekodieren. Der Standardport des Spiels ist nicht dokumentiert; der Recorder nutzt 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Einschalten {#switching-it-on-1}

Bearbeite `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally und DiRT 4 nutzen ebenfalls eine
`hardware_settings_config.xml`; ihr genauer Ordner dafür ist hier nicht geprüft), sodass das Element `udp` so lautet:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` sorgt dafür, dass Positionen, Räder und die Etappenlänge im Paket stehen. Der Recorder bearbeitet diese Datei nicht.

### Was es sendet {#what-it-sends-1}

66 Little-Endian-Gleitkommazahlen (DiRT Rally: 64). Pakete mit weniger als 64 Gleitkommazahlen werden ignoriert, und ein Paket mit 64 wird mit Nullen aufgefüllt.
Die genutzten Indizes:

| Index | Feld | Kanal |
|---|---|---|
| 1 | Zeit der Etappe bzw. Runde | die Uhr für das Teilen und `time` |
| 2 | Rundendistanz | `stageDistance` |
| 4-6 | Weltposition | `x`, `y`, `z` |
| 7 | Geschwindigkeit | `speed` |
| 8-10 | Weltgeschwindigkeit | `longVel` (auf vorn), `latVel` (auf den Seitenvektor) |
| 11-13 | Seitenvektor | |
| 14-16 | Vorwärtsvektor | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | Federposition hinten links, hinten rechts, vorn links, vorn rechts | `suspensionM.*` |
| 25-28 | Geschwindigkeit der Aufstandsfläche hinten links, hinten rechts, vorn links, vorn rechts | `wheelSurfaceSpeed.*` |
| 29-33 | Gas, Lenkung, Bremse, Kupplung, Gang | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 oder mehr heißt Rückwärts, geschrieben als -1) |
| 34, 35 | Quer- und Längs-g | `latAcc`, `longAcc` (mal 9,80665) |
| 37 | Drehzahl / 10 | `rpm` (mal 10) |
| 51-54 | Bremstemperaturen | `brakeTemp.*` |
| 59, 60, 61, 62 | absolvierte Runden, Runden insgesamt, Streckenlänge, letzte Rundenzeit | Teilen |

Es gibt **keinen Handbremskanal**. Die Richtung des Seitenvektors ist in beiden Richtungen dokumentiert, deshalb ist das Vorzeichen von `latVel` nicht
verlässlich (der Viewer liest die Größe des Driftwinkels).

Eine Etappe ist **fertig**, wenn die Zahl der absolvierten Runden über ihren Wert zu Beginn der Etappe steigt (bei einem Rallycross-Rennen bei jeder
Runde), oder, bei einer Veranstaltung mit einer einzigen Runde, wenn die Rundendistanz 99,9 % der Streckenlänge erreicht. Die Zeit der Etappe ist die letzte
Rundenzeit des Spiels, wenn sie positiv ist. Prüfung: Geschwindigkeit gegen Weltgeschwindigkeit wie bei EA WRC, mit der Meldung „is extradata set to 3?“.

Quellen: Codemasters' UDP-Dokument zu DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Einschalten {#switching-it-on-2}

In `RichardBurnsRally.ini`, Abschnitt `[NGP]`: `udpTelemetry=1` und der Endpunkt (127.0.0.1, Port 6776, außer du übergibst mit `--port` einen anderen).
Der Recorder bearbeitet diese Datei nicht.

### Was es sendet {#what-it-sends-2}

664 Bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): Etappenuhr und Distanz bis zum Ziel, Pedale, Lenkung, Gang, Weltposition, Lage, die
eigenen Geschwindigkeiten des Autos (Surge vorwärts, Sway seitlich, Heave vertikal), Beschleunigungen, Drehzahl, und vier 128-Byte-Radblöcke (LF, RF, LB, RB) mit
Federweg und Federkraft. Keine Radgeschwindigkeiten.

| Kanal | Aus |
|---|---|
| `x`, `y`, `z` | Position, Achsen wie gesendet, dann umsortiert (unten) |
| `longVel`, `latVel`, `vertVel` | Surge, Sway, Heave |
| `longAcc`, `latAcc` | Beschleunigung x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | wie gesendet |
| `gear` | `gear - 1` (0 Rückwärts, 1 Leerlauf, 2 erster Gang) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | Federeinfederung |
| `wheelLoad.*` | Federkraft |
| `speed` | **aus den Positionen errechnet** über ±2 Messpunkte, nicht aus dem Paket übernommen |

Die Positionsachsen, Lageeinheiten und Geschwindigkeitseinheit von RBR sind nicht dokumentiert. Deshalb wird beim Schreiben einer Etappe die Achse, entlang
der sich die Etappe am wenigsten ändert, als oben genommen und nach `y` getauscht (`orient_up`, braucht mindestens 10 Messpunkte). Die Geschwindigkeit wird aus
den Positionen neu berechnet (`speed_from_positions`). Die Lage wird dekodiert, aber nicht geschrieben. RBR-Dateien haben deshalb kein `yaw`.

Eine Etappe ist **fertig**, wenn die Rennuhr läuft und die Entfernung zum Ziel null erreicht hat. Die Uhr ist `race_time`.

Quellen: NGPs `rbr.telemetry.data.TelemetryData.h` über mika-n/RBRUDPTelemetryLogger und groybe/rbr-udp-telem.

## Etappen {#stages}

Alle fünf nutzen `StageSplitter` auf der Etappenuhr des Spiels. Eine Etappe öffnet sich, wenn die Uhr startet, und schließt sich vollständig, wenn das Spiel
sagt, dass das Auto fertig ist. Eine Uhr, die zurückgeht (ein Neustart oder die nächste Etappe), verwirft die offene Etappe. Sie wird als Datei `_partial`
behalten, wenn sie mehr als 10 Messpunkte und mindestens 300 m hat. Fertige Etappen unter 300 m werden nicht geschrieben. Details:
[Runden- und Etappenteilung](lap-splitting.md).

## Die Rundendatei {#the-lap-file}

`game` ist `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` oder `richard-burns-rally`. `meta` ist `{"discipline": "rally", "slip": null}`, plus
`"surface": "<Wert>"`, wenn `--surface` angegeben war. `slip` ist null, weil keines dieser Spiele Reifenschlupf sendet. Die Aufstandsflächen-Geschwindigkeit jedes
Rades (EA WRC, DiRT) steht stattdessen in der Datei. Der Viewer leitet daraus Schlupf und Driftwinkel ab, zusammen mit den Achsen des Autos; siehe
[Schlupf, Drift und abgeleitete Kanäle](slip-and-drift.md). Die Kanäle `suspension.*` (0..1 des genutzten Federwegs) werden aus `suspensionM.*` ergänzt.

Ohne `--surface` trägt die Datei bewusst gar keinen Untergrund. Ein hier geschriebener Standardwert würde die eigene Ableitung des Viewers überschreiben.
Der Viewer nimmt den Untergrund dann aus dem Namen der Etappe oder der Veranstaltung (Asphaltrallyes, Winterrallyes, die Monte-Carlo-Rallye als gemischt), sonst daraus,
wie das Auto auf ihr gefahren wurde (hartes Kurvenfahren bei kleinen Driftwinkeln ist Asphalt), und lose, wenn nichts darauf hinweist, was bei einer Rallye-Etappe
am häufigsten der Fall ist. Gib `--surface` an, wenn du es besser weißt.
