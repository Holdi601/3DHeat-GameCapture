---
title: "Разработка"
nav_order: 11
lang: "bg"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Разработка {#development}

## Структура на хранилището {#repository-layout}

| Път | Съдържание |
|---|---|
| `heat3d_capture/__main__.py` | командният ред: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (разположението на Data Out), `fulllap.py` (файлове с обиколки от Forza, релей), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (общият документ за обиколка) |
| `heat3d_capture/capture/` | `sources.py` (заснемане на живо, видео), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (това, което изпълнява сканерът), `estimator.py` (път през PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (записвачът), `reference.py` (синтетично еталонно ниво) |
| `heat3d_capture/scan/` | `session.py` (едно сканиране), `reconstruct.py` (ключови кадри в геометрия), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD на записа - изскачащ прозорец с точките, екрани при смърт, трасето в миникарта, поток от убийства (`profiles.py` за всяка игра) |
| `heat3d_capture/locate/` | `locate`: изображенията на нивото, базата данни, съпоставянето, моделът за всяка карта, миникартата |
| `heat3d_capture/ui/` | `__main__.py` (вход и проверка на зависимостите), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | проверката за издания и актуализаторът |
| `mods/beamng/heat3d/` | модът с протокол за BeamNG |
| `mods/trackmania/Heat3dRecorder/` | приставката за Openplanet |
| `tools/export_onnx.py` | конвертор на модела за дълбочина |
| `tools/gen_docs_reference.py` | записва `docs/cli-reference.md` от `--help`; `--check` казва дали е остарял |
| `tools/docs_diagrams.py` | рисува диаграмите в `docs/assets/img/` (за всеки език с `--lang`) |
| `tools/sync_wiki.py` | пресъздава `docs/wiki/` от `docs/` |
| `models/` | конвертирани `.onnx` файлове (не са под версиите) |
| `tests/` | наборът от тестове; `scene.py` и `track_scene.py` изобразяват синтетични сцени с известна геометрия |
| `docs/` | тази документация; `docs/wiki/` се генерира от нея |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

В логиката на сканирането няма Qt: `ScanSession` и `Reconstructor` приемат обикновени извиквани функции и могат да се управляват от скрипт или тест. Пример:

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

## Средата {#the-environment}

Проектът използва виртуална среда в `.venv` (създава се от `scan.bat` или ръчно). Тестовете, които пипат интерфейса, се нуждаят от **PySide6** в нея; `requirements.txt` я инсталира като `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

За конвертора на модела, тестовете за дълбочина с PyTorch и офлайн пътя инсталирайте PyTorch (съгласуван с графичната карта) **преди** `requirements.txt`; после `requirements-offline.txt` и реда му `vggt` за офлайн решателя, и `onnxscript` за конвертора. Вижте [Работна среда и зависимости](runtime.md#installing-by-hand).

## Пускане на тестовете {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` задава `testpaths = tests` и заглушава `UserWarning` съобщенията от `huggingface_hub`. Наборът има няколко стотин проверки; повечето не се нуждаят нито от игра, нито от графична карта, нито от хардуер за заснемане.

Какво се пропуска само, и защо:

| Тестове | Пропускат се, когато |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, тестовете за управление на прозореца в `test_ui_drives_a_scan.py` | няма `models/depth-*.onnx` - първо пуснете `tools/export_onnx.py` |
| тестовете на оценителя с графичната карта в `test_depth.py` | PyTorch не е инсталиран или няма CUDA устройство; тестовете за `fit_scale` и `AffineFit` се пускат във всеки случай |
| някои случаи в `test_offline.py` и `test_solveprep.py` | OpenCV няма видеокодиращо устройство, с което да запише синтетичния клип |
| `test_hotkeys.py` | тестовете за регистрация се нуждаят от Windows; резервният тест се пуска на други системи |
| `test_course_ground.py` | `HEAT3D_COURSE` не е зададена |
| няколко теста за сливане | синтетичен случай не е слял нищо |

### Тестът за стартиране {#the-launch-test}

`tests/test_launch.py` пуска истинската входна точка, `python -m heat3d_capture.ui`, като отделен процес (с `QT_QPA_PLATFORM=offscreen`) и проверява, че тя достига цикъла на събитията и остава работеща. Съществува, защото първата версия се срива при всяко стартиране, докато всички останали тестове минаваха: всички те сами създават `QApplication` и после строят прозореца, което пропуска единствената последователност, която извършва потребителят - проверката на зависимостите, която първо създава приложение. Компонентен тест, който сам изгражда своята среда, не може да види грешка в начина, по който се изгражда средата.

### Еталонни данни {#ground-truth}

- `tests/test_accuracy.py` - синтетична стая по известен път с аналитична дълбочина; вижте [Реконструкция на ниво](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - ширина на пътя, извличане на мащаба на трасето, мрежата на покритието, прочитана докато се записва, и защо затварянето на контура остава изключено.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - разположенията на телеметрията, върху пакети и страници, изградени по документираните структури, и файловете с обиколки, които записват (канонични имена на канали, `meta`, без `NaN` в JSON). `tests/test_trackmania_plugin.py` чете изходния код на приставката за Openplanet, за да види какво записва в описанието на всяко записано състезание.
- `tests/test_route_record.py` - файлът `route` е на диска цял, преди записващият уред да спре.
- `tests/test_telemetry_pose.py` - позите във Forza в собствените координати на играта, посоките на yaw, pitch и roll, и празнина в телеметрията, преодоляна визуално в огледалния свят.
- `tests/test_glb.py` - договорът за GLB; собствените тестове на визуализатора четат еталонно ниво, записано от този записвач, така че форматът се тества от двете страни.

### Проверка на експортиран курс спрямо обиколки {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` проверява дали курс, експортиран от [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles), наистина лежи под записаната кола - колата трябва да е на височината на просвета над повърхността точно под нея. Насочете го към основата на експортиран курс (`.glb` и `.json` до него):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Курс с големи скокове може да се провали по замисъл: колата е във въздуха над земя, която съществува.

## Правила {#conventions}

- Кодът в `heat3d_capture/` зарежда тежките зависимости (OpenCV, ONNX Runtime, PyTorch, Qt) при нужда, вътре във функциите, така че импортирането на модул, пускането на `--help` или на записващите уреди за телеметрия не струва нищо.
- Работните нишки никога не пипат Qt елементи; резултатите стигат до нишката на интерфейса като Qt сигнали.
- Записите, файловете с обиколки, мрежите, теглата на моделите и видеото са извадени от git чрез `.gitignore`, по папка и по тип файл.
- Подавания и издания: версията е файлът `VERSION`; изданията са GitHub издания на [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), които актуализаторът чете ([Обновления](updates.md)).
