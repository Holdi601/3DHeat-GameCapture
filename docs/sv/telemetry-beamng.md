---
title: BeamNG.drive
nav_order: 4
lang: "sv"
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

Sedan i spelet: **Options > Other > Protocols**, slå på **"others"**.

Kod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
och modden [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tester: `tests/test_beamng.py`, på paket byggda från modens struct. **Modden har ännu inte körts i spelet.**

## Varför en mod {#why-a-mod}

BeamNG skickar telemetri via "protokoll": Lua-moduler i fordonet som spelets egen
`lua/vehicle/protocols.lua` packar och skickar över UDP från bilen spelaren kör. De inbyggda
protokollen bär inte det en analys av bilkörning behöver - OutGauge har ingen position, MotionSim
inga hjul, och OutSim är en stubb i aktuella versioner. Så projektet levererar sitt eget protokoll,
`heat3d`. Det rör ingenting utanför fordonets egen Lua.

## Installera {#installing}

`--install` kopierar `mods/beamng/heat3d` till
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 och senare har
användarmoder där), tar bort en äldre kopia först, och skriver ut vart den gick. Utan `LOCALAPPDATA`
faller den tillbaka till hemmappen. Du kan också kopiera mappen för hand.

`--install` fortsätter sedan direkt med inspelningen.

## Modden {#the-mod}

| Inställning (i `heat3d.lua`) | Värde |
|---|---|
| Adress | `127.0.0.1` |
| Port | `4460` - ändra den här och skicka samma `--port` till inspelaren |
| Maximal uppdateringstakt | 100 Hz |
| Fysiksteg | används (`isPhysicsStepUsed` returnerar true) |

Varje paket är den 4-byte långa markören `H3D1` följt av 39 little-endian-flyttal (160 byte totalt):

| Fält | Antal | Källa i fordonets Lua |
|---|---|---|
| `time` | 1 | modens egen klocka: summan av fysiksteg, nollställd när fordonet återställs |
| position | 3 | `obj:getPositionXYZ()` |
| hastighet | 3 | `obj:getVelocityXYZ()` (världen) |
| framåt | 3 | `obj:getDirectionVector()` |
| upp | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, och 1/0 från `absActive` och `tcsActive` |
| `wheelSpeed` | 4 | varje hjuls ytfart (m/s) |
| `wheelAngular` | 4 | vinkelhastighet gånger hjulets riktning (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 när hjulet är utanför marken |

De fyra hjulen väljs efter **var de sitter på bilen**, inte efter namn (namnen skiljer sig mellan
fordon): fram eller bak efter nodens position längs bilen, vänster eller höger tvärs över den (fordonets
ram +X vänster, -Y framåt), och för varje hörn det hjul som ligger längst från mitten. Ett saknat hörn
skickas som nollor med material -1.

## Vad inspelaren gör med den {#what-the-recorder-does-with-it}

BeamNGs värld har Z uppåt; visarens har Y uppåt. Positioner och vektorer vrids kring X,
`(x, y, z) -> (x, z, -y)`, vilket behåller världens högerhänthet. Sedan:

| Kanal | Härleds som |
|---|---|
| `x`, `y`, `z` | vriden position |
| `speed` | längden av den vridna hastigheten |
| `longVel`, `latVel`, `vertVel` | hastigheten projicerad på framåt, på höger = framåt x upp, på upp |
| `longAcc`, `latAcc`, `vertAcc` | förändringen i världshastighet över +-2 sampel, projicerad på samma axlar (bilens egna sensorers ram är odokumenterad, så de används inte) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | som skickade |
| `absActive`, `tcActive` | ABS- och TC-lamporna, där bilen har dem |
| `wheelSurfaceSpeed.*` | absolutbeloppet av hjulets ytfart |
| `wheelSpeed.*` | rotation |
| `wheelLoad.*` | belastning |
| `groundContact.*` | 0 när materialet är negativt, annars 1 |

Paket utan markören eller kortare än 160 byte ignoreras.

## Varv {#laps}

`LineSplitter`, som för AC EVO: punkten där inspelningen började är linjen; ett varv stängs där bilen
nästa gång passerar närmast den i samma riktning, minst 300 m senare; en körning stängs när bilen
står still i 8 sekunder. Ett varv räknas som komplett bara om det började över 5 m/s, så det första
varvet från en stillastående start är ett partiellt. När modens klocka går bakåt mer än en halv sekund
(bilen återställdes) stängs först den körning som var öppen i det ögonblicket - skriven som en partiell
körning om den täckte minst 300 m, som i slutet av en inspelning - och sedan börjar delningen om. Se
[Varv- och etappdelning](lap-splitting.md).

## Varvfilen {#the-lap-file}

`game` är `beamng`, `meta` är `{"discipline": "circuit"}`, filerna heter
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Ingen slip skrivs; visaren härleder den från
hjulens ytfarter (se [Slip, drift och härledda kanaler](slip-and-drift.md)). Positionerna är i samma
ram som GameFiles BeamNG-banexport skriver, så ett inspelat varv sitter på en exporterad bana.
