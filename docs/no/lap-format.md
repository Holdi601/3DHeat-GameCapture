---
title: "`heat3d-lap`-filen"
nav_order: 9
lang: "no"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# `heat3d-lap`-filen {#the-heat3d-lap-file}

Hver telemetriopptaker i dette depotet skriver én fil per runde eller rallyetappe,
i samme form uansett spill. Kurseksporten i [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
leser den tilbake for å finne spillet, nivået og kjørelinjen. Alt som kan lese JSON kan lese den.

![Feltene og kanalene i en rundefil skrevet fra en syntetisk Forza-strøm](../assets/img/lap-file.svg)

## Dokumentet {#the-document}

Ett JSON-objekt. Kanaler lagres som kolonner: én matrise per kanal, alle med
samme lengde, én verdi per prøve.

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
| `game` | hvilket spill runden er fra; se listen nedenfor |
| `track` | banens, etappens eller kartets navn, når spillet sender et |
| `layout` | bare Forza: hvilket Data Out-pakkeoppsett som ble dekodet |
| `car` | alt spillet sier om bilen; fritt format |
| `lap` | rundenummeret, tiden slik spillet telte den (eller prøvenes spenn), om den ble fullført, og lengden |
| `meta` | hvordan tallene skal leses; se nedenfor |
| `units` | enheten for hver kanal som finnes, for en leser som ikke kjenner tabellen nedenfor |
| `channels` | prøvene |
| `unparsed` | bare Forza, når pakken har bytes uten feltnavn: `ranges` (deres `[start, end)`-forskyvninger i pakken) og `hex` (per prøve, disse bytene som hex), slik at filen alene inneholder hele pakken |

`game` er en av `forza-horizon`, `forza-motorsport`, `forza` (pakkeoppsett ikke
skilt ut), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`,
`assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`,
`richard-burns-rally`, `beamng`, `trackmania`.

`meta` sier hva tallene betyr der spillene er forskjellige:

- `slip`: hva sklikanalene inneholder, der spillet sender noen - `peak`
  (normalisert, så over 1 gir dekket slipp: Forza), `scaled` (en fysisk sklí
  delt på en typisk asfalttopp: Assetto Corsa-spillene), `physical` (en brøkdel
  og radianer), `index` (et 0..1 glidemål: Trackmania);
- `discipline`: `circuit`, `rally` eller `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` eller `mixed`, når det er kjent (rallyopptakerne
  henter det fra `--surface`).

## Kanaler {#channels}

En kanal spillet ikke sender, er fraværende, aldri fylt med nuller. Kanaler per
hjul har hjulet etter et punktum: `.FL`, `.FR`, `.RL`, `.RR`.

Posisjoner er spillets verden, i meter, med `y` opp. Et spill med Z-opp-verden
vris til Y-opp av opptakeren; ingen annen ting endres, så en venstrehåndet verden
(Forzas) forblir venstrehåndet.

| Kanal | Enhet | Betydning |
|---|---|---|
| `time` | s | fra rundens første prøve |
| `distance` | m | langs kjørt linje fra første prøve |
| `x`, `y`, `z` | m | posisjon; `y` er høyde |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedaler og spak |
| `steer` | -1..1 | positiv mot høyre |
| `gear` | | slik spillet teller den |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | bilens rammeverk |
| `yaw`, `pitch`, `roll` | rad | retning og holdning |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | fart i bilens ramme: høyre, fremover, opp |
| `bodySlip` | rad | driftvinkel, der spillet sender den |
| `loose` | 0/1 | på løst underlag (Trackmania) |
| `airborne` | 0/1 | ingen hjul på bakken |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | slik spillet sender dem |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | hjelpesystemer i bruk, slått på |
| `absLevel`, `tcLevel` | | innstillinger for hjelpesystemer |
| `brakeBias` | 0..1 | fremre andel |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | per hjul |
| `tirePressure` | psi | per hjul |
| `tireWear` | 0..1 | per hjul |
| `slipRatio`, `slipAngle`, `combinedSlip` | se `meta.slip` | per hjul |
| `slipIndex` | 0..1 | per hjul, glidemål (Trackmania) |
| `camber` | rad | per hjul |
| `brakeTemp` | °C | per hjul |
| `padLife`, `discLife` | | per hjul |
| `suspensionM` | m | per hjul, fjæringsutslag |
| `suspension` | 0..1 | per hjul, utslag innenfor det området denne runden brukte |
| `wheelLoad` | N | per hjul |
| `wheelSpeed` | rad/s | per hjul, rotasjon |
| `wheelSurfaceSpeed` | m/s | per hjul, kontaktflatens fart |
| `groundContact` | 0/1 | per hjul |
| `rumble`, `surfaceRumble` | | per hjul: på en rumlestripe; underlagets rumling |
| `puddle` | | per hjul, dybde av stående vann |

En opptaker kan legge til egne kanaler under andre navn; en leser beholder det den ikke kjenner.

Ingen av rallyspillene sender dekkslipp. En leser kan regne den ut fra hvert hjuls
kontaktflate eller overflatefart mot bilens fart, `(hjul - bil) / bil`, eller fra
rotasjonen og en rulleradius målt på selve runden der bare rotasjon sendes.
Driftvinkelen kommer fra bilens egen hastighet (`latVel`, `longVel`) der den
sendes, eller fra verdenshastigheten projisert på bilens akser.

## CSV-formen {#the-csv-form}

Trackmania-pluginen skriver `heat3d-lap-csv` i stedet: en første linje som starter
med `# ` og et JSON-objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`,
`meta`), en linje med kanalnavn, og deretter en linje per prøve. Kanalnavnene er
de samme som over.

## Hva hver opptaker faktisk skriver {#what-each-recorder-actually-writes}

Formatet over er kontrakten; opptakerne fyller det litt forskjellig, og en leser bør
tåle alle disse (kontrollert mot koden):

| Opptaker | `track` | `layout` | `meta` | `units` | Kanaler utover tabellen |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (Forza Motorsport 2023s banenummer er `lap.trackOrdinal`) | det oppdagede pakkeoppsettet | `slip: peak`, `discipline: circuit` | bare enheter for kanaler som finnes | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, spillets klokke `timestampMs`, `raceTime`, `bestLap`, `lastLap`; bilens lokale fart ligger under det kanoniske `latVel`, `vertVel`, `longVel`; `unparsed` ved siden av kanalene |
| Assetto Corsa-spillene (`kunos.py`) | fra den statiske siden, eller `null` | fraværende | `slip: scaled`, `discipline: circuit` eller `rally` | en fast liste | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (slik sendt), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rallyspill (`rally.py` via `lapfile.py`) | `null` | fraværende | `discipline: rally`, `slip: null`, `surface` bare når `--surface` ble gitt (ellers utleder viewer den) | bare enheter for kanaler som finnes | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` for flyttallene uten fast navn; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | fraværende | `discipline: circuit` | bare enheter for kanaler som finnes | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-plugin (CSV) | kartets navn | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` er Forza-bilblokken (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` for Kunos-spillene når den statiske siden
nevner en bil, og `{}` ellers. `lap.metres` er Forzas avstandsteller-differanse for
Forza og den summerte 3D-avstanden mellom prøvene ellers. Verdier avrundes når de
skrives: `time` til 4 desimaler, `distance` til 3, andre flyttall til 5. JSON skrives
kompakt (uten mellomrom).

Hver pakke eller side opptakeren mottok - ikke bare de som gjelder runder - beholdes
hel ved siden av rundefilene i `<stamp>_<game>.raw.parquet`, med en egenkontroll i
`<stamp>_<game>.summary.json` (avsnittet "Completeness" i README-filen).

En prøve en kanal ikke har verdi for - mangler i den rammen, eller ikke et endelig
tall slik spillet sendte det - skrives som `null` av alle opptakere (`lapfile.clean`),
og fjæringsbrøken utledet fra den er også `null`. `NaN` og `Infinity` skrives aldri: de
er ikke JSON, og en nettlesers `JSON.parse` avviser hele filen på grunn av én av dem.
En leser bør regne med `null` inne i en kanals matrise.

Forza-filene har `"game": "forza-horizon"`, `"forza-motorsport"` eller `"forza"`
etter det oppdagede oppsettet. Viewerens leser av FH Companions `.tele.gz`-filer lager runder
med `"game": "forza-horizon"` og `meta.slip = "peak"`; den leseren ligger i viewer, ikke her.
iRacing-runder (lest fra `.ibt` i viewer) har `"game": "iracing"`, som ikke står i listen
over opptakernes `game`-verdier fordi ingen opptaker skriver den.

Se [Splitting av runder og etapper](lap-splitting.md) for hvordan `lap.number`, `lap.seconds`
og `lap.complete` bestemmes, og [Slip, drift og avledede kanaler](slip-and-drift.md) for
hva viewer utleder fra disse kanalene.
