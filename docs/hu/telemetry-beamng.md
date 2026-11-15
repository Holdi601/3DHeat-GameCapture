---
title: BeamNG.drive
nav_order: 4
lang: "hu"
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

Ezután a játékban: **Options > Other > Protocols** (Beállítások > Egyéb > Protokollok), kapcsolja be az
**„others”** (mások) opciót.

Kód: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
és a módosítás, [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tesztek: `tests/test_beamng.py`, a módosítás struktúrájából épített csomagokon. **A módosítást a játékban még
nem futtatták.**

## Miért módosítás {#why-a-mod}

A BeamNG a telemetriát „protokollokon” keresztül küldi: a járműben futó Lua-modulok, amelyeket a játék saját
`lua/vehicle/protocols.lua` fájlja csomagol és küld UDP-n keresztül a játékos által vezetett autóból. A beépített
protokollok nem hordozzák azt, amire egy autóvezetés-elemzéshez szükség van: az OutGauge-ban nincs pozíció, a
MotionSimben nincsenek kerekek, az OutSim pedig a jelenlegi verziókban csonk. Ezért ez a projekt saját protokollt
szállít, `heat3d` néven. Nem nyúl a járművön kívülihez: csak a jármű saját Lua-kódját érinti.

## Telepítés {#installing}

Az `--install` átmásolja a `mods/beamng/heat3d` mappát a
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` helyre (a BeamNG 0.30-tól kezdve a felhasználói
modok ide kerülnek), előbb törölve a régebbi másolatot, és kiírja, hová került. `LOCALAPPDATA` nélkül a
saját mappába esik vissza. A mappát kézzel is átmásolhatja.

Az `--install` ezután rögtön folytatja a rögzítéssel.

## A módosítás {#the-mod}

| Beállítás (a `heat3d.lua`-ban) | Érték |
|---|---|
| Cím | `127.0.0.1` |
| Port | `4460` - itt változtassa meg, és a rögzítőnek ugyanazt a `--port` értéket adja meg |
| Maximális frissítési sebesség | 100 Hz |
| Fizikai lépés | használva (az `isPhysicsStepUsed` igazat ad vissza) |

Minden csomag a 4 bájtos `H3D1` azonosítóval kezdődik, majd 39 little-endian float következik (összesen
160 bájt):

| Mező | Darab | Forrás a jármű Lua-kódjában |
|---|---|---|
| `time` | 1 | a módosítás saját órája: a fizikai lépések összege, a jármű visszaállításakor nullázva |
| pozíció | 3 | `obj:getPositionXYZ()` |
| sebesség | 3 | `obj:getVelocityXYZ()` (világ) |
| előre | 3 | `obj:getDirectionVector()` |
| fel | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, valamint 1/0 az `absActive` és `tcsActive` értékekből |
| `wheelSpeed` | 4 | minden kerék felületi sebessége (m/s) |
| `wheelAngular` | 4 | szögsebesség, szorozva a kerék irányával (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1, ha nincs talajon |

A négy kereket **az autón elfoglalt helyük** alapján választjuk ki, nem a nevük alapján (a nevek járművenként
eltérnek): elöl vagy hátul az autó hossza mentén, bal vagy jobb oldalt a keresztirányban (a jármű keretében
+X balra, -Y előre), minden sarokhoz a középponttól legtávolabbi kereket véve. Hiányzó sarok nullákként megy,
anyaga -1.

## Amit a rögzítő csinál vele {#what-the-recorder-does-with-it}

A BeamNG világában a Z felfelé mutat, a megjelenítőében az Y. A pozíciókat és vektorokat az X tengely körül
forgatjuk, `(x, y, z) -> (x, z, -y)`, ami megőrzi a világ kezességét. Ezután:

| Csatorna | Számítás |
|---|---|
| `x`, `y`, `z` | az elforgatott pozíció |
| `speed` | az elforgatott sebesség hossza |
| `longVel`, `latVel`, `vertVel` | a sebesség vetülete előre, jobbra (= előre x fel) és fel tengelyre |
| `longAcc`, `latAcc`, `vertAcc` | a világbeli sebesség változása ±2 minta között, ugyanezekre a tengelyekre vetítve (az autó saját szenzorainak keretrendszere nincs dokumentálva, ezért nem használjuk őket) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | ahogy küldték |
| `absActive`, `tcActive` | az ABS- és TC-lámpák, ahol az autónak van |
| `wheelSurfaceSpeed.*` | a kerék felületi sebességének abszolút értéke |
| `wheelSpeed.*` | forgás |
| `wheelLoad.*` | terhelés |
| `groundContact.*` | 0, ha az anyag negatív, egyébként 1 |

A magic nélküli vagy 160 bájtnál rövidebb csomagokat figyelmen kívül hagyjuk.

## Körök {#laps}

`LineSplitter`, ahogy az AC EVO-nál: a rögzítés kezdő pontja a vonal; egy kör akkor zárul, ha az autó legközelebb
ugyanolyan irányban áthalad rajta, legalább 300 m-rel később. Egy futás akkor zárul, ha az autó 8 másodpercig áll.
Egy kör csak akkor számít teljesnek, ha 5 m/s felett kezdődött, így az álló helyzetből induló első kör részleges.
Ha a módosítás órája több mint fél másodperccel visszaugrik (az autó visszaállt), a pillanatban nyitott futást
előbb lezárjuk - részleges futásként írva, ha legalább 300 m-t tett meg, ahogy a felvétel végén is -, majd a
bontó újrakezdi. Lásd: [Kör- és szakaszbontás](lap-splitting.md).

## A körfájl {#the-lap-file}

A `game` értéke `beamng`, a `meta` értéke `{"discipline": "circuit"}`, a fájlok neve
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Csúszás nem íródik; a megjelenítő a kerekek felületi
sebességeiből számolja ki (lásd: [Csúszás, driftelés és származtatott csatornák](slip-and-drift.md)). A
pozíciók ugyanabban a keretben vannak, mint amelyben a GameFiles BeamNG pályaexportja írja őket, így a
rögzített kör ráül egy exportált pályára.
