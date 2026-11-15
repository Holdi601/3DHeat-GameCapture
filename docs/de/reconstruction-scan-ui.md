---
title: "Das Scan-Fenster"
nav_order: 1
lang: "de"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Das Scan-Fenster {#the-scan-window}

```bash
python -m heat3d_capture.ui        # oder Doppelklick auf scan.bat
```

Code: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Das Fenster ist eine dünne Ansicht über `scan/session.py` und `scan/reconstruct.py`; es enthält keine
Scan- oder Geometrielogik.

## Start {#starting-up}

1. **Update-Prüfung** - siehe [Updates](updates.md).
2. **Abhängigkeitsprüfung** - jedes Paket, das der Scanner braucht, wird geprüft, bevor etwas importiert wird;
   fehlende werden mit Zweck und Downloadgröße aufgelistet und erst nach „Herunterladen und installieren“
   installiert. Abbrechen beendet das Programm, ohne etwas zu ändern. Siehe [Laufzeit und Abhängigkeiten](runtime.md#first-run-preflight).
3. **Fenster** - „3DHeat — Level-Scanner“, 1420 x 900, Qt-Fusion-Stil.
4. **Hardware-Prüfung** - das beste Inferenz-Backend wird gewählt, das Tiefenmodell geladen und sein Durchsatz
   an 6 Bildern gemessen; das Urteilsfeld oben links sagt, wie der Scan voraussichtlich wird (siehe [Laufzeit](runtime.md#what-to-expect-from-this-machine)).
5. **Globale Tastenkürzel** werden zuletzt registriert.

### Wenn es noch kein Tiefenmodell gibt {#when-there-is-no-depth-model-yet}

Enthält `models/` keine `depth-*.onnx`, lautet das Urteil **„Noch eine Einrichtung nötig.“**, Start ist
deaktiviert, und eine Schaltfläche **Tiefenmodell einrichten** erscheint. Sie:

- prüft auf PyTorch, `transformers` und `onnxscript` (zusammen etwa 945 MB) und fragt, bevor sie installiert;
- führt `tools/export_onnx.py --size small` als eigenen Prozess aus (damit PyTorch nie im Speicher des Scanners
  bleibt), mit einem Zeitlimit von 30 Minuten. Das Fenster reagiert nicht, während es läuft;
- prüft bei Erfolg die Hardware erneut; bei Fehlschlag zeigt es die letzten 600 Zeichen der Ausgabe des Konverters.

Liegen mehrere Modelle vor, wird **nach Lizenz, nicht nach Dateiname** gewählt: `depth-small-*`
(Apache-2.0, kommerzielle Nutzung erlaubt) immer dann, wenn es eines gibt, danach Base, danach Large (beide
nicht kommerziell). Urteilsfeld und die graue Zeile unter den Schaltflächen nennen die verwendete Datei, ihre
Lizenz und alle anderen vorhandenen, aber nicht verwendeten Modelldateien - zum Beispiel `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Um mit Base zu scannen, verschiebe die Small-Datei aus `models/`.

## Linke Spalte: Einstellungen {#left-column-settings}

| Gruppe | Steuerelement | Standard | Bereich / Werte | Was es tut |
|---|---|---|---|---|
| (oben) | Urteilsfeld | „Checking your graphics card…“ | farbig grün, gelb oder rot je Stufe | Überschrift, `<device> via <API> — N views per second`, ein Hinweis und `Depth model: <file> (<licence>)` |
| Was scannen | Quelle | Ganzer Bildschirm | Ganzer Bildschirm, Ein Fenster, Eine Videodatei | Woher die Bilder kommen |
| | Welche | `1` | Monitornummer / Fenstertitel / Pfad zu einem Video | `monitor:<n>`, `window:<title>` oder ein Dateipfad |
| | Datei wählen… | bei Video sichtbar | `*.mp4 *.mkv *.avi *.mov` | Trägt den Pfad ein |
| Wie sorgfältig | Voreinstellung | Ausgewogen | Entwurf, Ausgewogen, Detailliert | Auflösung der Aufnahme und wie wählerisch die Schlüsselbilder sind (unten); eine einzeilige Zusammenfassung steht darunter |
| | Sichtfeld im Spiel | 90° | 30-140° | Das **horizontale** Sichtfeld des Spiels. Zu eng, und das Level wird tiefer rekonstruiert, als es ist; zu weit, und es wird flacher. Rennspiele liegen eher bei 65° |
| | Oberflächendetail | 0,25 m | 0,05-2,0 m, Schritt 0,05 | Voxelgröße der Oberfläche. Kleiner ist feiner und schwerer |
| Stoppen nach | Zeit | keine Grenze | 0-120 min | Beendet den Scan nach dieser Zeit (0 = keine Grenze) |
| | Behaltene Ansichten | 3000 | 0-100.000 | Beendet den Scan nach so vielen Schlüsselbildern, als Speicherschutz (0 = keine Grenze) |
| Was ignoriert wird | HUD und alles auf der Kamera ignorieren | an | | Lernt und maskiert das HUD, das Fadenkreuz, die Waffe, die Motorhaube, das Cockpit ([Aufnahme](reconstruction-capture.md#what-is-not-the-world)). Die Zeile darunter sagt, was der Detektor gerade entscheidet |
| Beim Spielen | Rückmeldung über dem Spiel anzeigen | an | | Öffnet das durchklickbare Overlay während des Scans. Der Hinweis darunter: Das Spiel im **randlosen Fenstermodus** laufen lassen; exklusives Vollbild kann von nichts überzeichnet werden |
| Renn-Telemetrie (Forza) | Auf Positionsdaten hören | aus | | Übernimmt den Kamerapfad aus Forzas Data Out, statt ihn aus dem Bild zu schätzen ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (Port) | 5300 | 1-65535 | Der Data-Out-Port |
| | (Statuszeile) | | | `N packets — poses come from the game, not from the picture`, oder `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Scan starten** / **Scan stoppen** | | | Startet oder stoppt; zeigt das Tastenkürzel, wenn es registriert wurde |
| | **Tiefenmodell einrichten** | versteckt | | Siehe oben |
| | **Level speichern…** | deaktiviert | | Aktiv nach einem Scan, der Oberflächen-Voxel erzeugt hat; fragt nach einem Dateinamen (Standard `scan.glb`) |
| | (graue Zeile) | | | `Model: <file> (<licence>) · Available: <backends>`, plus Einrichtungshinweise wie die Installation von `onnxruntime-gpu` |

### Die Voreinstellungen {#the-presets}

| Voreinstellung | Längste Seite der Aufnahme | Behalte-Quantil | Anfangsschwelle | Angezeigte Zusammenfassung |
|---|---|---|---|---|
| Entwurf | 640 px | 0,85 | 0,020 | Schnell und grob. Gut, um eine Route vor einem richtigen Scan zu prüfen. |
| Ausgewogen | 960 px | 0,65 | 0,010 | Die übliche Wahl. In normalem Tempo gehen. |
| Detailliert | 1280 px | 0,40 | 0,004 | Langsam und gründlich. Bewusst gehen und sanft drehen. |

Das Behalte-Quantil bedeutet „ein Bild behalten, wenn es sich mehr geändert hat als dieses Quantil der
Änderungen der letzten 240 Bilder“ - Entwurf behält grob die bewegtesten 15 %, Detailliert die bewegtesten 60 %.
Siehe [Schlüsselbilder](reconstruction-capture.md#keyframes).

### Einstellungen, die im Fenster fest sind {#settings-that-are-fixed-in-the-window}

Das Fenster rekonstruiert beim Scannen immer, nutzt eine Kamerahöhe von **1,15 m** für den Bodenebenen-Maßstab
(der Gehwert 1,70 m ist nicht wählbar) und lässt die Backend-Leiter die GPU wählen. Das sind `ScanSettings`-Felder
(`camera_height`, `prefer_backend`), die nur ein Skript ändern kann.

## Rechte Spalte: was der Scan gerade tut {#right-column-what-the-scan-is-doing}

| Element | Zeigt |
|---|---|
| **Was die Kamera sieht** | das letzte Schlüsselbild |
| **Form, die gelesen wird** | seine vorhergesagte Tiefe, mit der Turbo-Farbkarte gefärbt, normiert zwischen dem 2. und 98. Perzentil dieses Bildes (damit ein einzelner Himmelspixel den Bereich nicht flach macht) |
| **Abdeckung - wo du warst und wie gut** | eine Draufsicht (siehe unten) |
| **Lohnt einen weiteren Blick** | die Schwachstellen, nummeriert passend zu den Ringen auf der Karte, je mit einer Anweisung; die schlimmste (größte) zuerst, höchstens 8; danach die Stellen, die du markiert hast (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Gehgeschwindigkeits-Balken | `walk speed — N% of the way to the next view`: die Bildänderung des letzten Bildes geteilt durch die **verwendete Schwelle** - die Anfangsschwelle der Voreinstellung für die ersten 30 Bilder, danach die angepasste ([Schlüsselbilder](reconstruction-capture.md#keyframes)) |
| Gesundheitszeile | Tracking-Zustand oder eine Aufnahmewarnung (unten) |
| Größenzeile | `Size: ...`, wie der Maßstab des Levels festgelegt wurde oder warum nicht ([Maßstab](reconstruction-pose.md#scale)) |
| Statistikzeile | `views  frames  dropped  depth-per-second  seconds`, und während der Rekonstruktion `placed  cells  % well seen  metres`, plus `recovered` und `loops closed`, wenn einer von beiden nicht null ist |
| Tastenzeile | die registrierten Tasten oder der Grund, warum sie nicht registriert werden konnten |
| Hinweiszeile (gelb) | Live-Hinweise (unten), die letzte Meldung des Scans und Markierungen |

### Die Abdeckungskarte {#the-coverage-map}

Alle 900 ms auf einem Hintergrund-Thread neu gezeichnet (nie auf dem Oberflächen-Thread), mit 200 x 200
Zellen, skaliert auf 420 px:

- jede Spalte des Abdeckungsrasters nimmt die **beste** Beobachtungsqualität darin (damit ein gut gesehener
  Boden nicht durch eine schlecht gesehene Decke darüber gelb gefärbt wird);
- die Skala läuft rot (schlecht) - gelb (dünn) - gelbgrün (akzeptabel) - grün (gut);
- nie beobachtete Zellen sind ein eigenes dunkles Grau, damit eine unerforschte Ecke nicht wie eine schlecht
  gescannte aussieht;
- der begangene Weg ist eine dünne helle Linie, die aktuelle Position ein weißer Punkt;
- Schwachstellen sind weiße Ringe mit ihrer Nummer;
- markierte Stellen sind gelbe Quadrate mit der Beschriftung `M1`, `M2`, …

Wie Qualität und Schwachstellen berechnet werden: [Fusion, Abdeckung und Farbe](reconstruction-fusion-and-texture.md#coverage).

### Die Gesundheitszeile {#the-health-line}

| Tracking-Gesundheit (platzierte Bilder / Bilder) | Text | Farbe |
|---|---|---|
| noch keine Bilder | Waiting for the first frame. | grau |
| 90 % oder mehr | Tracking well — N of M frames placed. | grün |
| 60 % oder mehr | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | gelb |
| unter 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rot |

Eine Aufnahmewarnung aus dem Abdeckungsraster ersetzt sie (rot, wenn der Scan als nicht rekonstruierbar gilt,
sonst gelb): fast keine Parallaxe, alles aus mehr als 25 m gesehen, oder dünne Parallaxe. Siehe [Abdeckung](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Die Hinweiszeile {#the-hint-line}

| Bedingung | Hinweis |
|---|---|
| mehr als die Hälfte der Bilder verworfen, nach 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| weniger als 0,3 behaltene Ansichten pro Sekunde, nach 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| mehr als 8 behaltene Ansichten pro Sekunde, nach 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| Scan beendet | die Meldung der Sitzung: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` oder `failed: <error>` |

## Tastenkürzel {#hotkeys}

Mit Windows registriert (`RegisterHotKey`), daher funktionieren sie, während das Spiel den Fokus hat. Aus einem
Vollbildspiel heraus mit Alt-Tab zu wechseln ruiniert genau die Aufnahme.

| Tasten | Aktion |
|---|---|
| **Strg+Alt+F9** | Scan starten / stoppen |
| **Strg+Alt+F10** | Diese Stelle zum erneuten Besuch markieren (während des Scans) |
| **Strg+Alt+F11** | Overlay zeigen / verbergen (schaltet das Feld „Rückmeldung über dem Spiel anzeigen“ um) |

- Sie werden einmal registriert, wenn sich das Fenster öffnet, und freigegeben, wenn es schließt; solange sie
  registriert sind, werden diese Tastenkombinationen allen anderen Programmen entzogen, einschließlich des Spiels.
  F-Tasten mit zwei Modifikatoren wurden gewählt, weil Spiele sie selten belegen.
- Die Wiederholung beim Halten wird unterdrückt (`MOD_NOREPEAT`), damit das Halten einer Taste den Scan nicht
  dutzendmal umschaltet.
- Eine Taste, die schon ein anderes Programm belegt, wird gemeldet (`... unavailable: another program already
  has this key`), und die übrigen funktionieren weiter. Eine Schaltfläche zeigt nur eine Taste an, die tatsächlich
  registriert wurde.
- Die Tasten sind im Code fest (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); der Parser akzeptiert F1-F12 mit
  `ctrl`, `alt` und `shift`. Außerhalb von Windows gibt es keine globalen Tastenkürzel, und das Fenster sagt es.
- **Markieren** speichert die aktuelle Kameraposition (die des zuletzt platzierten Bildes) und zeigt „Marked MN.
  Marked spots are on the map and saved with the level.“ Bevor ein Bild platziert wurde, heißt es, dass es nichts
  gibt, was markiert werden könnte. Markierte Stellen werden auf der Karte des Fensters und des Overlays als gelbe
  Quadrate mit der Beschriftung `M1`, `M2`, … gezeichnet, unter den Schwachstellen aufgelistet, in der Statistikzeile
  des Overlays gezählt und mit dem Level gespeichert (unten).

## Das Overlay {#the-overlay}

Ein kleines Feld, über dem Spiel festgepinnt, damit die Rückmeldung dort ist, wo die Augen schon sind.

- Rahmenlos, immer oben, ein Werkzeugfenster (nicht in der Taskleiste oder bei Alt-Tab), in Qt für Eingaben
  durchlässig und unter Windows durchklickbar gemacht (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), damit ein Klick für das
  Spiel nie verschluckt wird. Es wird angezeigt, ohne den Fokus zu nehmen.
- Obere rechte Ecke des Hauptbildschirms, 18 px von den Rändern; 214 x 358 px.
- Öffnet sich, wenn ein Scan startet (wenn „Rückmeldung über dem Spiel anzeigen“ an ist), schließt sich, wenn er stoppt.
- **Braucht den randlosen Fenstermodus**: Nichts kann über exklusivem Vollbild zeichnen - weder dieses, noch das Overlay
  von Steam, noch das von Discord.

Von oben nach unten zeigt es:

| Element | Inhalt |
|---|---|
| Abdeckungskarte | 190 px, dieselbe Karte wie im Fenster in gröberen 120 x 120, mit dem Weg, den Schwachstellen-Ringen und markierten Stellen |
| Gesundheit | derselbe Text und dieselbe Farbe wie die Gesundheitszeile des Fensters |
| Statistik | `N placed · M to revisit · X m`, mit `· K marked`, wenn welche markiert sind |
| **Bewegungs**-Balken | wie der Gehgeschwindigkeits-Balken des Fensters: die Bildänderung des letzten Bildes über der verwendeten Schwelle, voll, wenn das nächste Bild behalten wird |
| **Schärfe**-Balken | Schärfe relativ zum eigenen Median dieser Aufnahme: grün ab 0,75, gelb ab 0,45, rot darunter |
| Hinweis | eine Anweisung, grün / gelb / rot (fett, wenn nicht „ok“) - siehe [Bildqualität](reconstruction-capture.md#frame-quality-and-advice) |
| Tastenkürzel | die registrierten Tasten |

Wenn das Aktualisieren des Overlays je fehlschlägt, wechselt es zu einem roten Feld **„Feedback stopped“**, das sagt,
dass alles, was zuvor angezeigt wurde, veraltet ist, dass der Scan noch läuft und das Hauptfenster weiter stimmt, mit
dem Fehler und einer Zählung. Ein Feld, das grün eingefroren ist, würde sonst weiter als Bestätigung gelesen.

## Speichern {#saving}

**Level speichern…** schreibt die Rekonstruktion als `.glb` (siehe [Die .glb-Ausgabe](glb-output.md)).
Wenn das Volumen keine Oberfläche ergibt, erklärt „Nothing to save“, dass die Verfolgung bei den meisten Teilen des Scans
wohl verloren ging. Bei Erfolg: „Written to <path> ... Load it in 3DHeat through the Level panel.“, und nennt die
Markierungsdatei ebenfalls, wenn es markierte Stellen gibt.

Markierte Stellen werden neben dem Level als **`<name>.marks.json`** geschrieben:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` ist in den eigenen Koordinaten des Levels (der Maßstab der GLB angewandt, damit eine Markierung auf dem Netz
sitzt, über dem sie gemacht wurde), `metres` in Metern; `number` entspricht `M1`, `M2`, … im Fenster. Wenn der Maßstab
auf einem späteren Schlüsselbild gefunden wurde ([Maßstab](reconstruction-pose.md#scale)), enthalten beide diesen Faktor.

Einen Scan zu stoppen behält, was gesammelt wurde; ein neues **Start** verwirft den vorherigen Scan.
**Beim Schließen des Fensters wird nicht nach dem Speichern gefragt**: Es stoppt den Scan, gibt die Tastenkürzel frei
und schließt das Overlay.
