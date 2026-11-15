---
title: "Assetto Corsa-spellen"
nav_order: 2
lang: "nl"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO en AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Code: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py). Tests: `tests/test_kunos.py` (synthetische pagina's). Nog niet tegen de echte spellen gedraaid.

## Waar de data vandaan komt {#where-the-data-comes-from}

De spellen van Kunos publiceren telemetrie voor apps als **benoemde gedeelde-geheugenpagina's van Windows** die het spel schrijft en die iedereen mag lezen. De opnemer opent ze alleen-lezen (`mmap` met een tagnaam), dus hij moet draaien **op de pc waarop het spel draait**, op Windows; elders stopt hij met een melding. De pagina's worden één keer geopend, bij het starten van de opnemer. Eerst het spel starten en in de auto stappen is de veilige volgorde; of de opnemer eerst starten werkt, is niet gecontroleerd.

| `--game` | Fysicapagina | Grafiekpagina (rondenteller) | Statische pagina (namen) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | niet gebruikt | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | niet gebruikt | `Local\acevo_pmf_static` |

De fysicapagina wordt 200 keer per seconde gelezen (`hz=200`); een nieuwe meting wordt alleen genomen als de `packetId` is veranderd en niet nul is. De eerste 800 bytes van de fysicapagina hebben in alle vier de spellen dezelfde indeling; van de eerste pagina van het spel is alleen 580 bytes gegarandeerd, dus als een mapping van 800 bytes niet kan worden geopend, valt de opnemer terug op 580 en ontbreken de velden daarna.

## Positie {#position}

Geen van de pagina's bevat een positie van de auto als zodanig, maar de fysicapagina bevat **het contactpunt van elke band in wereldcoördinaten** (offset 420, vier XYZ-drietallen). De positie van de auto is het gemiddelde van de vier. Een pagina waarop alle contactpunten nul zijn (menu, garage) levert geen meting op.

## Kanalen {#channels}

| Kanaal | Van | Opmerkingen |
|---|---|---|
| `time` | de eigen klok van de opnemer | seconden sinds het begin van de opname, verschoven naar de eerste meting van de ronde |
| `x`, `y`, `z` | gemiddeld contactpunt van de band | wereldmeters |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | de eenheden van het spel, per ronde geschaald naar -1..1 op de grootste absolute waarde die de ronde gebruikte, **alleen als** die waarde groter is dan 1,05 (een invoer die al in -1..1 ligt, blijft ongemoeid) |
| `gear` | `gear - 1` | het spel telt 0 achteruit, 1 neutraal, 2 eerste; geschreven als -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, maal 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | snelheid in het eigen frame vanaf offset 568 | autoframe; alleen als ongelijk aan nul. Naar welke kant de x-as wijst, is in beide richtingen gedocumenteerd, dus lees de grootte van de drifthoek, niet het teken |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | alleen de pagina van 800 bytes |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offsets 204 en 252, geschreven als 1 als boven 0; AC: `tcInAction`/`absInAction` uit de pagina van 800 bytes als die er is | hulpsystemen in werking |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | afgeleid | 0..1 van de veerweg die deze ronde gebruikte (minimum tot maximum van `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offsets 640, 656 (pagina van 800 bytes) | gedeeld door een typische piek - zie hieronder |
| `slipRatioRaw.*`, `slipAngleRaw.*` | hetzelfde | de fysieke waarden, ongeschaald |
| `padLife.*`, `discLife.*` | offsets 740, 756 | alleen de pagina van 800 bytes |

AC Rally stuurt zijn band- en remtemperaturen in kelvin: voor `--game acrally` wordt van elk van die waarden boven 200 273,15 afgetrokken.

`wheelSlip` (offset 56) wordt gedecodeerd maar niet geschreven.

## Slip schalen {#slip-scaling}

Forza stuurt slip genormaliseerd zodat 1 de rand van de grip is. Kunos stuurt de fysieke slip-ratio en slip-hoek. Dus deelt de opnemer ze door een typische piek voor asfalt - **0,12** voor de slip-ratio en **0,14 rad (ongeveer 8 graden)** voor de slip-hoek - zodat de lezing van de viewer "boven 1 betekent slippen" ongeveer klopt, bewaart de ruwe waarden ernaast, en schrijft `"meta": {"slip": "scaled"}`. Waar de grip echt eindigt, meet de viewer per auto uit de ronden. Zie [Slip, drifthoek en afgeleide kanalen](slip-and-drift.md).

## Ronden {#laps}

- **AC en ACC** tellen ronden op de grafiekpagina (`completedLaps` op offset 132, de tijd van de laatste ronde in milliseconden op 144). `CounterSplitter` sluit een ronde af wanneer de teller verandert; ze is alleen voltooid, met de rondetijd van het spel, als de teller precies één omhoog ging.
- **AC EVO en AC Rally** worden niet op ronden gelezen (de grafiekpagina van EVO is een andere, grotere indeling; AC Rally rijdt etappes). `LineSplitter` gebruikt het punt waar de opname begon als de lijn: een ronde sluit wanneer de auto de lijn het dichtst passeert in dezelfde richting, en een etappe of een willekeurige run sluit wanneer de auto 8 seconden stilstaat.

Details en drempelwaarden: [Ronde- en etappesplitsing](lap-splitting.md).

## Namen van baan en auto {#track-and-car-names}

Eenmaal gelezen, uit de statische pagina, zodra de eerste meting binnenkomt: voor AC, ACC en AC Rally de auto (UTF-16, offset 68) en de baan (offset 134); voor AC EVO de baan en haar configuratie (enkelbytetekst op de offsets 136 en 169, met een spatie samengevoegd) en geen auto. Ze gaan in het bestand als `track` en `car: {"name": ...}`.

## Het rondenbestand {#the-lap-file}

`game` is `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` of `assetto-corsa-rally`; `meta` is `{"slip": "scaled", "discipline": "rally"}` voor AC Rally en `{"slip": "scaled", "discipline": "circuit"}` voor de andere drie. Er wordt geen `surface` geschreven.

## Bronnen {#sources}

Het AC1-SDK voor gedeeld geheugen; de documentatie van het gedeelde geheugen van ACC (v1.8); de indeling van AC EVO zoals gemeten in `albertowd/live-telemetry-evo`; die van AC Rally zoals gelezen door `LuizZak/AssettoCorsaRallyTelemetryReader`. Zie [Spellen](games.md).
