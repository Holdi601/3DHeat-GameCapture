---
title: "Rögzítés, maszkok és képkockaminőség"
nav_order: 2
lang: "hu"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Rögzítés, maszkok és képkockaminőség {#capture-masks-and-frame-quality}

Kód: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Honnan jönnek a képkockák {#where-frames-come-from}

A forrás célja a következő egyike:

| Cél | Forrás | Megjegyzés |
|---|---|---|
| `monitor:<n>` | egy teljes monitor, élőben | az ablak „Whole screen” (Teljes képernyő) lehetősége, a számmal a „Which” (Melyik) mezőben |
| `window:<title>` | egy ablak, élőben | az ablak „A window” (Egy ablak) lehetősége, a címével |
| fájlelérési út | egy videofájl | az ablak „A video file” (Egy videófájl) lehetősége; bármilyen formátum, amit az OpenCV olvas |

### Élő rögzítés: Windows Graphics Capture {#live-capture-windows-graphics-capture}

A `WindowSource` a `windows-capture` csomagot használja, amely a **Windows Graphics Capture**-t csomagolja – azt a nyilvános API-t, amelyet a képernyőfelvevők is használnak. Semmi nincs a játékba injektálva. A kurzor nem kerül rögzítésre, és nem rajzolódik sárga rögzítési keret.

A rögzítőkönyvtár a képkockákat a kompozitor szálán lévő visszahívásnak adja át, és azt várja, hogy az azonnal visszatérjen. Ezért a visszahívás csak lemásolja a képkockát (a puffer újrahasznosított), BGRA-ból RGB-be alakítja, átméretezi, időbélyeggel látja el, és egy **4 képkockás** sorba teszi. Ha a sor tele van, a **legrégebbi képkocka eldobódik**, és egy számláló nő: a lemaradás legyen képkockavesztés, ne memóriahasználat vagy helytelenség, és az élő nézet azt mutassa, hol van most a játékos. Az eldobott képkockák az ablak statisztikai sorában látszanak, és ha több mint a fele eldobódik, tipp jelenik meg.

Minden képkockát megillet a `t` (másodpercek a rögzítés kezdete óta) és a `monotonic` (a nyers `time.monotonic()` a rögzítéskor) – ehhez az órához bélyegzik a telemetriacsomagokat is, ami lehetővé teszi, hogy a Forza-pózok a képkockákhoz igazodjanak.

A `windows-capture` a függőségellenőrzésben opcionális: nélküle videofájl is átvizsgálható.

### Videófájlok {#video-files}

A `VideoSource` az OpenCV-vel olvas, RGB-re alakít és átméretez. Frekvencia nélküli konténert 30 fps-nek veszünk. Az időbélyegek a képkockaindex osztva a képkockafrekvenciával; egy fájlnak nincs falióra-ideje, így a telemetria nem igazítható videóhoz.

### Felbontás {#resolution}

A képkockákat a forrásnál átméretezzük úgy, hogy a leghosszabb oldal a beállítás rögzítési mérete legyen (Draft 640, Balanced 960, Detailed 1280 px), területi interpolációval. Egy 4K-s képkocka harmincszor annyi pixel, mint amennyit a mélységmodell használ.

## Kulcsképkockák {#keyframes}

A rögzítés szinte minden képkockája felesleges: egy helyben állás száz nézetet ad ugyanarról. A rekonstrukció a *parallaxist* keresi. Ezért egy képkockát nem időzítő alapján tartunk meg, hanem azon, **mennyit változott a kép az utoljára megtartott képkockához képest**.

`picture_change(a, b)`:

1. mindkét képkocka szürkeárnyalatos lesz, és egy 16 x 16-os rács blokkátlagaira csökken (a blokkátlagok a kép mozgására reagálnak, nem a szemcsézettségre, a lombozatra, a villódzásra vagy a HUD-ra);
2. az átlagos abszolút különbség, a 255 törtrészeként;
3. ha a világmaszk ismert, minden blokkot a világ és nem a műszerfal részarányával súlyozunk, így egy félig műszerfalas blokk felet ér (ez akkor lép életbe, ha a maszk a rács súlyának 5%-át meghaladja).

A küszöb **alkalmazkodik a rögzítéshez**: az első 30 képkockánál a preset kezdőértéke (0,020 / 0,010 / 0,004), utána a preset kvantilise (0,85 / 0,65 / 0,40) az utolsó 240 mért változásból, de soha nem kisebb 0,0001-nél. Egy képkocka akkor marad meg, ha a változása eléri a küszöböt; az első képkocka mindig megmarad. Egy rögzített küszöb nem működne minden jelenetben – egy sötét műszerfalas kör képkockáinak változása kicsi egy világos, texturált szoba változásához képest –, míg „tartsuk a legzsúfoltabb harmadot” mindkét esetben ugyanazt jelenti. Az éppen használt küszöb minden folyamatjelentéssel együtt kimegy (`ScanProgress.threshold`), a sétasebesség-sávok pedig az ablakban és az átfedésben az utolsó változást mérik hozzá (`ScanProgress.toward_next_view`).

Csak a megtartott képkockák mennek át a mélységmodellen és a rekonstrukción. Képkockákat nem tárolunk, hacsak a hívó nem kéri (`keep_frames`); ebből 160-at megtartunk a háló színezéséhez (lásd [szín](reconstruction-fusion-and-texture.md#colour)).

A rögzítés akkor ér véget, ha megállítják, ha egy videó elfogy, vagy az időkorlátnál vagy a kulcsképkocka-korlátnál.

## Ami nem a világ {#what-is-not-the-world}

Két dolog egy játékképkockán nem szintgeometria, és mindkettő tönkreteszi a rekonstrukciót:

- **A HUD.** A célkereszt a legismétlődőbb jellemző egy képkockán. Egy jellemzőillesztő szereti: tökéletesen egyezik minden képkockapár között, és minden egyezés arra utal, hogy a kamera nem mozdult – ami összenyomja az egész rekonstrukciót.
- **A kamerához rögzített dolgok.** Fegyver, motorháztető, fülkeváz, műszerfal. Valódi geometria rossz koordinátarendszerben: összeillesztve végigkenődik a teljes megtett úton.

Két detektor találja meg őket. Mindkettő maszkot ad (255 = világ, 0 = nem világ), vagy `None`-t, amíg nincs elég bizonyíték; a `None` mindig azt jelenti, hogy „minden használható”, soha azt, hogy „semmi”.

A maszkot alkalmazzuk:

- a **jellemzőfelismerésnél** a vizuális odometriában (ha a célkeresztet kimaszkoljuk a kimenetből, de a pózt még mindig az befolyásolja, a látható tünetet javítjuk, a káros okot nem);
- az **összeillesztett pixeleken**, hogy semmilyen fülkegeometria ne kerüljön összeillesztésre;
- az **élességi és fényességi mérésen**, mert egy fülke mindig tökéletesen éles;
- a **képváltozáson**, amely a kulcsképkockákat dönti el.

A maszkot **nem** alkalmazzuk a megoldónak adott képkockákra az offline VGGT-megoldóban (lásd [Offline rekonstrukció](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: ami nem változik {#screenmask-what-does-not-change}

Az első kulcsképkockától kezdve használjuk, amíg a FlowMask kész nincs.

- Minden képkocka szürkeárnyalatos lesz, felezett méretű, és 3 x 3-as Gauss-elmosást kap, hogy egy statikus HUD-elem egypixeles remegése ne látsszon mozgásnak.
- Minden pixel abszolút különbsége az előző képkockától exponenciális átlagba (csillapítás 0,9) hajlik, így a maszk követi azt a HUD-ot, amely a játék közben jelenik meg vagy tűnik el.
- Csak azokból a képkockákból tanul, ahol ismert, hogy a kamera mozog (a szkennelésben: legalább egy képkocka követése után) – egy mozdulatlan kamera mindent statikusnak mutatna.
- **12** tanuló képkocka után egy pixel statikus, ha átlagos változása a képkocka medián változásának **0,22**-e alatt van – relatív, így a küszöb követi, milyen gyorsan mozog a játékos.
- Ha a képkocka több mint **45%-a** statikusnak látszik, a feltevés megbukott (menü, vágás), és semmi nincs maszkolva.
- A maszkot egy pixellel erodáljuk (a HUD széleinek antialiasing-pixelei sem egyik oldalhoz nem tartoznak), és visszaskálázzuk teljes méretre.

Az ablakban megjelenő üzenete: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected`, vagy `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: ami sosem utazik {#flowmask-what-never-travels}

A fülke nem statikus: a mutatók lendülnek, a fordulatszámmérő rezeg, a térkép forog, így a változásdetektor ezeket a pixeleket világnak tekinti – és ezek a legrosszabb jellemzők, amelyeket egy pózmegoldónak lehet adni. A FlowMask a jobb kérdést teszi fel: **melyik jellemzők maradnak meg anélkül, hogy elmozdulnának?**

- Az élő szkennelésben egyszer tanul, az első **40 kulcsképkockából** (szürkeárnyalatosan); utána a szkennelés hátralévő részében a ScreenMaskot váltja.
- A képkockákat **30** képkockás ablakokra vágjuk, félig átfedésben. Minden ablakban legfeljebb 800 sarokpont kerül kijelölésre (`goodFeaturesToTrack`, minőség 0,01, 8 px távolságra), és piramisos Lucas–Kanade-del (21 x 21, 4 szint) követjük őket **előre–hátra ellenőrzéssel**: az a követés, amelynek visszafelé mért mozgása nem ér vissza 1 pixelen belül a kiindulási pontjához, eldobódik, mert egy szomszédos mintázatra sodródó követő pont éppen azt a „megmaradó, de mozdulatlan” jelet hozná létre, amelyet keresünk. A rövid ablakok azért fontosak, mert egy hosszú futásnál szinte minden világjellemző kilép a képkockából, és a bizonyíték elvékonyodik.
- Minden túlélő jellemző nettó elmozdulását a képkockaszélesség **2%-ával** hasonlítjuk össze: az alatt „ragadt”, felette „mozgó”. A számlálókat a jellemzők kezdőpontja szerint egy **24 x 24**-es képernyőcella-rácson halmozzuk.
- Egy cella blokkolt, ha legalább 2 ragadt jellemzőt tartalmaz, és több ragadt van benne, mint mozgó, **és** a 8 szomszédja közül legalább 3 szintén blokkolt (egy magányos cella zaj; a sötét felvétel sok ilyet ad).
- Csak a **képkocka szélével összefüggő** blokkolt régiók maradnak meg. Minden, ami a kamerához van rögzítve, eléri a képernyő szélét; ami középen áll és nem mozog, az a tűnési pont – előre hajtva az előttünk lévő út nincs áramlásban, és ez a legkívánatosabb geometria.
- A túlélő régió egy cellával nő (egy műszerfal széle gradiens).
- Ha a képkocka több mint **60%-át** maszkolná, semmit sem maszkolunk: éjszakai felvételen a legtöbb cella nem tartalmaz követhető jellemzőt, ami ugyanúgy néz ki, mint egy mutató.

Az üzenete: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, vagy 60% fölött egy üzenet, amely megmagyarázza, hogy nem maszkol semmit.

Az offline út ugyanezt a FlowMaskot tanulja 4 futásból, mindegyik 90 egymást követő képkockából, a videón elosztva, 960 x 540-es szürkeárnyalatos képen ([Offline](reconstruction-offline.md)).

## Képkockaminőség és tanács {#frame-quality-and-advice}

A `QualityWatcher` minden kulcsképkockát megítél, és **egy** utasítást választ, hogy az átfedés „lassíts” jelzést adhasson, amíg még van idő.

Képkockánként a világpixelekre mér (ha a maszk 5%-nál kevesebbet hagy, az összes pixelre):

- **élesség**: a Laplace-szűrő varianciája – a szokásos egymenetes mérték, és pontosan arra reagál, amit a mozgási elmosódás elpusztít;
- **fényesség**: átlagos szürke szint, 0–255.

Az élességnek nincs abszolút skálája (egy éjszakai szakasz és egy világos utca nagyságrendekkel különbözik, mindkettő éles), ezért a **rögzítés futó mediánjához** hasonlítjuk: az utolsó 90 képkockához, és legalább 20 kell egyáltalán az ítélethez. Minden képkockát a *hozzáadása előtti* előzményekkel hasonlítunk össze, így egy hosszú elmosódott szakasz nem húzhatja le a mediánt önmagáig.

| Feltétel | Teszt |
|---|---|
| lapos | élesség legfeljebb 1,0 (egy töltőképernyő, egy fal, égbolt) |
| sötét | fényesség 26 alatt |
| elmosódott | élesség a medián 0,55-e alatt, és nem lapos |

A tanács, az első találat nyer (abból kiindulva, mi akadályozza leginkább a szkennelést):

| Helyzet | Tanács | Szint |
|---|---|---|
| 20-nál kevesebb képkocka | Getting a feel for the picture… (A kép megismerése…) | ok |
| lapos | Nothing to measure — point the camera at the level, not at the sky. (Nincs mit mérni – a kamerát a pályára irányítsd, ne az égre.) | stop |
| sötét | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. (Túl sötét a rekonstrukcióhoz. Kapcsold be a fényszórókat, vagy vezesd ezt a szakaszt nappal.) | stop |
| elmosódott | Blurred — slow down. (Elmosódott – lassíts.) | warn |
| a képkockák kevesebb mint fele követve | Losing track — slow down and keep more of the level in view. (Elvész a követés – lassíts, és tartsd több pályát a képen.) | warn |
| a követett képkockák kevesebb mint 40%-a összeillesztve | Positions are good but depth is not sticking. Drive nearer the scenery. (A pozíciók jók, de a mélység nem tapad meg. Vezess közelebb a díszlethez.) | warn |
| vannak gyenge pontok | N thin spots — the map marks them. (N vékony pont – a térkép megjelöli őket.) | ok |
| egyébként | Good — keep going. (Jó – menj tovább.) | ok |

A pálya színezi az átfedés tanácsát (zöld / sárga / piros). Az átfedés **élesség**-sávja a képkocka élessége a mediánhoz képest. (A kódban van még: „Blurred, and the camera is not moving. Check the capture.” – az álló kamerára; a szkennelés mindig mozgónak jelenti a kamerát, így ez nem látszik.)
