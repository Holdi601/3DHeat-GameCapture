---
title: Forza
nav_order: 1
lang: "pl"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon i Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(wykrywanie układu),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(wszystkie kanały, pliki okrążeń, przekaźnik).

## Włączenie w grze {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (albo cokolwiek podasz w `--port`). Forza Motorsport oferuje też format pakietu: musi to być **Dash**, a nie Sled. Sled nie zawiera w ogóle pozycji, a rejestrator go odrzuca.

Rejestrator wiąże się z `127.0.0.1`, więc gra musi działać na tym samym komputerze.

## Co wysyła gra i jak znajdowany jest układ {#what-the-game-sends-and-how-the-layout-is-found}

Data Out to jeden pakiet UDP na tik symulacji (około 60 na sekundę), płaska struktura C little-endian w tych rozmiarach:

| Długość | Wariant |
|---|---|
| 232 bajty | Motorsport „Sled”: bez pozycji. Odrzucany z komunikatem, by przełączyć na Dash. |
| 311 bajtów | Motorsport „Dash”: blok Sled plus 79-bajtowy blok deski rozdzielczej |
| 324 bajty | Horizon „Dash”: to samo z dopełnieniem między dwoma blokami |
| 331 bajtów | Forza Motorsport (2023): Dash plus 20 bajtów zużycia opon i identyfikator toru |

Blok Sled (przesunięcia 0-231) jest stabilny. Gdzie w wariancie Horizon zaczyna się blok deski rozdzielczej, jest opisane niespójnie w publikowanych źródłach, a zgadnięcie złe nie zawodzi - daje wiarygodnie wyglądające liczby zmiennoprzecinkowe z niewłaściwych pól. Więc początek jest **odkrywany**:

1. Kandydackie początki są próbowane w kolejności: `length - 79` (blok deski rozdzielczej kończy się na ostatnim bajcie w każdym udokumentowanym wariancie), 232, 244 i 232 do 260 co 4.
2. Każdy kandydat jest oceniany na pakietach z poruszającego się samochodu (składowa prędkości powyżej 1 m/s): wektor prędkości z bloku Sled i skalarne `Speed` z bloku deski to ta sama wielkość w dwóch miejscach, więc `| |velocity| - Speed |` jest bliskie zera tylko dla właściwego początku.
3. Wygrywa kandydat z najmniejszą najgorszą niezgodnością, jeśli ta niezgodność wynosi co najwyżej **1 m/s**. W przeciwnym razie wykrywanie nadal czeka.

Gdy samochód stoi, każdy kandydat czyta zera i wszystkie się zgadzają, co niczego nie dowodzi, więc **wykrywanie czeka, aż samochód się poruszy**: przejedź kilka metrów, zanim spodziewasz się wyniku. Do 600 pakietów jest trzymanych w czasie oczekiwania (przycinane do najnowszych 300). Gdy układ jest znany, trzymane pakiety są też dekodowane, więc początek pierwszego okrążenia się nie gubi. Pakiety o innej długości niż wykryty układ, pakiety krótsze niż 311 bajtów i pakiety z niebędącą skończoną liczbą pozycją lub prędkością są ignorowane przy plikach okrążeń.

Która Forza to jest, wynika z układu: układ Horizon daje `"game": "forza-horizon"`, układ Motorsport lub 331-bajtowy daje `"forza-motorsport"`, a każdy inny `"forza"`. Nazwa wykrytego układu (`Horizon dash`, `Motorsport dash`, `331-byte dash`) jest zapisywana jako `layout`.

## Nagrywane kanały {#channels-recorded}

Każde pole pakietu jest dekodowane (`decode_full`) i przeliczane:

- pedały `throttle`, `brake`, `clutch`, `handbrake` z 0..255 do 0..1;
- `steer` z -127..127 do -1..1; `drivingLine` i `aiBrakeDifference` tak samo, dzielone przez 127;
- `tireTemp.FL` ... `.RR` z Fahrenheita na Celsjusza;
- `latAcc`, `longAcc`, `vertAcc` i `yawRate` są kopiami `accelX`, `accelZ`, `accelY` i `angVelY` pod kanonicznymi nazwami (układ samochodu: x w prawo, y w górę, z do przodu);
- prędkość z Sled, podana w układzie współrzędnych samochodu (x w prawo, y w górę, z do przodu - nie świata), jest zapisywana wprost pod kanonicznymi nazwami `latVel`, `vertVel` i `longVel`, tak by przeglądarka odczytywała z niej kąt dryfu zamiast go szacować z kierunku i trasy.

Plik okrążenia zawiera wszystkie te kanały, poza polami przypadającymi na okrążenie:

| Grupa | Kanały |
|---|---|
| Czas i miejsce | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Ruch | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Silnik | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Kierowca | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Na koło (`.FL .FR .RL .RR`) | `suspension` (0 wysunięte .. 1 ściśnięte), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (znormalizowane: powyżej 1 opona traci przyczepność), `wheelSpeed` (rad/s), `rumble` (na pasie wibracyjnym), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Tylko Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` to bieżący zegar okrążenia gry minus jego wartość w pierwszej próbce okrążenia; `distance` to przejechany dystans gry minus jego pierwsza wartość. Pozycje to współrzędne świata Forzy w metrach, niezmienione (y w górę; świat jest lewoskrętny).

Brane raz na okrążenie, a nie na próbkę, pod `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Identyfikator toru FM2023 też trafia raz, jako `lap.trackOrdinal`. Nie są zachowywane na próbkę: `isRaceOn` (1 w każdej klatce okrążenia). `timestampMs`, `raceTime`, `bestLap` i `lastLap` są zachowywane jako kanały.

Reszta dokumentu jest wypełniana jak u każdego innego rejestratora:

- `"track": null` - Forza Horizon nie nazywa toru, a Forza Motorsport tylko go numeruje;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kanały poślizgu są znormalizowane tak, że powyżej 1 opona traci przyczepność;
- `units` wymienia tylko kanały, które plik ma (kanały per koło po ich nazwie podstawowej);
- wartość, która nie jest skończoną liczbą, jest zapisywana jako `null`, nigdy jako `NaN`.

Zob. [Plik heat3d-lap](lap-format.md).

## Podział okrążeń {#how-laps-are-split}

`LapSplitter` (zob. [Podział okrążeń i odcinków](lap-splitting.md)): okrążenie zamyka się, gdy licznik okrążeń gry się przesuwa, a jego czasem jest wtedy własne `lastLap` gry (to, co gra pokazuje). Przejazd punkt-do-punktu albo sesja kończąca się w połowie okrążenia zamyka się, gdy gra opuszcza wyścig (`isRaceOn` spada), gdy pakiety przestają przychodzić przez 2 sekundy albo gdy znacznik czasu gry cofa się; jest zachowywany jako `run`, jeśli objął co najmniej 400 m.

## Przekazywanie do FH Companion {#relaying-to-fh-companion}

Gra wysyła Data Out tylko na jeden adres. Z `--forward host:port` rejestrator przekazuje **każdy otrzymany pakiet bez zmian**, zanim cokolwiek zdekoduje (także podczas czekania na wykrycie układu), więc inna aplikacja czytająca strumień działa dalej: ustaw grę na 5300, drugą aplikację na 5301 i uruchom z `--forward 127.0.0.1:5301`.

FH Companion to osobna aplikacja, a nie część 3DHeat. Prowadzi bibliotekę okrążeń w `%LOCALAPPDATA%\FHCompanion\laps`: folder na tor, jeden plik okrążenia na okrążenie próbkowany co około pięć metrów, a obok każdego pliku okrążenia `<lap>.json.tele.gz` - cały Data Out okrążenia w szybkości gry. 3DHeat czyta oba:

- **Przeglądarka czyta `.tele.gz` wprost**, gdy upuścisz go (z plikiem okrążenia albo bez) na zakładkę Analiza wyścigowa. Mapuje nazwy pól Forzy (`PositionX`, `VelocityX`, `TireSlipRatio` + koło, ...) na kanały kanoniczne, zamienia lokalne dla samochodu `VelocityX/Y/Z` na `latVel`, `vertVel`, `longVel`, przelicza temperatury opon z Fahrenheita, odrzuca wiersze, które powtarzają poprzedni, różniąc się tylko zegarem rejestratora, i oznacza poślizg jako `peak`. Gdy podany jest też plik okrążenia, okrążenie bierze z niego samochód i czas. Ten czytnik jest w przeglądarce (`src/race/adapters.ts`, `readForzaTelemetry`), a nie w tym repozytorium.
- **Polecenie `laps`** czyta bibliotekę okrążeń i zapisuje trasę toru oraz CSV każdej próbki; zob. [Dokumentacja poleceń](commands.md#laps).

## Inne zastosowania tego samego strumienia {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` nagrywa tylko pozycje, zapisywane co kilka sekund podczas jazdy; zob. [Dokumentacja poleceń](commands.md#route).
- Opcja okna skanowania „Racing telemetry (Forza)” używa strumienia jako dokładnych póz kamery do rekonstrukcji; zob. [Poza kamery i skala](reconstruction-pose.md#telemetry-poses).

## Uwagi i zastrzeżenia {#notes-and-caveats}

- Do czego Forza normalizuje poślizg, nie jest udokumentowane. `1` jest odczytywane jako krawędź przyczepności, ale przeglądarka mierzy, gdzie przyczepność każdego samochodu faktycznie słabnie.
- Prędkość z Sled jest lokalna dla samochodu, jak mówi dokumentacja Data Out Forzy i potwierdzają nagrane okrążenia (jej składowa do przodu niesie prędkość, a boczna zostaje blisko zera). Wykrywanie układu używa tylko jej długości, która jest taka sama w każdej ramce.
- Pozycje są światem gry, z Y w górę i lewoskrętne. Kierunki `yaw`, `pitch` i `roll` sprawdzono na nagranych okrążeniach: yaw równa się kierunkowi jazdy `atan2(dx, dz)`, dodatni pitch to nos w dół, a dodatni roll opuszcza prawą stronę.
