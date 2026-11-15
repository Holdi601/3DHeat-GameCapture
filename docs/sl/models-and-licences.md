---
title: Modeli in licence
nav_order: 7
lang: "sl"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modeli in licence {#models-and-licences}

Vse, kar je napisano za ta repozitorij, je pod **licenco MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Česar MIT ne more
pokriti, je to, s čim orodja delujejo: paketi, ki jih uvažajo, modeli, ki jih uporablja
rekonstrukcija, in igre, ki jih berejo. Celoten zapis z viri je v
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); njegove
licence so bile prebrane iz metapodatkov paketov in kartic modelov septembra 2026. Kjer so se pogoji
komponente od takrat spremenili, šteje vir, ne ta stran. Tu ni pravnega nasveta.

## Model globine – tisti, ki odloča o komercialni uporabi {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **ni licenciran enako pri vseh velikostih**, rekonstrukcija pa podeduje licenco
modela, ki jo je naredil:

| Model | Licenca | Komercialna uporaba | Uporablja ga |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **dovoljena** | privzeti: pretvorjeni model skenerja (`tools/export_onnx.py` privzeto uporabi ta model, gumb okna „Set up the depth model“ pa ga vedno sestavi) in globina poti brez povezave (zlivanje); VGGT zagotovi njegove položaje |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | samo nekomercialno | samo če ga pretvorite sami (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | samo nekomercialno | samo če ga pretvorite sami (`--size large`) |

Base in Large dajeta boljšo globino. Pretvorba je dovoljena; ta datoteka modela in vsaka
rekonstrukcija, narejena z njo, postane nekomercialna. To je odločitev tistega, ki ga zažene, ne
privzeta vrednost, ki bi jo bilo treba podedovati. Skener izbira med datotekami `models/depth-*.onnx`
**po licenci, ne po imenu**: `depth-small-*`, kadar je ta na voljo, nato Base, nato Large
(`choose_model` v
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Okno navede datoteko, ki jo je vzelo, njeno licenco in vse druge datoteke modelov, ki jih je našlo in
ne uporabilo; če želite skenirati z Base, premaknite datoteko Small iz `models/`.

## VGGT – samo rekonstrukcija brez povezave {#vggt---offline-reconstruction-only}

| Model | Licenca | Dostopnost |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - samo nekomercialno**; rekonstrukcije, narejene z njim, to podedujejo | javno; privzeti |
| `facebook/VGGT-1B-Commercial` | ločeno licencirano; preverite pogoje, ki ste jih dobili | zaprto: dostop se zahteva pri Meti in odobri za vsak račun; brez njega prenos ne uspe. Izbere se z `reconstruct --model vggt-1b-commercial` |

VGGT uporablja samo `python -m heat3d_capture reconstruct`; skener v živo ga nikoli ne naloži. Ukaz
pred začetkom izpiše vrstico z licenco. Rekonstrukcija iz videa je del tega projekta, ki ga bo
igralec zagnal, in nekomercialni pogoji se temu prilegajo; za komercialno delo je pot izvoz iz
pogona ali izvoznik datotek igre, obe pa sta tako ali drugače natančni.

## Iskanje okvirjev – `locate` {#locating-frames---locate}

| Model | Licenca | Vloga |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | poišče upodobitve, ki prikazujejo isti kraj |
| ALIKED `aliked-n16` | BSD-3-Clause | ključne točke in opisniki |
| LightGlue (ALIKED variant) | Apache-2.0 | jih ujema |

Vsi trije dovoljujejo komercialno uporabo in se prenesejo ob prvi uporabi. SuperPoint, običajni
partner LightGlue, se ne uporablja: njegove uteži so nekomercialne. Glejte
[Iskanje okvirjev v nivoju](locate.md).

## Paketi Python {#python-packages}

| Paket | Licenca | Vloga |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, glajenje, marching cubes |
| opencv-python | Apache-2.0 | video, značilnosti, optični tok |
| onnxruntime, onnxruntime-directml | MIT | sklepanje globine |
| windows-capture | MIT | zajem v živo prek Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | okno |
| pytest | MIT | samo za razvoj |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | enkratna pretvorba modela; pot brez povezave |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | pot brez povezave (`requirements-offline.txt`) |
| vggt | Metina „VGGT License“ (sporazum o raziskovalnih gradivih s politiko sprejemljive uporabe) | pot brez povezave; namesti se z GitHuba z `--no-deps` |
| moderngl, glcontext | MIT | `locate`: upodabljanje nivoja zunaj zaslona (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: ključne točke in ujemanje |

**PySide6 ima pogoje.** LGPL-3.0 dovoljuje lastniško in komercialno uporabo, če Qt ostane
*zamenljiva* knjižnica. Tu se uporablja kot navaden dinamično povezan uvoz, kar to izpolnjuje, njegovo
obvestilo o licenci pa mora spremljati vsako distribucijo. Če bi orodje zapakirali v eno samo
izvedljivo datoteko, bi moral Qt ostati zamenljiv.

Lastna licenca paketa `vggt` je bila prebrana iz njegove datoteke `LICENSE.txt` in je zapisana v
`LICENSES.md`; zajema kodo, ločeno od CC-BY-NC-4.0 uteži.

## Igre {#the-games}

Telemetrija prihaja samo iz vmesnikov, ki jih igre objavljajo; okvirji prihajajo z zaslona. Glejte
[Pravila](rules.md). Za to, kamor uporabnik usmeri orodja, veljata licenca in EULA te igre, ta obveznost
pa je na strani tistega, ki orodje zažene.
