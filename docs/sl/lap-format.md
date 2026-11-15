---
title: "Datoteka `heat3d-lap`"
nav_order: 9
lang: "sl"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Datoteka `heat3d-lap` {#the-heat3d-lap-file}

Vsak snemalnik telemetrije v tem repozitoriju zapiše eno datoteko na krog ali relijsko etapo, v isti obliki ne glede na igro. Izvoz proge v [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) jo prebere, da najde igro, nivo in odpeljano linijo. Vse, kar bere JSON, lahko prebere tudi to.

![Polja in kanali datoteke kroga, zapisane iz sintetičnega vira Forze](../assets/img/lap-file.svg)

## Dokument {#the-document}

En JSON objekt. Kanali so shranjeni kot stolpci: en niz na kanal, vsi enake dolžine, en vnos na vzorec.

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

| Polje | Pomen |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | katera igra je krog; glejte seznam spodaj |
| `track` | ime proge, etape ali zemljevida, kadar ga igra pove |
| `layout` | samo Forza: katera postavitev paketa Data Out je bila dekodirana |
| `car` | kar igra pove o avtu; prosta oblika |
| `lap` | številka kroga, njegov čas, kot ga je štela igra (ali razpon vzorcev), ali je bil končan, njegova dolžina |
| `meta` | kako brati številke; glejte spodaj |
| `units` | enota vsakega prisotnega kanala, za bralnik, ki ne pozna spodnje tabele |
| `channels` | vzorci |
| `unparsed` | samo Forza, kadar paket vsebuje bajte, ki jim ne ustreza nobeno polje: `ranges` (njihovi odmiki v paketu v obliki `[start, end)`) in `hex` (za vsak vzorec ti bajti v šestnajstiški obliki), tako da datoteka sama hrani ves paket |

`game` je ena od vrednosti: `forza-horizon`, `forza-motorsport`, `forza` (postavitev paketa ni ločena), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` pove, kaj številke pomenijo tam, kjer se igre razlikujejo:

- `slip`: kaj držijo kanali zdrsa, kjer jih igra pošlje – `peak` (normirano, nad 1 guma popusti: Forza), `scaled` (fizikalni zdrs, deljen s tipično vrednostjo vrha na asfaltu: igre Assetto Corsa), `physical` (delež in radiani), `index` (merilo drsenja med 0 in 1: Trackmania);
- `discipline`: `circuit` (krožna), `rally` (relijska) ali `arcade` (arkadna);
- `surface`: `tarmac`, `loose`, `snow`, `ice` ali `mixed` (asfalt, nevezano, sneg, led ali mešano), kadar je znano (relijski snemalniki to vzamejo iz `--surface`).

## Kanali {#channels}

Kanal, ki ga igra ne pošlje, je odsoten, nikoli zapolnjen z ničlami. Kanali po kolesu nosijo ob piki ime kolesa: `.FL`, `.FR`, `.RL`, `.RR`.

Položaji so svet igre v metrih, z `y` navzgor. Igra, katere svet je z Z navzgor, jo njen snemalnik obrne na Y navzgor; nič drugega se ne spremeni. Levosučen svet (Forzin) tako ostane levosučen.

| Kanal | Enota | Pomen |
|---|---|---|
| `time` | s | od prvega vzorca kroga |
| `distance` | m | po prevoženi poti od prvega vzorca |
| `x`, `y`, `z` | m | položaj; `y` je višina |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedala in ročica |
| `steer` | -1..1 | pozitivno desno |
| `gear` | | kot jo šteje igra |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | koordinatni sistem avta |
| `yaw`, `pitch`, `roll` | rad | smer in drža |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | hitrost v koordinatnem sistemu avta: desno, naprej, navzgor |
| `bodySlip` | rad | kot drifta, kjer ga igra pošlje |
| `loose` | 0/1 | na ohlapni podlagi (Trackmania) |
| `airborne` | 0/1 | nobeno kolo ni na tleh |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | kot ju pošlje igra |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | pomoči delujejo, sistemi vklopljeni |
| `absLevel`, `tcLevel` | | nastavitve pomoči |
| `brakeBias` | 0..1 | delež sprednje osi |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | po kolesu |
| `tirePressure` | psi | po kolesu |
| `tireWear` | 0..1 | po kolesu |
| `slipRatio`, `slipAngle`, `combinedSlip` | glejte `meta.slip` | po kolesu |
| `slipIndex` | 0..1 | po kolesu, merilo drsenja (Trackmania) |
| `camber` | rad | po kolesu |
| `brakeTemp` | °C | po kolesu |
| `padLife`, `discLife` | | po kolesu |
| `suspensionM` | m | pot kolesa vzmetenja |
| `suspension` | 0..1 | pot kolesa vzmetenja, na območju, ki ga je ta krog uporabil |
| `wheelLoad` | N | po kolesu |
| `wheelSpeed` | rad/s | vrtenje kolesa, po kolesu |
| `wheelSurfaceSpeed` | m/s | hitrost točke stika kolesa, po kolesu |
| `groundContact` | 0/1 | po kolesu |
| `rumble`, `surfaceRumble` | | po kolesu: na robnem pasu; pasu površine |
| `puddle` | | po kolesu: globina stoječe vode |

Snemalnik lahko doda svoje kanale pod drugimi imeni; bralnik ohrani tiste, ki jih ne pozna.

Nobena relijska igra ne pošlje zdrsa gume. Bralnik ga lahko izračuna iz hitrosti točke stika ali površine vsakega kolesa glede na hitrost avta, `(kolo - avto) / avto`, oziroma iz vrtenja in polmera kotaljenja, izmerjenega na samem krogu, kjer je poslano samo vrtenje. Kot drifta pride iz lastne hitrosti avta (`latVel`, `longVel`), kadar je poslana, ali iz svetovne hitrosti, projicirane na osi avta.

## Oblika CSV {#the-csv-form}

Vtičnik za Trackmanio namesto tega zapiše `heat3d-lap-csv`: prva vrstica se začne z `# `, sledi JSON objekt (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), vrstica imen kanalov in nato ena vrstica na vzorec. Imena kanalov so ista kot zgoraj.

## Kaj vsak snemalnik dejansko zapiše {#what-each-recorder-actually-writes}

Zgornja oblika je pogodba; snemalniki jo napolnijo nekoliko drugače, bralnik pa mora vse to prenesti. Preverjeno v kodi:

| Snemalnik | `track` | `layout` | `meta` | `units` | Kanali zunaj tabele |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (številka proge Forze Motorsport 2023 je `lap.trackOrdinal`) | zaznana postavitev paketa | `slip: peak`, `discipline: circuit` | samo enote prisotnih kanalov | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, igrina ura `timestampMs`, `raceTime`, `bestLap`, `lastLap`; lokalna hitrost avta je pod kanoničnimi imeni `latVel`, `vertVel`, `longVel`; `unparsed` poleg kanalov |
| Igre Assetto Corsa (`kunos.py`) | iz statične strani ali `null` | ni | `slip: scaled`, `discipline: circuit` ali `rally` | fiksni seznam | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (kot poslano), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Relijske igre (`rally.py` prek `lapfile.py`) | `null` | ni | `discipline: rally`, `slip: null`, `surface` samo, kadar je bil dan `--surface` (sicer ga določi pregledovalnik) | samo enote prisotnih kanalov | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` za števila brez ustaljenega imena; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` prek `lapfile.py`) | `null` | ni | `discipline: circuit` | samo enote prisotnih kanalov | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Vtičnik Trackmania (CSV) | ime zemljevida | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` je blok avta iz Forze (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` za igre Kunos, kadar statična stran pove ime, in sicer `{}`. `lap.metres` je pri Forzi razlika prevožene razdalje, ki jo šteje igra, drugod pa seštevek 3D razdalj med vzorci. Vrednosti se pri zapisu zaokrožijo: `time` na 4 decimalke, `distance` na 3, ostala decimalna števila na 5. JSON je zapisan zgoščeno (brez presledkov).

Vsak paket ali stran, ki jo snemalnik prejme – ne le tiste v krogih – se ohrani celoten poleg datotek krogov v `<stamp>_<game>.raw.parquet`, s samopreverjanjem v `<stamp>_<game>.summary.json` (razdelek "Completeness" v README-ju).

Vzorec, za katerega kanal nima vrednosti – manjka v tistem okvirju ali igra ni poslala končnega števila – vsak snemalnik zapiše kot `null` (`lapfile.clean`); izpeljan delež vzmetenja iz njega je tudi `null`. `NaN` in `Infinity` se nikoli ne zapišeta: nista JSON, brskalnikov `JSON.parse` pa zavrne celo datoteko zaradi enega od njiju. Bralnik mora pričakovati `null` znotraj niza kanala.

Datoteke Forze imajo `"game": "forza-horizon"`, `"forza-motorsport"` ali `"forza"`, glede na zaznano postavitev. Bralnik pregledovalnika za datoteke `.tele.gz` FH Companiona ustvari kroge z `"game": "forza-horizon"` in `meta.slip = "peak"`; ta bralnik je v pregledovalniku, ne tukaj. Krogi iRacinga (prebrani iz `.ibt` v pregledovalniku) imajo `"game": "iracing"`, ki ni na zgornjem seznamu vrednosti `game`, ker je nobeden od snemalnikov ne zapisuje.

Glejte [Razdeljevanje krogov in etap](lap-splitting.md), kako se odločita `lap.number`, `lap.seconds` in `lap.complete`, in [Zdrs, drift in izpeljani kanali](slip-and-drift.md), kaj pregledovalnik izpelje iz teh kanalov.
