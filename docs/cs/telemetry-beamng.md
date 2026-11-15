---
title: BeamNG.drive
nav_order: 4
lang: "cs"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # zkopírovat mod, pak nahrávat
python -m heat3d_capture telemetry --game beamng -o laps      # nahrávat
```

Potom ve hře: **Options > Other > Protocols**, zapněte **"others"**.

Kód: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
a mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testy: `tests/test_beamng.py`, na paketech sestavených podle struktury modu. **Mod zatím nebyl spuštěn ve hře.**

## Proč mod {#why-a-mod}

BeamNG posílá telemetrii přes „protokoly“: moduly Lua ve vozidle, které vlastní `lua/vehicle/protocols.lua` hry zabalí a pošle přes UDP z auta, které hráč řídí. Standardní protokoly nenesou to, co potřebuje analýza ovládání auta. OutGauge nemá pozici, MotionSim nemá kola a OutSim je v aktuálních verzích jen prázdná kostra. Proto tento projekt přichází s vlastním protokolem `heat3d`. Nedotýká se ničeho mimo Lua vozidla.

## Instalace {#installing}

`--install` zkopíruje `mods/beamng/heat3d` do `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 a novější tam ukládají uživatelské mody). Nejdřív smaže starší kopii a vypíše, kam šlo. Bez `LOCALAPPDATA` se použije domovská složka. Složku můžete zkopírovat i ručně.

`--install` pak pokračuje rovnou do nahrávání.

## Mod {#the-mod}

| Nastavení (v `heat3d.lua`) | Hodnota |
|---|---|
| Adresa | `127.0.0.1` |
| Port | `4460`: změňte ho tady a předejte stejný `--port` záznamníku |
| Nejvyšší frekvence aktualizace | 100 Hz |
| Krok fyziky | použit (`isPhysicsStepUsed` vrací true) |

Každý paket je 4bajtová značka `H3D1`, za ní 39 float v little-endian (celkem 160 bajtů):

| Pole | Počet | Zdroj ve Lua vozidla |
|---|---|---|
| `time` | 1 | vlastní hodiny modu: součet kroků fyziky, nulované při resetu vozidla |
| pozice | 3 | `obj:getPositionXYZ()` |
| rychlost | 3 | `obj:getVelocityXYZ()` (světová) |
| dopředu | 3 | `obj:getDirectionVector()` |
| nahoru | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, a 1/0 z `absActive` a `tcsActive` |
| `wheelSpeed` | 4 | povrchová rychlost každého kola (m/s) |
| `wheelAngular` | 4 | úhlová rychlost krát směr kola (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, −1 když je kolo ve vzduchu |

Čtyři kola se vybírají podle toho, **kde sedí na autě**, ne podle jména (názvy se mezi vozidly liší). Přední nebo zadní se určí podle polohy uzlu podél auta, levé nebo pravé napříč (rámec vozidla: +X vlevo, −Y vpřed). U každého rohu se vezme kolo nejdál od středu. Chybějící roh se pošle jako nuly s materiálem −1.

## Co s tím dělá záznamník {#what-the-recorder-does-with-it}

Svět BeamNG má Z nahoru, prohlížeč má Y nahoru. Pozice a vektory se proto otočí kolem X, `(x, y, z) -> (x, z, -y)`, což zachová orientaci světa. Potom:

| Kanál | Odvozeno jako |
|---|---|
| `x`, `y`, `z` | otočená pozice |
| `speed` | délka otočené rychlosti |
| `longVel`, `latVel`, `vertVel` | rychlost promítnutá na dopředu, na vpravo (dopředu × nahoru) a na nahoru |
| `longAcc`, `latAcc`, `vertAcc` | změna světové rychlosti přes ±2 vzorky, promítnutá na tytéž osy (rámec vlastních senzorů auta není zdokumentován, proto se nepoužívají) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | jak přišly |
| `absActive`, `tcActive` | kontrolky ABS a TC, kde je auto má |
| `wheelSurfaceSpeed.*` | absolutní hodnota povrchové rychlosti kola |
| `wheelSpeed.*` | otáčení |
| `wheelLoad.*` | zatížení |
| `groundContact.*` | 0, když je materiál záporný, jinak 1 |

Pakety bez značky nebo kratší než 160 bajtů se ignorují.

## Kola {#laps}

`LineSplitter`, jako u AC EVO: bod, kde nahrávání začalo, je čára. Kolo se uzavře tam, kde auto příště projede nejblíž k ní ve stejném směru, nejméně 300 m později. Běh se uzavře, když auto stojí 8 sekund. Kolo se počítá jako úplné jen tehdy, když začalo nad 5 m/s, takže první kolo z rozjezdu z klidu je částečné. Když hodiny modu přeskočí zpět o víc než půl sekundy (auto bylo resetováno), běh otevřený v tu chvíli se nejdřív uzavře. Zapíše se jako částečný, když pokryl nejméně 300 m, jako na konci nahrávání. Potom se dělení začne znovu. Viz [Dělení kol a etap](lap-splitting.md).

## Soubor kola {#the-lap-file}

`game` je `beamng`, `meta` je `{"discipline": "circuit"}`, soubory se jmenují `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Neukládá se žádný skluz. Prohlížeč ho odvodí z povrchových rychlostí kol (viz [Skluz, drift a odvozené kanály](slip-and-drift.md)). Pozice jsou ve stejném rámci, v jakém zapisuje export kurzu GameFiles pro BeamNG, takže zaznamenané kolo sedí na exportovaném kurzu.
