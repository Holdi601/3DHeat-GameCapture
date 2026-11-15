---
title: "Kamera pózai és mérete"
nav_order: 4
lang: "hu"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kamera pózai és mérete {#camera-pose-and-scale}

A mélységtérkép azt mondja meg, milyen messze van minden *egy* nézőponttól. Ahhoz, hogy sokból egyetlen szintet készítsünk, tudni kell, hol volt az egyes nézőpontok, és milyen egységekben. Ez az oldal az élő utakat fedi le; az offline, előrecsatolt megoldás a [Offline rekonstrukció](reconstruction-offline.md) oldalon van.

Kód: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## A kameramodell {#the-camera-model}

Az `Intrinsics.from_fov(width, height, fov)` egy lyukkamerát épít a **vízszintes látómezőből**, amelyet az ablakban állítasz be: `fx = (width / 2) / tan(fov / 2)`, négyzetes pixelek (`fy = fx`), a főpont a képkocka közepén. Egy játék nem teszi közzé a vetítését, így ez az egyetlen feltételezett szám: túl szűk esetén a jelenet mélyebbnek látszik, mint amilyen. Az offline út 65 fokot használ.

A `Pose` **világ-ből-kamerába** van tárolva: `rotation` (3 x 3) és `translation` = a kamera középpontja a világban, ami a pályának, a lefedettségi térképnek és az átfedésnek egyaránt kell.

## Vizuális odometria (az alapértelmezés) {#visual-odometry-the-default}

A `VisualOdometry` minden kulcsképkockát az előzőhöz követ:

1. **Jellemzők**: ORB, képkockánként legfeljebb 1500, csak a világmaszkon detektálva (lásd [Rögzítés](reconstruction-capture.md#what-is-not-the-world)).
2. **Egyezések** az előző kulcsképkockához: brute force, Hamming-távolság, keresztellenőrzéssel (csak kölcsönösen legjobb párok).
3. **Emelés 3D-be**: az előző képkocka mélysége már világegységben van, így az egyezett pixelei világpontokká válnak.
4. **A kamera elhelyezése**: `solvePnPRansac` ezeken a pontokon (újravetítési hiba 3 px, megbízhatóság 0,999, 200 iteráció). Az eltolás ugyanezekben az egységekben jön ki, így **a skála átlépi a rést**.
5. **Ennek a képkockának a mélységének horgonyzása**: a saját jósolt inverz mélységét illesztjük (`fit_scale`) a PnP belső pontjainak mélységéhez, és a ciklus ismétlődik.

Az **első képkocka** a origó: identitás póz, és a mélységének affinja vagy a lenti talajkalibráció, vagy – ha nincs – az identitás (a rekonstrukció ekkor belsőleg következetes, de mértékegység nélküli).

Egy póz legalább **18 RANSAC-belső pontot** igényel – jóval a PnP minimumán (hat) felül, mert az a megoldás, amelyet épp alig elegendő pontból kaptunk, pontosan az, amelyik magabiztosan téved.

### Megbízhatóság {#confidence}

Minden elhelyezett képkocka kap egy 0..1 közötti megbízhatóságot, amely súlyozza az összeillesztését és a lefedettségét:

| A póz forrása | Megbízhatóság |
|---|---|
| telemetria | 1,0 |
| előrecsatolt megoldás | 0,85 |
| vizuális követés | `belső / egyezések x min(1, belső / 60)` |

### Amikor a követés megszakad {#when-tracking-breaks}

Egy képkocka, amelyet nem lehet elhelyezni, jelentésre kerül, sosem találgatják: `no features in the frame (N found)` (nincs jellemző a képkockában, N található), `too few matches to place the camera` (túl kevés egyezés a kamera elhelyezéséhez), `could not relocalise` (nem sikerült újralokalizálni). Nem rögzítünk pózt, és semmi nem olvad össze. Az utolsó pózról folytatni, vagy új origóval kezdeni a következő pálya-szakaszt egy önkényes eltolásba tenné – egy varratba, amely valódi geometriának látszik.

Megszakadás után minden új képkockát **újralokalizálunk** a korábbi kulcsképkockák adatbázisával szemben (minden 4. követett képkocka kerül be, legfeljebb 120, a legrégebbi kiesik), a legfrissebbtől a régebbi felé, ugyanazzal az egyeztetés-és-PnP lépéssel. Amíg egy sem sikerül, a képkockák eldobódnak. Egy visszatalált képkocka ugyanabban a koordinátarendszerben folytatódik. A visszatalálásokat számoljuk és megjelenítjük az ablakban (`N recovered`).

### Hurokzárás: kikapcsolva {#loop-closure-off}

Ugyanez az adatbázis támogatja a hurokzárást: egy sokkal korábbi kulcsképkockával való egyeztetéssel felismerjük, hogy visszatértünk egy helyre, és visszaigazítjuk az utat rá. **Alapértelmezetten ki van kapcsolva, és a szkenner soha nem kapcsolja be** (`Reconstructor(loop_closure=False)`). Ismétlődő díszletnél – egy ralisztárónál, egy folyosónál, fasornál – minden szakasz hasonlít a többire, és a jellemzőegyeztetés hamis visszatéréseket erősít meg, ami a kamerát ahhoz a ponthoz szorítja közel, ahonnan indult, miközben az tovább vezet. Ezt rendesen csak helyfelismerés (szógyűjtemény-szótár vagy tanult leíró) és geometriai ellenőrzés egy térképpel szemben lehetne megcsinálni, és ez nincs megépítve.

Ha kódból bekapcsolják, egy zárásnak kell: egy legalább 60 kulcsképkocka-öreg kulcsképkocka, legfeljebb 6 m-re az aktuális pózetól, legalább 90 belső egyezéssel, amely 0,02 m-nél többel, de 6 m-nél kevesebbel mozdítja a pózt. Még akkor is csak az aktuális pózt helyettesíti; nem póz-gráf, és nem mozdítja el a korábbi képkockákat vagy az összeillesztett geometriát.

## Telemetriai pózok {#telemetry-poses}

A **Racing telemetry (Forza) -> Listen for position data** (Versenytelemetria (Forza) -> Pozícióadatok fogadása) bekapcsolásával a kamera útja a Forza Data Outjából jön, nem a képekből (`ForzaPoseSource`):

- Egy szál figyel a `127.0.0.1:<port>` címen (alapértelmezés 5300) ugyanazzal az elrendezés-felismeréssel, mint a rögzítők ([Forza](telemetry-forza.md)); a csomagok használva vannak, amíg az `isRaceOn` be van állítva. Egy foglalt portot jelentünk, nem dobunk kivételt: a telemetria frissítés, és a szkennelés vizuálisan folytatódik.
- Minden csomagot az **érkezés monotonikus idejével** bélyegzünk – ugyanazzal az órával, amellyel a rögzítés a képkockáit. A játék saját időbélyege egy nem kapcsolódó dologtól számol, ezért az igazításhoz nem használjuk. A helyi visszhang egy-két ezredmásodpercnyi remegése 200 km/h-nál körülbelül 6 cm.
- Egy gördülő, 30 másodperces puffer marad meg. Egy képkocka pózát a befogási időpontja két oldalán lévő mintákból **interpoláljuk**: a pozíció lineárisan, a forgatás gömbi interpolációval (egy kevert mátrix nem forgatás, és minden pontot elferdítene). Egy 0,35 s-nál hosszabb résen vagy a pufferen kívül nincs póz.
- `pose_from_forza`: a kamera az autónál van (a követőkamera eltolása nincs közzétéve). **A pozíciókat pontosan úgy tartjuk, ahogy a játék küldi**: a Forza világa már Y-felfelé áll (x és z a térképen, y a magasság), ahogy a körfájlok és az útfájlok is írják, így a felület ugyanazokra a koordinátákra kerül, mint a fölötte rögzített körök. (Egy korábbi verzió y-t és z-t cserélt egy „Z-felfelé” világhoz, és a pályát oldalra fektette.)
- A forgatás yaw, pitch, roll sorrendben, az érzékeket rögzített köröktől olvasva: a haladás iránya `atan2(dx, dz)` egyenlő a yaw-val, a megmászott lejtő egyenlő a negatív pitch-csel (pozitív az orr lefelé), és a roll pozitív, ha a jobb oldali felfüggesztés be van nyomva (pozitív jobbra leejti az oldalt). Az autó tengelyei (x jobbra, y felfelé, z előre) a kamera tengelyeibe (x jobbra, y lefelé, z előre) fordulnak az y megfordításával.
- A Forza világa **balkezes**, a kamera keretrendszere nem, így az eredő világ-ből-kamerába mátrix tükrözés (determináns -1), és a szkennelés balkezesen jön ki, mint a körfájlok. Az interpoláció nem változik (két ilyen póz közötti fordulat valódi forgatás).
- Ha egy képkockának nincs telemetriapózja (rés), a rekonstruktor a vizuális követésre esik vissza az adott képkockára, az utolsó telemetriapózból folytatva, és amint a feed újra válaszol, visszatér a feed pózaihoz. A PnP csak forgatásokat ad vissza, ezért tükrözött világban úgy oldja meg, hogy a világot a z-n át tükrözi, és a tükrözést visszahajtja; így a képkocka a játék koordinátáiba kerül. Csak ha a vizuális követés is elbukik, lesz a képkocka követetlen.

### Mélységskála telemetriából {#depth-scale-from-telemetry}

A játék megmondja, hol van a kamera, de nem azt, milyen messze van bármi, így minden képkocka mélységét még horgonyozni kell – de nem a 0. képkockától láncolva, amelynek egysége önkényes, miközben a pózok méterben vannak. Ehelyett az előző és az aktuális képkocka közötti egyezett jellemzőket (legalább 8) **közvetlenül háromszögeljük az ismert két pózból**, méterben, és a mélységtérképet a kamera előtti pontokhoz illesztjük. Minden képkocka a telemetriához van horgonyozva, így nincs lánc, amely sodródna.

Ha a két póz 0,05 m-nél közelebb van egymáshoz, a sugarak közel párhuzamosak, és a háromszögelés zaj, így a képkockát horgonyozatlanul hagyjuk: pontosan elhelyezve, de nem összeillesztve („positioned, but its depth has no scale yet” – elhelyezve, de mélységének nincs még skálája). Ezért számolja az ablak külön az *elhelyezett* és az *összeillesztett* képkockákat.

## Skála {#scale}

A vizuális odometria helyesen láncolja a relatív skálát, de az egész szint egy ismeretlen tényező körül lebeg. A Depth Anything relatív kimenete önkényes egységekben jön, így ha az első képkockát identitáson hagyjuk, a világ egy önkényes méretben a kamera néhány méterén belül lesz.

A `GroundCalibrator` ezt a tényezőt rögzíti abból, **milyen magasan van a kamera a talajhoz képest**, az **első kulcsképkockán** mérve, és ha ott nincs használható talaj, a következőkön:

- Kameramagasság: **1,15 m** (egy sofőr szemmagassága) – az ablak ezt mindig használja; a szkriptek megadhatnak 1,70 m-t (`WALKING_HEIGHT`, egy álló játékos) vagy `None`-t (nincs kalibráció).
- Talajminta: a képkocka alsó 62–92%-a (a horizont alatt, a motorháztető vagy a fegyver felett) és a szélesség 30–70%-a (a szegélyektől távol).
- Minden ott lévő pixel, amelynek van használható jóslata, `1 / jósolt` mélységgel emelve a hálózat egységeiben; az optikai tengely alatti pontok a kamera alatti magasságot adnak. Ezek mediánja a kamera magassága a hálózati egységekben, így `méter egységenként = 1,15 / medián`, és a képkocka affinja `skála = 1 / méter egységenként`, eltolás 0.
- Csak legalább 200 talajmintával és a **szóródás** (medián abszolút eltérés osztva mediánnal) 0,60 alatt bízunk meg benne.
- Az első kulcsképkockán az illesztés lesz az origó egysége, így a szkennelés attól kezdve méterben van. Ha az első kulcsképkockán nincs használható talaj, a szkennelés egység nélkül indul, és minden későbbi követett kulcsképkockát megpróbálunk, összesen legfeljebb **30 képkockáig**. Az első, amelyik kalibrálódik, adja a *méter egységenként* értéket: a talajuk által a mélységre adott becslés és a lánc által arra a képkockára adott mélység hányadosának mediánja a talajsávon. Minden, ami már összeolvadt, az első képkocka egységében van, ezért a tényező nem kerül vissza a láncba; a teljes szintre alkalmazzuk (és a megjelölt helyekre), amikor íródik, és addig a megjelenített távolságra is. Ezért a voxelméret az első képkocka egységében van, így a méretük méterben eltér a beállítástól ezzel a tényezővel.
- 30 talaj nélküli képkocka után a szkennelés egység nélkül marad, és ezt kimondja.
- Telemetriával a későbbi kulcsképkockákat nem próbáljuk: a mélység a telemetria méterére van horgonyozva.

A tíz százalékon belül a valódi méret jobb, mint egy ezerszeres tévedés; a telemetria, ahol elérhető, ezt feleslegessé teszi. A megjegyzés az ablakban a követési sor alatt jelenik meg, `Size: ...` formában: `measuring the ground` (a talaj mérése), `no flat ground in view yet - still looking (N frames tried)` (még nincs sík talaj a képen – keresem (N képkocka próbálva)), `scaled from a 1.15 m camera height, ...` (1,15 m kameramagasságból skálázva, …; ha később jött, `found on frame N, so the level is scaled by F when it is written` – az N. képkockán találva, így a szintet F-fel skálázzuk íráskor), `no usable ground in the first N frames - sizes are relative, not metres` (nincs használható talaj az első N képkockán – a méretek relatívak, nem méterek), vagy `in metres, from the telemetry's positions` (méterben, a telemetria pozícióiból).

## Köteg-igazítás és hosszú sávok (nincs bekötve) {#bundle-adjustment-and-long-tracks-not-wired-in}

Két rész létezik egy jövőbeli ablakos megoldóhoz, és a szkenner **nem használja**:

- A **`FeatureTracks`** százas képkockák során megtartja a jellemzők azonosságát Lucas–Kanade-követéssel (600 jellemző, 60% alá újravetve, előre–hátra tűrés 1 px, az új jellemzők 10 px-re a meglévőktől), amire a köteg-igazításnak szüksége van – az egymást követő képkockák közötti leíró-egyeztetés csak párokat ad.
- A **`bundle_adjust`** egy ablak pózait és pontjait együtt finomítja a `scipy.optimize.least_squares`-szel (bizalmi tartomány, soft-L1 veszteség 2 px skálával, explicit Jacobi-ritkasági minta, a rögzített kamerák pontosan visszaállítva). A `tests/test_bundle.py` ismert igazsághoz teszteli.

A `WindowedOdometry` ezeket összeköti (12 kulcsképkockás ablakok, megoldás minden 3. kulcsképkockánál, az első két kamera rögzítve, a 6 px-nél nagyobb hibájú pontok eldobva, a friss lépés 6-szorosánál nagyobb ugrások visszautasítva). Dokumentációs megjegyzése rögzíti, hogy valódi felvételen **összeroppantotta az utat, és sokkal lassabb volt**, mint a képkockánkénti követés; az ismert okok a skála-szabadság (gauge) és a mélységalapú bootstrap, egy harmadik, azonosítatlan okkal. Ezért a képkockánkénti odometria marad az alapértelmezés; a kódban jelzett valószínű javítás egy kétnézetes esszenciális-mátrixos bootstrap, a bázistávolsággal a talajsík-kalibrációból rögzítve.
