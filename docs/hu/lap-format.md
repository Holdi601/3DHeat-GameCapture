---
title: "A heat3d-lap fájl"
nav_order: 9
lang: "hu"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# A `heat3d-lap` fájl {#the-heat3d-lap-file}

Ez a tárolóban minden telemetriarögzítő egy fájlt ír körönként vagy ralisztárónként, játéktól függetlenül ugyanabban a formában. A [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) pályaexportja visszaolvassa, hogy megtalálja a játékot, a pályát és a megtett vonalat. Bármi, ami JSON-t olvas, el tudja olvasni.

![A szintetikus Forza-adatfolyamból írt körfájl mezői és csatornái](../assets/img/lap-file.svg)

## A dokumentum {#the-document}

Egyetlen JSON-objektum. A csatornák oszlopokként vannak tárolva: csatornánként egy tömb, mind azonos hosszúságú, mintánként egy elemmel.

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

| Mező | Jelentése |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | melyik játékból való a kör; lent a lista |
| `track` | a pálya, szakasz vagy térkép neve, ha a játék megadja |
| `layout` | csak Forzánál: melyik Data Out csomagelrendezést dekódolták |
| `car` | bármi, amit a játék az autóról mond; kötetlen formában |
| `lap` | a kör száma, az ideje a játék számolása szerint (vagy a minták időtartama), hogy be lett-e fejezve, és a hossza |
| `meta` | hogyan kell olvasni a számokat; lent |
| `units` | minden jelen lévő csatorna mértékegysége, egy olyan olvasónak, amely nem ismeri az alábbi táblázatot |
| `channels` | a minták |
| `unparsed` | csak Forzánál, ha a csomagban van olyan bájt, amelynek nincs mezőneve: `ranges` (a bájtok `[kezdet, vég)` eltolásai a csomagban) és `hex` (mintánként ezek a bájtok hexadecimálisan), így a fájl önmagában tartalmazza a teljes csomagot |

A `game` a következők egyike: `forza-horizon`, `forza-motorsport`, `forza` (a csomagelrendezést nem különböztették meg), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

A `meta` megmondja, mit jelentenek a számok ott, ahol a játékok eltérnek:

- `slip`: mit tartalmaznak a csúszási csatornák, ha a játék küld bármit – `peak` (normalizált, így 1 felett a gumi elengedi az utat: Forza), `scaled` (fizikai csúszás osztva egy tipikus aszfaltcsúccsal: az Assetto Corsa-játékok), `physical` (törtszám és radián), `index` (0..1-es csúszásmérték: Trackmania);
- `discipline`: `circuit`, `rally` vagy `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` vagy `mixed`, ha ismert (a ralirögzítők a `--surface` kapcsolóból veszik).

## Csatornák {#channels}

Amelyik csatornát a játék nem küld, az hiányzik, soha nincs nullákkal kitöltve. A kerekenkénti csatornák a kerék jelét a pont után hordozzák: `.FL`, `.FR`, `.RL`, `.RR`.

A pozíciók a játék világában vannak, méterben, `y` értékkel felfelé. Ha egy játék világa Z-felfelé áll, a rögzítője Y-felfelé forgatja; más nem változik, így a balkezes világ (a Forzáé) balkezes marad.

| Csatorna | Egység | Jelentése |
|---|---|---|
| `time` | s | a kör első mintájától számítva |
| `distance` | m | a megtett úton, az első mintától számítva |
| `x`, `y`, `z` | m | pozíció; `y` a magasság |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedálok és kar |
| `steer` | -1..1 | pozitív jobbra |
| `gear` | | ahogy a játék számolja |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | autó-keretben |
| `yaw`, `pitch`, `roll` | rad | irány és hozzáállás |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | sebesség az autó keretében: jobbra, előre, felfelé |
| `bodySlip` | rad | driftszög, ahol a játék küldi |
| `loose` | 0/1 | laza talajon (Trackmania) |
| `airborne` | 0/1 | egy kerék sincs a talajon |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | ahogy a játék küldi |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | segédrendszerek működnek, a rendszerek be vannak kapcsolva |
| `absLevel`, `tcLevel` | | segédbeállítások |
| `brakeBias` | 0..1 | az első tengely részaránya |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | kerekenként |
| `tirePressure` | psi | kerekenként |
| `tireWear` | 0..1 | kerekenként |
| `slipRatio`, `slipAngle`, `combinedSlip` | lásd `meta.slip` | kerekenként |
| `slipIndex` | 0..1 | kerekenkénti csúszásmérték (Trackmania) |
| `camber` | rad | kerekenként |
| `brakeTemp` | °C | kerekenként |
| `padLife`, `discLife` | | kerekenként |
| `suspensionM` | m | kerekenkénti utazás |
| `suspension` | 0..1 | kerekenkénti utazás, az adott körben használt tartomány szerint |
| `wheelLoad` | N | kerekenként |
| `wheelSpeed` | rad/s | kerekenkénti forgás |
| `wheelSurfaceSpeed` | m/s | kerekenkénti érintkezési folt sebessége |
| `groundContact` | 0/1 | kerekenként |
| `rumble`, `surfaceRumble` | | kerekenként: rezgősávon van-e; a felület zörgése |
| `puddle` | | kerekenként: az álló víz mélysége |

A rögzítő saját, más nevű csatornákat is adhat hozzá; az olvasó megtartja azt, amit nem ismer.

Egyik ralijáték sem küld gumicsúszást. Az olvasó ki tudja számolni kerekenként az érintkezési folt vagy a felületi sebesség és az autó sebességének különbségéből, `(kerék - autó) / autó` alakban, vagy ha csak a forgást küldi, akkor a forgásából és a körön magán mért gördülősugárból. A driftszöget az autó saját sebességéből (`latVel`, `longVel`) számoljuk, ahol az küldve van, vagy a világsebességből, az autó tengelyeire vetítve.

## A CSV-forma {#the-csv-form}

A Trackmania-bővítmény helyette `heat3d-lap-csv` formátumot ír: az első sor `# ` jellel kezdődik, és egy JSON-objektumot tartalmaz (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), ezt követi a csatornanevek sora, majd soronként egy minta. A csatornanevek ugyanazok, mint fent.

## Amit az egyes rögzítők ténylegesen írnak {#what-each-recorder-actually-writes}

A fenti formátum a szerződés; a rögzítők kicsit másképp töltik ki, és az olvasónak mindezeket el kell viselnie (a kóddal egyeztetve):

| Rögzítő | `track` | `layout` | `meta` | `units` | A táblázaton túli csatornák |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (a Forza Motorsport 2023 pályaszáma a `lap.trackOrdinal`) | a felismert csomagelrendezés | `slip: peak`, `discipline: circuit` | csak a jelen lévő csatornák egységei | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, a játék órája `timestampMs`, `raceTime`, `bestLap`, `lastLap`; az autó-helyi sebesség a kanonikus `latVel`, `vertVel`, `longVel` alatt; `unparsed` a csatornák mellett |
| Assetto Corsa-játékok (`kunos.py`) | a statikus oldalból, vagy `null` | hiányzik | `slip: scaled`, `discipline: circuit` vagy `rally` | rögzített lista | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (ahogy érkezett), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Ralijátékok (`rally.py` a `lapfile.py`-on keresztül) | `null` | hiányzik | `discipline: rally`, `slip: null`, `surface` csak ha a `--surface` meg volt adva (egyébként az olvasó következtet) | csak a jelen lévő csatornák egységei | `stageDistance`; WRC: `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT: `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` azokra a lebegőpontos számokra, amelyeknek nincs kész nevük; RBR: `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` a `lapfile.py`-on keresztül) | `null` | hiányzik | `discipline: circuit` | csak a jelen lévő csatornák egységei | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-bővítmény (CSV) | a pálya neve | - | `slip: index`, `discipline: arcade` | - | `respawns` |

A `car` a Forza autóblokkja (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), a Kunos-játékoknál `{"name": ...}`, ha a statikus oldal megnevez egy autót, és egyébként `{}`. A `lap.metres` a Forzánál a játék megtett-távolság-különbsége, máshol a mintáknak a köztük lévő összegzett 3D-távolsága. Az értékek írásakor kerekítünk: a `time` 4 tizedesjegyre, a `distance` 3-ra, a többi lebegőpontos szám 5-re. A JSON tömörítve íródik (szóközök nélkül).

A rögzítő minden csomagot vagy oldalt, amelyet kapott – nemcsak a köröket –, teljes egészében megtart a körfájlok mellett, a `<stamp>_<game>.raw.parquet` fájlban, egy önellenőrzéssel a `<stamp>_<game>.summary.json` fájlban (a README „Teljesség” szakasza).

Egy minta, amelyhez a csatornának nincs értéke – hiányzik abból a képkockából, vagy a játék nem véges számot küldött –, minden rögzítőnél `null`-ként íródik (`lapfile.clean`), és az abból számolt felfüggesztési arány is `null`. A `NaN` és az `Infinity` soha nem íródik: ezek nem JSON, és a böngésző `JSON.parse` függvénye egyetlen ilyen miatt is visszautasítja az egész fájlt. Az olvasónak számítania kell arra, hogy egy csatorna tömbjében `null` lehet.

A Forza-fájlokban a `"game"` értéke `"forza-horizon"`, `"forza-motorsport"` vagy `"forza"` a felismert elrendezés szerint. A nézegető FH Companion `.tele.gz` fájljait olvasó része `"game": "forza-horizon"` és `meta.slip = "peak"` köröket állít elő; ez az olvasó a nézegetőben van, nem itt. Az iRacing-körök (a nézegetőben `.ibt`-ből olvasva) `"game": "iracing"` értéket viselnek, ami nincs a fenti rögzítő-`game` értékek listáján, mert egyetlen rögzítő sem írja.

A `lap.number`, `lap.seconds` és `lap.complete` eldöntéséhez lásd a [Kör- és szakaszdarabolás](lap-splitting.md) oldalt; a nézegető által ezekből a csatornákból származtatottakhoz pedig a [Csúszás, driftszög és származtatott csatornák](slip-and-drift.md) oldalt.
