---
title: "Upptaka, möskvar og gæði ramma"
nav_order: 2
lang: "is"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Upptaka, möskvar og gæði ramma {#capture-masks-and-frame-quality}

Kóði: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Hvaðan rammarnir koma {#where-frames-come-from}

Upptökumarkmið er eitt af þessu:

| Markmið | Uppspretta | Athugasemdir |
|---|---|---|
| `monitor:<n>` | heill skjár, í beinni | „Whole screen“ í glugganum með númerið í „Which“ |
| `window:<title>` | einn gluggi, í beinni | „A window“ í glugganum með heiti hans |
| skráarslóð | myndbandsskrá | „A video file“ í glugganum; hvaða snið sem OpenCV getur lesið |

### Bein upptaka: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` notar `windows-capture` pakkann, sem vefur utan um **Windows Graphics Capture** -
opinbera forritaskilið sem skjáupptökuforrit nota. Engu er sprautað inn í leikinn. Músarbendillinn er ekki
tekinn upp og enginn gulur rammi er teiknaður.

Upptökusafnið skilar römmum í kallfall á þræði samsetningarvélarinnar (compositor) og ætlast til að það
skili strax, svo kallfallið afritar aðeins rammann (biðminnið er endurnýtt), breytir BGRA í
RGB, breytir stærð, stimplar hann og setur í biðröð með **4 römmum**. Þegar biðröðin er full er
**elsti ramminn felldur niður** og teljari hækkar: að dragast aftur úr á að kosta ramma, ekki
minni eða réttleika, og beina myndin á að sýna hvar spilarinn er núna. Niðurfelldir rammar
sjást í tölfræðilínu gluggans, og ef meira en helmingur er felldur niður birtist ábending.

Hver rammi ber `t` (sekúndur frá því upptakan hófst) og `monotonic` (hrátt
`time.monotonic()` við upptöku), sömu klukku og mælingagagnapakkar eru stimplaðir með - sem er
það sem gerir kleift að para Forza-stöður við ramma.

`windows-capture` er valfrjáls í athugun á ósjálfstæðum: án hans er samt hægt að skanna
myndbandsskrá.

### Myndbandsskrár {#video-files}

`VideoSource` les með OpenCV, breytir í RGB og breytir stærð. Gámur án rammatíðni
er meðhöndlaður sem 30 fps. Tímastimplar eru rammanúmer deilt með rammatíðni; skrá hefur enga
veggklukku, svo ekki er hægt að stilla mælingagögnum saman við myndband.

### Upplausn {#resolution}

Stærð ramma er breytt við uppsprettuna svo lengsta hliðin sé upptökuhlið forstillingarinnar (Draft 640,
Balanced 960, Detailed 1280 px), með flatarmálsinnskoti (area interpolation). 4K rammi er þrítugfalt fleiri punktar
en dýptarlíkanið notar.

## Lykilrammar {#keyframes}

Nær allir rammar upptöku eru óþarfir: að standa kyrr gefur hundruð mynda af einum
hlut. Endurgerðin vill *hliðrun (parallax)*. Því er rammi geymdur eftir því **hversu mikið myndin
breyttist frá síðasta geymda ramma**, ekki eftir tímamæli.

`picture_change(a, b)`:

1. báðir rammar í grátt og niður í 16 x 16 rist af meðaltölum reita (meðaltöl reita bregðast við því að
   myndin hreyfist, ekki við korn, lauf, flökt eða HUD);
2. meðalabsólútmismunurinn, sem brot af 255;
3. þegar heimsmaski er þekktur er hver reitur vigtaður eftir því hversu stór hluti hans er heimur en ekki
   stjórnklefi, svo reitur sem er hálfur mælaborð telst hálfur (notað þegar maskinn þekur meira en 5% af
   þyngd ristarinnar).

Þröskuldurinn **aðlagast upptökunni**: fyrir fyrstu 30 rammana er hann upphafsgildi
forstillingarinnar (0.020 / 0.010 / 0.004), síðan er hann hlutfallsmark forstillingarinnar (0.85 / 0.65 / 0.40) af
síðustu 240 mældu breytingum, aldrei undir 0.0001. Rammi er geymdur þegar breyting hans nær
þröskuldinum; fyrsti ramminn er alltaf geymdur. Fastur þröskuldur getur ekki virkað á milli sena - breyting
milli ramma á dimmum stjórnklefa er lítið brot af breytingu í björtu áferðarríku herbergi -
en „geymdu þriðjung með mestri hreyfingu“ þýðir það sama í báðum. Þröskuldurinn í notkun fylgir
hverri framvinduuppfærslu (`ScanProgress.threshold`), og göngu­hraðastikurnar í glugganum og
yfirlaginu bera síðustu breytingu saman við hann (`ScanProgress.toward_next_view`).

Aðeins geymdir rammar fara í gegnum dýptarlíkanið og endurgerðina. Rammar eru ekki vistaðir
nema kallari biðji um það (`keep_frames`); 160 þeirra eru geymdir til að lita möskvann (sjá
[lit](reconstruction-fusion-and-texture.md#colour)).

Skönnun endar þegar hún er stöðvuð, þegar myndband klárast, eða við tíma- eða lykilrammamörk.

## Það sem er ekki heimurinn {#what-is-not-the-world}

Tvennt í leikjaramma er ekki rúmfræði borðsins, og hvort tveggja eyðileggur endurgerð:

- **HUD.** Miðpunktur er endurtekningarsamasti eiginleikinn í hverjum ramma. Eiginleikasamanburður
  elskar hann, hann passar fullkomlega milli allra rammapara, og hver samsvörun er sönnun þess
  að myndavélin hreyfðist ekki - sem þjappar saman allri endurgerðinni.
- **Hlutir sem eru boltaðir við myndavélina.** Vopn, vélarhlíf, stjórnklefarammi, mælaborð. Raunveruleg
  rúmfræði í röngu hnitakerfi: samrunnin smyrst hún eftir allri gengnu leiðinni.

Tveir greinar finna þetta. Báðir búa til maska (255 = heimur, 0 = ekki heimur) eða `None` meðan ekki
eru næg gögn, og `None` þýðir alltaf „notaðu allt“, aldrei „notaðu ekkert“.

Maskinn er notaður:

- við **eiginleikaleit** í sjónrænni hreyfimælingu (að fela miðpunkt úr úttakinu en
  leyfa honum að greiða atkvæði um stöðuna myndi laga sýnilega einkennið en halda skaðlega einkenninu);
- á **samrunna punkta**, svo engin rúmfræði stjórnklefa er sameinuð;
- á **skerpu- og birtumælingu**, því stjórnklefi er alltaf fullkomlega skarpur;
- á **myndbreytinguna** sem ákveður lykilramma.

Hann er **ekki** notaður á rammana sem gefnir eru offline VGGT-lausnaranum (sjá
[Offline endurgerð](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: það sem breytist ekki {#screenmask-what-does-not-change}

Notaður frá fyrsta lykilramma þar til FlowMask er tilbúinn.

- Hver rammi er gerður grár, helmingaður og gerður óskýr (3 x 3 Gauss) svo eins punkts skjálfti í
  föstum HUD-hluta lesist ekki sem hreyfing.
- Absólútmismunur hvers punkts frá fyrri ramma er felldur inn í veldisvísismeðaltal
  (hrörnun 0.9), svo maskinn fylgir HUD sem birtist eða hverfur í miðri skönnun.
- Hann lærir aðeins af römmum þar sem vitað er að myndavélin hreyfist (í skönnun: þegar að minnsta kosti einn
  rammi hefur verið rakinn) - kyrr myndavél gerir allt kyrrstætt.
- Eftir **12** námsramma er punktur kyrrstæður þegar meðalbreyting hans er undir **0.22** af
  miðgildisbreytingu rammans - hlutfallslegt, svo þröskuldurinn fylgir því hversu hratt spilarinn hreyfist.
- Ef meira en **45%** af rammanum lesast kyrrstæð hefur forsendan brugðist (valmynd, myndskeið) og
  ekkert er falið.
- Maskinn er veðraður um einn punkt (HUD-jaðrar með jöfnun tilheyra hvorugri hliðinni) og stækkaður
  aftur í fulla stærð.

Athugasemd hans í glugganum: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, eða `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: það sem ferðast aldrei {#flowmask-what-never-travels}

Stjórnklefi er ekki kyrrstæður: vísar sveiflast, snúningshraðamælirinn titrar, smákortið snýst, svo
breytingaskynjari kallar þá punkta heim - og þeir eru verstu eiginleikar sem hægt er að gefa
stöðulausnara. FlowMask spyr betri spurningar: **hvaða eiginleikar haldast án þess að ferðast?**

- Í beinni skönnun lærir hann einu sinni, af fyrstu **40 lykilrömmunum** (grátóna); síðan kemur hann í stað
  ScreenMask út skönnunina.
- Rammarnir eru skornir í glugga með **30** römmum, skarast til hálfs. Í hverjum glugga eru allt að
  800 horn sáð (`goodFeaturesToTrack`, gæði 0.01, 8 px á milli) og fylgt með
  pýramída Lucas-Kanade (21 x 21, 4 stig) með **fram-aftur athugun**: ferli þar sem
  afturflæði lendir ekki innan 1 px frá upphafsstað er fellt niður, því rekjari sem
  rekur yfir á nágrannamynstur myndi búa til nákvæmlega „viðvarandi en kyrrstæða“
  einkennið sem leitað er að. Gluggar styttri en 20 rammar eru sleppt. Stuttir gluggar skipta máli:
  yfir langa keyrslu fer nær hver heimseiginleiki úr rammanum og sönnunargögnin þynnast út í ekkert.
- Hreinar ferðir hvers eiginleika sem lifir af eru bornar saman við **2% af breidd rammans**: undir því er hann
  „fastur“; yfir því „á hreyfingu“. Talið er saman á **24 x 24** rist af skjáhólfum eftir
  því hvar hver eiginleiki byrjaði.
- Hólf er lokað þegar það geymir að minnsta kosti 2 fasta eiginleika og fleiri fasta en hreyfanlega,
  **og** að minnsta kosti 3 af 8 nágrönnum þess eru líka lokaðir (stakt hólf er suð; dimmt myndefni
  býr til nóg af því).
- Aðeins lokuð svæði **tengd við jaðar rammans** eru geymd. Allt sem er boltað við
  myndavélina nær að jaðri skjásins; það sem situr í miðjunni og ferðast ekki er
  hvarfpunkturinn - þegar ekið er áfram hefur vegurinn beint framundan ekkert flæði og er rúmfræðin
  sem mest er sóst eftir.
- Svæðið sem lifir er stækkað um eitt hólf (jaðar mælaborðs er stigull).
- Ef meira en **60%** af rammanum yrðu falin er ekkert falið: í næturmyndefni geyma flest
  hólf engan rekjanlegan eiginleika, sem lesast eins og skífa.

Athugasemd hans: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, eða, yfir 60%, skilaboð sem útskýra að hann feli ekkert.

Offline leiðin lærir sama FlowMask af 4 keyrslum með 90 samfelldum römmum dreifðum yfir
myndbandið, í 960 x 540 ([Offline](reconstruction-offline.md)).

## Gæði ramma og ráð {#frame-quality-and-advice}

`QualityWatcher` dæmir hvern lykilramma og velur **eina** fyrirskipun, svo yfirlagið geti sagt
„hægðu á þér“ meðan tími er til.

Fyrir hvern ramma mælir það, á heimspunktum eingöngu (alla punkta ef maskinn skilur eftir minna en 5%):

- **skerpu**: dreifni Laplace - staðlaða eins-umferðar mælingin, og hún bregst við
  nákvæmlega því sem hreyfióskýrleiki eyðileggur;
- **birtu**: meðalgráastig, 0-255.

Skerpa hefur engan algildan kvarða (næturleið og björt gata eru munur á stærðargráðu, báðar í fókus), svo hún er metin
gagnvart **gangandi miðgildi þessarar upptöku**:
síðustu 90 rammar, þarf 20 áður en nokkuð er metið. Hver rammi er borinn saman við söguna
*áður* en honum er bætt við, svo langur óskýr kafli geti ekki dregið miðgildið niður til að mæta sjálfum sér.

| Ástand | Próf |
|---|---|
| flatt | skerpa í mesta lagi 1.0 (hleðsluskjár, veggur, himinn) |
| dimmt | birta undir 26 |
| óskýrt | skerpa undir 0.55 af miðgildi, og ekki flatt |

Ráðið, fyrsta samsvörun vinnur (raðað eftir því hvað hindrar skönnunina mest):

| Aðstæður | Ráð | Stig |
|---|---|---|
| færri en 20 rammar | Getting a feel for the picture… | ok |
| flatt | Nothing to measure — point the camera at the level, not at the sky. | stop |
| dimmt | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| óskýrt | Blurred — slow down. | warn |
| færri en helmingur ramma rakinn | Losing track — slow down and keep more of the level in view. | warn |
| færri en 40% rakinna ramma samrunnir | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| veikir blettir til | N thin spots — the map marks them. | ok |
| annars | Good — keep going. | ok |

Stigið litar ráð yfirlagsins (grænt / gult / rautt). **Sharpness** stika yfirlagsins
er skerpa rammans miðað við miðgildið. (Kóðinn hefur líka „Blurred, and the camera is
not moving. Check the capture.“ fyrir kyrrstæða myndavél; skönnunin tilkynnir alltaf að myndavélin
hreyfist, svo það birtist ekki.)
