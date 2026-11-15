---
title: "Kameraposition og skala"
nav_order: 4
lang: "da"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kameraposition og skala {#camera-pose-and-scale}

Et dybdekort siger, hvor langt ting er fra *et* synspunkt. For at gøre mange af dem til ét niveau skal man vide, hvor hvert synspunkt var, og i hvilke enheder. Denne side dækker de live stier; den offline feed-forward-løsning står på [Offline-rekonstruktion](reconstruction-offline.md).

Kode: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Kameramodellen {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` bygger et hulkamera ud fra det **vandrette synsfelt**, du sætter i vinduet: `fx = (width / 2) / tan(fov / 2)`, kvadratiske pixels (`fy = fx`), hovedpunktet i billedets midte. Et spil offentliggør ikke sin projektion, så dette er det ene antagede tal: for smalt, og scenen ser dybere ud, end den er. Offline-stien bruger 65 grader.

En `Pose` gemmes **verden-til-kamera**: `rotation` (3 x 3) og `translation` = kameraets centrum i verden, hvilket er det, banen, dækningskortet og overlayet alle vil have.

## Visuel odometri (standard) {#visual-odometry-the-default}

`VisualOdometry` sporer hvert nøglebillede mod det forrige:

1. **Features**: ORB, op til 1500 pr. billede, kun fundet på verdensmasken (se [Optagelse](reconstruction-capture.md#what-is-not-the-world)).
2. **Matches** mod det forrige nøglebillede: brute force, Hamming-afstand, krydstjekket (kun gensidigt bedste par).
3. **Løft til 3D**: det forrige billedes dybde er allerede i verdensenheder, så dets matchede pixels bliver til verdenspunkter.
4. **Placer kameraet**: `solvePnPRansac` blandt disse punkter (reprojektionsfejl 3 px, konfidens 0,999, 200 iterationer). Translationen kommer ud i de samme enheder, så **skalaen krydser mellemrummet**.
5. **Ankr dette billedes dybde**: dets egen forudsagte invers dybde tilpasses (`fit_scale`) mod PnP-inliers' dybder, og cyklussen gentages.

Det **første billede** er origo: identitetspose, og dets dybdes affine er enten jordkalibreringen nedenfor eller, uden en, identiteten (rekonstruktionen er da selvkonsistent, men uden enhed).

En pose kræver mindst **18 RANSAC-inliers** - klart flere end PnP's minimum på seks, fordi en løsning ud fra næsten for få punkter netop er den, der er sikkert forkert.

### Konfidens {#confidence}

Hvert placeret billede får en konfidens i 0..1, der vægter dets fusion og dets dækning:

| Pose fra | Konfidens |
|---|---|
| telemetri | 1,0 |
| en feed-forward-løsning | 0,85 |
| visuel sporing | `inliers / matches x min(1, inliers / 60)` |

### Når sporingen bryder {#when-tracking-breaks}

Et billede, der ikke kan placeres, rapporteres, aldrig gættes: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Der registreres ingen pose, og intet fusioneres. At fortsætte fra den sidste pose eller starte en frisk origo ville sætte den næste strækning af niveauet på en vilkårlig forskydning - en søm, der ser ud som rigtig geometri.

Efter et brud **relokaliseres** hvert nyt billede mod en database af tidligere nøglebilleder (hvert 4. sporede billede tilføjes, op til 120, det ældste droppes), det seneste først, med det samme match-og-PnP-trin. Indtil et lykkes, droppes billeder. Et gendannet billede fortsætter i samme koordinatramme. Gendannelser tælles og vises i vinduet (`N recovered`).

### Loop-lukning: slået fra {#loop-closure-off}

Den samme database understøtter loop-lukning: matchning mod nøglebilleder fra langt tidligere for at opdage et genbesøg og snappe sporet tilbage på det. **Den er slået fra som standard, og scanneren tænder den aldrig** (`Reconstructor(loop_closure=False)`). På gentagne omgivelser - en rallyetape, en korridor, en række træer - ligner hver strækning hver anden, og feature-matching bekræfter falske genbesøg, hvilket fastholder kameraet tæt på dets start, mens det kører videre. At gøre det ordentligt kræver stedgenkendelse (et bag-of-words-vokabular eller en lært deskriptor) og geometrisk verifikation mod et kort, og det er ikke bygget.

Når den er slået til fra kode, kræver en lukning: et nøglebillede mindst 60 nøglebilleder gammelt, inden for 6 m af den aktuelle pose, matchet med mindst 90 inliers, der flytter posen mere end 0,02 m og mindre end 6 m. Selv da erstatter den kun den aktuelle pose; den er ikke et posegraf og flytter ikke tidligere billeder eller fusioneret geometri.

## Telemetri-positioner {#telemetry-poses}

Med **Racing telemetry (Forza) -> Listen for position data** slået til kommer kamerastien fra Forzas Data Out i stedet for fra billederne (`ForzaPoseSource`):

- En tråd lytter på `127.0.0.1:<port>` (5300 som standard) med den samme layoutgenkendelse som optagerne ([Forza](telemetry-forza.md)); pakker bruges, mens `isRaceOn` er sat. En optaget port meldes, den hæves ikke: telemetri er en opgradering, og scanningen fortsætter visuelt.
- Hver pakke stemples med **det monotone tidspunkt, den ankom** - det samme ur, som optagelsen stempler billeder med. Spillets eget tidsstempel tæller fra noget uafhængigt, så det bruges ikke til flugtning. Et loopback-jitter på et par millisekunder er cirka 6 cm ved 200 km/t.
- En rullende 30-sekunders buffer holdes. Et billedes pose **interpoleres** fra prøverne på hver side af dets optagetidspunkt: positionen lineært, rotationen ved sfærisk interpolation (en blandet matrix er ikke en rotation og ville skævvride alle punkter). Over et hul længere end **0,35 s**, eller uden for bufferen, er der ingen pose.
- `pose_from_forza`: kameraet placeres ved bilen (et kædekamera's forskydning offentliggøres ikke). **Positionerne beholdes præcis, som spillet sender dem**: Forzas verden er allerede Y-op (x og z hen over kortet, y højden), som optagelsesfilerne og rutefilerne skriver den, så overfladen lander på de samme koordinater som de omgange, der er optaget over den. (En tidligere version byttede y og z for en "Z-op"-verden og lagde banen på siden.)
- Rotationen er yaw, derefter pitch, derefter roll, med fortegnene aflæst af optagede omgange: kørselsretningen `atan2(dx, dz)` er lig med yaw, den klatrede hældning er lig med minus pitch (positiv er snuden nedad), og roll er positiv, når den højre affjedring er sammentrykt (positiv sænker højre side). Bilens akser (x til højre, y op, z fremad) drejes så til kameraets (x til højre, y ned, z fremad) ved at vende y.
- Forzas verden er **venstrehåndet**, og kameraets ramme er det ikke, så den resulterende verden-til-kamera-matrix er en spejling (determinant -1), og scanningen bliver venstrehåndet ligesom omgangsfilerne. Interpolation påvirkes ikke (drejningen mellem to sådanne positioner er en egentlig rotation).
- Når et billede ikke har en telemetri-pose (et hul), falder rekonstruktøren tilbage til **visuel sporing** for det billede, med udgangspunkt i den sidste telemetri-pose, og vender tilbage til feedets positioner, så snart de svarer. PnP returnerer kun rotationer, så i en spejlet verden løses den med verden spejlet gennem z og spejlingen foldet tilbage; billedet lander i spillets koordinater. Først hvis også den visuelle sporing fejler, er billedet usporet.

### Dybdeskala fra telemetri {#depth-scale-from-telemetry}

Spillet siger, hvor kameraet er, ikke hvor langt noget er væk, så hvert billedes dybde skal stadig ankres - men ikke ved at kæde fra billede nul, hvis enhed er vilkårlig, mens positionerne er i meter. I stedet trianguleres features, der er matchet mellem det forrige og det aktuelle billede (mindst 8), **direkte fra de to kendte positioner**, i meter, og dybdekortet tilpasses punkterne foran kameraet. Hvert billede ankres mod telemetrien, så der ikke er nogen kæde, der kan drive.

Hvis de to positioner er mindre end **0,05 m** fra hinanden, er strålerne næsten parallelle, og triangulering er støj, så billedet forbliver uankret: placeret præcist, men ikke fusioneret ("positioned, but its depth has no scale yet"). Derfor tæller vinduet *placerede* og *fusionerede* billeder hver for sig.

## Skala {#scale}

Visuel odometri kæder den relative skala korrekt, men hele niveauet flyder stadig på én ukendt faktor. Depth Anythings relative output kommer i vilkårlige enheder, så hvis man lader det første billede være identiteten, placeres verden inden for meter fra kameraet i en vilkårlig størrelse.

`GroundCalibrator` fastlægger den faktor ud fra **hvor højt kameraet er over jorden**, målt på **det første nøglebillede** og, hvis det ikke har en brugbar jord, på de følgende:

- Kamerahøjde: **1,15 m** (en førers øjenhøjde) - vinduet bruger altid dette; scripts kan give 1,70 m (`WALKING_HEIGHT`, en stående spiller) eller `None` (ingen kalibrering).
- Jordprøve: rækkerne 62-92 % nede i billedet (under horisonten, over motorhjelmen eller våbnet) og kolonnerne 30-70 % på tværs (væk fra kanterne).
- Hver pixel dér med en brugbar forudsigelse løftes med dybden `1 / predicted` i netværkets enheder; punkter under den optiske akse giver en højde under kameraet. Deres median er kamerahøjden i netværksenheder, så `meter pr. enhed = 1,15 / median`, og billedets affine er `scale = 1 / meter pr. enhed`, forskydning 0.
- Stoles kun på med mindst 200 jordprøver og en **spredning** (median absolut afvigelse over median) under **0,60**.
- På det første nøglebillede bliver tilpasningen origoens enhed, så scanningen er i meter fra start. Når det første nøglebillede ikke har en brugbar jord, starter scanningen uden enhed, og hvert senere sporet nøglebillede forsøges, op til **30 billeder** i alt. Den første, der kalibrerer, giver *meter pr. enhed*: medianen over jordbåndet af den dybde, dens jord implicerer, over den dybde kæden gav det billede. Alt, der allerede er fusioneret, er i det første billedes enhed, så faktoren fødes ikke tilbage i kæden; den anvendes på hele niveauet (og på de markerede steder), når det skrives, og på den afstand, der vises imens. Voxelstørrelsen er så i det første billedes enheder, så dens størrelse i meter afviger fra indstillingen med den faktor.
- Efter 30 billeder uden jord forbliver scanningen uden enhed, og siger det.
- Med telemetri forsøges senere nøglebilleder ikke: dybden er ankret til telemetriens meter.

At være inden for ti procent af den rigtige størrelse er bedre end at være ude med en faktor tusind; telemetri, hvor den findes, gør det unødvendigt. Noten vises i vinduet under sporingslinjen som `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (med `found on frame N, so the level is scaled by F when it is written`, når den kom senere), `no usable ground in the first N frames - sizes are relative, not metres` eller `in metres, from the telemetry's positions`.

## Bundle adjustment og lange spor (ikke koblet til) {#bundle-adjustment-and-long-tracks-not-wired-in}

To dele findes til en fremtidig vinduesløser og er **ikke brugt af scanneren**:

- **`FeatureTracks`** holder featureidentitet over hundredvis af billeder med Lucas-Kanade-sporing (600 features, genseedet under 60 %, fremad-bagud-tolerance 1 px, nye features 10 px fra eksisterende), hvilket bundle adjustment har brug for - deskriptormatching mellem på hinanden følgende billeder giver kun par.
- **`bundle_adjust`** forfiner et vindue af positioner og punkter sammen med `scipy.optimize.least_squares` (trust region, soft-L1-tab med en 2 px skala, et eksplicit Jacobi-sparsitetsmønster, faste kameraer gendannet præcist). Testet mod kendt sandhed i `tests/test_bundle.py`.

`WindowedOdometry` kombinerer dem (12-nøglebilleds-vinduer, en løsning hvert 3. nøglebillede, de første to kameraer fastlåst, punkter med over 6 px fejl droppes, spring over 6 gange det seneste skridt afvises). Dens docstring noterer, at den på rigtig optagelse **kollapsede stien og var meget langsommere** end billede-til-billede-sporing, med skalafrihed (gauge) og en dybdebaseret start som kendte årsager og en tredje årsag uidentificeret. Så billede-til-billede-odometri forbliver standard; den sandsynlige rettelse, der er noteret i koden, er en to-visnings essentiel-matrix-start med basislinjen fastlagt ud fra jordplanskalibreringen.
