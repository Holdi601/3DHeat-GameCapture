---
title: Entwicklung
nav_order: 11
lang: de
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Entwicklung {#development}

## Aufbau des Repositorys {#repository-layout}

| Pfad | Inhalt |
|---|---|
| `heat3d_capture/__main__.py` | die Kommandozeile: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data-Out-Layout), `fulllap.py` (Forza-Rundendateien, Relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (das gemeinsame Rundendokument) |
| `heat3d_capture/capture/` | `sources.py` (Live-Aufnahme, Video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (was der Scanner ausführt), `estimator.py` (PyTorch-Weg, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (der Schreiber), `reference.py` (synthetisches Referenz-Level) |
| `heat3d_capture/scan/` | `session.py` (ein Scan), `reconstruct.py` (Keyframes zu Geometrie), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: das HUD einer Aufnahme - Punkte-Popup, Todesbildschirme, Streckenkarte in der Minikarte, Killfeed (`profiles.py` pro Spiel) |
| `heat3d_capture/locate/` | `locate`: die Renderings des Levels, die Datenbank, der Abgleich, das Modell pro Karte, die Minikarte |
| `heat3d_capture/ui/` | `__main__.py` (Einstieg und Abhängigkeitsprüfung), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | die Versionsprüfung und der Updater |
| `mods/beamng/heat3d/` | der BeamNG-Protokoll-Mod |
| `mods/trackmania/Heat3dRecorder/` | das Openplanet-Plugin |
| `tools/export_onnx.py` | der Konverter für das Tiefenmodell |
| `tools/gen_docs_reference.py` | schreibt `docs/cli-reference.md` aus `--help`; `--check` sagt, ob sie veraltet ist |
| `tools/docs_diagrams.py` | zeichnet die Diagramme in `docs/assets/img/` (pro Sprache mit `--lang`) |
| `tools/sync_wiki.py` | erzeugt `docs/wiki/` neu aus `docs/` |
| `models/` | konvertierte `.onnx`-Dateien (nicht versioniert) |
| `tests/` | die Testsuite; `scene.py` und `track_scene.py` rendern synthetische Szenen mit bekannter Geometrie |
| `docs/` | diese Dokumentation; `docs/wiki/` wird daraus erzeugt |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Die Scan-Logik enthält kein Qt: `ScanSession` und `Reconstructor` nehmen einfache aufrufbare Funktionen entgegen und lassen sich aus einem Skript oder einem Test steuern. Beispiel:

```python
from heat3d_capture.depth.onnx_estimator import OnnxDepthEstimator
from heat3d_capture.scan.session import Quality, ScanSession, ScanSettings

settings = ScanSettings(source="walk.mp4", quality=Quality.BALANCED, field_of_view=90.0,
                        camera_height=1.70)
session = ScanSession(settings, estimator=OnnxDepthEstimator("models/depth-small-518.onnx"))
session.start()
session.wait()
print(session.progress.message, session.export("walk.glb"))
```

## Die Umgebung {#the-environment}

Das Projekt nutzt eine virtuelle Umgebung in `.venv` (angelegt von `scan.bat` oder von Hand). Die Tests, die die Oberfläche berühren, brauchen darin **PySide6**, das `requirements.txt` als `PySide6-Essentials` installiert:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Für den Modellkonverter, die PyTorch-Tiefentests und den Offline-Weg installiere PyTorch (passend zur GPU) **vor** `requirements.txt`; danach `requirements-offline.txt` und dessen `vggt`-Zeile für den Offline-Löser sowie `onnxscript` für den Konverter. Siehe [Laufzeit und Abhängigkeiten](runtime.md#installing-by-hand).

## Tests ausführen {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` setzt `testpaths = tests` und unterdrückt `UserWarning`s von `huggingface_hub`. Die Suite hat mehrere hundert Prüfungen; die meisten brauchen weder ein Spiel, eine GPU noch Aufnahmehardware.

Was sich selbst überspringt, und warum:

| Tests | Überspringen, wenn |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, die Fenstertests in `test_ui_drives_a_scan.py` | keine `models/depth-*.onnx` da - zuerst `tools/export_onnx.py` ausführen |
| die GPU-Schätzer-Tests in `test_depth.py` | PyTorch ist nicht installiert oder es gibt kein CUDA-Gerät; die Tests zu `fit_scale` und `AffineFit` laufen in jedem Fall |
| einige Fälle in `test_offline.py` und `test_solveprep.py` | OpenCV hat keinen Video-Encoder, um den synthetischen Clip zu schreiben |
| `test_hotkeys.py` | die Registrierungstests brauchen Windows; der Ausweichtest läuft anderswo |
| `test_course_ground.py` | `HEAT3D_COURSE` ist nicht gesetzt |
| ein paar Fusionstests | ein synthetischer Fall hat nichts fusioniert |

### Der Starttest {#the-launch-test}

`tests/test_launch.py` startet den echten Einstiegspunkt `python -m heat3d_capture.ui` als Unterprozess (mit `QT_QPA_PLATFORM=offscreen`) und prüft, dass er die Ereignisschleife erreicht und oben bleibt. Es gibt ihn, weil der erste Build bei jedem Start abstürzte, während alle anderen Tests bestanden: Sie bauen alle selbst eine `QApplication` und dann das Fenster, was genau die eine Abfolge überspringt, die ein Nutzer ausführt - die Abhängigkeitsprüfung, die zuerst eine Anwendung anlegt. Ein Komponententest, der seine eigene Umgebung baut, kann einen Fehler in der Art, wie die Umgebung gebaut wird, nicht sehen.

### Grundwahrheit {#ground-truth}

- `tests/test_accuracy.py` - ein synthetischer Raum mit bekanntem Weg und analytischer Tiefe; siehe [Level-Rekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - Straßenbreite, Extraktion des Streckenmaßstabs, das Abdeckungsgitter, das beim Schreiben gelesen wird, und warum das Schließen von Schleifen aus bleibt.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - die Telemetrie-Layouts, auf Paketen und Seiten, die aus den dokumentierten Strukturen gebaut sind, und die Rundendateien, die sie schreiben (kanonische Kanalnamen, `meta`, kein `NaN` im JSON). `tests/test_trackmania_plugin.py` liest den Quelltext des Openplanet-Plugins, um zu sehen, was es in die Beschreibung jedes Laufs schreibt.
- `tests/test_route_record.py` - die `route`-Datei liegt vollständig auf der Festplatte, bevor der Recorder stoppt.
- `tests/test_telemetry_pose.py` - Forza-Posen in den eigenen Koordinaten des Spiels, die Richtungen von Gier, Nick und Rollen, und eine Telemetrielücke, die in der gespiegelten Welt optisch überbrückt wird.
- `tests/test_glb.py` - der GLB-Vertrag; die eigenen Tests des Viewers lesen ein Referenz-Level, das dieser Schreiber erzeugt hat, sodass das Format auf beiden Seiten getestet wird.

### Eine exportierte Strecke gegen Runden prüfen {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` prüft, dass eine Strecke, die mit [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) exportiert wurde, wirklich unter dem aufgezeichneten Auto liegt - das Auto sollte eine Bodenfreiheit über der Fläche direkt darunter stehen. Gib ihm den Stamm einer exportierten Strecke an (die `.glb` und die `.json` daneben):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Eine Strecke mit großen Sprüngen kann absichtlich durchfallen: Das Auto ist in der Luft über Boden, der da ist.

## Konventionen {#conventions}

- Code unter `heat3d_capture/` lädt schwere Abhängigkeiten (OpenCV, ONNX Runtime, PyTorch, Qt) erst innerhalb von Funktionen, sodass der Import eines Moduls, `--help` oder das Starten der Telemetrie-Recorder nichts kostet.
- Worker-Threads berühren nie Qt-Widgets; Ergebnisse gehen als Qt-Signale an den Oberflächen-Thread.
- Aufnahmen, Rundendateien, Netze, Modellgewichte und Videos bleiben durch `.gitignore` aus Git heraus, nach Ordner und Dateityp.
- Commits und Releases: die Version steht in der Datei `VERSION`; Releases sind GitHub-Releases von [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), die der Updater liest ([Aktualisierungen](updates.md)).
