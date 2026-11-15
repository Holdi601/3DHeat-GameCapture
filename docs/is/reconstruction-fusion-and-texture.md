---
title: "Samruni, þekja og litur"
nav_order: 5
lang: "is"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Samruni, þekja og litur {#fusion-coverage-and-colour}

Kóði: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Hver lykilrammi sem fær stöðu uppfærir tvö gisin rist í einu: **yfirborðsrúmmálið**, sem verður að
möskvanum, og **þekjuristið**, sem segir hversu mikið á að trúa því og hvert á að fara aftur.
Bæði eru uppfærð fyrir hvern lykilramma, ekki í lokin, því þekjukortið er það sem spilarinn
stýrir eftir.

## Frá dýpt í punkta {#from-depth-to-points}

Fyrir hvern lykilramma þar sem staða er þekkt **og** dýpt hefur kvarða:

1. Annar hver punktur í hvora átt er notaður (`PIXEL_STRIDE = 2`; nágrannapunktar á
   einu yfirborði eru ekki óháðar mælingar).
2. Dýpt er breytt í metra með affín aðlögun rammans.
3. Aðeins geymt milli **0,35 m** (nær er vopnið, HUD, vélarhlífin) og **60 m**
   (skekkja með einu auga vex nokkurn veginn með kvaðrati fjarlægðar, svo fjarlægir punktar eru suð í lögun
   rúmfræði) og aðeins á heimspunktum maskans.
4. Lyft í gegnum myndavélarlíkanið og fært inn í heiminn með stöðunni.
5. Hver punktur ber lit punktsins.

Rammi sem hefur stöðu en ekkert dýptarkvarða telst *settur* en ekki *samrunninn*.

## Yfirborðsrúmmálið {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxel er „Surface detail“ í glugganum.

### Vigtað upptökuhlutfall, ekki TSDF {#weighted-occupancy-not-a-tsdf}

Stytt undirritað fjarlægðarsvið (TSDF) sker eftir geisla hvers punkts og fær fínar byggingar og
hreint autt rými rétt, því það veit að geisli fór *í gegnum* autt rými. Það þýðir að ganga eftir
geislanum fyrir hvern af hundruðum milljóna punkta. Þetta rúmmál safnar í staðinn
**vigtuðu upptökuhlutfalli (weighted occupancy)** fyrir hvern voxel og keyrir marching cubes á sléttaða niðurstöðu: nógu hratt til að
keyra meðan skannað er, á vél án nothæfs skjákorts, og úttakið er lokað yfirborð en ekki
punktaský. Kostnaðurinn: fínar byggingar og autt rými verða verri en TSDF næði.

### Að samþætta ramma {#integrating-a-frame}

- Punktum er skipt í voxla (`floor(point / voxel)`).
- Hver voxel sem snertist fær `weight x sqrt(count / max_count)`, þar sem `count` er hversu margir af
  punktum rammans féllu í hann og `weight = max(0.1, pose confidence)`. Kvaðratrót: umfram vissan punkt
  eru fleiri punktar á sama yfirborði frá sama stað ekki lengur sönnun; vigtun eftir öryggi stöðunnar
  kemur í veg fyrir að vafasöm staða ýti yfirborðinu til.
- Litur er gangandi vigtað meðaltal á hvern voxel.

Ristið er **gisið**: gengin leið snertir örlítið brot af umlykjandi kassa sínum. Voxelhnit
eru pökkuð í einn 64-bita lykil (21 bit á ás, allt að +-1.048.575 voxlar - við
0,25 m um +-262 km) og flett upp með raðaðri fylkingu og tvíleit, fullkomlega vigruð.

### Að vinna möskvann út {#extracting-the-mesh}

1. Voxlar með þyngd undir **0,35** eru felldir niður (stakir punktar á jaðri skuggamyndar yrðu
   broddar).
2. Þyngdir eru skalaðar með **75. hundraðshluta** yfir skönnunina og klipptar við 1.
3. Upptekna rýminu er skipt í **blokkir með 64 voxla** á hlið, hver útfærð með
   **3 voxla geislabaug (halo)** af gögnum nágranna sinna (án hans lokast hver blokkamörk í
   vegg og vegur kemur út sem röð af kössum).
4. Svið hverrar blokkar er slétt með Gauss (sigma 0,8 voxel) til að fjarlægja bylgjurnar sem dýptarsuð
   skilur eftir.
5. **Umferð eitt**: 99. hundraðshluti sléttaða sviðsins, sýnatekinn yfir allar blokkir (í mesta lagi 2
   milljón gildi), setur einn altækan stigskala. Að stilla á hverja blokk fyrir sig myndi hefja stakt
   útlagagildi upp í fullt yfirborð í sinni eigin tómu blokk.
6. **Umferð tvö**: svið hverrar blokkar deilt með þeim kvarða, marching cubes við **0,5**. Þríhyrningur
   tilheyrir þeirri blokk sem **miðja** hans lendir í, svo þríhyrningar sem liggja yfir sauma eru gefnir út
   nákvæmlega einu sinni.
7. Hornpunktar eru færðir í heimseiningar við miðju voxla; hver hornpunktur tekur lit voxils síns
   (miðgrár þar sem hann lendir utan upptekins voxils).

Útdráttur blokk fyrir blokk er það sem gerir skönnun af brautarstærð mögulega: ein þétt fylking yfir
kílómetra ferningskassa við 0,25 m væri milljarðar hólfa. `tests/test_track_scale.py` festir
að það virki á þeim kvarða með minni í réttu hlutfalli við það sem var skannað.

### Jörð og bygging {#ground-and-structure}

`classify` merkir hvern þríhyrning eftir stefnuvigri hans (snúið eftir útdregnum hornpunktsvigrum): innan
**35 gráðna frá beint upp** er `ground`, allt annað `structure`. Áhorfandinn teiknar jörð
heila og byggingar nær gegnsæjar. **Vatn er aldrei eignað** - það verður ekki greint frá flatri
jörð eftir lögun, og röng merking myndi sýna húsagarð sem stöðuvatn. Hvert merki verður einn
hluti `.glb` skráarinnar ([.glb úttakið](glb-output.md)).

## Þekja {#coverage}

`CoverageGrid(voxel=0.5)` skráir, fyrir hvert hálfs metra hólf, fjóra hluti sem eru ekki það sama:

| Hugtak | Geymt | Einkunn (hver klippt í 0..1) | Af hverju það telst sér |
|---|---|---|---|
| Hversu oft séð | fjöldi lykilramma sem sáu hólfið | `count / 3` | einu sinni er ágiskun án nokkurs til að taka meðaltal við |
| Úr hve mörgum áttum | summa einingasjónstefna | `(1 - spread) / (1 - 0.93)`, þar sem spread = lengd summunnar / count | tuttugu rammar gangandi beint á vegg hafa enga hliðrun (parallax) sín á milli; tvær sýnir með þrjátíu gráðna millibili eru meira virði |
| Úr hve mikilli fjarlægð | nærsta sjónfjarlægð | `1 - nearest / 40 m` | dýptarskekkja vex nokkurn veginn með kvaðrati fjarlægðar |
| Hversu vel myndavélin var staðsett | besta öryggi stöðu | öryggið | rúmfræði sem samrunnin er með vafasamri stöðu lendir á röngum stað |

Punktum rammans er fyrst safnað í hólf, svo tíu þúsund punktar af einum vegg teljast ein
athugun úr einni átt.

**Gæði = margfeldi fjögurra liðanna**, ekki meðaltalið: þeir eru skilyrði sem öll þurfa
að standast. Staður sem sést tvö hundruð sinnum úr einni átt úr sextíu metra fjarlægð er illa athugaður, og
meðaltal myndi fela það á bak við einn frábæran lið.

Aðaltölur (`summary`): upptekin hólf, hlutfall með gæði að minnsta kosti 0,5 („% well
seen“ í glugganum), meðalgæði og rúmmál.

### Veikir blettir {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. hólf með gæði undir 0,35 eru veik;
2. veik hólf eru flokkuð eftir **tengingu** (26 nágrannar, union-find yfir upptekin
   hólf eingöngu - ekki raster yfir umlykjandi kassa, sem á langri akstursleið eru milljónir tómra
   hólfa);
3. hópar með færri en 8 hólf eru hunsaðir;
4. ástæða hvers hóps er algengasti *veikasti liðurinn* í hólfum hans, og staða hans meðaltal
   hólfa hans;
5. raðað stærsta fyrst (síðan verstu gæði), í mesta lagi 8.

| Ástæða | Ráð sem sýnt er |
|---|---|
| fáar sýnir | Seen only once or twice — walk past it again. |
| ein átt | Only seen from one angle. Step sideways and look at it again. |
| fjarlægt | Only seen from far away. Get closer to it. |
| léleg rakning | The camera was not well located here. Approach it more slowly. |

Tengingin skiptir máli: að flokka eftir föstu blokkarristi tilkynnir eitt vanrækt hliðarherbergi sem marga
aðskilda hringi, og enginn getur greint átta staði frá einum stað talinn átta sinnum.

### Yfirlitskortið {#the-plan-view}

`top_down(resolution)` varpar hólfunum á x/z og geymir **bestu** gæði í hverjum dálki
(sá sem stendur í herbergi hefur slæma þekju á loftinu og frábæra þekju á
gólfinu; meðaltal myndi mála herbergið gult). Dálkar sem aldrei voru athugaðir eru merktir sér. Glugginn
teiknar það í 200 x 200, yfirlagið í 120 x 120 ([Skannglugginn](reconstruction-scan-ui.md#the-coverage-map)).

### Er hægt að endurgera þetta? {#is-this-reconstructable}

Á 25 samrunna ramma fresti, þegar hólf eru orðin að minnsta kosti 500:

| Niðurstaða | Úrskurður | Skilaboð (stytt) |
|---|---|---|
| færri en 2% hólfa hafa sjónardreifingu undir 0,93 | ekki endurgerðarhæft | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| miðgildi nærstu fjarlægðar yfir 25 m | ekki endurgerðarhæft | Everything was seen from N m away or further ... Get closer to what you want. |
| færri en 6% með góða dreifingu | endurgerðarhæft, með viðvörun | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Lág hliðrun (parallax) á sér tvær orsakir sem þetta greinir ekki í sundur, og þess vegna nefna skilaboðin báðar.

## Litur {#colour}

Litur hvers voxils úr samruna er ódýr og lifandi, og óskýr: hver punktur í
fjórðungs metra hólfi er tekinn í meðaltal, líka þeir sem sáust á rönd úr þrjátíu metra fjarlægð. Því er möskvinn við útflutning litaður
aftur, einu sinni, úr römmunum sjálfum:

- **Rammar geymdir**: allt að **160** lykilrammar (mynd og staða), valdir með geymslusýnatöku (reservoir sampling) svo þeir
  dreifist yfir alla skönnunina en ekki aðeins endann.
- **Fyrir hvern hornpunkt** (`project_colours`) leggur hver geymdur rammi sitt af mörkum ef hornpunkturinn er fyrir framan
  myndavélina og innan myndar, yfirborðið snýr ekki meira en um 70 gráður frá því að
  snúa beint að myndavélinni (`|normal . view| > 0.34`), það er nær en **35 m**, og ekkert
  nær stóð fyrir framan það (hér að neðan).
- Hver slík sýn fær einkunn `facing x (1 - distance / 35)`, svo nærsýn beint á slær fjarlæga
  sýn á ská. **4 hæstu** sýnirnar fyrir hvern hornpunkt eru geymdar - í hvaða röð sem
  rammarnir eru kemur betri sýn í stað þeirrar veikustu af fjórum - og blandaðar, vigtaðar með
  sömu einkunn.
- **Skygging (occlusion)**: í hverjum ramma eru eigin hornpunktar möskvans í sjónmáli teiknaðir í dýptarbiðminni með
  2 punkta hólfum, nærsti í hverju hólfi geymdur. Hornpunktur sem er meira en `0.3 m + 5%` af fjarlægð sinni
  á bak við þann nærsta í hólfinu var falinn í þeim ramma - veggur milli myndavélarinnar og
  vegarins handan - og sú sýn telst ekki. Prófið þekkir aðeins möskvann: skyggjandi hlutur sem
  var aldrei samrunninn (bíll sem ekur framhjá, stjórnklefastólpi utan HUD maskans) næst ekki.
- Hornpunktur sem enginn rammi sá heldur voxellit sínum; hornpunktur með hvorugt er miðgrár (svart
  læsist sem gat).

Litur er skrifaður sem `COLOR_0` á hvern hornpunkt, ekki sem áferðaratlas. Sjálfgefið útlit áhorfandans er
grátt kort undir mettuðum hita; liturinn er til að finna veginn á skönnuðum hring, þar sem
rúmfræðin ein aðgreinir hann ekki frá vegkantinum, og er sýndur á bak við rofann *Skráður litur* í
spjaldinu Bakgrunnur / borð. Atlas myndi margfalda skráarstærðina og krefjast afvafnings (unwrapper),
fyrir sýn sem er viljandi ekki sjálfgefin. Blender og önnur glTF verkfæri lesa `COLOR_0`.
