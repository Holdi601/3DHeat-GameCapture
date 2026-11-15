---
title: "heat3d-lap skráin"
nav_order: 9
lang: "is"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# `heat3d-lap` skráin {#the-heat3d-lap-file}

Hvert mælingagagna-upptökutæki í þessari geymslu skrifar eina skrá fyrir hvern hring eða
rallíleið, á sama sniði hvaða leikur sem er. Brautarútflutningurinn í [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
les hana til baka til að finna leikinn, borðið og ekna línu. Allt sem
les JSON getur lesið hana.

![Reitir og rásir í hringskrá sem skrifuð er úr gervi-Forza straumi](../assets/img/lap-file.svg)

## Skjalið {#the-document}

Eitt JSON hlutur. Rásir eru geymdar sem dálkar: ein fylking á hverja rás, allar
jafn langar, eitt gildi á hvert sýni.

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

| Reitur | Merking |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | úr hvaða leik hringurinn er; sjá listann hér að neðan |
| `track` | heiti brautar, leiðar eða korts, þegar leikurinn sendir það |
| `layout` | aðeins Forza: hvaða Data Out pakkauppsetning var afkóðuð |
| `car` | það sem leikurinn segir um bílinn; frjálst form |
| `lap` | númer hringsins, tími hans eins og leikurinn taldi hann (eða spönn sýnanna), hvort hann var kláraður, lengd hans |
| `meta` | hvernig á að lesa tölurnar; sjá hér að neðan |
| `units` | eining hverrar rásar sem er til staðar, fyrir lesara sem þekkir ekki töfluna hér að neðan |
| `channels` | sýnin |
| `unparsed` | aðeins Forza, þegar pakkinn hefur bæti sem enginn reitur nefnir: `ranges` (`[start, end)` bætafærslur þeirra í pakkanum) og `hex` (fyrir hvert sýni, þessi bæti sem hex), svo skráin ein geymir allan pakkann |

`game` er eitt af `forza-horizon`, `forza-motorsport`, `forza` (pakkauppsetning
ekki greind), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` segir hvað tölurnar þýða þar sem leikir eru ólíkir:

- `slip`: hvað skriðrásirnar geyma, þar sem leikur sendir einhverjar - `peak`
  (stöðlað, svo yfir 1 sleppir dekkið gripinu: Forza), `scaled` (eðlisfræðilegt skrið
  deilt með dæmigerðu hámarki á malbiki: Assetto Corsa leikirnir), `physical` (brot
  og radíanar), `index` (0..1 mælikvarði á rennsli: Trackmania);
- `discipline`: `circuit`, `rally` eða `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` eða `mixed`, þegar það er vitað (ralllí-
  upptökutækin taka það úr `--surface`).

## Rásir {#channels}

Rás sem leikur sendir ekki vantar, hún er aldrei fyllt með núllum. Rásir fyrir hvert hjól
bera hjólið á eftir punkti: `.FL`, `.FR`, `.RL`, `.RR`.

Staðsetningar eru heimur leiksins, í metrum, með `y` upp. Leikur þar sem heimurinn
er Z-upp er snúinn í Y-upp af upptökutækinu; engu öðru er breytt, svo
örvhentur heimur (Forza) helst örvhentur.

| Rás | Eining | Merking |
|---|---|---|
| `time` | s | frá fyrsta sýni hringsins |
| `distance` | m | eftir eknum ferli frá fyrsta sýni |
| `x`, `y`, `z` | m | staðsetning; `y` er hæð |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedalar og stöng |
| `steer` | -1..1 | jákvætt til hægri |
| `gear` | | eins og leikurinn telur |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | rammi bílsins |
| `yaw`, `pitch`, `roll` | rad | stefna og afstaða |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | hraði í ramma bílsins: til hægri, áfram, upp |
| `bodySlip` | rad | rekhorn, þar sem leikurinn sendir það |
| `loose` | 0/1 | á lausu undirlagi (Trackmania) |
| `airborne` | 0/1 | ekkert hjól á jörðinni |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | eins og leikurinn sendir þau |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | hjálpartæki virk, kerfi á |
| `absLevel`, `tcLevel` | | stillingar hjálpartækja |
| `brakeBias` | 0..1 | hlutur að framan |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | á hvert hjól |
| `tirePressure` | psi | á hvert hjól |
| `tireWear` | 0..1 | á hvert hjól |
| `slipRatio`, `slipAngle`, `combinedSlip` | sjá `meta.slip` | á hvert hjól |
| `slipIndex` | 0..1 | rennslismælikvarði á hvert hjól (Trackmania) |
| `camber` | rad | á hvert hjól |
| `brakeTemp` | °C | á hvert hjól |
| `padLife`, `discLife` | | á hvert hjól |
| `suspensionM` | m | slag á hvert hjól |
| `suspension` | 0..1 | slag á hvert hjól, af því bili sem þessi hringur notaði |
| `wheelLoad` | N | á hvert hjól |
| `wheelSpeed` | rad/s | snúningur á hvert hjól |
| `wheelSurfaceSpeed` | m/s | hraði snertiflatar á hvert hjól |
| `groundContact` | 0/1 | á hvert hjól |
| `rumble`, `surfaceRumble` | | á hvert hjól: á skröltrönd; skrölt undirlagsins |
| `puddle` | | dýpt vatns á hvert hjól |

Upptökutæki má bæta við eigin rásum undir öðrum heitum; lesari heldur því sem
hann þekkir ekki.

Engin ralllíleikjanna sendir dekkjaskrið. Lesari getur reiknað það út frá
hraða snertiflatar eða yfirborðshraða hvers hjóls miðað við hraða bílsins,
`(wheel - car) / car`, eða út frá snúningi þess og veltiradíus mældum á
hringnum sjálfum þar sem aðeins snúningur er sendur. Rekhornið kemur úr eigin
hraða bílsins (`latVel`, `longVel`) þar sem hann er sendur, eða úr heimshraðanum
varpað á ása bílsins.

## CSV-formið {#the-csv-form}

Trackmania viðbótin skrifar `heat3d-lap-csv` í staðinn: fyrsta lína með `# `
og JSON hlut (`format`, `version`, `game`, `track`, `complete`, `seconds`,
`meta`), lína með rásaheitum, svo ein lína á hvert sýni. Rásaheitin eru
þau sömu og hér að ofan.

## Hvað hvert upptökutæki skrifar í raun {#what-each-recorder-actually-writes}

Sniðið hér að ofan er samningurinn; upptökutækin fylla það örlítið mismunandi, og lesari
á að þola allt þetta (athugað gegn kóðanum):

| Upptökutæki | `track` | `layout` | `meta` | `units` | Rásir umfram töfluna |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (brautarnúmer Forza Motorsport 2023 er `lap.trackOrdinal`) | greind pakkauppsetning | `slip: peak`, `discipline: circuit` | aðeins einingar rása sem eru til staðar | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, klukka leiksins `timestampMs`, `raceTime`, `bestLap`, `lastLap`; hraði í ramma bílsins er undir hefðbundnu `latVel`, `vertVel`, `longVel`; `unparsed` við hlið rásanna |
| Assetto Corsa leikir (`kunos.py`) | úr föstu blaði, eða `null` | vantar | `slip: scaled`, `discipline: circuit` eða `rally` | föst skrá | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (eins og sent), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Ralllíleikir (`rally.py` um `lapfile.py`) | `null` | vantar | `discipline: rally`, `slip: null`, `surface` aðeins þegar `--surface` var gefið (annars ályktar áhorfandinn það) | aðeins einingar rása sem eru til staðar | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` fyrir fleytitölurnar án fasts heitis; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` um `lapfile.py`) | `null` | vantar | `discipline: circuit` | aðeins einingar rása sem eru til staðar | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania viðbót (CSV) | heiti kortsins | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` er Forza bílablokkin (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` fyrir Kunos leikina þegar fasta blaðið nefnir einn, og
`{}` annars. `lap.metres` er mismunur ekinnar vegalengdar leiksins fyrir Forza og
summa 3D vegalengdar milli sýna annars staðar. Gildi eru námunduð við skrif: `time` í 4
aukastafi, `distance` í 3, aðrar fleytitölur í 5. JSON er skrifað þétt (engin bil).

Hver pakki eða blað sem upptökutækið fékk - ekki aðeins hringjanna - er geymt heilt við hlið hringskránna
í `<stamp>_<game>.raw.parquet`, með sjálfsprófi í `<stamp>_<game>.summary.json` (kaflinn
"Completeness" í README).

Sýni sem rás hefur ekkert gildi fyrir - vantar í þann ramma, eða er ekki endanleg tala eins og
leikurinn sendi hana - er skrifað sem `null` af öllum upptökutækjum (`lapfile.clean`), og fjöðrunarhlutfallið
sem af því er leitt er líka `null`. `NaN` og `Infinity` eru aldrei skrifuð: þau eru ekki
JSON, og `JSON.parse` vafra hafnar allri skránni vegna eins þeirra. Lesari á að
búast við `null` inni í fylkingu rásar.

Forza skrárnar bera `"game": "forza-horizon"`, `"forza-motorsport"` eða `"forza"` eftir
greindri uppsetningu. Lesari áhorfandans á `.tele.gz` skrám FH Companion býr til hringi
með `"game": "forza-horizon"` og `meta.slip = "peak"`; sá lesari er í áhorfandanum, ekki
hér. iRacing hringir (lesnir úr `.ibt` í áhorfandanum) bera `"game": "iracing"`, sem er ekki í
listanum yfir `game` gildi upptökutækja hér að ofan því ekkert upptökutæki skrifar það.

Sjá [Hring- og leiðaskiptingu](lap-splitting.md) um hvernig `lap.number`, `lap.seconds` og
`lap.complete` eru ákveðin, og [Skrið, rek og afleiddar rásir](slip-and-drift.md) um
hvað áhorfandinn leiðir af þessum rásum.
