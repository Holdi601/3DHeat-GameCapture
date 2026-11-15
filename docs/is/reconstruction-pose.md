---
title: "Staða myndavélar og kvarði"
nav_order: 4
lang: "is"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Staða myndavélar og kvarði {#camera-pose-and-scale}

Dýptarkort segir hversu langt hlutir eru frá *einum* sjónarpunkti. Til að breyta mörgum þeirra í eitt borð
þarf að vita hvar hver sjónarpunktur var, og í hvaða einingum. Þessi síða fjallar um lifandi leiðirnar;
offline feed-forward lausnin er á [Offline endurgerð](reconstruction-offline.md).

Kóði: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Myndavélarlíkanið {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` smíðar nálaraugnamyndavél (pinhole) úr **láréttu sjónsviði** sem þú
stillir í glugganum: `fx = (width / 2) / tan(fov / 2)`, ferningslaga punktar (`fy = fx`),
miðpunktur myndar í miðju rammans. Leikur gefur ekki út vörpun sína, svo þetta er
eina ágiskaða talan: of þröngt og senan lítur út fyrir að vera dýpri en hún er. Offline leiðin notar
65 gráður.

`Pose` er geymd sem **heimur-frá-myndavél**: `rotation` (3 x 3) og `translation` = miðja myndavélarinnar
í heiminum, sem er það sem ferillinn, þekjukortið og yfirlagið vilja öll.

## Sjónræn hreyfimæling (sjálfgefið) {#visual-odometry-the-default}

`VisualOdometry` rekur hvern lykilramma gegn þeim fyrri:

1. **Eiginleikar**: ORB, allt að 1500 á ramma, aðeins fundnir á heimsmaskanum (sjá
   [Upptaka](reconstruction-capture.md#what-is-not-the-world)).
2. **Samsvaranir** við fyrri lykilramma: tæmandi leit, Hamming-fjarlægð, víxlathugað (aðeins
   gagnkvæmt bestu pör).
3. **Lyfta í 3D**: dýpt fyrri rammans er þegar í heimseiningum, svo samsvarandi punktar hans
   verða heimspunktar.
4. **Staðsetja myndavélina**: `solvePnPRansac` meðal þessara punkta (endurvörpunarskekkja 3 px,
   öryggi 0,999, 200 umferðir). Hliðrunin kemur út í sömu einingum, svo **kvarðinn
   flyst yfir bilið**.
5. **Festa dýpt þessa ramma**: eigin spáð andhverf dýpt hans er aðlöguð (`fit_scale`)
   að dýpt PnP innlagagilda, og hringurinn endurtekinn.

**Fyrsti ramminn** er upphafspunkturinn: samsemdarstaða, og affín dýptar hans er annaðhvort jarðkvörðunin
hér að neðan eða, án hennar, samsemd (endurgerðin er þá sjálfri sér samkvæm
en án eininga).

Staða þarf að minnsta kosti **18 RANSAC innlagagildi** - greinilega fleiri en lágmark PnP sem er sex, því
lausn úr rétt nægilega mörgum punktum er einmitt sú sem er sjálfsörugglega röng.

### Öryggi {#confidence}

Hver rammi sem fær stöðu fær öryggi á bilinu 0..1 sem vigtar samruna hans og þekju:

| Staða úr | Öryggi |
|---|---|
| mælingagögnum | 1,0 |
| feed-forward lausn | 0,85 |
| sjónrænni rakningu | `inliers / matches x min(1, inliers / 60)` |

### Þegar rakning brotnar {#when-tracking-breaks}

Rammi sem ekki er hægt að staðsetja er tilkynntur, aldrei giskað: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Engin staða er skráð,
og ekkert er samrunnið. Að halda áfram frá síðustu stöðu, eða byrja nýjan upphafspunkt, myndi setja
næsta kafla borðsins á handahófskennda hliðrun - saum sem lítur út eins og raunveruleg rúmfræði.

Eftir brot er hver nýr rammi **endurstaðsettur** gagnvart gagnagrunni liðinna lykilramma (hver
fjórði rakinn rammi er bætt við, allt að 120, elsti felldur niður), nýjasti fyrst, með sama
samsvörunar- og PnP-skrefi. Þar til eitt tekst eru rammar felldir niður. Endurheimtur rammi heldur áfram í
sama hnitakerfi. Endurheimtur eru taldar og sýndar í glugganum (`N recovered`).

### Lykkjulokun: slökkt {#loop-closure-off}

Sami gagnagrunnur styður lykkjulokun: samsvörun við mun eldri lykilramma til að
greina endurheimsókn og smella ferlinum aftur á hana. **Hún er slökkt sjálfgefið og skanninn
kveikir aldrei á henni** (`Reconstructor(loop_closure=False)`). Í síendurteknu landslagi - rallíleið,
gangur, röð trjáa - lítur hver kafli út eins og allir aðrir og eiginleikasamsvörun staðfestir
rangar endurheimsóknir, sem festir myndavélina nálægt upphafsstað á meðan hún ekur áfram. Að gera það
rétt krefst staðargreiningar (orðapoka-orðaforði eða lærður lýsir) og
rúmfræðilegrar staðfestingar gegn korti, sem er ekki smíðað.

Þegar kveikt er á því úr kóða þarf lokun: lykilramma sem er að minnsta kosti 60 lykilrömmum gamlan, innan 6 m frá
núverandi stöðu, samsvörun með að minnsta kosti 90 innlagagildum, sem færir stöðuna um meira en 0,02 m og
minna en 6 m. Jafnvel þá kemur hún aðeins í stað núverandi stöðu; hún er ekki stöðurit (pose graph) og færir ekki
fyrri ramma eða samrunna rúmfræði.

## Stöður úr mælingagögnum {#telemetry-poses}

Með **Racing telemetry (Forza) -> Listen for position data** á kemur ferill myndavélarinnar úr
Data Out frá Forza í stað myndanna (`ForzaPoseSource`):

- Þráður hlustar á `127.0.0.1:<port>` (sjálfgefið 5300) með sömu uppsetningargreiningu og
  upptökutækin ([Forza](telemetry-forza.md)); pakkar eru notaðir meðan `isRaceOn` er sett. Upptekin gátt
  er tilkynnt, ekki kastað sem villu: mælingagögn eru uppfærsla og skönnunin heldur áfram sjónrænt.
- Hver pakki er stimplaður með **einhæfa tímanum þegar hann barst** - sömu klukku og upptakan
  stimplar ramma með. Eigin tímastimpill leiksins telur frá einhverju óskyldu, svo hann er ekki
  notaður til stillingar. Loopback-skjálfti upp á millisekúndu eða tvær er um 6 cm á 200 km/klst.
- Gangandi 30 sekúndna biðminni er haldið. Staða ramma er **innskotin** úr sýnunum báðum megin við
  upptökutíma hans: staðsetning línulega, snúningur með kúlulaga innskoti (blönduð
  fylki er ekki snúningur og myndi skekkja hvern punkt). Yfir bil lengra en **0,35 s**, eða
  utan biðminnisins, er engin staða.
- `pose_from_forza`: myndavélin er sett við bílinn (hliðrun eltimyndavélar er ekki gefin út).
  **Staðsetningar eru geymdar nákvæmlega eins og leikurinn sendir þær**: heimur Forza er þegar Y-upp (x og z
  þvert yfir kortið, y hæðin), sem er hvernig hringskrárnar og leiðaskrárnar skrifa hann, svo
  yfirborðið lendir á sömu hnitum og hringirnir sem teknir voru upp yfir því. (Eldri útgáfa víxlaði
  y og z fyrir „Z-upp“ heim og lagði brautina á hliðina.)
- Snúningurinn er yaw, síðan pitch, síðan roll, með merkingum lesnum af upptökuhringjum: 
  ferðastefnan `atan2(dx, dz)` er jöfn yaw, brekkan sem klifrað er er jöfn mínus pitch
  (jákvætt er nef niður), og roll er jákvætt þegar hægri fjöðrun er þjöppuð
  (jákvætt lækkar hægri hliðina). Ásar bílsins (x hægri, y upp, z áfram) eru síðan snúnir í
  ása myndavélarinnar (x hægri, y niður, z áfram) með því að snúa y við.
- Heimur Forza er **örvhentur** og rammi myndavélarinnar er það ekki, svo fylkið heimur-frá-myndavél sem
  kemur út er speglun (ákvörðuður -1), og skönnunin kemur út örvhent
  eins og hringskrárnar. Innskot verður ekki fyrir áhrifum (snúningurinn milli tveggja slíkra staða er réttur
  snúningur).
- Þegar rammi hefur enga stöðu úr mælingagögnum (bil) fellur endurgerðarinn aftur á **sjónræna rakningu**
  fyrir þann ramma, heldur áfram frá síðustu stöðu úr mælingagögnum, og fer aftur í stöður straumsins um leið og hann
  svarar. PnP skilar aðeins snúningum, svo í spegluðum heimi er það leyst með
  heiminn speglaðan um z og spegluninni snúið til baka; rammi lendir í hnitum leiksins.
  Aðeins ef sjónræn rakning mistekst líka er rammi órakinn.

### Dýptarkvarði úr mælingagögnum {#depth-scale-from-telemetry}

Leikurinn segir hvar myndavélin er, ekki hversu langt neitt er í burtu, svo dýpt hvers ramma þarf enn
festingu - en ekki með því að keðja frá ramma núll, sem hefur handahófskennda einingu meðan staðan
er í metrum. Í staðinn eru eiginleikar sem passa milli fyrri og núverandi ramma (að minnsta kosti
8) **þríhyrningsmældir beint úr stöðunum tveimur sem eru þekktar**, í metrum, og dýptarkortið er
aðlagað að punktunum fyrir framan myndavélina. Hver rammi er festur gegn mælingagögnunum, svo
engin keðja er til að reka.

Ef stöðurnar tvær eru minna en **0,05 m** frá hvor annarri eru geislarnir nær því samsíða og þríhyrningsmæling er
suð, svo ramminn er skilinn eftir án festingar: staðsettur nákvæmlega, en ekki samrunninn („positioned, but its
depth has no scale yet“). Þess vegna telur glugginn *setta* og *samrunna* ramma sér.

## Kvarði {#scale}

Sjónræn hreyfimæling keðjar afstæðan kvarða rétt, en allt borðið svífur samt á einum óþekktum
stuðli. Afstætt úttak Depth Anything kemur út í handahófskenndum einingum, svo að skilja fyrsta
rammann eftir á samsemd setur heiminn innan metra frá myndavélinni í handahófskenndri stærð.

`GroundCalibrator` festir þann stuðul út frá **hæð myndavélarinnar yfir jörðu**, mældri á
**fyrsta lykilramma** og, þegar hann hefur enga nothæfa jörð, á þeim sem á eftir koma:

- Hæð myndavélar: **1,15 m** (augnhæð ökumanns) - glugginn notar alltaf þetta; skriftur geta
  gefið 1,70 m (`WALKING_HEIGHT`, standandi spilari) eða `None` (engin kvörðun).
- Jarðsýni: raðir 62-92% niður rammann (neðan sjóndeildarhrings, ofan vélarhlífar eða vopns) og
  dálkar 30-70% þvert (fjarri vegöxlum).
- Hver punktur þar með nothæfa spá er lyft með dýpt `1 / predicted` í einingum netsins;
  punktar neðan sjónássins gefa hæð neðan myndavélarinnar. Miðgildi þeirra er
  hæð myndavélarinnar í einingum netsins, svo `metres per unit = 1.15 / median`, og affín rammans er
  `scale = 1 / metres_per_unit`, shift 0.
- Aðeins treyst með að minnsta kosti 200 jarðsýnum og **dreifingu** (miðgildisfrávik absólút deilt með
  miðgildi) undir **0,60**.
- Á fyrsta lykilramma verður aðlögunin eining upphafspunktsins, svo skönnunin er í metrum frá
  byrjun. Þegar fyrsti lykilramminn hefur enga nothæfa jörð byrjar skönnunin án eininga og hver síðari
  rakinn lykilrammi er reyndur, allt að **30 römmum** alls. Sá fyrsti sem kvarðast gefur
  *metra á einingu*: miðgildi, yfir jarðbandið, dýptarinnar sem jörðin gefur til kynna deilt með
  dýptinni sem keðjan gaf þeim ramma. Allt sem þegar er samrunnið er í einingu fyrsta rammans, svo
  stuðullinn er ekki færður aftur inn í keðjuna; hann er notaður á allt borðið (og á merktu
  staðina) þegar það er skrifað, og á vegalengdina sem sýnd er á meðan. Voxelstærð er þá í einingum fyrsta
  rammans, svo stærð hennar í metrum víkur frá stillingunni um þann stuðul.
- Eftir 30 ramma án jarðar helst skönnunin án eininga, og segir það.
- Með mælingagögnum eru síðari lykilrammar ekki reyndir: dýptin er fest við metra mælingagagnanna.

Að vera innan tíu prósenta frá réttri stærð er betra en að vera þúsundfalt í burtu; mælingagögn,
þar sem þau eru til, gera það óþarft. Athugasemdin er sýnd í glugganum undir rakningarlínunni,
sem `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (með `found on frame N, so the level is scaled
by F when it is written` þegar það kom seinna), `no usable ground in the first N frames - sizes are
relative, not metres`, eða `in metres, from the telemetry's positions`.

## Búntaðlögun og löng ferli (ekki tengt inn) {#bundle-adjustment-and-long-tracks-not-wired-in}

Tveir hlutir eru til fyrir framtíðar gluggalausnara og eru **ekki notaðir af skannanum**:

- **`FeatureTracks`** heldur auðkenni eiginleika yfir hundruð ramma með Lucas-Kanade
  rakningu (600 eiginleikar, endursáð undir 60%, fram-aftur vikmörk 1 px, nýir eiginleikar 10 px
  frá þeim sem fyrir eru), sem er það sem búntaðlögun þarf - lýsisamsvörun milli
  samliggjandi ramma gefur aðeins pör.
- **`bundle_adjust`** fínstillir glugga af stöðum og punktum saman með
  `scipy.optimize.least_squares` (traustsvæði, mjúkt L1 tap með 2 px kvarða, skýrt
  gisið Jacobi-mynstur, fastar myndavélar endurheimtar nákvæmlega). Prófað gegn þekktum sannleika í
  `tests/test_bundle.py`.

`WindowedOdometry` sameinar þetta (12 lykilramma gluggar, lausn á 3 lykilramma fresti, fyrstu tvær
myndavélarnar fastar, punktum með yfir 6 px skekkju hent, stökkum yfir 6 sinnum nýlegt skref hafnað). Skýring þess
í kóða skráir að á raunverulegu myndefni **hrundi leiðin saman og var mun hægari** en
rakning ramma á ramma, með mælikvarðafrelsi (gauge freedom) og dýptarbyggða ræsingu sem þekktar orsakir og
þriðju orsök óþekkta. Því er ramma-á-ramma hreyfimæling áfram sjálfgefin; líklega lagfæringin sem nefnd er
í kóðanum er tveggja sýna ræsing með undirstöðufylki (essential matrix) með grunnlínuna fasta úr
jarðplanskvörðuninni.
