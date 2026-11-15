---
title: "Spájanie, pokrytie a farba"
nav_order: 5
lang: "sk"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Spájanie, pokrytie a farba {#fusion-coverage-and-colour}

Kód: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Každá umiestnená kľúčová snímka aktualizuje dve riedke mriežky naraz: **objemu povrchu**, ktorý sa
stane sieťou, a **mriežku pokrytia**, ktorá hovorí, koľko jej veriť a kam sa vrátiť. Obe sa aktualizujú
pre každú kľúčovú snímku, nie na konci, lebo mapa pokrytia je to, podľa čoho hráč riadi.

## Od hĺbky k bodom {#from-depth-to-points}

Pre každú kľúčovú snímku, ktorej poloha je známa **a** ktorej hĺbka má mierku:

1. Používa sa každý druhý pixel v každom smere (`PIXEL_STRIDE = 2`; susedné pixely jedného povrchu nie
   sú nezávislé merania).
2. Hĺbka sa prevedie na metre afinným prifitovaním snímky.
3. Zachová sa len medzi **0,35 m** (bližšie je zbraň, HUD, kapota) a **60 m** (monokulárna chyba rastie
   zhruba s druhou mocninou vzdialenosti, takže vzdialené body sú šum s tvarom geometrie) a len na
   pixeloch sveta z masky.
4. Zdvihne sa cez model kamery a presunie do sveta podľa polohy.
5. Každý bod nesie farbu pixelu.

Snímka, ktorá je umiestnená, ale nemá mierku hĺbky, sa počíta ako *umiestnená*, nie *spojená*.

## Objem povrchu {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` – voxel je nastavenie okna „Surface detail“.

### Vážená obsaditeľnosť, nie TSDF {#weighted-occupancy-not-a-tsdf}

Skrátená signed distance field (TSDF) vyhlbuje pozdĺž lúča každého pixelu a správne zachytí tenké
štruktúry a čistý voľný priestor, pretože pozná, že lúč prešiel *cez* prázdno. To znamená prejsť lúč
pre každý z stoviek miliónov pixelov. Tento objem namiesto toho nazbiera **váženú obsaditeľnosť** pre
každý voxel a na vyhladený výsledok spustí marching cubes: dosť rýchlo, aby bežal počas skenovania,
na stroji bez použiteľnej GPU, a výstup je uzavretý povrch, nie oblak bodov. Cena: tenké štruktúry a
voľný priestor sú horšie, než by dostala TSDF.

### Integrácia snímky {#integrating-a-frame}

- Body sa zaraďujú do voxelov (`floor(point / voxel)`).
- Každý dotknutý voxel dostane `weight x sqrt(count / max_count)`, kde `count` je koľko bodov snímky
  padlo do neho a `weight = max(0.1, pose confidence)`. Odmocnina: pri určitom bode už ďalšie pixely
  rovnakého povrchu z rovnakého miesta nie sú dôkaz; váženie istotou polohy zabráni tomu, aby
  pochybná poloha posúvala povrch.
- Farba je bežiaci vážený priemer na voxel.

Mriežka je **riedka**: prejdená trasa sa dotkne malého zlomku svojho ohraničujúceho boxu. Súradnice
voxelov sa zbalia do jedného 64-bitového kľúča (21 bitov na os, až ±1 048 575 voxelov – pri 0,25 m
zhruba ±262 km) a hľadajú sa v zoradenom poli binárnym vyhľadávaním, plne vektorizovane.

### Extrakcia siete {#extracting-the-mesh}

1. Voxely s váhou pod **0,35** sa zahodia (ojedinelé body na okrajoch siluet by sa zmenili na ostne).
2. Váhy sa škálujú **75. percentilom** naprieč skenom a orezávajú na 1.
3. Obsadený priestor sa rozreže na **bloky po 64 voxeloch** na stranu, každý sa realizuje s **3-voxelovým
   halo** z dát susedov (bez neho sa každá hranica bloku uzavrie ako stena a cesta vyjde ako rad
   škatúľ).
4. Pole každého bloku sa vyhladí Gaussovským filtrom (sigma 0,8 voxela), aby sa odstránilo vrásčenie,
   ktoré zanecháva šum hĺbky.
5. **Prvý prechod**: 99. percentil vyhladeného poľa, odobratý naprieč všetkými blokmi (najviac 2 milióny
   hodnôt), nastaví jednu globálnu mierku úrovne. Normalizovanie na blok by z osamelého odľahlého bodu
   spravilo plný povrch v jeho vlastnom prázdnom bloku.
6. **Druhý prechod**: pole každého bloku vydelené touto mierkou, marching cubes pri **0,5**. Trojuholník
   patrí bloku, do ktorého padne jeho **ťažisko**, takže trojuholníky prekračujúce hranicu sa vytvoria
   presne raz.
7. Vrcholy sa presunú do svetových jednotiek v stredoch voxelov; každý vrchol preberie farbu svojho
   voxelu (stredná sivá tam, kde leží mimo obsadeného voxelu).

Extrakcia po blokoch je to, čo umožňuje sken veľkosti trate: jedno husté pole nad štvorcovým boxom
o strane kilometer pri 0,25 m by bolo miliardy buniek. `tests/test_track_scale.py` zafixuje, že to
funguje v tejto mierke, s pamäťou úmernou tomu, čo bolo naskenované.

### Zem a štruktúra {#ground-and-structure}

`classify` označí každý trojuholník podľa jeho normály (orientovanej podľa normál vrcholov):
do **35 stupňov od priameho smeru hore** je `ground`, všetko ostatné `structure`. Prehliadač kreslí
zem plnú a štruktúry takmer priehľadné. **Voda sa nikdy neurčuje** – tvarom sa nedá odlíšiť od rovnej
zeme a zlý štítok by vykreslil nádvorie ako jazero. Každý štítok sa stane jednou časťou `.glb`
([Výstup .glb](glb-output.md)).

## Pokrytie {#coverage}

`CoverageGrid(voxel=0.5)` zaznamenáva pre každú polovičnú metrovú bunku štyri veci, ktoré nie sú to
isté:

| Pojem | Uložené | Skóre (každé orezané na 0..1) | Prečo sa počíta osobitne |
|---|---|---|---|
| Koľkokrát videné | počet kľúčových snímok, ktoré bunku videli | `count / 3` | raz je len tipovanie, nie je čo spriemerovať |
| Z koľkých smerov | súčet jednotkových smerov pohľadu | `(1 - spread) / (1 - 0,93)`, kde spread = dĺžka súčtu / počet | dvadsať snímok, ktoré idú rovno na stenu, nemá medzi sebou paralaxu; dva pohľady o tridsať stupňov od seba stoja viac |
| Z akej vzdialenosti | najbližšia vzdialenosť pohľadu | `1 - nearest / 40 m` | chyba hĺbky rastie zhruba s druhou mocninou vzdialenosti |
| Ako dobre bola kamera umiestnená | najlepšia istota polohy | samotná istota | geometria spojená s pochybnou polohou pristane na zlom mieste |

Body snímky sa najprv zoskupia po bunkách, takže desaťtisíc pixelov jednej steny sa počíta ako jedno
pozorovanie z jedného smeru.

**Kvalita = súčin štyroch členov**, nie priemer: sú to podmienky, ktoré musia platiť všetky naraz.
Miesto videné dvestokrát z jedného smeru zo šesťdesiatich metrov je zle pozorované, a priemer by to
skryl za jeden výborný člen.

Hlavné čísla (`summary`): obsadené bunky, podiel s kvalitou aspoň 0,5 („% well seen“ v okne), priemerná
kvalita a objem.

### Slabé miesta {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. bunky s kvalitou pod 0,35 sú slabé;
2. slabé bunky sa zoskupia podľa **súvislosti** (26-okolie, union-find len nad obsadenými bunkami –
   nie rastrom cez ohraničujúci box, ktorý je pri dlhej jazde miliónmi prázdnych buniek);
3. skupiny menšie ako 8 buniek sa ignorujú;
4. dôvod každej skupiny je najčastejší *najslabší člen* jej buniek a jej poloha stredom jej buniek;
5. zoradené od najväčšej (potom podľa najhoršej kvality), najviac 8.

| Dôvod | Zobrazená rada |
|---|---|
| málo pohľadov | Videné len raz alebo dvakrát – prejdite okolo znova. |
| jeden smer | Videné len z jedného uhla. Krok do strany a pozrite sa znova. |
| vzdialené | Videné len z ďaleka. Priblížte sa. |
| slabé sledovanie | Kamera tu nebola dobre zameraná. Približujte sa pomalšie. |

Súvislosť záleží: zoskupenie pevnou mriežkou blokov nahlási jednu zanedbanú vedľajšiu miestnosť ako
mnoho samostatných kruhov a nikto nerozozná osem miest od jedného miesta počítaného osemkrát.

### Pôdorysný pohľad {#the-plan-view}

`top_down(resolution)` premieta bunky na x/z a ponecháva **najlepšiu** kvalitu na stĺpec (niekto stojaci
v izbe má slabé pokrytie stropu a výborné pokrytie podlahy; priemerovanie by izbu vyfarbilo oranžovo).
Stĺpce, ktoré nikdy neboli pozorované, sú označené osobitne. Okno kreslí 200 x 200, prekrytie
120 x 120 ([Mapa pokrytia](reconstruction-scan-ui.md#the-coverage-map)).

### Dá sa to rekonštruovať? {#is-this-reconstructable}

Každých 25 spojených snímok, keď je aspoň 500 buniek:

| Zistenie | Verdikt | Správa (skrátená) |
|---|---|---|
| menej ako 2 % buniek má rozptyl pohľadu pod 0,93 | nedá sa rekonštruovať | Takmer žiadna paralaxa. Buď kamera sa nikdy nepozerá do strany, alebo sledovanie driftuje, takže sa ten istý povrch nikdy neobjaví dvakrát na tom istom mieste. Skontrolujte počet umiestnených snímok: ak je vysoký, je to drift. |
| medián najbližšej vzdialenosti nad 25 m | nedá sa rekonštruovať | Všetko bolo videné zo vzdialenosti N m a viac … Priblížte sa k tomu, čo chcete. |
| menej ako 6 % s dobrým rozptylom | rekonštruovateľné, s varovaním | Tenká paralaxa – geometria bude hrubá. Najviac pomôže pohyb do strany voči tomu, na čo sa pozeráte. |

Nízka paralaxa má dve príčiny, ktoré toto nedokáže rozlíšiť, preto správa menuje obe.

## Farba {#colour}

Farba na voxel z fúzie je lacná a živá, a rozmazaná: každý pixel v štvrť metrovej bunke sa spriemeruje,
vrátane tých videných z boku z tridsiatich metrov. Preto sa pri exporte sieť zafarbí znova, raz,
z samotných snímok:

- **Zachované snímky**: až **160** kľúčových snímok (obraz a poloha), vybraných reservoir samplingom,
  aby boli rozložené po celom skene, nie len na jeho konci.
- **Na vrchol** (`project_colours`) každá zachovaná snímka prispieva, ak je vrchol pred kamerou
  a vnútri obrazu, povrch sa odkláňa najviac asi o 70 stupňov od priameho smerovania ku kamere
  (`|normal . view| > 0.34`), je bližšie než **35 m** a nič bližšie pred ním nestálo (nižšie).
- Každý takýto pohľad sa ohodnotí `facing x (1 - distance / 35)`, takže blízky pohľad naproti vyhrá
  nad vzdialeným šikmým. **4 najlepšie hodnotené** pohľady každého vrcholu sa zachovajú – nech sú
  snímky v akomkoľvek poradí, lepší pohľad nahradí najslabší zo štyroch – a zmiešajú sa váhou tým
  istým skóre.
- **Okluzia**: v každej snímke sa vlastné vrcholy siete, ktoré sú vidieť, nakreslia do hĺbkového buffera
  s 2-pixelovými bunkami, pričom sa zachová najbližší v každej bunke. Vrchol, ktorý je v tej istej
  bunke viac ako `0,3 m + 5 %` svojej vzdialenosti za najbližším, bol v tej snímke skrytý – stena medzi
  kamerou a cestou za ňou – a tento pohľad sa nepočíta. Test pozná len sieť: nezachytí okluder, ktorý
  nebol nikdy spojený (prejdúce auto, pilier kokpitu mimo masky HUD).
- Vrchol, ktorý žiadna snímka nevidela, si ponechá farbu voxelu; vrchol bez oboch je stredne sivý
  (čierna by sa čítala ako diera).

Farba sa zapisuje ako `COLOR_0` na vrchol, nie ako atlas textúr. Predvolený vzhľad prehliadača je
sivá mapa pod sýtym teplom; farba slúži na nájdenie cesty na naskenovanom okruhu, kde geometria
samotná neoddelí cestu od krajnice, a zobrazuje sa za prepínačom prehliadača *Zachytená farba* v jeho
paneli Pozadie / level. Atlas by zdvojnásobil veľkosť súboru a potreboval by rozbaľovač pre pohľad,
ktorý je zámerne iný než predvolený. Blender a ostatné nástroje glTF čítajú `COLOR_0`.
