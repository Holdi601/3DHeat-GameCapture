---
title: "Forza Horizon en Forza Motorsport"
nav_order: 1
lang: "nl"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon en Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # en FH Companion blijft werken
```

Code: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py) (herkenning van de indeling), [`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py) (elk kanaal, rondenbestanden, doorsturen).

## Het aanzetten in het spel {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, poort `5300` (of wat je ook aan `--port` meegeeft). Forza Motorsport biedt ook een pakketformaat: het moet **Dash** zijn, niet Sled. Sled bevat helemaal geen positie, en de opnemer weigert het.

De opnemer bindt aan `127.0.0.1`, dus het spel moet op dezelfde pc draaien.

## Wat het spel verstuurt, en hoe de indeling wordt gevonden {#what-the-game-sends-and-how-the-layout-is-found}

Data Out is één UDP-pakket per simulatietik (ongeveer 60 per seconde), een platte little-endian C-struct in deze groottes:

| Lengte | Variant |
|---|---|
| 232 bytes | Motorsport "Sled": geen positie. Wordt geweigerd met een melding dat je naar Dash moet overschakelen. |
| 311 bytes | Motorsport "Dash": het Sled-blok plus het dash-blok van 79 bytes |
| 324 bytes | Horizon "Dash": hetzelfde, met opvulling tussen de twee blokken |
| 331 bytes | Forza Motorsport (2023): Dash plus 20 bytes slijtage van de banden en het baan-id |

Het Sled-blok (offsets 0-231) is stabiel. Waar het dash-blok in de Horizon-variant begint, wordt in gepubliceerde bronnen op verschillende manieren beschreven, en een verkeerde gok faalt niet - het levert plausibele floats uit de verkeerde velden op. Daarom wordt het begin **ontdekt**:

1. Kandidaatbegin worden in volgorde geprobeerd: `length - 79` (het dash-blok loopt in elke gedocumenteerde variant tot de laatste byte), 232, 244, en 232 tot 260 in stappen van 4.
2. Elke kandidaat wordt beoordeeld op pakketten van een rijdende auto (een snelheidscomponent boven 1 m/s): de snelheidsvector van het Sled-blok en de scalaire `Speed` van het dash-blok zijn dezelfde grootheid op twee plaatsen, dus `| |velocity| - Speed |` is alleen bij het juiste begin bijna nul.
3. De kandidaat met de kleinste slechtste afwijking wint, als die afwijking hoogstens **1 m/s** is. Anders blijft de herkenning wachten.

Terwijl de auto stilstaat, lezen alle kandidaten nul en komen ze overeen, wat niets bewijst, dus **wacht de herkenning tot de auto rijdt**: rij een paar meter voordat je uitvoer verwacht. Tot 600 pakketten worden vastgehouden terwijl er gewacht wordt (teruggebracht tot de laatste 300). Zodra de indeling bekend is, worden de vastgehouden pakketten ook gedecodeerd, zodat het begin van de eerste ronde niet verloren gaat. Pakketten met een andere lengte dan de herkende indeling, pakketten korter dan 311 bytes, en pakketten met een positie of snelheid die geen eindig getal is, worden voor de rondenbestanden genegeerd.

Welk Forza het is, volgt uit de indeling: een Horizon-indeling geeft `"game": "forza-horizon"`, een Motorsport- of 331-byte-indeling geeft `"forza-motorsport"`, al het andere `"forza"`. De naam van de herkende indeling (`Horizon dash`, `Motorsport dash`, `331-byte dash`) wordt geschreven als `layout`.

## Kanalen die worden opgenomen {#channels-recorded}

Elk veld van het pakket wordt gedecodeerd (`decode_full`) en omgezet:

- pedalen `throttle`, `brake`, `clutch`, `handbrake` van 0..255 naar 0..1;
- `steer` van -127..127 naar -1..1; `drivingLine` en `aiBrakeDifference` op dezelfde manier gedeeld door 127;
- `tireTemp.FL` ... `.RR` van Fahrenheit naar Celsius;
- `latAcc`, `longAcc`, `vertAcc` en `yawRate` zijn kopieën van `accelX`, `accelZ`, `accelY` en `angVelY` onder de kanonieke namen (autoframe: x naar rechts, y omhoog, z vooruit);
- de Sled-snelheid, die in het eigen frame van de auto staat (x naar rechts, y omhoog, z vooruit - niet die van de wereld), wordt rechtstreeks onder de kanonieke namen `latVel`, `vertVel` en `longVel` geschreven, zodat de viewer de drifthoek daaruit leest in plaats van die uit koers en pad te schatten.

De kanalen van het rondenbestand zijn al deze, behalve de velden per ronde:

| Groep | Kanalen |
|---|---|
| Tijd en plaats | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Beweging | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Bestuurder | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Per wiel (`.FL .FR .RL .RR`) | `suspension` (0 uitgerekt .. 1 ingedrukt), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (genormaliseerd: boven 1 laat de band los), `wheelSpeed` (rad/s), `rumble` (op een rumblestrip), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Alleen Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` is de rondetimer van het spel op de huidige ronde, min zijn waarde bij de eerste meting van de ronde; `distance` is de afgelegde afstand volgens het spel, min de eerste waarde. Posities zijn de wereldcoördinaten van Forza in meters, ongewijzigd (y is omhoog; de wereld is linkshandig).

Eenmaal per ronde, niet per meting, onder `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Het baan-id van FM2023 gaat ook eenmaal mee, als `lap.trackOrdinal`. Niet per meting bewaard: `isRaceOn` (1 in elk frame van een ronde). `timestampMs`, `raceTime`, `bestLap` en `lastLap` worden als kanalen bewaard.

De rest van het document wordt gevuld zoals bij elke andere opnemer:

- `"track": null` - Forza Horizon noemt de baan niet, en Forza Motorsport geeft die alleen een nummer;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - de slipkanalen zijn genormaliseerd zodat boven 1 de band loslaat;
- `units` noemt alleen de kanalen die het bestand heeft (kanalen per wiel op hun basisnaam);
- een waarde die geen eindig getal is, wordt als `null` geschreven, nooit als `NaN`.

Zie [Het `heat3d-lap`-bestand](lap-format.md).

## Hoe ronden worden gesplitst {#how-laps-are-split}

`LapSplitter` (zie [Ronde- en etappesplitsing](lap-splitting.md)): een ronde wordt afgesloten wanneer de rondenteller van het spel verspringt, en haar tijd is dan het eigen `lastLap` van het spel (wat het spel toont). Een punt-tot-puntrace of een sessie die midden in een ronde eindigt, wordt afgesloten wanneer het spel de race verlaat (`isRaceOn` valt weg), wanneer de pakketten 2 seconden stoppen, of wanneer de tijdstempel van het spel terugspringt; ze wordt bewaard als `run` als ze minstens 400 m besloeg.

## Doorsturen naar FH Companion {#relaying-to-fh-companion}

Het spel stuurt Data Out naar maar één adres. Met `--forward host:port` geeft de opnemer **elk ontvangen pakket ongewijzigd door**, nog voordat er iets wordt gedecodeerd (ook terwijl hij nog op de herkenning van de indeling wacht), zodat een andere app die de feed leest blijft werken: zet het spel op 5300, de andere app op 5301, en draai met `--forward 127.0.0.1:5301`.

FH Companion is een aparte app, geen onderdeel van 3DHeat. Het houdt een rondenbibliotheek bij onder `%LOCALAPPDATA%\FHCompanion\laps`: een map per baan, één rondenbestand per ronde, bemonsterd ongeveer elke vijf meter, en naast elk rondenbestand `<lap>.json.tele.gz`, de volledige Data Out van de ronde met de snelheid van het spel. 3DHeat leest beide:

- **De viewer leest `.tele.gz` rechtstreeks** wanneer je het (met of zonder rondenbestand) op het tabblad Race-analyse zet. Hij koppelt de veldnamen van Forza (`PositionX`, `VelocityX`, `TireSlipRatio` + wiel, ...) aan de kanonieke kanalen, zet de in de auto lokale `VelocityX/Y/Z` om in `latVel`, `vertVel`, `longVel`, zet temperaturen van de banden van Fahrenheit om, laat rijen vallen die de vorige herhalen behalve voor de klok van de opnemer, en markeert de slip als `peak`. Krijgt hij ook het rondenbestand, dan neemt de ronde auto en rondetijd daarvandaan over. Deze lezer zit in de viewer (`src/race/adapters.ts`, `readForzaTelemetry`), niet in deze repository.
- **Het commando `laps`** leest de rondenbibliotheek en schrijft de route van een baan en een CSV van elke meting; zie [Commandoverzicht](commands.md#laps).

## Overig gebruik van dezelfde feed {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` neemt alleen de posities op, elke paar seconden opgeslagen terwijl je rijdt; zie [Commandoverzicht](commands.md#route).
- De optie "Racing telemetry (Forza)" van het scanvenster gebruikt de feed als exacte cameraposities voor reconstructie; zie [Cameraposities en schaal](reconstruction-pose.md#telemetry-poses).

## Opmerkingen en voorbehouden {#notes-and-caveats}

- Waar Forza de slip op normaliseert, is niet gedocumenteerd. `1` wordt gelezen als de rand van de grip, maar de viewer meet waar de grip van elke auto echt wegvalt.
- De Sled-snelheid is in het eigen frame van de auto, zoals de Data Out-documentatie van Forza zegt en opgenomen ronden bevestigen (de voorwaartse component draagt de snelheid, de zijwaartse blijft dicht bij nul). Het herkennen van de indeling gebruikt alleen de lengte, die in elk frame gelijk is.
- Posities zijn de wereld van het spel, Y omhoog en linkshandig. De richtingen van `yaw`, `pitch` en `roll` zijn gecontroleerd op opgenomen ronden: de yaw is gelijk aan de rijrichting `atan2(dx, dz)`, een positieve pitch is neus omlaag, en een positieve roll drukt de rechterkant omlaag.
