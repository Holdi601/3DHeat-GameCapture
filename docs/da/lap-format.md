---
title: "Filen `heat3d-lap`"
nav_order: 9
lang: "da"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Filen `heat3d-lap` {#the-heat3d-lap-file}

Hver telemetrioptager i dette repository skriver én fil pr. omgang eller rallyetape, i den samme form uanset spil. Eksporten af baner i [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) læser den igen for at finde spillet, banen og den kørte linje. Alt, der kan læse JSON, kan læse den.

![Felterne og kanalerne i en lap-fil skrevet ud fra et syntetisk Forza-signal](../assets/img/lap-file.svg)

## Dokumentet {#the-document}

Ét JSON-objekt. Kanaler gemmes som kolonner: ét array pr. kanal, alle af samme længde, med ét element pr. prøve.

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

| Felt | Betydning |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | hvilket spil omgangen er fra; se listen nedenfor |
| `track` | banens, etapens eller kortets navn, når spillet sender et |
| `layout` | kun Forza: hvilket Data Out-pakkelayout, der blev afkodet |
| `car` | alt, spillet siger om bilen; frit format |
| `lap` | omgangens nummer, dens tid, som spillet talte den (eller prøvernes spænd), om den blev afsluttet, og dens længde |
| `meta` | hvordan tallene skal læses; se nedenfor |
| `units` | enheden for hver kanal, der findes, til en læser, der ikke kender tabellen nedenfor |
| `channels` | prøverne |
| `unparsed` | kun Forza, når pakken har bytes, som intet felt navngiver: `ranges` (deres `[start, end)`-byteforskydninger i pakken) og `hex` (pr. prøve, disse bytes som hex), så filen alene rummer hele pakken |

`game` er en af `forza-horizon`, `forza-motorsport`, `forza` (pakkelayout ikke skelnet), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` siger, hvad tallene betyder, hvor spillene er forskellige:

- `slip`: hvad slip-kanalerne indeholder, hvor spillet sender nogen - `peak` (normaliseret, så over 1 slipper dækket: Forza), `scaled` (et fysisk slip divideret med en typisk asfalttop: AC-spillene), `physical` (en brøk og radianer), `index` (et glidemål fra 0..1: Trackmania);
- `discipline`: `circuit`, `rally` eller `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` eller `mixed`, når det er kendt (rallyoptagerne tager det fra `--surface`).

## Kanaler {#channels}

En kanal, et spil ikke sender, er fraværende, aldrig udfyldt med nuller. Kanaler pr. hjul har hjulet efter et punktum: `.FL`, `.FR`, `.RL`, `.RR`.

Positioner er spillets verden i meter, med `y` op. En verden, der er Z-op, drejes til Y-op af optageren; intet andet ændres, så en venstrehåndet verden (Forzas) forbliver venstrehåndet.

| Kanal | Enhed | Betydning |
|---|---|---|
| `time` | s | siden den første prøve i omgangen |
| `distance` | m | langs den kørte sti siden den første prøve |
| `x`, `y`, `z` | m | position; `y` er højden |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedaler og håndbremse |
| `steer` | -1..1 | positiv mod højre |
| `gear` | | som spillet tæller den |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | bilens ramme |
| `yaw`, `pitch`, `roll` | rad | retning og attityde |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | hastighed i bilens ramme: højre, fremad, op |
| `bodySlip` | rad | driftvinkel, hvor spillet sender den |
| `loose` | 0/1 | på løst underlag (Trackmania) |
| `airborne` | 0/1 | intet hjul på jorden |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | som spillet sender dem |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | hjælpesystemer i brug, systemer tændt |
| `absLevel`, `tcLevel` | | indstilling af hjælpesystemerne |
| `brakeBias` | 0..1 | forreste andel |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | pr. hjul |
| `tirePressure` | psi | pr. hjul |
| `tireWear` | 0..1 | pr. hjul |
| `slipRatio`, `slipAngle`, `combinedSlip` | se `meta.slip` | pr. hjul |
| `slipIndex` | 0..1 | pr. hjul, glidemål (Trackmania) |
| `camber` | rad | pr. hjul |
| `brakeTemp` | °C | pr. hjul |
| `padLife`, `discLife` | | pr. hjul |
| `suspensionM` | m | pr. hjul, fjedervej |
| `suspension` | 0..1 | pr. hjul, fjedervej inden for det interval, omgangen brugte |
| `wheelLoad` | N | pr. hjul |
| `wheelSpeed` | rad/s | pr. hjul, rotation |
| `wheelSurfaceSpeed` | m/s | pr. hjul, kontaktfladens hastighed |
| `groundContact` | 0/1 | pr. hjul |
| `rumble`, `surfaceRumble` | | pr. hjul: på en rumlestrimmel; underlagets rumling |
| `puddle` | | pr. hjul, dybde af stående vand |

En optager må tilføje egne kanaler under andre navne; en læser beholder dem, den ikke kender.

Ingen af rallyspillene sender dæk-slip. En læser kan udregne det ud fra hvert hjuls kontaktflade- eller overfladehastighed mod bilens hastighed, `(hjul - bil) / bil`, eller ud fra dets rotation og en rulleradius målt på selve omgangen, hvor kun rotation sendes. Driftvinklen kommer fra bilens egen hastighed (`latVel`, `longVel`), hvor den sendes, eller fra verdenshastigheden projiceret på bilens akser.

## CSV-formen {#the-csv-form}

Trackmania-pluginet skriver i stedet `heat3d-lap-csv`: en første linje med `# ` og et JSON-objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), en linje med kanalnavne og derefter én linje pr. prøve. Kanalnavnene er de samme som ovenfor.

## Hvad hver optager faktisk skriver {#what-each-recorder-actually-writes}

Formatet ovenfor er kontrakten. Optagerne udfylder det lidt forskelligt, og en læser bør tåle alle disse (kontrolleret mod koden):

| Optager | `track` | `layout` | `meta` | `units` | Kanaler ud over tabellen |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (Forza Motorsport 2023's banenummer er `lap.trackOrdinal`) | det fundne pakkelayout | `slip: peak`, `discipline: circuit` | kun enheder for kanaler, der findes | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, spillets ur `timestampMs`, `raceTime`, `bestLap`, `lastLap`; bilens lokale hastighed ligger under de kanoniske `latVel`, `vertVel`, `longVel`; `unparsed` ved siden af kanalerne |
| Assetto Corsa-spillene (`kunos.py`) | fra den statiske side, eller `null` | fraværende | `slip: scaled`, `discipline: circuit` eller `rally` | en fast liste | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (som sendt), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rallyspil (`rally.py` via `lapfile.py`) | `null` | fraværende | `discipline: rally`, `slip: null`, `surface` kun når `--surface` blev givet (ellers udleder viewer'en det) | kun enheder for kanaler, der findes | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` for de flydere uden et fastlagt navn; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | fraværende | `discipline: circuit` | kun enheder for kanaler, der findes | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-pluginet (CSV) | banens navn | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` er Forzas bilblok (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` for Kunos-spillene, når den statiske side navngiver en bil, og ellers `{}`. `lap.metres` er spillets afstandsforskel for Forza og den samlede 3D-afstand mellem prøverne ellers. Værdier afrundes ved skrivning: `time` til 4 decimaler, `distance` til 3, andre decimaltal til 5. JSON skrives kompakt (uden mellemrum).

Hver pakke eller side, optageren modtog - ikke kun omgangenes - gemmes uændret ved siden af omgangsfilerne i `<stamp>_<game>.raw.parquet`, med en selvkontrol i `<stamp>_<game>.summary.json` (afsnittet "Completeness" i README'en).

En prøve, en kanal ingen værdi har for - manglende i det billede, eller ikke et endeligt tal, som spillet sendte det - skrives som `null` af alle optagere (`lapfile.clean`), og affjedringsbrøken udledt af den bliver også `null`. `NaN` og `Infinity` skrives aldrig: de er ikke JSON, og en browsers `JSON.parse` afviser hele filen på grund af én af dem. En læser bør forvente `null` inde i en kanals array.

Forza-filerne har `"game": "forza-horizon"`, `"forza-motorsport"` eller `"forza"` efter det fundne layout. Viewer'ens læser af FH Companions `.tele.gz`-filer giver omgange med `"game": "forza-horizon"` og `meta.slip = "peak"`; den læser ligger i viewer'en, ikke her. iRacing-omgange (læst fra `.ibt` i viewer'en) har `"game": "iracing"`, som ikke står på listen over optagerens `game`-værdier ovenfor, fordi ingen optager skriver den.

Se [Opdeling i omgange og etaper](lap-splitting.md) for, hvordan `lap.number`, `lap.seconds` og `lap.complete` afgøres, og [Slip, drift og afledte kanaler](slip-and-drift.md) for, hvad viewer'en udleder af disse kanaler.
