---
title: Udvikling
nav_order: 11
lang: "da"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Udvikling {#development}

## Repositoriets opbygning {#repository-layout}

| Sti | Indhold |
|---|---|
| `heat3d_capture/__main__.py` | kommandolinjen: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out-layout), `fulllap.py` (Forza-lap-filer, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (det fælles lap-dokument) |
| `heat3d_capture/capture/` | `sources.py` (live-optagelse, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (det scanneren kører), `estimator.py` (PyTorch-stien, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (skriveren), `reference.py` (syntetisk referencebane) |
| `heat3d_capture/scan/` | `session.py` (en scanning), `reconstruct.py` (keyframes om til geometri), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: optagelsens HUD - pointpop-op, dødsskærme, minikort med banen, dræbermeddelelser (`profiles.py` pr. spil) |
| `heat3d_capture/locate/` | `locate`: banens renderinger, databasen, matchning, den pr.-bane-model, minikortet |
| `heat3d_capture/ui/` | `__main__.py` (start og kontrol af afhængigheder), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | tjekket for nye udgivelser og opdateringsprogrammet |
| `mods/beamng/heat3d/` | BeamNG-protokolmodet |
| `mods/trackmania/Heat3dRecorder/` | Openplanet-plugin'et |
| `tools/export_onnx.py` | konverteren for dybdemodellen |
| `tools/gen_docs_reference.py` | skriver `docs/cli-reference.md` ud fra `--help`; `--check` siger, om den er forældet |
| `tools/docs_diagrams.py` | tegner diagrammerne i `docs/assets/img/` (pr. sprog med `--lang`) |
| `tools/sync_wiki.py` | genskaber `docs/wiki/` fra `docs/` |
| `models/` | konverterede `.onnx`-filer (ikke versioneret) |
| `tests/` | testpakken; `scene.py` og `track_scene.py` tegner syntetiske scener med kendt geometri |
| `docs/` | denne dokumentation; `docs/wiki/` genereres ud fra den |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Scan-logikken har ingen Qt i sig: `ScanSession` og `Reconstructor` tager almindelige funktioner
og kan styres fra et script eller en test. Eksempel:

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

## Miljøet {#the-environment}

Projektet bruger et virtuelt miljø i `.venv` (oprettet af `scan.bat` eller i hånden). Testene,
der rører ved grænsefladen, kræver **PySide6** i det, som `requirements.txt` installerer som
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Til modelkonverteren, PyTorch-dybdetestene og den offline-sti skal PyTorch (tilpasset GPU'en)
installeres **før** `requirements.txt`; derefter `requirements-offline.txt` og dens `vggt`-linje
til den offline-solver, og `onnxscript` til konverteren. Se
[Kørsel og afhængigheder](runtime.md#installing-by-hand).

## Kørsel af testene {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` sætter `testpaths = tests` og dæmper `UserWarning`'er fra `huggingface_hub`. Pakken
har flere hundrede kontroller; de fleste kræver hverken et spil, en GPU eller optagehardware.

Hvad der springer sig selv over, og hvorfor:

| Tests | Springes over, når |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, vindues-testene i `test_ui_drives_a_scan.py` | der ikke findes `models/depth-*.onnx` - kør `tools/export_onnx.py` først |
| GPU-estimator-testene i `test_depth.py` | PyTorch ikke er installeret, eller der ingen CUDA-enhed er; `fit_scale`- og `AffineFit`-testene kører altid |
| nogle `test_offline.py`- og `test_solveprep.py`-tilfælde | OpenCV ingen videoencoder har til at skrive den syntetiske klip |
| `test_hotkeys.py` | registreringstestene kræver Windows; reservetesten kører andre steder |
| `test_course_ground.py` | `HEAT3D_COURSE` ikke er sat |
| nogle fusionstests | et syntetisk tilfælde ikke fusionerede noget |

### Starttesten {#the-launch-test}

`tests/test_launch.py` kører det rigtige startpunkt, `python -m heat3d_capture.ui`, som en
underproces (med `QT_QPA_PLATFORM=offscreen`) og kontrollerer, at det når hændelsesløkken og
bliver oppe. Den findes, fordi den første build gik ned ved hver start, mens alle andre tests
var grønne: de opretter alle selv en `QApplication` og bygger derefter vinduet, og det springer
den ene rækkefølge over, en bruger udfører - afhængighedstjekket, som opretter et program først.
En komponenttest, der selv bygger sit miljø, kan ikke se en fejl i, hvordan miljøet bygges.

### Grundsandhed {#ground-truth}

- `tests/test_accuracy.py` - et syntetisk rum fra en kendt sti med analytisk dybde; se
  [Banerekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - vejbredde, udtrækning af banens skala, dækningsgitteret
  læst mens det skrives, og hvorfor lukning af sløjfer forbliver slået fra.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - telemetri-layouterne, på pakker og sider
  bygget ud fra de dokumenterede strukturer, og de lap-filer de skriver (kanoniske kanalnavne,
  `meta`, ingen `NaN` i JSON). `tests/test_trackmania_plugin.py` læser Openplanet-plugin'ets kildekode
  for at se, hvad det skriver i hver kørsels beskrivelse.
- `tests/test_route_record.py` - `route`-filen ligger hel på disken, før optageren stopper.
- `tests/test_telemetry_pose.py` - Forza-positioner i spillets egne koordinater, retningerne for
  gir, hældning og rulning, og et hul i telemetrien, der bliver overbygget visuelt i den spejlede verden.
- `tests/test_glb.py` - GLB-kontrakten; viewerens egne tests læser en referencebane skrevet af
  denne skriver, så formatet testes på begge sider.

### Kontrol af en eksporteret bane mod laps {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` kontrollerer, at en bane eksporteret med
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) virkelig ligger under den
optagede bil - bilen bør stå en køjehøjde over overfladen lige under sig. Peg den på en eksporteret
banes stamme (`.glb` og dens `.json` ved siden af):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

En bane med store spring kan fejle med vilje: bilen er i luften over jord, der faktisk findes.

## Konventioner {#conventions}

- Kode under `heat3d_capture/` importerer tunge afhængigheder (OpenCV, ONNX Runtime, PyTorch, Qt)
  dovent, inde i funktioner, så at importere et modul, køre `--help` eller køre telemetri-optagerne
  koster ingenting.
- Arbejdstråde rører aldrig Qt-widgets; resultater krydser til grænsefladens tråd som Qt-signaler.
- Optagelser, lap-filer, mesh'e, modelvægte og video holdes ude af git af `.gitignore`, efter mappe
  og efter filtype.
- Commits og udgivelser: versionen er filen `VERSION`; udgivelser er GitHub-releases i
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), som opdateringsprogrammet
  læser ([Opdateringer](updates.md)).
