---
title: "Fusion, dækning og farve"
nav_order: 5
lang: "da"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusion, dækning og farve {#fusion-coverage-and-colour}

Kode: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Hvert placeret nøglebillede opdaterer to sparse gitre på én gang: **overfladevolumen**, som bliver til mesh'en, og **dækningsgitteret**, som siger, hvor meget der skal tros, og hvor man skal tilbage hen. Begge opdateres pr. nøglebillede, ikke til sidst, fordi dækningskortet er det, spilleren styrer efter.

## Fra dybde til punkter {#from-depth-to-points}

For hvert nøglebillede, hvis position er kendt **og** hvis dybde har en skala:

1. Hver anden pixel i hver retning bruges (`PIXEL_STRIDE = 2`; nabopixels på samme overflade er ikke uafhængige målinger).
2. Dybden omregnes til meter med billedets affine tilpasning.
3. Beholdes kun mellem **0,35 m** (nærmere er våbnet, HUD'en, motorhjelmen) og **60 m** (den monokulære fejl vokser nogenlunde med afstanden i anden, så fjerne punkter er støj, der ligner geometri), og kun på verdenspixels i masken.
4. Løftes gennem kameramodellen og flyttes ind i verden af positionen.
5. Hvert punkt bærer pixelens farve.

Et billede, der er positioneret, men ikke har en dybdeskala, tælles som *placeret*, men ikke *fusioneret*.

## Overfladevolumen {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxelen er vinduets "Surface detail".

### Vægtet belægning, ikke en TSDF {#weighted-occupancy-not-a-tsdf}

Et truncated signed distance field skærer langs hver pixels stråle og får tynde strukturer og rent frit rum rigtigt, fordi det ved, at en stråle gik *gennem* tomt rum. Det kræver at gå strålen for hver af hundreder af millioner pixels. Dette volumen akkumulerer i stedet **vægtet belægning** pr. voxel og kører marching cubes på det udjævnede resultat: hurtigt nok til at køre under scanning på en maskine uden en brugbar GPU, og outputtet er en lukket overflade i stedet for en punktsky. Prisen: tynde strukturer og frit rum er dårligere, end en TSDF ville give.

### Indlæsning af et billede {#integrating-a-frame}

- Punkter placeres i voxels (`floor(point / voxel)`).
- Hver berørt voxel får `vægt x sqrt(antal / maks antal)`, hvor `antal` er, hvor mange af billedets punkter der faldt i den, og `vægt` er den største af 0,1 og pose-konfidensen. Kvadratroden: ud over et punkt er flere pixels fra samme overflade set fra samme sted ikke længere bevis; vægtning efter pose-konfidens forhindrer en tvivlsom position i at skubbe overfladen rundt.
- Farven er et løbende vægtet gennemsnit pr. voxel.

Gitteret er **sparset**: en gennemkørt rute berører en lille brøkdel af sin omsluttende boks. Voxel-koordinater pakkes i én 64-bit nøgle (21 bit pr. akse, op til ±1.048.575 voxels - ved 0,25 m cirka ±262 km) og slås op med et sorteret array og binær søgning, fuldt vektoriseret.

### Udtrækning af mesh'en {#extracting-the-mesh}

1. Voxels med vægt under **0,35** droppes (løse enkeltpunkter ved silhuetkanter ville blive til pigge).
2. Vægte skaleres med **75. percentil** over hele scanningen og klippes til 1.
3. Det belagte rum skæres i **blokke på 64 voxels** pr. side, hver realiseret med en **3-voxel halo** af naboernes data (uden den lukker hver blokgrænse sig til en væg, og en vej kommer ud som en række kasser).
4. Hver blokks felt udjævnes med en Gauss (sigma 0,8 voxel) for at fjerne den rynke, dybdestøjen efterlader.
5. **Første gennemgang**: 99. percentil af det udjævnede felt, udtaget på tværs af alle blokke (højst 2 millioner værdier), sætter én global niveauskala. Normalisering pr. blok ville gøre en enlig udligger til en fuld overflade i sin egen tomme blok.
6. **Anden gennemgang**: hver bloks felt divideret med den skala, marching cubes ved **0,5**. En trekant hører til den blok, dens **tyngdepunkt** falder i, så trekanter over en søm udsendes præcis én gang.
7. Hjørnepunkter flyttes til verdensenheder ved voxelcentre; hvert hjørnepunkt får sin voxels farve (mellemgråt, hvor det falder uden for en belagt voxel).

Blokvis udtrækning er det, der gør en scanning i banestørrelse mulig: ét tæt array over en kvadratkilometer-boks ved 0,25 m ville være milliarder af celler. `tests/test_track_scale.py` fastlægger, at det virker i den skala med hukommelse proportional med det, der er scannet.

### Jord og struktur {#ground-and-structure}

`classify` mærker hver trekant efter dens normal (orienteret efter de udtrukne hjørnenormaler): inden for **35 grader af lodret op** er det `ground`, alt andet `structure`. Viewer'en tegner jord fast og strukturer næsten gennemsigtige. **Vand påstås aldrig** - det kan ikke skelnes fra fladt jord på form, og en forkert mærkning ville gøre en gårdsplads til en sø. Hver mærkning bliver til én del af `.glb`-filen ([.glb-outputtet](glb-output.md)).

## Dækning {#coverage}

`CoverageGrid(voxel=0.5)` registrerer pr. halvmeter-celle fire ting, der ikke er det samme:

| Led | Gemt | Score (hver klippet til 0..1) | Hvorfor de tælles hver for sig |
|---|---|---|---|
| Hvor mange gange set | antal nøglebilleder, der så cellen | `antal / 3` | én gang er et gæt uden noget at gennemsnitte med |
| Fra hvor mange retninger | sum af enhedsvisningsretninger | `(1 - spredning) / (1 - 0,93)`, hvor spredning = længden af summen / antal | tyve billeder, der går lige mod en væg, har ingen parallakse mellem sig; to udsigter tredive grader fra hinanden er mere værd |
| Fra hvor langt væk | nærmeste visningsafstand | `1 - nærmest / 40 m` | dybdefejlen vokser nogenlunde med afstanden i anden |
| Hvor godt kameraet var placeret | bedste pose-konfidens | konfidensen | geometri fusioneret med en tvivlsom pose lander det forkerte sted |

Et billedes punkter grupperes først pr. celle, så ti tusinde pixels på én væg tæller som én observation fra én retning.

**Kvalitet = produktet af de fire led**, ikke gennemsnittet: de er betingelser, der hver skal være opfyldt. Et sted set to hundrede gange fra én retning på tres meter er dårligt observeret, og et gennemsnit ville skjule det bag ét fremragende led.

Hovedtallene (`summary`): belagte celler, andelen med kvalitet mindst 0,5 ("% well seen" i vinduet), gennemsnitlig kvalitet og volumen.

### Svage pletter {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. celler med kvalitet under 0,35 er svage;
2. svage celler grupperes efter **forbundethed** (26-naboskab, union-find kun over de belagte celler - ikke et raster over den omsluttende boks, som på en lang kørsel er millioner af tomme celler);
3. grupper med færre end 8 celler ignoreres;
4. hver gruppes årsag er den hyppigste *svageste led* blandt dens celler, og dens position er gruppens middel;
5. sorteret største først (så værste kvalitet), højst 8.

| Årsag | Vist råd |
|---|---|
| få observationer | Seen only once or twice — walk past it again. |
| én retning | Only seen from one angle. Step sideways and look at it again. |
| fjern | Only seen from far away. Get closer to it. |
| dårlig sporing | The camera was not well located here. Approach it more slowly. |

Forbundethed betyder noget: gruppering efter et fast blokgitter ville rapportere ét forsømt sidekammer som mange adskilte ringe, og ingen kunne se forskel på otte steder og ét sted talt otte gange.

### Planvisningen {#the-plan-view}

`top_down(resolution)` projicerer cellerne ned på x/z og beholder den **bedste** kvalitet pr. søjle (en person stående i et rum har dårlig dækning af loftet og fremragende dækning af gulvet; et gennemsnit ville male rummet gult). Søjler, der aldrig er observeret, markeres særskilt. Vinduet tegner den i 200 x 200, overlayet i 120 x 120 ([Scanvinduet](reconstruction-scan-ui.md#the-coverage-map)).

### Kan det rekonstrueres? {#is-this-reconstructable}

Hver 25. fusionerede billede, når der er mindst 500 celler:

| Konklusion | Vurdering | Besked (forkortet) |
|---|---|---|
| under 2 % af cellerne har visningsspredning under 0,93 | kan ikke rekonstrueres | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| median af nærmeste afstand over 25 m | kan ikke rekonstrueres | Everything was seen from N m away or further ... Get closer to what you want. |
| under 6 % med god spredning | kan rekonstrueres, med advarsel | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Lav parallakse har to årsager, som dette ikke kan skelne mellem, og det er derfor, beskeden nævner begge.

## Farve {#colour}

Fusionens farve pr. voxel er billig og live, og sløret: hver pixel i en kvart-meter celle er gennemsnittet, også dem set på skrå fra tredive meter. Så ved eksport farves mesh'en igen, én gang, ud fra selve billederne:

- **Gemte billeder**: op til **160** nøglebilleder (billede og pose), valgt ved reservoirprøvetagning, så de spredes over hele scanningen og ikke kun dens hale.
- **Pr. hjørnepunkt** (`project_colours`) bidrager hvert gemt billede, hvis hjørnepunktet er foran kameraet og inden for billedet, overfladen vender højst cirka 70 grader væk fra at vende direkte mod kameraet (`|normal . view| > 0,34`), den er nærmere end **35 m**, og intet nærmere stod foran den (nedenfor).
- Hver sådan visning scores `vendt x (1 - afstand / 35)`, så et tæt, direkte billede slår et fjernt skråt. De **4 højest scorende** visninger af hvert hjørnepunkt beholdes - uanset billedernes rækkefølge erstatter en bedre visning det svageste af de fire - og blandes, vægtet med den samme score.
- **Okklusion**: i hvert billede tegnes mesh'ens egne hjørnepunkter i syn ind i en dybdebuffer med 2-pixel-celler, og den nærmeste pr. celle beholdes. Et hjørnepunkt mere end `0,3 m + 5 %` af dets afstand bag det nærmeste i sin celle var skjult i billedet - en væg mellem kameraet og vejen bagved - og den visning tæller ikke. Testen kender kun mesh'en: en okkluder, der aldrig blev fusioneret (en forbikørende bil, en cockpitstolpe uden for HUD-masken), fanges ikke.
- Et hjørnepunkt, ingen billeder så, beholder sin voxelfarve; et hjørnepunkt med ingen af delene er mellemgråt (sort ville læses som et hul).

Farven skrives som pr. hjørnepunkt `COLOR_0`, ikke som en teksturatlas. Viewer'ens standardudseende er et gråt kort under mættet varme; farven er der for at finde vejen på en skannet bane, hvor geometri alene ikke skiller den fra skråningen, og den vises bag viewer'ens kontakt *Optaget farve* i panelet Baggrund / bane. En atlas ville fordoble filstørrelsen og kræve en udfoldningsmaskine for en visning, der bevidst ikke er standard. Blender og andre glTF-værktøjer læser `COLOR_0`.
