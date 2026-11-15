---
title: "BeamNG.drive"
nav_order: 4
lang: "pl"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copy the mod, then record
python -m heat3d_capture telemetry --game beamng -o laps      # record
```

Potem w grze: **Options > Other > Protocols**, włącz **„others”**.

Kod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
i mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testy: `tests/test_beamng.py`, na pakietach zbudowanych z struktury moda. **Mod nie został jeszcze uruchomiony w grze.**

## Dlaczego mod {#why-a-mod}

BeamNG wysyła telemetrię przez „protokoły”: moduły Lua w pojeździe, które własny plik gry
`lua/vehicle/protocols.lua` pakuje i wysyła przez UDP z samochodu, którym jedzie gracz. Standardowe nie niosą
tego, czego potrzebuje analiza sterowania samochodem - OutGauge nie ma pozycji, MotionSim nie ma kół, a OutSim
w bieżących wersjach jest atrapą. Dlatego ten projekt dostarcza własny protokół, `heat3d`. Nie dotyka niczego
poza Lua własnego pojazdu.

## Instalacja {#installing}

`--install` kopiuje `mods/beamng/heat3d` do `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d`
(BeamNG 0.30 i nowsze trzymają tam modyfikacje użytkownika), najpierw usuwając starszą kopię, i wypisuje, dokąd
trafiła. Bez `LOCALAPPDATA` wraca do folderu domowego. Folder możesz też skopiować ręcznie.

Po `--install` od razu przechodzi do nagrywania.

## Mod {#the-mod}

| Ustawienie (w `heat3d.lua`) | Wartość |
|---|---|
| Adres | `127.0.0.1` |
| Port | `4460` - zmień go tutaj i podaj ten sam `--port` rejestratorowi |
| Najwyższa częstotliwość aktualizacji | 100 Hz |
| Krok fizyki | używany (`isPhysicsStepUsed` zwraca true) |

Każdy pakiet to 4-bajtowy znacznik `H3D1`, po którym następuje 39 liczb zmiennoprzecinkowych little-endian
(w sumie 160 bajtów):

| Pole | Liczba | Źródło w Lua pojazdu |
|---|---|---|
| `time` | 1 | zegar moda: suma kroków fizyki, zerowany przy resecie pojazdu |
| pozycja | 3 | `obj:getPositionXYZ()` |
| prędkość | 3 | `obj:getVelocityXYZ()` (świat) |
| do przodu | 3 | `obj:getDirectionVector()` |
| w górę | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, oraz 1/0 z `absActive` i `tcsActive` |
| `wheelSpeed` | 4 | prędkość powierzchni każdego koła (m/s) |
| `wheelAngular` | 4 | prędkość kątowa razy kierunek koła (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 gdy koło jest w powietrzu |

Cztery koła wybiera się według **tego, gdzie stoją na samochodzie**, a nie po nazwie (nazwy różnią się między
pojazdami): przód lub tył według położenia węzła wzdłuż samochodu, lewe lub prawe w poprzek (układ pojazdu:
+X w lewo, -Y do przodu), dla każdego narożnika biorąc koło najdalsze od środka. Brakujący narożnik wysyła się
jako zera z materiałem -1.

## Co rejestrator z tym robi {#what-the-recorder-does-with-it}

Świat BeamNG ma Z w górę; przeglądarka ma Y w górę. Pozycje i wektory obraca się wokół osi X,
`(x, y, z) -> (x, z, -y)`, co zachowuje skrętność świata. Potem:

| Kanał | Wyliczany jako |
|---|---|
| `x`, `y`, `z` | obrócona pozycja |
| `speed` | długość obróconej prędkości |
| `longVel`, `latVel`, `vertVel` | prędkość rzutowana na kierunek do przodu, na prawo (= do przodu x w górę), na górę |
| `longAcc`, `latAcc`, `vertAcc` | zmiana prędkości świata w ±2 próbkach, rzutowana na te same osie (układ czujników samochodu nie jest udokumentowany, więc nie są używane) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | jak wysłano |
| `absActive`, `tcActive` | lampki ABS i TC, tam gdzie samochód je ma |
| `wheelSurfaceSpeed.*` | wartość bezwzględna prędkości powierzchni koła |
| `wheelSpeed.*` | obrót |
| `wheelLoad.*` | obciążenie |
| `groundContact.*` | 0, gdy materiał jest ujemny, w przeciwnym razie 1 |

Pakiety bez znacznika albo krótsze niż 160 bajtów są ignorowane.

## Okrążenia {#laps}

`LineSplitter`, tak jak dla AC EVO: linią jest punkt, w którym zaczęto nagrywać; okrążenie zamyka się tam, gdzie
samochód następnym razem przejeżdża najbliżej niej, jadąc w tym samym kierunku, co najmniej 300 m później;
przejazd zamyka się, gdy samochód stoi przez 8 sekund. Okrążenie liczy się jako pełne tylko wtedy, gdy zaczęło
się z prędkością powyżej 5 m/s, więc pierwsze okrążenie ze startu z miejsca jest częściowe. Gdy zegar moda
cofnie się o ponad pół sekundy (samochód został zresetowany), przejazd otwarty w tym momencie zostaje najpierw
zamknięty - zapisany jako częściowy, gdy pokrył co najmniej 300 m, jak na końcu nagrania - i dopiero potem
dzielenie zaczyna się od nowa. Zobacz [Podział okrążeń i odcinków](lap-splitting.md).

## Plik okrążenia {#the-lap-file}

`game` to `beamng`, `meta` to `{"discipline": "circuit"}`, pliki nazywają się
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Poślizg nie jest zapisywany; przeglądarka wylicza go z
prędkości powierzchni kół (zobacz [Poślizg, dryf i kanały pochodne](slip-and-drift.md)). Pozycje są w tym
samym układzie, który zapisuje eksport toru BeamNG z GameFiles, więc nagrane okrążenie leży na wyeksportowanym
torze.
