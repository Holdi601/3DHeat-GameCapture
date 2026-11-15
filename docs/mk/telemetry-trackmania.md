---
title: "Trackmania"
nav_order: 5
lang: "mk"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Код: приклучокот за Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Приклучокот сè уште не е пуштен во играта**; читачот на неговиот CSV
во прегледувачот е тестиран.

## Зошто приклучок што пишува датотеки {#why-a-plugin-that-writes-files}

Trackmania нема сопствен излез на телеметрија. Openplanet, платформата за приклучоци на играта,
им ја изложува на приклучоците состојбата на возилото што се гледа, но приклучоците на
Openplanet не можат да праќаат UDP. Затоа приклучокот пишува по една CSV датотека за секое
возење во својата папка за складирање, а прегледувачот ги чита тие датотеки како што се. Нема
процес на снимач: `telemetry --game trackmania` само го инсталира приклучокот (со `--install`) и
печати каде ќе се појават датотеките.

## Инсталирање и вчитување {#installing-and-loading}

- `--install` ја копира `mods/trackmania/Heat3dRecorder` во
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, заменувајќи постара копија. Без
  `--install` ништо не се копира.
- Во играта: **Openplanet > Developer > Load plugin**, и изберете `3DHeat recorder`.
- Приклучокот зависи од приклучокот **VehicleState** на Openplanet
  (`dependencies = ["VehicleState"]` во `info.toml`).
- Непотпишаните приклучоци се вчитуваат само во **развојниот режим на Openplanet**, што го
  ограничува играњето онлајн. Приклучокот може да се потпише на openplanet.dev; тука не е
  потпишан.

Возењата се запишуваат во `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Вчитајте
ги тие CSV датотеки во табот Анализа на трка на прегледувачот. `-o` и `--port` се игнорираат за
Trackmania.

## Што снима приклучокот {#what-the-plugin-records}

Чита само она што го изложува Openplanet - состојбата на возилото што се гледа
(`VehicleState::ViewingPlayerState()`) и времето на трката и бројот на повторни појавувања на
играчот (`CSmScriptPlayer`) - не праќа ништо никаде и не менува ништо во играта. Ред се запишува
на секоја рамка (`Update`), па стапката на отчитување е стапката на рамки на играта.

| Колона | Извор |
|---|---|
| `time` | `CurrentRaceTime` / 1000, секунди |
| `x`, `y`, `z` | `Position` (свет, Y нагоре) |
| `speed` | должината на `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 или 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` на секое тркало (мерка за лизгање од 0..1) |
| `loose` | 1 кога материјалот на земјата на кое било тркало е Grass, Ice, Sand, Dirt, Green или RoadIce |
| `airborne` | 1 кога автомобилот нема контакт со земјата |
| `respawns` | повторни појавувања откако почнало возењето |

## Возења {#runs}

- Возењето **почнува** на првата рамка каде времето на трката не е негативно (одбројувањето не
  се снима).
- **Завршува** кога UI-секвенцата на теренот е секвенцата за цел (вредност 11): датотеката се
  запишува како комплетна, со последното време на трката како нејзино `seconds`.
- Се **напушта** - се запишува со `_partial` во името и `"complete": false` - кога часовникот
  на трката ќе појде наназад за повеќе од половина секунда (рестарт), или кога играчот ќе го
  напушти теренот.
- Возење со помалку од 20 реда не се запишува.

## Датотеката {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Се вика `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Од името на мапата се отстрануваат кодовите
за форматирање, а двојните наводници се заменуваат со единечни. Вредностите се запишуваат со
четири децимали. Форматот е опишан во [Датотеката heat3d-lap](lap-format.md#the-csv-form).

`meta` во заглавјето носи `"slip": "index"` - каналите `slipIndex.*` се сопствената мерка за
лизгање од 0..1 на Trackmania, а не физичко лизгање - и `"discipline": "arcade"`.
