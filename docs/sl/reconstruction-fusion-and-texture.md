---
title: "Zlivanje, pokritost in barva"
nav_order: 5
lang: "sl"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Zlivanje, pokritost in barva {#fusion-coverage-and-colour}

Koda: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py), [`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py), [`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py), [`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py), [`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Vsak umeščen ključni okvir hkrati posodobi dve redki mreži: **površinski volumen**, iz katerega nastane mreža, in **mrežo pokritosti**, ki pove, koliko ji je treba zaupati in kam se vrniti. Obe se posodabljata na vsakem ključnem okviru, ne na koncu, ker je zemljevid pokritosti tisto, po čemer igralec usmerja.

## Od globine do točk {#from-depth-to-points}

Za vsak ključni okvir, katerega poza je znana **in** katerega globina ima merilo:

1. Vsak drugi piksel v vsaki smeri se uporabi (`PIXEL_STRIDE = 2`; sosednji pikseli iste površine niso neodvisne meritve).
2. Globina se pretvori v metre z afino prilagoditvijo okvira.
3. Obdržijo se samo globine med **0,35 m** (bližje je orožje, HUD, pokrov motorja) in **60 m** (monokularna napaka raste približno s kvadratom razdalje, zato so daljne točke šum, oblikovan kot geometrija), in samo piksli sveta maske.
4. Dvignejo se skozi model kamere in premaknejo v svet s pozo.
5. Vsaka točka nosi barvo piksla.

Okvir, ki je umeščen, a nima merila globine, se šteje kot *umeščen*, ne *zlit*.

## Površinski volumen {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` – voksel je "Surface detail" v oknu.

### Utežena zasedenost, ne TSDF {#weighted-occupancy-not-a-tsdf}

Predznačeno razdaljno polje (TSDF) reže vzdolž vsakega žarka piksla in dobro zadene tanke strukture in čist prazen prostor, ker ve, da je žarek šel *skozi* prazen prostor. To pomeni prehoditi žarek za vsakega od stotin milijonov pikslov. Ta volumen namesto tega kopiči **utežena zasedenost** na voksel in na zglajenem rezultatu požene marching cubes: dovolj hitro, da teče med skeniranjem, na računalniku brez uporabne grafične kartice, izhod pa je zaprta površina, ne oblak točk. Cena: tanke strukture in prazen prostor sta slabša, kot bi ju dobil TSDF.

### Vključitev okvira {#integrating-a-frame}

- Točke se razvrstijo v voksle (`floor(point / voxel)`).
- Vsak dotaknjen voksel dobi `weight x sqrt(count / max_count)`, kjer je `count` število točk okvira, ki so padle vanj, in `weight = max(0.1, zaupanje poze)`. Kvadratni koren: po neki točki več pikslov iste površine z istega mesta ne pomeni več dokazov; uteževanje z zaupanjem poze prepreči, da bi dvomljiva poza premikala površino.
- Barva je tekoče utežena povprečje na voksel.

Mreža je **redka**: pot, po kateri se hodi, dotakne majhen delež svojega omejujočega kvadra. Koordinate vokslov so spakirane v en 64-bitni ključ (21 bitov na os, do ±1.048.575 vokslov – pri 0,25 m okoli ±262 km) in se iščejo z urejenim poljem in binarnim iskanjem, popolnoma vektorizirano.

### Izvleček mreže {#extracting-the-mesh}

1. Voksli z utežjo pod **0,35** se izpustijo (posamezne točke na robovih silhuete bi postale konice).
2. Uteži se skalirajo z **75. percentilom** čez celoten sken in omejijo na 1.
3. Zasedeni prostor se razreže na **bloke po 64 vokslov** na stran, vsak pa se sestavi z **3-voksolskim halo** sosedov (brez tega se vsaka meja bloka zapre v steno in cesta izpade kot vrsta škatel).
4. Polje vsakega bloka se zgladi z Gaussovim filtrom (sigma 0,8 voksla), da se odstrani nagubanost, ki jo pusti šum globine.
5. **Prvi prehod**: 99. percentil zglajenega polja, vzorčen čez vse bloke (največ 2 milijona vrednosti), določi eno globalno skalo nivoja. Normiranje na blok bi osamljen osamelec povišalo v celotno površino v njegovem lastnem praznem bloku.
6. **Drugi prehod**: polje vsakega bloka, deljeno s to skalo, marching cubes pri **0,5**. Trikotnik pripada bloku, v katerega pade njegovo **središče**, zato se trikotniki čez zgornjo mejo oddajo natanko enkrat.
7. Oglišča se premaknejo v svetovne enote na središča vokslov; vsako oglišče prevzame barvo svojega vokslova (srednje siva tam, kjer pade izven zasedenega vokslova).

Izvleček po blokih je tisto, kar omogoča skeniranje velikosti proge: ena gosta matrika nad kvadratom kilometra pri 0,25 m bi bila milijarde celic. `tests/test_track_scale.py` zagotavlja, da to deluje pri tej velikosti z vsaj sorazmerno skeniranemu pomnilniku.

### Tla in struktura {#ground-and-structure}

`classify` označi vsak trikotnik po njegovi normali (orientirani z normalami oglišč iz izvleka): **v 35 stopinjah od naravnost navzgor** je `ground`, vse drugo `structure`. Pregledovalnik riše tla polno, strukture pa skoraj prozorno. **Voda se nikoli ne označi** – po obliki je ni mogoče ločiti od ravnih tal, napačna oznaka pa bi dvorišče prikazala kot jezero. Vsaka oznaka postane en del `.glb` ([Izhod .glb](glb-output.md)).

## Pokritost {#coverage}

`CoverageGrid(voxel=0.5)` za vsako polmetrsko celico beleži štiri stvari, ki niso isto:

| Izraz | Shranjeno | Ocena (vsaka omejena na 0..1) | Zakaj se šteje posebej |
|---|---|---|---|
| Kolikokrat je bila videna | število ključnih okvirjev, ki so videli celico | `count / 3` | enkrat je ugibanje brez česa, s čimer bi se primerjalo |
| Iz koliko smeri | vsota enotskih smeri pogleda | `(1 - spread) / (1 - 0,93)`, kjer je spread = dolžina vsote / število | dvajset okvirjev, ki gredo naravnost proti zidu, nima paralakse med seboj; dva pogleda na trideset stopinj druga od drugega sta več vredna |
| Od kod daleč | najbližja razdalja gledanja | `1 - nearest / 40 m` | napaka globine raste približno s kvadratom razdalje |
| Kako dobro je bila kamera umeščena | najboljše zaupanje poze | zaupanje | geometrija, zlita z dvomljivo pozo, pristane na napačnem mestu |

Točke okvira se najprej združijo po celicah, zato deset tisoč pikslov ene stene šteje kot eno opazovanje iz ene smeri.

**Kakovost = produkt vseh štirih izrazov**, ne povprečje: so pogoji, ki morajo vsi veljati. Mesto, ki je bilo videno dvestokrat iz ene smeri na šestdesetih metrih, je slabo opazovano, povprečje pa bi to skrilo za enim odličnim izrazom.

Glavne številke (`summary`): zasedene celice, delež s kakovostjo najmanj 0,5 ("% well seen" v oknu), povprečna kakovost in prostornina.

### Šibke točke {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. celice s kakovostjo pod 0,35 so šibke;
2. šibke celice se združijo po **povezanosti** (26-sosedstvo, union-find samo po zasedenih celicah – ne rastrski pregled omejujočega kvadra, ki bi bil na dolgi vožnji milijoni praznih celic);
3. skupine z manj kot 8 celicami se prezrejo;
4. razlog vsake skupine je najpogostejši *najšibkejši izraz* njenih celic, njen položaj pa povprečje njenih celic;
5. razvrščene od največje do najslabše kakovosti, največ 8.

| Razlog | Prikazan nasvet |
|---|---|
| few views | Seen only once or twice — walk past it again. |
| one direction | Only seen from one angle. Step sideways and look at it again. |
| distant | Only seen from far away. Get closer to it. |
| poor tracking | The camera was not well located here. Approach it more slowly. |

Povezanost je pomembna: združevanje po fiksni mreži blokov prijavi eno zanemarjeno stransko sobo kot veliko ločenih obročev, nihče pa ne more ločiti osmih krajev od enega kraja, štetega osemkrat.

### Tloris {#the-plan-view}

`top_down(resolution)` projicira celice na x/z in ohrani **najboljšo** kakovost na stolpec (nekdo, ki stoji v sobi, ima slabo pokritost stropa in odlično pokritost tal; povprečje bi sobo pobarvalo rumeno). Nikoli opazovani stolpci so označeni posebej. Okno ga riše na 200 x 200, prekrivni sloj na 120 x 120 ([Pokritost v oknu za skeniranje](reconstruction-scan-ui.md#the-coverage-map)).

### Ali je to mogoče rekonstruirati? {#is-this-reconstructable}

Vsakih 25 zlitih okvirjev, ko je celic vsaj 500:

| Ugotovitev | Ocena | Sporočilo (skrajšano) |
|---|---|---|
| manj kot 2 % celic ima razpon pogleda pod 0,93 | ni mogoče rekonstruirati | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| mediana najbližje razdalje nad 25 m | ni mogoče rekonstruirati | Everything was seen from N m away or further ... Get closer to what you want. |
| manj kot 6 % z dobrim razponom | mogoče, z opozorilom | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Nizka paralaksa ima dva vzroka, ki ju to ne more ločiti, zato sporočilo navede oba.

## Barva {#colour}

Barva zlitja na voksel je poceni in živa, a zabrisana: vsak piksel v četrt-metrski celici se povpreči, tudi tisti, ki so bili videni robno z trideset metrov. Zato se mreža ob izvozu še enkrat obarva, enkrat, iz samih okvirjev:

- **Ohranjeni okvirji**: do **160** ključnih okvirjev (slika in poza), izbranih z vzorčenjem z rezervoarjem, da so razporejeni čez celoten sken, ne samo na koncu.
- **Na oglišče** (`project_colours`) prispeva vsak tak okvir, če je oglišče pred kamero in znotraj slike, je površina obrnjena največ za približno 70 stopinj od neposrednega pogleda na kamero (`|normal . view| > 0.34`), je bližje kot **35 m**, in ni ničesar bližje pred njim (spodaj).
- Vsak tak pogled se oceni z `facing x (1 - distance / 35)`, zato blizu, naravnost gledan pogled premaga oddaljen, poševen. **4 najbolje ocenjeni** pogledi vsakega oglišča se ohranijo – ne glede na vrstni red okvirjev, boljši pogled nadomesti najšibkejšega od štirih – in se zmešajo, utežene s to isto oceno.
- **Zakrivanje**: v vsakem okviru se lastna oglišča mreže v pogledu narišejo v globinski medpomnilnik s celicami po 2 piksla, pri čemer se v vsaki celici ohrani najbližje. Oglišče, ki je za več kot `0,3 m + 5 %` svoje razdalje za najbližjim v svoji celici, je bilo v tem okviru skrito – stena med kamero in cesto za njo – in ta pogled ne šteje. Preizkus pozna samo mrežo: zakrivalec, ki ni bil nikoli zlit (mimo vozeči avto, steber kokpita zunaj maske HUD-a), ni ujet.
- Oglišče, ki ga noben okvir ni videl, ohrani barvo svojega vokslova; oglišče brez obojega je srednje sivo (črna bi se brala kot luknja).

Barva se zapiše kot `COLOR_0` na oglišče, ne kot atlas tekstur. Privzeti videz pregledovalnika je siva mreža pod nasičeno toplotno barvo; barva je tam, da se na skenirani krog najde cesta, kjer se sama geometrija ne loči od berme, in je prikazana za stikalom pregledovalnika *Captured colour* v plošči Background / level. Atlas bi povečal velikost datoteke in potreboval razpakiralnik za pregled, za pogled, ki namenoma ni privzeti. Blender in druga orodja glTF berejo `COLOR_0`.
