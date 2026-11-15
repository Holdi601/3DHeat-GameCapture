---
title: Środowisko uruchomieniowe i zależności
nav_order: 8
lang: "pl"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Środowisko uruchomieniowe, zależności i wydajność {#runtime-dependencies-and-performance}

Kod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Kliknij go dwukrotnie. Robi tylko dwie rzeczy:

1. **Znajduje Pythona** (`python`, potem `py`). Gdy go nie ma, pyta `Install it now with winget [Y,N]?`; na Y uruchamia `winget install -e --id Python.Python.3.12`, potem prosi o zamknięcie okna i ponowne uruchomienie `scan.bat`, żeby Windows odświeżył PATH. Na N nic nie jest instalowane.
2. **Tworzy prywatne środowisko**, `.venv` obok `scan.bat`, jeśli go nie ma, i aktualizuje jego pip - więc nic nie instaluje się w systemowym Pythonie.

Potem uruchamia `.venv\Scripts\python.exe -m heat3d_capture.ui`. Cała reszta - ustalanie, czego brakuje, wyjaśnianie po co, pytanie - dzieje się w Pythonie, w oknie dialogowym.

## Wstępne sprawdzenie przy pierwszym uruchomieniu {#first-run-preflight}

Zanim okno zaimportuje cokolwiek ciężkiego, sprawdzane jest każde wymaganie (przez `importlib.util.find_spec`, więc na wpół usunięty pakiet liczy się jako brakujący). Zasady:

- **Wszystko jest sprawdzane najpierw.** Pełna lista jest zbierana, zanim cokolwiek zostanie powiedziane, więc naprawa jednego pakietu nie prowadzi od razu do następnego błędu.
- **Pytaj, nigdy nie zakładaj.** Okno dialogowe wymienia każdy brakujący pakiet, do czego służy i łączne pobranie, i nic nie robi bez **Download and install**. Cancel kończy: „Nothing was installed and nothing was changed.”
- **Milczenie to nie zgoda.** Bez Qt sprawdzenie wraca do konsoli i pyta `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` oznaczają tak); bez terminala, z którego można odpowiedzieć (koniec wejścia), nic nie jest instalowane.
- **Do środowiska tego narzędzia.** Instalacja to `<running python> -m pip install ...` jako podproces - przy `scan.bat` w prywatnym `.venv`. Jeśli się nie uda, okno pokazuje ostatnią linię wyjścia pipa i polecenie do wykonania ręcznie.

| Pakiet | Importowany jako | Pokazywany jako, do czego służy | Mniej więcej pobranie |
|---|---|---|---|
| numpy | `numpy` | arytmetyka, na której zbudowane jest wszystko inne | 20 MB |
| opencv-python | `cv2` | czytanie plików wideo i klatek z kamery | 40 MB |
| onnxruntime-directml na Windows, onnxruntime gdzie indziej | `onnxruntime` | uruchamianie modelu głębokości na karcie graficznej | 120 MB |
| PySide6-Essentials | `PySide6` | okno i jego kontrolki | 90 MB |
| scipy | `scipy` | wygładzanie zrekonstruowanej powierzchni | 45 MB |
| scikit-image | `skimage` | zamiana pomiarów w powierzchnię 3D | 30 MB |
| windows-capture | `windows_capture` | przechwytywanie okna gry na żywo (opcjonalne: bez niego pliki wideo nadal działają) | 5 MB |

Konwersja modelu głębokości wymaga trzech kolejnych, pytanych osobno i tylko po naciśnięciu „Set up the depth model”: `torch` (około 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Sam skaner nigdy ich nie importuje.

Osobne sprawdzenie ma polecenie offline `reconstruct`, uruchamiane po wypisaniu linii licencji i tylko w terminalu: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow` oraz `vggt` z repozytorium GitHub Meta (instalowany z `--no-deps`, bo jego metadane przypinają numpy poniżej 2). Ta sama lista jest w `requirements-offline.txt`; zob. [Rekonstrukcja offline](reconstruction-offline.md#requirements).

Pakiet ONNX Runtime, który jest oferowany, to ten, który `requirements.txt` wybiera dla platformy: `onnxruntime-directml` na Windows, `onnxruntime` gdzie indziej. Jeśli `onnxruntime` jest już importowalne (na przykład `onnxruntime-gpu`), nic nie jest instalowane: sprawdzenie jest po nazwie modułu.

## Instalacja ręczna {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` przypina: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (tylko Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` na Windows i `onnxruntime>=1.19` gdzie indziej.

`requirements-offline.txt` dodaje to, czego potrzebuje tylko `reconstruct`: `transformers`, `einops`, `safetensors`, `huggingface_hub` i `Pillow`, wraz z linią instalacji `vggt` (`--no-deps`) i notatką o licencji VGGT w nagłówku. PyTorch też w nim nie ma, z powodu podanego niżej.

**PyTorch jest celowo nieobecny.** Właściwe koło zależy od GPU i wersji CUDA, a przypięcie jednego zainstalowałoby wersję CPU na maszynach, które najbardziej potrzebują wersji GPU. Jeśli go chcesz (konwersja modelu, offline'owa ścieżka `reconstruct`), zainstaluj go **przed** `requirements.txt`: koła torch mogą ściągnąć numpy 1.x, na którym scipy odmawia działania, a błąd wychodzi jako `module numpy has no attribute long` z wnętrza scipy, daleko od przyczyny.

`onnxruntime-directml` i `onnxruntime-gpu` się wykluczają: instaluj tylko jeden z nich.

Sprawdzone przez dewelopera: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na NVIDIA RTX 5080, oraz to samo środowisko bez pakietu specyficznego dla NVIDIA.

## Backendy wnioskowania {#inference-backends}

ONNX Runtime sięga do GPU przez dostawców wykonania (execution providers), a to, którzy istnieją, zależy od tego, jak zainstalowano onnxruntime, a nie od sprzętu. Dostępność jest więc wykrywana, od najlepszego:

| Pozycja | Dostawca | Pokazywany jako | Sprzęt |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | każda karta z Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | cokolwiek |

**DirectML to domyślna instalacja**, bo sięga kart AMD i Intel tak samo jak NVIDIA. NVIDIA jest szybsza z własnymi dostawcami - instalacja `onnxruntime-gpu` dodaje CUDA, a okno mówi o tym, gdy widzi kartę NVIDIA działającą na DirectML - ale NVIDIA nie może być jedyną opcją. CPU jest zawsze na końcu, więc maszyna bez użytecznego GPU dostaje wolny skan zamiast żadnego, a CPU jest dołączane jako zapas, gdy tworzona jest sesja GPU.

Nazwa karty jest odczytywana z klucza klasy kart graficznych w rejestrze Windows (nie z narzędzia producenta, takiego jak `nvidia-smi`, które istnieje tylko na niektórych maszynach), z pominięciem Basic Render Driver. Dostawcy zablokowani na producenta wskazują pasującą kartę; DirectML jest pokazywany na pierwszej wyliczonej karcie, czyli domyślnej karcie systemu. Nazwa służy tylko do wyświetlenia.

`ScanSettings.prefer_backend` (tylko dla skryptów) może nazwać dostawcę lub krótką nazwę.

## Czego spodziewać się na tej maszynie {#what-to-expect-from-this-machine}

Okno mierzy przepustowość modelu głębokości na tej maszynie przy starcie (6 klatek po rozgrzewce), zamiast szukać GPU w tabeli - stan termiczny, profile zasilania laptopów i wersje sterowników przesuwają to zbyt mocno - i mówi, czego spodziewać się skanu, zanim cokolwiek może się zacząć:

| Zmierzone widoki na sekundę | Poziom | Nagłówek | Porada |
|---|---|---|---|
| 25 lub więcej | w czasie rzeczywistym | Live scanning at full detail. | Chodź w normalnym tempie; nakładka nadąży. |
| 12 do 25 | wykonalny | Live scanning, with fewer views kept than at full speed. | Chodź wolno i skręcaj łagodnie - szybkie zakręty zostawią luki. Draft zachowuje mniej widoków, co pomaga modelowi głębokości nadążać. |
| 2 do 12 | wolny | Record first, reconstruct afterwards. | Nagraj wideo spaceru i zrekonstruuj z pliku potem. Wynik jest identyczny; tylko sprzężenie zwrotne nie jest na żywo. |
| poniżej 2 | niepraktyczny | This machine is too slow to scan usefully. | Krótsza trasa albo mniejszy model. **Start jest wyłączony.** |

Na CPU notatka dodaje, że zainstalowanie `onnxruntime-directml` zwykle to naprawia na Windows. Nic nie zmienia rozdzielczości przechwytywania samo z siebie: to by nie pomogło, bo model głębokości działa w swoim stałym rozmiarze wejścia, bez względu na to, co dostanie; to, co utrzymuje wolniejszą maszynę na powierzchni, to zachowywanie mniejszej liczby widoków, czyli to, co robi Draft.

### Zmierzone przez dewelopera {#measured-by-the-developer}

Ten sam plik ONNX, to samo wyjście, RTX 5080:

| Backend | Przepustowość głębokości |
|---|---|
| DirectML | 54 kl/s |
| CPU | 3,5 kl/s |

Testowy klip przez dostarczoną ścieżkę ONNX:

| Ustawienie | Zachowane widoki | Przepustowość głębokości |
|---|---|---|
| Draft | około 1 na 7 | około 50 /s |
| Balanced | około 1 na 4 | około 50 /s |
| Detailed | około 1 na 2 | około 40 /s |

Głębokość jest wyraźnie szybsza niż przechwytywanie, więc skanowanie na żywo nie jest ograniczone przez głębokość. Środowisko aplikacji zajmuje około 349 MiB bez PyTorcha, wobec około 3,5 GB dla torch z CUDA.

Ścieżka offline `reconstruct` jest inna: minuty na okno 16 klatek na stacjonarnym GPU.

## Pamięć {#memory}

- Klatki nie są przechowywane po fuzji, poza **160** do kolorowania siatki.
- Skan zatrzymuje się po **3000** zachowanych widokach domyślnie („Views kept”), jako zabezpieczenie.
- Kolejka przechwytywania na żywo trzyma 4 klatki; bufor póz z telemetrii 30 sekund.
- Obie siatki woksel są rzadkie, a siatka jest wyciągana blok po bloku, więc pamięć zależy od tego, co zeskanowano, a nie od obwiedni.

## Platforma {#platform}

Skaner i rejestratory Assetto Corsa działają w praktyce tylko na Windows: przechwytywanie na żywo używa Windows Graphics Capture, skróty klawiszowe i nakładka przezroczysta dla kliknięć używają API Win32, a strony Kunos to pamięć współdzielona Windows. Pliki wideo można skanować, a rejestratory UDP działają gdzie indziej, ale nie zostało to sprawdzone.
