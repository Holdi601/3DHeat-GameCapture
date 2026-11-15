---
title: Utvikling
nav_order: 11
lang: "no"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Utvikling {#development}

## Oppsett av repositoriet {#repository-layout}

| Sti | Innhold |
|---|---|
| `heat3d_capture/__main__.py` | kommandolinjen: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out-oppsettet), `fulllap.py` (Forza-rundefiler, relé), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (det delte rundedokumentet) |
| `heat3d_capture/capture/` | `sources.py` (direkte opptak, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (det skanneren kjører), `estimator.py` (PyTorch-varianten, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (skriveren), `reference.py` (det syntetiske referansenivået) |
| `heat3d_capture/scan/` | `session.py` (en skanning), `reconstruct.py` (nøkkelbilder til geometri), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD-en for et opptak - poengvindu, dødsskjermer, minikart med banen, drapslogg (`profiles.py` per spill) |
| `heat3d_capture/locate/` | `locate`: nivåets bilder, databasen, matching, modellen per kart, minikartet |
| `heat3d_capture/ui/` | `__main__.py` (start og sjekk av avhengigheter), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | sjekken for nye utgivelser og oppdateringen |
| `mods/beamng/heat3d/` | BeamNG-protokollmodden |
| `mods/trackmania/Heat3dRecorder/` | Openplanet-pluginen |
| `tools/export_onnx.py` | omformeren for dybdemodellen |
| `tools/gen_docs_reference.py` | skriver `docs/cli-reference.md` fra `--help`; `--check` sier om den er utdatert |
| `tools/docs_diagrams.py` | tegner diagrammene i `docs/assets/img/` (per språk med `--lang`) |
| `tools/sync_wiki.py` | lager `docs/wiki/` på nytt fra `docs/` |
| `models/` | konverterte `.onnx`-filer (ikke versjonert) |
| `tests/` | testsettet; `scene.py` og `track_scene.py` tegner syntetiske scener med kjent geometri |
| `docs/` | denne dokumentasjonen; `docs/wiki/` lages ut fra den |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Skanningslogikken har ingen Qt i seg: `ScanSession` og `Reconstructor` tar vanlige funksjoner og
kan styres fra et skript eller en test. Eksempel:

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

Prosjektet bruker et virtuelt miljø i `.venv` (laget av `scan.bat` eller for hånd). Testene som
bruker grensesnittet trenger **PySide6** i det miljøet. `requirements.txt` installerer det som
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

For omformeren for modellen, PyTorch-dybdetestene og den frakoblede løsningen: installer PyTorch
(tilpasset GPU-en) **før** `requirements.txt`. Installer deretter `requirements-offline.txt` og
linjen `vggt` for den frakoblede løseren, og `onnxscript` for omformeren. Se
[Kjøretid, avhengigheter og ytelse](runtime.md#installing-by-hand).

## Kjøre testene {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` setter `testpaths = tests` og skjuler `UserWarning`-meldinger fra `huggingface_hub`.
Testsettet har flere hundre sjekker. De fleste trenger verken et spill, en GPU eller
opptaksutstyr.

Hva som hopper over seg selv, og hvorfor:

| Tester | Hoppes over når |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, vindutestene i `test_ui_drives_a_scan.py` | ingen `models/depth-*.onnx` - kjør `tools/export_onnx.py` først |
| GPU-testene for dybde i `test_depth.py` | PyTorch er ikke installert, eller det finnes ingen CUDA-enhet; testene for `fit_scale` og `AffineFit` kjøres alltid |
| noen tilfeller i `test_offline.py` og `test_solveprep.py` | OpenCV har ingen videoenkoder til å skrive det syntetiske klippet |
| `test_hotkeys.py` | registreringstestene krever Windows; reservetesten kjøres ellers |
| `test_course_ground.py` | `HEAT3D_COURSE` er ikke satt |
| noen fusjonstester | et syntetisk tilfelle fusjonerte ingenting |

### Starttesten {#the-launch-test}

`tests/test_launch.py` kjører det ekte startpunktet, `python -m heat3d_capture.ui`, som en
underprosess (med `QT_QPA_PLATFORM=offscreen`). Den sjekker at det når hendelsesløkken og holder
seg oppe. Testen finnes fordi den første versjonen krasjet ved hver start, mens alle andre tester
var grønne. De lager alle en `QApplication` selv før vinduet bygges. Dermed hoppes over den ene
rekkefølgen en bruker faktisk gjør: avhengighetssjekken lager programmet først. En komponenttest som
lager sitt eget miljø kan ikke se en feil i hvordan miljøet settes opp.

### Fasit {#ground-truth}

- `tests/test_accuracy.py` - et syntetisk rom fra en kjent bane med analytisk dybde; se
  [Nivårekonstruksjon](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - veibredde, skalaen på banen, dekningsnettet lest mens det
  skrives, og hvorfor sløyfelukking er av.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - telemetrioppsettene, på pakker og sider
  bygd fra de dokumenterte strukturene, og rundefilene de skriver (kanalnavn i standardform,
  `meta`, ingen `NaN` i JSON). `tests/test_trackmania_plugin.py` leser kildekoden til Openplanet-
  pluginen for å se hva den skriver i beskrivelsen av hver kjøring.
- `tests/test_route_record.py` - `route`-filen ligger hel på disken før opptakeren stopper.
- `tests/test_telemetry_pose.py` - Forza-posisjoner i spillets egne koordinater, retningene for
  gir, stigning og rulling, og et telemetrihull som bindes visuelt i den speilvendte verdenen.
- `tests/test_glb.py` - GLB-kontrakten. Visningsprogrammets egne tester leser et referansenivå
  skrevet av denne skriveren, så formatet testes på begge sider.

### Sjekke en eksportert bane mot runder {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` sjekker at en bane eksportert av
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) faktisk ligger under den
innspilte bilen. Bilen skal stå en kjørehøyde over underlaget rett under seg. Pek testen på
stammen til en eksportert bane (`.glb`-filen og `.json`-filen ved siden av den):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

En bane med store hopp kan feile med vilje: bilen er i luften over underlag som faktisk finnes.

## Konvensjoner {#conventions}

- Kode under `heat3d_capture/` importerer tunge avhengigheter (OpenCV, ONNX Runtime, PyTorch, Qt)
  først inne i funksjoner. Dermed koster det ingenting å importere en modul, kjøre `--help` eller
  kjøre telemetriopptakerne.
- Arbeidstråder rører aldri Qt-elementer. Resultater sendes til grensesnitt-tråden som Qt-signaler.
- Opptak, rundefiler, masker, modellvekter og video holdes utenfor git av `.gitignore`, etter
  mappe og filtype.
- Commits og utgivelser: versjonen er filen `VERSION`. Utgivelser er GitHub-utgivelser i
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), som oppdateringen
  leser ([Oppdateringer](updates.md)).
