---
title: "Assetto Corsa leikir"
nav_order: 2
lang: "is"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO og AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kóði: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Prófanir: `tests/test_kunos.py` (gerviblöð). Ekki enn keyrt gegn raunverulegu leikjunum.

## Hvaðan gögnin koma {#where-the-data-comes-from}

Leikir Kunos gefa út mælingagögn fyrir forrit sem **nefnd Windows blöð í sameiginlegu minni** sem
leikurinn skrifar og hver sem er má lesa. Upptökutækið opnar þau skrifvarin (`mmap` með merkisheiti),
svo það verður að keyra **á tölvunni sem leikurinn keyrir á**, á Windows; annars staðar hættir það með skilaboðum.
Blöðin eru opnuð einu sinni, þegar upptökutækið ræsist. Að ræsa leikinn og komast inn í
bílinn fyrst er örugga röðin; hvort það virkar að ræsa upptökutækið á undan leiknum hefur ekki
verið athugað.

| `--game` | Eðlisfræðiblað | Grafíkblað (hringateljari) | Fast blað (heiti) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ekki notað | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ekki notað | `Local\acevo_pmf_static` |

Eðlisfræðiblaðið er lesið 200 sinnum á sekúndu (`hz=200`); nýtt sýni er aðeins tekið þegar
`packetId` þess hefur breyst og er ekki núll. Fyrstu 800 bæti eðlisfræðiblaðsins deila einni
uppsetningu í öllum fjórum leikjunum; blað fyrsta leiksins er aðeins tryggt 580 bæti, svo ef
ekki er hægt að opna 800 bæta vörpun fellur upptökutækið aftur á 580 og reitirnir þar fyrir utan
vantar.

## Staðsetning {#position}

Ekkert blaðanna ber bílstöðu sem slíka, en eðlisfræðiblaðið geymir **snertipunkt hvers dekks í
heimshnitum** (færsla 420, fjórir XYZ þrenndir). Staða bílsins er
meðaltal þeirra fjögurra. Blað þar sem allir snertipunktar eru núll (valmynd, bílskúr) býr ekki til
sýni.

## Rásir {#channels}

| Rás | Úr | Athugasemdir |
|---|---|---|
| `time` | eigin klukka upptökutækisins | sekúndur frá upphafi upptöku, endurreiknað við fyrsta sýni hringsins |
| `x`, `y`, `z` | meðaltal snertipunkta dekkja | heimsmetrar |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | einingar leiksins, skalað á hring í -1..1 með stærsta absólútgildi sem hringurinn notaði, **aðeins ef** það gildi fer yfir 1,05 (inntak sem er þegar í -1..1 er látið vera) |
| `gear` | `gear - 1` | leikurinn telur 0 bakk, 1 hlutlaus, 2 fyrsti; skrifað sem -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, sinnum 9.80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | staðbundinn hraði við færslu 568 | rammi bílsins; aðeins þegar ekki núll. Í hvora átt x vísar er skjalfest á báða vegu, svo lestu stærð rekhornsins, ekki formerki |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | færsla 564 | aðeins 800 bæta blað |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: færslur 204 og 252, skrifað sem 1 þegar yfir 0; AC: `tcInAction`/`absInAction` úr 800 bæta blaðinu þegar það er til | hjálpartæki virk |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | afleitt | 0..1 af slaginu sem þessi hringur notaði (lágmark til hámarks `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | færslur 640, 656 (800 bæta blað) | deilt með dæmigerðu hámarki - sjá hér að neðan |
| `slipRatioRaw.*`, `slipAngleRaw.*` | það sama | eðlisfræðilegu gildin, ósköluð |
| `padLife.*`, `discLife.*` | færslur 740, 756 | aðeins 800 bæta blað |

AC Rally sendir dekkja- og bremsuhita í kelvin: fyrir `--game acrally` er 273,15 dregið frá
hverju þessara gilda sem er yfir 200.

`wheelSlip` (færsla 56) er afkóðað en ekki skrifað.

## Skölun skriðs {#slip-scaling}

Forza sendir skrið stöðlað þannig að 1 er jaðar grips. Kunos sendir eðlisfræðilegt skriðhlutfall
og skriðhorn. Því deilir upptökutækið þeim með dæmigerðu hámarki á malbiki - **0,12** fyrir
skriðhlutfallið og **0,14 rad (um 8 gráður)** fyrir skriðhornið - svo lestur áhorfandans „yfir 1
þýðir rennsli“ haldi nokkurn veginn, geymir hrágildin við hliðina, og skrifar
`"meta": {"slip": "scaled"}`. Hvar grip endar í raun mælir áhorfandinn fyrir hvern bíl út frá
hringjunum. Sjá [Skrið, rek og afleiddar rásir](slip-and-drift.md).

## Hringir {#laps}

- **AC og ACC** telja hringi á grafíkblaðinu (`completedLaps` við færslu 132, tími síðasta
  hrings í millisekúndum við 144). `CounterSplitter` lokar hring þegar teljarinn
  breytist; hann er merktur kláraður, með hringtíma leiksins, aðeins ef teljarinn hækkaði um
  nákvæmlega einn.
- **AC EVO og AC Rally** eru ekki lesin fyrir hringi (grafíkblað EVO er önnur, stærri
  uppsetning; AC Rally ekur leiðir). `LineSplitter` notar punktinn þar sem upptakan hófst sem
  línuna: hringur lokast þegar bíllinn fer næst næst henni í sömu átt, og leið
  eða hvaða ferð sem er lokast þegar bíllinn stendur kyrr í 8 sekúndur.

Nánar og þröskuldar: [Hring- og leiðaskipting](lap-splitting.md).

## Heiti brautar og bíls {#track-and-car-names}

Lesið einu sinni, úr fasta blaðinu, þegar fyrsta sýnið berst: fyrir AC, ACC og AC Rally
bíllinn (UTF-16, færsla 68) og brautin (færsla 134); fyrir AC EVO brautin og uppsetning hennar
(eins bæta texti við færslur 136 og 169, tengt með bili) og enginn bíll. Þau fara inn í
skrána sem `track` og `car: {"name": ...}`.

## Hringskráin {#the-lap-file}

`game` er `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` eða
`assetto-corsa-rally`; `meta` er `{"slip": "scaled", "discipline": "rally"}` fyrir AC Rally og
`{"slip": "scaled", "discipline": "circuit"}` fyrir hina þrjá. Ekkert `surface` er skrifað.

## Heimildir {#sources}

AC1 SDK fyrir sameiginlegt minni; skjölun ACC fyrir sameiginlegt minni (v1.8); uppsetning AC EVO eins og hún var
mæld í `albertowd/live-telemetry-evo`; uppsetning AC Rally eins og
`LuizZak/AssettoCorsaRallyTelemetryReader` les hana. Sjá [Leikir](games.md).
