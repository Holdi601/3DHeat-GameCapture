---
title: BeamNG.drive
nav_order: 4
lang: "nl"
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

Zet daarna in het spel onder **Options > Other > Protocols** de optie **"others"** aan.

Code: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py) en de mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tests: `tests/test_beamng.py`, op pakketten die zijn gebouwd uit de struct van de mod. **De mod is nog niet in het spel gedraaid.**

## Waarom een mod {#why-a-mod}

BeamNG stuurt telemetrie via "protocols": Lua-modules in het voertuig die het eigen `lua/vehicle/protocols.lua` van het spel inpakt en via UDP verstuurt vanaf de auto die de speler bestuurt. De standaardprotocollen bevatten niet wat een analyse van de autobesturing nodig heeft: OutGauge heeft geen positie, MotionSim geen wielen, en OutSim is in de huidige versies een stub. Daarom levert dit project een eigen protocol, `heat3d`. Het raakt niets buiten de eigen Lua van het voertuig aan.

## Installeren {#installing}

`--install` kopieert `mods/beamng/heat3d` naar `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 en later bewaart gebruikersmods daar), verwijdert eerst een oudere kopie, en drukt af waar het naartoe ging. Zonder `LOCALAPPDATA` valt het terug op de thuismap. Je kunt de map ook met de hand kopiëren.

Daarna gaat `--install` meteen door met opnemen.

## De mod {#the-mod}

| Instelling (in `heat3d.lua`) | Waarde |
|---|---|
| Adres | `127.0.0.1` |
| Poort | `4460` - wijzig het hier en geef dezelfde `--port` aan de recorder |
| Maximale updatesnelheid | 100 Hz |
| Physics-stap | gebruikt (`isPhysicsStepUsed` geeft true terug) |

Elk pakket bestaat uit de 4-byte magic `H3D1`, gevolgd door 39 little-endian floats (160 bytes in totaal):

| Veld | Aantal | Bron in de Lua van het voertuig |
|---|---|---|
| `time` | 1 | de eigen klok van de mod: som van de physics-stappen, gereset wanneer het voertuig wordt gereset |
| positie | 3 | `obj:getPositionXYZ()` |
| snelheid | 3 | `obj:getVelocityXYZ()` (wereld) |
| vooruit | 3 | `obj:getDirectionVector()` |
| omhoog | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, en 1/0 uit `absActive` en `tcsActive` |
| `wheelSpeed` | 4 | de oppervlaktesnelheid van elk wiel (m/s) |
| `wheelAngular` | 4 | hoeksnelheid maal de richting van het wiel (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 wanneer het niet de grond raakt |

De vier wielen worden gekozen op **waar ze op de auto zitten**, niet op naam (namen verschillen per voertuig): voor of achter op basis van de positie van de node langs de auto, links of rechts ervan (voertuigframe +X links, -Y vooruit), en per hoek het wiel dat het verst van het midden zit. Een ontbrekende hoek wordt verzonden als nullen met materiaal -1.

## Wat de recorder ermee doet {#what-the-recorder-does-with-it}

De wereld van BeamNG heeft Z omhoog; die van de viewer heeft Y omhoog. Posities en vectoren worden om X gedraaid, `(x, y, z) -> (x, z, -y)`, wat de handigheid van de wereld behoudt. Daarna:

| Kanaal | Afgeleid als |
|---|---|
| `x`, `y`, `z` | gedraaide positie |
| `speed` | lengte van de gedraaide snelheid |
| `longVel`, `latVel`, `vertVel` | snelheid geprojecteerd op vooruit, op rechts = vooruit x omhoog, op omhoog |
| `longAcc`, `latAcc`, `vertAcc` | de verandering in wereldsnelheid over ±2 samples, geprojecteerd op dezelfde assen (het eigen assenstelsel van de sensoren van de auto is niet gedocumenteerd, dus die worden niet gebruikt) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | zoals verzonden |
| `absActive`, `tcActive` | de ABS- en TC-lampjes, waar de auto ze heeft |
| `wheelSurfaceSpeed.*` | absolute waarde van de oppervlaktesnelheid van het wiel |
| `wheelSpeed.*` | rotatie |
| `wheelLoad.*` | belasting |
| `groundContact.*` | 0 wanneer het materiaal negatief is, anders 1 |

Pakketten zonder de magic of korter dan 160 bytes worden genegeerd.

## Ronden {#laps}

`LineSplitter`, zoals voor AC EVO: het punt waar de opname begon is de lijn; een ronde sluit waar de auto de volgende keer het dichtst bij die lijn komt in dezelfde richting, minstens 300 m later; een run sluit wanneer de auto 8 seconden stilstaat. Een ronde telt alleen als compleet als die begon boven 5 m/s, dus de eerste ronde vanuit stilstand is een gedeeltelijke. Wanneer de klok van de mod meer dan een halve seconde teruggaat (de auto is gereset), wordt de run die op dat moment open is eerst gesloten - als gedeeltelijke run geschreven wanneer die minstens 300 m besloeg, zoals aan het eind van een opname - en daarna begint de splitter opnieuw. Zie [Ronde- en etappesplitsing](lap-splitting.md).

## Het rondebestand {#the-lap-file}

Het veld `game` is `beamng`, `meta` is `{"discipline": "circuit"}`, bestanden heten `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Er wordt geen slip geschreven; de viewer leidt die af uit de oppervlaktesnelheden van de wielen (zie [Slip, drift en afgeleide kanalen](slip-and-drift.md)). De posities staan in hetzelfde assenstelsel als de BeamNG-baanexport van GameFiles schrijft, zodat een opgenomen ronde op een geëxporteerde baan ligt.
