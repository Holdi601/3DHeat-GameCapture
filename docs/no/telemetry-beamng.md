---
title: BeamNG.drive
nav_order: 4
lang: "no"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # kopier modden, og ta så opp
python -m heat3d_capture telemetry --game beamng -o laps      # ta opp
```

Deretter i spillet: **Options > Other > Protocols**, slå på **"others"**. (Menyene står på engelsk, slik
spillet viser dem.)

Kode: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
og modden [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tester: `tests/test_beamng.py`, på pakker bygd fra modens struktur. **Modden er ennå ikke kjørt i
spillet.**

## Hvorfor en mod {#why-a-mod}

BeamNG sender telemetri gjennom "protokoller": Lua-moduler i kjøretøyet som spillets egen
`lua/vehicle/protocols.lua` pakker og sender over UDP fra bilen spilleren kjører. De innebygde
protokollene har ikke det en analyse av bilkontroll trenger. OutGauge har ingen posisjon, MotionSim har
ingen hjul, og OutSim er en stubb i nyere versjoner. Derfor leverer dette prosjektet sin egen
protokoll, `heat3d`. Den rører ingenting utenfor kjøretøyets egen Lua.

## Installere {#installing}

`--install` kopierer `mods/beamng/heat3d` til
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 og nyere har brukermodder
der). Den sletter en eldre kopi først, og skriver ut hvor den havnet. Uten `LOCALAPPDATA` brukes
hjemmemappen. Du kan også kopiere mappen for hånd.

`--install` fortsetter rett over til opptaket.

## Modden {#the-mod}

| Innstilling (i `heat3d.lua`) | Verdi |
|---|---|
| Adresse | `127.0.0.1` |
| Port | `4460` - endre den her, og send samme `--port` til opptakeren |
| Høyeste oppdateringshastighet | 100 Hz |
| Fysikksteg | brukt (`isPhysicsStepUsed` returnerer true) |

Hver pakke er den 4-byte lange markøren `H3D1` etterfulgt av 39 flyttall i little-endian (160 byte totalt):

| Felt | Antall | Kilde i kjøretøyets Lua |
|---|---|---|
| `time` | 1 | modens egen klokke: summen av fysikksteg, nullstilt når kjøretøyet nullstilles |
| posisjon | 3 | `obj:getPositionXYZ()` |
| hastighet | 3 | `obj:getVelocityXYZ()` (verden) |
| forover | 3 | `obj:getDirectionVector()` |
| opp | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, og 1/0 fra `absActive` og `tcsActive` |
| `wheelSpeed` | 4 | hvert hjuls overflatefart (m/s) |
| `wheelAngular` | 4 | vinkelhastighet ganget med hjulets retning (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 når hjulet er i luften |

De fire hjulene velges etter **hvor de sitter på bilen**, ikke etter navn. Navnene er forskjellige fra
kjøretøy til kjøretøy. Forran eller bak etter nodens posisjon langs bilen, venstre eller høyre på tvers
av den (kjøretøyets rammeretning +X er venstre, -Y er forover). For hvert hjørne tas hjulet lengst
unna midten. Et manglende hjørne sendes som nuller med materiale -1.

## Hva opptakeren gjør med det {#what-the-recorder-does-with-it}

BeamNGs verden har Z opp, visningsprogrammets har Y opp. Posisjoner og vektorer dreies om X,
`(x, y, z) -> (x, z, -y)`, som beholder verdenens håndhevelse. Deretter:

| Kanal | Utledet som |
|---|---|
| `x`, `y`, `z` | dreid posisjon |
| `speed` | lengden av den dreide hastigheten |
| `longVel`, `latVel`, `vertVel` | hastigheten projisert på forover, på høyre = forover x opp, på opp |
| `longAcc`, `latAcc`, `vertAcc` | endringen i verdenshastighet over +-2 prøver, projisert på de samme aksene (bilens egne sensorers rammeverk er ikke dokumentert, så de brukes ikke) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | som sendt |
| `absActive`, `tcActive` | ABS- og TC-lampene, der bilen har dem |
| `wheelSurfaceSpeed.*` | absoluttverdien av hjulets overflatefart |
| `wheelSpeed.*` | rotasjon |
| `wheelLoad.*` | belastning |
| `groundContact.*` | 0 når materialet er negativt, ellers 1 |

Pakker uten markøren, eller kortere enn 160 byte, ignoreres.

## Runder {#laps}

`LineSplitter`, som for AC EVO: punktet der opptaket startet er linjen. En runde lukkes der bilen neste
gang passerer nærmest den i samme retning, minst 300 m senere. En kjøring lukkes når bilen står stille i
8 sekunder. En runde regnes som fullført bare hvis den startet over 5 m/s, så den første runden fra
stillstand er en delrunde. Når modens klokke går bakover med mer enn et halvt sekund (bilen ble
nullstilt), lukkes kjøringen som var åpen i det øyeblikket først. Den skrives som delkjøring hvis den
dekket minst 300 m, akkurat som ved slutten av et opptak. Deretter starter delingen på nytt. Se
[Hvordan runder og etapper deles](lap-splitting.md).

## Rundefilen {#the-lap-file}

`game` er `beamng`, `meta` er `{"discipline": "circuit"}`, og filene heter
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Ingen sliring skrives. Visningsprogrammet utleder den
fra hjulenes overflatefart (se [Skli, drift og avledede kanaler](slip-and-drift.md)). Posisjonene er i
samme rammeverk som GameFiles-eksporten av BeamNG-baner skriver, så en innspilt runde sitter på en
eksportert bane.
