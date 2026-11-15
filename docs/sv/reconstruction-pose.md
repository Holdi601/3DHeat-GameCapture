---
title: "Kamerapose och skala"
nav_order: 4
lang: "sv"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kamerapose och skala {#camera-pose-and-scale}

En djupkarta säger hur långt bort saker är från *en* synpunkt. För att göra många av dem till en nivå måste man veta var varje synpunkt var och i vilka enheter. Den här sidan täcker de live-vägar; den offline-feed-forward-lösningen finns på [Offline-rekonstruktion](reconstruction-offline.md).

Kod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Kameramodellen {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` bygger en hålkamera från det **horisontella synfält** du ställer in i fönstret: `fx = (width / 2) / tan(fov / 2)`, kvadratiska pixlar (`fy = fx`) och huvudpunkten i bildrutans mitt. Ett spel publicerar inte sin projektion, så detta är det enda antagna talet: för smalt, och scenen ser djupare ut än den är. Den offline-vägen använder 65 grader.

En `Pose` lagras **världsfrån-kamera**: `rotation` (3 x 3) och `translation` = kamerans centrum i världen, vilket är vad banan, täckningskartan och overlayn alla vill ha.

## Visuell odometri (standard) {#visual-odometry-the-default}

`VisualOdometry` spårar varje nyckelbildruta mot den föregående:

1. **Särdrag**: ORB, upp till 1500 per bildruta, detekterade bara på världsmasken (se [Bildtagning](reconstruction-capture.md#what-is-not-the-world)).
2. **Matchningar** mot föregående nyckelbildruta: brute force, Hamming-avstånd, korskontrollerade (bara ömsesidigt bästa par).
3. **Lyft till 3D**: föregående bildrutas djup är redan i världsenheter, så dess matchade pixlar blir världspunkter.
4. **Placera kameran**: `solvePnPRansac` bland dessa punkter (återprojektionsfel 3 px, säkerhet 0,999, 200 iterationer). Translationen kommer ut i samma enheter, så **skalan går över luckan**.
5. **Ankra den här bildrutans djup**: dess egna förutsagda inversdjup anpassas (`fit_scale`) mot PnP-inlierns djup, och cykeln upprepas.

Den **första bildrutan** är origo: identitetspose, och dess djups affina är antingen markkalibreringen nedan eller, utan en, identiteten (rekonstruktionen är då självkonsistent men utan enheter).

En pose behöver minst **18 RANSAC-inlier**. Det är klart fler än PnP:s minimum på sex, eftersom en lösning från knappt tillräckligt många punkter är precis den som är självsäkert fel.

### Säkerhet {#confidence}

Varje placerad bildruta får en säkerhet i 0..1 som viktar dess fusion och täckning:

| Pose från | Säkerhet |
|---|---|
| telemetri | 1,0 |
| en feed-forward-lösning | 0,85 |
| visuell spårning | `inliers / matches x min(1, inliers / 60)` |

### När spårningen bryts {#when-tracking-breaks}

En bildruta som inte kan placeras rapporteras, aldrig gissas: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Ingen pose registreras, och ingenting fusioneras. Att fortsätta från den sista posen, eller starta ett nytt origo, skulle lägga nästa sträcka av nivån på en godtycklig förskjutning: en söm som ser ut som verklig geometri.

Efter ett avbrott **relokaliseras** varje ny bildruta mot en databas över tidigare nyckelbildrutor (var fjärde spårad bildruta läggs till, upp till 120, äldsta släpps), senaste först, med samma matchning-och-PnP-steg. Tills en lyckas släpps bildrutor. En återfunnen bildruta fortsätter i samma koordinatsystem. Återhämtningar räknas och visas i fönstret (`N recovered`).

### Loop closure: av {#loop-closure-off}

Samma databas stöder loop closure: matchning mot nyckelbildrutor från långt tidigare, för att upptäcka ett återbesök och snäppa banan tillbaka på det. **Den är av som standard, och skannern slår aldrig på den** (`Reconstructor(loop_closure=False)`). På repetitiva miljöer (en rallysträcka, en korridor, en rad träd) ser varje sträcka ut som varje annan, och särdragsmatchning bekräftar falska återbesök, vilket fäster kameran nära där den började medan den kör vidare. Att göra det ordentligt kräver platsigenkänning (ett bag-of-words-vokabulär eller en inlärd deskriptor) och geometrisk verifiering mot en karta, vilket inte är byggt.

När den aktiveras från kod kräver en closure: en nyckelbildruta minst 60 nyckelbildrutor gammal, inom 6 m från nuvarande pose, matchad med minst 90 inlier, som flyttar posen mer än 0,02 m och mindre än 6 m. Även då ersätter den bara den aktuella posen. Den är ingen posegraf och flyttar inte tidigare bildrutor eller fusionerad geometri.

## Telemetriposer {#telemetry-poses}

Med **Racing telemetry (Forza) -> Listen for position data** på kommer kamerabanan från Forzas Data Out i stället för från bilderna (`ForzaPoseSource`):

- En tråd lyssnar på `127.0.0.1:<port>` (5300 som standard) med samma layoutdetektering som inspelarna ([Forza](telemetry-forza.md)). Paket används medan `isRaceOn` är satt. En upptagen port rapporteras, inte kastas: telemetri är en uppgradering och skanningen fortsätter visuellt.
- Varje paket stämplas med **den monotona tiden då det kom fram**, samma klocka som fångsten stämplar bildrutor med. Spelets egen tidsstämpel räknar från något orelaterat, så den används inte för linjering. En till två millisekunders jitter på loopback är ungefär 6 cm vid 200 km/h.
- En rullande 30-sekundersbuffer hålls. En bildrutas pose **interpoleras** från proven på var sida om dess fångsttid: position linjärt, rotation med sfärisk interpolation (en blandad matris är inte en rotation och skulle snedvrida varje punkt). Över ett gap längre än **0,35 s**, eller utanför bufferten, finns ingen pose.
- `pose_from_forza`: kameran placeras vid bilen (en chase-kameras förskjutning publiceras inte). **Positionerna behålls exakt som spelet skickar dem**: Forzas värld är redan Y-upp (x och z över kartan, y höjden), vilket är hur varvfilerna och ruttfilerna skriver det, så ytan landar på samma koordinater som varven inspelade över den. (En tidigare version bytte y och z för en "Z-upp"-värld och lade banan på sidan.)
- Rotationen är gir, sedan stigning, sedan rulle, med sinnena lästa från inspelade varv: färdriktningen `atan2(dx, dz)` är lika med girningen, den uppförda lutningen är lika med minus stigningen (positiv är nos ner), och rullningen är positiv när den högra fjädringen är ihoptryckt (positiv sänker högra sidan). Bilens axlar (x höger, y upp, z framåt) vrids sedan till kamerans (x höger, y ner, z framåt) genom att vända y.
- Forzas värld är **vänsterhänt** och kamerans ram inte, så den resulterande världsfrån-kamera-matrisen är en spegling (determinant -1). Skanningen blir vänsterhänt som varvfilerna. Interpolation påverkas inte, eftersom vridningen mellan två sådana poser är en riktig rotation.
- När en bildruta saknar telemetripose (ett gap) faller rekonstruktören tillbaka på **visuell spårning** för den bildrutan, fortsätter från den sista telemetriposen, och går tillbaka till feedens poser så snart den svarar. PnP returnerar bara rotationer, så i en speglad värld löses den med världen speglad genom z och spegelvändningen vikt tillbaka. Bildrutan landar i spelets koordinater. Först om den visuella spårningen också misslyckas är bildrutan ospårad.

### Djupskala från telemetri {#depth-scale-from-telemetry}

Spelet säger var kameran är, inte hur långt bort något är, så varje bildrutas djup behöver ändå ankras. Men det görs inte genom att kedja från bildruta noll, vars enhet är godtycklig medan posena är i meter. I stället trianguleras särdrag som matchats mellan den föregående och den aktuella bildrutan (minst 8) **direkt från de två kända poserna**, i meter, och djupkartan anpassas till punkterna framför kameran. Varje bildruta ankras mot telemetrin, så det finns ingen kedja som driver.

Om de två poserna ligger närmare än **0,05 m** isär är strålarna nästan parallella och triangulering är brus. Då lämnas bildrutan oankrad: placerad exakt, men inte fusionerad ("positioned, but its depth has no scale yet"). Det är därför fönstret räknar *placerade* och *fusionerade* bildrutor var för sig.

## Skala {#scale}

Visuell odometri kedjar relativ skala korrekt, men hela nivån flyter fortfarande på en okänd faktor. Depth Anythings relativa utdata kommer i godtyckliga enheter, så om man lämnar första bildrutan vid identiteten hamnar världen inom meter från kameran i en godtycklig storlek.

`GroundCalibrator` fäster den faktorn utifrån **hur högt kameran är över marken**, mätt på den **första nyckelbildrutan** och, när den inte har någon användbar mark, på de följande:

- Kamerahöjd: **1,15 m** (en förares ögonhöjd). Fönstret använder alltid detta; skript kan ge 1,70 m (`WALKING_HEIGHT`, en stående spelare) eller `None` (ingen kalibrering).
- Markprov: rader 62-92 % ner i bilden (under horisonten, ovanför motorhuven eller vapnet) och kolumner 30-70 % över (bort från kanterna).
- Varje pixel där med en användbar förutsägelse lyfts med djup `1 / predicted` i nätverkets enheter. Punkter under den optiska axeln ger en höjd under kameran. Deras median är kamerans höjd i nätverksenheter, så `metres per unit = 1.15 / median`, och bildrutans affina är `scale = 1 / metres_per_unit`, shift 0.
- Litas på bara med minst 200 markprov och en **spridning** (medianabsolutavvikelse över median) under **0,60**.
- På den första nyckelbildrutan blir anpassningen origots enhet, så skanningen är i meter från början. När den första nyckelbildrutan inte har någon användbar mark startar skanningen utan enheter, och varje senare spårad nyckelbildruta prövas, upp till **30 bildrutor** totalt. Den första som kalibrerar ger *meter per enhet*: medianen, över markbandet, av djupet som dess mark ger över djupet kedjan gav för den bildrutan. Allt redan fusionerat är i första bildrutans enhet, så faktorn matas inte tillbaka i kedjan. Den tillämpas i stället på hela nivån (och på de markerade platserna) när den skrivs, och på avståndet som visas under tiden. Voxelstorleken är då i första bildrutans enheter, så dess storlek i meter skiljer sig från inställningen med den faktorn.
- Efter 30 bildrutor utan mark förblir skanningen utan enheter, och säger det.
- Med telemetri prövas inte senare nyckelbildrutor: djupet ankras till telemetrins meter.

Att vara inom tio procent av den verkliga storleken är bättre än att vara fel med en faktor tusen. Telemetri, där den finns, gör det onödigt. Notisen visas i fönstret under spårningsraden, som `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (med `found on frame N, so the level is scaled by F when it is written` när den kom senare), `no usable ground in the first N frames - sizes are relative, not metres`, eller `in metres, from the telemetry's positions`.

## Bundle-justering och långa spår (inte inkopplat) {#bundle-adjustment-and-long-tracks-not-wired-in}

Två delar finns för en framtida fönsterlösare och **används inte av skannern**:

- **`FeatureTracks`** behåller särdragsidentitet över hundratals bildrutor med Lucas-Kanade-spårning (600 särdrag, återsådda under 60 %, framåt-bakåt-tolerans 1 px, nya särdrag 10 px från befintliga). Bundle-justering behöver det, eftersom deskriptormatchning mellan på varandra följande bildrutor bara ger par.
- **`bundle_adjust`** förfinar ett fönster av poser och punkter tillsammans med `scipy.optimize.least_squares` (förtroendeområde, soft-L1-förlust med en 2 px-skala, ett explicit Jacobian-glesmönster, fasta kameror återställda exakt). Testad mot känd sanning i `tests/test_bundle.py`.

`WindowedOdometry` kombinerar dem (12-nyckelbildrutors fönster, en lösning var tredje nyckelbildruta, de två första kamerorna fixerade, punkter med över 6 px fel släpps, hopp större än 6 gånger det senaste steget vägras). Dess docstring noterar att den på riktig film **kollapsade banan och var mycket långsammare** än bildruta-till-bildruta-spårning, med frihetsgrad i skalan (gauge freedom) och ett djupbaserat start som kända orsaker och en tredje orsak som inte identifierats. Så bildruta-till-bildruta-odometri är kvar som standard. Den troliga åtgärden som nämns i koden är en två-vy-bootstrap med essentiell matris och basen fixerad från markplanskalibreringen.
