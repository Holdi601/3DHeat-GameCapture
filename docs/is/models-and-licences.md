---
title: "Líkön og leyfi"
nav_order: 7
lang: "is"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Líkön og leyfi {#models-and-licences}

Allt sem skrifað er fyrir þessa geymslu er undir **MIT-leyfi**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Það sem MIT getur ekki
náð yfir er það sem verkfærin keyra með: pakkarnir sem þau flytja inn, líkönin sem endurbygging notar
og leikirnir sem þau lesa. Öll skráin, með heimildum, er
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); leyfin í henni
voru lesin úr lýsigögnum pakka og líkanaspjöldum í september 2026. Þar sem skilmálar íhlutar hafa
breyst síðan gildir heimildin, ekki þessi síða. Ekkert hér er lögfræðiráðgjöf.

## Dýptarlíkanið - það sem ræður atvinnunotkun {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 er **ekki með sama leyfi í öllum stærðum**, og endurbygging erfir
leyfi líkansins sem bjó hana til:

| Líkan | Leyfi | Atvinnunotkun | Notað af |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **leyfð** | sjálfgefið: umbreytta líkan skannans (`tools/export_onnx.py` notar það sjálfgefið og „Set up the depth model“ í glugganum smíðar alltaf það), og dýpt leiðarinnar án nettengingar (samruni); VGGT gefur stöðurnar |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | aðeins óviðskiptaleg | aðeins ef þú umbreytir því sjálfur (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | aðeins óviðskiptaleg | aðeins ef þú umbreytir því sjálfur (`--size large`) |

Base og Large gefa betri dýpt. Það er leyfilegt að umbreyta þeim; það gerir þá líkanaskrá, og
sérhverja endurbyggingu gerða með henni, óviðskiptalega. Það er ákvörðun þess sem keyrir það, ekki
sjálfgefið sem erfist. Skanninn velur á milli `models/depth-*.onnx` skránna **eftir leyfi, ekki eftir
heiti**: `depth-small-*` þegar til er slík, síðan Base, síðan Large (`choose_model` í
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Glugginn nefnir skrána sem hann tók, leyfi hennar og allar aðrar líkanaskrár sem hann fann og notaði
ekki; til að skanna með Base skaltu færa Small skrána út úr `models/`.

## VGGT - aðeins endurbygging án nettengingar {#vggt---offline-reconstruction-only}

| Líkan | Leyfi | Aðgengi |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - aðeins óviðskiptaleg notkun**; endurbyggingar gerðar með því erfa það | opinbert; sjálfgefið |
| `facebook/VGGT-1B-Commercial` | sérstaklega með leyfi; kannaðu skilmálana sem þér voru veittir | læst: aðgangs er óskað hjá Meta og hann veittur fyrir hvern reikning; án hans mistekst niðurhalið. Valið með `reconstruct --model vggt-1b-commercial` |

VGGT er aðeins notað af `python -m heat3d_capture reconstruct`; beini skanninn hleður það aldrei. Skipunin
prentar leyfislínuna áður en hún byrjar. Endurbygging úr myndbandi er sá hluti þessa verkefnis sem
spilari myndi keyra, og óviðskiptalegir skilmálar henta því; fyrir atvinnuvinnu er vélarútflutningur eða
leikjaskráaútflytjandinn leiðin, og báðir eru nákvæmir hvort eð er.

## Að staðsetja ramma - `locate` {#locating-frames---locate}

| Líkan | Leyfi | Hlutverk |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | finnur teikningarnar sem sýna sama stað |
| ALIKED `aliked-n16` | BSD-3-Clause | lykilpunktar og lýsingar |
| LightGlue (ALIKED afbrigði) | Apache-2.0 | para þá saman |

Öll þrjú leyfa atvinnunotkun og eru sótt við fyrstu notkun. SuperPoint, venjulegur
förunautur LightGlue, er ekki notað: þyngdir þess eru óviðskiptalegar. Sjá [Að staðsetja ramma í borði](locate.md).

## Python pakkar {#python-packages}

| Pakki | Leyfi | Hlutverk |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | reikningur, sléttun, marching cubes |
| opencv-python | Apache-2.0 | myndband, eiginleikar, optical flow |
| onnxruntime, onnxruntime-directml | MIT | dýptarályktun |
| windows-capture | MIT | bein upptaka í gegnum Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | glugginn |
| pytest | MIT | aðeins þróun |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | einskiptis líkanaumbreyting; leiðin án nettengingar |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | leiðin án nettengingar (`requirements-offline.txt`) |
| vggt | „VGGT License“ Meta (rannsóknarefnissamningur með notkunarstefnu) | leiðin án nettengingar; sett upp frá GitHub með `--no-deps` |
| moderngl, glcontext | MIT | `locate`: teikna borðið utan skjás (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: lykilpunktar og pörun |

**PySide6 hefur skilyrði.** LGPL-3.0 leyfir séreignar- og atvinnunotkun svo framarlega sem Qt er áfram
*útskiptanlegt* safn. Það er notað hér sem venjulegur kvikt tengdur innflutningur, sem uppfyllir
það, og leyfistilkynning þess verður að fylgja allri dreifingu. Ef verkfærið væri pakkað í eina
keyrsluskrá þyrfti að halda Qt útskiptanlegu.

Leyfi `vggt` pakkans sjálfs var lesið úr `LICENSE.txt` hans og er skráð í `LICENSES.md`;
það nær yfir kóðann, aðskilið frá CC-BY-NC-4.0 leyfi þyngdanna.

## Leikirnir {#the-games}

Mælingagögn koma aðeins úr viðmótum sem leikirnir birta; rammar koma af skjánum. Sjá
[Reglurnar](rules.md). Ekkert úr leik fylgir með eða er dreift áfram, og það sem verkfærin búa til verður eftir á vél notandans. 3DHeat GameCapture tengist engum leikjaútgefanda og er ekki samþykkt af neinum þeirra; nöfn leikja og tengd vörumerki tilheyra eigendum sínum.
