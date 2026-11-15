---
title: "Kameraposisjon og skala"
nav_order: 4
lang: "no"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kameraposisjon og skala {#camera-pose-and-scale}

Et dybdekart sier hvor langt ting er fra *ett* synspunkt. For å gjøre mange av dem til ett nivå
må man vite hvor hvert synspunkt var, og i hvilke enheter. Denne siden dekker de live-banene;
den offline feed-forward-løsingen er på [Offline rekonstruksjon](reconstruction-offline.md).

Kode: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Kameramodellen {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` bygger et hullkamera fra det **horisontale synsfeltet** du setter i vinduet:
`fx = (width / 2) / tan(fov / 2)`, kvadratiske piksler (`fy = fx`), hovedpunktet i bildets midte. Et spill publiserer ikke
sin projeksjon, så dette er det ene antatte tallet: for smalt, og scenen leses som dypere enn den er. Den offline banen
bruker 65 grader.

En `Pose` lagres **verden-fra-kamera**: `rotation` (3 x 3) og `translation` = kameraets sentrum i verden, som er det
banen, dekningskartet og overlegget alle vil ha.

## Visuell odometri (standard) {#visual-odometry-the-default}

`VisualOdometry` sporer hvert nøkkelbilde mot det forrige:

1. **Trekk**: ORB, opptil 1500 per bilde, oppdaget bare på verdenmasken (se [Opptak](reconstruction-capture.md#what-is-not-the-world)).
2. **Treff** mot forrige nøkkelbilde: brute force, Hamming-avstand, krysssjekket (bare gjensidig beste par).
3. **Løft til 3D**: forrige bildes dybde er allerede i verdensenheter, så dets matchede piksler blir verdenspunkter.
4. **Plasser kameraet**: `solvePnPRansac` blant disse punktene (reprojeksjonsfeil 3 px, konfidens 0,999, 200 iterasjoner).
   Translasjonen kommer ut i samme enheter, så **skalaen krysser gapet**.
5. **Ankre dette bildets dybde**: dets egen predikerte invers dybde tilpasses (`fit_scale`) mot innliggerdybdene fra PnP,
   og syklusen gjentar seg.

Det **første bildet** er origo: identitetsposisjon, og dets dybdes affine er enten bakkekalibreringen nedenfor, eller uten
en slik identiteten (rekonstruksjonen er da selvkonsistent, men uten enhet).

En posisjon trenger minst **18 RANSAC-innliggere** - klart mer enn PnPs minimum på seks, siden en løsning fra knapt nok punkter
er nøyaktig den som er trygt feil.

### Sikkerhet {#confidence}

Hvert plassert bilde får en sikkerhet i 0..1 som vekter sin sammensmelting og dekning:

| Posisjon fra | Sikkerhet |
|---|---|
| telemetri | 1,0 |
| en feed-forward-løsing | 0,85 |
| visuell sporing | `innliggere / treff x min(1, innliggere / 60)` |

### Når sporingen brytes {#when-tracking-breaks}

Et bilde som ikke kan plasseres rapporteres, aldri gjettes: `ingen trekk i bildet (N
funnet)`, `for få treff til å plassere kameraet`, `kunne ikke relokaliseres`. Ingen posisjon
registreres, og ingenting sammensmeltes. Å fortsette fra siste posisjon, eller starte en ny origo, ville plassert
neste strekning av nivået på en vilkårlig forskyvning - en søm som ser ut som ekte geometri.

Etter et brudd **relokaliseres** hvert nytt bilde mot en database av tidligere nøkkelbilder (hver fjerde sporede bilde legges
til, opptil 120, de eldste droppes), de nyeste først, med samme treff-og-PnP-steg. Inntil et lykkes, droppes bilder.
Et gjenopprettet bilde fortsetter i samme koordinatramme. Gjenopprettinger telles og vises i vinduet (`N gjenopprettet`).

### Sløyfelukking: av {#loop-closure-off}

Den samme databasen støtter sløyfelukking: å matche mot nøkkelbilder fra mye tidligere for å oppdage et gjenbesøk og
snappe banen tilbake på det. **Den er av som standard, og skanneren slår den aldri på** (`Reconstructor(loop_closure=False)`).
På repeterende omgivelser - en rallyetappe, en korridor, en rad med trær - ser hver strekning ut som alle andre, og
trekkmatching bekrefter falske gjenbesøk, noe som fester kameraet nær startpunktet mens det kjører videre. Å gjøre det
ordentlig krever stedsgjenkjenning (et bag-of-words-vokabular eller en lært deskriptor) og geometrisk verifisering mot et kart,
og det er ikke bygget.

Når den er slått på fra kode, krever en lukking: et nøkkelbilde minst 60 nøkkelbilder gammelt, innenfor 6 m av gjeldende
posisjon, matchet med minst 90 innliggere, som flytter posisjonen mer enn 0,02 m og mindre enn 6 m. Selv da erstatter den
bare gjeldende posisjon; den er ikke en posisjonsgraf og flytter ikke tidligere bilder eller sammensmeltet geometri.

## Telemetriposisjoner {#telemetry-poses}

Med **Racing telemetry (Forza) -> Listen for position data** på, kommer kameraets bane fra Forzas Data Out i stedet for
fra bildene (`ForzaPoseSource`):

- En tråd lytter på `127.0.0.1:<port>` (5300 som standard) med samme oppsettdeteksjon som opptakerne ([Forza](telemetry-forza.md));
  pakker brukes mens `isRaceOn` er satt. En opptatt port rapporteres, ikke kastes: telemetri er en oppgradering, og skanningen
  fortsetter visuelt.
- Hver pakke stemples med **den monotone tiden den kom inn** - samme klokke som opptaket stempler bilder med. Spillets egen
  tidsstempel teller fra noe urelatert, så den brukes ikke til oppretting. Loopback-jitter på en-to millisekunder er omtrent 6 cm ved 200 km/t.
- En rullende buffer på 30 sekunder beholdes. Et bildes posisjon **interpoleres** fra prøvene på hver side av opptakstiden:
  posisjon lineært, rotasjon med sfærisk interpolasjon (en blandet matrise er ikke en rotasjon, og den ville skjevet hvert punkt).
  Over et gap lenger enn **0,35 s**, eller utenfor bufferen, finnes ingen posisjon.
- `pose_from_forza`: kameraet plasseres ved bilen (et jaktkameras forskyvning publiseres ikke). **Posisjonene beholdes nøyaktig
  slik spillet sender dem**: Forzas verden er allerede Y-opp (x og z over kartet, y høyden), slik lagrings- og rutefilene skriver den,
  så flaten lander på de samme koordinatene som rundene tatt over den. (En tidligere versjon byttet y og z for en "Z-opp"-verden
  og la banen på siden.)
- Rotasjonen er gir, deretter stigning, deretter rulling, med fortegnene lest av innspilte runder: kjøreretningen `atan2(dx, dz)`
  er lik giret, den oppadgående stigningen er lik minus stigningen (positiv er nesen ned), og rullingen er positiv når den høyre
  fjæringen er trykket sammen (positiv senker høyre side). Bilens akser (x høyre, y opp, z fremover) blir så til kameraets
  (x høyre, y ned, z fremover) ved å snu y.
- Forzas verden er **venstrehåndet** og kameraets ramme er det ikke, så den resulterende verden-fra-kamera-matrisen er en speiling
  (determinant -1), og skanningen kommer ut venstrehåndet som rundefilene. Interpolasjon påvirkes ikke (svingen mellom to slike
  posisjoner er en ekte rotasjon).
- Når et bilde ikke har telemetriposisjon (et gap), faller rekonstruktøren tilbake til **visuell sporing** for det bildet, og
  fortsetter fra siste telemetriposisjon, og går tilbake til feedens posisjoner så snart den svarer igjen. PnP returnerer bare
  rotasjoner, så i en speilet verden løses den med verden speilet gjennom z og speilingen foldet tilbake; bildet havner i spillets
  koordinater. Bare hvis visuell sporing også mislykkes er bildet ustyrt.

### Dybdeskala fra telemetri {#depth-scale-from-telemetry}

Spillet sier hvor kameraet er, ikke hvor langt unna noe er, så hvert bildes dybde trenger fortsatt å ankres - men ikke ved å kjede
fra bilde null, hvis enhet er vilkårlig mens posisjonene er i meter. I stedet blir trekk matchet mellom forrige og nåværende bilde
(minst 8) **triangulert direkte fra de to kjente posisjonene**, i meter, og dybdekartet tilpasses punktene foran kameraet. Hvert
bilde ankres mot telemetrien, så det finnes ingen kjede som kan drive.

Hvis de to posisjonene er mindre enn **0,05 m** fra hverandre, er strålene nesten parallelle og triangulering er støy, så bildet
forblir uankret: nøyaktig plassert, men ikke sammensmeltet ("positioned, but its depth has no scale yet" - plassert, men dybden
har ingen skala ennå). Derfor teller vinduet *plasserte* og *sammensmeltede* bilder hver for seg.

## Skala {#scale}

Visuell odometri kjeder relativ skala riktig, men hele nivået flyter fortsatt på en ukjent faktor. Depth Anythings relative utdata
kommer i vilkårlige enheter, så å la første bilde være identitet setter verden innen meter fra kameraet i en vilkårlig størrelse.

`GroundCalibrator` fester den faktoren ut fra **hvor høyt kameraet er over bakken**, målt på **første nøkkelbilde** og, når det ikke
har brukbart underlag, på de påfølgende:

- Kamerahøyde: **1,15 m** (en sjåførs øyehøyde) - vinduet bruker alltid denne; skript kan gi 1,70 m (`WALKING_HEIGHT`, en stående
  spiller) eller `None` (ingen kalibrering).
- Underlagsutvalg: rader 62-92 % ned i bildet (under horisonten, over panseret eller våpenet) og kolonner 30-70 % over
  (vekk fra kantene).
- Hver piksel der med en brukbar prediksjon løftes med dybde `1 / predikert` i nettverkets enheter; punkter under den optiske aksen
  gir en høyde under kameraet. Medianen deres er kamerahøyden i nettverksenheter, så `meter per enhet = 1,15 / median`, og bildets
  affine er `scale = 1 / meter_per_enhet`, forskyvning 0.
- Stoles bare på med minst 200 underlagsprøver og en **spredning** (median absolutt avvik over median) under **0,60**.
- På første nøkkelbilde blir tilpasningen origoens enhet, så skanningen er i meter fra starten. Når første nøkkelbilde ikke har brukbart
  underlag, starter skanningen uten enhet, og hvert senere sporet nøkkelbilde prøves, opptil **30 bilder** totalt. Den første som kalibrerer
  gir *meter per enhet*: medianen, over underlagsbåndet, av dybden dets underlag gir delt på dybden kjeden ga for det bildet. Alt som allerede er
  sammensmeltet er i første bildes enhet, så faktoren mates ikke tilbake i kjeden; den brukes på hele nivået (og på de merkede stedene) når det
  skrives, og på avstanden som vises i mellomtiden. Voxelstørrelsen er da i første bildes enheter, så størrelsen i meter avviker fra innstillingen med den faktoren.
- Etter 30 bilder uten underlag forblir skanningen uten enhet, og den sier det.
- Med telemetri prøves ikke senere nøkkelbilder: dybden er ankret til telemetriens meter.

Å være innenfor ti prosent av riktig størrelse er bedre enn å være ute med en faktor på tusen; telemetri gjør det unødvendig der den finnes.
Notatet vises i vinduet under sporingslinjen, som `Størrelse: ...`: `måler underlaget`, `ingen flatt underlag i synsfeltet ennå - leter fortsatt (N bilder prøvd)`,
`skalert fra en 1,15 m kamerahøyde, ...` (med `funnet på bilde N, så nivået skaleres med F når det skrives` når det kom senere),
`ingen brukbart underlag i de første N bildene - størrelsene er relative, ikke meter`, eller `i meter, fra telemetriens posisjoner`.

## Bundle-justering og lange spor (ikke koblet inn) {#bundle-adjustment-and-long-tracks-not-wired-in}

To deler finnes for en fremtidig vindusløser og er **ikke brukt av skanneren**:

- **`FeatureTracks`** beholder trekkidentitet over hundrevis av bilder med Lucas-Kanade-sporing (600 trekk, seedes på nytt under 60 %,
  forover-bakover-toleranse 1 px, nye trekk 10 px fra eksisterende), som bundle-justering trenger - deskriptormatching mellom etterfølgende
  bilder gir bare par.
- **`bundle_adjust`** forbedrer et vindu av posisjoner og punkter sammen med `scipy.optimize.least_squares` (tillitsregion, soft-L1-tap med
  2 px skala, et eksplisitt Jacobi-glissmønster, faste kameraer gjenopprettet nøyaktig). Testet mot kjent sannhet i `tests/test_bundle.py`.

`WindowedOdometry` kombinerer dem (12-nøkkelbildevinduer, en løsing hvert 3. nøkkelbilde, de to første kameraene fast, punkter med over 6 px
feil droppes, hopp over 6 ganger det nylige steget avvises). Dens docstring noterer at den på ekte opptak **kollapset banen og var mye tregere**
enn sporing bilde for bilde, med gauge-frihet (skala) og et dybdebasert oppstartsforsøk som kjente årsaker og en tredje årsak som ikke er identifisert.
Så odometri bilde for bilde forblir standard; den sannsynlige løsningen som er notert i koden er en essensiell-matrise-oppstart for to visninger med
grunnlinjen festet fra bakkeplankalibreringen.
