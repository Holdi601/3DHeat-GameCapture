---
title: "Развој"
nav_order: 11
lang: "sr"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Развој {#development}

## Распоред репозиторијума {#repository-layout}

| Путања | Садржај |
|---|---|
| `heat3d_capture/__main__.py` | командна линија: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (распоред Data Out), `fulllap.py` (датотеке кругова за Forza, релеј), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (заједнички документ круга) |
| `heat3d_capture/capture/` | `sources.py` (снимање уживо, видео), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (оно што скенер покреће), `estimator.py` (PyTorch путања, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (писац), `reference.py` (синтетички референтни ниво) |
| `heat3d_capture/scan/` | `session.py` (скенирање), `reconstruct.py` (кључни кадрови у геометрију), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD снимка - искачући прозор поена, екрани смрти, мини-мапа стазе, списак убистава (`profiles.py` за сваку игру) |
| `heat3d_capture/locate/` | `locate`: рендери нивоа, база, поређење, модел по мапи, мини-мапа |
| `heat3d_capture/ui/` | `__main__.py` (улаз и провера зависности), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | провера издања и ажурирање |
| `mods/beamng/heat3d/` | модификација протокола за BeamNG |
| `mods/trackmania/Heat3dRecorder/` | Openplanet додатак |
| `tools/export_onnx.py` | претварач модела дубине |
| `tools/gen_docs_reference.py` | пише `docs/cli-reference.md` из `--help`; `--check` каже да ли је застарео |
| `tools/docs_diagrams.py` | црта дијаграме у `docs/assets/img/` (по језику с `--lang`) |
| `tools/sync_wiki.py` | поново прави `docs/wiki/` из `docs/` |
| `models/` | претворени `.onnx` фајлови (нису под контролом верзија) |
| `tests/` | скуп тестова; `scene.py` и `track_scene.py` исцртавају синтетичке сцене познате геометрије |
| `docs/` | ова документација; `docs/wiki/` се прави из ње |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Логика скенирања нема Qt: `ScanSession` и `Reconstructor` узимају обичне функције и могу се покретати из скрипте или теста. Пример:

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

## Окружење {#the-environment}

Пројекат користи виртуелно окружење у `.venv` (прави га `scan.bat` или ручно). Тестовима који дирају интерфејс потребан је **PySide6** у њему, који `requirements.txt` инсталира као `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

За претварач модела, тестове дубине с PyTorch-ом и офлајн путању инсталирајте PyTorch (прилагођен GPU-у) **пре** `requirements.txt`; затим `requirements-offline.txt` и његов ред `vggt` за офлајн решавач, и `onnxscript` за претварач. Погледајте [Покретање и зависности](runtime.md#installing-by-hand).

## Покретање тестова {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` поставља `testpaths = tests` и утишава `UserWarning` упозорења из `huggingface_hub`. Скуп има неколико стотина провера; већини не треба ни игра, ни GPU, ни уређај за снимање.

Шта се само прескаче, и зашто:

| Тестови | Прескачу се кад |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, тестови управљања прозором у `test_ui_drives_a_scan.py` | нема `models/depth-*.onnx` - прво покрените `tools/export_onnx.py` |
| GPU тестови процењивача у `test_depth.py` | PyTorch није инсталиран или нема CUDA уређаја; тестови `fit_scale` и `AffineFit` раде увек |
| неки случајеви у `test_offline.py` и `test_solveprep.py` | OpenCV нема видео кодер за писање синтетичког клипа |
| `test_hotkeys.py` | тестови регистрације траже Windows; тест резерве ради на осталима |
| `test_course_ground.py` | `HEAT3D_COURSE` није постављен |
| неки тестови спајања | синтетички случај ништа није спојио |

### Тест покретања {#the-launch-test}

`tests/test_launch.py` покреће прави улазни процес, `python -m heat3d_capture.ui`, као подпроцес (с `QT_QPA_PLATFORM=offscreen`) и проверава да дође до петље догађаја и остане жив. Постоји зато што је први build пуцао при сваком покретању док су сви остали тестови пролазили: сви они сами праве `QApplication` и затим граде прозор, чиме прескачу низ корака који корисник заиста извршава - провера зависности прво прави апликацију. Тест компоненте који сам прави своје окружење не може да види грешку у томе како се окружење прави.

### Основна истина {#ground-truth}

- `tests/test_accuracy.py` - синтетичка соба из познате путање с аналитичком дубином; погледајте [Реконструкција нивоа](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - ширина пута, издвајање размере стазе, мрежа покривености читана док се пише, и зашто затварање петље остаје искључено.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - распореди телеметрије, на пакетима и страницама састављеним од документованих структура, и датотеке кругова које пишу (канонична имена канала, `meta`, без `NaN` у JSON-у). `tests/test_trackmania_plugin.py` чита изворни код Openplanet додатка за оно што он уписује у опис сваке вожње.
- `tests/test_route_record.py` - датотека `route` је на диску, цела, пре него што снимач стане.
- `tests/test_telemetry_pose.py` - Forza положаји у координатама саме игре, смерови yaw, pitch и roll, и празнина у телеметрији премошћена визуелно у огледалном свету.
- `tests/test_glb.py` - GLB уговор; сопствени тестови прегледача рашчлањују референтни ниво који је написао овај писац, па се формат тестира с обе стране.

### Провера извезеног курса према круговима {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` проверава да курс извезен помоћу [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) заиста лежи испод снимљеног аутомобила - аутомобил треба да буде на висини вожње изнад површине непосредно испод себе. Упутите га на основу извезеног курса (`.glb` и његов `.json` уз њега):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Курс с великим скоковима може намерно да падне: аутомобил је у ваздуху изнад тла које постоји.

## Конвенције {#conventions}

- Код под `heat3d_capture/` увози тешке зависности (OpenCV, ONNX Runtime, PyTorch, Qt) тек унутар функција, па увоз модула, покретање `--help` или снимача телеметрије ништа не кошта.
- Радне нити никад не дирају Qt widget-е; резултати прелазе на нит интерфејса као Qt сигнали.
- Снимци, датотеке кругова, мреже, тежине модела и видео су ван git-а преко `.gitignore`, по фасцикли и по врсти фајла.
- Комитови и издања: верзија је датотека `VERSION`; издања су GitHub издања [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), која ажуриратељ чита ([Ажурирања](updates.md)).
