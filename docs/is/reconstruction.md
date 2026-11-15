---
title: "Endurbygging borðs"
nav_order: 6
lang: "is"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Endurbygging borðs úr leik {#level-reconstruction-from-gameplay}

Gakktu hægt um borð, eða aktu braut, og skanninn breytir því sem skjárinn sýndi í
`.glb` sem 3DHeat-skoðarinn hleður sem samhengi undir mælingagögnunum - sami skráarsamningur
og Unreal-útflytjandinn skrifar. Þetta er fyrir tilvikið þar sem enginn flutti kortið út og skrár leiksins
er ekki hægt að lesa; vélarútflutningur eða leikjaskráaútflutningur er nákvæmur, þetta er mat.

## Ferlið {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Þrep | Bein skönnun (`heat3d_capture.ui`) | Án nettengingar (`reconstruct`) | Síða |
|---|---|---|---|
| Rammar | skjár, gluggi eða myndband, minnkað í lengstu hlið forstillingarinnar | myndband, sýnatekið tvisvar (lausnaráætlun og samrunabil) | [Upptaka](reconstruction-capture.md) |
| Lykilrammar | haldið eftir því hve mikið myndin breyttist, þröskuldur lagaður að upptökunni | á hverjum `--fuse-interval` sekúndum | [Upptaka](reconstruction-capture.md#keyframes) |
| Grímur | breytingabyggð `ScreenMask`, síðan flæðisbyggð `FlowMask` eftir 40 lykilramma | `FlowMask` lærð af fjórum keyrslum myndbandsins; ekki beitt á lausnarann | [Upptaka](reconstruction-capture.md#what-is-not-the-world) |
| Dýpt | ONNX líkan á besta GPU-bakenda | PyTorch Depth Anything V2 Small | [Dýpt](reconstruction-depth.md) |
| Staða | sjónræn odometry, eða nákvæm Forza mælingagögn | VGGT gluggar saumaðir í eina leið, brúaðir | [Staða](reconstruction-pose.md), [Án nettengingar](reconstruction-offline.md) |
| Kvarði | hæð myndavélar yfir jörðu (1,15 m) einu sinni, eða mælingagögn | eigin einingar lausnarleiðarinnar | [Staða](reconstruction-pose.md#scale) |
| Samruni | vegið setumat (occupancy), gisnir teningar (voxels); þekjunet | hið sama | [Samruni](reconstruction-fusion-and-texture.md) |
| Úttak | `.glb`, hlutar jörð/mannvirki, hnútalitur, sentímetrar | hið sama | [.glb úttakið](glb-output.md) |

Kóði: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - stillingar skönnunar og hraði; `reconstruct.py` - lykilrammar í rúmfræði;
`offline.py` - leiðin án nettengingar), með þrepunum í `capture/`, `depth/`, `pose/`, `fusion/`
og `geometry/`.

## Hvaðan nákvæmnin kemur {#where-accuracy-comes-from}

Einsjónar dýpt (monocular depth) er aðeins rétt upp að óþekktum kvarða - ljósmynd af herbergi og af dúkkuhúsi
er sama myndin. Því er netið látið gera það sem það er gott í (afstætt form, brúnir,
þunn mannvirki), og kvarðinn og ferill myndavélarinnar koma frá einhverju sem þekkir þau:

| Leikur | Ferill myndavélar | Kvarði |
|---|---|---|
| Forza Horizon / Motorsport með mælingagögn á | nákvæmur, úr Data Out, brúaður á upptökutíma hvers ramma | nákvæmur: dýptin er fest með þríhyrningamælingu eiginleika milli tveggja þekktra staða |
| Hvað annað sem er, beint | sjónræn odometry, keðjuð ramma frá ramma | fastur einu sinni út frá áætlaðri hæð myndavélar yfir jörðu |
| Upptaka, án nettengingar | VGGT, leyst yfir skarast glugga | eigin einingar lausnarinnar (ekki metrar) |

Eina talan sem skanninn er látinn fá í stað þess að mæla hana er **láréttur sjónvídd** leiksins (field of
view; 90 gráður sjálfgefið í glugganum; kappakstursleikir eru nær 65). Of þröng og borðið
endurbyggist dýpra en það er; of víð og það flattast út.

## Að segja notandanum snemma {#telling-the-user-early}

Skönnun er líkamleg athöfn - einhver gengur um borð í nokkrar mínútur - og dýra
mistökin eru að ljúka göngunni og uppgötva að hún var ónothæf. Því mælir glugginn
dýptarafköst þessarar vélar áður en nokkuð getur byrjað og segir hvernig skönnunin verður
([Keyrsluumhverfi](runtime.md#what-to-expect-from-this-machine)); meðan á skönnun stendur sýnir hann þekjukort
með númeruðum veikum blettum, heilsu rakningar, göngu­hraðastiku, skerpustiku og eina leiðbeiningu í einu, í glugganum og í yfirlagi sem hægt er að smella í gegnum yfir leiknum
([Skönnunarglugginn](reconstruction-scan-ui.md)).

## Mælt á tilbúnum viðmiðum (synthetic ground truth) {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` teiknar 12 x 8 m herbergi (4 m hátt) frá þekktri myndavélarleið, með
greinanlegri (ekki neti) dýpt, og endurbyggir það með 0,2 m teningum. Hún fullyrðir að meira en
90% ramma séu staðsettir, meðalskekkja leiðar sé undir 0,35 m (verst undir 1 m), gengin
vegalengd sé innan 10% frá sannleikanum, herbergið komi út í réttri breidd innan 1,5 m, yfir
75% veggjayfirborðsins liggi innan 0,45 m frá raunverulegum vegg, könnunargönguleið skili greinilega
betri þekju en að ganga beint áfram, og að tilbúið umhverfi án eiginleika sé hafnað frekar en að vera
uppfundið. Greinanleg dýpt einangrar stöðu, kvarða og
samruna frá netinu; hvernig netið stendur sig í raunverulegum leik er sérstök spurning sem engin
tilbúin sena svarar. `tests/test_track_width.py` athugar að hringur ekinn utan miðju á
vegi af þekktri breidd endurbyggi breidd vegarins, ekki aðeins ekna línuna.

## Síður {#pages}

- [Skönnunarglugginn](reconstruction-scan-ui.md) - allir stjórnhlutar, flýtilyklar og þættir yfirlagsins
- [Upptaka, grímur og gæði ramma](reconstruction-capture.md)
- [Dýpt](reconstruction-depth.md)
- [Staða og kvarði myndavélar](reconstruction-pose.md)
- [Samruni, þekja og litur](reconstruction-fusion-and-texture.md)
- [.glb úttakið](glb-output.md)
- [Endurbygging án nettengingar](reconstruction-offline.md)
