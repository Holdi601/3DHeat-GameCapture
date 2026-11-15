---
title: "Rekonstrukcja poziomu"
nav_order: 6
lang: "pl"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonstrukcja poziomu z rozgrywki {#level-reconstruction-from-gameplay}

Przejdź powoli przez poziom albo przejedź tor, a skaner zamieni to, co pokazał ekran, w plik `.glb`, który
przeglądarka 3DHeat wczytuje jako kontekst pod telemetrią - ten sam kontrakt plików, który zapisuje eksporter
Unreal. Jest na przypadek, gdy nikt nie wyeksportował mapy, a pliki gry nie dają się odczytać; eksport z
silnika albo eksport plików gry jest dokładny; to jest oszacowanie.

## Potok przetwarzania {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Etap | Skan na żywo (`heat3d_capture.ui`) | Offline (`reconstruct`) | Strona |
|---|---|---|---|
| Klatki | monitor, okno albo wideo, przeskalowane do dłuższego boku ustawienia | wideo, pobierane dwukrotnie (plan rozwiązania i odstęp fuzji) | [Przechwytywanie](reconstruction-capture.md) |
| Klatki kluczowe | zachowywane według tego, jak bardzo zmienił się obraz; próg dopasowany do przechwytywania | co `--fuse-interval` sekund | [Przechwytywanie](reconstruction-capture.md#keyframes) |
| Maski | `ScreenMask` oparta na zmianach, potem `FlowMask` oparta na przepływie po 40 klatkach kluczowych | `FlowMask` nauczona z czterech przebiegów wideo; nie stosowana w solverze | [Przechwytywanie](reconstruction-capture.md#what-is-not-the-world) |
| Głębia | model ONNX na najlepszym backendzie GPU | PyTorch Depth Anything V2 Small | [Głębia](reconstruction-depth.md) |
| Poza | odometria wizualna albo dokładna telemetria Forzy | okna VGGT złożone w jedną trasę, interpolowane | [Poza](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Skala | wysokość kamery nad ziemią (1,15 m) raz, albo telemetria | własne jednostki rozwiązanej trasy | [Poza](reconstruction-pose.md#scale) |
| Fuzja | ważone zajętości, rzadkie woksele; siatka pokrycia | to samo | [Fuzja](reconstruction-fusion-and-texture.md) |
| Wynik | `.glb`, części grunt/konstrukcja, kolor na wierzchołek, centymetry | to samo | [Wynik w formacie .glb](glb-output.md) |

Kod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - ustawienia skanu i tempo; `reconstruct.py` - klatki kluczowe w geometrię; `offline.py` - ścieżka
offline), a etapy w `capture/`, `depth/`, `pose/`, `fusion/` i `geometry/`.

## Skąd bierze się dokładność {#where-accuracy-comes-from}

Głębia z jednego obrazu jest dobra tylko z dokładnością do nieznanej skali - zdjęcie pokoju i domku dla lalek
to ten sam obraz. Dlatego sieć zostawia się do tego, w czym jest dobra (kształt względny, krawędzie, cienkie
konstrukcje), a skala i ścieżka kamery pochodzą skądś, kto je zna:

| Gra | Ścieżka kamery | Skala |
|---|---|---|
| Forza Horizon / Motorsport z włączoną telemetrią | dokładna, z Data Out, interpolowana do czasu przechwycenia każdej klatki | dokładna: głębia jest osadzona przez triangulację cech między dwiema znanymi pozami |
| Cokolwiek innego, na żywo | odometria wizualna, łańcuchowo klatka za klatką | ustalona raz z założonej wysokości kamery nad ziemią |
| Nagranie, offline | VGGT, rozwiązywane w nakładających się oknach | własne jednostki rozwiązania (nie metryczne) |

Jedną liczbą, którą skaner dostaje zamiast ją mierzyć, jest **poziomy kąt widzenia** gry (domyślnie 90 stopni
w oknie; gry wyścigowe są bliżej 65). Za wąski - poziom odtwarza się głębszy, niż jest; za szeroki - spłaszcza się.

## Informowanie z wyprzedzeniem {#telling-the-user-early}

Skan to czynność fizyczna - ktoś przez kilka minut chodzi po poziomie - a drogą w skutkach porażką jest
dokończyć spacer i dopiero potem odkryć, że był do niczego. Dlatego okno mierzy, jaką przepustowość głębi ma
ten komputer, zanim cokolwiek może ruszyć, i mówi, jaki będzie skan
([Środowisko uruchomieniowe](runtime.md#what-to-expect-from-this-machine)); w trakcie skanu pokazuje mapę
pokrycia z ponumerowanymi słabymi miejscami, stan śledzenia, pasek prędkości chodzenia, pasek ostrości i jedną
wskazówkę naraz, w oknie i w nakładce nad grą, przez którą można kliknąć
([Okno skanu](reconstruction-scan-ui.md)).

## Zmierzone na syntetycznych danych wzorcowych {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` renderuje pokój 12 x 8 m (4 m wysokości) z znanej ścieżki kamery, z analityczną (nie
sieciową) głębią, i odtwarza go w wokselach 0,2 m. Sprawdza, czy umieszczono ponad 90% klatek, średni błąd
trasy jest poniżej 0,35 m (najgorszy poniżej 1 m), przejechany dystans mieści się w 10% prawdy, pokój wychodzi
właściwej szerokości z dokładnością do 1,5 m, ponad 75% powierzchni ścian leży w odległości 0,45 m od
prawdziwej ściany, spacer metodą pomiarową daje wyraźnie lepsze pokrycie niż prosty marsz przed siebie, a scena
bez cech jest odrzucana zamiast wymyślana. Analityczna głębia izoluje pozę, skalę i fuzję od sieci; to, jak
sieć radzi sobie w prawdziwej rozgrywce, to osobne pytanie, na które żadna syntetyczna scena nie odpowie.
`tests/test_track_width.py` sprawdza, czy okrążenie przejechane poza środkiem drogi o znanej szerokości
odtwarza szerokość drogi, a nie tylko przejechaną linię.

## Strony {#pages}

- [Okno skanu](reconstruction-scan-ui.md) - każdy przycisk, skrót i element nakładki
- [Przechwytywanie, maski i jakość klatek](reconstruction-capture.md)
- [Głębia](reconstruction-depth.md)
- [Poza kamery i skala](reconstruction-pose.md)
- [Fuzja, pokrycie i kolor](reconstruction-fusion-and-texture.md)
- [Wynik w formacie .glb](glb-output.md)
- [Rekonstrukcja offline](reconstruction-offline.md)
