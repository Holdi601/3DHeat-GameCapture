---
title: "Rekonštrukcia levelu"
nav_order: 6
lang: "sk"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonštrukcia levelu z hrania {#level-reconstruction-from-gameplay}

Prejdite level pomaly alebo prejdite trať autom a skener premení to, čo ukázala obrazovka, na
`.glb`, ktorý prehliadač 3DHeat načíta ako kontext pod telemetriou - rovnaká zmluva súboru, aká
sa zapisuje exportérom Unreal. Je to pre prípad, keď nikto mapu nevyexportoval a herné súbory
sa nedajú čítať; export z motora alebo herných súborov je presný, toto je odhad.

## Postup {#the-pipeline}

```text
 snímky              kľúčové snímky       hĺbka                pózy                 fúzia               výstup
 ------              --------------       -----                ----                 ------              ------
 Windows Graphics -> prah zmeny       ->  Depth Anything V2 -> vizuálna odometria -> objemová mriežka -> marching cubes
 Capture, alebo      obrazu                (ONNX Runtime,        (ORB + PnP), alebo   + mriežka pokrytia  -> terén/stavba
 súbor videa         (adaptívny)           letterboxed)          telemetria Forza,    (živá mapa,          -> farba vrcholov
                                                                 alebo riešenie VGGT  slabé miesta)        -> .glb
                     masky HUD / kokpitu, rady ku kvalite snímok, mierka z roviny terénu
```

| Krok | Živé skenovanie (`heat3d_capture.ui`) | Offline (`reconstruct`) | Stránka |
|---|---|---|---|
| Snímky | monitor, okno alebo video, zmenšené na najdlhšiu stranu predvoľby | video, vzorkované dvakrát (plán riešenia a interval fúzie) | [Snímanie](reconstruction-capture.md) |
| Kľúčové snímky | ponechané podľa toho, koľko sa obraz zmenil; prah sa prispôsobuje snímaniu | každých `--fuse-interval` sekúnd | [Snímanie](reconstruction-capture.md#keyframes) |
| Masky | zmena založená na `ScreenMask`, potom `FlowMask` založená na toku po 40 kľúčových snímkach | `FlowMask` naučená zo štyroch behov videa; neaplikuje sa na riešiteľ | [Snímanie](reconstruction-capture.md#what-is-not-the-world) |
| Hĺbka | model ONNX na najlepšom backende GPU | PyTorch Depth Anything V2 Small | [Hĺbka](reconstruction-depth.md) |
| Póza | vizuálna odometria, alebo presná telemetria Forza | okná VGGT spojené do jednej dráhy, interpolované | [Póza](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Mierka | výška kamery nad terénom (1,15 m) raz, alebo telemetria | jednotky vyriešenej dráhy | [Póza](reconstruction-pose.md#scale) |
| Fúzia | vážený objem obsadenosti, riedke voxely; mriežka pokrytia | to isté | [Fúzia](reconstruction-fusion-and-texture.md) |
| Výstup | `.glb`, časti terén/stavba, farba vrcholov, centimetre | to isté | [Výstup .glb](glb-output.md) |

Kód: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - nastavenia skenovania a tempo; `reconstruct.py` - kľúčové snímky na geometriu;
`offline.py` - offline cesta), s krokmi v `capture/`, `depth/`, `pose/`, `fusion/`
a `geometry/`.

## Odkiaľ prichádza presnosť {#where-accuracy-comes-from}

Hĺbka z jedného obrazu je správna len až do neznámej mierky - fotka izby a fotka domčeka pre bábiky
sú ten istý obraz. Sieť preto robí to, v čom je dobrá (relatívny tvar, hrany, tenké konštrukcie),
a mierka a dráha kamery pochádzajú odniekiaľ, kto ich pozná:

| Hra | Dráha kamery | Mierka |
|---|---|---|
| Forza Horizon / Motorsport so zapnutou telemetriou | presná, z Data Out, interpolovaná na čas zachytenia každého snímku | presná: hĺbka je ukotvená triangulovaním znakov medzi dvoma známymi pózami |
| Ostatné, živé | vizuálna odometria, reťazená snímok po snímku | raz pevne podľa predpokladanej výšky kamery nad terénom |
| Nahrávka, offline | VGGT, riešené cez prekrývajúce sa okná | jednotky riešenia (nie metrické) |

Jediné číslo, ktoré skener dostane od používateľa a nezmeria ho sám, je **horizontálny zorný uhol**
hry (predvolene 90 stupňov v okne; pretekárske hry sú bližšie k 65). Príliš úzky a level sa
rekonštruuje hlbší, než je; príliš široký a sploští sa.

## Včasné upozornenie používateľa {#telling-the-user-early}

Skenovanie je fyzický úkon - niekto prejde level niekoľko minút - a drahé zlyhanie je dokončiť
prechod a zistiť, že bol zbytočný. Okno preto ešte pred štartom zmeria priepustnosť hĺbky na tomto
počítači a povie, aký bude výsledok skenovania ([Runtime](runtime.md#what-to-expect-from-this-machine));
počas skenovania ukazuje mapu pokrytia s očíslovanými slabými miestami, zdravie sledovania, lištu
rýchlosti chôdze, lištu ostrosti a jednu inštrukciu naraz, v okne aj v priehľadnom prekrytí cez
hru ([Okno skenovania](reconstruction-scan-ui.md)).

## Meranie na syntetickej overenej pravde {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` vykreslí miestnosť 12 x 8 m (4 m vysokú) zo známej cesty kamery, s
analytickou (nie sieťovou) hĺbkou, a rekonštruuje ju s voxelmi 0,2 m. Overuje, že sa umiestni viac
ako 90 % snímok, že priemerná chyba dráhy je menej ako 0,35 m (najhoršia pod 1 m), že prejdená
vzdialenosť je v rozmedzí 10 % od skutočnosti, že šírka miestnosti vyjde správne s odchýlkou do
1,5 m, že viac ako 75 % plochy stien leží do 0,45 m od skutočnej steny, že prechod typu prieskumu
dosiahne zreteľne lepšie pokrytie ako chôdza rovno dopredu, a že scéna bez znakov je odmietnutá
namiesto toho, aby sa niečo vymyslelo. Analytická hĺbka izoluje pózu, mierku a fúziu od siete;
ako si sieť poradí so skutočným hraním, je iná otázka, na ktorú žiadna syntetická scéna neodpovie.
`tests/test_track_width.py` overuje, že kolo jazdené mimo stredu na ceste známej šírky
rekonštruuje šírku cesty, nielen jazdenú čiaru.

## Stránky {#pages}

- [Okno skenovania](reconstruction-scan-ui.md) - každé ovládanie, klávesová skratka a prvok prekrytia
- [Snímanie, masky a kvalita snímok](reconstruction-capture.md)
- [Hĺbka](reconstruction-depth.md)
- [Póza kamery a mierka](reconstruction-pose.md)
- [Fúzia, pokrytie a farba](reconstruction-fusion-and-texture.md)
- [Výstup .glb](glb-output.md)
- [Offline rekonštrukcia](reconstruction-offline.md)
