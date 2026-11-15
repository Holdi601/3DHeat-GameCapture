---
title: "Összeillesztés, lefedettség és szín"
nav_order: 5
lang: "hu"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Összeillesztés, lefedettség és szín {#fusion-coverage-and-colour}

Kód: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Minden elhelyezett kulcsképkocka egyszerre két ritka rácsot frissít: a **felületi térfogatot**, amelyből a háló lesz, és a **lefedettségi rácsot**, amely megmondja, mennyire higgyünk benne, és hová kell visszamenni. Mindkettőt kulcsképkockánként frissítjük, nem a végén, mert a lefedettségi térkép az, amely szerint a játékos irányít.

## A mélységtől a pontokig {#from-depth-to-points}

Minden olyan kulcsképkockára, amelynek a pózát ismerjük **és** a mélysége skálázott:

1. Minden második pixelt használunk mindkét irányban (`PIXEL_STRIDE = 2`; ugyanazon felület szomszédos pixelei nem független mérések).
2. A mélységet a képkocka affin illesztésével méterré alakítjuk.
3. Csak a **0,35 m** és **60 m** közötti értékeket tartjuk meg (a 0,35 m-nél közelebbi a fegyver, a HUD, a motorháztető; a 60 m-nél távolabbi, mert az egyszemű hiba nagyjából a távolság négyzetével nő, így a távoli pontok geometriára hasonlító zaj), és csak a maszk világpixelein.
4. A kamera modellen keresztül felemeljük, és a pózzal a világba visszük.
5. Minden pont hordozza a pixel színét.

Az a képkocka, amely el van helyezve, de nincs mélységskálája, *elhelyezettként* számít, de nem *összeillesztettként*.

## A felületi térfogat {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` – a voxel az ablak „Surface detail” (Felületi részletesség) beállítása.

### Súlyozott telítettség, nem TSDF {#weighted-occupancy-not-a-tsdf}

Egy előjeles távolságmező (TSDF) minden pixel sugara mentén kivág, és jól kezeli a vékony szerkezeteket és a tiszta szabad teret, mert tudja, hogy a sugár *át* ment üres téren. Ehhez minden több százmillió pixel sugarát végig kellene járni. Ez a térfogat ehelyett voxelenként **súlyozott telítettséget** halmoz, és a simított eredményen marching cubes-ot futtat: elég gyors ahhoz, hogy a szkennelés közben fusson, használható GPU nélküli gépen is, és a kimenet zárt felület, nem pontfelhő. Az ára: a vékony szerkezetek és a szabad tér rosszabb, mint egy TSDF-fel lenne.

### Egy képkocka integrálása {#integrating-a-frame}

- A pontokat voxelekbe soroljuk (`floor(pont / voxel)`).
- Minden érintett voxel `súly x sqrt(darab / max_darab)` értéket kap, ahol a `darab` azt számolja, hányan estek a képkocka pontjai a voxelbe, a `súly = max(0.1, póz-megbízhatóság)`. Négyzetgyök: egy ponton túl több ugyanazon felületi pixel, ugyanonnan, már nem jelent több bizonyítékot; a póz-megbízhatóság szerinti súlyozás pedig megakadályozza, hogy egy kétes póz kimozdítsa a felületet.
- A szín voxelenként futó súlyozott átlag.

A rács **ritka**: egy bejárt útvonal a befoglaló téglatest töredékét érinti. A voxelkoordinátákat egyetlen 64 bites kulcsba csomagoljuk (tengelyenként 21 bit, legfeljebb ±1 048 575 voxel – 0,25 m-nél nagyjából ±262 km), és rendezett tömbben, bináris kereséssel keressük őket, teljesen vektorizálva.

### A háló kinyerése {#extracting-the-mesh}

1. A **0,35** súly alatti voxelek kiesnek (a szilhuettszéleken lévő, egyedi pontok tüskékké válnának).
2. A súlyokat a szkennelés **75. percentilisével** skálázzuk, és 1-re vágjuk.
3. A telített teret **64 voxeles oldalhosszúságú blokkokra** bontjuk, mindegyiket a szomszédai adatából álló **3 voxeles peremmel** (halo) realizálva (e nélkül minden blokkhatár falba záródna, és egy útból dobozsor lenne).
4. Minden blokk mezőjét Gauss-simítással (szórás 0,8 voxel) simítjuk, hogy eltüntessük a mélységzajból származó rovátkákat.
5. **Első menet**: a simított mező 99. percentilise, az összes blokkból mintavételezve (legfeljebb 2 millió érték), egy globális szintskálát ad. Blokkonkénti normalizálás egy magányos kiugrót teljes felületté léptetne a saját üres blokkjában.
6. **Második menet**: minden blokk mezőjét osztjuk ezzel a skálával, és marching cubes-ot futtatunk **0,5** szinten. Egy háromszög ahhoz a blokkhoz tartozik, amelybe a **súlypontja** esik, így a varratokat átívelő háromszögek pontosan egyszer keletkeznek.
7. A csúcspontok a voxelközéppontoknál világ-egységekbe kerülnek; minden csúcs megkapja a voxel színét (ahol egy csúcs telítetlen voxelen kívül esik, ott középszürke).

A blokkonkénti kinyerés teszi lehetővé egy pálya méretű szkennelést: egy egyetlen tömb a kilométer négyzetes dobozra 0,25 m-es felbontásban milliárd cella lenne. A `tests/test_track_scale.py` rögzíti, hogy ez ekkora méretnél is működik, a memória pedig arányos a beszkennelt területtel.

### Talaj és szerkezet {#ground-and-structure}

A `classify` minden háromszöget a normálvektorán keresztül címkéz (a kinyert csúcs-normálokhoz igazítva): **35 fokon belül a egyenesen felfelé** `ground` (talaj), minden más `structure` (szerkezet). A nézegető a talajt tömören rajzolja, a szerkezeteket szinte átlátszóan. **A víz soha nem kap címkét** – alakja alapján nem lehet megkülönböztetni a sík talajtól, és egy rossz címke egy udvart tóként rajzolna ki. Minden címke a `.glb` egy részévé válik ([A .glb kimenet](glb-output.md)).

## Lefedettség {#coverage}

A `CoverageGrid(voxel=0.5)` cellánként, félméteres felbontásban négy olyan dolgot rögzít, amelyek nem ugyanazok:

| Tényező | Tárolva | Pontszám (mindegyik 0..1-re vágva) | Miért külön számít |
|---|---|---|---|
| Hányszor látták | azon kulcsképkockák száma, amelyek látták a cellát | `darab / 3` | egyszer látni tipp, nincs mihez hasonlítani |
| Hány irányból | az egységnyi nézeti irányvektorok összege | `(1 - szórás) / (1 - 0,93)`, ahol a szórás az összeg hossza osztva a darabszámmal | húsz képkocka, amely egyenesen egy falnak tart, nem ad parallaxist közöttük; két, harminc fokkal eltérő nézet többet ér |
| Milyen messziről | a legközelebbi nézési távolság | `1 - legközelebbi / 40 m` | a mélységhiba nagyjából a távolság négyzetével nő |
| Mennyire jó a kamera elhelyezése | a legjobb póz-megbízhatóság | maga a megbízhatóság | kétes pózzal összeillesztett geometria rossz helyre kerül |

A képkocka pontjait először cellánként csoportosítjuk, így tízezer egy falon lévő pixel egy megfigyelésnek számít egy irányból.

**A minőség a négy tényező szorzata**, nem átlaga: ezek olyan feltételek, amelyeknek mindegyiknek teljesülnie kell. Egy helyet, amelyet kétszázszor láttak egy irányból, hatvan méterről, rosszul figyeltek meg; egy átlag ezt elrejtené egy kiváló tényező mögött.

A `summary` összesítő adatai: a telített cellák száma, a minőséggel legalább 0,5 rendelkezők aránya („% well seen” az ablakban), az átlagos minőség és a térfogat.

### Gyenge pontok {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. a 0,35 alatti minőségű cellák gyengék;
2. a gyenge cellákat **összefüggőség** szerint csoportosítjuk (26-os szomszédság, unió–keresés csak a telített cellákon – nem a befoglaló téglatesten bejárt rácson, amely hosszú út esetén milliók üres cella lenne);
3. a 8-nál kisebb csoportokat figyelmen kívül hagyjuk;
4. minden csoport okát a cellái leggyengébb tényezőinek leggyakoribbja adja, a helyét pedig a cellái átlaga;
5. a csoportok a legnagyobbtól a legkisebbig (majd a legrosszabb minőség szerint) rendeződnek, legfeljebb 8.

| Ok | Megjelenített tanács |
|---|---|
| kevés nézet | Csak egyszer vagy kétszer láttuk – menj el mellette újra. |
| egy irány | Csak egy szögből látták. Lépj oldalt, és nézd újra. |
| távoli | Csak messziről látták. Menj közelebb hozzá. |
| gyenge követés | A kamera nem volt jól helyezve itt. Közelíts meg lassabban. |

Az összefüggőség számít: egy rögzített blokkrácson való csoportosítás egy elhanyagolt oldalszobát sok különálló gyűrűnek mutatná, és senki nem tudná megkülönböztetni a nyolc helyet attól, ahol ugyanazt a helyet nyolcszor számolták.

### A alaprajz {#the-plan-view}

A `top_down(resolution)` a cellákat az x/z síkra vetíti, és oszloponként a **legjobb** minőséget tartja meg (valaki, aki egy szobában áll, rosszul látja a mennyezetet és kiválóan a padlót; átlagolva a szoba borostyánszínű lenne). A soha nem figyelt oszlopokat külön jelöli. Az ablak 200 x 200-as, az átfedés 120 x 120-as méretben rajzolja ([A lefedettségi térkép](reconstruction-scan-ui.md#the-coverage-map)).

### Rekonstruálható ez? {#is-this-reconstructable}

Minden 25 összeillesztett képkockánál, ha legalább 500 cella van:

| Megállapítás | Ítélet | Üzenet (rövidítve) |
|---|---|---|
| a cellák kevesebb mint 2%-ánál a nézetszórás 0,93 alatt van | nem rekonstruálható | Szinte nincs parallax. Vagy a kamera sosem néz oldalra, vagy a követés sodródik, így ugyanaz a felület sosem landol kétszer ugyanazon a helyen. Ellenőrizd az elhelyezett képkockák számát: ha az magas, sodródás van. |
| a legközelebbi távolság mediánja 25 m fölött | nem rekonstruálható | Mindent N m-ről vagy messzebbről láttak… Menj közelebb ahhoz, amit akarsz. |
| a jó szórású cellák aránya 6% alatt | rekonstruálható, figyelmeztetéssel | Vékony parallax – a geometria durva lesz. Ha oldalirányban mozogsz ahhoz képest, amit nézel, az segít a legtöbbet. |

Az alacsony parallaxisnak két oka van, amelyet ez nem tud megkülönböztetni, ezért nevezi meg az üzenet mindkettőt.

## Szín {#colour}

Az összeillesztés voxelenkénti színe olcsó és élő, de elmosódott: minden pixel egy negyedméteres cellában átlagolódik, beleértve azokat is, amelyeket harminc méterről, élükről láttak. Ezért exportáláskor a háló még egyszer, egyszer kap színt magukból a képkockákból:

- **Megtartott képkockák**: legfeljebb **160** kulcsképkocka (kép és póz), tartálymintavétellel kiválasztva, hogy a teljes szkennelésen oszoljanak el, ne csak a végén.
- **Csúcsonként** (`project_colours`): minden megtartott képkocka hozzájárul, ha a csúcs a kamera előtt van és a képen belül, a felület legfeljebb 70 fokkal fordul el a kamera felé néző állapottól (`|normál . nézet| > 0.34`), 35 m-nél közelebb van, és nincs előtte semmi közelebbi (lent).
- Minden ilyen nézet pontszámot kap: `szembenézés x (1 - távolság / 35)`, így egy közeli, szembenéző nézet megveri a távoli, súroló nézetet. Minden csúcs **4 legmagasabb pontszámú** nézete megmarad – a képkockák sorrendjétől függetlenül, egy jobb nézet kiszorítja a leggyengébb négyet –, és ezeket a pontszámukkal súlyozva keverjük.
- **Takarás**: minden képkockában a háló saját látható csúcsait 2 pixeles cellákból álló mélységpufferbe rajzoljuk, cellánként a legközelebbit megtartva. Egy csúcs, amely több mint `0,3 m + 5%`-kal van a cellájában lévő legközelebbi mögött, abban a képkockában rejtve volt – egy fal a kamera és a mögötte lévő út között –, és ez a nézet nem számít. A teszt csak a hálót ismeri: egy takaró, amelyet nem olvasztottak össze (egy elhaladó autó, egy fülkeoszlop a HUD-maszkon kívül), nem fogódik meg.
- Egy csúcsot, amelyet egyetlen képkocka sem látott, megtartja a voxelszínét; egy csúcs, amelynek egyike sincs, középszürke (a fekete lyuknak látszana).

A szín csúcsonkénti `COLOR_0`-ként íródik, nem textúraatlaszként. A nézegető alapértelmezett megjelenése szürke térkép telített hőszínekkel; a szín arra szolgál, hogy egy szkennelt versenypályán megtaláljuk az utat, ahol a geometria önmagában nem választja el a szegélytől, és a nézegető *Rögzített szín* kapcsolója mögött látható a Háttér / pálya panelen. Az atlasz megsokszorozná a fájlméretet, és kibontóra lenne szükség, egy olyan nézetért, amely szándékosan nem az alapértelmezett. A Blender és más glTF-eszközök olvassák a `COLOR_0`-t.
