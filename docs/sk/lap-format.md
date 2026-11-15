---
title: "Súbor heat3d-lap"
nav_order: 9
lang: "sk"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Súbor `heat3d-lap` {#the-heat3d-lap-file}

Každý telemetrický nahrávač v tomto repozitári zapisuje jeden súbor na kolo
alebo etapu, v rovnakom tvare bez ohľadu na hru. Export trate v
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) ho číta späť,
aby zistil hru, level a jazdnú líniu. Čokoľvek, čo číta JSON, ho dokáže prečítať.

![Polia a kanály súboru kola zapísaného zo syntetického kanála Forzy](../assets/img/lap-file.svg)

## Dokument {#the-document}

Jeden objekt JSON. Kanály sú uložené ako stĺpce: jedno pole na kanál, všetky
rovnakej dĺžky, jeden záznam na vzorku.

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

| Pole | Význam |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | z ktorej hry je kolo; pozrite zoznam nižšie |
| `track` | názov trate, etapy alebo mapy, ak ho hra posiela |
| `layout` | len Forza: ktoré rozloženie paketu Data Out bolo dekódované |
| `car` | čokoľvek, čo hra hovorí o aute; voľná štruktúra |
| `lap` | číslo kola, jeho čas tak, ako ho hra počítala (alebo rozpätie vzoriek), či bolo dokončené, jeho dĺžka |
| `meta` | ako čítať čísla; pozrite nižšie |
| `units` | jednotka každého prítomného kanála, pre čítač, ktorý nepozná tabuľku nižšie |
| `channels` | vzorky |
| `unparsed` | len Forza, keď paket obsahuje bajty bez mena poľa: `ranges` (ich offsety `[start, end)` v pakete) a `hex` (pre každú vzorku tieto bajty v hexa), takže samotný súbor obsahuje celý paket |

`game` je jedna z hodnôt `forza-horizon`, `forza-motorsport`, `forza` (rozloženie
paketu nerozlíšené), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` hovorí, čo čísla znamenajú, kde sa hry líšia:

- `slip`: čo držia kanály prešmyku, ak ich hra posiela – `peak`
  (normalizovaný, takže nad 1 pneumatika stráca prilipnutie: Forza), `scaled`
  (fyzikálny prešmyk delený typickým vrcholom na asfalte: hry Assetto Corsa),
  `physical` (zlomok a radiány), `index` (0..1 kĺzavá miera: Trackmania);
- `discipline`: `circuit`, `rally` alebo `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` alebo `mixed`, ak je známy (rally
  nahrávače ho berú z `--surface`).

## Kanály {#channels}

Kanál, ktorý hra neposiela, chýba a nikdy sa nevypĺňa nulami. Kanály pre
jednotlivé kolesá nesú za bodkou názov kolesa: `.FL`, `.FR`, `.RL`, `.RR`.

Polohy sú svet hry v metroch, s `y` smerom hore. Svet hry s osou Z hore
prepočíta nahrávač tak, aby mal os Y hore; nič iné sa nemení, takže
ľavoruký svet (Forzin) zostane ľavoruký.

| Kanál | Jednotka | Význam |
|---|---|---|
| `time` | s | od prvej vzorky kola |
| `distance` | m | po jazdnej dráhe od prvej vzorky |
| `x`, `y`, `z` | m | poloha; `y` je výška |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedále a páka |
| `steer` | -1..1 | kladné doprava |
| `gear` | | tak, ako ju hra počíta |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | vo vnútornom systéme auta |
| `yaw`, `pitch`, `roll` | rad | smer a postoj |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | rýchlosť vo vnútornom systéme auta: doprava, dopredu, hore |
| `bodySlip` | rad | driftový uhol, ak ho hra posiela |
| `loose` | 0/1 | na sypkom podklade (Trackmania) |
| `airborne` | 0/1 | žiadne koleso na zemi |
| `rpm` | ot/min | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | tak, ako ich hra posiela |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | asistencie v činnosti, systémy zapnuté |
| `absLevel`, `tcLevel` | | nastavenia asistencií |
| `brakeBias` | 0..1 | podiel vpredu |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | pre každé koleso |
| `tirePressure` | psi | pre každé koleso |
| `tireWear` | 0..1 | pre každé koleso |
| `slipRatio`, `slipAngle`, `combinedSlip` | pozrite `meta.slip` | pre každé koleso |
| `slipIndex` | 0..1 | pre každé koleso kĺzavá miera (Trackmania) |
| `camber` | rad | pre každé koleso |
| `brakeTemp` | °C | pre každé koleso |
| `padLife`, `discLife` | | pre každé koleso |
| `suspensionM` | m | pre každé koleso zdvih zavesenia |
| `suspension` | 0..1 | pre každé koleso zdvih zavesenia, z rozsahu, ktorý toto kolo použilo |
| `wheelLoad` | N | pre každé koleso |
| `wheelSpeed` | rad/s | pre každé koleso otáčanie |
| `wheelSurfaceSpeed` | m/s | pre každé koleso rýchlosť kontaktnej plochy |
| `groundContact` | 0/1 | pre každé koleso |
| `rumble`, `surfaceRumble` | | pre každé koleso: na vibračnom páse; vibrácie povrchu |
| `puddle` | | pre každé koleso hĺbka stojatej vody |

Nahrávač môže pridať vlastné kanály pod inými menami; čítač ponechá to, čo
nepozná.

Žiadna rally hra neposiela prešmyk pneumatík. Čítač ho dokáže vypočítať z
rýchlosti kontaktnej plochy každého kolesa oproti rýchlosti auta,
`(koleso - auto) / auto`, alebo z jeho otáčania a valivého polomeru
zmeraného na samotnom kole, kde sa posiela len otáčanie. Driftový uhol
vychádza z vlastnej rýchlosti auta (`latVel`, `longVel`), kde sa posiela, alebo
z rýchlosti sveta premietnutej na osi auta.

## Formát CSV {#the-csv-form}

Plugin Trackmania zapisuje namiesto toho `heat3d-lap-csv`: prvý riadok s `# `
a objektom JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`,
`meta`), riadok s menami kanálov a potom jeden riadok na vzorku. Mená kanálov
sú rovnaké ako vyššie.

## Čo každý nahrávač naozaj zapisuje {#what-each-recorder-actually-writes}

Formát vyššie je zmluva; nahrávače ho vypĺňajú trochu inak a čítač by mal
tolerovať všetky tieto variácie (overené proti kódu):

| Nahrávač | `track` | `layout` | `meta` | `units` | Kanály nad rámec tabuľky |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (číslo trate Forza Motorsport 2023 je `lap.trackOrdinal`) | zistené rozloženie paketu | `slip: peak`, `discipline: circuit` | len jednotky prítomných kanálov | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, hodinový čas hry `timestampMs`, `raceTime`, `bestLap`, `lastLap`; rýchlosť vo vnútornom systéme auta je pod kanonickými `latVel`, `vertVel`, `longVel`; `unparsed` vedľa kanálov |
| Hry Assetto Corsa (`kunos.py`) | zo statickej stránky, alebo `null` | chýba | `slip: scaled`, `discipline: circuit` alebo `rally` | pevný zoznam | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (ako poslané), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rally hry (`rally.py` cez `lapfile.py`) | `null` | chýba | `discipline: rally`, `slip: null`, `surface` len ak bol zadaný `--surface` (inak ho odvodí prehliadač) | len jednotky prítomných kanálov | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` pre plávajúce čísla bez ustáleného mena; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` cez `lapfile.py`) | `null` | chýba | `discipline: circuit` | len jednotky prítomných kanálov | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Plugin Trackmania (CSV) | názov mapy | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` je blok auta z Forzy (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` pre hry Kunos, keď statická stránka
názov uvádza, a inak `{}`. `lap.metres` je pre Forzu rozdiel prejdenej
vzdialenosti hry a inde súčet 3D vzdialeností medzi vzorkami. Hodnoty sa pri
zápise zaokrúhľujú: `time` na 4 desatinné miesta, `distance` na 3, ostatné
desatinné čísla na 5. JSON sa zapisuje kompaktne (bez medzier).

Každý paket alebo stránka, ktorú nahrávač dostal – nielen kolá – sa uchová
celá vedľa súborov kôl ako `<stamp>_<game>.raw.parquet`, so samokontrolou v
`<stamp>_<game>.summary.json` (sekcia „Completeness“ v README).

Vzorka, pri ktorej kanál nemá hodnotu – chýba v tom snímku alebo nie je konečné
číslo tak, ako ho hra poslala – sa každým nahrávačom zapíše ako `null`
(`lapfile.clean`), a odvodený zlomok zavesenia z nej je tiež `null`. `NaN` a
`Infinity` sa nikdy nezapisujú: nie sú JSON a `JSON.parse` v prehliadači
odmietne celý súbor kvôli jednému z nich. Čítač má počítať s hodnotou `null`
vnútri poľa kanála.

Súbory Forzy nesú `"game": "forza-horizon"`, `"forza-motorsport"` alebo `"forza"`
podľa zisteného rozloženia. Čítač prehliadača pre súbory `.tele.gz` od FH
Companion vytvára kolá s `"game": "forza-horizon"` a `meta.slip = "peak"`; tento
čítač je v prehliadači, nie tu. Kolá iRacing (čítané z `.ibt` v prehliadači) nesú
`"game": "iracing"`, čo nie je v zozname hodnôt `game` nahrávačov vyššie, lebo
žiadny nahrávač ho nezapisuje.

Pozrite [Delenie kôl a etáp](lap-splitting.md), ako sa rozhoduje o `lap.number`,
`lap.seconds` a `lap.complete`, a [Prešmyk, drift a odvodené kanály](slip-and-drift.md),
čo prehliadač z týchto kanálov odvodzuje.
