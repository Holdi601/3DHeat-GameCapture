---
title: "Poza e kamerës dhe shkalla"
nav_order: 4
lang: "sq"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poza e kamerës dhe shkalla {#camera-pose-and-scale}

Një hartë thellësie tregon sa larg janë gjërat nga *një* pikëshikim. Për ta kthyer shumë prej tyre në një nivel
duhet të dihet ku ishte çdo pikëshikim, dhe në çfarë njësish. Kjo faqe mbulon rrugët e drejtpërdrejta;
zgjidhja offline feed-forward është te [Rindërtimi offline](reconstruction-offline.md).

Kodi: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Modeli i kamerës {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` ndërton një kamerë vrimë-gjilpëre nga **fushëpamja
horizontale** që vendos në dritare: `fx = (width / 2) / tan(fov / 2)`, piksele katrorë (`fy = fx`), pika
kryesore në qendër të kuadrit. Një lojë nuk e publikon projeksionin e saj, prandaj ky është
numri i vetëm i supozuar: shumë i ngushtë dhe skena lexohet më e thellë se është. Rruga offline përdor
65 gradë.

Një `Pose` ruhet **bota-nga-kamera**: `rotation` (3 x 3) dhe `translation` = qendra e kamerës
në botë, që është ajo që duan trajektorja, harta e mbulimit dhe overlay.

## Odometria vizuale (e paracaktuara) {#visual-odometry-the-default}

`VisualOdometry` ndjek çdo kuadër kyç kundrejt të mëparshmit:

1. **Tiparet**: ORB, deri në 1500 për kuadër, të zbuluara vetëm në maskën e botës (shih
   [Kapja](reconstruction-capture.md#what-is-not-the-world)).
2. **Përputhjet** me kuadrin kyç të mëparshëm: forcë brutale, largësi Hamming, me kontroll të kryqëzuar (vetëm çiftet
   reciprokisht më të mira).
3. **Ngritja në 3D**: thellësia e kuadrit të mëparshëm është tashmë në njësi botërore, kështu që pikselat e tij
   të përputhur bëhen pika botërore.
4. **Vendosja e kamerës**: `solvePnPRansac` mes atyre pikave (gabim riprojektimi 3 px,
   besueshmëri 0.999, 200 përsëritje). Zhvendosja del në të njëjtat njësi, kështu që **shkalla kalon
   hendekun**.
5. **Ankorimi i thellësisë së këtij kuadri**: thellësia e tij e anasjellë e parashikuar përshtatet (`fit_scale`)
   me thellësitë e inlier-ave të PnP, dhe cikli përsëritet.

**Kuadri i parë** është origjina: poza identitet, dhe afini i thellësisë së tij është ose kalibrimi i tokës
më poshtë ose, pa të, identiteti (rindërtimi është atëherë i vetëkonsistent por pa njësi).

Një pozë ka nevojë për të paktën **18 inlier-a RANSAC** - qartësisht më shumë se minimumi i PnP prej gjashtë, pasi
një zgjidhje nga pikë që mezi mjaftojnë është saktësisht ajo që gabon me besim.

### Besueshmëria {#confidence}

Çdo kuadër i vendosur merr një besueshmëri në 0..1 që peshon bashkimin dhe mbulimin e tij:

| Poza nga | Besueshmëria |
|---|---|
| telemetria | 1.0 |
| një zgjidhje feed-forward | 0.85 |
| ndjekja vizuale | `inliers / matches x min(1, inliers / 60)` |

### Kur prishet ndjekja {#when-tracking-breaks}

Një kuadër që nuk mund të vendoset raportohet, nuk hamendësohet kurrë: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Nuk regjistrohet asnjë pozë,
dhe asgjë nuk bashkohet. Të vazhdosh nga poza e fundit, ose të nisësh një origjinë të re, do ta vendoste
pjesën tjetër të nivelit në një zhvendosje arbitrare - një tegel që duket si gjeometri e vërtetë.

Pas një prishjeje, çdo kuadër i ri **rilokalizohet** kundrejt një baze të dhënash kuadrosh kyç të kaluar (çdo
kuadër i 4-t i ndjekur shtohet, deri në 120, më i vjetri hidhet), më i fundit i pari, me të njëjtin
hap përputhje-dhe-PnP. Derisa një të ketë sukses, kuadrot hidhen tej. Një kuadër i rikuperuar vazhdon në të
njëjtën kornizë koordinative. Rikuperimet numërohen dhe shfaqen në dritare (`N recovered`).

### Mbyllja e ciklit: e fikur {#loop-closure-off}

E njëjta bazë të dhënash mbështet mbylljen e ciklit: përputhje me kuadro kyç shumë më të hershëm për të
zbuluar një rikthim dhe për ta kthyer pistën mbi të. **Është e fikur si e paracaktuar, dhe skaneri nuk
e ndez kurrë** (`Reconstructor(loop_closure=False)`). Në peizazhe të përsëritura - një etapë rali, një
korridor, një rresht pemësh - çdo shtrirje duket si çdo tjetër dhe përputhja e tipareve konfirmon
rikthime të rreme, që e mbërthen kamerën afër ku filloi ndërsa ajo vazhdon. Për ta bërë siç duhet duhet njohje vendesh
(një fjalor bag-of-words ose një përshkrues i mësuar) dhe verifikim gjeometrik kundrejt një harte, që nuk është ndërtuar.

Kur ndizet nga kodi, një mbyllje ka nevojë për: një kuadër kyç të paktën 60 kuadro kyç të vjetër, brenda 6 m nga
poza aktuale, të përputhur me të paktën 90 inlier-a, që e zhvendos pozën me më shumë se 0.02 m dhe më
pak se 6 m. Edhe atëherë vetëm zëvendëson pozën aktuale; nuk është graf pozash dhe nuk lëviz
kuadrot e mëparshëm ose gjeometrinë e bashkuar.

## Pozat nga telemetria {#telemetry-poses}

Me **Racing telemetry (Forza) -> Listen for position data** të ndezur, rruga e kamerës vjen nga
Data Out i Forza dhe jo nga pamjet (`ForzaPoseSource`):

- Një fill dëgjon te `127.0.0.1:<port>` (5300 si e paracaktuar) me të njëjtin zbulim strukture si
  regjistruesit ([Forza](telemetry-forza.md)); paketat përdoren ndërsa `isRaceOn` është i vendosur. Një portë e zënë
  raportohet, nuk ngre përjashtim: telemetria është përmirësim dhe skanimi vazhdon vizualisht.
- Çdo paketë vuloset me **kohën monotone kur arriti** - i njëjti orar me të cilin kapja vulos
  kuadrot. Vula kohore e vetë lojës numëron nga diçka e palidhur, prandaj nuk përdoret për rreshtim. Dridhja e loopback prej
  një a dy milisekondash është rreth 6 cm në 200 km/h.
- Mbahet një bufer rrjedhës 30-sekondash. Poza e një kuadri **interpolohet** nga kampionët në të dyja anët e
  kohës së kapjes: pozicioni në mënyrë lineare, rotacioni me interpolim sferik (një matricë e përzier nuk është rotacion
  dhe do t'i anonte të gjitha pikat). Përtej një hendeku më të gjatë se **0.35 s**, ose jashtë buferit,
  nuk ka pozë.
- `pose_from_forza`: kamera vendoset te makina (zhvendosja e një kamere ndjekëse nuk publikohet).
  **Pozicionet mbahen saktësisht siç i dërgon loja**: bota e Forza ka Y lart që tani (x dhe z
  përgjatë hartës, y lartësia), siç e shkruajnë skedarët e xhirove dhe të rrugës, kështu që
  sipërfaqja bie në të njëjtat koordinata me xhirot e regjistruara mbi të. (Një version i hershëm këmbente
  y dhe z për një botë "Z lart" dhe e shtriu pistën në anë.)
- Rotacioni është yaw, pastaj pitch, pastaj roll, me kuptimet e lexuara nga xhiro të regjistruara: drejtimi
  i udhëtimit `atan2(dx, dz)` është i barabartë me yaw, pjerrësia e ngjitur është minus pitch
  (pozitiv është hunda poshtë), dhe roll është pozitiv kur pezullimi i djathtë është i ngjeshur
  (pozitiv ul anën e djathtë). Akset e makinës (x djathtas, y lart, z përpara) kthehen pastaj në ato të
  kamerës (x djathtas, y poshtë, z përpara) duke përmbysur y.
- Bota e Forza është **e majtë** dhe korniza e kamerës jo, kështu që matrica bota-nga-kamera që rezulton
  është një pasqyrim (përcaktor -1), dhe skanimi del i majtë si skedarët e xhirove. Interpolimi nuk preket
  (kthesa mes dy pozave të tilla është rotacion i vërtetë).
- Kur një kuadër nuk ka pozë telemetrie (një hendek), rindërtuesi kalon te **ndjekja vizuale**
  për atë kuadër, duke vazhduar nga poza e fundit e telemetrisë, dhe kthehet te pozat e burimit sapo
  ai përgjigjet. PnP kthen vetëm rotacione, kështu që në një botë të pasqyruar zgjidhet me
  botën të pasqyruar nëpër z dhe pasqyrën të palosur prapë; kuadri bie në koordinatat e lojës.
  Vetëm nëse edhe ndjekja vizuale dështon, kuadri mbetet i pandjekur.

### Shkalla e thellësisë nga telemetria {#depth-scale-from-telemetry}

Loja tregon ku është kamera, jo sa larg është ndonjë gjë, kështu që thellësia e çdo kuadri ka ende nevojë
për ankorim - por jo duke zinxhiruar nga kuadri zero, njësia e të cilit është arbitrare ndërsa pozat
janë në metra. Në vend të kësaj, tiparet e përputhura mes kuadrit të mëparshëm dhe atij aktual (të paktën
8) **triangularizohen drejtpërdrejt nga dy pozat e njohura**, në metra, dhe harta e thellësisë
përshtatet me pikat përpara kamerës. Çdo kuadër ankorohet kundrejt telemetrisë, kështu që
nuk ka zinxhir që të shmanget.

Nëse dy pozat janë më pak se **0.05 m** larg njëra tjetrës rrezet janë pothuajse paralele dhe triangularizimi është
zhurmë, prandaj kuadri lihet pa ankoruar: i pozicionuar saktësisht, por jo i bashkuar ("positioned, but its
depth has no scale yet"). Kjo është arsyeja pse dritarja numëron kuadrot *e vendosur* dhe *e bashkuar* veçmas.

## Shkalla {#scale}

Odometria vizuale zinxhiron shkallën relative saktë, por gjithë niveli noton prapë mbi një faktor të vetëm të panjohur.
Dalja relative e Depth Anything del në njësi arbitrare, kështu që të lësh kuadrin e parë në identitet e vendos
botën brenda metrave nga kamera me një madhësi arbitrare.

`GroundCalibrator` e fikson atë faktor nga **sa lart është kamera mbi tokë**, matur në
**kuadrin e parë kyç** dhe, kur ai nuk ka tokë të përdorshme, në ata që vijojnë:

- Lartësia e kamerës: **1.15 m** (vija e syrit të një shoferi) - dritarja gjithmonë këtë përdor; skriptet mund të
  japin 1.70 m (`WALKING_HEIGHT`, një lojtar në këmbë) ose `None` (pa kalibrim).
- Kampioni i tokës: rreshtat 62-92% poshtë kuadrit (nën horizont, mbi kapakun e motorit ose armën) dhe
  kolonat 30-70% përtej (larg bankinave).
- Çdo piksel aty me parashikim të përdorshëm ngrihet me thellësi `1 / predicted` në njësitë e
  rrjetit; pikat poshtë aksit optik japin një lartësi nën kamerë. Mediana e tyre është
  lartësia e kamerës në njësi rrjeti, kështu që `metres per unit = 1.15 / median`, dhe afini i kuadrit është
  `scale = 1 / metres_per_unit`, shift 0.
- Besohet vetëm me të paktën 200 kampionë toke dhe një **shpërndarje** (devijimi absolut medianë mbi
  medianën) nën **0.60**.
- Në kuadrin e parë kyç përshtatja bëhet njësia e origjinës, kështu që skanimi është në metra që nga
  fillimi. Kur kuadri i parë kyç nuk ka tokë të përdorshme, skanimi nis pa njësi dhe çdo kuadër kyç
  i ndjekur më pas provohet, deri në **30 kuadro** gjithsej. I pari që kalibrohet jep
  *metra për njësi*: mediana, mbi brezin e tokës, e thellësisë që nënkupton toka e tij mbi
  thellësinë që zinxhiri i dha atij kuadri. Gjithçka e bashkuar tashmë është në njësinë e kuadrit të parë, kështu që
  faktori nuk ushqehet prapë në zinxhir; zbatohet në gjithë nivelin (dhe në vendet e
  shënuara) kur shkruhet, dhe në largësinë e shfaqur ndërkohë. Madhësia e voxel-it është atëherë në
  njësitë e kuadrit të parë, kështu që madhësia e tij në metra ndryshon nga cilësimi me atë faktor.
- Pas 30 kuadrove pa tokë skanimi mbetet pa njësi, dhe e thotë.
- Me telemetri, kuadrot kyç të mëvonshëm nuk provohen: thellësia ankorohet me metrat e telemetrisë.

Të jesh brenda dhjetë për qind të madhësisë së vërtetë fiton ndaj të qenit gabim me një faktor të mijë; telemetria,
aty ku ka, e bën të panevojshëm. Shënimi shfaqet në dritare nën rreshtin e ndjekjes,
si `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (me `found on frame N, so the level is scaled
by F when it is written` kur erdhi më vonë), `no usable ground in the first N frames - sizes are
relative, not metres`, ose `in metres, from the telemetry's positions`.

## Bundle adjustment dhe gjurmët e gjata (nuk është lidhur) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dy pjesë ekzistojnë për një zgjidhës të ardhshëm me dritare dhe **nuk përdoren nga skaneri**:

- **`FeatureTracks`** mban identitetin e tipareve nëpër qindra kuadro me ndjekje Lucas-Kanade
  (600 tipare, rimbjellje nën 60%, tolerancë përpara-mbrapa 1 px, tipare të reja 10 px
  larg atyre ekzistuese), që është ajo që i duhet bundle adjustment - përputhja e përshkruesve mes
  kuadrove të njëpasnjëshëm jep vetëm çifte.
- **`bundle_adjust`** përmirëson një dritare pozash dhe pikash së bashku me
  `scipy.optimize.least_squares` (rajon besimi, humbje soft-L1 me shkallë 2 px, një model eksplicit
  rrallësie i Jakobianit, kamera të fiksuara të rivendosura saktësisht). I testuar kundrejt të vërtetës së njohur te
  `tests/test_bundle.py`.

`WindowedOdometry` i kombinon (dritare me 12 kuadro kyç, një zgjidhje çdo 3 kuadro kyç, dy kamerat e para
të fiksuara, pikat mbi 6 px gabim hidhen, kërcimet mbi 6 herë hapin e fundit refuzohen). Docstring i saj
regjistron se në pamje të vërteta ajo **e shembi rrugën dhe ishte shumë më e ngadaltë** se ndjekja
kuadër pas kuadri, me lirinë e gauge-it (shkalla) dhe një bootstrap me bazë thellësie si shkaqe të njohura dhe
një shkak të tretë të paidentifikuar. Prandaj odometria kuadër pas kuadri mbetet e paracaktuara; rregullimi i mundshëm i shënuar
në kod është një bootstrap me matricë esenciale dy-pamjesh me bazën e fiksuar nga kalibrimi i planit
të tokës.
