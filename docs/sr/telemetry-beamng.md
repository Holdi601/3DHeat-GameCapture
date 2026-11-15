---
title: "BeamNG.drive"
nav_order: 4
lang: "sr"
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

Затим у игри: **Options > Other > Protocols**, и укључите **"others"**.

Код: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
и модификација [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Тестови: `tests/test_beamng.py`, на пакетима састављеним од структуре модификације. **Модификација још није покренута у игри.**

## Зашто модификација {#why-a-mod}

BeamNG шаље телеметрију преко „протокола": Lua модула у возилу које сопствени `lua/vehicle/protocols.lua` игре пакује и шаље преко UDP-а из аутомобила којим игра вози. Стандардни не носе оно што је анализи управљања аутомобилом потребно - OutGauge нема положај, MotionSim нема точкове, а OutSim је празан оквир у актуелним верзијама. Зато овај пројекат испоручује свој протокол, `heat3d`. Не дира ништа ван Lua-е самог возила.

## Инсталација {#installing}

`--install` копира `mods/beamng/heat3d` у `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 и новији држе корисничке модификације тамо), брише старију копију пре тога и исписује куда је отишла. Без `LOCALAPPDATA` враћа се на кућну фасциклу. Фасциклу можете копирати и ручно.

`--install` затим одмах прелази на снимање.

## Модификација {#the-mod}

| Подешавање (у `heat3d.lua`) | Вредност |
|---|---|
| Адреса | `127.0.0.1` |
| Порт | `4460` - промените га овде и проследите исти `--port` снимачу |
| Највећа брзина освежавања | 100 Hz |
| Корак физике | користи се (`isPhysicsStepUsed` враћа true) |

Сваки пакет је 4-бајтни запис `H3D1`, па затим 39 float-ова у little-endian формату (укупно 160 бајтова):

| Поље | Број | Извор у Lua-и возила |
|---|---|---|
| `time` | 1 | сопствени сат модификације: збир корака физике, поништава се кад се возило врати на почетак |
| положај | 3 | `obj:getPositionXYZ()` |
| брзина | 3 | `obj:getVelocityXYZ()` (свет) |
| смер напред | 3 | `obj:getDirectionVector()` |
| смер горе | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, и 1/0 из `absActive` и `tcsActive` |
| `wheelSpeed` | 4 | брзина површине сваког точка (m/s) |
| `wheelAngular` | 4 | угаона брзина помножена смером точка (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 кад је ван тла |

Четири точка бирају се по **месту на аутомобилу**, а не по имену (имена се разликују између возила): предњи или задњи по положају чвора дуж аутомобила, леви или десни попречно (оквир возила +X лево, -Y напред), узимајући за сваки ћошак точак најдаљи од средишта. Недостајући ћошак се шаље као нуле с материјалом -1.

## Шта снимач ради с тим {#what-the-recorder-does-with-it}

BeamNG-ов свет има Z нагоре; прегледачев има Y нагоре. Положаји и вектори се окрећу око X-а, `(x, y, z) -> (x, z, -y)`, што чува руку света. Затим:

| Канал | Израчунава се као |
|---|---|
| `x`, `y`, `z` | окренути положај |
| `speed` | дужина окренуте брзине |
| `longVel`, `latVel`, `vertVel` | брзина пројектована на напред, на десно = напред × горе, на горе |
| `longAcc`, `latAcc`, `vertAcc` | промена брзине света током ±2 узорка, пројектована на исте осе (оквир сопствених сензора аутомобила није документован, па се не користе) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | како се шаљу |
| `absActive`, `tcActive` | лампице ABS-а и TC-а, где их аутомобил има |
| `wheelSurfaceSpeed.*` | апсолутна вредност брзине површине точка |
| `wheelSpeed.*` | обртање |
| `wheelLoad.*` | оптерећење |
| `groundContact.*` | 0 кад је материјал негативан, иначе 1 |

Пакети без записа или краћи од 160 бајтова се занемарују.

## Кругови {#laps}

`LineSplitter`, као за AC EVO: тачка где је снимање почело је линија; круг се затвара где аутомобил следећи пут прође најближе њој у истом смеру, најмање 300 m касније; вожња се затвара кад аутомобил стоји 8 секунди. Круг се сматра завршеним само ако је почео брже од 5 m/s, па је први круг из стања мировања делимичан. Кад сат модификације врати назад за више од пола секунде (аутомобил је враћен на почетак), вожња отворена у том тренутку прво се затвара - записује се као делимична ако је покрила најмање 300 m, као на крају снимка - па делилац почиње испочетка. Погледајте [Подела на кругове и деонице](lap-splitting.md).

## Датотека круга {#the-lap-file}

`game` је `beamng`, `meta` је `{"discipline": "circuit"}`, датотеке се зову `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Клизање се не записује; прегледач га изводи из брзина површине точкова (погледајте [Клизање, дриф и изведени канали](slip-and-drift.md)). Положаји су у истом оквиру у којем извоз BeamNG курса из GameFiles-а пише, па снимљени круг лежи на извезеном курсу.
