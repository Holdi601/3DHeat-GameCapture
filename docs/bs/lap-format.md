---
title: "Datoteka heat3d-lap"
nav_order: 9
lang: "bs"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Datoteka `heat3d-lap` {#the-heat3d-lap-file}

Svaki telemetrijski snimač u ovom repozitoriju piše jednu datoteku po krugu ili
reli dionici, u istom obliku bez obzira na igru. Izvoz staze u [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
čita je nazad da bi pronašao igru, nivo i prevoženu liniju. Sve što čita JSON može je pročitati.

![Polja i kanali datoteke kruga zapisane iz sintetičkog Forza feeda](../assets/img/lap-file.svg)

## Dokument {#the-document}

Jedan JSON objekt. Kanali su pohranjeni kao kolone: jedan niz po kanalu, svi
iste dužine, jedan unos po uzorku.

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
| `game` | iz koje je igre krug; pogledajte spisak ispod |
| `track` | ime staze, dionice ili mape, kada ga igra šalje |
| `layout` | samo Forza: koji je raspored Data Out paketa dekodiran |
| `car` | sve što igra kaže o automobilu; slobodan oblik |
| `lap` | broj kruga, njegovo vrijeme kako ga je igra brojala (ili raspon uzoraka), je li završen, njegova dužina |
| `meta` | kako čitati brojeve; pogledajte ispod |
| `units` | jedinica svakog prisutnog kanala, za čitač koji ne poznaje tabelu ispod |
| `channels` | uzorci |
| `unparsed` | samo Forza, kada paket ima bajtove koje nijedno polje ne imenuje: `ranges` (njihovi pomaci bajtova `[start, end)` u paketu) i `hex` (po uzorku, ti bajtovi kao heksadecimalni zapis), tako da sama datoteka drži cijeli paket |

`game` je jedno od: `forza-horizon`, `forza-motorsport`, `forza` (raspored
paketa nije razlučen), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` kaže šta brojevi znače tamo gdje se igre razlikuju:

- `slip`: šta drže kanali klizanja, tamo gdje ih igra šalje - `peak`
  (normalizirano, pa preko 1 guma popušta: Forza), `scaled` (fizičko klizanje
  podijeljeno tipičnim asfaltnim vrhom: Assetto Corsa igre), `physical` (razlomak
  i radijani), `index` (mjera klizanja od 0 do 1: Trackmania);
- `discipline`: `circuit`, `rally` ili `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` ili `mixed`, kada je poznato (reli
  snimači je uzimaju iz `--surface`).

## Kanali {#channels}

Kanal koji igra ne šalje je odsutan, nikada popunjen nulama. Kanali po točku
nose točak iza tačke: `.FL`, `.FR`, `.RL`, `.RR`.

Pozicije su svijet igre, u metrima, sa `y` prema gore. Igra čiji je svijet
Z-gore okreće se u Y-gore u svom snimaču; ništa drugo se ne mijenja, pa
lijevoruki svijet (Forzin) ostaje lijevoruk.

| Kanal | Jedinica | Značenje |
|---|---|---|
| `time` | s | od prvog uzorka kruga |
| `distance` | m | duž prevaljene putanje od prvog uzorka |
| `x`, `y`, `z` | m | pozicija; `y` je visina |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedale i ručica |
| `steer` | -1..1 | pozitivno udesno |
| `gear` | | kako ga igra broji |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | okvir automobila |
| `yaw`, `pitch`, `roll` | rad | smjer i stav |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | brzina u okviru automobila: desno, naprijed, gore |
| `bodySlip` | rad | ugao zanošenja, tamo gdje ga igra šalje |
| `loose` | 0/1 | na rastresitom tlu (Trackmania) |
| `airborne` | 0/1 | nijedan točak nije na tlu |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | kako ih igra šalje |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | pomoćni sistemi u radu, sistemi uključeni |
| `absLevel`, `tcLevel` | | postavke pomoćnih sistema |
| `brakeBias` | 0..1 | prednji udio |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | po točku |
| `tirePressure` | psi | po točku |
| `tireWear` | 0..1 | po točku |
| `slipRatio`, `slipAngle`, `combinedSlip` | pogledajte `meta.slip` | po točku |
| `slipIndex` | 0..1 | mjera klizanja po točku (Trackmania) |
| `camber` | rad | po točku |
| `brakeTemp` | °C | po točku |
| `padLife`, `discLife` | | po točku |
| `suspensionM` | m | hod po točku |
| `suspension` | 0..1 | hod po točku, u rasponu koji je ovaj krug koristio |
| `wheelLoad` | N | po točku |
| `wheelSpeed` | rad/s | rotacija po točku |
| `wheelSurfaceSpeed` | m/s | brzina kontaktne površine po točku |
| `groundContact` | 0/1 | po točku |
| `rumble`, `surfaceRumble` | | po točku: na rumble traci; vibracija površine |
| `puddle` | | dubina stajaće vode po točku |

Snimač može dodati vlastite kanale pod drugim imenima; čitač zadržava ono što
ne poznaje.

Nijedna reli igra ne šalje klizanje guma. Čitač ga može izračunati iz brzine
kontaktne površine ili površine svakog točka u odnosu na brzinu automobila,
`(wheel - car) / car`, ili iz njegove rotacije i radijusa kotrljanja izmjerenog
na samom krugu tamo gdje se šalje samo rotacija. Ugao zanošenja dolazi iz
vlastite brzine automobila (`latVel`, `longVel`) tamo gdje se šalje, ili iz
svjetske brzine projicirane na ose automobila.

## CSV oblik {#the-csv-form}

Trackmania dodatak umjesto toga piše `heat3d-lap-csv`: prvi red je `# `
i JSON objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`,
`meta`), zatim red s imenima kanala, pa jedan red po uzorku. Imena kanala su
ista kao gore.

## Šta svaki snimač zaista piše {#what-each-recorder-actually-writes}

Gornji format je ugovor; snimači ga popunjavaju malo različito, a čitač
treba tolerisati sve ovo (provjereno prema kodu):

| Snimač | `track` | `layout` | `meta` | `units` | Kanali izvan tabele |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (broj staze u Forza Motorsport 2023 je `lap.trackOrdinal`) | otkriveni raspored paketa | `slip: peak`, `discipline: circuit` | samo jedinice prisutnih kanala | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, igrin sat `timestampMs`, `raceTime`, `bestLap`, `lastLap`; brzina u lokalnom okviru automobila je pod kanonskim `latVel`, `vertVel`, `longVel`; `unparsed` pored kanala |
| Assetto Corsa igre (`kunos.py`) | sa statične stranice, ili `null` | odsutan | `slip: scaled`, `discipline: circuit` ili `rally` | fiksan spisak | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (kako je poslan), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Reli igre (`rally.py` preko `lapfile.py`) | `null` | odsutan | `discipline: rally`, `slip: null`, `surface` samo kada je dat `--surface` (inače ga preglednik zaključuje) | samo jedinice prisutnih kanala | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` za float vrijednosti bez utvrđenog imena; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` preko `lapfile.py`) | `null` | odsutan | `discipline: circuit` | samo jedinice prisutnih kanala | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania dodatak (CSV) | ime mape | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` je Forza blok automobila (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` za Kunos igre kada statična stranica navodi ime, i
`{}` inače. `lap.metres` je razlika prevaljene udaljenosti igre za Forzu, a drugdje
zbir 3D udaljenosti između uzoraka. Vrijednosti se pri pisanju zaokružuju: `time` na 4
decimale, `distance` na 3, ostali float-ovi na 5. JSON se piše zbijeno (bez razmaka).

Svaki paket ili stranica koju je snimač primio - ne samo krugova - čuva se cijel pored datoteka kruga
u `<stamp>_<game>.raw.parquet`, s autoprovjerom u `<stamp>_<game>.summary.json` (odjeljak
"Completeness" u README-u).

Uzorak za koji kanal nema vrijednost - nedostaje u tom kadru, ili nije konačan broj kako ga je
igra poslala - svaki snimač zapisuje kao `null` (`lapfile.clean`), a iz njega izvedena
frakcija ovjesa je također `null`. `NaN` i `Infinity` se nikada ne zapisuju: nisu
JSON, a preglednikov `JSON.parse` odbija cijelu datoteku zbog jednog od njih. Čitač treba
očekivati `null` unutar niza kanala.

Forza datoteke nose `"game": "forza-horizon"`, `"forza-motorsport"` ili `"forza"` prema
otkrivenom rasporedu. Čitač FH Companion `.tele.gz` datoteka u pregledniku proizvodi krugove
s `"game": "forza-horizon"` i `meta.slip = "peak"`; taj čitač je u pregledniku, ne
ovdje. iRacing krugovi (čitani iz `.ibt` u pregledniku) nose `"game": "iracing"`, što nije u
gornjem spisku `game` vrijednosti snimača jer ga nijedan snimač ne piše.

Pogledajte [Dijeljenje na krugove i dionice](lap-splitting.md) o tome kako se odlučuju `lap.number`, `lap.seconds` i
`lap.complete`, te [Klizanje, zanošenje i izvedeni kanali](slip-and-drift.md) o tome
šta preglednik izvodi iz ovih kanala.
