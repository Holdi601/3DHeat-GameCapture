---
title: "Trackmania (2020)"
nav_order: 5
lang: "sr"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Код: Openplanet додатак [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Додатак још није покренут у игри**; читач његовог CSV-а у прегледачу је тестиран.

## Зашто додатак који пише фајлове {#why-a-plugin-that-writes-files}

Trackmania нема сопствени излаз телеметрије. Openplanet, платформа додатака игре, излаже додацима стање возила гледаног аутомобила, али Openplanet додаци не могу да шаљу UDP. Зато додатак пише по једну CSV датотеку по вожњи у своју фасциклу за складиштење, а прегледач чита те фајлове онакве какви јесу. Нема процеса снимача: `telemetry --game trackmania` само инсталира додатак (с `--install`) и исписује где ће се фајлови појавити.

## Инсталација и учитавање {#installing-and-loading}

- `--install` копира `mods/trackmania/Heat3dRecorder` у `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, замењујући старију копију. Без `--install` ништа се не копира.
- У игри: **Openplanet > Developer > Load plugin**, и изаберите `3DHeat recorder`.
- Додатак зависи од Openplanet-овог додатка **VehicleState** (`dependencies = ["VehicleState"]` у `info.toml`).
- Непотписани додаци се учитавају само у **режиму програмера Openplanet-а**, што ограничава игру на мрежи. Додатак се може потписати на openplanet.dev; овде није потписан.

Вожње се записују у `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Учитајте те CSV фајлове на картици „Анализа трке" у прегледачу. `-o` и `--port` се за Trackmania занемарују.

## Шта додатак бележи {#what-the-plugin-records}

Чита само оно што Openplanet излаже - стање возила гледаног аутомобила (`VehicleState::ViewingPlayerState()`) и време трке играча и број поновних појављивања (`CSmScriptPlayer`) - ништа никуда не шаље и ништа у игри не мења. Ред се записује на сваком кадру (`Update`), па је брзина узорковања брзина кадрова игре.

| Колона | Извор |
|---|---|
| `time` | `CurrentRaceTime` / 1000, секунде |
| `x`, `y`, `z` | `Position` (свет, Y нагоре) |
| `speed` | дужина `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 или 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` сваког точка (мера клизања 0..1) |
| `loose` | 1 кад је материјал тла било ког точка Grass, Ice, Sand, Dirt, Green или RoadIce |
| `airborne` | 1 кад аутомобил нема додир са тлом |
| `respawns` | поновна појављивања од почетка вожње |

## Вожње {#runs}

- Вожња **почиње** на првом кадру где време трке није негативно (одбројавање се не бележи).
- **Завршава се** кад је UI низ playground-а низ циља (вредност 11): фајл се записује као комплетан, а последње време трке је његов `seconds`.
- **Напушта се** - записује се с `_partial` у имену и `"complete": false` - кад сат трке врати назад за више од пола секунде (поновно покретање), или кад играч напусти playground.
- Вожња с мање од 20 редова се не записује.

## Фајл {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Именује се `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Из назива мапе уклањају се кодови за форматирање, а двоструки наводници се замењују једноструким. Вредности се записују с четири децимале. Формат је описан у [Датотека heat3d-lap](lap-format.md#the-csv-form).

`meta` у заглављу носи `"slip": "index"` - канали `slipIndex.*` су Trackmania-ина сопствена мера клизања 0..1, а не физичко клизање - и `"discipline": "arcade"`.
