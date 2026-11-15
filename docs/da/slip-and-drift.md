---
title: "Slip, drift og afledte kanaler"
nav_order: 8
lang: "da"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Slip, drift og afledte kanaler {#slip-drift-and-derived-channels}

Analysen af bilkontrol i viewer'ens fane Løbsanalyse har brug for de samme få størrelser fra hvert spil: hvor meget hvert dæk glider, hvor meget bilen peger væk fra der, hvor den er på vej hen (driftvinklen), om den er i luften, og om den er på løst underlag. Spil sender disse i meget forskellige former, eller slet ikke. Optagerne her skriver det, hvert spil sender, under kanoniske navne, plus en `meta.slip`-note, der siger, hvad slip-tallene betyder; viewer'en udleder så det, der mangler, én gang, når den indlæser en omgang. **Et spils egen værdi vinder altid over en udledt.**

## Hvad optagerne skriver {#what-the-recorders-write}

| Spil | Slip-kanaler | `meta.slip` | Input til driftvinklen |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` pr. hjul, som sendt | `peak` (skrevet af optageren; viewer'ens læser af `.tele.gz` sætter det samme) | `latVel`, `longVel` fra den bilbårne hastighed |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` fra hastigheden i bilens ramme |
| EA SPORTS WRC, DiRT-spillene | ingen; i stedet `wheelSurfaceSpeed` pr. hjul | `null` | `latVel`, `longVel` = verdenshastigheden projiceret på bilens akser |
| Richard Burns Rally | ingen; heller ingen hjulhastigheder | ingen | `latVel`, `longVel` = bilens egen sidebevægelse og fremdrift |
| BeamNG.drive | ingen; `wheelSurfaceSpeed` og `wheelSpeed` pr. hjul | ingen | `latVel`, `longVel` = verdenshastigheden projiceret på bilens akser |
| Trackmania | `slipIndex` pr. hjul (et glidemål fra 0..1) | `index` | `latVel` (sidehastighed), `longVel` (fronthastighed) |
| iRacing | ingen (ikke logget) | ingen | `yaw` og stien, `yawRate` |

Værdierne for `meta.slip` er defineret i [Filen `heat3d-lap`](lap-format.md): `peak` (normaliseret, så over 1 slipper dækket), `scaled` (et fysisk slip divideret med en typisk asfalttop), `physical` (en brøk og radianer), `index` (et glidemål fra 0..1).

### Hvorfor Kunos' slip skaleres {#why-kunos-slip-is-scaled}

Forzas slip er normaliseret, så 1 er grænsen for greb, og hvad det normaliseres med, er ikke dokumenteret. Kunos sender det fysiske slip-forhold (en brøk) og slip-vinklen (radianer). Ved at dividere med en typisk asfalttop - 0,12 for slip-forholdet og 0,14 rad (cirka 8 grader) for vinklen - bliver "over 1 betyder glidning" cirka sandt for begge familier, hvilket holder én læsning for viewer'ens visninger. Det er en tilnærmelse: reelle toppe varierer efter dæk og underlag, og det er grunden til, at de rå værdier gemmes ved siden af de skalerede, og til at viewer'en måler, hvor hver bils greb reelt bliver mindre, ud fra selve omgangene.

## Hvad viewer'en udleder (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Disse kører i viewer'en (`src/race/derive.ts` i 3DHeat-viewer'en), ikke i dette repository.

### Driftvinkel, `bodySlip` {#drift-angle-bodyslip}

- **Ud fra hastigheden i bilens ramme**, når `latVel` og `longVel` findes: `atan2(latVel, |longVel|)`, og 0 under 3 m/s (en bil, der står stille på tværs, driver ikke).
  Fortegnet følger spillets sidelæns hastighed, hvis retning for nogle spil er dokumenteret begge veje - læs størrelsen.
- **Ellers ud fra retningen mod stien**: kørselsretningen tages fra positioner cirka 2 m til hver side af hver prøve (`atan2(dx, dz)`); spillets `yaw` tilpasses den med et fortegn og en forskydning (hvert spil har sit eget nulpunkt og sin egen omdrejningsretning) ved hjælp af prøver over 10 m/s, og den stoles kun på, hvis den derefter stemmer nøje (cirkulær spredning højst 0,05, mindst 20 prøver). Driftvinklen er forskellen, 0 under 3 m/s.

### Slip-forhold ud fra hjulene {#slip-ratio-from-the-wheels}

Hvor en omgang ikke har `slipRatio.*`, men har hjulhastigheder, er slip-forholdet `(hjul - bil) / bil` pr. hjul, ud fra:

- `wheelSurfaceSpeed.*` (kontaktfladens hastighed, m/s) direkte, når den sendes (EA WRC, DiRT, BeamNG);
- ellers `wheelSpeed.*` (rotation, rad/s) gange en **rulleradius målt på omgangen**: medianen af `speed / |omega|` over prøver, hvor bilen ruller ud i en lige linje (over 10 m/s, ikke i luften, gashåndtag under 0,3, bremse under 0,05, længdeacceleration under 3 m/s²); med færre end 20 sådanne prøver, hver prøve over 10 m/s. En radius uden for 0,1-1 m afvises.

Kun når alle fire hjul kan udledes, og omgangens `meta.slip` bliver da `physical`. Under 3 m/s er slip 0.

### I luften {#airborne}

`airborne` er 1, hvor alle hjul er fri af jorden, bedømt ud fra den første af disse, omgangen har for alle fire hjul:

1. `groundContact.*` (BeamNG): ingen hjul over 0,5;
2. `wheelLoad.*` (AC-spillene, RBR, BeamNG): ingen hjul over 5 % af sin egen medianbelastning;
3. `suspension.*` (0..1 af vejen): ingen hjul over 0,02, altså alle helt udstrakte.

En enkelt isoleret prøve i luften ryddes. Trackmania skriver selv `airborne`.

### Løst underlag {#loose-ground}

Hvor en omgang har `surfaceRumble.*` (Forza), er `loose` 1, hvor mindst to hjul melder rumling i mindst en tredjedel sekund, med huller kortere end et sekund overbygget (et jævnt stykke på en grusvej er stadig grusvejen). Trackmania skriver selv `loose` ud fra hjulenes underlagsmaterialer.

### Giringshastighed {#yaw-rate}

Hvor en omgang har `yaw`, men ikke `yawRate`, er den ændringen i yaw over de nabostående prøver.

## Hvad optagerne selv udleder {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): alle optagere undtagen Forza (som sender den) skriver den ud fra `suspensionM.*` som positionen inden for det interval, omgangen brugte (mindste til største). Den er til bilens affjedringsstænger og til at se et hjul, der hænger i luften; den er ikke en absolut fjederbrøk.
- **`steer`** for Kunos-spillene, skaleret pr. omgang (se [Assetto Corsa-spillene](telemetry-assetto-corsa.md)).
- **Accelerationer** for BeamNG, ud fra ændringen i verdenshastigheden ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** og opadretningen for Richard Burns Rally, ud fra positionerne ([Rallyspil](telemetry-rally.md)).

## Håndethed {#handedness}

Hvor et spils verden er venstrehåndet - Forzas er det - kommer en bane spejlvendt ud i en højrehåndet viewer; omgangenes egen styring og affjedring afslører det. Optagerne ændrer ikke håndethed: en Z-op-verden (BeamNG) drejes til Y-op med en rotation, som bevarer den, og alt andet skrives som sendt.
