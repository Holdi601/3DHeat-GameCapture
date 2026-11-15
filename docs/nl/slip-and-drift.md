---
title: "Slip, drifthoek en afgeleide kanalen"
nav_order: 8
lang: "nl"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Slip, drifthoek en afgeleide kanalen {#slip-drift-and-derived-channels}

De autocontrole-analyse in het tabblad Race-analyse van de viewer wil van elk spel dezelfde paar grootheden: hoeveel elke band slipt, hoe ver de auto wegwijst van waar hij heen gaat (de drifthoek), of hij in de lucht is, of hij op losse ondergrond rijdt. Spellen sturen die in heel verschillende vormen, of helemaal niet. De opnemers hier schrijven wat elk spel stuurt, onder kanonieke namen, plus een `meta.slip`-notitie die zegt wat de slipgetallen betekenen; de viewer leidt daarna af wat ontbreekt, één keer, wanneer hij een ronde laadt. **De eigen waarde van een spel wint altijd van een afgeleide.**

## Wat de opnemers schrijven {#what-the-recorders-write}

| Spel | Slipkanalen | `meta.slip` | Invoer voor de drifthoek |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` per wiel, zoals verstuurd | `peak` (geschreven door de opnemer; de `.tele.gz`-lezer van de viewer zet hetzelfde) | `latVel`, `longVel` uit de snelheid in het autoframe |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` uit de snelheid in het autoframe |
| EA SPORTS WRC, DiRT-spellen | geen; in plaats daarvan `wheelSurfaceSpeed` per wiel | `null` | `latVel`, `longVel` = wereldsnelheid geprojecteerd op de assen van de auto |
| Richard Burns Rally | geen; ook geen wielsnelheden | geen | `latVel`, `longVel` = de eigen slinger- en voortstuwingssnelheid van de auto |
| BeamNG.drive | geen; `wheelSurfaceSpeed` en `wheelSpeed` per wiel | geen | `latVel`, `longVel` = wereldsnelheid geprojecteerd op de assen van de auto |
| Trackmania | `slipIndex` per wiel (een 0..1-maat voor slippen) | `index` | `latVel` (zijsnelheid), `longVel` (voorsnelheid) |
| iRacing | geen (niet gelogd) | geen | `yaw` en het pad, `yawRate` |

De waarden van `meta.slip` zijn beschreven in [Het `heat3d-lap`-bestand](lap-format.md): `peak` (genormaliseerd, dus boven 1 laat de band los), `scaled` (een fysieke slip gedeeld door een typische piek voor asfalt), `physical` (een fractie en radialen), `index` (een 0..1-maat voor slippen).

### Waarom Kunos-slip wordt geschaald {#why-kunos-slip-is-scaled}

De slip van Forza is genormaliseerd zodat 1 de rand van de grip is; waar het op normaliseert, is niet gedocumenteerd. Kunos stuurt de fysieke slip-ratio (een fractie) en slip-hoek (radialen). Delen door een typische piek voor asfalt - 0,12 voor de slip-ratio en 0,14 rad (ongeveer 8 graden) voor de slip-hoek - maakt "boven 1 betekent slippen" ongeveer waar voor beide families, wat één lezing houdt voor de weergaven van de viewer. Het is een benadering: echte pieken verschillen per band en ondergrond, en daarom worden de ruwe waarden naast de geschaalde bewaard, en meet de viewer uit de ronden zelf waar de grip van elke auto echt wegvalt.

## Wat de viewer afleidt (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Deze draaien in de viewer (`src/race/derive.ts` in de 3DHeat-viewer), niet in deze repository.

### Drifthoek, `bodySlip` {#drift-angle-bodyslip}

- **Uit de snelheid in het autoframe** als `latVel` en `longVel` aanwezig zijn: `atan2(latVel, |longVel|)`, en 0 onder 3 m/s (een auto die zijwaarts stilstaat drift niet).
  Het teken volgt de zijsnelheid van het spel, waarvan de richting voor sommige spellen in beide richtingen is gedocumenteerd - lees de grootte.
- **Anders uit de koers tegen het pad**: de rijrichting wordt bepaald uit posities ongeveer 2 m aan weerszijden van elke meting (`atan2(dx, dz)`); de `yaw` van het spel wordt eraan gefit met een teken en een offset (elk spel heeft zijn eigen nul en draairichting), met metingen boven 10 m/s, en alleen vertrouwd als het daarna goed overeenkomt (circulaire spreiding hoogstens 0,05, minstens 20 metingen). De drifthoek is het verschil, 0 onder 3 m/s.

### Slip-ratio uit de wielen {#slip-ratio-from-the-wheels}

Waar een ronde geen `slipRatio.*` heeft maar wel wielsnelheden, is de slip-ratio `(wiel - auto) / auto` per wiel, uit:

- `wheelSurfaceSpeed.*` (de snelheid van het contactvlak, m/s) rechtstreeks, als die wordt gestuurd (EA WRC, DiRT, BeamNG);
- anders `wheelSpeed.*` (rotatie, rad/s) maal een **rolstraal die op de ronde zelf is gemeten**: de mediaan van `snelheid / |omega|` over metingen waar de auto rechtdoor uitrolt (boven 10 m/s, niet in de lucht, gas onder 0,3, rem onder 0,05, langsversnelling onder 3 m/s²); bij minder dan 20 van zulke metingen elke meting boven 10 m/s. Een straal buiten 0,1-1 m wordt verworpen.

Alleen als alle vier de wielen kunnen worden afgeleid; de `meta.slip` van de ronde wordt dan `physical`. Onder 3 m/s is de slip 0.

### In de lucht {#airborne}

`airborne` is 1 waar alle wielen van de grond af zijn, beoordeeld met de eerste van deze die de ronde voor alle vier de wielen heeft:

1. `groundContact.*` (BeamNG): geen wiel boven 0,5;
2. `wheelLoad.*` (AC-spellen, RBR, BeamNG): geen wiel boven 5% van zijn eigen mediane belasting;
3. `suspension.*` (0..1 van de veerweg): geen wiel boven 0,02, dus allemaal volledig uitgeveerd.

Een losse, geïsoleerde meting in de lucht wordt gewist. Trackmania schrijft `airborne` zelf.

### Losse ondergrond {#loose-ground}

Waar een ronde `surfaceRumble.*` heeft (Forza), is `loose` 1 waar minstens twee wielen een rumble melden, gedurende minstens een derde seconde, met hiaten korter dan een seconde overbrugd (een glad stuk op een grindweg blijft de grindweg). Trackmania schrijft `loose` zelf uit de ondergrondmaterialen van de wielen.

### Gierhoeksnelheid {#yaw-rate}

Waar een ronde `yaw` heeft maar geen `yawRate`, is het de verandering van de `yaw` over de naburige metingen.

## Wat de opnemers zelf afleiden {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): elke opnemer behalve Forza (die het zelf stuurt) schrijft het uit `suspensionM.*` als de positie binnen het bereik dat deze ronde gebruikte (minimum tot maximum). Het is voor de veerstangen van de auto en om een wiel te herkennen dat in de lucht hangt; het is geen absolute veerwegfractie.
- **`steer`** voor de Kunos-spellen, per ronde geschaald (zie [Assetto Corsa-spellen](telemetry-assetto-corsa.md)).
- **Versnellingen** voor BeamNG, uit de verandering van de wereldsnelheid ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** en de verticale as voor Richard Burns Rally, uit de posities ([Rallyspellen](telemetry-rally.md)).

## Handigheid {#handedness}

Waar de wereld van een spel linkshandig is - die van Forza is dat - komt een baan gespiegeld uit in een rechtshandige viewer; de eigen stuur- en veerdata van de ronden laten dat zien. De opnemers veranderen de handigheid niet: een Z-omhoog-wereld (BeamNG) wordt door een rotatie naar Y-omhoog gedraaid, wat de handigheid behoudt, en al het andere wordt geschreven zoals het is verstuurd.
