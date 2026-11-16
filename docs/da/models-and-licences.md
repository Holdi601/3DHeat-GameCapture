---
title: Modeller og licenser
nav_order: 7
lang: "da"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modeller og licenser {#models-and-licences}

Alt, der er skrevet til dette repository, er under **MIT-licensen**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Det MIT ikke kan
dække, er det, værktøjerne kører med: de pakker de importerer, de modeller rekonstruktionen bruger, og
de spil de læser. Den fulde fortegnelse, med kilder, er
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); dens licenser er
læst af pakkemetadata og modelkort i september 2026. Hvis en komponents vilkår er ændret siden, gælder
kilden, ikke denne side. Intet her er juridisk rådgivning.

## Dybdemodellen - den, der afgør kommerciel brug {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 er **ikke licenseret ens på tværs af sine størrelser**, og en rekonstruktion arver
licensen fra den model, der lavede den:

| Model | Licens | Kommerciel brug | Bruges af |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **tilladt** | standarden: scannerens konverterede model (`tools/export_onnx.py` vælger den som standard, og vinduets "Set up the depth model" bygger altid den), og den offline-stis dybde (fusion); VGGT leverer dens positioner |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | kun ikke-kommerciel | kun hvis du selv konverterer den (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | kun ikke-kommerciel | kun hvis du selv konverterer den (`--size large`) |

Base og Large giver bedre dybde. At konvertere dem er tilladt; det gør den modelfil og hver
rekonstruktion lavet med den ikke-kommerciel. Det er en beslutning for den, der kører den, ikke en
standard at arve. Scanneren vælger blandt filerne `models/depth-*.onnx` **efter licens, ikke efter
navn**: `depth-small-*`, når der findes én, derefter Base, derefter Large (`choose_model` i
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Vinduet nævner den fil, det tog, dens licens og eventuelle andre modelfiler, det fandt og ikke brugte;
for at scanne med Base skal du flytte Small-filen ud af `models/`.

## VGGT - kun offline-rekonstruktion {#vggt---offline-reconstruction-only}

| Model | Licens | Tilgængelighed |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - kun ikke-kommerciel**; rekonstruktioner lavet med den arver det | offentlig; standarden |
| `facebook/VGGT-1B-Commercial` | særskilt licenseret; tjek de vilkår, du har fået | afskærmet: adgang anmodes hos Meta og gives pr. konto; uden den fejler downloaden. Vælges med `reconstruct --model vggt-1b-commercial` |

VGGT bruges kun af `python -m heat3d_capture reconstruct`; den live-scanner indlæser den aldrig.
Kommandoen skriver licenslinjen, før den starter. Rekonstruktion fra video er den del af projektet, en
spiller ville køre, og ikke-kommercielle vilkår passer til det; til kommercielt arbejde er en motoreksport
eller spilfilseksportøren vejen, og begge er alligevel nøjagtige.

## Find billeder - `locate` {#locating-frames---locate}

| Model | Licens | Rolle |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | finder renderingerne, der viser det samme sted |
| ALIKED `aliked-n16` | BSD-3-Clause | nøglepunkter og deskriptorer |
| LightGlue (ALIKED-variant) | Apache-2.0 | matcher dem |

Alle tre tillader kommerciel brug og hentes ved første brug. SuperPoint, LightGlues sædvanlige
partner, bruges ikke: dens vægte er ikke-kommercielle. Se [Find billeder i en bane](locate.md).

## Python-pakker {#python-packages}

| Pakke | Licens | Rolle |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | regning, udglatning, marching cubes |
| opencv-python | Apache-2.0 | video, features, optisk flow |
| onnxruntime, onnxruntime-directml | MIT | dybdeinference |
| windows-capture | MIT | live-optagelse gennem Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | vinduet |
| pytest | MIT | kun udvikling |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | engangskonvertering af modeller; den offline-sti |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | den offline-sti (`requirements-offline.txt`) |
| vggt | Metas "VGGT License" (aftale om forskningsmateriale med en brugspolitik) | den offline-sti; installeret fra GitHub med `--no-deps` |
| moderngl, glcontext | MIT | `locate`: rendering af banen offscreen (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: nøglepunkter og matching |

**PySide6 har betingelser.** LGPL-3.0 tillader proprietær og kommerciel brug, forudsat at Qt forbliver
et *udskifteligt* bibliotek. Det bruges her som en almindelig dynamisk linket import, hvilket opfylder
det, og dets licensmeddelelse skal følge med enhver udgivelse. Hvis værktøjet blev pakket i en enkelt
eksekverbar fil, skulle Qt forblive udskifteligt.

Pakken `vggt`s egen licens er læst af dens `LICENSE.txt` og er registreret i `LICENSES.md`; den dækker
koden, adskilt fra vægtenes CC-BY-NC-4.0.

## Spillene {#the-games}

Telemetri kommer kun fra grænseflader, spillene selv udgiver; billeder kommer fra skærmen. Se
[Reglerne](rules.md). Intet fra et spil leveres med eller videredistribueres, og det, værktøjerne laver, bliver på brugerens maskine. 3DHeat GameCapture er ikke tilknyttet eller godkendt af nogen spiludgiver; spilnavne og tilhørende varemærker tilhører deres ejere.
