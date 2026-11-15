---
title: "Trackmania (2020)"
nav_order: 5
lang: "pl"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kod: wtyczka Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Wtyczka nie została jeszcze uruchomiona w grze**; czytnik jej CSV w przeglądarce
jest testowany.

## Dlaczego wtyczka zapisująca pliki {#why-a-plugin-that-writes-files}

Trackmania nie ma własnego wyjścia telemetrii. Openplanet, platforma wtyczek gry, udostępnia wtyczkom stan
oglądanego pojazdu, ale wtyczki Openplanet nie mogą wysyłać UDP. Dlatego wtyczka zapisuje jeden plik CSV na
przejazd we własnym folderze magazynu, a przeglądarka czyta te pliki tak, jak są. Nie ma procesu rejestratora:
`telemetry --game trackmania` tylko instaluje wtyczkę (z `--install`) i wypisuje, gdzie pojawią się pliki.

## Instalacja i wczytywanie {#installing-and-loading}

- `--install` kopiuje `mods/trackmania/Heat3dRecorder` do `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`,
  zastępując starszą kopię. Bez `--install` nic nie jest kopiowane.
- W grze: **Openplanet > Developer > Load plugin** i wybierz `3DHeat recorder`.
- Wtyczka zależy od wtyczki **VehicleState** Openplanet (`dependencies = ["VehicleState"]` w `info.toml`).
- Niepodpisane wtyczki wczytują się tylko w **trybie dewelopera Openplanet**, który ogranicza grę online.
  Wtyczkę można podpisać na openplanet.dev; tutaj nie jest podpisana.

Przejazdy zapisują się w `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Wczytaj te pliki CSV na
zakładce Analiza wyścigowa w przeglądarce. `-o` i `--port` są dla Trackmanii ignorowane.

## Co wtyczka zapisuje {#what-the-plugin-records}

Czyta tylko to, co udostępnia Openplanet - stan oglądanego pojazdu (`VehicleState::ViewingPlayerState()`) oraz
czas wyścigu gracza i liczbę respawnów (`CSmScriptPlayer`) - niczego nigdzie nie wysyła i niczego w grze nie
zmienia. Wiersz zapisuje się przy każdej klatce (`Update`), więc częstotliwość próbkowania to liczba klatek
gry na sekundę.

| Kolumna | Źródło |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekundy |
| `x`, `y`, `z` | `Position` (świat, Y w górę) |
| `speed` | długość `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 lub 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` każdego koła (miara poślizgu 0..1) |
| `loose` | 1, gdy materiał podłoża któregokolwiek koła to Grass, Ice, Sand, Dirt, Green albo RoadIce |
| `airborne` | 1, gdy samochód nie ma kontaktu z podłożem |
| `respawns` | respawny od startu przejazdu |

## Przejazdy {#runs}

- Przejazd **zaczyna się** w pierwszej klatce, w której czas wyścigu nie jest ujemny (odliczanie nie jest
  zapisywane).
- **Kończy się**, gdy sekwencja UI placu zabaw jest sekwencją mety (wartość 11): plik zapisuje się jako
  kompletny, z ostatnim czasem wyścigu jako `seconds`.
- Jest **porzucany** - zapisywany z `_partial` w nazwie i `"complete": false` - gdy zegar wyścigu cofnie się
  o ponad pół sekundy (restart) albo gdy gracz opuści plac zabaw.
- Przejazd z mniej niż 20 wierszami się nie zapisuje.

## Plik {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Nazwa: `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Z nazwy mapy usuwane są kody formatowania, a podwójne
cudzysłowy zamieniane na pojedyncze. Wartości zapisuje się z czterema miejscami po przecinku. Format opisano w
[Plik heat3d-lap](lap-format.md#the-csv-form).

Pole `meta` w nagłówku niesie `"slip": "index"` - kanały `slipIndex.*` to własna miara poślizgu Trackmanii
w skali 0..1, a nie fizyczny poślizg - oraz `"discipline": "arcade"`.
