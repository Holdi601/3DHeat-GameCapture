---
title: "Slip, drift och härledda kanaler"
nav_order: 8
lang: "sv"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Slip, drift och härledda kanaler {#slip-drift-and-derived-channels}

Analysen av bilkontroll i visarens flik Racinganalys vill ha samma få storheter från varje spel: hur mycket varje däck glider, hur mycket bilen pekar bort från dit den är på väg (driftvinkeln), om den är i luften, och om den är på lös mark. Spel skickar dessa i mycket olika former, eller inte alls. Inspelarna här skriver det varje spel skickar, under kanoniska namn, plus en `meta.slip`-notis som säger vad slip-värdena betyder. Visaren härleder sedan det som saknas, en gång, när den laddar ett varv. **Ett spels eget värde vinner alltid över ett härlett.**

## Vad inspelarna skriver {#what-the-recorders-write}

| Spel | Slip-kanaler | `meta.slip` | Indata för driftvinkel |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` per hjul, som skickat | `peak` (skrivs av inspelaren; visarens `.tele.gz`-läsare sätter samma) | `latVel`, `longVel` från den bilslokala hastigheten |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` från hastigheten i bilens ram |
| EA SPORTS WRC, DiRT-spelen | inga; `wheelSurfaceSpeed` per hjul i stället | `null` | `latVel`, `longVel` = världshastigheten projicerad på bilens axlar |
| Richard Burns Rally | inga; inte heller hjulhastigheter | ingen | `latVel`, `longVel` = bilens egen sidsvängning och längdrörelse |
| BeamNG.drive | inga; `wheelSurfaceSpeed` och `wheelSpeed` per hjul | ingen | `latVel`, `longVel` = världshastigheten projicerad på bilens axlar |
| Trackmania | `slipIndex` per hjul (ett 0..1 glidmått) | `index` | `latVel` (sidhastighet), `longVel` (framhastighet) |
| iRacing | inga (loggas inte) | ingen | `yaw` och banan, `yawRate` |

`meta.slip`-värdena definieras i [heat3d-lap-filen](lap-format.md): `peak` (normaliserad, så att däcket släpper taget när värdet är över 1), `scaled` (en fysisk slip delad med ett typiskt toppvärde för asfalt), `physical` (en bråkdel och radianer) och `index` (ett 0..1 glidmått).

### Varför Kunos-slip skalas {#why-kunos-slip-is-scaled}

Forzas slip är normaliserad så att 1 är gränsen för grepp. Vad den normaliseras mot är inte dokumenterat. Kunos skickar den fysiska slip-kvoten (en bråkdel) och slip-vinkeln (radianer). Genom att dela med ett typiskt toppvärde för asfalt (0,12 för kvoten, 0,14 rad, ungefär 8 grader, för vinkeln) blir "över 1 betyder glidning" ungefär sant för båda familjerna, vilket ger en läsning för visarens displayer. Det är en approximation: verkliga toppvärden varierar med däck och underlag. Därför behålls de råa värdena bredvid de skalade, och visaren mäter var varje bils grepp faktiskt upphör från varven själva.

## Vad visaren härleder (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Dessa körs i visaren (`src/race/derive.ts` i 3DHeat-visaren), inte i det här repot.

### Driftvinkel, `bodySlip` {#drift-angle-bodyslip}

- **Från hastigheten i bilens ram** när `latVel` och `longVel` finns: `atan2(latVel, |longVel|)`, och 0 under 3 m/s (en bil som står still åt sidan driftar inte). Dess tecken följer spelets sidhastighet, vars riktning är dokumenterad åt båda håll för vissa spel. Läs storleken.
- **Annars från riktningen mot banan**: färdriktningen tas från positioner ungefär 2 m på vardera sidan om varje sampel (`atan2(dx, dz)`). Spelets `yaw` anpassas till den med ett tecken och en förskjutning, eftersom varje spel har sin egen nollpunkt och rotationsriktning. Anpassningen använder sampel över 10 m/s och litas bara på om den sedan stämmer väl (cirkulär spridning högst 0,05, minst 20 sampel). Driftvinkeln är skillnaden, 0 under 3 m/s.

### Slip-kvot från hjulen {#slip-ratio-from-the-wheels}

Där ett varv saknar `slipRatio.*` men har hjulhastigheter är slip-kvoten `(hjul - bil) / bil` per hjul, från:

- `wheelSurfaceSpeed.*` (kontaktytans hastighet, m/s) direkt, när den skickas (EA WRC, DiRT, BeamNG);
- annars `wheelSpeed.*` (rotation, rad/s) gånger en **rullradie uppmätt på varvet**: medianen av `speed / |omega|` över sampel där bilen rullar rakt (över 10 m/s, inte i luften, gas under 0,3, broms under 0,05, längsgående acceleration under 3 m/s²). Med färre än 20 sådana sampel används varje sampel över 10 m/s. En radie utanför 0,1-1 m förkastas.

Det görs bara när alla fyra hjul kan härledas, och varvets `meta.slip` blir då `physical`. Under 3 m/s är slip 0.

### I luften {#airborne}

`airborne` är 1 där varje hjul är utan markkontakt. Det bedöms efter den första av dessa som varvet har för alla fyra hjulen:

1. `groundContact.*` (BeamNG): inget hjul över 0,5;
2. `wheelLoad.*` (AC-spelen, RBR, BeamNG): inget hjul över 5 % av sin egen medianlast;
3. `suspension.*` (0..1 av väg): inget hjul över 0,02, dvs. alla helt utsträckta.

Ett enstaka isolerat luftsampel tas bort. Trackmania skriver `airborne` själv.

### Lös mark {#loose-ground}

Där ett varv har `surfaceRumble.*` (Forza) är `loose` 1 där minst två hjul rapporterar vibrationer i minst en tredjedel av en sekund. Gap kortare än en sekund överbryggas, så att en slät fläck på en grusväg fortfarande är grusvägen. Trackmania skriver `loose` själv utifrån hjulens markmaterial.

### Gir-hastighet {#yaw-rate}

Där ett varv har `yaw` men ingen `yawRate` är den förändringen i yaw över grannsamplen.

## Vad inspelarna härleder själva {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): alla inspelare utom Forza (som skickar den) skriver den från `suspensionM.*` som positionen inom det omfång varvet använde (minimum till maximum). Den är till för bilens fjädringsstänger och för att se ett hjul som hänger i luften. Den är inte en absolut fjädringsandel.
- **`steer`** för Kunos-spelen, skalad per varv (se [Assetto Corsa-spelen](telemetry-assetto-corsa.md)).
- **Accelerationer** för BeamNG, från förändringen i världshastighet ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** och upp-axeln för Richard Burns Rally, från positionerna ([Rallyspel](telemetry-rally.md)).

## Orientering {#handedness}

Där ett spels värld är vänsterhänt, som Forzas är, kommer en bana ut spegelvänd i en högerhänt visare. Varvens egen styrning och fjädring avslöjar det. Inspelarna ändrar inte orienteringen: en Z-upp-värld (BeamNG) vrids till Y-upp av en rotation, vilket behåller den, och allt annat skrivs som det skickas.
