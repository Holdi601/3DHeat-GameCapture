---
title: "Trackmania (2020)"
nav_order: 5
lang: "bg"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Код: приставката за Openplanet [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder) (`info.toml`, `main.as`). **Приставката още не е пускана в играта**; четецът на нейния CSV във визуализатора е тестван.

## Защо приставка, която записва файлове {#why-a-plugin-that-writes-files}

Trackmania няма собствен изход за телеметрия. Openplanet, платформата за приставки на играта, показва състоянието на гледаното превозно средство на приставките, но приставките на Openplanet не могат да изпращат UDP. Затова приставката записва по един CSV файл за всеки заезд в собствената си папка за съхранение, а визуализаторът чете тези файлове такива, каквито са. Няма процес за запис: `telemetry --game trackmania` само инсталира приставката (с `--install`) и показва къде ще се появят файловете.

## Инсталиране и зареждане {#installing-and-loading}

- `--install` копира `mods/trackmania/Heat3dRecorder` в `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, като замества по-стар екземпляр. Без `--install` нищо не се копира.
- В играта: **Openplanet > Developer > Load plugin** и изберете `3DHeat recorder`.
- Приставката зависи от приставката **VehicleState** на Openplanet (`dependencies = ["VehicleState"]` в `info.toml`).
- Неподписаните приставки се зареждат само в **режима за разработчици на Openplanet**, който ограничава играта онлайн. Приставката може да бъде подписана на openplanet.dev; тук не е подписана.

Заездите се записват в `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Заредете тези CSV файлове в раздела „Състезателен анализ“ на визуализатора. `-o` и `--port` се пренебрегват за Trackmania.

## Какво записва приставката {#what-the-plugin-records}

Чете само това, което Openplanet показва - състоянието на гледаното превозно средство (`VehicleState::ViewingPlayerState()`) и времето на състезателя и броя на възраждания (`CSmScriptPlayer`) - не изпраща нищо никъде и не променя нищо в играта. Ред се записва на всеки кадър (`Update`), така че честотата на отчетите е честотата на кадрите в играта.

| Колона | Източник |
|---|---|
| `time` | `CurrentRaceTime` / 1000, секунди |
| `x`, `y`, `z` | `Position` (светът, Y нагоре) |
| `speed` | дължина на `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 или 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` на всяко колело (мярка за приплъзване от 0 до 1) |
| `loose` | 1, когато материалът под някое колело е Grass, Ice, Sand, Dirt, Green или RoadIce |
| `airborne` | 1, когато колата няма контакт със земята |
| `respawns` | възраждания от началото на заезда |

## Заезди {#runs}

- Заездът **започва** на първия кадър, където времето на състезанието не е отрицателно (обратното броене не се записва).
- Заездът **завършва**, когато UI последователността на игралната площадка е последователността на финала (стойност 11): файлът се записва като пълен, с последното време на състезанието като `seconds`.
- Заездът е **прекратен** - записва се с `_partial` в името и `"complete": false` - когато часовникът на състезанието се върне назад с над половин секунда (рестарт), или когато играчът напусне игралната площадка.
- Заезд с под 20 реда не се записва.

## Файлът {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Името е `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Името на картата е без кодовете за форматиране, а двойните кавички са заменени с единични. Стойностите се записват с четири десетични знака. Форматът е описан в [Файлът heat3d-lap](lap-format.md#the-csv-form).

В заглавието `meta` стои `"slip": "index"` - каналите `slipIndex.*` са собствената мярка на Trackmania за приплъзване от 0 до 1, а не физическо приплъзване - и `"discipline": "arcade"`.
