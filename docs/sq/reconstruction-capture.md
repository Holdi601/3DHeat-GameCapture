---
title: "Kapja, maskat dhe cilësia e kuadrove"
nav_order: 2
lang: "sq"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Kapja, maskat dhe cilësia e kuadrove {#capture-masks-and-frame-quality}

Kodi: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Nga vijnë kuadrot {#where-frames-come-from}

Një objektiv burimi është një nga:

| Objektivi | Burimi | Shënime |
|---|---|---|
| `monitor:<n>` | një monitor i tërë, drejtpërdrejt | "Whole screen" i dritares me numrin te "Which" |
| `window:<title>` | një dritare, drejtpërdrejt | "A window" i dritares me titullin e saj |
| një rrugë skedari | një skedar video | "A video file" i dritares; çdo format që OpenCV e lexon |

### Kapja e drejtpërdrejtë: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` përdor paketën `windows-capture`, që mbështjell **Windows Graphics Capture** -
API-n publik që përdorin regjistruesit e ekranit. Asgjë nuk injektohet në lojë. Kursori nuk
kapet dhe nuk vizatohet kornizë e verdhë kapjeje.

Biblioteka e kapjes dërgon kuadrot te një callback në fillin e kompozitorit dhe pret që ai të
kthehet menjëherë, prandaj callback vetëm e kopjon kuadrin (buferi ripërdoret), e konverton BGRA
në RGB, e ndryshon madhësinë, e vulos dhe e fut në një radhë me **4 kuadro**. Kur radha është plot,
**kuadri më i vjetër hidhet tej** dhe rritet një numërues: të mbetesh pas duhet të kushtojë kuadro,
jo memorie ose saktësi, dhe pamja e drejtpërdrejtë duhet të tregojë ku është lojtari tani. Kuadrot
e hedhura shfaqen te rreshti i statistikave të dritares, dhe nëse hidhen më shumë se gjysma jepet një
sugjerim.

Çdo kuadër mban `t` (sekonda që nga nisja e kapjes) dhe `monotonic` (`time.monotonic()` i
papërpunuar në momentin e kapjes), ora me të cilën vulosen edhe paketat e telemetrisë - gjë që
lejon që pozat e Forza të rreshtohen me kuadrot.

`windows-capture` është opsional në kontrollin e varësive: pa të një skedar video prapë mund
të skanohet.

### Skedarët video {#video-files}

`VideoSource` lexon me OpenCV, konverton në RGB dhe ndryshon madhësinë. Një kontejner pa shpejtësi
kuadrosh trajtohet si 30 fps. Vulat kohore janë indeksi i kuadrit i pjesëtuar me shpejtësinë e kuadrove;
një skedar nuk ka kohë muri, prandaj telemetria nuk mund të rreshtohet me një video.

### Rezolucioni {#resolution}

Kuadrot ndryshohen në madhësi te burimi që ana më e gjatë të jetë ana e kapjes e paracaktimit (Draft 640,
Balanced 960, Detailed 1280 px), me interpolim sipërfaqeje. Një kuadër 4K ka tridhjetë herë më shumë
piksele se sa përdor modeli i thellësisë.

## Kuadrot kyç {#keyframes}

Pothuajse çdo kuadër i një kapjeje është i tepërt: të qëndruarit pa lëvizur prodhon qindra pamje të një
gjëje. Ajo që do rindërtimi është *parallaksa*. Prandaj një kuadër mbahet sipas **sa ndryshoi pamja që nga
kuadri i fundit i mbajtur**, jo sipas një kohëmatësi.

`picture_change(a, b)`:

1. të dy kuadrot në gri dhe të ulura në një rrjetë 16 x 16 mesataresh blloqesh (mesataret e blloqeve i
   përgjigjen lëvizjes së pamjes, jo kokrrizave, gjetheve, dridhjes ose HUD-it);
2. diferenca absolute mesatare, si pjesë e 255;
3. kur dihet një maskë bote, çdo bllok peshohet me pjesën e tij që është botë dhe jo kabinë, kështu
   që një bllok gjysmë-pult numërohet gjysmë (përdoret sapo maska mbulon më shumë se 5% të peshës së rrjetës).

Pragu **përshtatet me kapjen**: për 30 kuadrot e para është vlera fillestare e paracaktimit
(0.020 / 0.010 / 0.004), pastaj është kuantili i paracaktimit (0.85 / 0.65 / 0.40) i 240 ndryshimeve të fundit
të matura, kurrë nën 0.0001. Një kuadër mbahet kur ndryshimi i tij arrin pragun; kuadri i parë mbahet
gjithmonë. Një prag i fiksuar nuk funksionon nëpër skena - ndryshimi nga kuadri në kuadër i një xhiroje
në kabinë të errët është një pjesë e vogël e atij të një dhome të ndritshme me tekstura - ndërsa "mbaj
të tretën më të zënë" do të thotë e njëjta gjë në të dyja. Pragu në përdorim del me çdo përditësim
progresi (`ScanProgress.threshold`), dhe shiritat e shpejtësisë së ecjes në dritare dhe në overlay e
masin ndryshimin e fundit ndaj tij (`ScanProgress.toward_next_view`).

Vetëm kuadrot e mbajtura kalojnë nëpër modelin e thellësisë dhe rindërtimin. Kuadrot nuk ruhen
përveç nëse e kërkon një thirrës (`keep_frames`); 160 prej tyre mbahen për ngjyrosjen e rrjetës (shih
[ngjyra](reconstruction-fusion-and-texture.md#colour)).

Një skanim mbaron kur ndalohet, kur mbaron një video, ose në kufirin e kohës ose të kuadrove kyç.

## Çfarë nuk është bota {#what-is-not-the-world}

Dy gjëra në një kuadër loje nuk janë gjeometri e nivelit, dhe të dyja e prishin një rindërtim:

- **HUD.** Një kryq shënjestre është tipari më i përsëritshëm në çdo kuadër. Një përputhës tiparesh
  e do, përputhet në mënyrë të përsosur mes çdo çifti kuadrosh, dhe çdo përputhje është provë se
  kamera nuk lëvizi - gjë që e ngjesh gjithë rindërtimin.
- **Gjërat e ngjitura te kamera.** Një armë, një kapak motori, një kornizë kabine, një pult. Gjeometri
  e vërtetë në sistemin e gabuar koordinativ: e bashkuar, njollos gjithë rrugën e ecur.

Dy detektorë i gjejnë. Të dy prodhojnë një maskë (255 = botë, 0 = jo botë) ose `None` derisa nuk
ka mjaft prova, dhe `None` do të thotë gjithmonë "përdor gjithçka", kurrë "mos përdor asgjë".

Maska zbatohet:

- te **zbulimi i tipareve** në odometrinë vizuale (të maskosh një kryq shënjestre nga dalja ndërsa e lë të
  votojë për pozën do ta rregullonte simptomën e dukshme dhe do ta mbante atë dëmprurëse);
- te **pikselat e bashkuar**, që të mos bashkohet gjeometri kabine;
- te matja e **mprehtësisë dhe e ndriçimit**, sepse një kabinë është gjithmonë në mënyrë të përsosur e mprehtë;
- te **ndryshimi i pamjes** që vendos kuadrot kyç.

**Nuk** zbatohet te kuadrot që i jepen zgjidhësit offline VGGT (shih
[Rindërtimi offline](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: ajo që nuk ndryshon {#screenmask-what-does-not-change}

Përdoret nga kuadri i parë kyç derisa FlowMask të jetë gati.

- Çdo kuadër konvertohet në gri, përgjysmohet dhe turbullohet (Gaussian 3 x 3) që një dridhje një-pikselëshe
  në një element statik të HUD të mos lexohet si lëvizje.
- Diferenca absolute për çdo piksel nga kuadri i mëparshëm futet në një mesatare eksponenciale
  (zbehje 0.9), kështu që maska ndjek një HUD që shfaqet ose zhduket në mes të skanimit.
- Mëson vetëm nga kuadrot ku dihet që kamera lëviz (në skanim: pasi të paktën një kuadër është ndjekur) -
  një kamerë e parkuar e bën gjithçka statike.
- Pas **12** kuadrove mësimi, një piksel është statik kur ndryshimi i tij mesatar është nën **0.22** të
  ndryshimit mesatar të kuadrit (medianës) - relative, kështu që pragu ndjek sa shpejt lëviz lojtari.
- Nëse më shumë se **45%** e kuadrit lexohet statike, premisa ka dështuar (një meny, një skenë filmike)
  dhe nuk maskohet asgjë.
- Maska ngushtohet me një piksel (skajet e HUD të zbutura nuk i përkasin asnjërës anë) dhe shkallëzohet
  prapë në madhësi të plotë.

Shënimi i saj në dritare: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, ose `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: ajo që nuk udhëton kurrë {#flowmask-what-never-travels}

Një kabinë nuk është statike: gjilpërat fshijnë, numërari i rrotullimeve dridhet, minihartat rrotullohen,
kështu që një detektor ndryshimi i quan ato piksele botë - dhe janë tiparet më të këqija për t'i dhënë një
zgjidhësi poze. FlowMask pyet pyetjen më të mirë: **cilat tipare qëndrojnë pa udhëtuar?**

- Në skanimin e drejtpërdrejtë mëson një herë, nga **40 kuadrot kyç** e para (në nuanca gri); pastaj
  zëvendëson ScreenMask për pjesën tjetër të skanimit.
- Kuadrot priten në dritare me **30** kuadro, që mbivendosen përgjysmë. Në secilën dritare mbillen deri
  në 800 qoshe (`goodFeaturesToTrack`, cilësia 0.01, 8 px larg njëra tjetrës) dhe ndiqen me Lucas-Kanade
  piramidal (21 x 21, 4 nivele) me një **kontroll përpara-mbrapa**: një gjurmë, rrjedha e kundërt e së
  cilës nuk bie brenda 1 px nga vendi ku filloi, hidhet tej, sepse një ndjekës që shmanget te një model fqinj
  do të prodhonte pikërisht firmën "e qëndrueshme por e palëvizshme" që kërkohet. Dritaret më të shkurtra
  se 20 kuadro anashkalohen. Dritaret e shkurtra kanë rëndësi: në një vozitje të gjatë pothuajse çdo tipar i
  botës largohet nga kuadri dhe provat shpërndahen në hiç.
- Udhëtimi neto i çdo tipari të mbijetuar krahasohet me **2% të gjerësisë së kuadrit**: poshtë tij është
  "i ngecur"; sipër, "në lëvizje". Numrat grumbullohen në një rrjetë **24 x 24** qelizash ekrani sipas
  vendit ku filloi çdo tipar.
- Një qelizë bllokohet kur mban të paktën 2 tipare të ngecura dhe më shumë të ngecura se në lëvizje,
  **dhe** të paktën 3 nga 8 fqinjët e saj janë të bllokuar gjithashtu (një qelizë e vetme është zhurmë;
  pamjet e errëta prodhojnë plot).
- Mbahen vetëm rajonet e bllokuara **të lidhura me skajin e kuadrit**. Gjithçka e ngjitur te kamera
  arrin në një skaj të ekranit; ajo që është në mes dhe nuk udhëton është pika e ikjes - kur vozit përpara,
  rruga drejt përpara nuk ka rrjedhë dhe është gjeometria më e dëshiruar.
- Rajoni i mbijetuar zgjerohet me një qelizë (skaji i një pulti instrumentesh është gradient).
- Nëse më shumë se **60%** e kuadrit do të maskohej, nuk maskohet asgjë: në pamjet e natës shumica e
  qelizave nuk kanë tipar të ndjekshëm, që lexohet njësoj si një cipë ore.

Shënimi i saj: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, ose, mbi 60%, një mesazh që shpjegon se nuk maskon asgjë.

Rruga offline mëson të njëjtin FlowMask nga 4 vozitje me 90 kuadro radhazi të shpërndara nëpër
video, në 960 x 540 ([Offline](reconstruction-offline.md)).

## Cilësia e kuadrove dhe këshillat {#frame-quality-and-advice}

`QualityWatcher` gjykon çdo kuadër kyç dhe zgjedh **një** udhëzim, kështu që overlay mund të thotë
"ngadalëso" ndërsa ka ende kohë.

Për çdo kuadër mat, vetëm në pikselat e botës (të gjithë pikselat nëse maska lë më pak se 5%):

- **mprehtësinë**: variancën e Laplasianit - masa standarde me një kalim, dhe i përgjigjet saktësisht
  asaj që e shkatërron turbullimi i lëvizjes;
- **ndriçimin**: nivelin mesatar të gri, 0-255.

Mprehtësia nuk ka shkallë absolute (një etapë nate dhe një rrugë e ndritshme ndryshojnë me një rend
madhësie, të dyja në fokus), prandaj gjykohet kundrejt **medianës rrjedhëse të kësaj kapjeje**:
90 kuadrot e fundit, duke pasur nevojë për 20 para çdo gjykimi. Çdo kuadër krahasohet me historinë
*para* se të shtohet, kështu që një shtrirje e gjatë e turbullt nuk mund ta tërheqë medianën poshtë
që ta takojë veten.

| Kushti | Testi |
|---|---|
| i sheshtë | mprehtësia më së shumti 1.0 (një ekran ngarkimi, një mur, qiell) |
| i errët | ndriçimi nën 26 |
| i turbullt | mprehtësia nën 0.55 të medianës, dhe jo i sheshtë |

Këshilla, e para që përputhet fiton (e renditur sipas asaj që e bllokon skanimin më shumë):

| Situata | Këshilla | Niveli |
|---|---|---|
| më pak se 20 kuadro | Getting a feel for the picture… | ok |
| i sheshtë | Nothing to measure — point the camera at the level, not at the sky. | stop |
| i errët | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| i turbullt | Blurred — slow down. | warn |
| më pak se gjysma e kuadrove të ndjekura | Losing track — slow down and keep more of the level in view. | warn |
| më pak se 40% e kuadrove të ndjekura u bashkuan | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| ekzistojnë pika të dobëta | N thin spots — the map marks them. | ok |
| përndryshe | Good — keep going. | ok |

Niveli ngjyros këshillën e overlay (jeshile / qelibar / e kuqe). Shiriti **sharpness** i overlay
është mprehtësia e kuadrit në raport me medianën. (Kodi ka edhe "Blurred, and the camera is
not moving. Check the capture." për një kamerë të palëvizshme; skanimi e raporton gjithmonë
kamerën si në lëvizje, prandaj nuk shfaqet.)
