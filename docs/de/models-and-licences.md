---
title: Modelle und Lizenzen
nav_order: 7
lang: "de"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modelle und Lizenzen {#models-and-licences}

Alles, was für dieses Repository geschrieben wurde, steht unter der **MIT-Lizenz** ([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Was MIT nicht abdecken kann, ist das, womit die Werkzeuge laufen: die Pakete, die sie importieren, die Modelle, die die Rekonstruktion nutzt, und die Spiele, die sie lesen. Der vollständige Nachweis mit Quellen steht in [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); seine Lizenzen wurden im September 2026 aus den Paketangaben und Modellkarten abgelesen. Wenn sich die Bedingungen einer Komponente seitdem geändert haben, gilt die Quelle, nicht diese Seite. Dies ist keine Rechtsberatung.

## Das Tiefenmodell - das, das über die kommerzielle Nutzung entscheidet {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 ist **nicht in allen Größen gleich lizenziert**, und eine Rekonstruktion erbt die Lizenz des Modells, das sie erzeugt hat:

| Modell | Lizenz | Kommerzielle Nutzung | Verwendet von |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **erlaubt** | der Standard: das konvertierte Modell des Scanners (`tools/export_onnx.py` nimmt es standardmäßig, und „Set up the depth model“ im Fenster baut immer dieses), und die Tiefe des Offline-Wegs (Fusion); VGGT liefert seine Posen |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | nur nicht kommerziell | nur, wenn du es selbst konvertierst (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | nur nicht kommerziell | nur, wenn du es selbst konvertierst (`--size large`) |

Base und Large liefern bessere Tiefe. Sie zu konvertieren ist erlaubt; das macht diese Modelldatei und jede damit erstellte Rekonstruktion nicht-kommerziell. Das entscheidet, wer es ausführt; es ist kein Standard, den man übernimmt. Der Scanner wählt unter den Dateien `models/depth-*.onnx` **nach Lizenz, nicht nach Name**: `depth-small-*`, wenn eine vorhanden ist, dann Base, dann Large (`choose_model` in [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). Das Fenster nennt die Datei, die es genommen hat, ihre Lizenz und alle anderen gefundenen Modelldateien, die es nicht genutzt hat; um mit Base zu scannen, die Small-Datei aus `models/` herausschieben.

## VGGT - nur für die Offline-Rekonstruktion {#vggt---offline-reconstruction-only}

| Modell | Lizenz | Verfügbarkeit |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - nur nicht kommerziell**; damit erstellte Rekonstruktionen erben das | öffentlich; der Standard |
| `facebook/VGGT-1B-Commercial` | eigene Lizenz; prüfe die Bedingungen, die dir eingeräumt wurden | eingeschränkt: Der Zugang wird bei Meta beantragt und pro Konto freigegeben; ohne ihn schlägt der Download fehl. Gewählt mit `reconstruct --model vggt-1b-commercial` |

VGGT wird nur von `python -m heat3d_capture reconstruct` genutzt; der Live-Scanner lädt es nie. Der Befehl gibt die Lizenzzeile aus, bevor er startet. Die Rekonstruktion aus Video ist der Teil dieses Projekts, den ein Spieler ausführen würde, und nicht-kommerzielle Bedingungen passen dazu; für kommerzielle Arbeit ist ein Engine-Export oder der Spieldatei-Exporter der Weg, und beide sind ohnehin exakt.

## Bilder finden - `locate` {#locating-frames---locate}

| Modell | Lizenz | Aufgabe |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | findet die Renderings, die dieselbe Stelle zeigen |
| ALIKED `aliked-n16` | BSD-3-Clause | Schlüsselpunkte und Deskriptoren |
| LightGlue (ALIKED-Variante) | Apache-2.0 | gleicht sie ab |

Alle drei erlauben kommerzielle Nutzung und werden beim ersten Gebrauch geladen. SuperPoint, der übliche Partner von LightGlue, wird nicht genutzt: seine Gewichte sind nicht kommerziell. Siehe [Bilder in einem Level finden](locate.md).

## Python-Pakete {#python-packages}

| Paket | Lizenz | Aufgabe |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | Rechnen, Glätten, Marching Cubes |
| opencv-python | Apache-2.0 | Video, Merkmale, optischer Fluss |
| onnxruntime, onnxruntime-directml | MIT | Tiefen-Inferenz |
| windows-capture | MIT | Live-Aufnahme über Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | das Fenster |
| pytest | MIT | nur Entwicklung |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | einmalige Modellkonvertierung; der Offline-Weg |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | der Offline-Weg (`requirements-offline.txt`) |
| vggt | Metas „VGGT License“ (Vereinbarung über Forschungsmaterialien mit einer Richtlinie zur zulässigen Nutzung) | der Offline-Weg; von GitHub mit `--no-deps` installiert |
| moderngl, glcontext | MIT | `locate`: das Level außerhalb des Bildschirms rendern (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: Schlüsselpunkte und Abgleich |

**PySide6 hat Bedingungen.** LGPL-3.0 erlaubt proprietäre und kommerzielle Nutzung, solange Qt eine *austauschbare* Bibliothek bleibt. Hier wird es als gewöhnlicher, dynamisch gebundener Import genutzt, was dies erfüllt, und sein Lizenzhinweis muss mit jeder Verteilung mitgeliefert werden. Das Werkzeug in eine einzige ausführbare Datei zu bündeln, müsste Qt austauschbar halten.

Die eigene Lizenz des Pakets `vggt` wurde aus seiner `LICENSE.txt` abgelesen und steht in `LICENSES.md`; sie deckt den Code ab, getrennt von den CC-BY-NC-4.0 der Gewichte.

## Die Spiele {#the-games}

Telemetrie kommt nur von Schnittstellen, die die Spiele veröffentlichen; Bilder kommen vom Bildschirm. Siehe [Die Regeln](rules.md). Nichts aus einem Spiel wird mitgeliefert oder weitergegeben, und was die Werkzeuge erzeugen, bleibt auf dem Rechner des Nutzers. 3DHeat GameCapture steht mit keinem Spielehersteller in Verbindung und wird von keinem unterstützt; Spielnamen und zugehörige Marken gehören ihren Inhabern.
