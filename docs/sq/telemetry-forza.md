---
title: "Forza"
nav_order: 1
lang: "sq"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon dhe Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kodi: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(zbulimi i strukturës),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(çdo kanal, skedarët e xhirove, përcjellja).

## Ndezja në lojë {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, porta `5300` (ose çfarëdo që
jep si `--port`). Forza Motorsport ofron edhe një format paketash: duhet të jetë **Dash**, jo
Sled. Sled nuk mbart aspak pozicion, dhe regjistruesi e refuzon.

Regjistruesi lidhet me `127.0.0.1`, prandaj loja duhet të punojë në të njëjtën PC.

## Çfarë dërgon loja, dhe si gjendet struktura {#what-the-game-sends-and-how-the-layout-is-found}

Data Out është një paketë UDP për çdo tik simulimi (rreth 60 në sekondë), një strukturë C e sheshtë little-endian
në këto madhësi:

| Gjatësia | Varianti |
|---|---|
| 232 bajte | Motorsport "Sled": pa pozicion. Refuzohet me një mesazh që të thotë të kalosh te Dash. |
| 311 bajte | Motorsport "Dash": blloku Sled plus blloku dash 79-bajtësh |
| 324 bajte | Horizon "Dash": e njëjta me mbushje mes dy blloqeve |
| 331 bajte | Forza Motorsport (2023): Dash plus 20 bajte veshjeje gomash dhe ID e pistës |

Blloku Sled (zhvendosjet 0-231) është i qëndrueshëm. Ku fillon blloku dash në variantin Horizon
përshkruhet në mënyrë jokonsistente në burimet e publikuara, dhe hamendja e gabuar nuk dështon - jep
float-e të besueshëm nga fusha të gabuara. Prandaj fillimi **zbulohet**:

1. Fillimet kandidate provohen me radhë: `length - 79` (blloku dash shkon deri në bajtin e fundit
   në çdo variant të dokumentuar), 232, 244, dhe 232 deri 260 me hap 4.
2. Çdo kandidat vlerësohet në paketa nga një makinë në lëvizje (një përbërës shpejtësie mbi
   1 m/s): vektori i shpejtësisë i bllokut Sled dhe `Speed` skalar i bllokut dash janë e njëjta
   madhësi në dy vende, kështu që `| |velocity| - Speed |` është afër zeros vetëm për fillimin e duhur.
3. Fiton kandidati me mospërputhjen më të vogël në rastin më të keq, nëse ajo mospërputhje është më së shumti
   **1 m/s**. Përndryshe zbulimi vazhdon të presë.

Ndërsa makina është e parkuar çdo kandidat lexon zero dhe përputhen, që nuk provon asgjë, prandaj
**zbulimi pret derisa makina të lëvizë**: vozit disa metra para se të presësh dalje. Deri në
600 paketa mbahen gjatë pritjes (të shkurtuara në 300 të fundit). Sapo struktura njihet,
paketat e mbajtura dekodohen gjithashtu, kështu që fillimi i xhiros së parë nuk humbet. Paketat me
gjatësi të ndryshme nga struktura e zbuluar, paketat më të shkurtra se 311 bajte, dhe paketat
me pozicion ose shpejtësi jo të fundme shpërfillen për skedarët e xhirove.

Cila Forza është rrjedh nga struktura: një strukturë Horizon jep `"game": "forza-horizon"`,
një strukturë Motorsport ose 331-bajtëshe jep `"forza-motorsport"`, çdo gjë tjetër `"forza"`. Emri i
strukturës së zbuluar (`Horizon dash`, `Motorsport dash`, `331-byte dash`) shkruhet si
`layout`.

## Kanalet e regjistruara {#channels-recorded}

Çdo fushë e paketës dekodohet (`decode_full`) dhe konvertohet:

- pedalet `throttle`, `brake`, `clutch`, `handbrake` nga 0..255 në 0..1;
- `steer` nga -127..127 në -1..1; `drivingLine` dhe `aiBrakeDifference` po ashtu të pjesëtuara me 127;
- `tireTemp.FL` ... `.RR` nga Farenhajt në Celsius;
- `latAcc`, `longAcc`, `vertAcc` dhe `yawRate` janë kopje të `accelX`, `accelZ`, `accelY` dhe
  `angVelY` me emrat standardë (korniza e makinës: x djathtas, y lart, z përpara);
- shpejtësia Sled, që është në kornizën e vetë makinës (x djathtas, y lart, z përpara - jo ajo e
  botës), shkruhet drejtpërdrejt me emrat standardë `latVel`, `vertVel` dhe `longVel`, kështu që
  shikuesi e lexon këndin e drift-it prej saj dhe nuk e vlerëson nga drejtimi dhe rruga.

Kanalet e skedarit të xhiros janë të gjitha këto përveç fushave për çdo xhiro:

| Grupi | Kanalet |
|---|---|
| Koha dhe vendi | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Lëvizja | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motori | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Shoferi | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Për çdo rrotë (`.FL .FR .RL .RR`) | `suspension` (0 e zgjatur .. 1 e ngjeshur), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizuar: pas 1 goma lëshon), `wheelSpeed` (rad/s), `rumble` (mbi një breg dridhës), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Vetëm Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` është kronometri i xhiros aktuale të lojës minus vlera e tij te kampioni i parë i xhiros; `distance`
është distanca e përshkuar e lojës minus vlera e saj e parë. Pozicionet janë koordinatat botërore të Forza
në metra, të pandryshuara (y është lart; bota është e majtë).

Merren një herë për xhiro dhe jo për kampion, nën `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. ID e pistës së FM2023 hyn gjithashtu një herë, si
`lap.trackOrdinal`. Nuk mbahet për kampion: `isRaceOn` (1 në çdo kuadër të një xhiroje). `timestampMs`,
`raceTime`, `bestLap` dhe `lastLap` mbahen si kanale.

Pjesa tjetër e dokumentit plotësohet si ajo e çdo regjistruesi tjetër:

- `"track": null` - Forza Horizon nuk e emërton pistën, dhe Forza Motorsport vetëm e numëron;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kanalet e rrëshqitjes janë normalizuar që
  pas 1 goma lëshon;
- `units` liston vetëm kanalet që ka skedari (ato për çdo rrotë me emrin e tyre bazë);
- një vlerë që nuk është numër i fundëm shkruhet si `null`, kurrë `NaN`.

Shih [Skedari heat3d-lap](lap-format.md).

## Si ndahen xhirot {#how-laps-are-split}

`LapSplitter` (shih [Ndarja e xhirove dhe e etapave](lap-splitting.md)): një xhiro mbyllet kur
numëruesi i xhirove të lojës ecën përpara, dhe koha e saj është atëherë `lastLap` i vetë lojës (ajo që
tregon loja). Një garë nga pika në pikë ose një seancë që mbaron në mes të xhiros mbyllet kur loja del nga
gara (`isRaceOn` bie), kur paketat ndalojnë për 2 sekonda, ose kur vula kohore e lojës
kërcen mbrapa; mbahet si `run` nëse mbuloi të paktën 400 m.

## Përcjellja te FH Companion {#relaying-to-fh-companion}

Loja dërgon Data Out vetëm në një adresë. Me `--forward host:port`, regjistruesi kalon
**çdo paketë që merr të pandryshuar**, para se të dekodojë ndonjë gjë (edhe ndërsa pret ende të
zbulojë strukturën), kështu që një aplikacion tjetër që lexon rrjedhën vazhdon të punojë: vendose lojën
te 5300, aplikacionin tjetër te 5301, dhe ekzekuto me `--forward 127.0.0.1:5301`.

FH Companion është një aplikacion i veçantë, jo pjesë e 3DHeat. Ai mban një bibliotekë xhirosh nën
`%LOCALAPPDATA%\FHCompanion\laps`: një dosje për çdo pistë, një skedar xhiroje për çdo xhiro të kampionuar afërsisht
çdo pesë metra, dhe pranë çdo skedari xhiroje `<lap>.json.tele.gz`, gjithë Data Out i xhiros me
shpejtësinë e lojës. 3DHeat lexon të dyja:

- **Shikuesi e lexon `.tele.gz` drejtpërdrejt** kur e hedh (me ose pa skedarin e xhiros) në
  skedën "Analiza e garës". Ai harton emrat e vetë fushave të Forza (`PositionX`, `VelocityX`, `TireSlipRatio`
  + rrota, ...) në kanalet standarde, kthen `VelocityX/Y/Z` lokale të makinës në `latVel`,
  `vertVel`, `longVel`, konverton temperaturat e gomave nga Farenhajt, heq rreshtat që përsërisin
  të mëparshmin përveç orës së regjistruesit, dhe e shënon rrëshqitjen si `peak`. Nëse i jepet edhe skedari i xhiros,
  xhiroja merr makinën dhe kohën e xhiros prej andej. Ky lexues jeton në shikues
  (`src/race/adapters.ts`, `readForzaTelemetry`), jo në këtë repo.
- **Komanda `laps`** lexon bibliotekën e xhirove dhe shkruan rrugën e një pistë dhe një CSV të çdo
  kampioni; shih [Referenca e komandave](commands.md#laps).

## Përdorime të tjera të të njëjtës rrjedhë {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` regjistron vetëm pozicionet, të ruajtura çdo disa sekonda
  gjatë vozitjes; shih [Referenca e komandave](commands.md#route).
- Opsioni "Racing telemetry (Forza)" i dritares së skanimit e përdor rrjedhën si poza të sakta kamere
  për rindërtimin; shih [Poza e kamerës dhe shkalla](reconstruction-pose.md#telemetry-poses).

## Shënime dhe kujdes {#notes-and-caveats}

- Ndaj çfarë normalizon Forza rrëshqitjen e saj nuk është e dokumentuar. `1` lexohet si skaji i kapjes,
  por shikuesi mat ku e humbet realisht kapjen çdo makinë.
- Shpejtësia Sled është lokale e makinës, siç thotë dokumentacioni i Data Out të Forza dhe e konfirmojnë xhirot e regjistruara
  (përbërësi i saj përpara mbart shpejtësinë, ai anësor mbetet afër zeros). Zbulimi i strukturës
  përdor vetëm gjatësinë e saj, që është e njëjtë në çdo kornizë.
- Pozicionet janë bota e lojës, me Y lart dhe të majtë. Kuptimet e `yaw`, `pitch` dhe `roll`
  u kontrolluan në xhiro të regjistruara: yaw është i barabartë me drejtimin e udhëtimit `atan2(dx, dz)`, një
  pitch pozitiv është hunda poshtë, dhe një roll pozitiv ul anën e djathtë.
