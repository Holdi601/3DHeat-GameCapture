---
title: BeamNG.drive
nav_order: 4
lang: "da"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # kopier modet, og optag derefter
python -m heat3d_capture telemetry --game beamng -o laps      # optag
```

Derefter i spillet: **Options > Other > Protocols**, slå **"others"** til.

Kode: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
og modet [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tests: `tests/test_beamng.py`, på pakker bygget ud fra modets struct. **Modet er endnu ikke blevet
kørt i spillet.**

## Hvorfor et mod {#why-a-mod}

BeamNG sender telemetri gennem "protokoller": Lua-moduler i køretøjet, som spillets egen
`lua/vehicle/protocols.lua` pakker og sender over UDP fra den bil, spilleren kører. De faste har ikke det,
en bilkontrolanalyse har brug for - OutGauge har ingen position, MotionSim ingen hjul, og OutSim er en
stub i nyere versioner. Så dette projekt leverer sin egen protokol, `heat3d`. Den rører intet uden for
køretøjets egen Lua.

## Installation {#installing}

`--install` kopierer `mods/beamng/heat3d` til
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 og nyere gemmer brugermods
der), sletter en ældre kopi først, og skriver hvor den blev lagt. Uden `LOCALAPPDATA` falder den tilbage til
hjemmemappen. Du kan også kopiere mappen selv.

`--install` fortsætter derefter direkte over i optagelsen.

## Modet {#the-mod}

| Indstilling (i `heat3d.lua`) | Værdi |
|---|---|
| Adresse | `127.0.0.1` |
| Port | `4460` - ændr den her, og giv den samme `--port` til optageren |
| Maksimal opdateringshastighed | 100 Hz |
| Fysisk trin | brugt (`isPhysicsStepUsed` returnerer sand) |

Hver pakke er den 4 byte lange magi `H3D1` efterfulgt af 39 little-endian floats (160 byte i alt):

| Felt | Antal | Kilde i køretøjets Lua |
|---|---|---|
| `time` | 1 | modets eget ur: sum af fysiske trin, nulstilles når køretøjet nulstilles |
| position | 3 | `obj:getPositionXYZ()` |
| hastighed | 3 | `obj:getVelocityXYZ()` (verden) |
| forward | 3 | `obj:getDirectionVector()` |
| up | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, og 1/0 fra `absActive` og `tcsActive` |
| `wheelSpeed` | 4 | hvert hjuls overfladehastighed (m/s) |
| `wheelAngular` | 4 | vinkelhastighed gange hjulets retning (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 når hjulet er fri af jorden |

De fire hjul vælges efter **hvor de sidder på bilen**, ikke efter navn (navnene varierer mellem køretøjer):
forrest eller bagest efter nodens position langs bilen, venstre eller højre på tværs af den (køretøjets
ramme +X venstre, -Y fremad), og for hvert hjørne det hjul, der er længst fra midten. Et manglende hjørne
sendes som nuller med materiale -1.

## Hvad optageren gør med den {#what-the-recorder-does-with-it}

BeamNGs verden har Z op; viewerens har Y op. Positioner og vektorer drejes om X,
`(x, y, z) -> (x, z, -y)`, som bevarer verdens håndedhed. Derefter:

| Kanal | Udledt som |
|---|---|
| `x`, `y`, `z` | den drejede position |
| `speed` | længden af den drejede hastighed |
| `longVel`, `latVel`, `vertVel` | hastigheden projiceret på forward, på højre = forward x up, på up |
| `longAcc`, `latAcc`, `vertAcc` | ændringen i verdenshastighed over +-2 prøver, projiceret på de samme akser (bilens egne sensorers ramme er udokumenteret, så de bruges ikke) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | som sendt |
| `absActive`, `tcActive` | ABS- og TC-lamperne, hvor bilen har dem |
| `wheelSurfaceSpeed.*` | absolut værdi af hjulets overfladehastighed |
| `wheelSpeed.*` | rotation |
| `wheelLoad.*` | belastning |
| `groundContact.*` | 0 når materialet er negativt, ellers 1 |

Pakker uden magien, eller kortere end 160 byte, ignoreres.

## Lap'e {#laps}

`LineSplitter`, som for AC EVO: det punkt, hvor optagelsen begyndte, er linjen; et lap lukkes der, hvor
bilen næste gang passerer tættest på den med samme retning, mindst 300 m senere; en kørsel lukkes, når bilen
står stille i 8 sekunder. Et lap tæller kun som komplet, hvis det begyndte ved mere end 5 m/s, så det første
lap fra stille start er et delvist. Når modets ur går tilbage med mere end et halvt sekund (bilen blev
nulstillet), lukkes den kørsel, der var åben i det øjeblik, først - skrevet som en delvis kørsel, når den
dækkede mindst 300 m, som ved slutningen af en optagelse - og derefter starter splitteren forfra. Se
[Opdeling i lap og etaper](lap-splitting.md).

## Lap-filen {#the-lap-file}

`game` er `beamng`, `meta` er `{"discipline": "circuit"}`, filerne navngives
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Ingen slip skrives; vieweren udleder den fra hjulenes
overfladehastigheder (se [Slip, drift og afledte kanaler](slip-and-drift.md)). Positionerne er i samme ramme,
som GameFiles-eksporten af en BeamNG-bane skriver, så et optaget lap ligger på en eksporteret bane.
