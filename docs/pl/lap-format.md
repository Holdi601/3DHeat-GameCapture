---
title: Plik heat3d-lap
nav_order: 9
lang: "pl"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Plik `heat3d-lap` {#the-heat3d-lap-file}

Każdy rejestrator telemetrii w tym repozytorium zapisuje jeden plik na okrążenie lub odcinek rajdowy, w tym samym kształcie, niezależnie od gry. Eksport torów w [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) czyta go z powrotem, by znaleźć grę, poziom i przejechaną linię. Wszystko, co czyta JSON, może go odczytać.

![Pola i kanały pliku okrążenia zapisanego z syntetycznego strumienia Forzy](../assets/img/lap-file.svg)

## Dokument {#the-document}

Jeden obiekt JSON. Kanały są zapisane jako kolumny: jedna tablica na kanał, wszystkie tej samej długości, jeden wpis na próbkę.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Pole | Znaczenie |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | z jakiej gry jest okrążenie; zob. listę poniżej |
| `track` | nazwa toru, odcinka lub mapy, gdy gra ją podaje |
| `layout` | tylko Forza: który układ pakietu Data Out został odkodowany |
| `car` | wszystko, co gra podaje o samochodzie; dowolna struktura |
| `lap` | numer okrążenia, jego czas tak, jak liczyła go gra (lub rozpiętość próbek), czy zostało ukończone, jego długość |
| `meta` | jak czytać liczby; zob. poniżej |
| `units` | jednostka każdego obecnego kanału, dla czytnika, który nie zna poniższej tabeli |
| `channels` | próbki |
| `unparsed` | tylko Forza, gdy pakiet ma bajty, których żadne pole nie nazywa: `ranges` (ich przesunięcia bajtów `[start, end)` w pakiecie) i `hex` (dla każdej próbki te bajty w hex), więc sam plik zawiera cały pakiet |

`game` to jedna z wartości: `forza-horizon`, `forza-motorsport`, `forza` (układu pakietu nie rozróżniono), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` mówi, co oznaczają liczby tam, gdzie gry się różnią:

- `slip`: co zawierają kanały poślizgu, jeśli gra je wysyła - `peak` (znormalizowany, więc powyżej 1 opona traci przyczepność: Forza), `scaled` (poślizg fizyczny podzielony przez typowy szczyt dla asfaltu: gry Assetto Corsa), `physical` (ułamek i radiany), `index` (miara poślizgu w zakresie 0..1: Trackmania);
- `discipline`: `circuit` (tor), `rally` (rajd) lub `arcade`;
- `surface`: `tarmac` (asfalt), `loose` (luźne podłoże), `snow` (śnieg), `ice` (lód) lub `mixed` (mieszana), gdy wiadomo (rejestratory rajdowe biorą to z `--surface`).

## Kanały {#channels}

Kanał, którego gra nie wysyła, jest nieobecny, nigdy nie wypełniony zerami. Kanały per koło mają po kropce nazwę koła: `.FL`, `.FR`, `.RL`, `.RR`.

Pozycje są we współrzędnych świata gry, w metrach, z `y` w górę. Gra, której świat jest zorientowany z Z w górę, jest obracana przez swój rejestrator do Y w górę; nic innego nie jest zmieniane, więc świat lewoskrętny (Forzy) pozostaje lewoskrętny.

| Kanał | Jednostka | Znaczenie |
|---|---|---|
| `time` | s | od pierwszej próbki okrążenia |
| `distance` | m | wzdłuż przejechanej drogi od pierwszej próbki |
| `x`, `y`, `z` | m | położenie; `y` to wysokość |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedały i dźwignia |
| `steer` | -1..1 | dodatni w prawo |
| `gear` | | tak, jak liczy go gra |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | układ samochodu |
| `yaw`, `pitch`, `roll` | rad | kierunek i orientacja |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | prędkość w układzie samochodu: w prawo, do przodu, w górę |
| `bodySlip` | rad | kąt dryfu, tam gdzie gra go wysyła |
| `loose` | 0/1 | na luźnym podłożu (Trackmania) |
| `airborne` | 0/1 | żadne koło nie dotyka podłoża |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | tak, jak je wysyła gra |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | systemy wspomagania działają, włączone |
| `absLevel`, `tcLevel` | | ustawienia wspomagania |
| `brakeBias` | 0..1 | udział przodu |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | na koło |
| `tirePressure` | psi | na koło |
| `tireWear` | 0..1 | na koło |
| `slipRatio`, `slipAngle`, `combinedSlip` | patrz `meta.slip` | na koło |
| `slipIndex` | 0..1 | miara poślizgu na koło (Trackmania) |
| `camber` | rad | na koło |
| `brakeTemp` | °C | na koło |
| `padLife`, `discLife` | | na koło |
| `suspensionM` | m | skok koła |
| `suspension` | 0..1 | skok koła z zakresu użytego w tym okrążeniu |
| `wheelLoad` | N | na koło |
| `wheelSpeed` | rad/s | obrót koła, na koło |
| `wheelSurfaceSpeed` | m/s | prędkość strefy styku na koło |
| `groundContact` | 0/1 | na koło |
| `rumble`, `surfaceRumble` | | na koło: na pasie wibracyjnym; wibracje nawierzchni |
| `puddle` | | na koło: głębokość stojącej wody |

Rejestrator może dodać własne kanały pod innymi nazwami; czytnik zachowuje to, czego nie zna.

Żadna gra rajdowa nie wysyła poślizgu opon. Czytnik może go wyliczyć z prędkości strefy styku każdego koła względem prędkości samochodu, `(koło - samochód) / samochód`, albo z obrotu koła i promienia toczenia zmierzonego na samym okrążeniu, tam gdzie wysyłany jest tylko obrót. Kąt dryfu pochodzi z prędkości własnej samochodu (`latVel`, `longVel`), tam gdzie jest wysyłana, albo z prędkości świata rzutowanej na osie samochodu.

## Format CSV {#the-csv-form}

Wtyczka Trackmania zapisuje zamiast tego `heat3d-lap-csv`: pierwsza linia zaczyna się od `# ` i zawiera obiekt JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), potem linia z nazwami kanałów, a potem jedna linia na próbkę. Nazwy kanałów są takie same jak wyżej.

## Co faktycznie zapisuje każdy rejestrator {#what-each-recorder-actually-writes}

Format powyżej jest kontraktem; rejestratory wypełniają go nieco inaczej, a czytnik powinien tolerować wszystkie te warianty (sprawdzone na kodzie):

| Rejestrator | `track` | `layout` | `meta` | `units` | Kanały poza tabelą |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (numer toru Forza Motorsport 2023 to `lap.trackOrdinal`) | wykryty układ pakietu | `slip: peak`, `discipline: circuit` | tylko jednostki obecnych kanałów | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, zegar gry `timestampMs`, `raceTime`, `bestLap`, `lastLap`; prędkość w układzie samochodu jest pod kanonicznymi `latVel`, `vertVel`, `longVel`; `unparsed` obok kanałów |
| Gry Assetto Corsa (`kunos.py`) | ze statycznej strony, albo `null` | brak | `slip: scaled`, `discipline: circuit` lub `rally` | stała lista | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (tak, jak wysłany), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Gry rajdowe (`rally.py` przez `lapfile.py`) | `null` | brak | `discipline: rally`, `slip: null`, `surface` tylko wtedy, gdy podano `--surface` (w przeciwnym razie przeglądarka to ustala) | tylko jednostki obecnych kanałów | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` dla pól float bez ustalonej nazwy; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` przez `lapfile.py`) | `null` | brak | `discipline: circuit` | tylko jednostki obecnych kanałów | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Wtyczka Trackmania (CSV) | nazwa mapy | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` to blok samochodu z Forzy (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` dla gier Kunos, gdy statyczna strona podaje nazwę, a `{}` w przeciwnym razie. `lap.metres` to dla Forzy różnica przejechanego dystansu podanego przez grę, a w pozostałych przypadkach suma odległości 3D między próbkami. Wartości są zaokrąglane przy zapisie: `time` do 4 miejsc po przecinku, `distance` do 3, pozostałe liczby zmiennoprzecinkowe do 5. JSON jest zapisywany zwarcie (bez spacji).

Każdy pakiet lub strona, które rejestrator otrzymał - nie tylko te z okrążeń - jest zachowywany w całości obok plików okrążeń w `<stamp>_<game>.raw.parquet`, z samokontrolą w `<stamp>_<game>.summary.json` (sekcja „Completeness” w README).

Próbka, dla której kanał nie ma wartości - brak w danej klatce albo wartość, która nie jest skończoną liczbą, taką jaką wysłała gra - jest zapisywana jako `null` przez każdy rejestrator (`lapfile.clean`), a udział zawieszenia wyliczony z niej też jest `null`. `NaN` i `Infinity` nigdy nie są zapisywane: nie są JSON-em, a `JSON.parse` w przeglądarce odrzuca cały plik z powodu jednej z nich. Czytnik powinien spodziewać się `null` w tablicy kanału.

Pliki Forzy mają `"game": "forza-horizon"`, `"forza-motorsport"` lub `"forza"` zależnie od wykrytego układu. Czytnik plików `.tele.gz` FH Companion w przeglądarce 3DHeat tworzy okrążenia z `"game": "forza-horizon"` i `meta.slip = "peak"`; ten czytnik jest w przeglądarce, nie tutaj. Okrążenia iRacing (czytane z `.ibt` w przeglądarce) mają `"game": "iracing"`, czego nie ma na liście wartości `game` rejestratorów wyżej, bo żaden rejestrator go nie zapisuje.

Zob. [Podział okrążeń i odcinków](lap-splitting.md), jak ustalane są `lap.number`, `lap.seconds` i `lap.complete`, oraz [Poślizg, dryf i kanały pochodne](slip-and-drift.md), co przeglądarka wylicza z tych kanałów.
