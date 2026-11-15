---
title: "Datoteka `heat3d-lap`"
nav_order: 9
lang: "hr"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Datoteka `heat3d-lap` {#the-heat3d-lap-file}

Svaki snimač telemetrije u ovom repozitoriju piše jednu datoteku po krugu ili vozačkoj
etapi, u istom obliku bez obzira na igru. Ispis staze u [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
čita je da bi našao igru, razinu i vožnju po stazi. Sve što može čitati JSON može čitati i nju.

![Polja i kanali datoteke kruga zapisane iz sintetičkog toka Forze](../assets/img/lap-file.svg)

## Dokument {#the-document}

Jedan JSON objekt. Kanali su pohranjeni kao stupci: jedno polje po kanalu, svi iste
duljine, jedan unos po uzorku.

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

| Polje | Značenje |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | iz koje je igre krug; vidi popis u nastavku |
| `track` | ime staze, etape ili karte, kad ga igra šalje |
| `layout` | Samo Forza: koji je raspored paketa Data Out dekodiran |
| `car` | što igra kaže o vozilu; slobodnog oblika |
| `lap` | broj kruga, njegovo vrijeme kako ga je igra brojala (ili raspon uzoraka), je li završen i njegova duljina |
| `meta` | kako čitati brojeve; vidi u nastavku |
| `units` | jedinica svakog prisutnog kanala, za čitača koji ne poznaje tablicu u nastavku |
| `channels` | uzorci |
| `unparsed` | Samo Forza, kad paket ima bajtove koje nijedno polje ne imenuje: `ranges` (njihovi pomaci `[start, end)` u paketu) i `hex` (po uzorku, ti bajtovi u heksadecimalnom zapisu), pa datoteka sama sadrži cijeli paket |

`game` je jedna od vrijednosti `forza-horizon`, `forza-motorsport`, `forza` (raspored
paketa nije razlikovan), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` kaže što brojevi znače tamo gdje se igre razlikuju:

- `slip`: što kanali klizanja sadrže, ako igra išta šalje: `peak` (normalizirano, pa iznad
  1 guma popušta: Forza), `scaled` (fizičko klizanje podijeljeno s tipičnim vrhom na
  asfaltu: igre Assetto Corsa), `physical` (udio i radijani), `index` (mjera klizanja od
  0 do 1: Trackmania);
- `discipline`: `circuit`, `rally` ili `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` ili `mixed`, kad je poznato (snimači vozačkih
  igara uzimaju ga iz `--surface`).

## Kanali {#channels}

Kanal koji igra ne šalje nije prisutan, nikad nije popunjen nulama. Kanali po kotaču
nose oznaku kotača iza točke: `.FL`, `.FR`, `.RL`, `.RR`.

Položaji su svijet igre, u metrima, s `y` prema gore. Igra čiji je svijet okrenut
prema Z gore snimač okreće tako da je Y gore; ništa drugo se ne mijenja, pa lijevo
orijentirani svijet (Forzin) ostaje lijevo orijentiran.

| Kanal | Jedinica | Značenje |
|---|---|---|
| `time` | s | od prvog uzorka kruga |
| `distance` | m | duž vožnje od prvog uzorka |
| `x`, `y`, `z` | m | položaj; `y` je visina |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedale i poluga |
| `steer` | -1..1 | pozitivno desno |
| `gear` | | kako je igra broji |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | okvir vozila |
| `yaw`, `pitch`, `roll` | rad | smjer i stav |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | brzina u okviru vozila: desno, naprijed, gore |
| `bodySlip` | rad | kut drifta, gdje ga igra šalje |
| `loose` | 0/1 | na rastresitom tlu (Trackmania) |
| `airborne` | 0/1 | nijedan kotač ne dodiruje tlo |
| `rpm` | o/min | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | kako ih igra šalje |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | pomoći u radu, sustavi uključeni |
| `absLevel`, `tcLevel` | | postavke pomoći |
| `brakeBias` | 0..1 | udio prednjih kočnica |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | po kotaču |
| `tirePressure` | psi | po kotaču |
| `tireWear` | 0..1 | po kotaču |
| `slipRatio`, `slipAngle`, `combinedSlip` | vidi `meta.slip` | po kotaču |
| `slipIndex` | 0..1 | po kotaču, mjera klizanja (Trackmania) |
| `camber` | rad | po kotaču |
| `brakeTemp` | °C | po kotaču |
| `padLife`, `discLife` | | po kotaču |
| `suspensionM` | m | put ovjesa po kotaču |
| `suspension` | 0..1 | put ovjesa po kotaču, u rasponu koji je ovaj krug koristio |
| `wheelLoad` | N | po kotaču |
| `wheelSpeed` | rad/s | okretanje kotača po kotaču |
| `wheelSurfaceSpeed` | m/s | brzina dodirne površine kotača po kotaču |
| `groundContact` | 0/1 | po kotaču |
| `rumble`, `surfaceRumble` | | po kotaču: na rubnim trakama za vibriranje; vibriranje podloge |
| `puddle` | | po kotaču, dubina stajaće vode |

Snimač može dodati vlastite kanale pod drugim imenima; čitač zadržava ono što ne poznaje.

Nijedna vozačka igra ne šalje klizanje guma. Čitač ga može izračunati iz brzine dodirne
površine svakog kotača naspram brzine vozila, `(wheel - car) / car`, ili iz okretanja i
polumjera kotrljanja izmjerenog na samom krugu tamo gdje se šalje samo okretanje. Kut
drifta dolazi iz vlastite brzine vozila (`latVel`, `longVel`) kad je poslana, ili iz
brzine svijeta projicirane na osi vozila.

## Zapis CSV {#the-csv-form}

Dodatak Trackmanie umjesto toga piše `heat3d-lap-csv`: prvi redak počinje s `# `, a
slijedi JSON objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`,
`meta`), redak s imenima kanala, pa po jedan redak za svaki uzorak. Imena kanala ista su kao gore.

## Što svaki snimač stvarno piše {#what-each-recorder-actually-writes}

Format iznad je ugovor; snimači ga popunjavaju malo drukčije, a čitač treba podnijeti sve
ove oblike (provjereno prema kodu):

| Snimač | `track` | `layout` | `meta` | `units` | Kanali izvan tablice |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (broj staze Forze Motorsport 2023. je `lap.trackOrdinal`) | otkriveni raspored paketa | `slip: peak`, `discipline: circuit` | samo jedinice prisutnih kanala | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, vremenski sat igre `timestampMs`, `raceTime`, `bestLap`, `lastLap`; brzina u okviru vozila nalazi se pod kanonskim `latVel`, `vertVel`, `longVel`; `unparsed` uz kanale |
| Igre Assetto Corsa (`kunos.py`) | iz statične stranice, ili `null` | nema | `slip: scaled`, `discipline: circuit` ili `rally` | fiksni popis | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (kako je poslan), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Vozačke igre (`rally.py` preko `lapfile.py`) | `null` | nema | `discipline: rally`, `slip: null`, `surface` samo kad je dan `--surface` (inače ga preglednik zaključuje) | samo jedinice prisutnih kanala | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` za decimalne brojeve bez ustaljenog imena; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` preko `lapfile.py`) | `null` | nema | `discipline: circuit` | samo jedinice prisutnih kanala | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Dodatak Trackmanie (CSV) | ime karte | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` je blok vozila Forze (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` za igre Kunos kad statična stranica navede ime,
a inače `{}`. `lap.metres` je razlika u prijeđenom putu koju javlja igra za Forzu, a
drugdje zbroj 3D udaljenosti između uzoraka. Vrijednosti se zaokružuju pri pisanju: `time`
na 4 decimale, `distance` na 3, ostali decimalni brojevi na 5. JSON se piše zbijeno (bez razmaka).

Svaki paket ili stranicu koju je snimač primio, ne samo one iz krugova, čuva se cijela
uz datoteke krugova u `<stamp>_<game>.raw.parquet`, s provjerom u `<stamp>_<game>.summary.json`
(odjeljak „Completeness” u README-u).

Uzorak za koji kanal nema vrijednost, jer nedostaje u tom okviru ili igra nije poslala
konačan broj, snimači zapisuju kao `null` (`lapfile.clean`), a izvedeni udio ovjesa iz
njega također je `null`. `NaN` i `Infinity` se nikad ne zapisuju: nisu JSON, a
`JSON.parse` u pregledniku odbije cijelu datoteku zbog jednog od njih. Čitač treba
očekivati `null` unutar polja kanala.

Datoteke Forze imaju `"game": "forza-horizon"`, `"forza-motorsport"` ili `"forza"`, prema
otkrivenom rasporedu. Čitač preglednika za datoteke `.tele.gz` iz FH Companion-a daje krugove
s `"game": "forza-horizon"` i `meta.slip = "peak"`; taj čitač je u pregledniku, ne ovdje.
Krugovi iz iRacinga (čitani iz `.ibt` u pregledniku) imaju `"game": "iracing"`, što nije na
popisu vrijednosti `game` iznad jer ih nijedan snimač ne piše.

Vidi [Kako se krugovi i etape dijele](lap-splitting.md) za to kako se odlučuje o `lap.number`,
`lap.seconds` i `lap.complete`, i [Klizanje, drift i izvedeni kanali](slip-and-drift.md) za
ono što preglednik izvodi iz ovih kanala.
