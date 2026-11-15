---
title: "Het `heat3d-lap`-bestand"
nav_order: 9
lang: "nl"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Het `heat3d-lap`-bestand {#the-heat3d-lap-file}

Elke telemetrieopnemer in deze repository schrijft één bestand per ronde of rally-etappe, in dezelfde vorm, welk spel het ook is. De baanexport in [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) leest het terug om het spel, het level en de gereden lijn te vinden. Alles wat JSON kan lezen, kan het lezen.

![De velden en kanalen van een rondenbestand, geschreven uit een synthetische Forza-feed](../assets/img/lap-file.svg)

## Het document {#the-document}

Eén JSON-object. Kanalen worden als kolommen opgeslagen: één array per kanaal, allemaal even lang, één item per meting.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Veld | Betekenis |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | welk spel de ronde is; zie de lijst hieronder |
| `track` | de naam van de baan, de etappe of de kaart, als het spel die stuurt |
| `layout` | alleen Forza: welke Data Out-pakketindeling is gedecodeerd |
| `car` | wat het spel over de auto zegt; vrije vorm |
| `lap` | het rondenummer, de tijd zoals het spel die telde (of de spanne van de metingen), of de ronde af was, en de lengte |
| `meta` | hoe de getallen te lezen zijn; zie hieronder |
| `units` | de eenheid van elk aanwezig kanaal, voor een lezer die de tabel hieronder niet kent |
| `channels` | de metingen |
| `unparsed` | alleen Forza, als het pakket bytes heeft zonder veldnaam: `ranges` (hun `[start, end)`-byteposities in het pakket) en `hex` (per meting die bytes als hex), zodat het bestand alleen het hele pakket bevat |

`game` is een van `forza-horizon`, `forza-motorsport`, `forza` (pakketindeling niet onderscheiden), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` zegt wat de getallen betekenen waar spellen verschillen:

- `slip`: wat de slipkanalen bevatten, waar het spel er één stuurt - `peak` (genormaliseerd, dus boven 1 laat de band los: Forza), `scaled` (een fysieke slip gedeeld door een typische piek voor asfalt: de Assetto Corsa-spellen), `physical` (een fractie en radialen), `index` (een 0..1-maat voor slippen: Trackmania);
- `discipline`: `circuit`, `rally` of `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` of `mixed`, als het bekend is (de rally-opnemers nemen het uit `--surface`).

## Kanalen {#channels}

Een kanaal dat een spel niet stuurt, is afwezig, nooit opgevuld met nullen. Kanalen per wiel hebben het wiel na een punt: `.FL`, `.FR`, `.RL`, `.RR`.

Posities zijn de wereld van het spel, in meters, met `y` omhoog. Een spel waarvan de wereld Z-omhoog is, wordt door zijn opnemer naar Y-omhoog gedraaid; verder wordt niets veranderd, dus een linkshandige wereld (die van Forza) blijft linkshandig.

| Kanaal | Eenheid | Betekenis |
|---|---|---|
| `time` | s | sinds het eerste meetpunt van de ronde |
| `distance` | m | langs het gereden pad sinds het eerste meetpunt |
| `x`, `y`, `z` | m | positie; `y` is de hoogte |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedalen en hendel |
| `steer` | -1..1 | positief naar rechts |
| `gear` | | zoals het spel het telt |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | autoframe |
| `yaw`, `pitch`, `roll` | rad | koers en houding |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | snelheid in het autoframe: rechts, vooruit, omhoog |
| `bodySlip` | rad | drifthoek, waar het spel die stuurt |
| `loose` | 0/1 | op losse ondergrond (Trackmania) |
| `airborne` | 0/1 | geen wiel op de grond |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | zoals het spel ze stuurt |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | hulpsystemen in werking, ingeschakeld |
| `absLevel`, `tcLevel` | | instellingen van de hulpsystemen |
| `brakeBias` | 0..1 | aandeel voor |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | per wiel |
| `tirePressure` | psi | per wiel |
| `tireWear` | 0..1 | per wiel |
| `slipRatio`, `slipAngle`, `combinedSlip` | zie `meta.slip` | per wiel |
| `slipIndex` | 0..1 | per wiel, slipmaat (Trackmania) |
| `camber` | rad | per wiel |
| `brakeTemp` | °C | per wiel |
| `padLife`, `discLife` | | per wiel |
| `suspensionM` | m | veerweg per wiel |
| `suspension` | 0..1 | veerweg per wiel, van het bereik dat deze ronde gebruikte |
| `wheelLoad` | N | per wiel |
| `wheelSpeed` | rad/s | rotatie per wiel |
| `wheelSurfaceSpeed` | m/s | snelheid van het contactvlak per wiel |
| `groundContact` | 0/1 | per wiel |
| `rumble`, `surfaceRumble` | | per wiel: op een rumblestrip; de rumble van het wegdek |
| `puddle` | | per wiel: diepte van stilstaand water |

Een opnemer mag eigen kanalen onder andere namen toevoegen; een lezer houdt bij wat hij niet kent.

Geen van de rally-spellen stuurt bandenslip. Een lezer kan het uitrekenen uit de contactvlak- of oppervlaktesnelheid van elk wiel tegenover de snelheid van de auto, `(wiel - auto) / auto`, of uit de rotatie en een rolstraal die op de ronde zelf wordt gemeten waar alleen rotatie wordt gestuurd. De drifthoek komt uit de eigen snelheid van de auto (`latVel`, `longVel`) waar die wordt gestuurd, of uit de wereldsnelheid geprojecteerd op de assen van de auto.

## Het CSV-formaat {#the-csv-form}

De Trackmania-plugin schrijft in plaats daarvan `heat3d-lap-csv`: een eerste regel die met `# ` begint en een JSON-object (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), een regel met kanaalnamen, en dan één regel per meting. De kanaalnamen zijn dezelfde als hierboven.

## Wat elke opnemer werkelijk schrijft {#what-each-recorder-actually-writes}

De indeling hierboven is het contract; de opnemers vullen haar iets anders in, en een lezer moet dit allemaal verdragen (nagekeken tegen de code):

| Opnemer | `track` | `layout` | `meta` | `units` | Kanalen buiten de tabel |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (het baannummer van Forza Motorsport 2023 staat in `lap.trackOrdinal`) | de herkende pakketindeling | `slip: peak`, `discipline: circuit` | alleen de eenheden van aanwezige kanalen | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, de klok van het spel `timestampMs`, `raceTime`, `bestLap`, `lastLap`; de snelheid van de auto in zijn eigen frame staat onder de canonieke `latVel`, `vertVel`, `longVel`; `unparsed` naast de kanalen |
| Assetto Corsa-spellen (`kunos.py`) | uit de statische pagina, anders `null` | afwezig | `slip: scaled`, `discipline: circuit` of `rally` | een vaste lijst | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (zoals verstuurd), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rally-spellen (`rally.py` via `lapfile.py`) | `null` | afwezig | `discipline: rally`, `slip: null`, `surface` alleen als `--surface` is opgegeven (anders leidt de viewer het af) | alleen de eenheden van aanwezige kanalen | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` voor de floats zonder vaste naam; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | afwezig | `discipline: circuit` | alleen de eenheden van aanwezige kanalen | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-plugin (CSV) | de naam van de kaart | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` is het Forza-autoblok (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` voor de Kunos-spellen als de statische pagina een auto noemt, en anders `{}`. `lap.metres` is bij Forza het verschil in de afgelegde afstand van het spel en elders de opgetelde 3D-afstand tussen de metingen. Waarden worden bij het schrijven afgerond: `time` op 4 decimalen, `distance` op 3, andere floats op 5. JSON wordt compact geschreven (zonder spaties).

Elk pakket of elke pagina die de opnemer ontving - niet alleen die van de ronden - wordt heel bewaard naast de rondenbestanden in `<stamp>_<game>.raw.parquet`, met een zelfcontrole in `<stamp>_<game>.summary.json` (de sectie "Completeness" in de README).

Een meting waarvoor een kanaal geen waarde heeft - ontbrekend in dat frame, of geen eindig getal zoals het spel het stuurde - wordt door elke opnemer als `null` geschreven (`lapfile.clean`), en de veerfractie die daaruit wordt afgeleid is ook `null`. `NaN` en `Infinity` worden nooit geschreven: dat is geen JSON, en de `JSON.parse` van een browser weigert het hele bestand door er één van. Een lezer moet `null` binnen de array van een kanaal verwachten.

De Forza-bestanden hebben `"game": "forza-horizon"`, `"forza-motorsport"` of `"forza"`, naar gelang de herkende indeling. De lezer van de `.tele.gz`-bestanden van FH Companion in de viewer maakt ronden met `"game": "forza-horizon"` en `meta.slip = "peak"`; die lezer zit in de viewer, niet hier. iRacing-ronden (uit `.ibt` in de viewer) hebben `"game": "iracing"`, wat niet in de lijst van opnemerwaarden hierboven staat omdat geen opnemer het schrijft.

Zie [Ronde- en etappesplitsing](lap-splitting.md) voor hoe `lap.number`, `lap.seconds` en `lap.complete` worden bepaald, en [Slip, drifthoek en afgeleide kanalen](slip-and-drift.md) voor wat de viewer uit deze kanalen afleidt.
