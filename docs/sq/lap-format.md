---
title: "Skedari heat3d-lap"
nav_order: 9
lang: "sq"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Skedari `heat3d-lap` {#the-heat3d-lap-file}

Çdo regjistrues telemetrie në këtë repo shkruan një skedar për çdo xhiro ose etapë
rali, në të njëjtën formë pavarësisht lojës. Eksporti i pistës në [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
e lexon prapë për të gjetur lojën, nivelin dhe vijën e vozitur. Çdo gjë që lexon
JSON mund ta lexojë.

![Fushat dhe kanalet e një skedari xhiroje të shkruar nga një burim sintetik Forza](../assets/img/lap-file.svg)

## Dokumenti {#the-document}

Një objekt JSON. Kanalet ruhen si kolona: një varg për çdo kanal, të gjitha me
të njëjtën gjatësi, një hyrje për çdo kampion.

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

| Fusha | Kuptimi |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | nga cila lojë është xhiroja; shih listën më poshtë |
| `track` | emri i pistës, etapës ose hartës, kur loja e dërgon |
| `layout` | vetëm Forza: cila strukturë paketash Data Out u dekodua |
| `car` | çfarë thotë loja për makinën; formë e lirë |
| `lap` | numri i xhiros, koha e saj siç e numëroi loja (ose hapësira e kampioneve), nëse u përfundua, gjatësia e saj |
| `meta` | si të lexohen numrat; shih më poshtë |
| `units` | njësia e çdo kanali të pranishëm, për një lexues që nuk e njeh tabelën më poshtë |
| `channels` | kampionet |
| `unparsed` | vetëm Forza, kur paketa ka bajte që asnjë fushë nuk i emërton: `ranges` (zhvendosjet e tyre `[start, end)` në bajte në paketë) dhe `hex` (për çdo kampion, ato bajte si hex), kështu që vetëm skedari mban të gjithë paketën |

`game` është një nga `forza-horizon`, `forza-motorsport`, `forza` (struktura e
paketës nuk u dallua), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` tregon çfarë nënkuptojnë numrat aty ku lojërat ndryshojnë:

- `slip`: çfarë mbajnë kanalet e rrëshqitjes, aty ku loja dërgon ndonjë - `peak`
  (e normalizuar, kështu që pas 1 goma lëshon: Forza), `scaled` (një rrëshqitje
  fizike e pjesëtuar me një maksimum tipik në asfalt: lojërat Assetto Corsa),
  `physical` (një thyesë dhe radianë), `index` (një masë rrëshqitjeje 0..1:
  Trackmania);
- `discipline`: `circuit`, `rally` ose `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` ose `mixed`, kur dihet (regjistruesit
  e ralit e marrin nga `--surface`).

## Kanalet {#channels}

Një kanal që një lojë nuk e dërgon mungon, nuk plotësohet kurrë me zero. Kanalet
për çdo rrotë e mbajnë rrotën pas një pike: `.FL`, `.FR`, `.RL`, `.RR`.

Pozicionet janë bota e lojës, në metra, me `y` lart. Një lojë bota e së cilës ka
Z lart kthehet në Y lart nga regjistruesi i saj; asgjë tjetër nuk ndryshohet,
kështu që një botë e majtë (ajo e Forza) mbetet e majtë.

| Kanali | Njësia | Kuptimi |
|---|---|---|
| `time` | s | që nga kampioni i parë i xhiros |
| `distance` | m | përgjatë rrugës së vozitur që nga kampioni i parë |
| `x`, `y`, `z` | m | pozicioni; `y` është lartësia |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedalet dhe leva |
| `steer` | -1..1 | pozitive djathtas |
| `gear` | | siç e numëron loja |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | korniza e makinës |
| `yaw`, `pitch`, `roll` | rad | drejtimi dhe qëndrimi |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | shpejtësia në kornizën e makinës: djathtas, përpara, lart |
| `bodySlip` | rad | këndi i drift-it, aty ku loja e dërgon |
| `loose` | 0/1 | në tokë të lirshme (Trackmania) |
| `airborne` | 0/1 | asnjë rrotë në tokë |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | siç i dërgon loja |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | ndihma në veprim, sisteme të ndezura |
| `absLevel`, `tcLevel` | | cilësimet e ndihmave |
| `brakeBias` | 0..1 | pjesa e përparme |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | për çdo rrotë |
| `tirePressure` | psi | për çdo rrotë |
| `tireWear` | 0..1 | për çdo rrotë |
| `slipRatio`, `slipAngle`, `combinedSlip` | shih `meta.slip` | për çdo rrotë |
| `slipIndex` | 0..1 | masa e rrëshqitjes për çdo rrotë (Trackmania) |
| `camber` | rad | për çdo rrotë |
| `brakeTemp` | °C | për çdo rrotë |
| `padLife`, `discLife` | | për çdo rrotë |
| `suspensionM` | m | udhëtimi i çdo rrote |
| `suspension` | 0..1 | udhëtimi i çdo rrote, brenda intervalit që përdori kjo xhiro |
| `wheelLoad` | N | për çdo rrotë |
| `wheelSpeed` | rad/s | rrotullimi i çdo rrote |
| `wheelSurfaceSpeed` | m/s | shpejtësia e njollës së kontaktit të çdo rrote |
| `groundContact` | 0/1 | për çdo rrotë |
| `rumble`, `surfaceRumble` | | për çdo rrotë: mbi një breg dridhës; dridhja e sipërfaqes |
| `puddle` | | thellësia e ujit të ndenjur për çdo rrotë |

Një regjistrues mund të shtojë kanale të veta me emra të tjerë; një lexues e mban
atë që nuk e njeh.

Asnjë nga lojërat e ralit nuk dërgon rrëshqitjen e gomave. Një lexues mund ta
llogarisë nga shpejtësia e njollës së kontaktit ose e sipërfaqes së çdo rrote
krahasuar me shpejtësinë e makinës, `(wheel - car) / car`, ose nga rrotullimi i saj
dhe një rreze rrotullimi e matur në vetë xhironë aty ku dërgohet vetëm rrotullimi.
Këndi i drift-it vjen nga shpejtësia e vetë makinës (`latVel`, `longVel`) aty ku
dërgohet, ose nga shpejtësia botërore e projektuar mbi akset e makinës.

## Forma CSV {#the-csv-form}

Shtesa e Trackmania shkruan `heat3d-lap-csv` në vend të tij: një rresht i parë me
`# ` dhe një objekt JSON (`format`, `version`, `game`, `track`, `complete`,
`seconds`, `meta`), një rresht me emrat e kanaleve, pastaj një rresht për çdo
kampion. Emrat e kanaleve janë të njëjtë si më sipër.

## Çfarë shkruan realisht çdo regjistrues {#what-each-recorder-actually-writes}

Formati më sipër është kontrata; regjistruesit e plotësojnë paksa ndryshe, dhe një
lexues duhet t'i durojë të gjitha këto (kontrolluar me kodin):

| Regjistruesi | `track` | `layout` | `meta` | `units` | Kanale përtej tabelës |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (numri i pistës i Forza Motorsport 2023 është `lap.trackOrdinal`) | struktura e paketës e zbuluar | `slip: peak`, `discipline: circuit` | vetëm njësitë e kanaleve të pranishme | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, ora e lojës `timestampMs`, `raceTime`, `bestLap`, `lastLap`; shpejtësia lokale e makinës është nën `latVel`, `vertVel`, `longVel` standarde; `unparsed` pranë kanaleve |
| Lojërat Assetto Corsa (`kunos.py`) | nga faqja statike, ose `null` | mungon | `slip: scaled`, `discipline: circuit` ose `rally` | një listë e fiksuar | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (siç dërgohet), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Lojërat e ralit (`rally.py` nëpërmjet `lapfile.py`) | `null` | mungon | `discipline: rally`, `slip: null`, `surface` vetëm kur është dhënë `--surface` (përndryshe shikuesi e nxjerr vetë) | vetëm njësitë e kanaleve të pranishme | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` për float-et pa emër të vendosur; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` nëpërmjet `lapfile.py`) | `null` | mungon | `discipline: circuit` | vetëm njësitë e kanaleve të pranishme | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Shtesa Trackmania (CSV) | emri i hartës | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` është blloku i makinës së Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` për lojërat Kunos kur faqja statike emërton një, dhe
`{}` përndryshe. `lap.metres` është diferenca e distancës së përshkuar të lojës për Forza dhe
largësia 3D e mbledhur mes kampioneve gjetkë. Vlerat rrumbullakohen gjatë shkrimit: `time` në 4
shifra pas presjes, `distance` në 3, float-et e tjerë në 5. JSON shkruhet kompakt (pa hapësira).

Çdo paketë ose faqe që e mori regjistruesi - jo vetëm ato të xhirove - ruhet e plotë pranë skedarëve të
xhirove te `<stamp>_<game>.raw.parquet`, me një vetëkontroll te `<stamp>_<game>.summary.json` (seksioni
"Completeness" i README).

Një kampion për të cilin një kanal nuk ka vlerë - që mungon nga ai kuadër, ose nuk është numër i
fundëm siç e dërgoi loja - shkruhet si `null` nga çdo regjistrues (`lapfile.clean`), dhe pjesa e
pezullimit e nxjerrë prej tij është gjithashtu `null`. `NaN` dhe `Infinity` nuk shkruhen kurrë: nuk
janë JSON, dhe `JSON.parse` i një shfletuesi e refuzon gjithë skedarin për një prej tyre. Një lexues
duhet të presë `null` brenda vargut të një kanali.

Skedarët Forza mbajnë `"game": "forza-horizon"`, `"forza-motorsport"` ose `"forza"` sipas
strukturës së zbuluar. Lexuesi i shikuesit për skedarët `.tele.gz` të FH Companion prodhon xhiro
me `"game": "forza-horizon"` dhe `meta.slip = "peak"`; ai lexues është në shikues, jo këtu.
Xhirot e iRacing (të lexuara nga `.ibt` në shikues) mbajnë `"game": "iracing"`, që nuk është në
listën e vlerave `game` të regjistruesve më sipër sepse asnjë regjistrues nuk e shkruan.

Shih [Ndarja e xhirove dhe e etapave](lap-splitting.md) për mënyrën si vendosen `lap.number`,
`lap.seconds` dhe `lap.complete`, dhe [Rrëshqitja, drift-i dhe kanalet e nxjerra](slip-and-drift.md) për
atë që shikuesi nxjerr nga këto kanale.
