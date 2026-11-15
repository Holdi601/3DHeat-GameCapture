---
title: "Sloučení, pokrytí a barva"
nav_order: 5
lang: "cs"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Sloučení, pokrytí a barva {#fusion-coverage-and-colour}

Kód: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Každý umístěný klíčový snímek aktualizuje dvě řídké mřížky najednou: **objemový povrch**,
ze kterého vznikne síť, a **mřížku pokrytí**, která říká, jak moc jí věřit a kam se
vrátit. Obě se aktualizují po každém klíčovém snímku, ne na konci, protože mapa
pokrytí je to, podle čeho hráč řídí.

## Od hloubky k bodům {#from-depth-to-points}

Pro každý klíčový snímek, jehož poloha je známa **a** jehož hloubka má měřítko:

1. Používá se každý druhý pixel v každém směru (`PIXEL_STRIDE = 2`; sousední pixely
   jednoho povrchu nejsou nezávislá měření).
2. Hloubka se převede na metry afinním přizpůsobením snímku.
3. Ponechají se jen hodnoty mezi **0,35 m** (bližší je zbraň, HUD, kapota) a **60 m**
   (monokulární chyba roste zhruba s druhou mocninou vzdálenosti, takže vzdálené body
   jsou šum tvarovaný jako geometrie), a jen na pixelech světa z masky.
4. Zvednou se přes model kamery a přesunou do světa podle polohy.
5. Každý bod nese barvu svého pixelu.

Snímek, který je umístěn, ale nemá měřítko hloubky, se počítá jako *umístěný*, ale ne
*sloučený*.

## Objemový povrch {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxel je „Detail povrchu“ v okně.

### Vážená obsazenost, ne TSDF {#weighted-occupancy-not-a-tsdf}

Zkrácené signed distance field vrhá paprsek podél každého pixelu a správně zachytí
tenké struktury a čistý volný prostor, protože ví, že paprsek prošel *skrz* prázdno.
To znamená obcházet paprsek pro každý z stovek milionů pixelů. Tento objem místo toho
hromadí **váženou obsazenost** na voxel a na vyhlazený výsledek pouští pochodující
kostky: dost rychle na běh během skenování, na stroji bez použitelné grafické karty,
a výstup je uzavřený povrch, ne mračno bodů. Cena: tenké struktury a volný prostor
jsou horší než by dalo TSDF.

### Vložení snímku {#integrating-a-frame}

- Body se třídí do voxelů (`floor(bod / voxel)`).
- Každý dotčený voxel dostane `váha x sqrt(počet / max_počet)`, kde `počet` je kolik
  bodů snímku spadlo do něj a `váha = max(0,1; jistota polohy)`. Odmocnina: za bodem
  další pixely téhož povrchu ze stejného místa přestanou být důkazem; vážení jistotou
  polohy zabrání tomu, aby pochybná poloha tlačila povrch kolem.
- Barva je běžící vážený průměr na voxel.

Mřížka je **řídká**: projetá trasa se dotkne malého zlomku svého ohraničujícího
obdélníku. Souřadnice voxelů se balí do jednoho 64bitového klíče (21 bitů na osu, až
±1 048 575 voxelů - při 0,25 m asi ±262 km) a hledají se seřazeným polem a binárním
vyhledáváním, plně vektorově.

### Získání sítě {#extracting-the-mesh}

1. Voxely s váhou pod **0,35** se zahodí (ojedinělé body na okrajích siluety by se
   staly ostny).
2. Váhy se škálují na **75. percentil** přes celé skenování a ořežou na 1.
3. Obsazený prostor se rozřeže na **bloky po 64 voxelech** na stranu, každý se
   realizuje s **3-voxelovým halo** dat sousedů (bez něj se každá hranice bloku uzavře
   do zdi a silnice vyjde jako řada krabic).
4. Pole každého bloku se vyhladí Gaussem (sigma 0,8 voxelu), aby se odstranilo
   zvlnění, které šum hloubky zanechá.
5. **Průchod první**: 99. percentil vyhlazeného pole, vzorkovaný přes všechny bloky
   (nejvýše 2 miliony hodnot), nastaví jedno globální měřítko úrovně. Normalizovat na
   blok by povýšilo osamělou odlehlou hodnotu na celý povrch v jejím vlastním
   prázdném bloku.
6. **Průchod druhý**: pole každého bloku dělené tímto měřítkem, pochodující kostky na
   **0,5**. Trojúhelník patří bloku, do kterého padne jeho **těžiště**, takže trojúhelníky
   přes šev se vyemitují přesně jednou.
7. Vrcholy se přesunou do světových jednotek na středy voxelů; každý vrchol převezme
   barvu svého voxelu (střední šedá tam, kde padne mimo obsazený voxel).

Získávání po blocích je to, co dělá možným sken velikosti tratě: jediné husté pole nad
kilometrovým čtvercem o 0,25 m by bylo miliardy buněk. `tests/test_track_scale.py`
zajišťuje, že to funguje v tomto měřítku s pamětí úměrnou tomu, co se naskenovalo.

### Země a struktura {#ground-and-structure}

`classify` označí každý trojúhelník podle jeho normály (orientované podle normál vrcholů):
do **35 stupňů od přímo nahoru** je `ground`, všechno ostatní `structure`. Prohlížeč
kreslí zem plnou a struktury téměř průhledné. **Voda se nikdy neoznačuje** - podle tvaru
ji nelze odlišit od rovné země a chybný štítek by vykreslil nádvoří jako jezero. Každý
štítek se stane jednou částí `.glb` ([Výstup .glb](glb-output.md)).

## Pokrytí {#coverage}

`CoverageGrid(voxel=0.5)` zaznamenává na každou půlmetrovou buňku čtyři věci, které nejsou
totéž:

| Pojem | Uloženo | Skóre (každé ořezané do 0..1) | Proč se počítá zvlášť |
|---|---|---|---|
| Kolikrát viděno | počet klíčových snímků, které buňku viděly | `počet / 3` | jednou je odhad bez čeho by se průměrovalo |
| Z kolika směrů | součet jednotkových směrů pohledu | `(1 - rozptyl) / (1 - 0,93)`, kde rozptyl = délka součtu / počet | dvacet snímků jdoucích přímo ke zdi nemá mezi sebou paralaxu; dva pohledy o třicet stupňů od sebe stojí víc |
| Z jaké dálky | nejbližší vzdálenost pohledu | `1 - nejbližší / 40 m` | chyba hloubky roste zhruba s druhou mocninou vzdálenosti |
| Jak dobře byla kamera umístěna | nejlepší jistota polohy | samotná jistota | geometrie sloučená s pochybnou polohou přistane na špatném místě |

Body snímku se nejdřív seskupí podle buňky, takže deset tisíc pixelů jedné zdi se počítá
jako jedno pozorování z jednoho směru.

**Kvalita = součin čtyř členů**, ne průměr: jsou to podmínky, které musí platit všechny
zároveň. Místo viděné dvě stě krát z jednoho směru na šedesáti metrech je špatně
pozorované, a průměr by to schoval za jeden výborný člen.

Hlavní čísla (`summary`): obsazené buňky, podíl s kvalitou alespoň 0,5 („% well seen“ v okně), průměrná kvalita a objem.

### Slabá místa {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. buňky s kvalitou pod 0,35 jsou slabé;
2. slabé buňky se seskupují podle **souvislosti** (26-okolí, union-find jen nad obsazenými
   buňkami - ne rastr přes ohraničující obdélník, který je na dlouhé jízdě milionem
   prázdných buněk);
3. skupiny menší než 8 buněk se ignorují;
4. důvodem skupiny je nejčastější *nejslabší člen* jejích buněk a její poloha je průměr
   jejích buněk;
5. seřazeno od největší (pak podle nejhorší kvality), nejvýše 8.

| Důvod | Zobrazená rada |
|---|---|
| málo pohledů | `Seen only once or twice — walk past it again.` |
| jeden směr | `Only seen from one angle. Step sideways and look at it again.` |
| daleko | `Only seen from far away. Get closer to it.` |
| špatné sledování | `The camera was not well located here. Approach it more slowly.` |

Souvislost záleží: seskupení podle pevné mřížky bloků nahlásí jednu zanedbanou vedlejší
místnost jako mnoho oddělených kruhů a nikdo nerozezná osm míst od jednoho místa
započítaného osmkrát.

### Půdorys {#the-plan-view}

`top_down(resolution)` promítne buňky na x/z a ponechá **nejlepší** kvalitu na sloupec
(někdo stojící v místnosti má slabé pokrytí stropu a výborné pokrytí podlahy; průměr by
místnost vykreslil jantarově). Sloupce, které nikdo neviděl, se značí zvlášť. Okno
kreslí 200 x 200, překryv 120 x 120 ([Mapa pokrytí](reconstruction-scan-ui.md#the-coverage-map)).

### Je to rekonstruovatelné? {#is-this-reconstructable}

Každých 25 sloučených snímků, jakmile je alespoň 500 buněk:

| Zjištění | Verdikt | Zpráva (zkrácená) |
|---|---|---|
| méně než 2 % buněk má rozptyl pohledu pod 0,93 | nerekonstruovatelné | `Almost no parallax (N%). Either the camera never looks aside from the way it travels, or the tracking is drifting … Check the placed-frame count: if that is high, it is drift.` |
| medián nejbližší vzdálenosti přes 25 m | nerekonstruovatelné | `Everything was seen from N m away or further … Get closer to what you want.` |
| méně než 6 % s dobrým rozptylem | rekonstruovatelné, s varováním | `Thin parallax (N%) — the geometry will be rough. Moving sideways relative to what you are looking at helps most.` |

Nízká paralaxa má dvě příčiny, které tohle nerozliší, a proto zpráva jmenuje obě.

## Barva {#colour}

Barva sloučení na voxel je levná a živá, a rozmazaná: každý pixel v čtvrtmetrové buňce
se průměruje, včetně těch, které byly vidět zboku z třiceti metrů. Proto se při exportu
síť obarví znovu, jednou, z samotných snímků:

- **Zachované snímky**: až **160** klíčových snímků (obraz i poloha), vybraných
  rezervoárovým vzorkováním, aby byly rozprostřené přes celé skenování, ne jen na jeho
  konci.
- **Na vrchol** (`project_colours`) každý zachovaný snímek přispívá, pokud je vrchol před
  kamerou a uvnitř obrazu, povrch se odklání nejvýš asi 70 stupňů od přímého čelního
  pohledu na kameru (`|normála . pohled| > 0,34`), je blíž než **35 m** a nic blíž nestálo
  před ním (níže).
- Každý takový pohled se ohodnotí `čelnost x (1 - vzdálenost / 35)`, takže blízký
  čelní pohled porazí vzdálený šikmý. **4 nejvýše hodnocené** pohledy každého vrcholu se
  drží - v jakémkoli pořadí jsou snímky, lepší pohled nahradí nejslabší ze čtyř - a
  smíchají se, vážené týmž skóre.
- **Okluze**: v každém snímku se vlastní vrcholy sítě ve výhledu vykreslí do hloubkové
  vyrovnávací paměti s buňkami po 2 pixelech, nejbližší na buňku. Vrchol více než
  `0,3 m + 5 %` svojí vzdálenosti za nejbližším ve své buňce byl v tom snímku skryt -
  zeď mezi kamerou a silnicí za ní - a tento pohled neplatí nic. Test zná jen síť:
  okluder, který nebyl sloučen (projíždějící auto, sloupek kokpitu mimo masku HUD), se
  nezachytí.
- Vrchol, který žádný snímek neviděl, si ponechá barvu voxelu; vrchol bez obojího je
  střední šedá (černá by se četla jako díra).

Barva se zapisuje jako `COLOR_0` na vrchol, ne jako texturový atlas. Výchozí vzhled
prohlížeče je šedá mapa pod nasycenou teplotou; barva slouží k nalezení silnice na
naskenované okruhové trati, kde samotná geometrie nerozliší vozovku od krajnice, a je
vidět za přepínačem prohlížeče *Zachycená barva* v jeho panelu Pozadí / úroveň. Atlas by
násobil velikost souboru a potřeboval by rozbalovač, a to pro pohled, který je záměrně
ne výchozí. Blender a jiné nástroje glTF `COLOR_0` čtou.
