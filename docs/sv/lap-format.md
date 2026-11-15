---
title: "`heat3d-lap`-filen"
nav_order: 9
lang: "sv"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# `heat3d-lap`-filen {#the-heat3d-lap-file}

Varje telemetriinspelare i det här repot skriver en fil per varv eller rallyetapp, i samma form oavsett spel. Kursexporten i [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) läser tillbaka den för att hitta spelet, nivån och den körda linjen. Allt som kan läsa JSON kan läsa den.

![Fälten och kanalerna i en varvfil skriven från ett syntetiskt Forza-flöde](../assets/img/lap-file.svg)

## Dokumentet {#the-document}

Ett JSON-objekt. Kanaler lagras som kolumner: en array per kanal, alla lika långa, en post per sampel.

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

| Fält | Betydelse |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | vilket spel varvet är från; se listan nedan |
| `track` | bana-, etapp- eller kartnamnet, när spelet skickar ett |
| `layout` | endast Forza: vilket Data Out-paketlayout som avkodades |
| `car` | allt spelet säger om bilen; fritt format |
| `lap` | varvets nummer, dess tid så som spelet räknade den (eller samplenas spann), om det avslutades, dess längd |
| `meta` | hur värdena ska läsas; se nedan |
| `units` | enheten för varje kanal som finns, för en läsare som inte känner tabellen nedan |
| `channels` | samplen |
| `unparsed` | endast Forza, när paketet har byte som inget fält förklarar: `ranges` (deras `[start, end)`-byteoffset i paketet) och `hex` (per sampel, dessa byte som hex), så att filen ensam innehåller hela paketet |

`game` är ett av `forza-horizon`, `forza-motorsport`, `forza` (paketlayouten inte särskiljd), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` säger vad värdena betyder där spelen skiljer sig åt:

- `slip`: vad slip-kanalerna innehåller, där spelet skickar någon - `peak` (normaliserad, så att däcket släpper taget när värdet är över 1: Forza), `scaled` (en fysisk slip delad med ett typiskt toppvärde för asfalt: Assetto Corsa-spelen), `physical` (en bråkdel och radianer), `index` (ett 0..1-mått för glidning: Trackmania);
- `discipline`: `circuit`, `rally` eller `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` eller `mixed`, när det är känt (rally-inspelarna tar det från `--surface`).

## Kanaler {#channels}

En kanal som ett spel inte skickar finns inte, den fylls aldrig med nollor. Kanaler per hjul har hjulet efter en punkt: `.FL`, `.FR`, `.RL`, `.RR`.

Positioner är spelets värld, i meter, med `y` uppåt. Ett spel vars värld är Z-upp vrids till Y-upp av sin inspelare; inget annat ändras, så en vänsterhänt värld (Forzas) förblir vänsterhänt.

| Kanal | Enhet | Betydelse |
|---|---|---|
| `time` | s | sedan varvets första sampel |
| `distance` | m | längs den körda vägen sedan första samplet |
| `x`, `y`, `z` | m | position; `y` är höjden |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedaler och spak |
| `steer` | -1..1 | positivt åt höger |
| `gear` | | så som spelet räknar den |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | bilens ram |
| `yaw`, `pitch`, `roll` | rad | riktning och attityd |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | hastighet i bilens ram: höger, framåt, upp |
| `bodySlip` | rad | driftvinkel, där spelet skickar den |
| `loose` | 0/1 | på lös mark (Trackmania) |
| `airborne` | 0/1 | inget hjul på marken |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | som spelet skickar dem |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | hjälpsystem aktiva, system påslagna |
| `absLevel`, `tcLevel` | | inställningar för hjälpsystemen |
| `brakeBias` | 0..1 | framaxelns andel |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | per hjul |
| `tirePressure` | psi | per hjul |
| `tireWear` | 0..1 | per hjul |
| `slipRatio`, `slipAngle`, `combinedSlip` | se `meta.slip` | per hjul |
| `slipIndex` | 0..1 | per hjul, ett glidmått (Trackmania) |
| `camber` | rad | per hjul |
| `brakeTemp` | °C | per hjul |
| `padLife`, `discLife` | | per hjul |
| `suspensionM` | m | hjulets fjäderväg |
| `suspension` | 0..1 | hjulets fjäderväg, av det omfång varvet använde |
| `wheelLoad` | N | per hjul |
| `wheelSpeed` | rad/s | hjulets rotation |
| `wheelSurfaceSpeed` | m/s | kontaktytans hastighet per hjul |
| `groundContact` | 0/1 | per hjul |
| `rumble`, `surfaceRumble` | | per hjul: på en vibrationsremsa; ytans vibrationer |
| `puddle` | | per hjul, djup av stående vatten |

En inspelare kan lägga till egna kanaler under andra namn; en läsare behåller det den inte känner igen.

Ingen av rallyspelen skickar däckslip. En läsare kan räkna ut den från varje hjuls kontaktyta eller ytfart mot bilens hastighet, `(hjul - bil) / bil`, eller från dess rotation och en rullradie uppmätt på själva varvet där bara rotation skickas. Driftvinkeln kommer från bilens egen hastighet (`latVel`, `longVel`) där den skickas, eller från världshastigheten projicerad på bilens axlar.

## CSV-formen {#the-csv-form}

Trackmania-pluginet skriver `heat3d-lap-csv` i stället: en första rad med `# ` och ett JSON-objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), en rad med kanalnamn och sedan en rad per sampel. Kanalnamnen är desamma som ovan.

## Vad varje inspelare faktiskt skriver {#what-each-recorder-actually-writes}

Formatet ovan är kontraktet; inspelarna fyller det lite olika, och en läsare bör klara av alla dessa (kontrollerat mot koden):

| Inspelare | `track` | `layout` | `meta` | `units` | Kanaler utöver tabellen |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (Forza Motorsport 2023:s bannummer är `lap.trackOrdinal`) | den upptäckta paketlayouten | `slip: peak`, `discipline: circuit` | endast enheter för kanaler som finns | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, spelets klocka `timestampMs`, `raceTime`, `bestLap`, `lastLap`; bilens lokala hastighet ligger under de kanoniska `latVel`, `vertVel`, `longVel`; `unparsed` bredvid kanalerna |
| Assetto Corsa-spelen (`kunos.py`) | från den statiska sidan, eller `null` | saknas | `slip: scaled`, `discipline: circuit` eller `rally` | en fast lista | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (som skickat), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rallyspelen (`rally.py` via `lapfile.py`) | `null` | saknas | `discipline: rally`, `slip: null`, `surface` endast när `--surface` angavs (annars härleder visaren den) | endast enheter för kanaler som finns | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` för flyttalen utan fastställt namn; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | saknas | `discipline: circuit` | endast enheter för kanaler som finns | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-pluginet (CSV) | kartans namn | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` är Forzas bilblock (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` för Kunos-spelen när den statiska sidan anger ett namn, och `{}` annars. `lap.metres` är spelets körda distans-skillnad för Forza och den summerade 3D-distansen mellan samplen annars. Värden avrundas vid skrivning: `time` till 4 decimaler, `distance` till 3, övriga flyttal till 5. JSON skrivs kompakt (utan mellanslag).

Varje paket eller sida inspelaren tog emot - inte bara varvens - sparas helt bredvid varvfilerna i `<stamp>_<game>.raw.parquet`, med en självkontroll i `<stamp>_<game>.summary.json` (avsnittet "Completeness" i README:n).

Ett sampel som en kanal saknar värde för - saknas i den bildrutan, eller inte ett ändligt tal så som spelet skickade det - skrivs som `null` av varje inspelare (`lapfile.clean`), och fjädringsandelen som härleds från det blir också `null`. `NaN` och `Infinity` skrivs aldrig: de är inte JSON, och en webbläsares `JSON.parse` vägrar hela filen för en enda av dem. En läsare ska vänta sig `null` inne i en kanals array.

Forza-filerna bär `"game": "forza-horizon"`, `"forza-motorsport"` eller `"forza"` beroende på den upptäckta layouten. Visarens läsare av FH Companions `.tele.gz`-filer ger varv med `"game": "forza-horizon"` och `meta.slip = "peak"`; den läsaren finns i visaren, inte här. iRacing-varv (lästa från `.ibt` i visaren) bär `"game": "iracing"`, vilket inte finns i listan över inspelarnas `game`-värden ovan eftersom ingen inspelare skriver det.

Se [Varv- och etappdelning](lap-splitting.md) för hur `lap.number`, `lap.seconds` och `lap.complete` avgörs, och [Slip, drift och härledda kanaler](slip-and-drift.md) för vad visaren härleder från dessa kanaler.
