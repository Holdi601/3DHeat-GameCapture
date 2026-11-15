---
title: "Trackmania"
nav_order: 5
lang: "ro"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Cod: modulul Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Modulul nu a fost încă rulat în joc**; cititorul din vizualizator al
fișierului său CSV este testat.

## De ce un modul care scrie fișiere {#why-a-plugin-that-writes-files}

Trackmania nu are o ieșire proprie de telemetrie. Openplanet, platforma de module a jocului, expune
modulelor starea vehiculului mașinii văzute, dar modulele Openplanet nu pot trimite UDP. Așa că modulul
scrie un fișier CSV pentru fiecare rulare în folderul său de stocare, iar vizualizatorul citește
fișierele așa cum sunt. Nu există un proces înregistrator: `telemetry --game trackmania` doar instalează
modulul (cu `--install`) și afișează unde vor apărea fișierele.

## Instalarea și încărcarea {#installing-and-loading}

- `--install` copiază `mods/trackmania/Heat3dRecorder` în
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, înlocuind o copie mai veche. Fără `--install`
  nu se copiază nimic.
- În joc: **Openplanet > Developer > Load plugin**, și alegeți `3DHeat recorder`.
- Modulul depinde de modulul **VehicleState** al Openplanet (`dependencies = ["VehicleState"]` în
  `info.toml`).
- Modulele nesemnate se încarcă doar în **modul dezvoltator al Openplanet**, care limitează jocul
  online. Modulul poate fi semnat pe openplanet.dev; aici nu este semnat.

Rulările sunt scrise în `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Încărcați aceste
fișiere CSV în fila Analiză de cursă a vizualizatorului. `-o` și `--port` sunt ignorate pentru
Trackmania.

## Ce înregistrează modulul {#what-the-plugin-records}

Citește doar ce expune Openplanet - starea vehiculului mașinii văzute
(`VehicleState::ViewingPlayerState()`) și timpul de cursă al jucătorului și numărul de reapariții
(`CSmScriptPlayer`) - nu trimite nimic nicăieri și nu schimbă nimic în joc. Un rând este scris la fiecare
cadru (`Update`), deci rata de eșantionare este rata de cadre a jocului.

| Coloană | Sursa |
|---|---|
| `time` | `CurrentRaceTime` / 1000, secunde |
| `x`, `y`, `z` | `Position` (lume, Y în sus) |
| `speed` | lungimea lui `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 sau 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` al fiecărei roți (o măsură a alunecării între 0 și 1) |
| `loose` | 1 când materialul de sub vreuna dintre roți este Grass, Ice, Sand, Dirt, Green sau RoadIce |
| `airborne` | 1 când mașina nu are contact cu solul |
| `respawns` | reapariții de la începutul rulării |

## Rulări {#runs}

- O rulare **începe** pe primul cadru unde timpul de cursă nu este negativ (numărătoarea inversă nu
  este înregistrată).
- Se **termină** când secvența de interfață a playground-ului este secvența de final (valoarea 11):
  fișierul este scris ca complet, cu ultimul timp de cursă ca `seconds`.
- Este **abandonată** - scrisă cu `_partial` în nume și cu `"complete": false` - când ceasul cursei dă
  înapoi cu mai mult de o jumătate de secundă (o repornire), sau când jucătorul părăsește playground-ul.
- O rulare cu mai puțin de 20 de rânduri nu este scrisă.

## Fișierul {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Numit `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Numele hărții are codurile de formatare eliminate, iar
ghilimelele duble sunt înlocuite cu cele simple. Valorile sunt scrise cu patru zecimale. Formatul este
descris în [Fișierul heat3d-lap](lap-format.md#the-csv-form).

Antetul `meta` conține `"slip": "index"` - canalele `slipIndex.*` sunt măsura proprie a Trackmania de la
0 la 1 pentru alunecare, nu un slip fizic - și `"discipline": "arcade"`.
