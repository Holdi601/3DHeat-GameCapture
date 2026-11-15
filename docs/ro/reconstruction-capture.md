---
title: "Captură, măști și calitatea cadrelor"
nav_order: 2
lang: "ro"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Captură, măști și calitatea cadrelor {#capture-masks-and-frame-quality}

Cod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## De unde vin cadrele {#where-frames-come-from}

O țintă de sursă este una dintre:

| Țintă | Sursă | Observații |
|---|---|---|
| `monitor:<n>` | un monitor întreg, în timp real | „Whole screen" din fereastră, cu numărul din „Which" |
| `window:<title>` | o fereastră, în timp real | „A window" din fereastră, cu titlul ei |
| o cale de fișier | un fișier video | „A video file" din fereastră; orice format pe care îl poate citi OpenCV |

### Captură în timp real: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` folosește pachetul `windows-capture`, care înfășoară **Windows Graphics Capture** - API-ul public pe care îl folosesc înregistratoarele de ecran. Nimic nu este injectat în joc. Cursorul nu este capturat și nu se desenează niciun contur galben de captură.

Biblioteca de captură livrează cadrele unei funcții de apel pe firul compozitorului și se așteaptă ca aceasta să revină imediat, deci funcția doar copiază cadrul (bufferul este refolosit), îl convertește din BGRA în RGB, îl redimensionează, îi pune o marcă de timp și îl pune într-o coadă de **4 cadre**. Când coada este plină, **cel mai vechi cadru este aruncat** și un contor crește: a rămâne în urmă trebuie să coste cadre, nu memorie sau corectitudine, iar vederea în direct trebuie să arate unde este jucătorul acum. Cadrele aruncate apar în linia de statistici a ferestrei, iar dacă sunt aruncate mai mult de jumătate apare un sfat.

Fiecare cadru poartă `t` (secunde de la începutul capturii) și `monotonic` (valoarea brută `time.monotonic()` la captură), același ceas cu care sunt marcate pachetele de telemetrie - ceea ce permite ca pozele Forza să fie aliniate cu cadrele.

`windows-capture` este opțional la verificarea dependențelor: fără el, un fișier video poate fi tot scanat.

### Fișiere video {#video-files}

`VideoSource` citește cu OpenCV, convertește în RGB și redimensionează. Un container fără rată de cadre este tratat ca 30 fps. Marcajele de timp sunt indexul cadrului împărțit la rata de cadre; un fișier nu are timp de ceas, deci telemetria nu poate fi aliniată cu un video.

### Rezoluție {#resolution}

Cadrele sunt redimensionate la sursă astfel încât latura cea mai lungă să fie dimensiunea de captură a presetării (Draft 640, Balanced 960, Detailed 1280 px), cu interpolare de arie. Un cadru 4K are de treizeci de ori mai mulți pixeli decât folosește modelul de adâncime.

## Cadre-cheie {#keyframes}

Aproape fiecare cadru al unei capturi este redundant: a sta pe loc produce sute de vederi ale aceluiași lucru. Ce cere reconstrucția este *paralaxa*. Deci un cadru este păstrat în funcție de **cât s-a schimbat imaginea de la ultimul cadru păstrat**, nu după un cronometru.

`picture_change(a, b)`:

1. ambele cadre sunt aduse la nuanțe de gri și la o grilă de 16 x 16 de medii de blocuri (mediile pe blocuri reacționează la mișcarea imaginii, nu la granulație, vegetație, pâlpâire sau HUD);
2. diferența absolută medie, ca fracție din 255;
3. când o mască a lumii este cunoscută, fiecare bloc este ponderat cu partea din el care este lume și nu cabină, astfel încât un bloc pe jumătate din bord contează pe jumătate (folosit odată ce masca acoperă mai mult de 5% din greutatea grilei).

Pragul **se adaptează la captură**: primele 30 de cadre folosesc valoarea de start a presetării (0,020 / 0,010 / 0,004), apoi cuantila presetării (0,85 / 0,65 / 0,40) din ultimele 240 de schimbări măsurate, niciodată sub 0,0001. Un cadru este păstrat când schimbarea sa ajunge la prag; primul cadru este întotdeauna păstrat. Un prag fix nu poate funcționa între scene - schimbarea de la un cadru la altul a unei tură pe timp de noapte, cu cabina întunecată, este o fracție mică din cea a unei camere luminoase cu textură - în timp ce „păstrează cel mai aglomerat al treilea" înseamnă același lucru în ambele. Pragul folosit iese cu fiecare actualizare de progres (`ScanProgress.threshold`), iar barele de viteză de mers din fereastră și din overlay măsoară ultima schimbare față de el (`ScanProgress.toward_next_view`).

Doar cadrele păstrate trec prin modelul de adâncime și prin reconstrucție. Cadrele nu sunt stocate decât dacă un apelant cere (`keep_frames`); 160 dintre ele sunt păstrate pentru colorarea mesh-ului (vezi [culoarea](reconstruction-fusion-and-texture.md#colour)).

O scanare se termină când este oprită, când se termină un video, sau la limita de timp sau de cadre-cheie.

## Ce nu este lumea {#what-is-not-the-world}

Două lucruri dintr-un cadru de joc nu sunt geometrie a nivelului, iar amândouă strică o reconstrucție:

- **HUD-ul.** Un punct de mira este cea mai repetabilă trăsătură din orice cadru. Un potrivitor de trăsături o iubește, se potrivește perfect între fiecare pereche de cadre, iar fiecare potrivire este o dovadă că camera nu s-a mișcat - ceea ce comprimă toată reconstrucția.
- **Lucrurile fixate de cameră.** O armă, un capotaj, un cadru de cabină, un bord. Geometrie reală în sistemul de coordonate greșit: fuzionată, se întinde de-a lungul întregului drum parcurs.

Două detectoare le găsesc. Amândouă produc o mască (255 = lume, 0 = nu lume) sau `None` cât timp nu există dovezi suficiente, iar `None` înseamnă întotdeauna „folosește tot", niciodată „nu folosi nimic".

Masca se aplică:

- la **detectarea trăsăturilor** în odometria vizuală (mascarea unui punct de mira din ieșire, lăsându-l să voteze pentru poziție, ar repara simptomul vizibil și ar păstra cel dăunător);
- la **pixelii fuzionați**, ca să nu fie fuzionată geometrie de cabină;
- la măsura de **claritate și luminozitate**, pentru că o cabină este întotdeauna perfect clară;
- la **schimbarea imaginii** care decide cadrele-cheie.

**Nu** se aplică cadrelor date solverului offline VGGT (vezi [Reconstrucție offline](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: ce nu se schimbă {#screenmask-what-does-not-change}

Folosit de la primul cadru-cheie până când FlowMask este gata.

- Fiecare cadru este convertit în nuanțe de gri, înjumătățit și estompat (Gaussian 3 x 3), astfel încât o tremurare de un pixel a unui element HUD static să nu fie citită ca mișcare.
- Diferența absolută pe pixel față de cadrul anterior este adunată într-o medie exponențială (decădere 0,9), astfel încât masca urmărește un HUD care apare sau dispare în mijlocul scanării.
- Învață numai din cadre în care camera este știută că se mișcă (în scanare: după ce cel puțin un cadru a fost urmărit) - o cameră parcată face totul static.
- După **12** cadre de învățare, un pixel este static când media schimbării sale este sub **0,22** din schimbarea mediană a cadrului - relativ, deci pragul urmărește cât de repede se mișcă jucătorul.
- Dacă mai mult de **45%** din cadru apare static, premisa a eșuat (un meniu, o scenă cinematografică) și nimic nu este mascat.
- Masca este erodată cu un pixel (marginile HUD-ului cu antialias nu aparțin nici uneia dintre părți) și readusă la dimensiunea completă.

Nota sa în fereastră: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` sau `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: ce nu se mișcă niciodată {#flowmask-what-never-travels}

Un cocpit nu este static: acele se mișcă, turometrul tremură, harta mică se rotește, așa că un detector de schimbare numește lume acei pixeli - și sunt cele mai proaste trăsături de dat unui solver de poziție. FlowMask pune o întrebare mai bună: **care trăsături persistă fără să călătorească?**

- În scanarea în direct învață o singură dată, din primele **40 de cadre-cheie** (în nuanțe de gri); apoi înlocuiește ScreenMask pentru restul scanării.
- Cadrele sunt tăiate în ferestre de **30** de cadre, suprapuse pe jumătate. În fiecare fereastră se seminează până la 800 de colțuri (`goodFeaturesToTrack`, calitate 0,01, la 8 px distanță) și sunt urmărite cu Lucas-Kanade piramidal (21 x 21, 4 niveluri) cu o **verificare înainte-înapoi**: o urmă al cărei flux înapoi nu aterizează la mai puțin de 1 px de locul de start este aruncată, pentru că un urmăritor care alunecă pe un model vecin ar fabrica exact semnătura „persistent dar staționar" pe care o caută. Ferestrele mai scurte de 20 de cadre sunt sărite. Ferestrele scurte contează: pe o rulare lungă aproape fiecare trăsătură a lumii părăsește cadrul, iar dovezile se subțiază până la nimic.
- Deplasarea netă a fiecărei trăsături supraviețuitoare este comparată cu **2% din lățimea cadrului**: sub, este „blocată"; peste, este „în mișcare". Numărătorile se acumulează pe o grilă de **24 x 24** de celule de ecran, după locul unde a început fiecare trăsătură.
- O celulă este blocată când are cel puțin 2 trăsături blocate și mai multe blocate decât în mișcare, **și** cel puțin 3 dintre cei 8 vecini ai săi sunt blocați și ei (o celulă izolată este zgomot; footage-ul întunecat produce destule).
- Sunt păstrate numai regiunile blocate **conectate de marginea cadrului**. Tot ce este fixat de cameră ajunge la o margine a ecranului; ce stă la mijloc și nu se mișcă este punctul de fugă - mergând înainte, drumul din față nu are flux și este geometria cea mai dorită.
- Regiunea supraviețuitoare crește cu o celulă (marginea unui tablou de bord este un gradient).
- Dacă mai mult de **60%** din cadru ar fi mascat, nu se maschează nimic: pe footage de noapte majoritatea celulelor nu conțin nicio trăsătură urmăribilă, ceea ce arată la fel ca un cadran.

Nota sa: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels` sau, peste 60%, un mesaj care explică faptul că nu maschează nimic.

Calea offline învață același FlowMask din 4 rulări de câte 90 de cadre consecutive, împrăștiate pe întregul video, la 960 x 540 ([Offline](reconstruction-offline.md)).

## Calitatea cadrelor și sfaturile {#frame-quality-and-advice}

`QualityWatcher` judecă fiecare cadru-cheie și alege **o** instrucțiune, ca overlay-ul să poată spune „încetinește" cât mai este timp.

Pentru fiecare cadru măsoară, doar pe pixelii lumii (toți pixelii dacă masca lasă mai puțin de 5%):

- **claritatea**: varianța Laplacianului - măsura standard dintr-o singură trecere, care reacționează exact la ce distruge estomparea de mișcare;
- **luminozitatea**: nivelul mediu de gri, 0-255.

Claritatea nu are o scară absolută (o scenă de noapte și o stradă luminoasă diferă cu un ordin de mărime, amândouă în focus), așa că este judecată față de **mediana rulată a acestei capturi**: ultimele 90 de cadre, cu nevoie de 20 înainte de orice judecată. Fiecare cadru este comparat cu istoria *dinaintea* lui, astfel încât o porțiune lungă estompată să nu poată trage mediana în jos până să se întâlnească cu ea.

| Condiție | Test |
|---|---|
| plat | claritate cel mult 1,0 (un ecran de încărcare, un perete, cerul) |
| întunecat | luminozitate sub 26 |
| estompat | claritate sub 0,55 din mediană, și nu plat |

Sfatul, prima potrivire câștigă (ordonat după cât de tare blochează scanarea):

| Situație | Sfat | Nivel |
|---|---|---|
| mai puțin de 20 de cadre | Ne facem o idee despre imagine… | ok |
| plat | Nimic de măsurat - îndreaptă camera spre nivel, nu spre cer. | stop |
| întunecat | Prea întuneric pentru reconstrucție. Faza pornită sau conduce porțiunea asta pe lumină de zi. | stop |
| estompat | Estompat - încetinește. | warn |
| mai puțin de jumătate din cadre urmărite | Pierdem urma - încetinește și ține mai mult din nivel în vedere. | warn |
| mai puțin de 40% din cadrele urmărite fuzionate | Pozițiile sunt bune, dar adâncimea nu se fixează. Conduce mai aproape de decor. | warn |
| există zone slabe | N zone slabe - harta le marchează. | ok |
| altfel | Bine - continuă. | ok |

Nivelul colorează sfatul din overlay (verde / chihlimbar / roșu). Bara de **claritate** din overlay este claritatea cadrului față de mediană. (Codul mai are „Blurred, and the camera is not moving. Check the capture." pentru o cameră staționară; scanarea raportează întotdeauna camera ca mișcându-se, deci nu este afișat.)
