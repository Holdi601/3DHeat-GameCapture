---
title: iRacing
nav_order: 6
lang: "nl"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing heeft **geen recorder** nodig. De simulator schrijft zelf telemetriebestanden, `.ibt`, wanneer telemetrielogging aan staat (Alt+L in de auto): de hele sessie op 60 Hz, elk kanaal dat de simulator blootstelt, met de YAML-beschrijving van de sessie ernaast. Zet het `.ibt`-bestand op het tabblad Race-analyse van de viewer.

De lezer zit in de viewer, niet in deze repository (`src/race/ibt.ts` in de 3DHeat-viewer). Hij wordt getest op een synthetisch bestand; hij staat hier beschreven omdat hij het iRacing-deel is van hetzelfde verhaal over rondeopnamen.

## Wat het bestand bevat, en hoe het wordt gelezen {#what-the-file-holds-and-how-it-is-read}

Het bestand is de gedocumenteerde geheugenindeling van de simulator, naar schijf geschreven:

| Deel | Grootte | Bevat |
|---|---|---|
| Header | 112 bytes | versie, ticksnelheid, waar de YAML en de variabelentabel staan, de lengte van één samplerij, waar de rijen beginnen |
| Disk-subheader | 32 bytes | startdatum en -tijd, aantal ronden, aantal rijen |
| Variabelentabel | 144 bytes per kanaal | type, offset in de rij, aantal, naam, beschrijving, eenheid |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rijen | één per tick | |

Een bestand wordt geweigerd wanneer het korter is dan 144 bytes, wanneer de header niet klopt (geen variabelen, een variabelentabel buiten het bestand, een rijlengte van nul), wanneer een van `SessionTime`, `Lap`, `Lat`, `Lon` ontbreekt, of wanneer geen enkel sample een positiefix heeft.

## Positie {#position}

iRacing geeft breedtegraad, lengtegraad en hoogte, geen positie in het eigen assenstelsel van de baan. Posities worden in meters uitgezet op een vlak dat raakt aan het eerste sample met een fix (aardstraal 6.371.008,8 m): `x` oost, `z` zuid, `y` de hoogte - zodat van bovenaf, met de standaardrichting van de viewercamera, het noorden boven in het scherm ligt.

## Ronden {#laps}

De sessie wordt gesplitst op de teller `Lap` van de simulator. Een ronde wordt alleen bewaard als die meer dan 60 samples heeft, begint onder 5% van de rondelengte (`LapDistPct`) en eindigt boven 95% - dat wil zeggen ronden die van lijn tot lijn zijn gereden. Als geen enkele ronde voldoet, wordt het bestand geweigerd met een melding die de baanlengte uit de YAML noemt. `distance` is `LapDist` teruggerekend naar het begin van de ronde, of de gereden afstand uit de posities wanneer `LapDist` ontbreekt; `time` is `SessionTime` vanaf het begin van de ronde.

## Kanalen {#channels}

| iRacing | Kanaal | Omzetting |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | geen |
| `Clutch` | `clutch` | `1 - waarde` (iRacing telt de koppeling als ingeschakeld; het kanaal is het pedaal) |
| `SteeringWheelAngle` | `steer` | `-hoek / SteeringWheelAngleMax` (radialen, linksom positief, naar -1..1 met rechts positief; pi wanneer het maximum ontbreekt) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | geen |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | geen |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | hulpinstellingen |
| `dcBrakeBias` | `brakeBias` | gedeeld door 100 wanneer het boven 1,5 ligt (bij sommige auto's een percentage) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatuur van de karkas over het midden |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa maal 0,145038, naar psi |
| `..wearM` | `tireWear.*` | `1 - waarde` |

Elk ander kanaal met één waarde per sample (en niet één byte) wordt onder zijn eigen naam doorgegeven, met een wielvoorvoegsel (`LF`, `RF`, `LR`, `RR`) omgezet naar een achtervoegsel (`.FL`, `.FR`, `.RL`, `.RR`), zodat de grafieken van de viewer het aanbieden zonder dat iemand het beschrijft.

De auto komt uit `DriverInfo`: het item waarvan `CarIdx` overeenkomt met `DriverCarIdx` levert `CarScreenName`, `CarID` en `CarClassShortName`. De baan is `TrackDisplayName` (of `TrackName`).

## Wat iRacing niet geeft {#what-iracing-does-not-give}

Er wordt geen bandenslip gelogd, dus er zijn geen slipkanalen. De drifthoek wordt afgeleid uit de yaw-snelheid ten opzichte van het pad (zie [Slip, drift en afgeleide kanalen](slip-and-drift.md)). Baanmodellen worden in een beschermd formaat geleverd en zijn geen doel voor het uitpakken van bestanden (zie [Games](games.md)).
