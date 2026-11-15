---
title: Level-Rekonstruktion aus dem Spiel
nav_order: 6
lang: de
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Level-Rekonstruktion aus dem Spiel {#level-reconstruction-from-gameplay}

Geh langsam durch ein Level oder fahre eine Strecke, und der Scanner macht aus dem, was der Bildschirm zeigte, eine `.glb`, die der 3DHeat-Viewer als Kontext unter der Telemetrie lädt - derselbe Dateivertrag, den der Unreal-Exporter schreibt. Das ist für den Fall gedacht, dass niemand die Karte exportiert hat und die Spieldateien nicht gelesen werden können; ein Engine-Export oder ein Spieldatei-Export ist exakt, dies ist eine Schätzung.

## Die Pipeline {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Stufe | Live-Scan (`heat3d_capture.ui`) | Offline (`reconstruct`) | Seite |
|---|---|---|---|
| Bilder | Monitor, Fenster oder Video, auf die lange Seite der Voreinstellung verkleinert | Video, zweimal abgetastet (Lösungsplan und Fusionsintervall) | [Aufnahme](reconstruction-capture.md) |
| Keyframes | behalten je nach Bildänderung, Schwelle an die Aufnahme angepasst | alle `--fuse-interval` Sekunden | [Aufnahme](reconstruction-capture.md#keyframes) |
| Masken | auf Änderung basierende `ScreenMask`, danach auf Fluss basierende `FlowMask` nach 40 Keyframes | `FlowMask`, gelernt aus vier Durchläufen des Videos; nicht auf den Löser angewendet | [Aufnahme](reconstruction-capture.md#what-is-not-the-world) |
| Tiefe | ONNX-Modell auf dem besten GPU-Backend | PyTorch Depth Anything V2 Small | [Tiefe](reconstruction-depth.md) |
| Pose | visuelle Odometrie oder exakte Forza-Telemetrie | VGGT-Fenster, zu einem Pfad zusammengefügt und interpoliert | [Pose](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Maßstab | einmal die Kamerahöhe über dem Boden (1,15 m) oder Telemetrie | die eigenen Einheiten des gelösten Pfads | [Pose](reconstruction-pose.md#scale) |
| Fusion | gewichtete Belegung, dünn besetzte Voxel; Abdeckungsgitter | dasselbe | [Fusion](reconstruction-fusion-and-texture.md) |
| Ausgabe | `.glb`, Boden-/Bauteile, Farbe pro Eckpunkt, Zentimeter | dasselbe | [Die .glb-Ausgabe](glb-output.md) |

Code: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan) (`session.py` - Einstellungen und Takt eines Scans; `reconstruct.py` - Keyframes zu Geometrie; `offline.py` - der Offline-Weg), die Stufen liegen in `capture/`, `depth/`, `pose/`, `fusion/` und `geometry/`.

## Woher die Genauigkeit kommt {#where-accuracy-comes-from}

Monokulare Tiefe stimmt nur bis auf einen unbekannten Maßstab - ein Foto eines Raums und eines Puppenhauses sind dasselbe Bild. Deshalb darf das Netzwerk tun, was es gut kann (relative Form, Kanten, dünne Strukturen), und Maßstab und Kamerapfad kommen von irgendwo, das sie kennt:

| Spiel | Kamerapfad | Maßstab |
|---|---|---|
| Forza Horizon / Motorsport mit eingeschalteter Telemetrie | exakt, aus Data Out, auf den Aufnahmezeitpunkt jedes Bildes interpoliert | exakt: Die Tiefe wird verankert, indem Merkmale zwischen zwei bekannten Posen trianguliert werden |
| Alles andere, live | visuelle Odometrie, Bild für Bild verkettet | einmal festgelegt aus einer angenommenen Kamerahöhe über dem Boden |
| Eine Aufnahme, offline | VGGT, über sich überlappende Fenster gelöst | die eigenen Einheiten der Lösung (nicht metrisch) |

Die eine Zahl, die dem Scanner vorgegeben statt gemessen wird, ist das **horizontale Sichtfeld** des Spiels (im Fenster standardmäßig 90 Grad; Rennspiele liegen eher bei 65). Zu eng, und das Level wird tiefer rekonstruiert, als es ist; zu weit, und es flacht ab.

## Dem Nutzer früh Bescheid sagen {#telling-the-user-early}

Ein Scan ist eine körperliche Handlung - jemand läuft mehrere Minuten durch ein Level -, und der teure Fehler ist, den Weg zu Ende zu gehen und dann zu merken, dass er nichts taugte. Deshalb misst das Fenster den Tiefendurchsatz dieses Rechners, bevor etwas starten kann, und sagt, wie der Scan werden wird ([Laufzeit](runtime.md#what-to-expect-from-this-machine)); während des Scans zeigt es eine Abdeckungskarte mit nummerierten Schwachstellen, Tracking-Zustand, eine Balkenanzeige für die Gehgeschwindigkeit, eine für die Schärfe und jeweils eine Anweisung, im Fenster und in einem durchklickbaren Overlay über dem Spiel ([Das Scan-Fenster](reconstruction-scan-ui.md)).

## Gemessen an synthetischer Grundwahrheit {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` rendert einen 12 x 8 m großen Raum (4 m hoch) von einem bekannten Kamerapfad, mit analytischer (nicht netzwerkbasierter) Tiefe, und rekonstruiert ihn mit 0,2-m-Voxeln. Er prüft, dass mehr als 90 % der Bilder platziert werden, der mittlere Pfadfehler unter 0,35 m liegt (im schlimmsten Fall unter 1 m), die gegangene Strecke innerhalb von 10 % der Wahrheit liegt, der Raum mit der richtigen Breite herauskommt, auf 1,5 m genau, über 75 % der Wandfläche innerhalb von 0,45 m einer echten Wand liegen, ein Gang im Stil einer Vermessung eine deutlich bessere Abdeckung erreicht als geradeaus zu gehen, und eine Szene ohne Merkmale abgelehnt statt erfunden wird. Die analytische Tiefe trennt Pose, Maßstab und Fusion vom Netzwerk; wie das Netzwerk im echten Spiel abschneidet, ist eine eigene Frage, die keine synthetische Szene beantwortet. `tests/test_track_width.py` prüft, dass eine Runde, die außermittig auf einer Straße bekannter Breite gefahren wird, die Breite der Straße rekonstruiert, nicht nur die gefahrene Linie.

## Seiten {#pages}

- [Das Scan-Fenster](reconstruction-scan-ui.md) - jedes Bedienelement, jeder Tastenkürzel und jedes Overlay-Element
- [Aufnahme, Masken und Bildqualität](reconstruction-capture.md)
- [Tiefe](reconstruction-depth.md)
- [Kamerapose und Maßstab](reconstruction-pose.md)
- [Fusion, Abdeckung und Farbe](reconstruction-fusion-and-texture.md)
- [Die .glb-Ausgabe](glb-output.md)
- [Offline-Rekonstruktion](reconstruction-offline.md)
