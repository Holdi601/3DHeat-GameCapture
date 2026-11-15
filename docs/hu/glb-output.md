---
title: A .glb kimenet
nav_order: 6
lang: "hu"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# A .glb kimenet {#the-glb-output}

A rekonstrukció bináris glTF 2.0 fájlba (`.glb`) íródik, amelyet a 3DHeat megjelenítő a Háttér / pálya
panelján keresztül speciális kezelés nélkül betölt - ugyanazt a szerződést, amelyet az Unreal exportáló ír.
Kód: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Kézzel íródik, nem glTF-könyvtáron keresztül: a kimenet szűk részhalmaz (egy buffer, szorosan csomagolva,
nincs animáció, nincs csontozás), és egy olyan függőség, amely a glTF egészét tudja írni, a verziós
eltéréseivel néhány száz sorért cserébe túl nagy kockázat lenne.

## Mi van egy szkennelés fájljában {#what-is-in-a-scans-file}

| Rész (csomópont- és hálónév) | Tartalom |
|---|---|
| `ground:<name>` | a 35 foknál kisebb szögben felfelé néző háromszögek |
| `structure:<name>` | minden más |

A `<name>` a fájlnév kiterjesztés nélkül, ha az ablakból mentünk, vagy a videó neve a `reconstruct`
esetén. A háromszög nélküli rész kimarad. Szkennelés soha nem ír `water:` részt. Az `asset.generator`
értéke `heat3d-capture-scan`.

## A szerződés {#the-contract}

- **Egy csomópont részenként**, a rész címkéjével elnevezve; a háló ugyanezt a nevet viseli. A
  megjelenítő a *csomópont* nevét olvassa először, ezért ha csak a hálók kapnának nevet, az osztályozás
  elveszne.
- A címke `<class>:<name>` alakú, az osztály `ground`, `structure` vagy `water`. Ez a prefix az, amit a
  megjelenítő illeszt (`^(ground|structure|water)\s*[:|]`), így az osztályt a címkéből veszi át, nem a
  geometriából találgatja. A talaj tömörnek látszik, a szerkezetek majdnem átlátszók.
- **A koordináták a megjelenítő terében vannak**: Y felfelé, jobbsodrású, és **centiméterre skálázva**
  (méter x 100), hogy illeszkedjen az Unreal exportálóhoz. Így egy szkennelés és egy motorexport ugyanazon
  a helyen ugyanakkora méretben, ugyanazokkal a kamera-alapértékekkel töltődik be. A fájl legfelső szintű
  `extras.unit_metres` értéke `0.01` (egy egység egy centiméter), így a méterben dolgozó olvasó, például a
  [`locate`](locate.md), valódi méretében veszi. Egy Forza-telemetriával elhelyezett szkennelés kivétel a
  kezességben: a játék saját világában marad, Y felfelé és balsodrású, pontosan úgy, ahogy a körfájlok
  vannak, így a fölötte rögzített körök rá esnek. Ha egy szkennelés méretarányát későbbi kulcskockán
  találták meg ([Méretarány](reconstruction-pose.md#scale)), ez a tényező beleszámít a kiírt méretarányba.
- A `COLOR_0` értéket a megjelenítő olvassa, és a talajt ezzel színezi, ha a Háttér / pálya panel
  *Rögzített szín* kapcsolója be van kapcsolva (alapértelmezésben ki).
- Az a szkennelés, amelyhez kézzel jelölt helyek vannak, mellé kap egy `<name>.marks.json` fájlt; lásd
  [Mentés](reconstruction-scan-ui.md#saving).
- Primitívenként: `POSITION` (float VEC3, `min` és `max` értékkel, ezekből keretezi a megjelenítő a kamerát),
  `NORMAL` (float VEC3), opcionális `COLOR_0` (float VEC3, 0..1), opcionális `TEXCOORD_0`; az indexek 16
  bitesek, ha minden index kisebb 65 536-nál, egyébként 32 bitesek; mód: triangles.
- Minden buffer-nézet 4 bájtra igazított kezdettel indul; a JSON-blokk szóközökkel, a BIN-blokk nullákkal
  van 4 bájtra kitöltve.

## Ellenőrzések írás előtt {#checks-before-writing}

Minden rész ellenőrzésen megy át. Elutasítja, és a hibaüzenet megnevezi a részt, ha nincs csúcspontja,
az indexek száma nem teljes háromszögekből áll, egy index tartományon kívül vagy negatív, a pozíciók nem
végesek, vagy a normálisok, illetve színek száma nem egyezik a csúcspontok számával. A hiányzó normálisok
kiszámításra kerülnek, **területtel súlyozva** (a marching cubes vékony csíkokat hagy a nagy lapok mellett,
és a súlyozatlan átlag az apró háromszögeket engedné felülírni a lapot, amelyen ülnek); az elfajuló csúcsnál
az irány „felfelé”. Ha egyetlen rész sincs, az hiba.

Ha a térfogatból nincs felület, az export nem ad vissza semmit, és az ablak azt írja: „Nincs mit menteni”.
Így nem születik üres fájl, amely sikeres szkennelésnek látszana.

## Textúrák {#textures}

Az író részenként támogat PNG alapszín-textúrát (UV-koordinátákkal, kétoldalas, nem fémes, teljesen érdes
anyaggal). A szkennelések ezt nem használják; csúcsponti színt hordoznak. Lásd: [szín](reconstruction-fusion-and-texture.md#colour).

## A referenciapálya {#the-reference-level}

A `geometry/reference.py` pontosan ismert méretű szintetikus pályát épít ugyanezen íróval: egy 400 m-es,
felosztott talaj, három 20 x 20 x 12 m-es épület és egy 50 m-es tó 1,5 m-rel a talaj alatt, minden osztály
más, egyszínű színnel. A megjelenítő saját tesztjei generálják, és a megjelenítő valódi olvasójával
dolgozzák fel, így a fájlformátum mindkét oldalon tesztelve marad játék és rögzítőhardver nélkül.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
