---
title: "BeamNG.drive"
nav_order: 4
lang: "sk"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # skopírovať mod, potom nahrávať
python -m heat3d_capture telemetry --game beamng -o laps      # nahrávať
```

Potom v hre: **Options > Other > Protocols**, zapnite **"others"**.

Kód: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
a mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testy: `tests/test_beamng.py`, na paketoch postavených zo štruktúry modu. **Mod ešte nebol spustený
v hre.**

## Prečo mod {#why-a-mod}

BeamNG posiela telemetriu cez "protokoly": moduly Lua vo vozidle, ktoré vlastný
`lua/vehicle/protocols.lua` hry zabalí a pošle cez UDP z auta, ktoré hráč riadi. Štandardné
protokoly neobsahujú to, čo potrebuje analýza jazdy - OutGauge nemá pozíciu, MotionSim nemá kolesá
a OutSim je v aktuálnych verziách len kostra. Preto tento projekt prináša vlastný protokol,
`heat3d`. Nedotýka sa ničoho mimo Lua daného vozidla.

## Inštalácia {#installing}

`--install` skopíruje `mods/beamng/heat3d` do
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 a novší tam ukladajú
používateľské mody), najprv zmaže staršiu kópiu a vypíše, kam skopíroval. Bez `LOCALAPPDATA` použije
domovský priečinok. Priečinok môžete skopírovať aj ručne.

Potom `--install` pokračuje rovno do nahrávania.

## Mod {#the-mod}

| Nastavenie (v `heat3d.lua`) | Hodnota |
|---|---|
| Adresa | `127.0.0.1` |
| Port | `4460` - zmeňte ho tu a rovnaký zadajte cez `--port` v nahrávači |
| Najvyššia frekvencia aktualizácie | 100 Hz |
| Krok fyziky | použitý (`isPhysicsStepUsed` vracia true) |

Každý paket je 4-bajtová značka `H3D1` nasledovaná 39 floatmi v little-endian (celkom 160 bajtov):

| Pole | Počet | Zdroj vo vozidlovom Lua |
|---|---|---|
| `time` | 1 | vlastné hodiny modu: súčet krokov fyziky, vynulované pri resete vozidla |
| pozícia | 3 | `obj:getPositionXYZ()` |
| rýchlosť | 3 | `obj:getVelocityXYZ()` (svet) |
| dopredu | 3 | `obj:getDirectionVector()` |
| nahor | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, a 1/0 z `absActive` a `tcsActive` |
| `wheelSpeed` | 4 | rýchlosť povrchu každého kolesa (m/s) |
| `wheelAngular` | 4 | uhlová rýchlosť vynásobená smerom kolesa (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 keď je vo vzduchu |

Štyri kolesá sa vyberajú podľa **toho, kde sú na aute**, nie podľa názvu (názvy sa medzi vozidlami
líšia): vpredu alebo vzadu podľa polohy uzla pozdĺž auta, vľavo alebo vpravo naprieč ním (vozidlový
rámec +X vľavo, -Y dopredu), pre každý roh berie koleso najďalej od stredu. Chýbajúci roh sa posiela
ako nuly s materiálom -1.

## Čo s tým nahrávač robí {#what-the-recorder-does-with-it}

Svet BeamNG má Z nahor; svet prehliadača má Y nahor. Pozície a vektory sa otáčajú okolo X,
`(x, y, z) -> (x, z, -y)`, čím sa zachová pravotočivosť sveta. Potom:

| Kanál | Odvodenie |
|---|---|
| `x`, `y`, `z` | otočená pozícia |
| `speed` | dĺžka otočenej rýchlosti |
| `longVel`, `latVel`, `vertVel` | rýchlosť premietnutá na smer dopredu, na pravú stranu = dopredu x nahor, na hore |
| `longAcc`, `latAcc`, `vertAcc` | zmena svetovej rýchlosti za +-2 vzorky, premietnutá na tie isté osi (rámec senzorov auta nie je zdokumentovaný, preto sa nepoužívajú) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | tak, ako sa poslali |
| `absActive`, `tcActive` | kontrolky ABS a TC, kde ich auto má |
| `wheelSurfaceSpeed.*` | absolútna hodnota rýchlosti povrchu kolesa |
| `wheelSpeed.*` | otáčanie |
| `wheelLoad.*` | zaťaženie |
| `groundContact.*` | 0 keď je materiál záporný, inak 1 |

Pakety bez značky alebo kratšie ako 160 bajtov sa ignorujú.

## Kolá {#laps}

`LineSplitter`, rovnako ako pri AC EVO: bod, kde nahrávanie začalo, je čiara; kolo sa uzavrie tam,
kde auto najbližšie prejde okolo nej v rovnakom smere, aspoň 300 m neskôr; beh sa uzavrie, keď auto
stojí 8 sekúnd. Kolo sa počíta ako úplné len vtedy, ak začalo nad 5 m/s, takže prvé kolo zo štartu
z miesta je čiastočné. Keď hodiny modu klesnú o viac ako pol sekundy (auto bolo resetované), beh
otvorený v tom okamihu sa najprv uzavrie - zapíše sa ako čiastočný, ak pokryl aspoň 300 m, ako na
konci nahrávky - a potom sa delenie začne odznova. Pozrite [Delenie kôl a etáp](lap-splitting.md).

## Súbor kola {#the-lap-file}

`game` je `beamng`, `meta` je `{"discipline": "circuit"}`, súbory sa volajú
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Netreba žiadny prešmyk; prehliadač ho odvodí z
rýchlostí povrchu kolies (pozrite [Prešmyk, driftový uhol a odvodené kanály](slip-and-drift.md)). Pozície
sú v rovnakom rámci, v akom zapisuje export GameFiles pre BeamNG, takže nahrané kolo sedí na
exportovanej trati.
