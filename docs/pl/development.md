---
title: "Rozwój"
nav_order: 11
lang: "pl"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Rozwój {#development}

## Układ repozytorium {#repository-layout}

| Ścieżka | Zawartość |
|---|---|
| `heat3d_capture/__main__.py` | wiersz poleceń: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (układ Data Out), `fulllap.py` (pliki okrążeń Forzy, przekaźnik), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (wspólny dokument okrążenia) |
| `heat3d_capture/capture/` | `sources.py` (przechwytywanie na żywo, wideo), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (to, co uruchamia skaner), `estimator.py` (ścieżka PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (zapis), `reference.py` (syntetyczny poziom wzorcowy) |
| `heat3d_capture/scan/` | `session.py` (skan), `reconstruct.py` (klatki kluczowe w geometrię), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD nagrania - okienko punktów, ekrany śmierci, ślad z minimapy, kanał zabójstw (`profiles.py` dla każdej gry) |
| `heat3d_capture/locate/` | `locate`: renderowania poziomu, baza danych, dopasowywanie, model dla mapy, minimapa |
| `heat3d_capture/ui/` | `__main__.py` (wejście i sprawdzenie zależności), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | sprawdzanie wydań i aktualizator |
| `mods/beamng/heat3d/` | mod protokołu BeamNG |
| `mods/trackmania/Heat3dRecorder/` | wtyczka Openplanet |
| `tools/export_onnx.py` | konwerter modelu głębi |
| `tools/gen_docs_reference.py` | zapisuje `docs/cli-reference.md` na podstawie `--help`; `--check` mówi, czy plik jest nieaktualny |
| `tools/docs_diagrams.py` | rysuje diagramy w `docs/assets/img/` (dla każdego języka z `--lang`) |
| `tools/sync_wiki.py` | odtwarza `docs/wiki/` na podstawie `docs/` |
| `models/` | przekonwertowane pliki `.onnx` (nie są wersjonowane) |
| `tests/` | zestaw testów; `scene.py` i `track_scene.py` renderują syntetyczne sceny o znanej geometrii |
| `docs/` | ta dokumentacja; `docs/wiki/` jest generowane z niej |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skanowania nie zawiera Qt: `ScanSession` i `Reconstructor` przyjmują zwykłe funkcje i można nimi
sterować ze skryptu lub testu. Przykład:

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

## Środowisko {#the-environment}

Projekt używa środowiska wirtualnego w `.venv` (tworzonego przez `scan.bat` albo ręcznie). Testy, które
dotykają interfejsu, potrzebują w nim **PySide6**, który `requirements.txt` instaluje jako
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Do konwertera modelu, testów głębi PyTorch i ścieżki offline zainstaluj PyTorch (dopasowany do karty
graficznej) **przed** `requirements.txt`; potem `requirements-offline.txt` i jego linię `vggt` dla
solvera offline oraz `onnxscript` dla konwertera. Zobacz
[Środowisko uruchomieniowe i zależności](runtime.md#installing-by-hand).

## Uruchamianie testów {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` ustawia `testpaths = tests` i wycisza ostrzeżenia `UserWarning` z `huggingface_hub`. Zestaw
ma kilkaset sprawdzeń; większość nie potrzebuje gry, karty graficznej ani sprzętu do przechwytywania.

Co pomija się samo i dlaczego:

| Testy | Pomijane, gdy |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testy sterujące oknem w `test_ui_drives_a_scan.py` | brak `models/depth-*.onnx` - najpierw uruchom `tools/export_onnx.py` |
| testy estymatora GPU w `test_depth.py` | PyTorch nie jest zainstalowany albo nie ma urządzenia CUDA; testy `fit_scale` i `AffineFit` działają zawsze |
| niektóre przypadki w `test_offline.py` i `test_solveprep.py` | OpenCV nie ma kodera wideo do zapisania syntetycznego klipu |
| `test_hotkeys.py` | testy rejestracji wymagają Windows; test zapasowy działa wszędzie indziej |
| `test_course_ground.py` | nie ustawiono `HEAT3D_COURSE` |
| kilka testów fuzji | syntetyczny przypadek nic nie scalił |

### Test uruchomienia {#the-launch-test}

`tests/test_launch.py` uruchamia prawdziwy punkt wejścia, `python -m heat3d_capture.ui`, jako podproces
(z `QT_QPA_PLATFORM=offscreen`) i sprawdza, czy dochodzi do pętli zdarzeń i działa dalej. Powstał, bo
pierwsza wersja padała przy każdym uruchomieniu, podczas gdy wszystkie inne testy przechodziły: każdy z
nich sam tworzył `QApplication` i potem budował okno, pomijając jedną sekwencję, którą wykonuje
użytkownik - sprawdzenie zależności tworzące najpierw aplikację. Test komponentu, który buduje własne
środowisko, nie zobaczy błędu w tym, jak to środowisko jest budowane.

### Dane wzorcowe {#ground-truth}

- `tests/test_accuracy.py` - syntetyczny pokój z analityczną głębią i znaną ścieżką; zobacz
  [Rekonstrukcja poziomu](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - szerokość drogi, odczyt skali toru, siatka pokrycia odczytywana
  podczas zapisu oraz dlaczego zamykanie pętli pozostaje wyłączone.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - układy telemetrii, na pakietach i stronach
  zbudowanych z udokumentowanych struktur, oraz pliki okrążeń, które zapisują (kanoniczne nazwy kanałów,
  `meta`, brak `NaN` w JSON). `tests/test_trackmania_plugin.py` czyta kod źródłowy wtyczki Openplanet, by
  sprawdzić, co zapisuje ona w opisie każdego przejazdu.
- `tests/test_route_record.py` - plik `route` jest na dysku w całości, zanim rejestrator się zatrzyma.
- `tests/test_telemetry_pose.py` - pozy Forzy we własnych współrzędnych gry, kierunki yaw, pitch i roll
  oraz przerwa w telemetrii przemostkowana wizualnie w lustrzanym świecie.
- `tests/test_glb.py` - kontrakt GLB; własne testy przeglądarki czytają poziom wzorcowy zapisany przez ten
  zapis, więc format jest testowany po obu stronach.

### Sprawdzanie wyeksportowanego toru względem okrążeń {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` sprawdza, czy tor wyeksportowany przez
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) rzeczywiście leży pod nagranym
samochodem - samochód powinien znajdować się na wysokości prześwitu nad powierzchnią tuż pod nim. Wskaż
mu nazwę wyeksportowanego toru (plik `.glb` i jego `.json` obok):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Trasa z dużymi skokami może celowo nie przejść testu: samochód jest w powietrzu nad podłożem, które tam
jest.

## Konwencje {#conventions}

- Kod w `heat3d_capture/` importuje ciężkie zależności (OpenCV, ONNX Runtime, PyTorch, Qt) z opóźnieniem,
  wewnątrz funkcji, więc import modułu, uruchomienie `--help` albo rejestratorów telemetrii nic nie kosztuje.
- Wątki robocze nigdy nie dotykają widżetów Qt; wyniki trafiają do wątku interfejsu jako sygnały Qt.
- Nagrania, pliki okrążeń, siatki, wagi modeli i wideo są trzymane poza gitem przez `.gitignore` - według
  folderu i typu pliku.
- Commity i wydania: wersja to plik `VERSION`; wydania to wydania GitHub w
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), które czyta aktualizator
  ([Aktualizacje](updates.md)).
