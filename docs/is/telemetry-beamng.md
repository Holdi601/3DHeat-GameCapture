---
title: "BeamNG.drive"
nav_order: 4
lang: "is"
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

Síðan í leiknum: **Options > Other > Protocols**, kveiktu á **„others“**.

Kóði: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
og modið [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Prófanir: `tests/test_beamng.py`, á pökkum smíðuðum úr gagnagerð modsins. **Modið hefur ekki enn verið
keyrt í leiknum.**

## Hvers vegna mod {#why-a-mod}

BeamNG sendir mælingagögn í gegnum „protocols“: Lua einingar í ökutækinu sem `lua/vehicle/protocols.lua`
leiksins sjálfs pakkar og sendir yfir UDP frá bílnum sem spilarinn ekur. Þær
innbyggðu bera ekki það sem greining á stjórn bílsins þarf - OutGauge hefur enga stöðu,
MotionSim engin hjól, og OutSim er tómt skrapatól í núverandi útgáfum. Því fylgir þessu verkefni sín eigin
samskiptaregla, `heat3d`. Hún snertir ekkert utan eigin Lua ökutækisins.

## Uppsetning {#installing}

`--install` afritar `mods/beamng/heat3d` í
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 og síðari geyma
notendamod þar), eyðir eldra afriti fyrst og prentar hvert það fór. Án
`LOCALAPPDATA` fellur það aftur á heimamöppuna. Þú getur líka afritað möppuna í höndunum.

`--install` heldur svo beint áfram í upptöku.

## Modið {#the-mod}

| Stilling (í `heat3d.lua`) | Gildi |
|---|---|
| Vistfang | `127.0.0.1` |
| Gátt (port) | `4460` - breyttu henni hér og gefðu sömu `--port` til upptökutækisins |
| Hámarks uppfærslutíðni | 100 Hz |
| Eðlisfræðiskref | notað (`isPhysicsStepUsed` skilar true) |

Hver pakki er 4 bæta töfratalan `H3D1` og síðan 39 little-endian float tölur (160 bæti
alls):

| Reitur | Fjöldi | Uppruni í Lua ökutækisins |
|---|---|---|
| `time` | 1 | eigin klukka modsins: summa eðlisfræðiskrefa, núllstillt þegar ökutækið endurstillist |
| staða | 3 | `obj:getPositionXYZ()` |
| hraði | 3 | `obj:getVelocityXYZ()` (heimur) |
| áfram | 3 | `obj:getDirectionVector()` |
| upp | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, og 1/0 úr `absActive` og `tcsActive` |
| `wheelSpeed` | 4 | yfirborðshraði hvers hjóls (m/s) |
| `wheelAngular` | 4 | hornhraði margfaldaður með stefnu hjólsins (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 þegar hjólið er af jörðu |

Hjólin fjögur eru valin eftir **því hvar þau sitja á bílnum**, ekki eftir heiti (heiti eru ólík milli
ökutækja): framan eða aftan eftir stöðu hnútsins eftir bílnum endilöngum, vinstri eða hægri þvert á hann
(ökutækjarammi: +X vinstri, -Y áfram), og fyrir hvert horn er tekið hjólið sem er lengst frá
miðju. Hornið sem vantar er sent sem núll með efni -1.

## Hvað upptökutækið gerir við það {#what-the-recorder-does-with-it}

Heimur BeamNG hefur Z upp; heimur skoðarans hefur Y upp. Stöður og vigrar eru snúin um X,
`(x, y, z) -> (x, z, -y)`, sem heldur handhverfu heimsins. Síðan:

| Rás | Leidd sem |
|---|---|
| `x`, `y`, `z` | snúin staða |
| `speed` | lengd snúna hraðans |
| `longVel`, `latVel`, `vertVel` | hraði varpað á áfram, á hægri = áfram x upp, og á upp |
| `longAcc`, `latAcc`, `vertAcc` | breyting heimshraðans yfir +-2 sýni, varpað á sömu ása (rammi eigin skynjara bílsins er óskjalfestur, svo þeir eru ekki notaðir) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | eins og sent |
| `absActive`, `tcActive` | ABS og TC ljósin, þar sem bíllinn hefur þau |
| `wheelSurfaceSpeed.*` | algildi yfirborðshraða hjólsins |
| `wheelSpeed.*` | snúningur |
| `wheelLoad.*` | álag |
| `groundContact.*` | 0 þegar efnið er neikvætt, annars 1 |

Pökkum án töfratölunnar eða styttri en 160 bæti er sleppt.

## Hringir {#laps}

`LineSplitter`, eins og fyrir AC EVO: staðurinn þar sem upptakan hófst er línan; hringur lokast
þar sem bíllinn fer næst henni í sömu stefnu, að minnsta kosti 300 m síðar; hlaupi lýkur
þegar bíllinn stendur kyrr í 8 sekúndur. Hringur telst fullkominn aðeins ef hann byrjaði á
meira en 5 m/s, svo fyrsti hringurinn úr kyrrstöðu er hlutahringur. Þegar klukka modsins fer aftur um meira en hálfa sekúndu (bílnum var endurstillt) er hlaupið sem er opið á því augnabliki
lokað fyrst - skrifað sem hlutahlaup þegar það náði að minnsta kosti 300 m, eins og í lok
upptöku - og síðan byrjar skiptirinn upp á nýtt. Sjá [Skipting í hringi og áfanga](lap-splitting.md).

## Hringskráin {#the-lap-file}

`game` er `beamng`, `meta` er `{"discipline": "circuit"}`, skrár heita
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Ekkert slip er skrifað; skoðarinn leiðir það af
yfirborðshraða hjólanna (sjá [Slip, skrið og afleiddar rásir](slip-and-drift.md)).
Stöðurnar eru í sama ramma og GameFiles BeamNG brautarútflutningurinn skrifar, svo skráður
hringur situr á útfluttri braut.
