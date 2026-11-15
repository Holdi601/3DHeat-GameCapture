---
title: "Csúszás, driftszög és származtatott csatornák"
nav_order: 8
lang: "hu"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Csúszás, driftszög és származtatott csatornák {#slip-drift-and-derived-channels}

A nézegető Versenyelemzés fülének autóvezetés-elemzéséhez minden játékból ugyanazokra a néhány mennyiségre van szükség: mennyire csúszik minden gumi, mennyire néz az autó arrafelé, amerre nem halad (a driftszög), van-e a levegőben, és laza talajon van-e. A játékok ezeket nagyon különböző formában küldik, vagy egyáltalán nem. Az itteni rögzítők azt írják, amit az egyes játékok küldenek, kanonikus nevekkel, plusz egy `meta.slip` megjegyzéssel arról, mit jelentenek a csúszási számok; a nézegető azután származtatja, ami hiányzik, egyszer, amikor betölt egy kört. **A játék saját értéke mindig nyer egy származtatott érték felett.**

## Amit a rögzítők írnak {#what-the-recorders-write}

| Játék | Csúszási csatornák | `meta.slip` | Driftszög bemenetei |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` kerekenként, ahogy küldik | `peak` (a rögzítő írja; a nézegető `.tele.gz` olvasója ugyanezt állítja be) | `latVel`, `longVel` az autó-helyi sebességből |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plusz `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` az autó keretében lévő sebességből |
| EA SPORTS WRC, DiRT-játékok | nincs; helyette `wheelSurfaceSpeed` kerekenként | `null` | `latVel`, `longVel` = a világsebesség az autó tengelyeire vetítve |
| Richard Burns Rally | nincs; kerékfordulatszám sincs | nincs | `latVel`, `longVel` = az autó saját oldalirányú és előre irányú sebessége |
| BeamNG.drive | nincs; `wheelSurfaceSpeed` és `wheelSpeed` kerekenként | nincs | `latVel`, `longVel` = a világsebesség az autó tengelyeire vetítve |
| Trackmania | `slipIndex` kerekenként (0..1-es csúszásmérték) | `index` | `latVel` (oldalsebesség), `longVel` (előrehaladási sebesség) |
| iRacing | nincs (nincs naplózva) | nincs | `yaw` és az útvonal, `yawRate` |

A `meta.slip` értékeit a [A heat3d-lap fájl](lap-format.md) oldal határozza meg: `peak` (normalizált, így 1 felett a gumi elengedi az utat), `scaled` (fizikai csúszás osztva egy tipikus aszfaltcsúccsal), `physical` (törtszám és radián), `index` (0..1-es csúszásmérték).

### Miért skálázzuk a Kunos csúszását {#why-kunos-slip-is-scaled}

A Forza csúszása úgy van normalizálva, hogy 1 a tapadás határa; hogy mihez normalizál, azt nem dokumentálják. A Kunos a fizikai csúszási arányt (törtszám) és csúszási szöget (radián) küldi. Ezeket egy tipikus aszfaltcsúccsal osztva – 0,12 az aránynál, 0,14 rad (körülbelül 8 fok) a szögnél – azt érjük el, hogy az „1 felett csúszik” állítás mindkét családnál nagyjából igaz legyen, így a nézegető kijelzőinek egy olvasata marad. Ez közelítés: a valódi csúcsok gumitól és felülettől függnek, ezért tartjuk meg a nyers értékeket a skálázottak mellett, és ezért méri a nézegető a köröknek magukból azt, hol kezd elfogyni az egyes autók tapadása.

## Amit a nézegető származtat (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Ezek a nézegetőben futnak (a 3DHeat nézegető `src/race/derive.ts` fájljában), nem ebben a tárolóban.

### Driftszög, `bodySlip` {#drift-angle-bodyslip}

- **Az autó keretében lévő sebességből**, ha `latVel` és `longVel` jelen van: `atan2(latVel, |longVel|)`, és 3 m/s alatt 0 (az oldalra megállt autó nem driftel).
  Az előjele a játék oldalirányú sebességét követi, amelynek iránya egyes játékoknál mindkét irányban dokumentált – a nagyságát olvasd, ne az előjelét.
- **Különben az iránynak az útvonalhoz képesti eltéréséből**: a haladási irányt minden minta két oldalán nagyjából 2 m-re lévő pozíciókból vesszük (`atan2(dx, dz)`); a játék `yaw`-ját ehhez illesztjük előjellel és eltolással (minden játéknak saját nullpontja és forgási iránya van), 10 m/s feletti mintákat használva, és csak akkor bízunk benne, ha utána szorosan egyezik (körkörös szórás legfeljebb 0,05, legalább 20 minta). A driftszög a különbség; 3 m/s alatt 0.

### Csúszási arány a kerekekből {#slip-ratio-from-the-wheels}

Ahol egy körből hiányzik a `slipRatio.*`, de van kerékfordulatszám, a csúszási arány `(kerék - autó) / autó` kerekenként, ebből:

- `wheelSurfaceSpeed.*` (az érintkezési folt sebessége, m/s), ha küldik (EA WRC, DiRT, BeamNG), közvetlenül;
- egyébként `wheelSpeed.*` (forgás, rad/s) szorozva egy a körön mért **gördülősugárral**: a `speed / |omega|` mediánja azokon a mintákon, ahol az autó egyenesen gurul (10 m/s felett, nincs a levegőben, gázállás 0,3 alatt, fék 0,05 alatt, hosszirányú gyorsulás 3 m/s² alatt); 20-nál kevesebb ilyen mintánál minden 10 m/s feletti minta. A 0,1–1 m-en kívüli sugár elvetődik.

Csak akkor, ha mind a négy kerék származtatható; a kör `meta.slip` értéke ekkor `physical` lesz. 3 m/s alatt a csúszás 0.

### Levegőben {#airborne}

Az `airborne` 1, ha minden kerék elhagyta a talajt; ezt a kör első olyan csatornája dönti el, amely mind a négy kerékre megvan:

1. `groundContact.*` (BeamNG): egyik kerék sincs 0,5 fölött;
2. `wheelLoad.*` (AC-játékok, RBR, BeamNG): egyik kerék sem 5%-nál nagyobb a saját mediánterhelésénél;
3. `suspension.*` (0..1 az utazásból): egyik kerék sincs 0,02 fölött, azaz mind teljesen kinyújtva.

Egyetlen elszigetelt levegős mintát törlünk. A Trackmania maga írja az `airborne`-t.

### Laza talaj {#loose-ground}

Ahol egy körben van `surfaceRumble.*` (Forza), a `loose` 1, ahol legalább két kerék legalább a harmadmásodpercen át zörgést jelez, a egy másodpercnél rövidebb réseket áthidalva (egy sima folt egy kavicsos úton még kavicsos út). A Trackmania maga írja a `loose`-t a kerekek talajanyagából.

### Fordulási sebesség {#yaw-rate}

Ahol egy körben van `yaw`, de nincs `yawRate`, az a szomszédos minták közötti yaw-változás.

## Amit a rögzítők maguk származtatnak {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): minden rögzítő a Forza kivételével (amely küldi) a `suspensionM.*`-ből írja, az adott körben használt tartományon belüli pozícióként (minimumtól maximumig). Az autó felfüggesztési rúdjaihoz és egy a levegőben lógó kerék észleléséhez szolgál; nem abszolút utazási arány.
- **`steer`** a Kunos-játékoknál, körönként skálázva (lásd [Assetto Corsa játékok](telemetry-assetto-corsa.md)).
- **Gyorsulások** a BeamNG-nél, a világsebesség változásából ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** és a függőleges tengely a Richard Burns Rallynál, a pozíciókból ([Ralijátékok](telemetry-rally.md)).

## Kezesség {#handedness}

Ahol egy játék világa balkezes – a Forzáé az –, a pálya tükrözve jön ki egy jobbkezes nézegetőben; a körök saját kormányzása és felfüggesztése elárulja ezt. A rögzítők nem változtatják a kezességet: a Z-felfelé világot (BeamNG) egy forgatás Y-felfelé fordítja, ami megtartja a kezességet, minden más pedig úgy íródik, ahogy érkezik.
