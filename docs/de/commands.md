---
title: "Befehlsübersicht"
nav_order: 5
lang: "de"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Befehlsübersicht {#command-reference}

Alle Befehle laufen aus dem Ordner des Repositorys, mit der Umgebung des Projekts:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Befehl | Tut |
|---|---|
| [`route`](#route) | Zeichnet nur die Positionen einer Forza-Runde auf, damit die Karte in den Spieldateien gefunden werden kann |
| [`telemetry`](#telemetry) | Zeichnet jeden Kanal auf, eine Rundendatei pro Runde, für den Tab Rennanalyse |
| [`laps`](#laps) | Liest eine Rundenbibliothek von FH Companion und schreibt Route und Messwerte einer Strecke |
| [`reconstruct`](#reconstruct) | Berechnet eine Aufnahme offline und schreibt eine `.glb` |
| [`hud`](#hud) | Liest aus einer Aufnahme die eigenen Aktionen, Tode und die Minikartenspur des Spielers sowie den Killfeed |
| [`locate`](#locate) | Wo jedes Bild einer Aufnahme aufgenommen wurde, im Vergleich mit Renderings des Levels |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Das Scan-Fenster |
| [`python -m heat3d_update`](#updates) | Prüft auf ein Update und spielt es ein |
| [`python tools/export_onnx.py`](#the-model-converter) | Wandelt das Tiefenmodell in ONNX um |

Wird das Tool als `python -m heat3d_capture` gestartet, prüft es zuerst, ob es eine neuere
Version gibt (siehe [Updates](updates.md); `HEAT3D_NO_UPDATE=1` schaltet das ab). `--help` nach
jedem Befehl listet seine Optionen auf:

![heat3d_capture --help](../assets/img/cli-help.svg)

Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Hört auf Forza Data Out und speichert nur die Positionen des Autos, sonst nichts: kein Tiefenmodell,
keine GPU, keine Aufnahme. Code: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Option | Standard | Bedeutung |
|---|---|---|
| `-o`, `--out` | erforderlich | Ausgabepfad; seine Endung wird ersetzt, `-o lap` schreibt also `lap.npz` und `lap.json`. |
| `--port` | `5300` | Port, an den das Spiel sendet (auf 127.0.0.1 gebunden). |
| `--seconds` | `0` | Nach so vielen Sekunden anhalten; `0` läuft bis Strg+C. |

Eine Position wird nur behalten, solange das Spiel ein Rennen meldet (`isRaceOn`), das Auto
schneller als 0,5 m/s fährt und mindestens 0,5 m von der letzten behaltenen Position entfernt ist.
Sonst würde das Sitzen in einem Menü bei 60 Paketen pro Sekunde die Datei mit der Startlinie füllen.
Die Zeit jedes Messwerts ist die Rennzeit des Spiels, oder die Uhrzeit, wenn diese 0 ist. Das
Layout wird genauso erkannt wie bei `telemetry` (das Auto muss sich zuerst bewegen; siehe [Forza](telemetry-forza.md)).

Jede Sekunde gibt es aus: empfangene Pakete, behaltene Positionen und die aktuelle Position oder
`nothing on port 5300 yet - is Data Out on?`. Die Route wird **während der Fahrt gespeichert**: alle
2 Sekunden, sobald eine neue Position angekommen ist (der Abstand wächst auf das Zwanzigfache der
Dauer des letzten Speicherns, damit eine sehr lange Sitzung nie mehr als ein Zwanzigstel ihrer Zeit
mit Schreiben verbringt), und ein letztes Mal, wenn der Recorder aus irgendeinem Grund stoppt -
Strg+C, `--seconds` oder eine Ausnahme. Jedes Speichern schreibt zuerst `lap.npz.partial` / `lap.json.partial`
und verschiebt die Datei dann über die echte Datei, so sind die Dateien auf der Festplatte immer
vollständig; ein Absturz oder ein beendeter Prozess verliert höchstens die letzten Sekunden. Wurde
nichts behalten, zeigt es, wie Data Out eingeschaltet wird, und beendet sich mit Exitcode 1.

Ausgabe:

- `lap.npz` - NumPy-Arrays `positions` (n x 3, Meter), `times`, `speeds` (m/s);
- `lap.json` - lesbar ohne dieses Projekt:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Die Positionen sind die eigenen Weltkoordinaten des Spiels. Genau das macht sie zu einem Anknüpfungspunkt,
um denselben Boden in den Spieldateien wiederzufinden: Der Befehl `course` von
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) nimmt diese JSON-Datei und
exportiert die Strecke, über die die Runde führte.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Jede Option und jedes Spiel wird auf [Telemetrie-Recorder](telemetry.md) beschrieben.

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Liest die Rundenbibliothek, die FH Companion führt, und schreibt zwei Dateien für eine Strecke: eine
Route, die sagt, welches Stück Karte aus dem Spielarchiv ausgeschnitten wird, und eine Tabelle mit
jedem Messwert jeder Runde. Beide werden zusammen geschrieben, damit sie nicht auseinanderlaufen
können. Code: [`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Option | Standard | Bedeutung |
|---|---|---|
| `course` | keine | Streckenname, locker abgeglichen. Weglassen, um die Bibliothek aufzulisten. |
| `-o`, `--out` | der Streckenname in Kleinbuchstaben, Leerzeichen als `_` | Ausgabepfad; `.json` und `.csv` werden nebeneinander geschrieben. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Wo die Streckenordner liegen. |
| `--margin` | `80` | Meter, die um die Ausdehnung der Strecke in x und z in den `bounds` der Route ergänzt werden. |

### Auflisten {#listing}

Ohne Strecke gibt es die Anzahl der Streckenordner aus und für jeden die Anzahl der Rundendateien
(`*.json` überall darunter außer `course.json`) und den Streckennamen, dann
`Name one to write it out:  -o <file> <course>`.

### Eine Strecke finden {#finding-a-course}

Streckenordner heißen `<name> (course_<x>_<z>_to_<x>_<z>)` - Start und Ziel, gerundet. Eine Strecke
wird in dieser Reihenfolge gesucht: der exakte Ordnername; der Namensteil des Ordnernamens, ohne
Groß-/Kleinschreibung; ein eindeutiger Ordner, dessen Name den Text enthält. Mehrere Treffer sind
ein Fehler, der sie auflistet.

### Lesen {#reading-it}

- `course.json` im Ordner, wenn lesbar, liefert den Namen und Start und Ziel ungerundet (`Name`,
  `StartX`, `StartZ`, `FinishX`, `FinishZ`); sonst kommen sie aus dem Ordnernamen. Eine Strecke gilt
  als Rundkurs, wenn Start und Ziel weniger als 10 m auseinander liegen.
- Jede andere `*.json` unter dem Ordner ist eine Runde (Runden liegen mehrere Ordner tief - nach
  Klasse, Auto, Abstimmung, Tag - und die Suche ist einfach rekursiv). Dateien werden als UTF-8 mit
  Byte-Order-Mark gelesen. Eine nicht lesbare Runde wird übersprungen. Runden werden nach ihrer
  Aufnahmezeit sortiert.
- Pro Runde: `Lap.samples` (jeweils mit `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`) sowie die Fahrzeugklasse,
  die Ordnungszahl, der Leistungsindex, die Rundenzeit in Sekunden, die Länge, die Aufnahmezeit und der
  fliegende oder stehende Start.

Es gibt eine Zusammenfassung aus (Runden, Messwerte, beste Runde und ihre Klasse, die Ausdehnung in x/y/z).

### Ausgabe {#output}

**`<out>.json`** - dieselbe Routenform, die `route` schreibt, damit der Karten-Extraktor beides
annimmt: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (um `--margin` in x und z
erweitert) und `positions` der **schnellsten** Runde (eine Linie statt eines Verschmierens aller Runden).

**`<out>.csv`** - jeder Messwert jeder Runde, eine Zeile je Messwert:

| Spalte | Bedeutung |
|---|---|
| `course` | Streckenname |
| `lap` | eine Bezeichnung je Runde: Aufnahmedatum und -uhrzeit auf die Minute und die Rundenzeit |
| `car` | Fahrzeug-Ordnungszahl |
| `car_class` | Buchstabe der Leistungsklasse |
| `pi` | Leistungsindex |
| `lap_seconds` | Zeit der Runde |
| `speed_kmh` | Geschwindigkeit in km/h |
| `x`, `y`, `z` | Weltposition, Meter, 3 Nachkommastellen |
| `speed_ms` | Geschwindigkeit, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | so, wie FH Companion sie aufzeichnet |
| `metres` | Strecke entlang der Runde, 3 Nachkommastellen |
| `elapsed` | Sekunden seit dem eigenen Start der Runde, 3 Nachkommastellen |

Andere Werte als Positionen werden mit 4 signifikanten Stellen geschrieben; Positionen bekommen feste
Nachkommastellen, weil 4 signifikante Stellen eine Strecke auf ein Ein-Meter-Raster zwängen würden.
Die Spaltennamen sind so gewählt, dass der Viewer die Datei ohne Hinweis zuordnet: `lap` wird zur
Sitzung (zwei Runden desselben Autos werden nie verbunden), `car` zu dem, was sich bewegt,
`car_class` zur Gruppe für die Farbe, `elapsed` zur Zeitachse (jede Runde startet bei ihrem eigenen Start).

Zum Schluss gibt es einen Hinweis aus, wie die Karte mit GameFiles aus dem Spiel ausgeschnitten wird,
mit der Routendatei oder einem eigenen Kasten.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Berechnet eine Aufnahme offline, wobei der Kamerapfad auf einmal von VGGT gelöst wird. Langsam:
Minuten pro Fenster auf einer Desktop-GPU. Braucht PyTorch, Hugging Face `transformers` und das Paket
`vggt`, die der Scanner nicht braucht: Sie stehen in `requirements-offline.txt`, und der Befehl prüft
nach der Lizenzzeile auf sie und bietet an, fehlende zu installieren (Exitcode 1, wenn abgelehnt).
Vollständige Beschreibung: [Offline-Rekonstruktion](reconstruction-offline.md).

| Option | Standard | Bedeutung |
|---|---|---|
| `video` | erforderlich | Die Aufnahme. Exitcode 2, wenn sie nicht existiert. |
| `-o`, `--out` | erforderlich | Die zu schreibende `.glb`. |
| `--solve-budget` | `260` | Höchstzahl der Bilder, die an den Löser gegeben werden. Sie werden nach dem Weg verteilt, den das Bild zurücklegt, nicht nach der Uhr. Mehr ist genauer und viel langsamer. Mehr als 400 geplante Bilder werden abgelehnt. |
| `--fuse-interval` | `0.4` | Sekunden zwischen Bildern, die zu Geometrie verschmolzen werden. |
| `--model` | `vggt-1b` | Mit welchen VGGT-Gewichten gelöst wird: `vggt-1b` (`facebook/VGGT-1B`, nicht kommerziell) oder `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, gesperrt; Zugang muss von Meta gewährt werden). Die zuerst ausgegebene Lizenzzeile gehört zu diesem Modell. |

Zuerst gibt es die Lizenzzeile des Modells aus, dann jede Stufe (`masking`, `planning`, `solving`,
`fusing`, `exporting`) mit verstrichenen Sekunden und Fortschritt, und am Ende eine Zusammenfassung:
gelöste Kameras, Schließfehler, schlimmste Naht, Hinweise und die geschriebene Datei. Der Exitcode ist
nur dann 0, wenn eine Datei geschrieben wurde.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Liest das HUD des Spiels aus der eigenen Aufnahme des Spielers, nach dem Match: die eigenen Aktionen
des Spielers aus dem Punkte-Popup, Tode und Wiederbelebungen aus den Bildschirmen für Ausgeschaltet
und Einsatz, die Minikartenspur und den Killfeed. Schreibt `<out>.parquet` (Spur und Ereignisse, eine
3DHeat-Tabelle), `<out>.events.jsonl`, `<out>.summary.json` sowie `<out>.map.png` + `.map.json` (das
Minikarten-Mosaik und seine Anker für das Kartenbild des Viewers). Battlefield 6 (`bf6`) ist bisher
das einzige Profil.

Braucht **ffmpeg und ffprobe** im PATH (`winget install Gyan.FFmpeg`, dann ein neues Terminal).

| Option | Standard | Bedeutung |
|---|---|---|
| `video` | erforderlich | Die Aufnahme. |
| `-o`, `--out` | der Name des Videos | Ausgabepfad ohne Endung. |
| `--game` | `bf6` | Wessen HUD gelesen wird. |
| `--player` | geraten | Der Name des Spielers, so wie der Killfeed ihn zeigt, locker abgeglichen. |
| `--fps` | `5` | Minikarten-Messwerte pro Sekunde. |
| `--start`, `--seconds` | ganzes Video | Der Teil der Aufnahme, der gelesen wird. |
| `--metres-per-pixel` | keiner | Der Maßstab der Minikarte, wenn bekannt; ohne ihn sind Positionen in Minikarten-Pixeln. |
| `--cpu` | aus | Auf der CPU dekodieren, auch wenn eine NVIDIA-Karte vorhanden ist. |

Vollständige Beschreibung: [HUD aus einer Aufnahme lesen](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` rendert ein Level von jedem Ort, an dem ein Spieler stehen kann, und indiziert die Renderings;
`frames` ordnet jedes abgetastete Bild einer Aufnahme dagegen ein, anhand des Bildes, mit der
Minikartenspur des Befehls `hud` als Ersatz; `eval` vergleicht ein Ergebnis mit bekannten
Kameraposen; `train` trainiert ein Ortsmodell pro Karte auf Renderings des Levels (und auf Bildern,
die ein Lauf schon eingeordnet hat), für `build --head`; `refmap` legt die eigene Karte des Spiels
(ihren Einsatzbildschirm) auf das Level, und `minimap` liest die Minikarte einer Aufnahme dagegen,
Bild für Bild - die Vorgabe, die `frames --minimap` nehmen kann. Braucht PyTorch und
`requirements-locate.txt`. **Experimentell:** Auf echten Aufnahmen werden bisher nur wenige Bilder
eingeordnet. Alle Optionen, Ausgaben und das Verfahren:
[Bilder in einem Level verorten](locate.md); die vollständige Optionsliste: [Befehlsübersicht](../cli-reference.md).

<a id="the-scan-window"></a>

## Das Scan-Fenster {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

oder einen Doppelklick auf `scan.bat`. Keine Optionen. Siehe [Das Scan-Fenster](reconstruction-scan-ui.md).

## Updates {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Siehe [Updates](updates.md).

<a id="the-model-converter"></a>

## Der Modellkonverter {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Wandelt einen Depth-Anything-V2-Checkpoint in die ONNX-Datei um, die der Scanner ausführt. Braucht PyTorch,
`transformers` und `onnxscript`. Siehe [Tiefe](reconstruction-depth.md#building-the-model).
