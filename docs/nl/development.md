---
title: Ontwikkeling
nav_order: 11
lang: "nl"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Ontwikkeling {#development}

## Indeling van de repository {#repository-layout}

| Pad | Inhoud |
|---|---|
| `heat3d_capture/__main__.py` | de opdrachtregel: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out-indeling), `fulllap.py` (Forza-rondebestanden, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (het gedeelde rondedocument) |
| `heat3d_capture/capture/` | `sources.py` (live opname, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (wat de scanner draait), `estimator.py` (PyTorch-pad, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (de schrijver), `reference.py` (synthetisch referentielevel) |
| `heat3d_capture/scan/` | `session.py` (een scan), `reconstruct.py` (keyframes naar geometrie), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: de HUD van een opname - puntenpop-up, doodsschermen, minimap-track, killfeed (`profiles.py` per game) |
| `heat3d_capture/locate/` | `locate`: de renders van het level, de database, matching, het model per map, de minimap |
| `heat3d_capture/ui/` | `__main__.py` (ingang en afhankelijkheidscontrole), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | de versiecontrole en de updater |
| `mods/beamng/heat3d/` | de BeamNG-protocolmod |
| `mods/trackmania/Heat3dRecorder/` | de Openplanet-plugin |
| `tools/export_onnx.py` | de converter voor het dieptemodel |
| `tools/gen_docs_reference.py` | schrijft `docs/cli-reference.md` vanuit `--help`; `--check` zegt of het verouderd is |
| `tools/docs_diagrams.py` | tekent de diagrammen in `docs/assets/img/` (per taal met `--lang`) |
| `tools/sync_wiki.py` | maakt `docs/wiki/` opnieuw op basis van `docs/` |
| `models/` | geconverteerde `.onnx`-bestanden (niet versiebeheerd) |
| `tests/` | de testsuite; `scene.py` en `track_scene.py` renderen synthetische scènes met bekende geometrie |
| `docs/` | deze documentatie; `docs/wiki/` wordt eruit gegenereerd |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

De scanlogica bevat geen Qt: `ScanSession` en `Reconstructor` nemen gewone functies aan en kunnen vanuit een script of een test worden aangestuurd. Voorbeeld:

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

## De omgeving {#the-environment}

Het project gebruikt een virtuele omgeving in `.venv` (aangemaakt door `scan.bat` of met de hand). De tests die de interface raken hebben **PySide6** daarin nodig; `requirements.txt` installeert dat als `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Voor de modelconverter, de PyTorch-dieptetests en het offline-pad installeer je PyTorch (passend bij de GPU) **voordat** `requirements.txt`; daarna `requirements-offline.txt` en de `vggt`-regel daarin voor de offline-solver, en `onnxscript` voor de converter. Zie [Runtime en afhankelijkheden](runtime.md#installing-by-hand).

## De tests draaien {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` zet `testpaths = tests` en dempt de `UserWarning`s van `huggingface_hub`. De suite heeft er enkele honderden; de meeste hebben geen game, geen GPU en geen opnamehardware nodig.

Wat zichzelf overslaat, en waarom:

| Tests | Overgeslagen wanneer |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, de venstertests in `test_ui_drives_a_scan.py` | er geen `models/depth-*.onnx` is - draai eerst `tools/export_onnx.py` |
| de GPU-estimatortests in `test_depth.py` | PyTorch niet is geïnstalleerd, of er geen CUDA-apparaat is; de `fit_scale`- en `AffineFit`-tests draaien altijd |
| enkele `test_offline.py`- en `test_solveprep.py`-gevallen | OpenCV geen videocodeerder heeft om het synthetische filmpje te schrijven |
| `test_hotkeys.py` | de registratietests Windows nodig hebben; de fallback-test draait op andere systemen |
| `test_course_ground.py` | `HEAT3D_COURSE` niet is ingesteld |
| enkele fusietests | een synthetisch geval niets heeft samengevoegd |

### De launchtest {#the-launch-test}

`tests/test_launch.py` start het echte startpunt, `python -m heat3d_capture.ui`, als subproces (met `QT_QPA_PLATFORM=offscreen`) en controleert dat het de event loop bereikt en blijft draaien. Die test bestaat omdat de eerste build bij elke start crashte, terwijl alle andere tests slaagden: die maken allemaal zelf een `QApplication` aan en bouwen dan het venster, waarbij de ene reeks wordt overgeslagen die een gebruiker wel doorloopt - de afhankelijkheidscontrole die eerst een applicatie aanmaakt. Een componenttest die zijn eigen omgeving bouwt, kan een fout in hoe de omgeving wordt opgebouwd niet zien.

### Grondwaarheid {#ground-truth}

- `tests/test_accuracy.py` - een synthetische kamer met een bekend pad en analytische diepte; zie [Level-reconstructie](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - wegbreedte, het afleiden van de baanschaal, het dekkingsraster dat wordt gelezen terwijl het wordt geschreven, en waarom loop-sluiting uit blijft.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - de telemetrie-indelingen, op pakketten en pagina's die zijn gebouwd uit de gedocumenteerde structuren, en de rondebestanden die ze schrijven (kanonieke kanaalnamen, `meta`, geen `NaN` in de JSON). `tests/test_trackmania_plugin.py` leest de bron van de Openplanet-plugin na voor wat die in de beschrijving van elke run schrijft.
- `tests/test_route_record.py` - het `route`-bestand staat compleet op schijf voordat de recorder stopt.
- `tests/test_telemetry_pose.py` - Forza-posities in de eigen coördinaten van het spel, de draairichtingen van yaw, pitch en roll, en een telemetriegat dat visueel wordt overbrugd in de gespiegelde wereld.
- `tests/test_glb.py` - het GLB-contract; de eigen tests van de viewer lezen een referentielevel dat deze schrijver maakt, dus het formaat wordt aan beide kanten getest.

### Een geëxporteerde baan controleren tegen ronden {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` controleert of een baan die is geëxporteerd met [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) echt onder de opgenomen auto ligt - de auto hoort een rijhoogte boven het oppervlak direct eronder te zweven. Wijs het naar de stam van een geëxporteerde baan (de `.glb` en de `.json` ernaast):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Een baan met grote sprongen kan met opzet falen: de auto is in de lucht boven grond die er wél is.

## Conventies {#conventions}

- Code onder `heat3d_capture/` importeert zware afhankelijkheden (OpenCV, ONNX Runtime, PyTorch, Qt) pas binnen functies, zodat een module importeren, `--help` draaien of de telemetrierecorders draaien niets kost.
- Werkthreads raken nooit Qt-widgets aan; resultaten gaan naar de interfacethread als Qt-signalen.
- Opnames, rondebestanden, meshes, modelgewichten en video worden door `.gitignore` buiten git gehouden, per map en per bestandstype.
- Commits en releases: de versie is het bestand `VERSION`; releases zijn GitHub-releases van [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), die de updater uitleest ([Updates](updates.md)).
