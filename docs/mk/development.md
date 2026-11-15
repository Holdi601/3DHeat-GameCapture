---
title: "Развој"
nav_order: 11
lang: "mk"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Развој {#development}

## Распоред на складиштето {#repository-layout}

| Патека | Содржина |
|---|---|
| `heat3d_capture/__main__.py` | командната линија: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (распоредот на Data Out), `fulllap.py` (датотеки на кругови од Forza, релеј), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (заедничкиот документ на кругот) |
| `heat3d_capture/capture/` | `sources.py` (снимање во живо, видео), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (она што го извршува скенерот), `estimator.py` (патеката со PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (пишувачот), `reference.py` (синтетичко референтно ниво) |
| `heat3d_capture/scan/` | `session.py` (едно скенирање), `reconstruct.py` (клучните рамки во геометрија), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD-от на една снимка - скокачкиот прозорец со поени, екраните при смрт, мини-мапата со патеката, листата на убиства (`profiles.py` по игра) |
| `heat3d_capture/locate/` | `locate`: рендерите на нивото, базата на податоци, совпаѓањето, моделот по мапа, мини-мапата |
| `heat3d_capture/ui/` | `__main__.py` (влез и проверка на зависности), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | проверката за издание и ажурирачот |
| `mods/beamng/heat3d/` | протоколниот мод за BeamNG |
| `mods/trackmania/Heat3dRecorder/` | приклучокот за Openplanet |
| `tools/export_onnx.py` | претворувачот на моделот за длабочина |
| `tools/gen_docs_reference.py` | ја пишува `docs/cli-reference.md` од `--help`; `--check` кажува дали е застарена |
| `tools/docs_diagrams.py` | ги црта дијаграмите во `docs/assets/img/` (по јазик со `--lang`) |
| `tools/sync_wiki.py` | го создава `docs/wiki/` одново од `docs/` |
| `models/` | претворените `.onnx` датотеки (не се во верзионирањето) |
| `tests/` | збирката тестови; `scene.py` и `track_scene.py` рендерираат синтетички сцени со позната геометрија |
| `docs/` | оваа документација; `docs/wiki/` се создава од неа |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Логиката на скенирањето нема Qt во себе: `ScanSession` и `Reconstructor` примаат обични
функции и може да се водат од скрипта или од тест. Пример:

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

## Околината {#the-environment}

Проектот користи виртуелна околина во `.venv` (ја создава `scan.bat` или рачно). Тестовите
што го допираат интерфејсот бараат **PySide6** во неа, што го инсталира `requirements.txt` како
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

За претворувачот на моделот, PyTorch тестовите за длабочина и офлајн патеката, инсталирајте
PyTorch (прилагоден на графичката картичка) **пред** `requirements.txt`; потоа
`requirements-offline.txt` и неговата линија `vggt` за офлајн решавачот, и `onnxscript` за
претворувачот. Видете [Извршна околина и зависности](runtime.md#installing-by-hand).

## Извршување на тестовите {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` поставува `testpaths = tests` и ги замолчува `UserWarning`-ите од `huggingface_hub`.
Збирката има неколку стотици проверки; повеќето не бараат ни игра, ни графичка картичка, ни
опрема за снимање.

Што се прескокнува само и зошто:

| Тестови | Се прескокнуваат кога |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, тестовите што го возат прозорецот во `test_ui_drives_a_scan.py` | нема `models/depth-*.onnx` - прво извршете `tools/export_onnx.py` |
| тестовите за GPU проценувачот во `test_depth.py` | PyTorch не е инсталиран или нема CUDA уред; тестовите `fit_scale` и `AffineFit` се извршуваат во секој случај |
| некои случаи во `test_offline.py` и `test_solveprep.py` | OpenCV нема видео енкодер за да ја запише синтетичката снимка |
| `test_hotkeys.py` | тестовите за регистрација бараат Windows; тестот за резервниот пат се извршува и на друго место |
| `test_course_ground.py` | `HEAT3D_COURSE` не е поставена |
| неколку тестови за спојување | синтетичкиот случај не спојал ништо |

### Тестот за стартување {#the-launch-test}

`tests/test_launch.py` ја извршува вистинската влезна точка, `python -m heat3d_capture.ui`, како
подпроцес (со `QT_QPA_PLATFORM=offscreen`) и проверува дали стигнува до јамката на настани и
останува жива. Постои затоа што првата верзија паѓаше при секое стартување, додека сите други
тестови поминуваа: сите тие сами создаваат `QApplication` и потоа го градат прозорецот, со што
го прескокнуваат единствениот редослед што го прави корисникот - проверката на зависности
прво создава апликација. Тест на компонента што сам си ја гради околината не може да види
грешка во начинот на кој се гради околината.

### Вистинити референтни податоци {#ground-truth}

- `tests/test_accuracy.py` - синтетичка соба од позната патека со аналитичка длабочина; видете
  [Реконструкција на ниво](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - ширина на патот, извлекување на размерот на патеката,
  мрежата на покриеност читана додека се пишува, и зошто затворањето на јамката останува
  исклучено.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - распоредите на телеметријата, на пакети
  и страници изградени според документираните структури, и датотеките на кругови што ги пишуваат
  (канонски имиња на канали, `meta`, без `NaN` во JSON). `tests/test_trackmania_plugin.py` го
  чита изворниот код на приклучокот за Openplanet за да види што запишува во описот на секое
  возење.
- `tests/test_route_record.py` - датотеката `route` е на диск, цела, пред снимачот да запре.
- `tests/test_telemetry_pose.py` - позиции на Forza во сопствените координати на играта,
  насоките на вртење (yaw, pitch, roll), и празнина во телеметријата премостена визуелно во
  огледалниот свет.
- `tests/test_glb.py` - договорот за GLB; тестовите на самиот прегледувач парсираат референтно
  ниво запишано од овој пишувач, па форматот се тестира од двете страни.

### Проверка на извезена патека наспроти кругови {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` проверува дали патека извезена од
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) навистина лежи под снимениот
автомобил - автомобилот треба да седи на висина на возењето над површината директно под него.
Упатете го на името (без наставка) на извезената патека (`.glb` и неговиот `.json` до него):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Патека со големи скокови може да падне по дизајн: автомобилот е во воздух над земја што си е
тука.

## Договори {#conventions}

- Кодот под `heat3d_capture/` ги увезува тешките зависности (OpenCV, ONNX Runtime, PyTorch, Qt)
  доцна, во функциите, па увезувањето на модул, извршувањето на `--help` или извршувањето на
  снимачите на телеметрија не чини ништо.
- Работните нишки никогаш не допираат Qt елементи; резултатите стигнуваат до нишката на
  интерфејсот како Qt сигнали.
- Снимките, датотеките на кругови, мрежите, тежините на моделите и видеото се држат надвор од
  git со `.gitignore`, по папка и по тип на датотека.
- Комити и изданија: верзијата е датотеката `VERSION`; изданијата се GitHub изданија на
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), кои ги чита
  ажурирачот ([Ажурирања](updates.md)).
