---
title: "Zhvillimi"
nav_order: 11
lang: "sq"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Zhvillimi {#development}

## Struktura e repozitorit {#repository-layout}

| Rruga | Përmbajtja |
|---|---|
| `heat3d_capture/__main__.py` | rreshti i komandave: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (struktura e Data Out), `fulllap.py` (skedarët e xhiros së Forzës, rele), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (dokumenti i përbashkët i xhiros) |
| `heat3d_capture/capture/` | `sources.py` (kapje e drejtpërdrejtë, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (ajo që ekzekuton skaneri), `estimator.py` (rruga me PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (shkruesi), `reference.py` (niveli sintetik i referencës) |
| `heat3d_capture/scan/` | `session.py` (një skanim), `reconstruct.py` (kuadrot kyç në gjeometri), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD-i i një regjistrimi - dritarja e pikëve, ekranet e vdekjes, shtegu në minihartë, lista e vrasjeve (`profiles.py` për çdo lojë) |
| `heat3d_capture/locate/` | `locate`: pamjet e nivelit, baza e të dhënave, përputhja, modeli për çdo hartë, miniharta |
| `heat3d_capture/ui/` | `__main__.py` (hyrja dhe kontrolli i varësive), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | kontrolli i botimeve dhe përditësuesi |
| `mods/beamng/heat3d/` | moduli i protokollit për BeamNG |
| `mods/trackmania/Heat3dRecorder/` | shtojca Openplanet |
| `tools/export_onnx.py` | konvertuesi i modelit të thellësisë |
| `tools/gen_docs_reference.py` | shkruan `docs/cli-reference.md` nga `--help`; `--check` tregon nëse është e vjetruar |
| `tools/docs_diagrams.py` | vizaton diagramet në `docs/assets/img/` (për çdo gjuhë me `--lang`) |
| `tools/sync_wiki.py` | rigjeneron `docs/wiki/` nga `docs/` |
| `models/` | skedarë `.onnx` të konvertuar (nuk ruhen në git) |
| `tests/` | grupi i testeve; `scene.py` dhe `track_scene.py` vizatojnë skena sintetike me gjeometri të njohur |
| `docs/` | ky dokumentacion; `docs/wiki/` gjenerohet prej tij |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logjika e skanimit nuk ka Qt brenda: `ScanSession` dhe `Reconstructor` marrin funksione të thjeshta
dhe mund të drejtohen nga një skript ose një test. Shembull:

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

## Mjedisi {#the-environment}

Projekti përdor një mjedis virtual në `.venv` (krijohet nga `scan.bat` ose me dorë). Testet
që prekin ndërfaqen kanë nevojë për **PySide6** në të, të cilin e instalon `requirements.txt`
si `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Për konvertuesin e modelit, testet e thellësisë me PyTorch dhe rrugën offline, instaloje PyTorch (të përshtatur me
GPU-në) **para** `requirements.txt`; pastaj `requirements-offline.txt` dhe rreshtin e tij `vggt` për
zgjidhësin offline, dhe `onnxscript` për konvertuesin. Shih
[Runtime dhe varësitë](runtime.md#installing-by-hand).

## Ekzekutimi i testeve {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` vendos `testpaths = tests` dhe heshtë `UserWarning`-et nga `huggingface_hub`. Grupi
ka disa qindra kontrolle; shumica nuk kanë nevojë as për lojë, as për GPU, as për pajisje kapjeje.

Çfarë e anashkalon vetveten, dhe pse:

| Testet | Anashkalohen kur |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testet që drejtojnë dritaren te `test_ui_drives_a_scan.py` | nuk ka `models/depth-*.onnx` - ekzekuto fillimisht `tools/export_onnx.py` |
| testet e vlerësuesit me GPU te `test_depth.py` | PyTorch nuk është instaluar, ose nuk ka pajisje CUDA; testet `fit_scale` dhe `AffineFit` ekzekutohen gjithsesi |
| disa raste të `test_offline.py` dhe `test_solveprep.py` | OpenCV nuk ka kodues videoje për të shkruar klipin sintetik |
| `test_hotkeys.py` | testet e regjistrimit kërkojnë Windows; testi rezervë ekzekutohet gjetkë |
| `test_course_ground.py` | `HEAT3D_COURSE` nuk është vendosur |
| disa teste të bashkimit | një rast sintetik nuk bashkoi asgjë |

### Testi i nisjes {#the-launch-test}

`tests/test_launch.py` ekzekuton pikën e vërtetë të hyrjes, `python -m heat3d_capture.ui`, si nënproces
(me `QT_QPA_PLATFORM=offscreen`) dhe kontrollon që arrin te cikli i ngjarjeve dhe mbetet ndezur. Ekziston
sepse ndërtimi i parë u prish në çdo nisje ndërsa të gjitha testet e tjera kalonin: ato krijojnë vetë
një `QApplication` dhe pastaj ndërtojnë dritaren, gjë që anashkalon të vetmen radhë hapash që kryen një
përdorues - kontrolli i varësive që krijon një aplikacion fillimisht. Një test komponenti që ndërton
mjedisin e vet nuk mund ta shohë një gabim në mënyrën si ndërtohet mjedisi.

### E vërteta e njohur {#ground-truth}

- `tests/test_accuracy.py` - një dhomë sintetike nga një shteg i njohur me thellësi analitike; shih
  [Rindërtimi i nivelit](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - gjerësia e rrugës, nxjerrja e shkallës së pistës, rrjeta e mbulimit
  e lexuar ndërsa shkruhet, dhe pse mbyllja e ciklit mbetet e fikur.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - strukturat e telemetrisë, mbi pakete dhe
  faqe të ndërtuara nga strukturat e dokumentuara, dhe skedarët e xhiros që shkruajnë (emrat kanonikë
  të kanaleve, `meta`, pa `NaN` në JSON). `tests/test_trackmania_plugin.py` lexon kodin burimor të
  shtojcës Openplanet për atë që shkruan në përshkrimin e çdo ecjeje.
- `tests/test_route_record.py` - skedari `route` është në disk, i plotë, para se regjistruesi të ndalojë.
- `tests/test_telemetry_pose.py` - pozat e Forzës në koordinatat e vetë lojës, kahet e yaw,
  pitch dhe roll, dhe një boshllëk telemetrie i mbushur vizualisht në botën e pasqyruar.
- `tests/test_glb.py` - kontrata GLB; testet e vetë shikuesit lexojnë një nivel referencë të shkruar
  nga ky shkrues, ndaj formati testohet nga të dyja anët.

### Kontrollimi i një kursi të eksportuar me xhirat {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` kontrollon që një kurs i eksportuar nga
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) shtrihet vërtet nën makinën e
regjistruar - makina duhet të qëndrojë një lartësi udhëtimi mbi sipërfaqen që është drejtpërdrejt poshtë saj.
Drejtoje te emri i një kursi të eksportuar (`.glb` dhe `.json` pranë tij):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Një kurs me kërcime të mëdha mund të dështojë me qëllim: makina është në ajër mbi tokë që ekziston.

## Konventat {#conventions}

- Kodi nën `heat3d_capture/` i importon varësitë e rënda (OpenCV, ONNX Runtime, PyTorch, Qt)
  me vonesë brenda funksioneve, ndaj importimi i një moduli, ekzekutimi i `--help` ose ekzekutimi i
  regjistruesve të telemetrisë nuk kushton asgjë.
- Fijet punëtore nuk prekin kurrë elementët e Qt; rezultatet kalojnë te fija e ndërfaqes si sinjale Qt.
- Regjistrimet, skedarët e xhirave, rrjetat, peshat e modeleve dhe videoja mbahen jashtë git nga `.gitignore`, sipas
  dosjes dhe llojit të skedarit.
- Commit-et dhe botimet: versioni është skedari `VERSION`; botimet janë botime në GitHub të
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), që i lexon
  përditësuesi ([Përditësimet](updates.md)).
