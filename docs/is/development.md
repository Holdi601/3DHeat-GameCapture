---
title: "Þróun"
nav_order: 11
lang: "is"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Þróun {#development}

## Uppbygging geymslunnar {#repository-layout}

| Slóð | Innihald |
|---|---|
| `heat3d_capture/__main__.py` | skipanalínan: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (snið Data Out), `fulllap.py` (Forza hringskrár, sendir), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (sameiginlega hringskjalið) |
| `heat3d_capture/capture/` | `sources.py` (bein upptaka, myndband), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (það sem skanninn keyrir), `estimator.py` (PyTorch leiðin, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (skrifarinn), `reference.py` (tilbúið viðmiðunarborð) |
| `heat3d_capture/scan/` | `session.py` (skönnun), `reconstruct.py` (lykilrammar í rúmfræði), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD upptöku - stigagluggi, dauðaskjáir, smákortsferill, drápalisti (`profiles.py` fyrir hvern leik) |
| `heat3d_capture/locate/` | `locate`: teikningar borðsins, gagnagrunnurinn, pörun, líkan fyrir hvert kort, smákortið |
| `heat3d_capture/ui/` | `__main__.py` (inngangur og athugun á ósjálfstæði), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | útgáfuathugunin og uppfærslan |
| `mods/beamng/heat3d/` | BeamNG samskiptareglu-modið |
| `mods/trackmania/Heat3dRecorder/` | Openplanet viðbótin |
| `tools/export_onnx.py` | umbreytir dýptarlíkansins |
| `tools/gen_docs_reference.py` | skrifar `docs/cli-reference.md` úr `--help`; `--check` segir hvort hún er úrelt |
| `tools/docs_diagrams.py` | teiknar skýringarmyndirnar í `docs/assets/img/` (fyrir hvert tungumál með `--lang`) |
| `tools/sync_wiki.py` | býr `docs/wiki/` til upp á nýtt úr `docs/` |
| `models/` | umbreyttar `.onnx` skrár (ekki í útgáfustjórn) |
| `tests/` | prófanasafnið; `scene.py` og `track_scene.py` teikna tilbúnar senur með þekktri rúmfræði |
| `docs/` | þessi skjöl; `docs/wiki/` er búið til úr þeim |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Skönnunarrökfræðin inniheldur ekkert Qt: `ScanSession` og `Reconstructor` taka einföld köll (callables) og hægt er að
stjórna þeim úr skriftu eða prófun. Dæmi:

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

## Umhverfið {#the-environment}

Verkefnið notar sýndarumhverfi (virtual environment) í `.venv` (búið til af `scan.bat` eða í höndunum). Prófanirnar
sem snerta viðmótið þurfa **PySide6** í því, sem `requirements.txt` setur upp sem
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Fyrir líkanaumbreytarann, PyTorch dýptarprófanirnar og leiðina án nettengingar skaltu setja upp PyTorch (í samræmi við
skjákortið) **áður en** þú setur upp `requirements.txt`; síðan `requirements-offline.txt` og `vggt` línuna í henni fyrir
lausnarann án nettengingar, og `onnxscript` fyrir umbreytarann. Sjá
[Keyrsluumhverfi og ósjálfstæði](runtime.md#installing-by-hand).

## Prófanir keyrðar {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` setur `testpaths = tests` og þaggar niður í `UserWarning` frá `huggingface_hub`. Safnið
hefur nokkur hundruð athuganir; flestar þurfa hvorki leik, skjákort né upptökubúnað.

Hvað sleppir sjálft sér og hvers vegna:

| Prófanir | Sleppt þegar |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, prófanirnar sem stjórna glugganum í `test_ui_drives_a_scan.py` | engin `models/depth-*.onnx` - keyrðu fyrst `tools/export_onnx.py` |
| GPU-mats prófanirnar í `test_depth.py` | PyTorch er ekki uppsett, eða ekkert CUDA tæki er til; `fit_scale` og `AffineFit` prófanirnar keyra samt |
| sumar `test_offline.py` og `test_solveprep.py` prófanir | OpenCV hefur engan myndbandskóðara til að skrifa tilbúna bútinn |
| `test_hotkeys.py` | skráningarprófanir þurfa Windows; varaprófunin keyrir annars staðar |
| `test_course_ground.py` | `HEAT3D_COURSE` er ekki stillt |
| nokkrar samrunaprófanir | tilbúið tilvik samrunaði ekkert |

### Ræsiprófunin {#the-launch-test}

`tests/test_launch.py` keyrir raunverulega inngangsstaðinn, `python -m heat3d_capture.ui`, sem undirferli
(með `QT_QPA_PLATFORM=offscreen`) og athugar að hann nái atburðalykkjunni og haldist uppi. Hún er til
vegna þess að fyrsta útgáfan hrundi við hverja ræsingu á meðan allar aðrar prófanir stóðust: þær búa allar til
`QApplication` sjálfar og smíða svo gluggann, sem sleppir einu röðinni sem notandi
framkvæmir - athugun á ósjálfstæði býr fyrst til forrit. Íhlutaprófun sem smíðar
sitt eigið umhverfi sér ekki galla í því hvernig umhverfið er smíðað.

### Raunveruleg viðmið (ground truth) {#ground-truth}

- `tests/test_accuracy.py` - tilbúið herbergi eftir þekktri leið með greinanlegri dýpt; sjá
  [Endurbygging borðs](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - breidd vegar, útdráttur brautarkvarða, þekjunetið lesið
  meðan það er skrifað, og hvers vegna lokun lykkju er höfð slökkt.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - mælingasniðin, á pökkum og
  síðum smíðuðum úr skjalfestum gagnagerðum, og hringskrárnar sem þau skrifa (viðurkennd rásaheiti,
  `meta`, ekkert `NaN` í JSON). `tests/test_trackmania_plugin.py` les frumkóða Openplanet
  viðbótarinnar til að sjá hvað hún skrifar í lýsingu hvers hlaups.
- `tests/test_route_record.py` - `route` skráin er á disknum, heil, áður en upptökutækið stöðvast.
- `tests/test_telemetry_pose.py` - Forza stöður í hnitum leiksins sjálfs, áttir yaw,
  pitch og roll, og mælingagat brúað sjónrænt í speglaða heiminum.
- `tests/test_glb.py` - GLB samningurinn; eigin prófanir skoðarans lesa viðmiðunarborð sem þessi skrifari
  skrifaði, svo sniðið er prófað báðum megin.

### Útfluttri braut borið saman við hringi {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` athugar að braut sem [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
flutti út liggi í raun undir bílnum sem var tekinn upp - bíllinn ætti að sitja í aksturshæð yfir yfirborðinu beint undir honum. Bentu á
heiti útfluttrar brautar án endingar (`.glb` skráin og `.json` skráin við hlið hennar):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Braut með stórum stökkum getur fallið að hönnun: bíllinn er í lofti yfir jörð sem er þar.

## Venjur {#conventions}

- Kóði undir `heat3d_capture/` flytur inn þung ósjálfstæði (OpenCV, ONNX Runtime, PyTorch, Qt)
  letilega inni í föllum, svo að innflutningur einingar, `--help` eða keyrsla mælingaskráaranna
  kostar ekkert.
- Vinnuþræðir snerta aldrei Qt stjórnhluti; niðurstöður berast til viðmótsþráðarins sem Qt merki (signals).
- Upptökur, hringskrár, net (meshes), líkanaþyngdir og myndband eru höfð utan git með `.gitignore`, eftir
  möppu og skráartegund.
- Framlög og útgáfur: útgáfan er `VERSION` skráin; útgáfur eru GitHub útgáfur af
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), sem uppfærslan
  les ([Uppfærslur](updates.md)).
