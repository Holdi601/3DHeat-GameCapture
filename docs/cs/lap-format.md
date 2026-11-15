---
title: "Soubor heat3d-lap"
nav_order: 9
lang: "cs"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Soubor `heat3d-lap` {#the-heat3d-lap-file}

Každý telemetrický nahrávač v tomto repozitáři zapisuje jeden soubor na kolo nebo
rallye etapu, ve stejném tvaru bez ohledu na hru. Export tratě v
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) ho čte zpět,
aby zjistil hru, level a odjetou linii. Cokoli, co čte JSON, ho umí číst.

![Pole a kanály souboru kola zapsaného ze syntetického kanálu Forzy](../assets/img/lap-file.svg)

## Dokument {#the-document}

Jeden objekt JSON. Kanály jsou uloženy jako sloupce: jedno pole na kanál, všechna
stejně dlouhá, jedna položka na vzorek.

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
| `game` | ze které hry kolo je; viz seznam níže |
| `track` | název trati, etapy nebo mapy, pokud ho hra pošle |
| `layout` | jen Forza: který rozložení paketu Data Out bylo dekódováno |
| `car` | cokoli, co hra řekne o autě; volný tvar |
| `lap` | číslo kola, jeho čas tak, jak ho hra počítala (nebo rozpětí vzorků), zda bylo dokončeno, jeho délka |
| `meta` | jak číst čísla; viz níže |
| `units` | jednotka každého přítomného kanálu, pro čtenáře, který tabulku níže nezná |
| `channels` | vzorky |
| `unparsed` | jen Forza, když paket obsahuje bajty, které nemají žádné pojmenované pole: `ranges` (jejich rozsahy `[start, end)` v bajtech paketu) a `hex` (pro každý vzorek ty bajty jako hex), takže samotný soubor drží celý paket |

`game` je jedna z hodnot `forza-horizon`, `forza-motorsport`, `forza` (rozložení
paketu nerozlišeno), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` říká, co čísla znamenají, kde se hry liší:

- `slip`: co držají kanály skluzu, pokud hra nějaké posílá - `peak`
  (normalizovaný, takže nad 1 pneumatika ztrácí přilnavost: Forza), `scaled`
  (fyzikální skluz vydělený typickým vrcholem přilnavosti na asfaltu: hry Assetto
  Corsa), `physical` (zlomek a radiány), `index` (měřítko skluzu 0..1: Trackmania);
- `discipline`: `circuit`, `rally` nebo `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` nebo `mixed`, je-li znám (rallye
  nahrávače ho berou z `--surface`).

## Kanály {#channels}

Kanál, který hra neposílá, chybí; nikdy není vyplněn nulami. Kanály pro jednotlivá
kola nesou kolo za tečkou: `.FL`, `.FR`, `.RL`, `.RR`.

Polohy jsou světové souřadnice hry v metrech, s `y` nahoru. Hra, jejíž svět je
s osou Z nahoru, se jejím nahrávačem otočí na osu Y nahoru; nic dalšího se nemění,
takže levotočivý svět (Forzin) zůstane levotočivý.

| Kanál | Jednotka | Význam |
|---|---|---|
| `time` | s | od prvního vzorku kola |
| `distance` | m | po odjeté dráze od prvního vzorku |
| `x`, `y`, `z` | m | poloha; `y` je výška |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedály a páka |
| `steer` | -1..1 | kladné doprava |
| `gear` | | tak, jak ji hra počítá |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | rám auta |
| `yaw`, `pitch`, `roll` | rad | směr a postoj |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | rychlost v rámu auta: doprava, dopředu, nahoru |
| `bodySlip` | rad | driftový úhel, pokud ho hra posílá |
| `loose` | 0/1 | na volném povrchu (Trackmania) |
| `airborne` | 0/1 | žádné kolo na zemi |
| `rpm` | ot/min | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | tak, jak je hra posílá |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | asistence v činnosti, systémy zapnuté |
| `absLevel`, `tcLevel` | | nastavení asistencí |
| `brakeBias` | 0..1 | podíl předních brzd |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | na kolo |
| `tirePressure` | psi | na kolo |
| `tireWear` | 0..1 | na kolo |
| `slipRatio`, `slipAngle`, `combinedSlip` | viz `meta.slip` | na kolo |
| `slipIndex` | 0..1 | měřítko skluzu na kolo (Trackmania) |
| `camber` | rad | na kolo |
| `brakeTemp` | °C | na kolo |
| `padLife`, `discLife` | | na kolo |
| `suspensionM` | m | zdvih kola |
| `suspension` | 0..1 | zdvih kola, z rozsahu, který toto kolo použilo |
| `wheelLoad` | N | na kolo |
| `wheelSpeed` | rad/s | otáčení kola |
| `wheelSurfaceSpeed` | m/s | rychlost styku pneumatiky na kolo |
| `groundContact` | 0/1 | na kolo |
| `rumble`, `surfaceRumble` | | na kolo: na vibračním pásu; vibrace povrchu |
| `puddle` | | na kolo: hloubka stojící vody |

Nahrávač může přidat vlastní kanály pod jinými názvy; čtenář zachová to, co
nezná.

Žádná rallye hra neposílá skluz pneumatik. Čtenář ho umí spočítat z rychlosti styku
každého kola nebo povrchu proti rychlosti auta, `(kolo - auto) / auto`, nebo z
otáčení a poloměru valení změřeného na samotném kole, pokud posílá jen otáčení.
Driftový úhel vychází z vlastní rychlosti auta (`latVel`, `longVel`), kde je
posílána, nebo ze světové rychlosti promítnuté na osy auta.

## Formát CSV {#the-csv-form}

Plugin Trackmanie zapisuje místo toho `heat3d-lap-csv`: první řádek začíná `# `
a pokračuje objektem JSON (`format`, `version`, `game`, `track`, `complete`,
`seconds`, `meta`), pak řádek názvů kanálů a jeden řádek na vzorek. Názvy kanálů
jsou stejné jako výše.

## Co každý nahrávač skutečně zapisuje {#what-each-recorder-actually-writes}

Formát výše je závazný; nahrávače ho vyplňují mírně jinak a čtenář má všechny
tyto varianty zvládnout (ověřeno proti kódu):

| Nahrávač | `track` | `layout` | `meta` | `units` | Kanály nad rámec tabulky |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (číslo trati Forzy Motorsport 2023 je `lap.trackOrdinal`) | zjištěné rozložení paketu | `slip: peak`, `discipline: circuit` | jen jednotky přítomných kanálů | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, herní hodiny `timestampMs`, `raceTime`, `bestLap`, `lastLap`; rychlost v lokálním rámu auta je pod kanonickými názvy `latVel`, `vertVel`, `longVel`; `unparsed` vedle kanálů |
| hry Assetto Corsa (`kunos.py`) | ze statické stránky, nebo `null` | chybí | `slip: scaled`, `discipline: circuit` nebo `rally` | pevný seznam | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (jak přišlo), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| rallye hry (`rally.py` přes `lapfile.py`) | `null` | chybí | `discipline: rally`, `slip: null`, `surface` jen když byl zadán `--surface` (jinak ho odvodí prohlížeč) | jen jednotky přítomných kanálů | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` pro čísla bez ustáleného názvu; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` přes `lapfile.py`) | `null` | chybí | `discipline: circuit` | jen jednotky přítomných kanálů | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| plugin Trackmanie (CSV) | název mapy | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` je blok auta z Forzy (`carOrdinal`, `carClass`, `carPI`, `drivetrain`,
`cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` u her Kunos, když statická
stránka jméno auta uvádí, a jinak `{}`. `lap.metres` je u Forzy rozdíl ujeté
vzdálenosti hlášený hrou, jinde součet trojrozměrné vzdálenosti mezi vzorky.
Hodnoty se při zápisu zaokrouhlují: `time` na 4 desetinná místa, `distance` na 3,
ostatní desetinná čísla na 5. JSON se zapisuje kompaktně (bez mezer).

Každý paket nebo stránka, kterou nahrávač dostal - nejen ty z kol - se zachová
celá vedle souborů kol v `<stamp>_<game>.raw.parquet`, s vlastní kontrolou v
`<stamp>_<game>.summary.json` (sekce „Completeness“ v README).

Vzorek, pro který kanál nemá hodnotu - chybí v daném snímku, nebo hra poslala
něco, co není konečné číslo - každý nahrávač zapíše jako `null` (`lapfile.clean`);
odvozený zlomek odpružení z něj je také `null`. `NaN` a `Infinity` se nikdy
nezapisují: nejsou to JSON a `JSON.parse` v prohlížeči odmítne celý soubor kvůli
jedné takové hodnotě. Čtenář musí počítat s `null` uvnitř pole kanálu.

Soubory Forzy nesou `"game": "forza-horizon"`, `"forza-motorsport"` nebo `"forza"`
podle zjištěného rozložení. Čtečka prohlížeče souborů `.tele.gz` z FH Companion
vytváří kola s `"game": "forza-horizon"` a `meta.slip = "peak"`; tato čtečka je
v prohlížeči, ne tady. Kola iRacingu (čtená z `.ibt` v prohlížeči) nesou
`"game": "iracing"`, což v seznamu hodnot `game` výše není, protože žádný nahrávač
ji nezapisuje.

Jak se rozhoduje o `lap.number`, `lap.seconds` a `lap.complete`, viz
[Rozdělení kol a etap](lap-splitting.md); co prohlížeč z těchto kanálů odvozuje,
viz [Skluz, driftový úhel a odvozené kanály](slip-and-drift.md).
