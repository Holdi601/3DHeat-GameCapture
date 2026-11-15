---
title: Vývoj
nav_order: 11
lang: "cs"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Vývoj {#development}

## Rozložení repozitáře {#repository-layout}

| Cesta | Obsah |
|---|---|
| `heat3d_capture/__main__.py` | příkazový řádek: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (rozložení Data Out), `fulllap.py` (soubory kol Forzy, přeposílání), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (sdílený dokument kola) |
| `heat3d_capture/capture/` | `sources.py` (živé zachytávání, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (co spouští skener), `estimator.py` (cesta PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (zapisovatel), `reference.py` (syntetická referenční úroveň) |
| `heat3d_capture/scan/` | `session.py` (sken), `reconstruct.py` (klíčové snímky na geometrii), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD záznamu – vyskakovací okno bodů, obrazovky smrti, minimapa trati, seznam zabití (`profiles.py` pro každou hru) |
| `heat3d_capture/locate/` | `locate`: vykreslení úrovně, databáze, párování, model pro každou mapu, minimapa |
| `heat3d_capture/ui/` | `__main__.py` (vstup a kontrola závislostí), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | kontrola vydání a aktualizátor |
| `mods/beamng/heat3d/` | protokolový mod pro BeamNG |
| `mods/trackmania/Heat3dRecorder/` | plugin pro Openplanet |
| `tools/export_onnx.py` | převodník modelu hloubky |
| `tools/gen_docs_reference.py` | zapisuje `docs/cli-reference.md` z `--help`; `--check` říká, zda je zastaralý |
| `tools/docs_diagrams.py` | kreslí diagramy do `docs/assets/img/` (pro každý jazyk s `--lang`) |
| `tools/sync_wiki.py` | znovu vytvoří `docs/wiki/` z `docs/` |
| `models/` | převedené soubory `.onnx` (nejsou ve správě verzí) |
| `tests/` | sada testů; `scene.py` a `track_scene.py` vykreslují syntetické scény se známou geometrií |
| `docs/` | tato dokumentace; `docs/wiki/` se generuje z ní |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skenování nemá žádné Qt: `ScanSession` a `Reconstructor` berou obyčejné funkce a dají se řídit ze skriptu nebo z testu. Příklad:

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

## Prostředí {#the-environment}

Projekt používá virtuální prostředí v `.venv` (vytvořené `scan.bat` nebo ručně). Testy, které pracují s rozhraním, potřebují **PySide6**, který `requirements.txt` instaluje jako `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Pro převodník modelu, testy hloubky v PyTorch a offline cestu nainstalujte PyTorch (podle grafické karty) **před** `requirements.txt`; potom `requirements-offline.txt` a jeho řádek `vggt` pro offline řešitele a `onnxscript` pro převodník. Viz [Běh a závislosti](runtime.md#installing-by-hand).

## Spouštění testů {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` nastavuje `testpaths = tests` a potlačuje varování `UserWarning` z `huggingface_hub`. Sada má několik stovek kontrol; většina nepotřebuje hru, GPU ani záznamový hardware.

Co se přeskočí a proč:

| Testy | Přeskočí se, když |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testy řízení okna v `test_ui_drives_a_scan.py` | chybí `models/depth-*.onnx` – nejdřív spusťte `tools/export_onnx.py` |
| testy estimátoru na GPU v `test_depth.py` | PyTorch není nainstalovaný, nebo chybí zařízení CUDA; testy `fit_scale` a `AffineFit` běží vždy |
| některé případy v `test_offline.py` a `test_solveprep.py` | OpenCV nemá kodér videa pro zápis syntetického klipu |
| `test_hotkeys.py` | testy registrace potřebují Windows; test záložní varianty běží jinde |
| `test_course_ground.py` | není nastavené `HEAT3D_COURSE` |
| několik testů fúze | syntetický případ nic nesloučil |

### Test spuštění {#the-launch-test}

`tests/test_launch.py` spustí skutečný vstupní bod, `python -m heat3d_capture.ui`, jako podproces (s `QT_QPA_PLATFORM=offscreen`) a ověří, že se dostane do smyčky událostí a zůstane běžet. Vznikl proto, že první sestavení se při každém spuštění zhroutilo, zatímco všechny ostatní testy prošly. Ty si `QApplication` vytvářejí samy a teprve potom sestaví okno, takže přeskočí jedinou posloupnost, kterou uživatel provede: kontrolu závislostí, která jako první vytvoří aplikaci. Test komponenty, který si sestaví vlastní prostředí, nemůže vidět chybu v tom, jak se prostředí sestavuje.

### Referenční data {#ground-truth}

- `tests/test_accuracy.py` – syntetická místnost ze známé cesty s analytickou hloubkou; viz [Rekonstrukce úrovně](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` – šířka silnice, získání měřítka trati, mřížka pokrytí čtená během zápisu a důvod, proč zůstává uzavírání smyčky vypnuté.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` – rozložení telemetrie na paketech a stránkách sestavených z dokumentovaných struktur a soubory kol, které zapisují (kanonické názvy kanálů, `meta`, žádné `NaN` v JSON). `tests/test_trackmania_plugin.py` čte zdrojový kód pluginu Openplanet a zjišťuje, co zapisuje do popisu každého běhu.
- `tests/test_route_record.py` – soubor `route` je celý na disku dřív, než se záznamník zastaví.
- `tests/test_telemetry_pose.py` – pózy Forzy v souřadnicích samotné hry, smysl yaw, pitch a roll a mezera v telemetrii přemostěná vizuálně v zrcadlovém světě.
- `tests/test_glb.py` – smlouva GLB; testy prohlížeče parsují referenční úroveň zapsanou tímto zapisovatelem, takže formát je testovaný na obou stranách.

### Kontrola exportovaného kurzu vůči kolům {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` ověřuje, že kurz exportovaný z [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) skutečně leží pod zaznamenaným autem. Auto má být ve výšce jízdy nad povrchem přímo pod sebou. Ukažte ho na exportovaný kurz (soubor `.glb` a k němu `.json` vedle něj):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Kurz s velkými skoky může selhat záměrně: auto je ve vzduchu nad terénem, který tam skutečně je.

## Konvence {#conventions}

- Kód v `heat3d_capture/` importuje těžké závislosti (OpenCV, ONNX Runtime, PyTorch, Qt) líně, uvnitř funkcí, takže import modulu, spuštění `--help` nebo běh záznamníků telemetrie nic nestojí.
- Pracovní vlákna se nikdy nedotýkají widgetů Qt; výsledky přecházejí do vlákna rozhraní jako signály Qt.
- Záznamy, soubory kol, sítě, váhy modelů a video drží `.gitignore` mimo git – podle složky i podle typu souboru.
- Commity a vydání: verze je v souboru `VERSION`; vydání jsou GitHub releases repozitáře [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), které čte aktualizátor ([Aktualizace](updates.md)).
