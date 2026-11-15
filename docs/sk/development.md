---
title: Vývoj
nav_order: 11
lang: "sk"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Vývoj {#development}

## Rozloženie repozitára {#repository-layout}

| Cesta | Obsah |
|---|---|
| `heat3d_capture/__main__.py` | príkazový riadok: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (rozloženie Data Out), `fulllap.py` (súbory kôl Forza, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (spoločný dokument kola) |
| `heat3d_capture/capture/` | `sources.py` (živé snímanie, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (čo spúšťa skener), `estimator.py` (cesta PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (zapisovač), `reference.py` (syntetický referenčný level) |
| `heat3d_capture/scan/` | `session.py` (jedno skenovanie), `reconstruct.py` (kľúčové snímky na geometriu), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD nahrávky - vyskakovacie okno bodov, obrazovky smrti, mini mapa trate, zoznam zabití (`profiles.py` pre každú hru) |
| `heat3d_capture/locate/` | `locate`: rendery levelu, databáza, párovanie, model pre každú mapu, mini mapa |
| `heat3d_capture/ui/` | `__main__.py` (vstup a kontrola závislostí), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | kontrola vydania a aktualizátor |
| `mods/beamng/heat3d/` | mod protokolu pre BeamNG |
| `mods/trackmania/Heat3dRecorder/` | zásuvný modul Openplanet |
| `tools/export_onnx.py` | konvertor modelu hĺbky |
| `tools/gen_docs_reference.py` | zapíše `docs/cli-reference.md` z `--help`; `--check` povie, či je zastaraný |
| `tools/docs_diagrams.py` | nakreslí diagramy do `docs/assets/img/` (pre každý jazyk s `--lang`) |
| `tools/sync_wiki.py` | znovu vytvorí `docs/wiki/` z `docs/` |
| `models/` | prevedené súbory `.onnx` (nie sú vo verziách) |
| `tests/` | súbor testov; `scene.py` a `track_scene.py` vykresľujú syntetické scény so známou geometriou |
| `docs/` | táto dokumentácia; `docs/wiki/` sa vytvára automaticky z nej |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skenovania nemá v sebe Qt: `ScanSession` a `Reconstructor` berú obyčajné volateľné
objekty a dajú sa riadiť zo skriptu alebo testu. Príklad:

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

## Prostredie {#the-environment}

Projekt používa virtuálne prostredie v `.venv` (vytvorí ho `scan.bat` alebo ručne). Testy, ktoré
pracujú s rozhraním, potrebujú **PySide6** v ňom; `requirements.txt` ho nainštaluje ako
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Pre konvertor modelu, testy hĺbky PyTorch a offline cestu nainštalujte PyTorch (podľa grafickej
karty) **pred** `requirements.txt`; potom `requirements-offline.txt` a jeho riadok `vggt` pre
offline riešiteľ a `onnxscript` pre konvertor. Pozrite
[Runtime a závislosti](runtime.md#installing-by-hand).

## Spustenie testov {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` nastavuje `testpaths = tests` a stíši `UserWarning` z `huggingface_hub`. Súbor má
niekoľko stoviek kontrol; väčšina nepotrebuje hru, grafickú kartu ani snímací hardvér.

Čo sa samo preskočí a prečo:

| Testy | Preskočia sa, keď |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testy ovládania okna v `test_ui_drives_a_scan.py` | chýba `models/depth-*.onnx` - najprv spustite `tools/export_onnx.py` |
| testy estimátora na GPU v `test_depth.py` | PyTorch nie je nainštalovaný alebo chýba zariadenie CUDA; testy `fit_scale` a `AffineFit` bežia vždy |
| niektoré prípady v `test_offline.py` a `test_solveprep.py` | OpenCV nemá video kodek na zápis syntetického klipu |
| `test_hotkeys.py` | testy registrácie potrebujú Windows; test záložného riešenia beží všade inde |
| `test_course_ground.py` | nie je nastavená premenná `HEAT3D_COURSE` |
| niektoré testy fúzie | syntetický prípad nespojil nič |

### Test spustenia {#the-launch-test}

`tests/test_launch.py` spustí skutočný vstupný bod, `python -m heat3d_capture.ui`, ako podproces
(s `QT_QPA_PLATFORM=offscreen`) a overí, že sa dostane do hlavnej slučky udalostí a zostane
spustený. Existuje preto, lebo prvá verzia padala pri každom spustení, hoci všetky ostatné testy
prechádzali: všetky si `QApplication` vytvárajú samy a až potom stavajú okno, čo preskočí
postupnosť, ktorú používateľ vykoná vždy - kontrolu závislostí, ktorá ako prvá vytvorí aplikáciu.
Test jednej časti, ktorý si vytvára vlastné prostredie, nevidí chybu v tom, ako sa prostredie
stavia.

### Overená pravda {#ground-truth}

- `tests/test_accuracy.py` - syntetická miestnosť z known cesty s analytickou hĺbkou; pozrite
  [Rekonštrukcia levelu](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - šírka cesty, extrakcia mierky trate, mriežka pokrytia čítaná
  počas zápisu a prečo zostáva uzavretie slučky vypnuté.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - rozloženia telemetrie na paketoch a
  stránkach postavených z dokumentovaných štruktúr, a súbory kôl, ktoré zapisujú (kanonické názvy
  kanálov, `meta`, žiadne `NaN` v JSON). `tests/test_trackmania_plugin.py` číta zdrojový kód
  zásuvného modulu Openplanet, aby zistil, čo zapisuje do popisu každého behu.
- `tests/test_route_record.py` - súbor `route` je celý na disku skôr, než sa nahrávač zastaví.
- `tests/test_telemetry_pose.py` - pózy Forza v súradniciach samotnej hry, zmysel yaw, pitch a
  roll a medzera v telemetrii preklenutá vizuálne v zrkadlovom svete.
- `tests/test_glb.py` - zmluva GLB; testy prehliadača parsujú referenčný level zapísaný týmto
  zapisovačom, takže formát je overený na oboch stranách.

### Kontrola exportovanej trate voči kolám {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` overí, že trať exportovaná cez
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) naozaj leží pod nahraným
autom - auto má byť vo výške jazdy nad povrchom priamo pod sebou. Nasmerujte ho na základ
názvu exportovanej trate (súbor `.glb` a `.json` vedľa neho):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Trať s veľkými skokmi môže zámerne zlyhať: auto je vo vzduchu nad terénom, ktorý tam skutočne je.

## Konvencie {#conventions}

- Kód pod `heat3d_capture/` importuje ťažké závislosti (OpenCV, ONNX Runtime, PyTorch, Qt)
  lenivo, až vnútri funkcií, takže import modulu, spustenie `--help` alebo spustenie nahrávačov
  telemetrie nestojí nič.
- Pracovné vlákna sa nikdy nedotýkajú Qt widgetov; výsledky prechádzajú do vlákna rozhrania ako
  signály Qt.
- Nahrávky, súbory kôl, siete, váhy modelov a video drží mimo gitu súbor `.gitignore` - podľa
  priečinka aj podľa typu súboru.
- Verzie a vydania: verzia je v súbore `VERSION`; vydania sú GitHub releases repozitára
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), ktoré číta
  aktualizátor ([Aktualizácie](updates.md)).
