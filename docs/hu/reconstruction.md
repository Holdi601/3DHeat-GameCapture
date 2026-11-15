---
title: Pályarekonstrukció
nav_order: 6
lang: "hu"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Pályarekonstrukció játékmenetből {#level-reconstruction-from-gameplay}

Járja be lassan egy pályát, vagy vezessen egy versenypályán, és a szkenner azt, amit a képernyő mutatott,
olyan `.glb` fájllá alakítja, amelyet a 3DHeat megjelenítő a telemetria alatti háttérként tölt be - ugyanazt
a fájlszerződést használva, amelyet az Unreal exportáló ír. Arra az esetre való, amikor senki nem exportálta
a térképet, és a játék fájljai sem olvashatók; a motorexport vagy a játékfájl-export pontos, ez egy becslés.

## A folyamat {#the-pipeline}

```text
 képkockák           kulcskockák          mélység              pozíció              fúzió               kimenet
 ----------          -----------          -------              -------              -----               -------
 Windows Graphics -> képváltozás-     ->  Depth Anything V2 -> vizuális odometria -> foglaltsági térfogat -> marching cubes
 Capture, vagy egy   küszöb (adaptív)     (ONNX Runtime,       (ORB + PnP), vagy    + lefedettségi rács    -> talaj/szerkezet
 videófájl                                 letterboxolva)      Forza-telemetria,    (élő térkép,           -> csúcspontszín
                                                               vagy VGGT-megoldás   gyenge pontok)         -> .glb
                     HUD- / pilótafülke-maszkok, képkockaminőségi tanácsok, talajsík-méretarány
```

| Szakasz | Élő szkennelés (`heat3d_capture.ui`) | Offline (`reconstruct`) | Oldal |
|---|---|---|---|
| Képkockák | monitor, ablak vagy videó, a beállítás leghosszabb oldalára átméretezve | videó, kétszer mintavételezve (megoldási terv és fúziós intervallum) | [Rögzítés](reconstruction-capture.md) |
| Kulcskockák | a kép mennyiben változott, a küszöb a rögzítéshez igazodik | minden `--fuse-interval` másodpercben | [Rögzítés](reconstruction-capture.md#keyframes) |
| Maszkok | változásalapú `ScreenMask`, 40 kulcskocka után áramlásalapú `FlowMask` | a videó négy futtatásából tanult `FlowMask`; a megoldóra nem alkalmazva | [Rögzítés](reconstruction-capture.md#what-is-not-the-world) |
| Mélység | ONNX-modell a legjobb GPU-háttéren | PyTorch Depth Anything V2 Small | [Mélység](reconstruction-depth.md) |
| Pozíció | vizuális odometria, vagy pontos Forza-telemetria | VGGT-ablakok, egy úttá fűzve, interpolálva | [Pozíció](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Méretarány | a kamera magassága a talaj felett (1,15 m) egyszer, vagy telemetria | a megoldott út saját egységei | [Pozíció](reconstruction-pose.md#scale) |
| Fúzió | súlyozott foglaltság, ritka voxelek; lefedettségi rács | ugyanaz | [Fúzió](reconstruction-fusion-and-texture.md) |
| Kimenet | `.glb`, talaj/szerkezet részek, csúcspontszín, centiméterben | ugyanaz | [A .glb kimenet](glb-output.md) |

Kód: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - egy szkennelés beállításai és üteme; `reconstruct.py` - kulcskockák geometriává alakítása;
`offline.py` - az offline útvonal), a szakaszok a `capture/`, `depth/`, `pose/`, `fusion/` és `geometry/`
mappákban vannak.

## Honnan jön a pontosság {#where-accuracy-comes-from}

A monokuláris mélység csak egy ismeretlen méretarányig pontos - egy szoba fényképe és egy babaház fényképe
ugyanaz a kép. Ezért a hálózatra azt bízzuk, amihez jó (a relatív alak, az élek, a vékony szerkezetek), a
méretarányt és a kamera útvonalát pedig olyan forrásból vesszük, amely ismeri azokat:

| Játék | Kamera-útvonal | Méretarány |
|---|---|---|
| Forza Horizon / Motorsport telemetriával | pontos, a Data Outból, minden képkocka rögzítési idejére interpolálva | pontos: a mélység két ismert pozíció közti jellemzők háromszögelésével rögzül |
| Bármi más, élőben | vizuális odometria, képkockáról képkockára láncolva | egyszer rögzítve, egy feltételezett kamera-magasságból a talaj felett |
| Felvétel, offline | VGGT, átfedő ablakokon megoldva | a megoldás saját egységei (nem metrikusak) |

Az egyetlen szám, amelyet a szkenner megkap, és nem mér, a játék **vízszintes látószöge** (az ablakban
alapértelmezésben 90 fok; a versenyjátékok inkább 65 körül vannak). Ha túl szűk, a pálya mélyebbnek
rekonstruálódik, mint amilyen; ha túl tág, lelapul.

## A felhasználó korai tájékoztatása {#telling-the-user-early}

A szkennelés fizikai tevékenység - valaki több percen át végigjár egy pályát -, és a drága hiba az, ha a
séta végén derül ki, hogy nem volt jó. Ezért az ablak a szkennelés indítása előtt megméri ennek a gépnek a
mélységi átbocsátóképességét, és megmondja, milyen lesz a szkennelés ([Futtatókörnyezet](runtime.md#what-to-expect-from-this-machine));
közben lefedettségi térképet mutat számozott gyenge pontokkal, a követés állapotát, egy sebességsávot, egy
élességi sávot, és egyszerre egy utasítást - az ablakban és a játék fölé helyezett, átkattintható rétegen
([A szkennelőablak](reconstruction-scan-ui.md)).

## Mérés szintetikus referencián {#measured-on-synthetic-ground-truth}

A `tests/test_accuracy.py` egy 12 x 8 m-es szobát (4 m magas) renderel ismert kameraútvonalról,
analitikus (nem hálózati) mélységgel, és 0,2 m-es voxelekkel rekonstruálja. Ellenőrzi, hogy a képkockák több
mint 90%-a elhelyezhető, az átlagos úthiba 0,35 m alatt van (a legrosszabb 1 m alatt), a megtett táv a valós
érték 10%-án belül van, a szoba szélessége 1,5 m-en belül helyes, a falfelület több mint 75%-a 0,45 m-en
belül esik valódi falra, egy felmérés-jellegű séta határozottan jobb lefedettséget ad, mint az egyenesen
előre gyaloglás, és egy textúrátlan jelenetet elutasít, nem pedig kitalál. Az analitikus mélység a pozíciót,
a méretarányt és a fúziót különíti el a hálózattól; az, hogy a hálózat valódi játékmenetben hogyan teljesít,
külön kérdés, amelyre egyetlen szintetikus jelenet sem ad választ. A `tests/test_track_width.py` ellenőrzi,
hogy a szélétől eltérő vonalon megtett, ismert szélességű úton készült kör a út szélességét rekonstruálja,
nem csak a megtett vonalat.

## Oldalak {#pages}

- [A szkennelőablak](reconstruction-scan-ui.md) - minden vezérlő, gyorsbillentyű és réteg
- [Rögzítés, maszkok és képkockaminőség](reconstruction-capture.md)
- [Mélység](reconstruction-depth.md)
- [Kamera-pozíció és méretarány](reconstruction-pose.md)
- [Fúzió, lefedettség és szín](reconstruction-fusion-and-texture.md)
- [A .glb kimenet](glb-output.md)
- [Offline rekonstrukció](reconstruction-offline.md)
