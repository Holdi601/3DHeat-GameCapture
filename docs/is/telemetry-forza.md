---
title: "Forza"
nav_order: 1
lang: "is"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon og Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kóði: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(uppsetningargreining),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(allar rásir, hringskrár, áframsending).

## Að kveikja á því í leiknum {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, gátt `5300` (eða það sem
þú gefur sem `--port`). Forza Motorsport býður líka upp á pakkasnið: það verður að vera **Dash**, ekki
Sled. Sled ber enga staðsetningu og upptökutækið hafnar því.

Upptökutækið tengist `127.0.0.1`, svo leikurinn verður að keyra á sömu tölvu.

## Hvað leikurinn sendir og hvernig uppsetningin er fundin {#what-the-game-sends-and-how-the-layout-is-found}

Data Out er einn UDP pakki á hvert hermitikk (um 60 á sekúndu), flatt little-endian C
struct í þessum stærðum:

| Lengd | Afbrigði |
|---|---|
| 232 bæti | Motorsport „Sled“: engin staðsetning. Hafnað með skilaboðum sem segja þér að skipta í Dash. |
| 311 bæti | Motorsport „Dash“: Sled blokk plús 79 bæta dash blokk |
| 324 bæti | Horizon „Dash“: það sama með fyllingu milli blokkanna tveggja |
| 331 bæti | Forza Motorsport (2023): Dash plús 20 bæti af dekkjasliti og brautarauðkenni |

Sled blokkin (færslur 0-231) er stöðug. Hvar dash blokkin byrjar í Horizon afbrigðinu
er lýst ósamræmt í útgefnum heimildum, og að giska rangt bregst ekki - það
gefur sennilegar fleytitölur úr röngum reitum. Því er byrjunin **uppgötvuð**:

1. Prófaðar eru mögulegar byrjanir í röð: `length - 79` (dash blokkin nær að síðasta
   bæti í öllum skjalfestum afbrigðum), 232, 244, og 232 til 260 í skrefum um 4.
2. Hver möguleiki er metinn á pökkum frá bíl á hreyfingu (hraðaþáttur yfir
   1 m/s): hraðavigur Sled blokkarinnar og kvarðinn `Speed` í dash blokkinni eru sama
   stærð á tveimur stöðum, svo `| |velocity| - Speed |` er nálægt núlli aðeins fyrir rétta byrjun.
3. Sá möguleiki með minnsta versta ósamræmið vinnur, ef það ósamræmi er í mesta
   lagi **1 m/s**. Annars heldur greining áfram að bíða.

Meðan bíllinn er kyrr les hver möguleiki núll og þeir eru sammála, sem sannar ekkert, svo
**greining bíður þar til bíllinn hreyfist**: aktu nokkra metra áður en þú býst við úttaki. Allt að
600 pakkar eru geymdir á meðan beðið er (klipptir í nýjustu 300). Þegar uppsetningin er þekkt
eru geymdu pakkarnir líka afkóðaðir, svo byrjun fyrsta hringsins tapast ekki. Pakkar af
annarri lengd en greind uppsetning, pakkar styttri en 311 bæti, og pakkar
með óendanlega eða ótiltæka staðsetningu eða hraða eru hunsaðir fyrir hringskrárnar.

Hvaða Forza það er leiðir af uppsetningunni: Horizon uppsetning gefur `"game": "forza-horizon"`,
Motorsport eða 331 bæta uppsetning gefur `"forza-motorsport"`, annað `"forza"`. Heiti
greindrar uppsetningar (`Horizon dash`, `Motorsport dash`, `331-byte dash`) er skrifað sem
`layout`.

## Rásir sem eru skráðar {#channels-recorded}

Hver reitur pakkans er afkóðaður (`decode_full`) og umbreyttur:

- pedalar `throttle`, `brake`, `clutch`, `handbrake` úr 0..255 í 0..1;
- `steer` úr -127..127 í -1..1; `drivingLine` og `aiBrakeDifference` eins deilt með 127;
- `tireTemp.FL` ... `.RR` úr Fahrenheit í Celsíus;
- `latAcc`, `longAcc`, `vertAcc` og `yawRate` eru afrit af `accelX`, `accelZ`, `accelY` og
  `angVelY` undir föstum heitum (rammi bílsins: x hægri, y upp, z áfram);
- Sled hraðinn, sem er í eigin ramma bílsins (x hægri, y upp, z áfram - ekki
  heimsins), er skrifaður beint undir föstu heitin `latVel`, `vertVel` og `longVel`, svo
  áhorfandinn lesi rekhornið af honum í stað þess að áætla það út frá stefnu og ferli.

Rásir hringskrárinnar eru allar þessar nema reitirnir fyrir hvern hring:

| Hópur | Rásir |
|---|---|
| Tími og staður | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Hreyfing | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Vél | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Ökumaður | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Á hvert hjól (`.FL .FR .RL .RR`) | `suspension` (0 útdregið .. 1 þjappað), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (stöðlað: yfir 1 sleppir dekkið gripinu), `wheelSpeed` (rad/s), `rumble` (á skröltrönd), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Aðeins Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` er núverandi hringtímamælir leiksins mínus gildi hans við fyrsta sýni hringsins; `distance`
er ekin vegalengd leiksins mínus fyrsta gildi hennar. Staðsetningar eru heimshnit Forza
í metrum, óbreytt (y er upp; heimurinn er örvhentur).

Tekið einu sinni á hring en ekki á sýni, undir `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Brautarauðkenni FM2023 fer líka inn einu sinni, sem
`lap.trackOrdinal`. Ekki geymt á sýni: `isRaceOn` (1 í hverjum ramma hrings). `timestampMs`,
`raceTime`, `bestLap` og `lastLap` eru geymd sem rásir.

Restin af skjalinu er fyllt eins og hjá hverju öðru upptökutæki:

- `"track": null` - Forza Horizon nefnir ekki brautina, og Forza Motorsport númerar hana aðeins;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - skriðrásirnar eru stöðlaðar þannig að
  yfir 1 sleppir dekkið gripinu;
- `units` telur aðeins upp rásirnar sem skráin hefur (rásir á hvert hjól eftir grunnheiti);
- gildi sem er ekki endanleg tala er skrifað sem `null`, aldrei `NaN`.

Sjá [heat3d-lap skrána](lap-format.md).

## Hvernig hringjum er skipt {#how-laps-are-split}

`LapSplitter` (sjá [Hring- og leiðaskipting](lap-splitting.md)): hringur lokast þegar
hringateljari leiksins færist áfram, og tími hans er þá eigið `lastLap` leiksins (það sem leikurinn
sýnir). Keppni frá punkti til punkts eða lota sem endar í miðjum hring lokast þegar leikurinn yfirgefur
keppnina (`isRaceOn` fellur), þegar pakkarnir stöðvast í 2 sekúndur, eða þegar tímastimpill leiksins
stekkur afturábak; hún er geymd sem `run` ef hún náði yfir að minnsta kosti 400 m.

## Áframsending til FH Companion {#relaying-to-fh-companion}

Leikurinn sendir Data Out á eitt heimilisfang aðeins. Með `--forward host:port` sendir upptökutækið
**hvern pakka sem það tekur á móti áfram óbreyttan**, áður en það afkóðar nokkuð (líka meðan það bíður
enn eftir að greina uppsetninguna), svo annað forrit sem les strauminn heldur áfram að virka: stilltu leikinn
á 5300, hitt forritið á 5301, og keyrðu með `--forward 127.0.0.1:5301`.

FH Companion er sérstakt forrit, ekki hluti af 3DHeat. Það heldur hringasafn undir
`%LOCALAPPDATA%\FHCompanion\laps`: mappa fyrir hverja braut, ein hringskrá á hring sýnatekin um það bil á
fimm metra fresti, og við hlið hverrar hringskrár `<lap>.json.tele.gz`, allt Data Out hringsins á
tíðni leiksins. 3DHeat les bæði:

- **Áhorfandinn les `.tele.gz` beint** þegar þú sleppir henni (með eða án hringskrárinnar) á
  flipann Kappakstursgreining. Hann varpar eigin reitaheitum Forza (`PositionX`, `VelocityX`, `TireSlipRatio`
  + hjól, ...) á föstu rásirnar, breytir staðbundnu `VelocityX/Y/Z` bílsins í `latVel`,
  `vertVel`, `longVel`, umbreytir dekkjahita úr Fahrenheit, fellir niður raðir sem endurtaka
  fyrri röð nema fyrir klukku upptökutækisins, og merkir skriðið sem `peak`. Ef hringskráin er
  gefin líka tekur hringurinn bílinn sinn og hringtíma þaðan. Þessi lesari er í áhorfandanum
  (`src/race/adapters.ts`, `readForzaTelemetry`), ekki í þessari geymslu.
- **`laps` skipunin** les hringasafnið og skrifar leið brautar og CSV af hverju
  sýni; sjá [Skipanayfirlit](commands.md#laps).

## Önnur notkun á sama straumi {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` skráir aðeins staðsetningarnar, vistaðar á nokkurra sekúndna fresti
  meðan ekið er; sjá [Skipanayfirlit](commands.md#route).
- Valkosturinn „Racing telemetry (Forza)“ í skannglugganum notar strauminn sem nákvæmar myndavélarstöður
  fyrir endurgerð; sjá [Staða myndavélar og kvarði](reconstruction-pose.md#telemetry-poses).

## Athugasemdir og fyrirvarar {#notes-and-caveats}

- Við hvað Forza stillir skrið sitt er ekki skjalfest. `1` er lesið sem jaðar grips,
  en áhorfandinn mælir hvar grip hvers bíls fer í raun að minnka.
- Sled hraðinn er staðbundinn í bílnum, eins og Data Out skjölun Forza segir og upptökuhringir
  staðfesta (framþáttur hans ber hraðann, hliðarþátturinn er nálægt núlli). Uppsetningargreining
  notar aðeins lengd hans, sem er sú sama í hvaða ramma sem er.
- Staðsetningar eru heimur leiksins, Y upp og örvhentur. Merkingar `yaw`, `pitch` og `roll`
  voru athugaðar á upptökuhringjum: yaw er jafnt ferðastefnunni `atan2(dx, dz)`, jákvætt
  pitch er nef niður, og jákvætt roll lækkar hægri hliðina.
