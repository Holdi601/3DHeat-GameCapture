---
title: "Cameraposities en schaal"
nav_order: 4
lang: "nl"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Cameraposities en schaal {#camera-pose-and-scale}

Een diepte-kaart zegt hoe ver dingen zijn van *een* gezichtspunt. Om er veel tot één level van te maken, moet je weten waar elk gezichtspunt was, en in welke eenheden. Deze pagina gaat over de live paden; de offline oplossing met feed-forward staat op [Offline reconstructie](reconstruction-offline.md).

Code: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py), [`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py), [`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py), [`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py), [`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py), [`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Het cameramodel {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` bouwt een pinhole-camera uit het **horizontale gezichtsveld** dat je in het venster instelt: `fx = (width / 2) / tan(fov / 2)`, vierkante pixels (`fy = fx`), het hoofdpunt in het midden van het frame. Een spel publiceert zijn projectie niet, dus is dit het ene aangenomen getal: te smal en de scène lijkt dieper dan hij is. Het offline pad gebruikt 65 graden.

Een `Pose` wordt opgeslagen als **wereld-van-camera**: `rotation` (3 x 3) en `translation` = het middelpunt van de camera in de wereld, wat de baan, de dekkingskaart en de overlay allemaal willen.

## Visuele odometrie (de standaard) {#visual-odometry-the-default}

`VisualOdometry` volgt elk keyframe ten opzichte van het vorige:

1. **Features**: ORB, tot 1500 per frame, alleen gevonden op het wereldmasker (zie [Opname](reconstruction-capture.md#what-is-not-the-world)).
2. **Matches** met het vorige keyframe: brute force, Hamming-afstand, kruiscontrole (alleen wederzijds beste paren).
3. **Omhoog naar 3D**: de diepte van het vorige frame is al in wereldeenheden, dus worden de gematchte pixels wereldpunten.
4. **De camera plaatsen**: `solvePnPRansac` tussen die punten (herprojectiefout 3 px, betrouwbaarheid 0,999, 200 iteraties). De translatie komt in dezelfde eenheden uit, dus **de schaal steekt de kloof over**.
5. **De diepte van dit frame verankeren**: de eigen voorspelde inverse diepte wordt gefit (`fit_scale`) op de dieptes van de PnP-inliers, en de cyclus herhaalt zich.

Het **eerste frame** is de oorsprong: identiteitspose, en zijn diepte-affiene is ofwel de grondkalibratie hieronder of, zonder die, de identiteit (de reconstructie is dan intern consistent maar zonder eenheden).

Een pose heeft minstens **18 RANSAC-inliers** nodig - duidelijk meer dan het minimum van zes van PnP, want een oplossing uit nauwelijks genoeg punten is precies degene die zelfverzekerd fout is.

### Confidentie {#confidence}

Elk geplaatst frame krijgt een confidentie tussen 0 en 1 die zijn samenvoegen en zijn dekking weegt:

| Pose uit | Confidentie |
|---|---|
| telemetrie | 1,0 |
| een feed-forward-oplossing | 0,85 |
| visuele tracking | `inliers / matches x min(1, inliers / 60)` |

### Wanneer tracking breekt {#when-tracking-breaks}

Een frame dat niet geplaatst kan worden, wordt gemeld, nooit geraden: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Er wordt geen pose vastgelegd, en er wordt niets samengevoegd. Doorgaan vanaf de laatste pose, of een nieuwe oorsprong beginnen, zou het volgende stuk level op een willekeurige verschuiving zetten - een naad die eruitziet als echte geometrie.

Na een breuk wordt elk nieuw frame **gerelocaliseerd** tegen een database van eerdere keyframes (elk vierde gevolgde frame wordt toegevoegd, tot 120, het oudste valt weg), het meest recente eerst, met dezelfde match-en-PnP-stap. Totdat er één slaagt, worden frames weggegooid. Een gerelocaliseerd frame gaat verder in hetzelfde coördinatenstelsel. Herlocalisaties worden geteld en in het venster getoond (`N recovered`).

### Loop-sluiting: uit {#loop-closure-off}

Dezelfde database ondersteunt loop-sluiting: matchen tegen keyframes van veel eerder om een terugkeer te herkennen en het spoor daarop terug te snappen. **Het staat standaard uit, en de scanner zet het nooit aan** (`Reconstructor(loop_closure=False)`). Op repeterend landschap - een rallyetappe, een gang, een rij bomen - lijkt elk stuk op elk ander, en bevestigt feature-matching valse terugkeren, wat de camera dicht bij het startpunt vastpint terwijl hij verder rijdt. Het goed doen vraagt om plaatsherkenning (een bag-of-words-vocabulaire of een geleerde descriptor) en geometrische verificatie tegen een kaart, en dat is niet gebouwd.

Als het vanuit code wordt aangezet, heeft een sluiting nodig: een keyframe van minstens 60 keyframes oud, binnen 6 m van de huidige pose, gematcht met minstens 90 inliers, die de pose verschuift met meer dan 0,02 m en minder dan 6 m. Zelfs dan vervangt het alleen de huidige pose; het is geen posegrafiek en verplaatst geen eerdere frames of samengevoegde geometrie.

## Telemetrieposes {#telemetry-poses}

Met **Racing telemetry (Forza) -> Listen for position data** aan, komt het cameraspoor uit Forza's Data Out in plaats van uit de beelden (`ForzaPoseSource`):

- Een thread luistert op `127.0.0.1:<port>` (standaard 5300) met dezelfde indelingsherkenning als de opnemers ([Forza](telemetry-forza.md)); pakketten worden gebruikt zolang `isRaceOn` aan staat. Een bezette poort wordt gemeld, niet opgeworpen: telemetrie is een verbetering en de scan gaat visueel door.
- Elk pakket krijgt de **monotone tijd waarop het binnenkwam** als stempel - dezelfde klok waarmee de opname frames stempelt. De eigen tijdstempel van het spel telt vanaf iets wat er niets mee te maken heeft, dus wordt die niet voor uitlijning gebruikt. Een jitter van een of twee milliseconden op de loopback is bij 200 km/u ongeveer 6 cm.
- Er wordt een rollende buffer van 30 seconden bijgehouden. De pose van een frame wordt **geïnterpoleerd** uit de metingen aan weerszijden van zijn opnametijd: positie lineair, rotatie sferisch (een gemengde matrix is geen rotatie en zou elk punt scheef trekken). Over een gat langer dan **0,35 s**, of buiten de buffer, is er geen pose.
- `pose_from_forza`: de camera wordt bij de auto geplaatst (de offset van een achtervolgingscamera wordt niet gepubliceerd). **Posities blijven precies zoals het spel ze stuurt**: de wereld van Forza is al Y-omhoog (x en z over de kaart, y de hoogte), zoals de rondenbestanden en routebestanden het schrijven, dus landt het oppervlak op dezelfde coördinaten als de ronden die erover zijn opgenomen. (Een eerdere versie wisselde y en z voor een "Z-omhoog"-wereld en legde het spoor op zijn zij.)
- De rotatie is gier, dan pitch, dan roll, met de zinnen gelezen uit opgenomen ronden: de rijrichting `atan2(dx, dz)` is gelijk aan de gier, de klimhelling is gelijk aan min de pitch (positief is neus omlaag), en de roll is positief als de rechter ophangingsveer is ingedrukt (positief drukt de rechterkant omlaag). De assen van de auto (x naar rechts, y omhoog, z vooruit) worden daarna omgezet naar die van de camera (x naar rechts, y omlaag, z vooruit) door y om te keren.
- De wereld van Forza is **linkshandig** en het frame van de camera niet, dus is de resulterende wereld-van-camera-matrix een spiegeling (determinant -1), en komt de scan linkshandig uit zoals de rondenbestanden. Interpolatie wordt niet beïnvloed (de draai tussen twee zulke posen is een echte rotatie).
- Wanneer een frame geen telemetriepose heeft (een gat), valt de reconstructor voor dat frame terug op **visuele tracking**, vanaf de laatste telemetriepose, en keert terug naar de posities van de feed zodra die weer antwoordt. PnP levert alleen rotaties, dus in een gespiegelde wereld wordt het opgelost met de wereld gespiegeld door z en wordt de spiegeling er weer in gevouwen; het frame komt in de coördinaten van het spel terecht. Alleen als visuele tracking ook faalt, is het frame niet getrackt.

### Diepteschaal uit telemetrie {#depth-scale-from-telemetry}

Het spel zegt waar de camera is, niet hoe ver iets weg is, dus heeft de diepte van elk frame nog steeds een verankering nodig - maar niet door te ketenen vanaf frame nul, waarvan de eenheid willekeurig is terwijl de posities in meters zijn. In plaats daarvan worden features die tussen het vorige en het huidige frame gematcht zijn (minstens 8) **direct getrianguleerd uit de twee bekende posities**, in meters, en wordt de diepte-kaart gefit op de punten voor de camera. Elk frame wordt tegen de telemetrie verankerd, dus is er geen keten die kan wegdrijven.

Als de twee posities minder dan **0,05 m** uit elkaar liggen, zijn de stralen bijna evenwijdig en is triangulatie ruis, dus blijft het frame niet verankerd: exact geplaatst, maar niet samengevoegd ("positioned, but its depth has no scale yet"). Daarom telt het venster geplaatste en samengevoegde frames apart.

## Schaal {#scale}

Visuele odometrie ketent de relatieve schaal correct, maar het hele level zweeft op één onbekende factor. De relatieve uitvoer van Depth Anything komt in willekeurige eenheden uit, dus als het eerste frame op de identiteit blijft, staat de wereld binnen meters van de camera op een willekeurige grootte.

`GroundCalibrator` legt die factor vast uit **hoe hoog de camera boven de grond zit**, gemeten op het **eerste keyframe** en, als dat geen bruikbare grond heeft, op de volgende:

- Cameradhoogte: **1,15 m** (de ooglijn van een bestuurder) - het venster gebruikt dit altijd; scripts kunnen 1,70 m (`WALKING_HEIGHT`, een rechtopstaande speler) of `None` (geen kalibratie) meegeven.
- Grondmonster: rijen op 62-92% van de hoogte van het frame (onder de horizon, boven de motorkap of het wapen) en kolommen op 30-70% van de breedte (weg van de bermen).
- Elke pixel daar met een bruikbare voorspelling wordt opgetild met diepte `1 / predicted` in de eenheden van het netwerk; punten onder de optische as geven een hoogte onder de camera. Hun mediaan is de cameradhoogte in netwerkeenheden, dus is `meter per eenheid = 1,15 / mediaan`, en is de affiene van het frame `scale = 1 / meter_per_eenheid`, shift 0.
- Alleen vertrouwd met minstens 200 grondmonsters en een **spreiding** (mediane absolute afwijking over mediaan) onder **0,60**.
- Op het eerste keyframe wordt de fit de eenheid van de oorsprong, zodat de scan vanaf het begin in meters is. Heeft het eerste keyframe geen bruikbare grond, dan start de scan zonder eenheden en wordt elk latere getraceerd keyframe geprobeerd, tot in totaal **30 frames**. De eerste die kalibreert, geeft *meter per eenheid*: de mediaan, over de grondband, van de diepte die de grond impliceert gedeeld door de diepte die de keten voor dat frame gaf. Alles wat al is samengevoegd, is in de eenheid van het eerste frame, dus wordt de factor niet teruggekoppeld in de keten; hij wordt op het hele level toegepast (en op de gemarkeerde plekken) wanneer het wordt geschreven, en op de afstand die ondertussen wordt getoond. De voxelgrootte is dan in de eenheid van het eerste frame, dus verschilt haar grootte in meters van de instelling met die factor.
- Na 30 frames zonder grond blijft de scan zonder eenheden, en dat wordt gemeld.
- Met telemetrie worden latere keyframes niet geprobeerd: de diepte is verankerd aan de meters van de telemetrie.

Binnen tien procent van de werkelijke grootte zitten is beter dan met een factor duizend ernaast; telemetrie maakt het, waar beschikbaar, overbodig. De notitie wordt in het venster onder de trackingregel getoond, als `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (met `found on frame N, so the level is scaled by F when it is written` als het later kwam), `no usable ground in the first N frames - sizes are relative, not metres`, of `in metres, from the telemetry's positions`.

## Bundle-aanpassing en lange sporen (niet aangesloten) {#bundle-adjustment-and-long-tracks-not-wired-in}

Twee onderdelen bestaan voor een toekomstige vensteroplosser en worden **door de scanner niet gebruikt**:

- **`FeatureTracks`** houdt de identiteit van features over honderden frames bij met Lucas-Kanade-tracking (600 features, opnieuw gezaaid onder 60%, voorwaarts-achterwaartse tolerantie 1 px, nieuwe features 10 px van bestaande), wat bundle-aanpassing nodig heeft - descriptor-matching tussen opeenvolgende frames levert alleen paren op.
- **`bundle_adjust`** verfijnt een venster van posen en punten samen met `scipy.optimize.least_squares` (trust region, soft-L1-verlies met een schaal van 2 px, een expliciet Jacobiaanpatroon van ijlheid, vaste camera's exact hersteld). Getest tegen bekende waarheid in `tests/test_bundle.py`.

`WindowedOdometry` combineert ze (vensters van 12 keyframes, een oplossing elke 3 keyframes, de eerste twee camera's vast, punten met meer dan 6 px fout gedropt, sprongen boven 6 keer de recente stap geweigerd). Zijn docstring vermeldt dat het op echte beelden **het spoor deed instorten en veel trager was** dan frame-naar-frame-tracking, met te veel vrijheid in de schaal en een op diepte gebaseerde opstart als bekende oorzaken en een derde oorzaak die niet is geïdentificeerd. Dus blijft frame-naar-frame-odometrie de standaard; de waarschijnlijke oplossing die in de code wordt genoemd, is een tweeweergave-opstart met de essentiële matrix en de basislijn vastgelegd vanuit de grondvlakkalibratie.
