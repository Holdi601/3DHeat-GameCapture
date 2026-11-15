---
title: Lista poleceń
nav_order: 5
lang: "pl"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Lista poleceń {#command-reference}

Wszystkie polecenia uruchamia się z folderu repozytorium, ze środowiskiem projektu:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Polecenie | Robi |
|---|---|
| [`route`](#route) | Zapisuje wyłącznie pozycje przejazdu Forzy, aby znaleźć mapę w plikach gry |
| [`telemetry`](#telemetry) | Zapisuje każdy kanał, po jednym pliku na okrążenie, dla karty „Analiza wyścigowa” |
| [`laps`](#laps) | Czyta bibliotekę okrążeń FH Companion i zapisuje trasę oraz próbki jednego toru |
| [`reconstruct`](#reconstruct) | Rozwiązuje nagranie offline i zapisuje `.glb` |
| [`hud`](#hud) | Odczytuje z nagrania własne działania gracza, zgony i ślad z minimapy oraz kanał zabójstw |
| [`locate`](#locate) | Gdzie została nagrana każda klatka, na podstawie renderów poziomu |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Okno skanowania |
| [`python -m heat3d_update`](#updates) | Sprawdza i instaluje aktualizację |
| [`python tools/export_onnx.py`](#the-model-converter) | Konwertuje model głębi do ONNX |

Po uruchomieniu jako `python -m heat3d_capture` narzędzie najpierw sprawdza, czy jest nowsze wydanie (zob. [Aktualizacje](updates.md); `HEAT3D_NO_UPDATE=1` wyłącza to sprawdzanie). `--help` po dowolnym poleceniu wypisuje jego opcje:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Nasłuchuje na Forza Data Out i zachowuje wyłącznie pozycje samochodu, nic więcej: bez modelu głębi, bez GPU, bez przechwytywania. Kod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `-o`, `--out` | wymagane | Ścieżka wyjściowa; jej rozszerzenie jest zastępowane, więc `-o lap` zapisze `lap.npz` i `lap.json`. |
| `--port` | `5300` | Port, na który wysyła gra (nasłuch na 127.0.0.1). |
| `--seconds` | `0` | Zatrzymaj po tylu sekundach; `0` działa do Ctrl+C. |

Pozycja jest zachowywana tylko wtedy, gdy gra zgłasza wyścig (`isRaceOn`), samochód porusza się szybciej niż 0.5 m/s i jest co najmniej 0.5 m od ostatnio zachowanej pozycji. Inaczej stanie w menu przy 60 pakietach na sekundę zapełniłoby plik linią startu. Czas każdej próbki to czas wyścigu w grze, a gdy jest on równy 0, zegar ścienny. Układ wykrywa się tak samo jak w `telemetry` (samochód musi najpierw ruszyć; zob. [Forza](telemetry-forza.md)).

Co sekundę wypisuje liczbę odebranych pakietów, zachowanych pozycji i bieżącą pozycję albo `nothing on port 5300 yet - is Data Out on?`. Trasa jest **zapisywana podczas jazdy**: co 2 sekundy, gdy nadeszła nowa pozycja (odstęp rośnie do dwudziestokrotności czasu ostatniego zapisu, więc bardzo długa sesja nigdy nie poświęca na zapis więcej niż jednej dwudziestej swojego czasu), i jeszcze raz, gdy rejestrator zatrzyma się z dowolnego powodu - Ctrl+C, `--seconds` albo wyjątek. Każdy zapis najpierw zapisuje `lap.npz.partial` / `lap.json.partial`, a potem przenosi je na właściwe pliki, więc pliki na dysku są zawsze kompletne; awaria lub zabicie procesu traci co najwyżej ostatnie kilka sekund. Jeśli nic nie zostało zachowane, wypisuje, jak włączyć Data Out, i kończy działanie z kodem 1.

Wynik:

- `lap.npz` - tablice NumPy `positions` (n x 3, metry), `times`, `speeds` (m/s);
- `lap.json` - czytelny bez tego projektu:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Pozycje to współrzędne świata gry, co czyni je punktem zaczepienia do znalezienia tego samego terenu w plikach gry: polecenie `course` z [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) przyjmuje ten JSON i eksportuje tor, po którym jechało okrążenie.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Każda opcja i każda gra są opisane na [Rejestratory telemetrii](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Czyta bibliotekę okrążeń, którą prowadzi FH Companion, i zapisuje dwa pliki dla jednego toru: trasę, która określa, jaki fragment mapy wyciąć z archiwum gry, oraz tabelę każdej próbki każdego okrążenia. Zapisywane są razem, żeby nie mogły się rozjechać. Kod: [`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `course` | brak | Nazwa toru, dopasowywana luźno. Pomiń, aby wypisać bibliotekę. |
| `-o`, `--out` | nazwa toru małymi literami, spacje jako `_` | Ścieżka wyjściowa; obok siebie zapisywane są `.json` i `.csv`. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Gdzie leżą foldery torów. |
| `--margin` | `80` | Metry dodane wokół zasięgu toru w x i z w `bounds` trasy. |

### Wyświetlanie listy {#listing}

Bez toru wypisuje liczbę folderów torów i dla każdego liczbę plików okrążeń (`*.json` na dowolnej głębokości, z wyjątkiem `course.json`) oraz nazwę toru, a potem `Name one to write it out:  -o <file> <course>`.

### Znajdowanie toru {#finding-a-course}

Foldery torów nazywają się `<nazwa> (course_<x>_<z>_to_<x>_<z>)` - start i meta, zaokrąglone. Tor jest szukany w tej kolejności: dokładna nazwa folderu; część nazwy folderu bez współrzędnych, bez względu na wielkość liter; jedyny folder, którego nazwa zawiera podany tekst. Kilka dopasowań to błąd, który wypisuje ich listę.

### Odczyt {#reading-it}

- `course.json` w folderze, jeśli da się go odczytać, podaje nazwę oraz niezaokrąglone start i meta (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); w przeciwnym razie są brane z nazwy folderu. Tor jest uznawany za pętlę, gdy start i meta są oddalone o mniej niż 10 m.
- Każdy inny `*.json` poniżej folderu jest okrążeniem (okrążenia leżą kilka folderów głębiej - według klasy, auta, strojenia, znacznika - a przeszukiwanie jest po prostu rekurencyjne). Pliki czyta się jako UTF-8 z BOM. Nieczytelne okrążenie jest pomijane. Okrążenia są sortowane według czasu nagrania.
- Dla każdego okrążenia: `Lap.samples` (każda próbka z `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`) oraz klasa auta, numer porządkowy, indeks wydajności, czas okrążenia, długość, czas nagrania i start z miejsca.

Wypisuje podsumowanie (okrążenia, próbki, najlepsze okrążenie i jego klasa, zakres x/y/z).

### Wynik {#output}

**`<out>.json`** - ten sam kształt trasy, który zapisuje `route`, więc ekstraktor mapy przyjmuje oba: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (rozszerzone o `--margin` w x i z) oraz `positions` **najszybszego** okrążenia (jedna linia zamiast smugi ze wszystkich okrążeń).

**`<out>.csv`** - każda próbka każdego okrążenia, po jednym wierszu:

| Kolumna | Znaczenie |
|---|---|
| `course` | nazwa toru |
| `lap` | etykieta okrążenia: data i godzina nagrania co do minuty oraz czas okrążenia |
| `car` | numer porządkowy auta |
| `car_class` | litera klasy wydajności |
| `pi` | indeks wydajności |
| `lap_seconds` | czas okrążenia |
| `speed_kmh` | prędkość w km/h |
| `x`, `y`, `z` | pozycja w świecie, metry, 3 miejsca po przecinku |
| `speed_ms` | prędkość w m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | tak, jak zapisuje je FH Companion |
| `metres` | odległość wzdłuż okrążenia, 3 miejsca po przecinku |
| `elapsed` | sekundy od własnego startu okrążenia, 3 miejsca po przecinku |

Wartości niebędące pozycjami zapisuje się z 4 cyframi znaczącymi; pozycje mają stałą liczbę miejsc po przecinku, bo 4 cyfry znaczące przyciągnęłyby tor do siatki co metr. Nazwy kolumn są tak dobrane, że przeglądarka 3DHeat mapuje plik bez podpowiedzi: `lap` staje się sesją (dwa okrążenia tego samego auta nigdy się nie łączą), `car` - obiektem, który się porusza, `car_class` - grupą do kolorowania, a `elapsed` - osią czasu (każde okrążenie zaczyna się od swojego startu).

Na koniec wypisuje podpowiedź, jak wyciąć mapę z gry narzędziem GameFiles, z plikiem trasy albo z podanym prostokątem.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruuje nagranie offline, z trajektorią kamery rozwiązaną naraz przez VGGT. To wolne: minuty na okno na komputerowej karcie graficznej. Potrzebuje PyTorch, Hugging Face `transformers` i pakietu `vggt`, których skaner nie potrzebuje. Są wymienione w `requirements-offline.txt`, a polecenie sprawdza je po wypisaniu wiersza licencji i proponuje zainstalowanie brakujących (kod wyjścia 1, jeśli odmówisz). Pełny opis: [Rekonstrukcja offline](reconstruction-offline.md).

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `video` | wymagane | Nagranie. Kod wyjścia 2, jeśli plik nie istnieje. |
| `-o`, `--out` | wymagane | Plik `.glb` do zapisania. |
| `--solve-budget` | `260` | Najwięcej klatek przekazanych solverowi. Są rozmieszczane według tego, jak bardzo zmienia się obraz, a nie według zegara. Więcej to dokładniej i znacznie wolniej. Więcej niż 400 zaplanowanych klatek jest odrzucane. |
| `--fuse-interval` | `0.4` | Sekundy między klatkami wtapianymi w geometrię. |
| `--model` | `vggt-1b` | Wagi VGGT, którymi rozwiązujemy: `vggt-1b` (`facebook/VGGT-1B`, niekomercyjne) albo `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, z ograniczonym dostępem; wymaga przyznanego dostępu od Mety). Wiersz licencji wypisany jako pierwszy jest licencją tego modelu. |

Najpierw wypisuje wiersz licencji modelu, potem każdy etap (`masking`, `planning`, `solving`, `fusing`, `exporting`) z upływem sekund i postępem, a na końcu podsumowanie: rozwiązane kamery, błąd zamknięcia, najgorszy szew, uwagi i zapisany plik. Kod wyjścia to 0 tylko wtedy, gdy plik został zapisany.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Odczytuje HUD gry z **własnego** nagrania gracza, po meczu: jego własne akcje z wyskakującego okienka punktów, zgony i ożywienia z ekranów padnięcia i rozmieszczenia, ślad z minimapy oraz kanał zabójstw. Zapisuje `<out>.parquet` (ślad i zdarzenia, tabela 3DHeat), `<out>.events.jsonl`, `<out>.summary.json` oraz `<out>.map.png` + `.map.json` (mozaika minimapy i jej kotwice dla opcji Obraz mapy w przeglądarce). Battlefield 6 (`bf6`) jest na razie jedynym profilem.

Wymaga **ffmpeg i ffprobe** w PATH (`winget install Gyan.FFmpeg`, potem nowy terminal).

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `video` | wymagane | Nagranie. |
| `-o`, `--out` | nazwa wideo | Ścieżka wyjściowa bez rozszerzenia. |
| `--game` | `bf6` | Czyj HUD czytać. |
| `--player` | zgadywane | Nazwa gracza tak, jak pokazuje ją kanał zabójstw, dopasowywana luźno. |
| `--fps` | `5` | Próbki minimapy na sekundę. |
| `--start`, `--seconds` | całe wideo | Fragment nagrania do odczytu. |
| `--metres-per-pixel` | brak | Skala minimapy, gdy jest znana; bez niej pozycje są w pikselach minimapy. |
| `--cpu` | wyłączone | Dekoduj na procesorze, nawet gdy jest karta NVIDIA. |

Pełny opis: [Odczyt HUD z nagrania](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderuje poziom z każdego miejsca, z którego może stać gracz, i indeksuje te renderowania; `frames` umieszcza każdą próbkowaną klatkę nagrania względem tego indeksu, na podstawie obrazu, ze śladem minimapy z polecenia `hud` jako rezerwą; `eval` porównuje wynik ze znanymi pozycjami kamery; `train` trenuje model miejsc dla mapy na renderach poziomu (i na klatkach, które przebieg już zlokalizował), dla `build --head`; `refmap` umieszcza własną mapę gry (ekran rozmieszczenia) na poziomie, a `minimap` odczytuje minimapę nagrania względem niej, klatka po klatce - to wcześniejsze dane, które może przyjąć `frames --minimap`. Potrzebuje PyTorch i `requirements-locate.txt`. **Eksperymentalne:** na prawdziwych nagraniach umieszcza na razie tylko niewielką część klatek. Wszystkie opcje, wyniki i metodę znajdziesz na stronie [Lokalizowanie klatek w poziomie](locate.md); pełna lista opcji: [Lista poleceń](../cli-reference.md).

<a id="the-scan-window"></a>
## Okno skanowania {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

albo kliknij dwukrotnie `scan.bat`. Bez opcji. Zob. [Okno skanowania](reconstruction-scan-ui.md).

<a id="updates"></a>
## Aktualizacje {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Zob. [Aktualizacje](updates.md).

<a id="the-model-converter"></a>
## Konwerter modelu {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Konwertuje checkpoint Depth Anything V2 do pliku ONNX, który uruchamia skaner. Potrzebuje PyTorch, `transformers` i `onnxscript`. Zob. [Głębia](reconstruction-depth.md#building-the-model).
