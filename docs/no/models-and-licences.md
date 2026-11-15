---
title: Modeller og lisenser
nav_order: 7
lang: "no"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modeller og lisenser {#models-and-licences}

Alt som er skrevet for dette repositoriet står under **MIT-lisensen**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Det MIT ikke kan
dekke, er det verktøyene kjører med: pakkene de importerer, modellene rekonstruksjonen bruker, og
spillene de leser. Hele oversikten, med kilder, er
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md). Lisensene ble
lest av pakkemetadata og modellkort i september 2026. Der en komponents vilkår er endret siden da,
gjelder kilden, ikke denne siden. Ingenting her er juridisk rådgivning.

## Dybdemodellen - den som avgjør kommersiell bruk {#the-depth-model-the-one-that-decides-commercial-use}

Depth Anything V2 har **ikke lik lisens for alle størrelser**, og en rekonstruksjon arver lisensen
til modellen som laget den:

| Modell | Lisens | Kommersiell bruk | Brukes av |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **tillatt** | standarden: skannerens konverterte modell (`tools/export_onnx.py` velger den som standard, og knappen "Set up the depth model" i vinduet bygger alltid den), og dybden i den frakoblede banen (fusjon). VGGT gir posisjonene |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | kun ikke-kommersielt | bare hvis du konverterer den selv (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | kun ikke-kommersielt | bare hvis du konverterer den selv (`--size large`) |

Base og Large gir bedre dybde. Det er tillatt å konvertere dem. Men det gjør modellfilen, og hver
rekonstruksjon laget med den, ikke-kommersiell. Det er en beslutning for den som kjører den, ikke en
standard som arves. Skanneren velger blant filene `models/depth-*.onnx` **etter lisens, ikke etter
navn**: `depth-small-*` når en finnes, deretter Base, deretter Large (`choose_model` i
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Vinduet sier hvilken fil det tok, lisensen, og eventuelle andre modellfiler det fant og ikke brukte.
For å skanne med Base, flytt Small-filen ut av `models/`.

## VGGT - kun frakoblet rekonstruksjon {#vggt-offline-reconstruction-only}

| Modell | Lisens | Tilgang |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - kun ikke-kommersiell**; rekonstruksjoner laget med den arver dette | offentlig; standarden |
| `facebook/VGGT-1B-Commercial` | egen lisens; sjekk vilkårene du fikk | begrenset: tilgang må be om fra Meta og gis per konto. Uten den feiler nedlastingen. Velges med `reconstruct --model vggt-1b-commercial` |

VGGT brukes bare av `python -m heat3d_capture reconstruct`. Den live skanneren laster den aldri.
Kommandoen skriver ut lisenslinjen før den starter. Rekonstruksjon fra video er den delen av
prosjektet en spiller faktisk kjører, og ikke-kommersielle vilkår passer til det. For kommersielt
arbeid er en motoreksport eller spillfilseksportøren veien, og begge er uansett eksakte.

## Lokalisere rammer - `locate` {#locating-frames-locate}

| Modell | Lisens | Rolle |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | finner bildene som viser samme sted |
| ALIKED `aliked-n16` | BSD-3-Clause | nøkkelpunkter og deskriptorer |
| LightGlue (ALIKED-varianten) | Apache-2.0 | matcher dem |

Alle tre tillater kommersiell bruk, og hentes første gang de brukes. SuperPoint, den vanlige
partneren til LightGlue, brukes ikke: vektene er ikke-kommersielle. Se
[Lokalisere rammer i et nivå](locate.md).

## Python-pakker {#python-packages}

| Pakke | Lisens | Rolle |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | regning, glatting, marching cubes |
| opencv-python | Apache-2.0 | video, egenskaper, optisk flyt |
| onnxruntime, onnxruntime-directml | MIT | dybdeinferens |
| windows-capture | MIT | direkte opptak gjennom Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | vinduet |
| pytest | MIT | kun utvikling |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | engangskonvertering av modeller; den frakoblede banen |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | den frakoblede banen (`requirements-offline.txt`) |
| vggt | Metas "VGGT License" (avtale om forskningsmateriale med en retningslinje for akseptabel bruk) | den frakoblede banen; installeres fra GitHub med `--no-deps` |
| moderngl, glcontext | MIT | `locate`: tegning av nivået offskjerm (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: nøkkelpunkter og matching |

**PySide6 har vilkår.** LGPL-3.0 tillater proprietær og kommersiell bruk, forutsatt at Qt forblir et
*utskiftbart* bibliotek. Her brukes det som en vanlig dynamisk lenket import, og det oppfyller kravet.
Lisensmerknaden må følge med ved enhver distribusjon. Å pakke verktøyet i én kjørbar fil ville kreve
at Qt fortsatt kan byttes ut.

Lisensen til pakken `vggt` ble lest fra `LICENSE.txt` og står i `LICENSES.md`. Den dekker koden, og er
atskilt fra vektenes CC-BY-NC-4.0.

## Spillene {#the-games}

Telemetri kommer bare fra grensesnitt spillene selv publiserer. Bilder kommer fra skjermen. Se
[Reglene](rules.md). Hva en bruker peker verktøyene mot, er fortsatt underlagt lisensen og
sluttbrukeravtalen for det spillet. Den plikten ligger hos den som kjører verktøyet.
