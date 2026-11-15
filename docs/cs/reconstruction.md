---
title: Rekonstrukce úrovně
nav_order: 6
lang: "cs"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonstrukce úrovně z hraní {#level-reconstruction-from-gameplay}

Projděte úroveň pomalu nebo projeďte trať a skener promění to, co ukázala obrazovka, v `.glb`. Prohlížeč 3DHeat ho načte jako kontext pod telemetrií. Je to stejná smlouva souborů, jakou zapisuje exportér Unreal. Je určen pro případ, kdy nikdo mapu nevyexportoval a herní soubory nejdou číst. Export z enginu nebo z herních souborů je přesný, tohle je odhad.

## Postup {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Fáze | Živý sken (`heat3d_capture.ui`) | Offline (`reconstruct`) | Stránka |
|---|---|---|---|
| Snímky | monitor, okno nebo video, zmenšené na nejdelší stranu předvolby | video, vzorkované dvakrát (plán řešení a interval fúze) | [Zachytávání](reconstruction-capture.md) |
| Klíčové snímky | ponechané podle toho, jak moc se obraz změnil; práh se přizpůsobí zachytávání | každých `--fuse-interval` sekund | [Zachytávání](reconstruction-capture.md#keyframes) |
| Masky | změnová `ScreenMask`, potom `FlowMask` založená na toku po 40 klíčových snímcích | `FlowMask` naučená ze čtyř průchodů videa; neaplikuje se na řešitele | [Zachytávání](reconstruction-capture.md#what-is-not-the-world) |
| Hloubka | model ONNX na nejlepším GPU backendu | PyTorch Depth Anything V2 Small | [Hloubka](reconstruction-depth.md) |
| Póza | vizuální odometrie, nebo přesná telemetrie Forzy | okna VGGT slepená do jedné dráhy, interpolovaná | [Póza](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Měřítko | výška kamery nad zemí (1,15 m) jednou, nebo telemetrie | jednotky vyřešené dráhy | [Póza](reconstruction-pose.md#scale) |
| Fúze | vážená obsazenost, řídké voxely; mřížka pokrytí | totéž | [Fúze](reconstruction-fusion-and-texture.md) |
| Výstup | `.glb`, části ground/structure, barva na vrchol, centimetry | totéž | [Výstup .glb](glb-output.md) |

Kód: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan) (`session.py`: nastavení skenu a jeho tempo; `reconstruct.py`: klíčové snímky na geometrii; `offline.py`: offline cesta), s fázemi v `capture/`, `depth/`, `pose/`, `fusion/` a `geometry/`.

## Odkud pochází přesnost {#where-accuracy-comes-from}

Monokulární hloubka je správná jen až do neznámého měřítka. Fotka místnosti a fotka domečku pro panenky jsou tentýž obrázek. Síť proto nechá dělat to, v čem je dobrá (relativní tvar, hrany, tenké konstrukce), a měřítko a dráhu kamery vezme odjinud, kde je znají:

| Hra | Dráha kamery | Měřítko |
|---|---|---|
| Forza Horizon / Motorsport s telemetrií zapnutou | přesná, z Data Out, interpolovaná na čas zachycení každého snímku | přesné: hloubka je ukotvena triangulací rysů mezi dvěma známými pózami |
| Cokoli jiného, živě | vizuální odometrie, řetězená snímek po snímku | jednou pevně z předpokládané výšky kamery nad zemí |
| Záznam, offline | VGGT, řešený přes překrývající se okna | jednotky samotného řešení (ne metrické) |

Jediné číslo, které skener dostane řečené místo naměřené, je **horizontální zorné pole** hry. Ve výchozím nastavení okna je 90 stupňů; závodní hry jsou spíš kolem 65. Příliš úzké a úroveň se rekonstruuje hlouběji, než je. Příliš široké a zploští se.

## Říct uživateli brzy {#telling-the-user-early}

Sken je fyzická činnost, někdo prochází úroveň několik minut. Drahé selhání je dojít až do konce chůze a zjistit, že nebyla k ničemu. Okno proto změří propustnost hloubky na tomto stroji dřív, než cokoli může začít, a řekne, jaký sken bude ([Běh](runtime.md#what-to-expect-from-this-machine)). Během skenu ukazuje mapu pokrytí s očíslovanými slabými místy, zdraví sledování, lištu rychlosti chůze, lištu ostrosti a jednu instrukci najednou. Dělá to v okně i v průhledném překryvu přes hru, který propouští kliknutí ([Okno skenu](reconstruction-scan-ui.md)).

## Změřeno na syntetické referenční pravdě {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` vykreslí místnost 12 x 8 m (4 m vysokou) ze známé dráhy kamery, s analytickou (ne sítovou) hloubkou, a rekonstruuje ji s voxely 0,2 m. Ověřuje, že se umístí více než 90 % snímků. Průměrná chyba dráhy je menší než 0,35 m, nejhorší pod 1 m. Ujetá vzdálenost je do 10 % od pravdy a místnost vyjde se správnou šířkou do 1,5 m. Přes 75 % plochy stěn leží do 0,45 m od skutečné stěny. Procházka ve stylu průzkumu skóruje zřetelně lépe pokrytí než chůze rovně a scéna bez rysů je odmítnuta místo vymyšlení. Analytická hloubka izoluje pózu, měřítko a fúzi od sítě. Jak si síť vede na skutečném hraní, je jiná otázka, na kterou žádná syntetická scéna neodpoví. `tests/test_track_width.py` ověřuje, že jízda mimo střed na silnici známé šířky rekonstruuje šířku silnice, ne jen jízdní čáru.

## Stránky {#pages}

- [Okno skenu](reconstruction-scan-ui.md): každé ovládání, klávesová zkratka a překryv
- [Zachytávání, masky a kvalita snímků](reconstruction-capture.md)
- [Hloubka](reconstruction-depth.md)
- [Póza kamery a měřítko](reconstruction-pose.md)
- [Fúze, pokrytí a barva](reconstruction-fusion-and-texture.md)
- [Výstup .glb](glb-output.md)
- [Offline rekonstrukce](reconstruction-offline.md)
