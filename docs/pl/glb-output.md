---
title: "Wynik w formacie .glb"
nav_order: 6
lang: "pl"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Wynik w formacie .glb {#the-glb-output}

Rekonstrukcja zapisywana jest jako binarny plik glTF 2.0 (`.glb`), który przeglądarka 3DHeat wczytuje przez
swój panel Tło / poziom bez żadnej specjalnej obsługi - ten sam kontrakt, który zapisuje eksporter Unreal.
Kod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Zapis jest napisany ręcznie, a nie przez bibliotekę glTF: wynik to wąski podzbiór (jeden bufor, ciasno
upakowany, bez animacji i bez skinningu), a zależność, która potrafi zapisać cały glTF, wniosłaby własne
rozbieżności wersji, a potrzeba jest tylko kilkuset linii kodu.

## Co jest w pliku skanu {#what-is-in-a-scans-file}

| Część (nazwa węzła i siatki) | Zawartość |
|---|---|
| `ground:<name>` | trójkąty skierowane w górę, o nachyleniu do 35 stopni |
| `structure:<name>` | wszystko inne |

`<name>` to nazwa pliku bez rozszerzenia przy zapisie z okna albo nazwa wideo dla `reconstruct`. Część bez
trójkątów jest pomijana. Skan nigdy nie zapisuje części `water:`. `asset.generator` ma wartość
`heat3d-capture-scan`.

## Kontrakt {#the-contract}

- **Jeden węzeł na część**, nazwany etykietą części; siatka powtarza nazwę. Przeglądarka czyta najpierw
  nazwę *węzła*, więc nazwanie samych siatek zgubiłoby klasyfikację.
- Etykieta to `<klasa>:<nazwa>`, gdzie klasa to `ground`, `structure` albo `water` - prefiks, który
  przeglądarka dopasowuje (`^(ground|structure|water)\s*[:|]`), by wziąć klasę wprost, zamiast zgadywać ją
  z geometrii. Grunt jest renderowany jako bryła, konstrukcje - prawie przezroczyste.
- **Współrzędne są w przestrzeni przeglądarki**: Y w górę, układ prawoskrętny, i **przeskalowane na
  centymetry** (metry x 100), by pasowały do eksportera Unreal - przechwycenie i eksport z silnika tego
  samego miejsca wczytają się w tym samym rozmiarze, z tymi samymi domyślnymi ustawieniami kamery. Pole
  najwyższego poziomu `extras.unit_metres` pliku ma wartość `0.01` (jednostka to centymetr), więc czytnik
  działający w metrach, na przykład [`locate`](locate.md), bierze ją w prawdziwym rozmiarze. Wyjątkiem co do
  skrętności jest skan umieszczony przez telemetrię Forzy: zostaje w świecie samej gry, Y w górę i układ
  lewoskrętny, dokładnie jak pliki okrążeń, dzięki czemu okrążenia nagrane nad nim lądują na nim. Gdy
  skalę skanu znaleziono na późniejszej klatce kluczowej ([Skala](reconstruction-pose.md#scale)), ten
  współczynnik jest wliczony w zapisaną skalę.
- `COLOR_0` czyta przeglądarka, która cieniuje nim grunt, gdy w jej panelu Tło / poziom włączony jest
  przełącznik *Zarejestrowany kolor* (domyślnie wyłączony).
- Skan z ręcznie zaznaczonymi miejscami dostaje obok plik `<name>.marks.json`; zobacz
  [Zapis](reconstruction-scan-ui.md#saving).
- Na prymityw: `POSITION` (float VEC3, z `min` i `max`, od których przeglądarka ustawia kadr kamery),
  `NORMAL` (float VEC3), opcjonalnie `COLOR_0` (float VEC3, 0..1), opcjonalnie `TEXCOORD_0`; indeksy jako
  16-bitowe, gdy każdy indeks jest poniżej 65 536, w przeciwnym razie 32-bitowe; tryb: trójkąty.
- Każdy widok bufora zaczyna się wyrównany do 4 bajtów; blok JSON dopełniany jest spacjami, a blok BIN
  zerami do 4 bajtów.

## Sprawdzenia przed zapisem {#checks-before-writing}

Każda część jest sprawdzana i odrzucana z komunikatem, który ją nazywa, gdy nie ma wierzchołków, liczba
indeksów nie tworzy pełnych trójkątów, indeks jest poza zakresem lub ujemny, pozycje nie są skończone, albo
normalne lub kolory nie zgadzają się z liczbą wierzchołków. Normalne są liczone, gdy ich brakuje, **ważone
powierzchnią** (marching cubes zostawia cienkie trójkąty przy dużych ścianach, a średnia bez wag pozwoliłaby
drobnym trójkątom przegłosować ścianę, na której leżą); zdegenerowany wierzchołek dostaje kierunek „w górę”.
Zapis bez żadnej części to błąd.

Eksport nic nie zwraca - a okno pokazuje „Nothing to save” - gdy bryła nie daje powierzchni, zamiast
zapisywać pusty plik, który wyglądałby jak udany skan.

## Tekstury {#textures}

Zapis obsługuje teksturę PNG koloru bazowego dla każdej części (z UV, materiał dwustronny, niemetaliczny,
całkowicie matowy). Skany jej nie używają; mają kolor na wierzchołek. Zobacz [kolor](reconstruction-fusion-and-texture.md#colour).

## Poziom wzorcowy {#the-reference-level}

`geometry/reference.py` buduje tym samym zapisem syntetyczny poziom o dokładnie znanym rozmiarze: podłoże
400 m z podziałem na siatkę, trzy budynki 20 x 20 x 12 m i staw 50 m, 1,5 m pod ziemią; każda klasa ma
osobny płaski kolor. Własne testy przeglądarki generują go i czytają jej prawdziwym czytnikiem, więc format
pliku jest testowany po obu stronach, bez gry i bez sprzętu do przechwytywania.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
