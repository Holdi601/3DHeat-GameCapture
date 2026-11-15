---
title: "Sammensmelting, dekning og farge"
nav_order: 5
lang: "no"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Sammensmelting, dekning og farge {#fusion-coverage-and-colour}

Kode: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Hvert plasserte nøkkelbilde oppdaterer to glisne rutenett samtidig: **overflatevolumet**, som blir
nettet, og **dekningsrutenettet**, som sier hvor mye man skal tro på det og hvor man skal gå tilbake.
Begge oppdateres per nøkkelbilde, ikke til slutt, fordi dekningskartet er det spilleren styrer etter.

## Fra dybde til punkter {#from-depth-to-points}

For hvert nøkkelbilde hvis posisjon er kjent **og** hvis dybde har en skala:

1. Hver annen piksel i hver retning brukes (`PIXEL_STRIDE = 2`; nabopiksler på samme flate er ikke
   uavhengige målinger).
2. Dybden omregnes til meter med bildets affine tilpasning.
3. Beholdes bare mellom **0,35 m** (nærmere er våpenet, HUD-en, panseret) og **60 m**
   (monokulær feil vokser omtrent med kvadratet av avstanden, så fjerne punkter er støy formet som
   geometri) og bare på verdenspikslene i masken.
4. Løftes gjennom kameramodellen og flyttes inn i verden av posisjonen.
5. Hvert punkt bærer pikselens farge.

Et bilde som er plassert, men ikke har en dybdeskala, telles som *plassert* men ikke *sammensmeltet*.

## Overflatevolumet {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxelen er vinduets "Overflatedetalj".

### Vektet okkupasjon, ikke en TSDF {#weighted-occupancy-not-a-tsdf}

Et avkortet signert avstandsfelt (TSDF) skjærer langs hver pikselstråle og får tynn struktur og
ren fri plass riktig, fordi det vet at en stråle gikk *gjennom* tomt rom. Det betyr å gå strålen for
hver av hundrevis av millioner piksler. Dette volumet akkumulerer i stedet **vektet okkupasjon** per
voxel og kjører marching cubes på det glattede resultatet: raskt nok til å kjøre mens det skannes, på
en maskin uten brukbar GPU, og utdataene er en lukket flate og ikke en punktsky. Prisen: tynn struktur
og fri plass er dårligere enn en TSDF ville gitt.

### Integrering av et bilde {#integrating-a-frame}

- Punkter legges i voxler (`floor(punkt / voxel)`).
- Hver berørt voxel får `vekt x sqrt(antall / maks_antall)`, der `antall` er hvor mange av bildets
  punkter som havnet i den, og `vekt = max(0.1, posisjonssikkerhet)`. Kvadratrot: etter et punkt
  teller ikke flere piksler fra samme flate fra samme sted som ny evidens; vekting etter
  posisjonssikkerhet hindrer at en tvilsom posisjon flytter flaten.
- Farge er et løpende vektet gjennomsnitt per voxel.

Rutenettet er **glissent**: en kjørt rute berører en liten brøkdel av sin avgrensningsboks. Voksel-
koordinater pakkes i én 64-bits nøkkel (21 bit per akse, opptil ±1 048 575 voxler - ved 0,25 m omtrent
±262 km) og slås opp med en sortert matrise og binærsøk, fullt vektorisert.

### Trekke ut nettet {#extracting-the-mesh}

1. Voxler med vekt under **0,35** fjernes (løse enkeltpunkter ved silhuettkanter ville blitt
   piggar).
2. Vektene skaleres etter **75. persentil** over hele skanningen og klippes til 1.
3. Det okkuperte rommet deles i **blokker på 64 voxler** per side, hver realisert med en **3-voxel
   halo** av naboenes data (uten den ville hver blokkgrense lukke seg til en vegg, og en vei ville
   komme ut som en rad med bokser).
4. Hvert blokkfelt glattes med en Gauss (sigma 0,8 voxel) for å fjerne rynkene dybdestøyen etterlater.
5. **Pass én**: 99. persentil av det glattede feltet, tatt over alle blokker (høyst 2 millioner verdier),
   setter én global nivåskala. Å normalisere per blokk ville gjort en enslig avviker til en full flate i
   sin egen tomme blokk.
6. **Pass to**: hvert blokkfelt delt på den skalaen, marching cubes ved **0,5**. En trekant hører til
   blokken dens **tyngdepunkt** faller i, så trekanter som krysser en søm sendes ut nøyaktig én gang.
7. Hjørnene flyttes til verdensenheter i voxelsentrene; hvert hjørne tar sin voxels farge (mellomgrå der
   det faller utenfor en okkupert voxel).

Blokkvis uttrekk er det som gjør en skanning i banestørrelse mulig: ett tett array over en boks på en
kilometer i kvadrat med 0,25 m ville vært milliarder av celler. `tests/test_track_scale.py` slår fast at
det fungerer i den skalaen, med minne proporsjonalt med det som ble skannet.

### Underlag og struktur {#ground-and-structure}

`classify` merker hver trekant etter normalen (orientert etter de uttrukne hjørnenormalene): innenfor
**35 grader rett opp** er den `ground` (underlag), alt annet `structure` (struktur). Viewer tegner underlag
fast og strukturer nesten gjennomsiktige. **Vann merkes aldri** - det kan ikke skilles fra flatt underlag på
form, og en feil merking ville gjengi en gårdsplass som en innsjø. Hver merking blir én del av `.glb`-filen
([.glb-utdata](glb-output.md)).

## Dekning {#coverage}

`CoverageGrid(voxel=0.5)` registrerer, per halvmeter-celle, fire ting som ikke er det samme:

| Begrep | Lagret | Poeng (hver klippet til 0..1) | Hvorfor det telles separat |
|---|---|---|---|
| Hvor mange ganger sett | antall nøkkelbilder som så cellen | `antall / 3` | én gang er en gjetning uten noe å gjennomsnitte mot |
| Fra hvor mange retninger | sum av enhetsretninger for synet | `(1 - spredning) / (1 - 0,93)`, der spredning = lengden av summen / antall | tjue bilder som går rett mot en vegg har ingen parallakse mellom seg; to utsikter 30 grader fra hverandre er verdt mer |
| Fra hvor langt | nærmeste synsavstand | `1 - nærmest / 40 m` | dybdefeil vokser omtrent med avstanden i annen |
| Hvor godt kameraet var plassert | beste posisjonssikkerhet | sikkerheten | geometri sammensmeltet med en tvilsom posisjon havner feil |

Et bildes punkter grupperes først per celle, så ti tusen piksler av én vegg teller som én observasjon fra
én retning.

**Kvalitet = produktet av de fire leddene**, ikke gjennomsnittet: de er betingelser som hver må
holde. Et sted sett to hundre ganger fra én retning på seksti meter er dårlig observert, og et
gjennomsnitt ville skjult det bak ett utmerket ledd.

Hovedtallene (`summary`): okkuperte celler, andelen med kvalitet minst 0,5 ("% godt sett" i vinduet),
gjennomsnittlig kvalitet og volum.

### Svake punkter {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. celler med kvalitet under 0,35 er svake;
2. svake celler grupperes etter **sammenheng** (26-nabolag, union-find over bare de okkuperte cellene -
   ikke et rasternett over avgrensningsboksen, som på en lang kjøring er millioner av tomme celler);
3. grupper med færre enn 8 celler ignoreres;
4. hver gruppes årsak er den hyppigste *svakeste leddet* blant cellene, og posisjonen er gjennomsnittet
   av cellene;
5. sortert størst først (så verste kvalitet), høyst 8.

| Årsak | Råd som vises |
|---|---|
| få observasjoner | Sett bare én eller to ganger - gå forbi igjen. |
| én retning | Bare sett fra én vinkel. Gå sidelengs og se på det igjen. |
| langt unna | Bare sett langt unna. Kom nærmere. |
| dårlig sporing | Kameraet var ikke godt posisjonert her. Nærm deg saktere. |

Sammenheng betyr noe: gruppering etter et fast blokkrutenett rapporterer ett forsømt sidekammer som mange
separate ringer, og ingen kan skille åtte steder fra ett sted talt åtte ganger.

### Oversiktskartet {#the-plan-view}

`top_down(resolution)` projiserer cellene på x/z og beholder den **beste** kvaliteten per kolonne (noen
som står i et rom har dårlig dekning av taket og utmerket dekning av gulvet; et gjennomsnitt ville gjort
rommet gulbrunt). Kolonner som aldri er observert merkes separat. Vinduet tegner det i 200 x 200, overlegget i
120 x 120 ([Skanningsvinduet](reconstruction-scan-ui.md#the-coverage-map)).

### Er dette rekonstruerbart? {#is-this-reconstructable}

Hver 25. sammensmeltede bilde, når det finnes minst 500 celler:

| Funn | Dom | Melding (forkortet) |
|---|---|---|
| færre enn 2 % av cellene har synsspredning under 0,93 | ikke rekonstruerbart | Nesten ingen parallakse. Enten ser kameraet aldri til siden, eller sporingen driver slik at den samme flaten aldri havner to ganger på samme sted. Sjekk antallet plasserte bilder: er det høyt, er det drift. |
| median nærmeste avstand over 25 m | ikke rekonstruerbart | Alt ble sett fra N m eller lenger ... Kom nærmere det du vil ha. |
| færre enn 6 % med god spredning | rekonstruerbart, med advarsel | Tynn parallakse - geometrien blir grov. Å bevege seg sidelengs i forhold til det du ser på hjelper mest. |

Lav parallakse har to årsaker dette ikke kan skille fra hverandre, og derfor nevner meldingen begge.

## Farge {#colour}

Sammensmeltingens farge per voxel er billig og live, og uskarp: hver piksel i en kvart-meter-celle
gjennomsnittes, også de som er sett på kant fra tretti meter. Så ved eksport farges nettet på nytt, én
gang, fra bildene selv:

- **Beholdte bilder**: opptil **160** nøkkelbilder (bilde og posisjon), valgt med reservoarsampling slik
  at de spres over hele skanningen og ikke bare dens hale.
- **Per hjørne** (`project_colours`) bidrar hvert beholdt bilde hvis hjørnet er foran kameraet og innenfor
  bildet, flaten er vendt høyst omtrent 70 grader bort fra å se rett på kameraet (`|normal . visning| > 0,34`),
  det er nærmere enn **35 m**, og ingenting nærmere sto foran det (se under).
- Hver slik visning poengsettes `vendt x (1 - avstand / 35)`, så en nær visning rett forfra slår en fjern
  skrå. De **4 høyest poengsatte** visningene for hvert hjørne beholdes - uansett rekkefølgen bildene kommer i,
  erstatter en bedre visning den svakeste av de fire - og blandes, vektet med samme poengsum.
- **Okklusjon**: i hvert bilde tegnes nettets egne hjørner som er synlige inn i en dybdebuffer med 2-piksel-
  celler, og beholder det nærmeste per celle. Et hjørne mer enn `0,3 m + 5 %` av sin avstand bak det nærmeste i
  sin celle var skjult i det bildet - en vegg mellom kameraet og veien bak - og den visningen teller ingenting.
  Testen kjenner bare nettet: en okkluder som aldri ble sammensmeltet (en forbikjørende bil, en cockpitstolpe
  utenfor HUD-masken) fanges ikke.
- Et hjørne ingen bilde så beholder sin voxelfarge; et hjørne uten noen av delene er mellomgrå (svart ville
  lest som et hull).

Farge skrives som per-hjørne `COLOR_0`, ikke som et teksturatlas. Viewerens standardutseende er et grått kart
under mettet varme; farge er der for å finne veien på en skannet bane, der geometri alene ikke skiller
banen fra kanten, og den vises bak viewerens *Registrert farge*-bryter i panelet Bakgrunn / nivå. Et atlas
ville multiplisert filstørrelsen og trengt en utfolder, for en visning som bevisst ikke er standard. Blender og
andre glTF-verktøy leser `COLOR_0`.
