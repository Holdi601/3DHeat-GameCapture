---
title: "Játékok"
nav_order: 4
lang: "hu"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Játékok: rögzítés és pályák {#games-recording-and-courses}

Hogyan rögzítjük az egyes támogatott játékokat, mit küldenek, és melyik pályáik exportálhatók a játék saját fájljaiból.

A szabályok minden játékra ugyanazok: a pálya a felhasználó saját fájljaiból származik, vagy a felhasználó saját játékmenetéből rekonstruálódik. A titkosított archívumok csak olyan kulccsal nyílnak meg, amelyet a felhasználó már birtokol – itt semmi nem szállít kulcsokat és nem fejt vissza kulcsokat, és semmi nem nyúl bele egy játék folyamatába. A telemetria csak azokból az interfészekből jön, amelyeket a játékok közzétesznek (UDP-kimenetek, megosztott memória, saját mod- és bővítményinterfészek). Az, hogy a felhasználó mire irányítja az eszközöket, továbbra is az adott játék licencétől függ.

## Telemetria {#telemetry}

Minden játék `heat3d-lap` fájlokká lesz ([`lap-format.md`](lap-format.md)), egységes csatornanevekkel és egy `meta` blokkal, amely megmondja, mit jelentenek a számai – hogyan skálázzák a csúszást, pálya, rally vagy arcade-e, és ha ismert, a felület. Így az olvasó mindet egyformán kezeli. Minden parancs `python -m heat3d_capture ...` alakú ebben a tárolóban.

| Játék | Hogyan rögzítsd | Pozíció | Gumik és csúszás | Driftszög | Állapot |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out UDP-n: `heat3d_capture telemetry` (továbbítja az FH Companionnak) – vagy az FH Companion saját `.tele.gz` fájlja minden kör mellett, a körfájllal együtt betöltve | világ XYZ | kerekenkénti csúszási arány, csúszási szög, összesített csúszás, normalizálva; felületi zörgés | autó-keretbeli sebesség | a rögzítő tesztelve; a `.tele.gz` olvasó valódi köröken ellenőrizve |
| Forza Motorsport (a 2023-as is) | ugyanaz; a csomaghossz alapján különböztetjük meg | világ XYZ | ugyanaz | ugyanaz | a rögzítő tesztelve |
| Assetto Corsa, ACC, AC EVO | megosztott memória: `telemetry --game ac / acc / acevo` | a négy gumi érintkezési pontjának átlaga | csúszási arány és szög (fizikai, egy tipikus aszfaltcsúcs szerint skálázva); ABS és TC működésben (ACC, EVO) | autó-keretbeli sebesség | a rögzítő szintetikus oldalakon tesztelve |
| Assetto Corsa Rally | `telemetry --game acrally` | ugyanaz | ugyanaz; kerékterhelések; a hőmérsékletek kelvinből átszámítva | autó-keretbeli sebesség | a rögzítő szintetikus oldalakon tesztelve |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Dokumentumok>/My Games/WRC/telemetry/config.json"` bekapcsolja az alapértelmezett `wrc` csomagot (a fájlról előbb biztonsági mentés készül) | világ XYZ | érintkezési folt sebessége kerekenként; a csúszás származtatott | az autó tengelyeiből és a sebességéből | a rögzítő a dokumentált elrendezés szerint épített csomagokon tesztelve |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: állítsd be a `<udp enabled="true" extradata="3" port="20777" delay="1" />` sort a `hardware_settings_config.xml` fájlban, majd `telemetry --game dirtrally2` (vagy `dirtrally`, `dirt4`) | világ XYZ | érintkezési folt sebessége kerekenként; a csúszás származtatott. Nincs kézifék-csatorna | az autó tengelyeiből és a sebességéből | ugyanaz |
| Richard Burns Rally (RSF/NGP) | az NGP UDP-telemetriája (`udpTelemetry=1`): `telemetry --game rbr` | világ, a függőleges tengely a szakaszból derül ki | rugóbehajlás és erő kerekenként; kerékfordulatszám nincs | az autó saját sebességei | ugyanaz; a tengelyek és a sebességegység nincs dokumentálva, az adatokból kezeljük |
| BeamNG.drive | a `heat3d` protokollmod: `telemetry --game beamng --install`, majd Options > Other > Protocols > "others" | világ, Y felfelé fordítva | kerék felületi sebessége, forgása, terhelése, talajérintkezése; csúszás származtatott | az autó tengelyeiből és a sebességéből | a rögzítő a mod struktúrájából épített csomagokon tesztelve; a modot a játékban még nem tesztelték |
| Trackmania (2020) | az Openplanet-bővítmény, a `Heat3dRecorder`: `telemetry --game trackmania --install`, az Openplanet fejlesztői módjában betöltve; futásonként egy CSV a tárolómappájában | világ XYZ | a Trackmania csúszási együtthatója kerekenként; laza talaj a kerekek anyagaiból; levegőben | oldalirányú és előre irányuló sebesség | az olvasó tesztelve; a bővítményt a játékban még nem tesztelték |
| iRacing | a saját `.ibt` fájljai; nincs szükség rögzítőre | szélesség/hosszúság/magasság, érintősíkra vetítve | nincs csúszás (nincs naplózva); fordulási sebesség és oldalirányú gyorsulás | a fordulási sebességből az útvonallal szemben | az olvasó szintetikus fájlon tesztelve |

Amit a ralijátékok közül egyik sem küld – a gumicsúszást –, azt az olvasó számolja ki: ahol a játék küld kerekenkénti érintkezési folt- vagy felületi sebességet, ott az adott kerék és az autó sebességének különbségéből (`(kerék - autó) / autó`); ahol csak forgást küld, ott a forgásból és a körön magán mért gördülősugárból. A driftszöget az autó saját sebességéből számoljuk (Forza, az AC-játékok, Trackmania, RBR), vagy a világsebességnek az autó tengelyeire vetítéséből (EA WRC, DiRT, BeamNG), vagy az irány és az útvonal eltéréséből. Azt, hogy az autó a levegőben van-e, a kerekek érintkezéséből, terheléséből vagy felfüggesztéséből tudjuk meg.

Ahol egy játék világa balkezes – a Forzáé az –, ott a pálya tükrözve jön ki egy jobbkezes nézegetőben; a körök saját kormányzása és felfüggesztése elárulja ezt. Azok a játékok, amelyek kézrendszere nincs dokumentálva (RBR, BeamNG, Trackmania), ugyanígy kezelődnek: megmérjük, nem feltételezzük.

A vezetési csatornákon túl a rögzítők megtartják, amit minden játék hozzátesz: az AC-játékok ABS- és traction control-működését, a fékeloszlást, a DRS-t, a boxutca-korlátozót, a turbónyomást, valamint a fékbetétek és a tárcsák élettartamát; az iRacing segédbeállításait, a fékeloszlást, az üzemanyag-, olaj- és vízhőmérsékletet, és minden más csatornát, amelyet saját néven naplóz.

### Források és ami még nincs megerősítve {#sources-and-what-is-not-yet-confirmed}

- **Forza:** a hivatalos Data Out dokumentáció (Forza Motorsport; Forza Horizon 6) a mezőkhöz, azok mértékegységeihez és az autó keretéhez (x jobbra, y felfelé, z előre – balkezes). Azt, amihez a Forza a csúszását normalizálja, nem dokumentálja: ahelyett, hogy feltételeznéd, hogy az 1 a határ, mérd meg, hol kezd el az egyes autók tapadása ténylegesen elfogyni.
- **Kunos:** az AC1 SDK, az ACC megosztott memória dokumentációja v1.8.12, az `albertowd/live-telemetry-evo` (EVO, mérve; az AC Rally az ACC elrendezését használja, „bájtonkénti vizsgálattal megerősítve”), a `LuizZak/AssettoCorsaRallyTelemetryReader`. Hogy melyik oldalra mutat az autó-keretbeli x tengely, azt a dokumentáció mindkét irányban írja le: a driftszög nagyságát használd, nem az előjelét.
- **EA SPORTS WRC:** az EA UDP Telemetry Guide v1.3 és a csatornalista, amelyet a játék a `readme/channels.json` fájlba ír; az alapértelmezett `wrc` csomag eltolásai, ahogy a nobonobo/obs-codemasters-telemetry dekódolja. Az alapértelmezett port nincs dokumentálva; a rögzítő 20777-re kapcsolja be a csomagot.
- **DiRT:** a Codemasters DiRT 4 UDP-dokumentuma, az ErlerPhilipp/dr2_logger, a soong-construction/dirt-rally-time-recorder. Az oldalvektor irányát és a felfüggesztési pozíció mértékegységét mindkét irányban dokumentálják; egyik sem dönt el semmilyen megállapítást.
- **RBR:** az NGP `rbr.telemetry.data.TelemetryData.h` fájlja (a mika-n/RBRUDPTelemetryLogger és a groybe/rbr-udp-telem közvetítésével). A pozíciótengelyek, a hozzáállás mértékegységei és a sebességegység nincs dokumentálva: a rögzítő a függőleges irányt a szakaszból veszi, a sebességet a pozíciókból.
- **BeamNG:** a documentation.beamng.com (protocols; refNodes: a jármű +X balra, -Y előre, Z felfelé), és a játék saját `lua/vehicle/protocols.lua` és `wheels.lua` fájljai. Az OutSim a jelenlegi verziókban csonk; az OutGauge-nak nincs pozíciója, a MotionSim-nek nincsenek kerekei – ezért kell a mod.
- **Trackmania:** az Openplanet `CSceneVehicleVisState` és VehicleState bővítménye, a `CSmScriptPlayer` versenyidő. Az Openplanet-bővítmények nem tudnak UDP-t küldeni, ezért a bővítmény fájlokat ír. Az aláíratlan bővítmények csak fejlesztői módban töltődnek be, ami korlátozza az online játékot; a bővítmény az openplanet.dev oldalon aláírható.

A rögzítők egyikét sem futtattuk még az élő játékokon; mindegyiknél az első valódi munkamenet a döntő teszt, és a `tests/test_kunos.py`, a `test_rally.py` és a `test_beamng.py` azokat az elrendezéseket rögzíti, amelyekre készültek. Minden rögzítő ellenőrzi a csomagjait, ahogy érkeznek – a sebességet a mért sebességgel, a struktúra méretét –, és jelzi, ha egy elrendezés nem stimmel.

## Pályák: mit exportálunk játékonként {#courses-what-is-exported-per-game}

A pálya hozzáadja a szegélyeket, falakat és a kifutót, amelyek megmagyarázzák a vonalat. A pályákat a [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) exportálja (`python -m heat3d_gamefiles course <kör>`), a játék saját fájljaiból, ahol ezt egy telepített példányon megépítették és ellenőrizték. A részletek a [GameFiles dokumentációjában](https://holdi601.github.io/3DHeat-GameFiles/) vannak.

| Játék | Pálya egy körből |
|---|---|
| Forza Horizon | igen |
| BeamNG.drive | igen |
| Assetto Corsa Rally | igen |
| Assetto Corsa EVO | nem: tartalma nem olvasható fájlként |
| iRacing | nem: a pályamodellek védett formátumban érkeznek |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | még nem: mindegyikhez telepített példány kell az elkészítéshez és az ellenőrzéshez |

Addig is a lenti játékmenet-útvonal minden játékra működik.

## Az útvonal, amely minden játéknál működik {#the-route-that-works-for-every-game}

A GameCapture játékmenet-videóból rekonstruál egy pályát. A nehéz része a kamera útvonala, és a Forzánál ez pontos, mert a telemetria minden képkockánál megadja az autó pozícióját. Most minden fent említett játéknál van ugyanilyen: pozíció és hozzáállás, élőben, dokumentált interfészről. Ezeknek a `pose/telemetry_pose.py`-ba a Forza adatai helyett való betáplálása az egyetlen rész, amely a játékmenet-útvonalat mindegyiknél pontossá teszi – a folyamat többi része (mélység, összeillesztés, textúrázás) nem törődik azzal, melyik játék rajzolta a képkockákat.
