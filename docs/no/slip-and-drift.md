---
title: "Skli, drift og avledede kanaler"
nav_order: 8
lang: "no"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Skli, drift og avledede kanaler {#slip-drift-and-derived-channels}

Analysen av bilkontroll i viewerens fane Løpsanalyse trenger de samme få størrelsene fra hvert spill: hvor
mye hvert dekk sliper, hvor mye bilen peker bort fra der den er på vei (driftvinkelen), om den er i luften,
og om den er på løst underlag. Spill sender disse i svært ulik form, eller ikke i det hele tatt. Opptakerne her
skriver det hvert spill sender, under kanoniske navn, pluss en `meta.slip`-merknad som sier hva sklitallene
betyr; viewer utleder så det som mangler, en gang, når den laster en runde. **Et spills egen verdi vinner alltid
over en utledet.**

## Hva opptakerne skriver {#what-the-recorders-write}

| Spill | Sklikanaler | `meta.slip` | Driftvinkelens inndata |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` per hjul, slik sendt | `peak` (skrevet av opptakeren; viewerens `.tele.gz`-leser setter det samme) | `latVel`, `longVel` fra bilens lokale fart |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, pluss `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` fra fart i bilens ramme |
| EA SPORTS WRC, DiRT-spillene | ingen; `wheelSurfaceSpeed` per hjul i stedet | `null` | `latVel`, `longVel` = verdenshastigheten projisert på bilens akser |
| Richard Burns Rally | ingen; heller ingen hjulfart | ingen | `latVel`, `longVel` = bilens egen sving og surge |
| BeamNG.drive | ingen; `wheelSurfaceSpeed` og `wheelSpeed` per hjul | ingen | `latVel`, `longVel` = verdenshastigheten projisert på bilens akser |
| Trackmania | `slipIndex` per hjul (et 0..1 glidemål) | `index` | `latVel` (sidefart), `longVel` (fremfart) |
| iRacing | ingen (ikke logget) | ingen | `yaw` og banen, `yawRate` |

`meta.slip`-verdiene er definert i [`heat3d-lap`-filen](lap-format.md): `peak`
(normalisert, så over 1 gir dekket slipp), `scaled` (en fysisk sklí delt på en typisk asfalttopp),
`physical` (en brøkdel og radianer), `index` (et 0..1 glidemål).

### Hvorfor Kunos-sklien er skalert {#why-kunos-slip-is-scaled}

Forzas sklí er normalisert slik at 1 er grensen for grep, og hva den normaliseres mot er ikke dokumentert.
Kunos sender den fysiske sklíforholdet (en brøkdel) og sklívinkelen (radianer). Ved å dele på en typisk
asfalttopp - 0,12 for forholdet, 0,14 rad (omtrent 8 grader) for vinkelen - blir "over 1 betyr at den sliper"
omtrent sant for begge familiene, og det gir én lesing for viewerens skjermbilder. Det er en tilnærming: reelle
topper varierer etter dekk og underlag, og det er grunnen til at de rå verdiene beholdes ved siden av de skalerte, og
hvorfor viewer måler hvor hver bils grep faktisk avtar ut fra rundene selv.

## Hva viewer utleder (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Disse kjøres i viewer (`src/race/derive.ts` i 3DHeat-viewer), ikke i dette depotet.

### Driftvinkel, `bodySlip` {#drift-angle-bodyslip}

- **Fra fart i bilens ramme** når `latVel` og `longVel` finnes: `atan2(latVel, |longVel|)`, og 0 under 3 m/s
  (en bil som står stille på tvers er ikke i drift). Fortegnet følger spillets sidefart, hvis retning er dokumentert
  begge veier for noen spill - les størrelsen.
- **Ellers fra kursen mot banen**: kjøreretningen tas fra posisjoner omtrent 2 m på hver side av hver prøve
  (`atan2(dx, dz)`); spillets `yaw` tilpasses den med et fortegn og en forskyvning (hvert spill har sin egen nullpunkt og
  rotasjonsretning) ved hjelp av prøver over 10 m/s, og stoles bare på hvis den deretter stemmer godt
  (sirkulær spredning høyst 0,05, minst 20 prøver). Driftvinkelen er differansen, 0 under 3 m/s.

### Sklíforhold fra hjulene {#slip-ratio-from-the-wheels}

Der en runde ikke har `slipRatio.*` men har hjulhastigheter, er sklíforholdet
`(hjul - bil) / bil` per hjul, fra:

- `wheelSurfaceSpeed.*` (kontaktflatens fart, m/s) direkte, når den sendes (EA WRC, DiRT, BeamNG);
- ellers `wheelSpeed.*` (rotasjon, rad/s) ganget med en **rulleradius målt på runden**: medianen av `speed / |omega|`
  over prøver der bilen ruller rett fram (over 10 m/s, ikke i luften, gass under 0,3, brems under 0,05, lengdeakselerasjon under
  3 m/s²); med færre enn 20 slike prøver, hver prøve over 10 m/s. En radius utenfor 0,1-1 m forkastes.

Bare når alle fire hjulene kan utledes; rundens `meta.slip` blir da `physical`. Under 3 m/s er sklien 0.

### I luften {#airborne}

`airborne` er 1 der hvert hjul er av bakken, bedømt etter den første av disse runden har for alle fire hjulene:

1. `groundContact.*` (BeamNG): ingen hjul over 0,5;
2. `wheelLoad.*` (AC-spillene, RBR, BeamNG): ingen hjul over 5 % av sin egen mediane last;
3. `suspension.*` (0..1 av utslaget): ingen hjul over 0,02, altså alle helt utstrakte.

En enkelt isolert luftprøve fjernes. Trackmania skriver `airborne` selv.

### Løst underlag {#loose-ground}

Der en runde har `surfaceRumble.*` (Forza), er `loose` 1 der minst to hjul melder rumling i minst en tredjedels
sekund, med gap kortere enn ett sekund overbygget (en jevn flekk på en grusvei er fortsatt grusveien). Trackmania
skriver `loose` selv, fra hjulenes underlagsmaterialer.

### Gir-rate {#yaw-rate}

Der en runde har `yaw` men ikke `yawRate`, er den endringen i yaw over de nærliggende prøvene.

## Hva opptakerne selv utleder {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): hver opptaker unntatt Forza (som sender den) skriver den fra `suspensionM.*` som posisjonen
  innenfor området denne runden brukte (minimum til maksimum). Den er til bilens fjæringsstenger og for å se et hjul som henger
  i luften; den er ikke en absolutt utslagsbrøk.
- **`steer`** for Kunos-spillene, skalert per runde (se [Assetto Corsa-spill](telemetry-assetto-corsa.md)).
- **Akselerasjoner** for BeamNG, fra endringen i verdenshastighet ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** og opp-aksen for Richard Burns Rally, fra posisjonene ([Rallyspill](telemetry-rally.md)).

## Håndsystem {#handedness}

Der et spills verden er venstrehåndet - Forzas er det - kommer en bane speilvendt ut i en høyrehåndet viewer;
rundenes egen styring og fjæring viser det. Opptakerne endrer ikke håndsystemet: en Z-opp-verden (BeamNG) vris
til Y-opp med en rotasjon, som beholder den, og alt annet skrives slik det sendes.
