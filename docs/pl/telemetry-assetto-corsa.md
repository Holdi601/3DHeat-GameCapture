---
title: Gry Assetto Corsa
nav_order: 2
lang: "pl"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO i AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kod: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testy: `tests/test_kunos.py` (syntetyczne strony). Jeszcze nie uruchamiane na działających grach.

## Skąd pochodzą dane {#where-the-data-comes-from}

Gry Kunos publikują telemetrię dla aplikacji jako **nazwane strony pamięci współdzielonej Windows**, które gra zapisuje, a z których może czytać każdy. Rejestrator otwiera je tylko do odczytu (`mmap` z nazwą znacznika), więc musi działać **na tym komputerze, na którym działa gra**, na Windows; gdzie indziej kończy działanie z komunikatem.

Strony są otwierane raz, gdy rejestrator startuje. Bezpieczna kolejność to najpierw uruchomić grę i wsiąść do samochodu; czy uruchomienie rejestratora przed grą działa, nie zostało sprawdzone.

| `--game` | Strona fizyki | Strona grafiki (licznik okrążeń) | Strona statyczna (nazwy) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nieużywana | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nieużywana | `Local\acevo_pmf_static` |

Stronę fizyki czyta się 200 razy na sekundę (`hz=200`); nowa próbka jest pobierana tylko wtedy, gdy zmienił się jej `packetId` i nie jest zerowy. Pierwsze 800 bajtów strony fizyki ma ten sam układ we wszystkich czterech grach; strona pierwszej gry ma gwarantowane tylko 580 bajtów, więc jeśli 800-bajtowego mapowania nie da się otworzyć, rejestrator wraca do 580, a pola poza tym są nieobecne.

## Pozycja {#position}

Żadna strona nie zawiera pozycji samochodu jako takiej, ale strona fizyki zawiera **punkt styku każdej opony we współrzędnych świata** (przesunięcie 420, cztery trójki XYZ). Pozycja samochodu to średnia z czterech. Strona, na której wszystkie punkty styku są zerowe (menu, garaż), nie daje próbki.

## Kanały {#channels}

| Kanał | Skąd | Uwagi |
|---|---|---|
| `time` | własny zegar rejestratora | sekundy od rozpoczęcia nagrywania, przesunięte do pierwszej próbki okrążenia |
| `x`, `y`, `z` | średni punkt styku opony | metry świata |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | jednostki gry, skalowane na okrążenie do -1..1 przez największą wartość bezwzględną użytą na tym okrążeniu, **tylko jeśli** ta wartość przekracza 1,05 (wejście już w zakresie -1..1 zostaje nietknięte) |
| `gear` | `gear - 1` | gra liczy 0 wsteczny, 1 luz, 2 pierwszy; zapisywane jako -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, razy 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | prędkość lokalna z przesunięcia 568 | układ samochodu; tylko gdy niezerowe. Strona, w którą wskazuje x, jest udokumentowana w obu kierunkach, więc czytaj wielkość kąta dryfu, nie jego znak |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | przesunięcie 564 | tylko strona 800-bajtowa |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: przesunięcia 204 i 252, zapisywane jako 1, gdy większe od 0; AC: `tcInAction`/`absInAction` ze strony 800-bajtowej, gdy jest | systemy wspomagania działają |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | wyliczane | 0..1 skoku użytego na tym okrążeniu (od min do max `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | przesunięcia 640, 656 (strona 800-bajtowa) | podzielone przez typowy szczyt - zob. niżej |
| `slipRatioRaw.*`, `slipAngleRaw.*` | to samo | wartości fizyczne, nieskalowane |
| `padLife.*`, `discLife.*` | przesunięcia 740, 756 | tylko strona 800-bajtowa |

AC Rally wysyła temperatury opon i hamulców w kelwinach: dla `--game acrally` każda z tych wartości powyżej 200 ma odjęte 273,15.

`wheelSlip` (przesunięcie 56) jest dekodowany, ale nie zapisywany.

## Skalowanie poślizgu {#slip-scaling}

Forza wysyła poślizg znormalizowany tak, że 1 to krawędź przyczepności. Kunos wysyła fizyczny współczynnik poślizgu podłużnego i kąt poślizgu bocznego. Więc rejestrator dzieli je przez typowy szczyt dla asfaltu - **0,12** dla współczynnika poślizgu i **0,14 rad (około 8 stopni)** dla kąta - tak, by odczyt przeglądarki „powyżej 1 znaczy ślizganie” w przybliżeniu się zgadzał, zachowuje surowe wartości obok nich i zapisuje `"meta": {"slip": "scaled"}`. Gdzie przyczepność faktycznie się kończy, przeglądarka mierzy dla każdego samochodu z okrążeń. Zob. [Poślizg, dryf i kanały pochodne](slip-and-drift.md).

## Okrążenia {#laps}

- **AC i ACC** liczą okrążenia na stronie grafiki (`completedLaps` w przesunięciu 132, czas ostatniego okrążenia w milisekundach w 144). `CounterSplitter` zamyka okrążenie, gdy licznik się zmienia; jest oznaczane jako ukończone, z czasem gry, tylko wtedy, gdy licznik wzrósł dokładnie o jeden.
- **AC EVO i AC Rally** nie są czytane pod kątem okrążeń (strona grafiki EVO ma inny, większy układ; AC Rally jeździ odcinkami). `LineSplitter` używa punktu, w którym zaczęto nagrywać, jako linii: okrążenie zamyka się, gdy samochód następnym razem przejedzie najbliżej niej, jadąc w tym samym kierunku, a odcinek lub dowolny przejazd zamyka się, gdy samochód stoi przez 8 sekund.

Szczegóły i progi: [Podział okrążeń i odcinków](lap-splitting.md).

## Nazwy toru i samochodu {#track-and-car-names}

Czytane raz, ze strony statycznej, gdy nadejdzie pierwsza próbka: dla AC, ACC i AC Rally samochód (UTF-16, przesunięcie 68) i tor (przesunięcie 134); dla AC EVO tor i jego konfiguracja (tekst jednobajtowy w przesunięciach 136 i 169, połączone spacją) i bez samochodu. Trafiają do pliku jako `track` i `car: {"name": ...}`.

## Plik okrążenia {#the-lap-file}

`game` to `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` lub `assetto-corsa-rally`; `meta` to `{"slip": "scaled", "discipline": "rally"}` dla AC Rally i `{"slip": "scaled", "discipline": "circuit"}` dla pozostałych trzech. `surface` nie jest zapisywane.

## Źródła {#sources}

SDK pamięci współdzielonej AC1; dokumentacja pamięci współdzielonej ACC (v1.8); układ AC EVO zmierzony w `albertowd/live-telemetry-evo`; układ AC Rally odczytany przez `LuizZak/AssettoCorsaRallyTelemetryReader`. Zob. [Gry](games.md).
