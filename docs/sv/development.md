---
title: Utveckling
nav_order: 11
lang: "sv"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Utveckling {#development}

## Repositoriets struktur {#repository-layout}

| Sökväg | Innehåll |
|---|---|
| `heat3d_capture/__main__.py` | kommandoraden: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out-layouten), `fulllap.py` (Forza-varvfiler, relä), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (det gemensamma varvdokumentet) |
| `heat3d_capture/capture/` | `sources.py` (live-inspelning, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (det skannern kör), `estimator.py` (PyTorch-vägen, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (skrivaren), `reference.py` (syntetisk referensnivå) |
| `heat3d_capture/scan/` | `session.py` (en skanning), `reconstruct.py` (nyckelbilder till geometri), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD:en för en inspelning - poängpopup, dödsskärmar, minikarta med bana, dödsnotisflöde (`profiles.py` per spel) |
| `heat3d_capture/locate/` | `locate`: nivåns renderingar, databasen, matchningen, modellen per karta, minikartan |
| `heat3d_capture/ui/` | `__main__.py` (start och kontroll av beroenden), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | kontrollen av nya versioner och uppdateraren |
| `mods/beamng/heat3d/` | BeamNG-protokollmodden |
| `mods/trackmania/Heat3dRecorder/` | Openplanet-insticksprogrammet |
| `tools/export_onnx.py` | omvandlaren för djupmodellen |
| `tools/gen_docs_reference.py` | skriver `docs/cli-reference.md` från `--help`; `--check` säger om den är gammal |
| `tools/docs_diagrams.py` | ritar diagrammen i `docs/assets/img/` (per språk med `--lang`) |
| `tools/sync_wiki.py` | skapar om `docs/wiki/` från `docs/` |
| `models/` | konverterade `.onnx`-filer (inte versionshanterade) |
| `tests/` | testsviten; `scene.py` och `track_scene.py` ritar syntetiska scener med känd geometri |
| `docs/` | den här dokumentationen; `docs/wiki/` skapas från den |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Skanningslogiken innehåller ingen Qt: `ScanSession` och `Reconstructor` tar vanliga funktioner
och kan köras från ett skript eller ett test. Exempel:

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

## Miljön {#the-environment}

Projektet använder en virtuell miljö i `.venv` (skapad av `scan.bat` eller för hand). Testerna som
rör gränssnittet behöver **PySide6** i den, som `requirements.txt` installerar som
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

För modellomvandlaren, PyTorch-djuptesterna och den offline-vägen installerar du PyTorch (anpassat
efter grafikkortet) **före** `requirements.txt`; sedan `requirements-offline.txt` och dess rad för
`vggt` för den offline-lösaren, och `onnxscript` för omvandlaren. Se
[Körtid och beroenden](runtime.md#installing-by-hand).

## Köra testerna {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` sätter `testpaths = tests` och tystar `UserWarning`-meddelanden från
`huggingface_hub`. Sviten har flera hundra kontroller; de flesta behöver varken ett spel, ett
grafikkort eller inspelningsutrustning.

Vad som hoppar över sig självt, och varför:

| Tester | Hoppas över när |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, fönsterteserna i `test_ui_drives_a_scan.py` | ingen `models/depth-*.onnx` - kör `tools/export_onnx.py` först |
| GPU-skattningstesterna i `test_depth.py` | PyTorch är inte installerat, eller det finns ingen CUDA-enhet; testerna för `fit_scale` och `AffineFit` körs ändå |
| vissa fall i `test_offline.py` och `test_solveprep.py` | OpenCV saknar en videokodare för att skriva det syntetiska klippet |
| `test_hotkeys.py` | registreringstesterna kräver Windows; reservtestet körs på andra system |
| `test_course_ground.py` | `HEAT3D_COURSE` är inte satt |
| några fusionstester | ett syntetiskt fall sammanfogade ingenting |

### Starttestet {#the-launch-test}

`tests/test_launch.py` kör den riktiga startpunkten, `python -m heat3d_capture.ui`, som en
underprocess (med `QT_QPA_PLATFORM=offscreen`) och kontrollerar att den når händelseloopen och
håller sig igång. Det finns för att det första bygget kraschade vid varje start medan alla andra
tester gick igenom: de skapar alla ett `QApplication` själva och bygger sedan fönstret, vilket
hoppar över den enda ordning en användare faktiskt följer - beroendekontrollen som skapar ett
program först. Ett komponenttest som bygger sin egen miljö kan inte se ett fel i hur miljön byggs.

### Facit {#ground-truth}

- `tests/test_accuracy.py` - ett syntetiskt rum från en känd väg med analytiskt djup; se
  [Nivårekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - vägbredd, extrahering av banans skala, täckningsnätet läst
  medan det skrivs, och varför slutningskoppling är av.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - telemetrilayouterna, på paket och sidor
  byggda från de dokumenterade strukturerna, och varvfilerna de skriver (kanoniska kanalnamn,
  `meta`, inget `NaN` i JSON). `tests/test_trackmania_plugin.py` läser insticksprogrammets källkod
  för vad det skriver i varje körnings beskrivning.
- `tests/test_route_record.py` - `route`-filen finns på disken, hel, innan inspelaren stoppar.
- `tests/test_telemetry_pose.py` - Forza-poser i spelets egna koordinater, riktningarna för yaw,
  pitch och roll, och en telemetrilucka som överbryggas visuellt i den speglade världen.
- `tests/test_glb.py` - GLB-kontraktet; visarens egna tester läser en referensnivå skriven av
  den här skrivaren, så formatet testas på båda sidor.

### Kontrollera en exporterad bana mot varv {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` kontrollerar att en bana exporterad av
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) verkligen ligger under den
inspelade bilen - bilen ska sitta en markfrigång över ytan direkt under den. Peka på den
exporterade banans stam (`.glb` och `.json` bredvid):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

En bana med stora hopp kan falla med avsikt: bilen är i luften över mark som finns.

## Konventioner {#conventions}

- Kod under `heat3d_capture/` importerar tunga beroenden (OpenCV, ONNX Runtime, PyTorch, Qt) lazy,
  inne i funktioner, så att en import av en modul, `--help` eller att köra telemetriinspelarna
  inte kostar något.
- Arbetstrådar rör aldrig Qt-widgetar; resultat går till gränssnittstråden som Qt-signaler.
- Inspelningar, varvfiler, nät, modellvikter och video hålls utanför git av `.gitignore`, per
  mapp och per filtyp.
- Commits och släpp: versionen är filen `VERSION`; släpp är GitHub-releaser i
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), som uppdateraren
  läser ([Uppdateringar](updates.md)).
