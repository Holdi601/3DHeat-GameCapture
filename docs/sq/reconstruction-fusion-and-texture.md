---
title: "Bashkimi, mbulimi dhe ngjyra"
nav_order: 5
lang: "sq"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Bashkimi, mbulimi dhe ngjyra {#fusion-coverage-and-colour}

Kodi: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Çdo kuadër kyç i vendosur përditëson dy rrjeta të rralla njëherësh: **vëllimin e sipërfaqes**, që
bëhet rrjeta, dhe **rrjetën e mbulimit**, që tregon sa t'i besohet dhe ku të kthehesh. Të dyja
përditësohen për çdo kuadër kyç, jo në fund, sepse harta e mbulimit është ajo me të cilën drejtohet lojtari.

## Nga thellësia te pikat {#from-depth-to-points}

Për çdo kuadër kyç pozicioni i të cilit dihet **dhe** thellësia e të cilit ka shkallë:

1. Përdoret çdo piksel i dytë në çdo drejtim (`PIXEL_STRIDE = 2`; pikselat fqinjë të një
   sipërfaqeje nuk janë matje të pavarura).
2. Thellësia konvertohet në metra me përshtatjen afine të kuadrit.
3. Mbahet vetëm mes **0.35 m** (më afër është arma, HUD-i, kapaku i motorit) dhe **60 m**
   (gabimi monokular rritet afërsisht me katrorin e largësisë, kështu që pikat e largëta janë zhurmë me
   formë gjeometrie) dhe vetëm në pikselat e botës të maskës.
4. Ngrihet nëpër modelin e kamerës dhe zhvendoset në botë me pozën.
5. Çdo pikë mban ngjyrën e pikselit.

Një kuadër që është pozicionuar por nuk ka shkallë thellësie numërohet si *i vendosur* por jo *i bashkuar*.

## Vëllimi i sipërfaqes {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxel-i është "Surface detail" i dritares.

### Zënie e peshuar, jo TSDF {#weighted-occupancy-not-a-tsdf}

Një fushë e shenjuar largësish e prerë (TSDF) gdhend përgjatë rrezes së çdo pikseli dhe merr drejt strukturat e holla dhe
hapësirën e lirë të pastër, sepse di që një rreze kaloi *përmes* hapësirës bosh. Kjo do të thotë të ecësh
rrezen për secilin nga qindra milionë pikselë. Ky vëllim në vend të kësaj grumbullon
**zënie të peshuar** për çdo voxel dhe ekzekuton marching cubes mbi rezultatin e zbutur: mjaft i shpejtë për
t'u ekzekutuar gjatë skanimit, në një makinë pa GPU të përdorshme, dhe dalja është një sipërfaqe e mbyllur
dhe jo një re pikash. Kostoja: strukturat e holla dhe hapësira e lirë dalin më keq se me një TSDF.

### Integrimi i një kuadri {#integrating-a-frame}

- Pikat vendosen në voxel-e (`floor(point / voxel)`).
- Çdo voxel i prekur merr `weight x sqrt(count / max_count)`, ku `count` është sa nga pikat e kuadrit
  ranë në të dhe `weight = max(0.1, pose confidence)`. Rrënja katrore: pas një pike, më shumë
  pikselë të së njëjtës sipërfaqe nga i njëjti vend pushojnë së qeni provë; peshimi me besueshmërinë e pozës
  e pengon një pozë të dyshimtë të shtyjë sipërfaqen andej-këndej.
- Ngjyra është një mesatare e peshuar rrjedhëse për çdo voxel.

Rrjeta është **e rrallë**: një rrugë e ecur prek një pjesë të vogël të kutisë së saj kufizuese. Koordinatat e
voxel-eve paketohen në një çelës 64-bitësh (21 bit për bosht, deri në +-1,048,575 voxel-e - në
0.25 m rreth +-262 km) dhe kërkohen me një varg të renditur dhe kërkim binar, plotësisht të vektorizuar.

### Nxjerrja e rrjetës {#extracting-the-mesh}

1. Voxel-et me peshë nën **0.35** hidhen tej (pika të vetme endacake në skajet e siluetave do të
   bëheshin gjemba).
2. Peshat shkallëzohen me **përqindjen e 75-të** nëpër skanim dhe pritën në 1.
3. Hapësira e zënë pritet në **blloqe me 64 voxel-e** për anë, secili realizuar me një
   **halo prej 3 voxel-esh** të të dhënave të fqinjëve (pa të, çdo kufi blloku mbyllet në një
   mur dhe një rrugë del si një varg kutish).
4. Fusha e çdo blloku zbutet me një Gaussian (sigma 0.8 voxel) për të hequr rrudhën që lë zhurma e
   thellësisë.
5. **Kalimi i parë**: përqindja e 99-të e fushës së zbutur, e marrë nga të gjithë blloqet (më së shumti 2
   milionë vlera), vendos një shkallë globale niveli. Normalizimi për çdo bllok do ta ngrinte një
   outlier të vetëm në sipërfaqe të plotë në bllokun e tij bosh.
6. **Kalimi i dytë**: fusha e çdo blloku e pjesëtuar me atë shkallë, marching cubes në **0.5**. Një trekëndësh
   i përket bllokut ku bie **centroidi** i tij, kështu që trekëndëshat që kalojnë një tegel
   nxirren saktësisht një herë.
7. Kulmet kalojnë në njësi botërore te qendrat e voxel-eve; çdo kulm merr ngjyrën e voxel-it të tij
   (gri e mesme aty ku bie jashtë një voxel-i të zënë).

Nxjerrja bllok pas blloku është ajo që e bën të mundur një skanim në madhësinë e një pistë: një varg i dendur mbi një
kuti një kilometër katrore në 0.25 m do të ishte miliarda qeliza. `tests/test_track_scale.py` fikson
që funksionon në atë shkallë me memorie proporcionale me atë që u skanua.

### Toka dhe struktura {#ground-and-structure}

`classify` etiketon çdo trekëndësh sipas normales së tij (e orientuar nga normalet e nxjerra të kulmeve): brenda
**35 gradë nga drejt lart** është `ground`, çdo gjë tjetër `structure`. Shikuesi vizaton tokën
të plotë dhe strukturat pothuajse transparente. **Uji nuk pretendohet kurrë** - nuk dallohet nga toka e sheshtë
sipas formës, dhe një etiketë e gabuar do ta vizatonte një oborr si liqen. Çdo etiketë bëhet një
pjesë e `.glb` ([Dalja .glb](glb-output.md)).

## Mbulimi {#coverage}

`CoverageGrid(voxel=0.5)` regjistron, për çdo qelizë gjysmë-metri, katër gjëra që nuk janë e njëjta gjë:

| Termi | Ruhet | Pikët (secila e prerë në 0..1) | Pse numërohet veçmas |
|---|---|---|---|
| Sa herë u pa | numri i kuadrove kyç që e panë qelizën | `count / 3` | një herë është hamendje pa ç'të mesatarizosh |
| Nga sa drejtime | shuma e drejtimeve njësi të pamjes | `(1 - spread) / (1 - 0.93)`, ku spread = gjatësia e shumës / count | njëzet kuadro që ecin drejt një muri nuk kanë parallaks mes tyre; dy pamje tridhjetë gradë larg njëra tjetrës vlejnë më shumë |
| Nga sa larg | largësia më e afërt e vështrimit | `1 - nearest / 40 m` | gabimi i thellësisë rritet afërsisht me katrorin e largësisë |
| Sa mirë u vendos kamera | besueshmëria më e mirë e pozës | besueshmëria | gjeometria e bashkuar me një pozë të dyshimtë bie në vendin e gabuar |

Pikat e një kuadri grupohen më parë sipas qelizës, kështu që dhjetë mijë pikselë të një muri numërohen si një
vëzhgim nga një drejtim.

**Cilësia = prodhimi i katër termave**, jo mesatarja: janë kushte që secili duhet të plotësohet. Një
vend i parë dyqind herë nga një drejtim në gjashtëdhjetë metra është i vëzhguar keq, dhe një mesatare do ta fshihte
këtë pas një termi të shkëlqyer.

Shifrat kryesore (`summary`): qelizat e zëna, pjesa me cilësi të paktën 0.5 ("% well
seen" në dritare), cilësia mesatare dhe vëllimi.

### Pikat e dobëta {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. qelizat me cilësi nën 0.35 janë të dobëta;
2. qelizat e dobëta grupohen sipas **lidhshmërisë** (fqinjësi 26, union-find vetëm mbi qelizat e
   zëna - jo një raster mbi kutinë kufizuese, që në një vozitje të gjatë janë miliona qeliza
   bosh);
3. grupet me më pak se 8 qeliza shpërfillen;
4. arsyeja e çdo grupi është *termi më i dobët* më i zakonshëm i qelizave të tij, dhe pozicioni i tij mesatarja
   e qelizave të tij;
5. renditen nga më i madhi (pastaj cilësia më e keqe), më së shumti 8.

| Arsyeja | Këshilla e shfaqur |
|---|---|
| few views | Seen only once or twice — walk past it again. |
| one direction | Only seen from one angle. Step sideways and look at it again. |
| distant | Only seen from far away. Get closer to it. |
| poor tracking | The camera was not well located here. Approach it more slowly. |

Lidhshmëria ka rëndësi: grupimi sipas një rrjete blloqesh të fiksuar raporton një dhomë anësore të lënë pas dore si
shumë unaza të veçanta, dhe askush nuk mund të dallojë tetë vende nga një vend i numëruar tetë herë.

### Pamja e planit {#the-plan-view}

`top_down(resolution)` projekton qelizat në x/z dhe mban cilësinë **më të mirë** për çdo kolonë
(dikush që qëndron në një dhomë ka mbulim të dobët të tavanit dhe mbulim të shkëlqyer të
dyshemesë; mesatarja do ta ngjyroste dhomën qelibar). Kolonat e pavëzhguara kurrë shënohen veçmas.
Dritarja e vizaton në 200 x 200, overlay në 120 x 120 ([Dritarja e skanimit](reconstruction-scan-ui.md#the-coverage-map)).

### A rindërtohet kjo? {#is-this-reconstructable}

Çdo 25 kuadro të bashkuar, pasi ka të paktën 500 qeliza:

| Konstatimi | Verdikti | Mesazhi (i shkurtuar) |
|---|---|---|
| më pak se 2% e qelizave kanë përhapje pamjeje nën 0.93 | nuk rindërtohet | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| largësia mediane më e afërt mbi 25 m | nuk rindërtohet | Everything was seen from N m away or further ... Get closer to what you want. |
| më pak se 6% me përhapje të mirë | rindërtohet, me paralajmërim | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Parallaksi i ulët ka dy shkaqe që kjo nuk i dallon, prandaj mesazhi i emërton të dyja.

## Ngjyra {#colour}

Ngjyra e bashkimit për çdo voxel është e lirë dhe e drejtpërdrejtë, dhe e turbullt: çdo piksel në një qelizë çerek-metri
mesatarizohet, përfshirë ato që u panë nga ana nga tridhjetë metra. Prandaj gjatë eksportit rrjeta
ngjyroset përsëri, një herë, nga vetë kuadrot:

- **Kuadrot e mbajtura**: deri në **160** kuadro kyç (imazh dhe pozë), të zgjedhura me kampionim rezervuari që
  të shpërndahen nëpër gjithë skanimin dhe jo në bishtin e tij.
- **Për çdo kulm** (`project_colours`), çdo kuadër i mbajtur kontribuon nëse kulmi është përpara
  kamerës dhe brenda imazhit, sipërfaqja është kthyer jo më shumë se rreth 70 gradë larg
  përballjes frontale me kamerën (`|normal . view| > 0.34`), është më afër se **35 m**, dhe asgjë
  më afër nuk qëndronte përpara saj (më poshtë).
- Çdo pamje e tillë vlerësohet `facing x (1 - distance / 35)`, kështu që një pamje e afërt frontale fiton ndaj një
  të largët me kënd të ulët. **4 pamjet me pikët më të larta** të çdo kulmi mbahen - në çfarëdo renditjeje që janë
  kuadrot, një pamje më e mirë zëvendëson më të dobtën e katërve - dhe përzihen, të peshuara me
  të njëjtën pikë.
- **Fshehja (occlusion)**: në çdo kuadër kulmet e vetë rrjetës në pamje vizatohen në një bufer thellësie me
  qeliza 2-pikselëshe, duke mbajtur më të afërtin për çdo qelizë. Një kulm më shumë se `0.3 m + 5%` e largësisë së tij
  pas më të afërtit në qelizën e tij ishte i fshehur në atë kuadër - një mur mes kamerës dhe
  rrugës përtej - dhe ajo pamje nuk numërohet fare. Testi njeh vetëm rrjetën: një pengesë që
  nuk u bashkua kurrë (një makinë që kalon, një shtyllë kabine jashtë maskës së HUD) nuk kapet.
- Një kulm që asnjë kuadër nuk e pa e mban ngjyrën e voxel-it të tij; një kulm pa asnjërën është gri e mesme (e zeza
  do të lexohej si vrimë).

Ngjyra shkruhet si `COLOR_0` për çdo kulm, jo si atlas teksture. Pamja e paracaktuar e shikuesit është një
hartë gri nën nxehtësi të ngopur; ngjyra është aty për të gjetur rrugën në një qark të skanuar, ku
gjeometria vetëm nuk e ndan nga bankina, dhe shfaqet pas çelësit *Ngjyra e kapur* të shikuesit në panelin e tij
Sfondi / niveli. Një atlas do ta shumëfishonte madhësinë e skedarit dhe do të kishte nevojë për një shpalosës,
për një pamje që qëllimisht nuk është e paracaktuara. Blender dhe mjete të tjera glTF e lexojnë `COLOR_0`.
