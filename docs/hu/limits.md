---
title: "Korlátok és ellenőrzés"
nav_order: 9
lang: "hu"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Korlátok és amit ellenőriztek {#limits-and-what-is-verified}

Őszinte lista: mit nem csinálnak az eszközök, és mi nincs ellenőrizve egy futó játékkal szemben.

## Telemetria {#telemetry}

| Felvevő | Állapot |
|---|---|
| Forza | A hivatalos Data Out dokumentáción alapul; az elrendezést maguk a csomagok alapján érzékeli. A nézegető FH Companion `.tele.gz` olvasóját valódi köröken ellenőrizték. |
| AC, ACC, AC EVO, AC Rally | Szintetikus oldalakon tesztelték, a közzétett elrendezésekből építve. **Még nem futtatták élő játékok ellen.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | A dokumentált elrendezésekből épített csomagokon tesztelték. **Még nem futtatták élő játékok ellen.** Az RBR tengelyei, hozzáállása és sebességegységei nincsenek dokumentálva, ezeket az adatokból kezelik. |
| BeamNG.drive | A felvevőt a mod szerkezetéből épített csomagokon tesztelték. **A modot nem futtatták a játékban.** |
| Trackmania | A nézegető CSV-olvasóját tesztelték. **A bővítményt nem futtatták a játékban.** Csak az Openplanet fejlesztői módjában tölt be. |
| iRacing | A nézegető `.ibt` olvasóját egy szintetikus fájlon tesztelték. |

Egyéb telemetriai korlátok:

- A Forza csúszás-normalizálása nincs dokumentálva. A Kunos-csúszást egy tipikus aszfalt-csúcsértékkel skálázzák, ez közelítés.
- Néhány autó-keretbeli oldalirány előjele (Kunos, DiRT) kétféleképpen is dokumentált. A drift szögének nagysága megbízható, az előjele nem.
- Egyik rally-játék sem küld kerékcsúszást; a nézegetőben származtatják. Az RBR nem küld kerékfordulatszámot.
- Egy rally-szakasz felülete csak akkor íródik ki, ha meg van adva a `--surface`. Különben a fájl nem nevez meg egyet, és a nézegető következtet (szakasz- vagy eseménynév, aztán vezetési stílus, alapesetben lazán).
- A körszámláló nélküli körfelismerés (AC EVO, AC Rally, BeamNG) azt a pontot használja vonalként, ahol a felvétel elkezdődött, ezért a rajtvonalnál kezdd a felvételt.
- Egy BeamNG-jármű visszaállítása abban a pillanatban lezárja a nyitott kört. Részleges futásként íródik ki, ha legalább a minimális távolságot (300 m) lefedte, különben eldobják.
- A `route` kb. 2 másodpercenként ment vezetés közben. Összeomlás vagy megölt folyamat legfeljebb az utolsó mentés óta gyűjtött pozíciókat veszíti el.
- A Forza Horizon nem küld pályanevet, ezért a Forza-körfájlokban `"track": null` van. A Forza Motorsport (2023) csak egy számot küld, ezt `lap.trackOrdinal`-ként tartjuk meg.

## Rekonstrukció {#reconstruction}

- **A mélység becsült, nem olvasott.** Ez a megközelítés plafonja, és annak ára, hogy a játék folyamatához soha nem nyúl.
- **A látómező feltételezett, nem mért.** Túl szűk esetén a pálya mélyebbnek rekonstruálódik, mint amilyen.
- **A globális léptéket** egy feltételezett kamera-magasság adja (1,15 m az ablakban), vagy a telemetria. Az első kulcskockán mérik. Ha ott nincs használható talaj, a következő kulcskockákat próbálják (legfeljebb 30 képkocka), a később talált lépték pedig az egész pályára érvényes, amikor kiíródik. Az ablak „Size:” sora megmondja, mi történt. Ha egyáltalán nincs talaj, a szkennelés mértékegység nélküli marad. Ilyenkor a voxelméret az első képkocka egységeiben van, így a méterben mért mérete eltér a beállítástól. Az offline rekonstrukciók a megoldás saját egységeiben vannak.
- **A hurokzárás ki van kapcsolva**, és kódban bekapcsolva sem pózgráf. A sodródást csak a képkockáról-képkockára követés minősége korlátozza.
- **Az ablakos köteg-korrekció létezik, de nincs bekötve**; valódi felvételen összeomlott.
- **A felület súlyozott kitöltöttség, nem TSDF**: a vékony szerkezetek és a szabad tér rosszabb, mint TSDF-fel lenne.
- **Nincs textúra-atlasz.** A szín csúcsonként van (`COLOR_0`), a 160 megtartott képkockából a 4 legjobb nézetből keverve. A takarási teszt durva: a háló saját csúcsaihoz hasonlítja egy 2 pixeles mélységpufferben, így a háló által nem tartalmazott takaró (egy elhaladó autó) nem fogódik meg.
- **A víz soha nincs címkézve**; minden talaj vagy szerkezet.
- **A visszacsatolásos megoldás nem élő**: a felvételt előbb meg kell kapnia. A nehéz szakaszok adaptív újra-megoldása nincs megépítve.
- **A telemetriás pózok** a kamerát az autóhoz helyezik (egy követő kamera eltolása ismeretlen). A pozíciókat úgy vesszük, ahogy a Forza küldi (Y felfelé, mint a körfájlokban). A yaw, pitch és roll irányát a rögzített körökből olvasták le (haladási irány, lejtő, melyik oldal rugózása nyomódik össze), nem a futó játék kamerájából.
- A fedvény **kizárólagos teljes képernyő** felett nem tud rajzolni; használj szegélyezett ablakos módot.
- A globális billentyűparancsok, a kattintás-áteresztő fedvény és az élő rögzítés **csak Windowsra** működik.
- Az ablak bezárásakor nem kérdez a mentésről.

## Mit mértek {#what-is-measured}

- `tests/test_accuracy.py`: egy szintetikus szoba ismert úttal és analitikus mélységgel. Mérik az elhelyezett képkockákat, az útvonalhibát, a megtett távolságot, a szobaméretet és a falak felületét ([Pályarekonstrukció](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: egy ismert szélességű utat, amelyen középről eltérve haladnak, a szélességét rekonstruálja.
- `tests/test_track_scale.py`: felületkinyerés versenypálya-méretben, a memória arányos azzal, amit beszkenneltek, a blokkok egy felületté állnak össze.
- `tests/test_glb.py` a nézegető saját tesztjeivel együtt: a `.glb`-szerződés mindkét oldalról.
- Hogy a mélységhálózat valódi játékmenetben hogyan teljesít, azt egy szintetikus jelenet nem tudja megválaszolni, és a tesztcsomag sem méri.
