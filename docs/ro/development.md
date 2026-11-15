---
title: Dezvoltare
nav_order: 11
lang: "ro"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Dezvoltare {#development}

## Structura depozitului {#repository-layout}

| Cale | Conținut |
|---|---|
| `heat3d_capture/__main__.py` | linia de comandă: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (structura Data Out), `fulllap.py` (fișierele de tur Forza, releu), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (documentul comun al turului) |
| `heat3d_capture/capture/` | `sources.py` (captură live, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (ce rulează scanerul), `estimator.py` (calea PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (scriitorul), `reference.py` (nivel de referință sintetic) |
| `heat3d_capture/scan/` | `session.py` (o scanare), `reconstruct.py` (cadre-cheie transformate în geometrie), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD-ul unei înregistrări - fereastra cu puncte, ecranele de moarte, harta mică a traseului, fluxul de eliminări (`profiles.py` pentru fiecare joc) |
| `heat3d_capture/locate/` | `locate`: randările nivelului, baza de date, potrivirea, modelul pentru fiecare hartă, harta mică |
| `heat3d_capture/ui/` | `__main__.py` (intrarea și verificarea dependențelor), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | verificarea versiunilor noi și actualizatorul |
| `mods/beamng/heat3d/` | modificarea de protocol pentru BeamNG |
| `mods/trackmania/Heat3dRecorder/` | modulul Openplanet |
| `tools/export_onnx.py` | convertorul modelului de adâncime |
| `tools/gen_docs_reference.py` | scrie `docs/cli-reference.md` din `--help`; `--check` spune dacă pagina este învechită |
| `tools/docs_diagrams.py` | desenează diagramele din `docs/assets/img/` (pentru fiecare limbă, cu `--lang`) |
| `tools/sync_wiki.py` | regenerează `docs/wiki/` din `docs/` |
| `models/` | fișiere `.onnx` convertite (nu sunt versionate) |
| `tests/` | suita de teste; `scene.py` și `track_scene.py` randează scene sintetice cu geometrie cunoscută |
| `docs/` | această documentație; `docs/wiki/` se generează din ea |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logica de scanare nu conține Qt: `ScanSession` și `Reconstructor` primesc funcții simple și pot
fi conduse dintr-un script sau un test. Exemplu:

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

## Mediul de lucru {#the-environment}

Proiectul folosește un mediu virtual în `.venv` (creat de `scan.bat` sau manual). Testele care
ating interfața au nevoie de **PySide6** în el, pe care `requirements.txt` îl instalează ca
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Pentru convertorul de modele, testele estimatorului de adâncime PyTorch și calea offline,
instalați PyTorch (potrivit cu placa grafică) **înainte** de `requirements.txt`; apoi
`requirements-offline.txt` și linia lui `vggt` pentru solverul offline, și `onnxscript` pentru
convertor. Vezi [Rulare și dependențe](runtime.md#installing-by-hand).

## Rularea testelor {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` setează `testpaths = tests` și ascunde avertismentele `UserWarning` venite din
`huggingface_hub`. Suita are câteva sute de verificări; majoritatea nu au nevoie nici de un joc,
nici de o placă grafică, nici de hardware de captură.

Ce se sare singur și de ce:

| Teste | Se sar când |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testele de conducere a ferestrei din `test_ui_drives_a_scan.py` | lipsește `models/depth-*.onnx` - rulați mai întâi `tools/export_onnx.py` |
| testele estimatorului pe GPU din `test_depth.py` | PyTorch nu este instalat sau nu există un dispozitiv CUDA; testele `fit_scale` și `AffineFit` rulează oricum |
| unele cazuri din `test_offline.py` și `test_solveprep.py` | OpenCV nu are un codificator video pentru a scrie clipul sintetic |
| `test_hotkeys.py` | testele de înregistrare cer Windows; testul de rezervă rulează oriunde |
| `test_course_ground.py` | `HEAT3D_COURSE` nu este setat |
| câteva teste de fuziune | un caz sintetic nu a fuzionat nimic |

### Testul de pornire {#the-launch-test}

`tests/test_launch.py` rulează punctul real de intrare, `python -m heat3d_capture.ui`, ca subproces
(cu `QT_QPA_PLATFORM=offscreen`) și verifică faptul că ajunge în bucla de evenimente și rămâne
pornit. Există pentru că prima versiune se bloca la fiecare pornire, în timp ce toate celelalte
teste treceau: toate creau singure un `QApplication` și apoi construiau fereastra, sărind peste
singura secvență pe care o parcurge un utilizator - verificarea dependențelor, care creează întâi
o aplicație. Un test de componentă care își construiește singur mediul nu poate vedea o greșeală
în modul în care este construit mediul.

### Adevărul de referință {#ground-truth}

- `tests/test_accuracy.py` - o cameră sintetică dintr-un traseu cunoscut, cu adâncime analitică;
  vezi [Reconstrucția nivelului](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - lățimea drumului, extragerea scării pistei, grila de
  acoperire citită în timp ce este scrisă și motivul pentru care închiderea buclei rămâne oprită.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - structurile de telemetrie, pe pachete și
  pagini construite din structurile documentate, și fișierele de tur pe care le scriu (numele
  canonice ale canalelor, `meta`, fără `NaN` în JSON). `tests/test_trackmania_plugin.py` citește
  codul sursă al modulului Openplanet ca să vadă ce scrie în descrierea fiecărei curse.
- `tests/test_route_record.py` - fișierul `route` este pe disc, complet, înainte ca înregistratorul
  să se oprească.
- `tests/test_telemetry_pose.py` - pozițiile Forza în coordonatele jocului, sensurile yaw-ului,
  pitch-ului și roll-ului și un gol de telemetrie umplut vizual în lumea oglindită.
- `tests/test_glb.py` - contractul GLB; testele vizualizatorului 3DHeat citesc un nivel de referință
  scris de acest scriitor, deci formatul este testat în ambele părți.

### Verificarea unui traseu exportat față de ture {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` verifică faptul că un traseu exportat prin
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) se află cu adevărat sub mașina
înregistrată - mașina ar trebui să stea la o înălțime de rulare deasupra suprafeței de dedesubt.
Indicați-i rădăcina numelui unui traseu exportat (fișierele `.glb` și `.json` de lângă el):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Un traseu cu sărituri mari poate eșua din proiect: mașina este în aer deasupra unui teren care
chiar există.

## Convenții {#conventions}

- Codul din `heat3d_capture/` importă dependențele grele (OpenCV, ONNX Runtime, PyTorch, Qt) leneș,
  în interiorul funcțiilor, astfel încât importarea unui modul, rularea lui `--help` sau rularea
  înregistratorilor de telemetrie nu costă nimic.
- Firele de lucru nu ating niciodată widget-urile Qt; rezultatele trec spre firul interfeței prin
  semnale Qt.
- Înregistrările, fișierele de tur, plasele, greutățile modelelor și video-ul sunt ținute afară din
  git de `.gitignore`, pe foldere și pe tip de fișier.
- Commit-uri și lansări: versiunea este fișierul `VERSION`; lansările sunt versiuni GitHub ale
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), pe care le citește
  actualizatorul ([Actualizări](updates.md)).
