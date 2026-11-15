---
title: Fejlesztés
nav_order: 11
lang: "hu"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Fejlesztés {#development}

## Tárolószerkezet {#repository-layout}

| Útvonal | Tartalom |
|---|---|
| `heat3d_capture/__main__.py` | a parancssor: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out elrendezés), `fulllap.py` (Forza körfájlok, továbbító), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (a közös körfájl-dokumentum) |
| `heat3d_capture/capture/` | `sources.py` (élő rögzítés, videó), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (amit a szkenner futtat), `estimator.py` (PyTorch útvonal, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (az író), `reference.py` (szintetikus referenciapálya) |
| `heat3d_capture/scan/` | `session.py` (egy szkennelés), `reconstruct.py` (kulcskockákból geometria), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: a felvétel HUD-ja - pontpopup, halálképernyők, kis térkép a pályával, gyilkossági napló (`profiles.py` játékonként) |
| `heat3d_capture/locate/` | `locate`: a pálya renderjei, az adatbázis, az illesztés, a pályánkénti modell, a kis térkép |
| `heat3d_capture/ui/` | `__main__.py` (belépés és függőségellenőrzés), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | a kiadás-ellenőrzés és a frissítő |
| `mods/beamng/heat3d/` | a BeamNG protokollmódosítás |
| `mods/trackmania/Heat3dRecorder/` | az Openplanet-bővítmény |
| `tools/export_onnx.py` | a mélységmodell-konvertáló |
| `tools/gen_docs_reference.py` | a `docs/cli-reference.md` fájlt írja a `--help` alapján; a `--check` megmondja, ha elavult |
| `tools/docs_diagrams.py` | rajzolja a diagramokat a `docs/assets/img/` mappába (nyelvenként a `--lang` kapcsolóval) |
| `tools/sync_wiki.py` | újragenerálja a `docs/wiki/` mappát a `docs/` alapján |
| `models/` | átalakított `.onnx` fájlok (nincs verziókezelve) |
| `tests/` | a tesztcsomag; a `scene.py` és a `track_scene.py` ismert geometriájú szintetikus jeleneteket renderel |
| `docs/` | ez a dokumentáció; a `docs/wiki/` ebből készül |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

A szkennelési logika nem tartalmaz Qt-t: a `ScanSession` és a `Reconstructor` sima függvényeket
kap, így szkriptből vagy tesztből is vezérelhető. Példa:

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

## A környezet {#the-environment}

A projekt a `.venv` virtuális környezetet használja (a `scan.bat` hozza létre, vagy kézzel). A
felülettel kapcsolatos tesztekhez ebben kell a **PySide6**, amit a `requirements.txt`
`PySide6-Essentials` néven telepít:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

A modellkonvertálóhoz, a PyTorch-mélységi teszteknél és az offline útvonalnál a PyTorchot (a GPU-hoz
illeszkedő verzióban) telepítse **a** `requirements.txt` **előtt**. Utána jöhet a
`requirements-offline.txt` és annak `vggt` sora az offline megoldóhoz, valamint az `onnxscript` a
konvertálóhoz. Lásd: [Futtatókörnyezet és függőségek](runtime.md#installing-by-hand).

## A tesztek futtatása {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

A `pytest.ini` a `testpaths = tests` értéket állítja be, és elnémítja a `huggingface_hub`
`UserWarning` figyelmeztetéseit. A tesztcsomag több száz ellenőrzést tartalmaz; a legtöbbhöz nincs
szükség játékra, GPU-ra vagy rögzítő hardverre.

Mely tesztek hagyják ki magukat, és miért:

| Tesztek | Kihagyás, ha |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, a `test_ui_drives_a_scan.py` ablakvezérlő tesztjei | nincs `models/depth-*.onnx` - előbb futtassa a `tools/export_onnx.py` parancsot |
| a `test_depth.py` GPU-s becslő tesztjei | nincs telepítve a PyTorch, vagy nincs CUDA-eszköz; a `fit_scale` és az `AffineFit` tesztek mindig lefutnak |
| néhány `test_offline.py` és `test_solveprep.py` eset | az OpenCV-ben nincs videókódoló a szintetikus klip írásához |
| `test_hotkeys.py` | a regisztrációs tesztekhez Windows kell; a tartalék teszt máshol is fut |
| `test_course_ground.py` | a `HEAT3D_COURSE` nincs beállítva |
| néhány fúziós teszt | egy szintetikus eset sem fúzionált semmit |

### Az indítási teszt {#the-launch-test}

A `tests/test_launch.py` a valódi belépési pontot, a `python -m heat3d_capture.ui` parancsot futtatja
külön folyamatként (`QT_QPA_PLATFORM=offscreen` beállítással), és ellenőrzi, hogy eléri az
eseményhurkot, és ott is marad. Azért van, mert az első build minden indításkor összeomlott, miközben
minden más teszt zöld volt: ezek mind maguk hoznak létre `QApplication`-t, majd építik fel az ablakot.
Így kimarad az egyetlen sorrend, amelyet a felhasználó valóban végigjár: a függőségellenőrzés először
alkalmazást hoz létre. Egy komponensteszt, amely saját környezetet épít, nem láthat hibát abban, ahogyan
a környezet épül.

### Referenciaadatok (ground truth) {#ground-truth}

- `tests/test_accuracy.py` - ismert útvonalról nézett szintetikus szoba, analitikus mélységgel; lásd
  [Pályarekonstrukció](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - útszélesség, pályaméret-kinyerés, az írás közben olvasott
  lefedettségi rács, és az, hogy a hurokzárás miért marad kikapcsolva.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - a telemetriai elrendezések, a dokumentált
  szerkezetekből épített csomagokon és oldalakon, valamint az általuk írt körfájlok (kanonikus csatornanevek,
  `meta`, nincs `NaN` a JSON-ban). A `tests/test_trackmania_plugin.py` az Openplanet-bővítmény forrását
  olvassa, hogy megnézze, mit ír az egyes futások leírásába.
- `tests/test_route_record.py` - a `route` fájl teljes egészében a lemezen van, mielőtt a rögzítő leáll.
- `tests/test_telemetry_pose.py` - Forza-pozíciók a játék saját koordinátáiban, a yaw, a pitch és a roll
  irányai, és egy telemetriai rés, amelyet vizuálisan hidalunk át a tükrözött világban.
- `tests/test_glb.py` - a GLB-szerződés; a megjelenítő saját tesztjei ezen író által írt referenciapályát
  olvassák be, így a formátum mindkét oldalon tesztelve van.

### Exportált pálya ellenőrzése körökkel {#checking-an-exported-course-against-laps}

A `tests/test_course_ground.py` ellenőrzi, hogy a [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
által exportált pálya valóban a rögzített autó alatt fekszik-e: az autónak a felszín felett egy
futómagasságnyira kell lennie az alatta lévő talajtól. Adja meg az exportált pálya törzsnevét (a `.glb` és
mellette lévő `.json`):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Nagy ugrásokat tartalmazó pálya tervszerűen elbukhat: az autó a levegőben van olyan talaj felett, amely
valóban ott van.

## Konvenciók {#conventions}

- A `heat3d_capture/` alatti kód a nehéz függőségeket (OpenCV, ONNX Runtime, PyTorch, Qt) a függvényeken
  belül tölti be, így egy modul importálása, a `--help` futtatása vagy a telemetriai rögzítők indítása
  nem kerül semmibe.
- A háttérszálak sosem nyúlnak Qt-widgetekhez; az eredmények Qt-jelzésekként jutnak el a felületi szálhoz.
- A felvételeket, a körfájlokat, a hálókat, a modellsúlyokat és a videókat a `.gitignore` tartja ki a git-ből,
  mappa és fájltípus szerint.
- Kiadások: a verziót a `VERSION` fájl adja; a kiadások a
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) GitHub-kiadásai, amelyeket a
  frissítő olvas ([Frissítések](updates.md)).
