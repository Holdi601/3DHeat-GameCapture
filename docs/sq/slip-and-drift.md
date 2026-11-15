---
title: "Rrëshqitja, drift-i dhe kanalet e nxjerra"
nav_order: 8
lang: "sq"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Rrëshqitja, drift-i dhe kanalet e nxjerra {#slip-drift-and-derived-channels}

Analiza e kontrollit të makinës në skedën "Analiza e garës" të shikuesit do të njëjtat disa madhësi nga çdo
lojë: sa rrëshqet çdo gomë, sa e largon makina hundën nga ku po shkon (këndi i drift-it),
nëse është në ajër, nëse është në tokë të lirshme. Lojërat i dërgojnë këto në forma shumë
të ndryshme, ose aspak. Regjistruesit këtu shkruajnë atë që dërgon çdo lojë, me emra
standardë, plus një shënim `meta.slip` që tregon çfarë nënkuptojnë numrat e rrëshqitjes; shikuesi pastaj
nxjerr atë që mungon, një herë, kur ngarkon një xhiro. **Vlera e vetë lojës fiton gjithmonë ndaj një
vlere të nxjerrë.**

## Çfarë shkruajnë regjistruesit {#what-the-recorders-write}

| Loja | Kanalet e rrëshqitjes | `meta.slip` | Hyrjet e këndit të drift-it |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` për çdo rrotë, siç dërgohen | `peak` (shkruar nga regjistruesi; lexuesi `.tele.gz` i shikuesit vendos të njëjtën) | `latVel`, `longVel` nga shpejtësia lokale e makinës |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0.12, `slipAngle` / 0.14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` nga shpejtësia në kornizën e makinës |
| EA SPORTS WRC, lojërat DiRT | asnjë; në vend të tyre `wheelSurfaceSpeed` për çdo rrotë | `null` | `latVel`, `longVel` = shpejtësia botërore e projektuar mbi akset e makinës |
| Richard Burns Rally | asnjë; as shpejtësi rrotash | asnjë | `latVel`, `longVel` = lëkundja dhe përpara-prapa e vetë makinës |
| BeamNG.drive | asnjë; `wheelSurfaceSpeed` dhe `wheelSpeed` për çdo rrotë | asnjë | `latVel`, `longVel` = shpejtësia botërore e projektuar mbi akset e makinës |
| Trackmania | `slipIndex` për çdo rrotë (një masë rrëshqitjeje 0..1) | `index` | `latVel` (shpejtësia anësore), `longVel` (shpejtësia përpara) |
| iRacing | asnjë (nuk regjistrohet) | asnjë | `yaw` dhe rruga, `yawRate` |

Vlerat e `meta.slip` përcaktohen te [Skedari heat3d-lap](lap-format.md): `peak`
(normalizuar që pas 1 goma lëshon), `scaled` (një rrëshqitje fizike e pjesëtuar me një maksimum tipik në
asfalt), `physical` (një thyesë dhe radianë), `index` (një masë rrëshqitjeje 0..1).

### Pse rrëshqitja Kunos shkallëzohet {#why-kunos-slip-is-scaled}

Rrëshqitja e Forza është normalizuar që 1 të jetë skaji i kapjes; ndaj çfarë normalizohet nuk është
e dokumentuar. Kunos dërgon raportin fizik të rrëshqitjes (një thyesë) dhe këndin e rrëshqitjes (radianë). Pjesëtimi
me një maksimum tipik në asfalt - 0.12 për raportin, 0.14 rad (rreth 8 gradë) për këndin -
e bën "pas 1 do të thotë rrëshqet" përafërsisht të vërtetë për të dyja familjet, gjë që mban një lexim të vetëm
për shfaqjet e shikuesit. Është një përafrim: maksimumet reale ndryshojnë sipas gomës dhe sipërfaqes, prandaj
vlerat e papërpunuara mbahen pranë atyre të shkallëzuara dhe prandaj shikuesi mat ku e humbet realisht kapjen
çdo makinë nga vetë xhirot.

## Çfarë nxjerr shikuesi (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Këto ekzekutohen në shikues (`src/race/derive.ts` në shikuesin 3DHeat), jo në këtë repo.

### Këndi i drift-it, `bodySlip` {#drift-angle-bodyslip}

- **Nga shpejtësia në kornizën e makinës** kur `latVel` dhe `longVel` janë të pranishëm:
  `atan2(latVel, |longVel|)`, dhe 0 nën 3 m/s (një makinë e ndalur anash nuk po bën drift).
  Shenja e tij ndjek shpejtësinë anësore të lojës, kuptimi i së cilës dokumentohet në të dyja mënyrat për disa
  lojëra - lexo madhësinë.
- **Përndryshe nga drejtimi krahasuar me rrugën**: drejtimi i udhëtimit merret nga
  pozicionet rreth 2 m në të dyja anët e çdo kampioni (`atan2(dx, dz)`); `yaw` i lojës
  përshtatet me të me një shenjë dhe një zhvendosje (çdo lojë ka zeron dhe kuptimin e vet të rrotullimit) duke përdorur
  kampionë mbi 10 m/s, dhe besohet vetëm nëse pastaj përputhet ngushtë (përhapja rrethore më së shumti
  0.05, të paktën 20 kampionë). Këndi i drift-it është diferenca, 0 nën 3 m/s.

### Raporti i rrëshqitjes nga rrotat {#slip-ratio-from-the-wheels}

Aty ku një xhiro nuk ka `slipRatio.*` por ka shpejtësi rrotash, raporti i rrëshqitjes është
`(wheel - car) / car` për çdo rrotë, nga:

- `wheelSurfaceSpeed.*` (shpejtësia e njollës së kontaktit, m/s) drejtpërdrejt, kur dërgohet (EA WRC, DiRT,
  BeamNG);
- përndryshe `wheelSpeed.*` (rrotullimi, rad/s) herë një **rreze rrotullimi e matur në xhiro**:
  mediana e `speed / |omega|` mbi kampionët ku makina lëviz me inerci në vijë të drejtë (mbi
  10 m/s, jo në ajër, gazi nën 0.3, frena nën 0.05, nxitimi gjatësor nën
  3 m/s²); me më pak se 20 kampionë të tillë, çdo kampion mbi 10 m/s. Një rreze jashtë
  0.1-1 m refuzohet.

Vetëm kur mund të nxirren të katër rrotat; `meta.slip` e xhiros bëhet atëherë `physical`. Nën
3 m/s rrëshqitja është 0.

### Në ajër {#airborne}

`airborne` është 1 aty ku çdo rrotë është larg tokës, e gjykuar nga i pari prej këtyre që xhiroja ka
për të katër rrotat:

1. `groundContact.*` (BeamNG): asnjë rrotë mbi 0.5;
2. `wheelLoad.*` (lojërat AC, RBR, BeamNG): asnjë rrotë mbi 5% të ngarkesës së vet mediane;
3. `suspension.*` (0..1 e udhëtimit): asnjë rrotë mbi 0.02, pra të gjitha plotësisht të zgjatura.

Një kampion i vetëm i izoluar në ajër pastrohet. Trackmania e shkruan vetë `airborne`.

### Toka e lirshme {#loose-ground}

Aty ku një xhiro ka `surfaceRumble.*` (Forza), `loose` është 1 aty ku të paktën dy rrota raportojnë
dridhje për të paktën një të tretën e sekondës, me hendeqe më të shkurtra se një sekondë të mbyllura (një
copë e lëmuar në një rrugë zhavorri është prapë rruga e zhavorrit). Trackmania e shkruan vetë `loose` nga
materialet e tokës së rrotave.

### Shpejtësia e rrotullimit (yaw rate) {#yaw-rate}

Aty ku një xhiro ka `yaw` por jo `yawRate`, ajo është ndryshimi i yaw mbi kampionët fqinjë.

## Çfarë nxjerrin vetë regjistruesit {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): çdo regjistrues përveç Forza (që e dërgon) e shkruan nga
  `suspensionM.*` si pozicioni brenda intervalit që përdori kjo xhiro (minimum deri maksimum). Është
  për shiritat e pezullimit të makinës dhe për të dalluar një rrotë që varet në ajër; nuk është një
  pjesë absolute e udhëtimit.
- **`steer`** për lojërat Kunos, shkallëzuar për çdo xhiro (shih
  [Lojërat Assetto Corsa](telemetry-assetto-corsa.md)).
- **Nxitimet** për BeamNG, nga ndryshimi i shpejtësisë botërore
  ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** dhe aksi lart për Richard Burns Rally, nga pozicionet
  ([Lojërat e ralit](telemetry-rally.md)).

## Orientimi i botës (handedness) {#handedness}

Aty ku bota e një loje është e majtë - ajo e Forza është - një pistë del e pasqyruar në një
shikues me sistem të djathtë; drejtimi dhe pezullimi i vetë xhirove e zbulojnë këtë. Regjistruesit nuk
e ndryshojnë orientimin: një botë me Z lart (BeamNG) kthehet në Y lart me një rrotullim, që e ruan,
dhe çdo gjë tjetër shkruhet siç dërgohet.
