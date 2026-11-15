---
title: "BeamNG.drive"
nav_order: 4
lang: "sq"
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

Pastaj te loja: **Options > Other > Protocols**, ndez **"others"**.

Kodi: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
dhe moduli [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testet: `tests/test_beamng.py`, mbi pakete të ndërtuara nga struct-i i modulit. **Moduli ende nuk është
ekzekutuar në lojë.**

## Pse një modul {#why-a-mod}

BeamNG dërgon telemetri përmes "protokolleve": module Lua në automjet që `lua/vehicle/protocols.lua`
i vetë lojës i paketon dhe i dërgon me UDP nga makina që drejton lojtari. Ato të përfshira
nuk mbartin atë që i duhet një analize të kontrollit të makinës - OutGauge nuk ka pozicion,
MotionSim nuk ka rrota, dhe OutSim është një stub në versionet e tanishme. Ndaj ky projekt sjell protokollin e vet,
`heat3d`. Nuk prek asgjë jashtë Lua-s së vetë automjetit.

## Instalimi {#installing}

`--install` kopjon `mods/beamng/heat3d` te
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 e më vonë i mbajnë
modulet e përdoruesit aty), duke fshirë fillimisht një kopje më të vjetër, dhe printon ku shkoi. Pa
`LOCALAPPDATA` kthehet te dosja kryesore e përdoruesit. Mund ta kopjosh dosjen edhe me dorë.

Pastaj `--install` vazhdon drejtpërdrejt te regjistrimi.

## Moduli {#the-mod}

| Cilësimi (te `heat3d.lua`) | Vlera |
|---|---|
| Adresa | `127.0.0.1` |
| Porta | `4460` - ndryshoje këtu dhe jepi të njëjtën `--port` regjistruesit |
| Shpejtësia maksimale e përditësimit | 100 Hz |
| Hapi i fizikës | përdoret (`isPhysicsStepUsed` kthen true) |

Çdo paketë është magjia 4-bajtëshe `H3D1` e ndjekur nga 39 float little-endian (160 bajt
gjithsej):

| Fusha | Numri | Burimi në Lua të automjetit |
|---|---|---|
| `time` | 1 | ora e vetë modulit: shuma e hapave të fizikës, rivendoset kur automjeti rivendoset |
| pozicioni | 3 | `obj:getPositionXYZ()` |
| shpejtësia | 3 | `obj:getVelocityXYZ()` (bota) |
| përpara | 3 | `obj:getDirectionVector()` |
| lart | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, dhe 1/0 nga `absActive` dhe `tcsActive` |
| `wheelSpeed` | 4 | shpejtësia e sipërfaqes së çdo rrote (m/s) |
| `wheelAngular` | 4 | shpejtësia këndore shumëzuar me drejtimin e rrotës (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 kur është larg tokës |

Katër rrotat zgjidhen sipas **vendit ku ndodhen në makinë**, jo sipas emrit (emrat ndryshojnë mes
automjeteve): përpara ose prapa sipas pozicionit të nyjës gjatë makinës, majtas ose djathtas përgjatë saj
(në kornizën e automjetit +X majtas, -Y përpara), duke marrë për çdo cep rrotën më të largët nga
qendra. Një cep që mungon dërgohet si zero me material -1.

## Çfarë bën regjistruesi me të {#what-the-recorder-does-with-it}

Bota e BeamNG ka Z lart; ajo e shikuesit ka Y lart. Pozicionet dhe vektorët rrotullohen rreth X,
`(x, y, z) -> (x, z, -y)`, që e ruan orientimin e botës. Pastaj:

| Kanali | Nxirret si |
|---|---|
| `x`, `y`, `z` | pozicioni i rrotulluar |
| `speed` | gjatësia e shpejtësisë së rrotulluar |
| `longVel`, `latVel`, `vertVel` | shpejtësia e projektuar mbi përpara, mbi djathtas = përpara x lart, mbi lart |
| `longAcc`, `latAcc`, `vertAcc` | ndryshimi i shpejtësisë së botës mbi +-2 mostra, i projektuar mbi të njëjtat bosht (korniza e sensorëve të vetë makinës nuk është e dokumentuar, ndaj nuk përdoren) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | siç dërgohen |
| `absActive`, `tcActive` | llambat ABS dhe TC, ku i ka makina |
| `wheelSurfaceSpeed.*` | vlera absolute e shpejtësisë së sipërfaqes së rrotës |
| `wheelSpeed.*` | rrotullimi |
| `wheelLoad.*` | ngarkesa |
| `groundContact.*` | 0 kur materiali është negativ, përndryshe 1 |

Paketat pa magjinë ose më të shkurtra se 160 bajt shpërfillen.

## Xhirat {#laps}

`LineSplitter`, si për AC EVO: pika ku nisi regjistrimi është vija; një xhiro mbyllet
aty ku makina kalon sërish më afër saj me të njëjtin drejtim, të paktën 300 m më vonë; një ecje
mbyllet kur makina qëndron e ndalur 8 sekonda. Një xhiro llogaritet e plotë vetëm nëse nisi me
më shumë se 5 m/s, ndaj xhiroja e parë nga qëndrimi është e pjesshme. Kur ora e modulit kthehet pas me më shumë se
gjysmë sekonde (makina u rivendos), ecja e hapur në atë çast mbyllet së pari -
shkruhet si ecje e pjesshme kur ka mbuluar të paktën 300 m, si në fund të një
regjistrimi - dhe pastaj ndarësi nis nga e para. Shih [Ndarja e xhirave dhe e etapave](lap-splitting.md).

## Skedari i xhirasë {#the-lap-file}

`game` është `beamng`, `meta` është `{"discipline": "circuit"}`, skedarët emërtohen
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Nuk shkruhet slip; shikuesi e nxjerr
nga shpejtësitë e sipërfaqes së rrotave (shih [Slip, drift dhe kanalet e nxjerra](slip-and-drift.md)).
Pozicionet janë në të njëjtën kornizë që shkruan eksporti i kursit BeamNG i GameFiles, ndaj një
xhiro e regjistruar bie mbi një kurs të eksportuar.
