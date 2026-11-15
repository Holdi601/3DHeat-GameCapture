---
title: Modellen en licenties
nav_order: 7
lang: "nl"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modellen en licenties {#models-and-licences}

Alles wat voor deze repository is geschreven valt onder de **MIT-licentie** ([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Wat MIT niet kan dekken, is waarmee de tools draaien: de pakketten die ze importeren, de modellen die de reconstructie gebruikt, en de games die ze lezen. Het volledige overzicht, met bronnen, staat in [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); de licenties zijn in september 2026 afgelezen uit pakketmetadata en modelkaarten. Waar de voorwaarden van een onderdeel sindsdien zijn veranderd, telt de bron, niet deze pagina. Niets hierin is juridisch advies.

## Het dieptemodel - het model dat over commercieel gebruik beslist {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 heeft **niet voor alle formaten dezelfde licentie**, en een reconstructie erft de licentie van het model dat ze heeft gemaakt:

| Model | Licentie | Commercieel gebruik | Gebruikt door |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **toegestaan** | de standaard: het geconverteerde model van de scanner (`tools/export_onnx.py` kiest het standaard, en de knop "Set up the depth model" in het venster bouwt het altijd), en de diepte van het offline-pad (fusie); VGGT levert de posities |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | alleen niet-commercieel | alleen als je het zelf converteert (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | alleen niet-commercieel | alleen als je het zelf converteert (`--size large`) |

Base en Large geven betere diepte. Ze converteren mag; dan wordt dat modelbestand, en elke reconstructie die ermee is gemaakt, niet-commercieel. Dat is een beslissing voor wie het draait, geen standaard om over te nemen. De scanner kiest tussen de `models/depth-*.onnx`-bestanden **op licentie, niet op naam**: `depth-small-*` wanneer er een is, dan Base, dan Large (`choose_model` in [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). Het venster noemt het bestand dat het heeft gekozen, de licentie ervan, en alle andere modelbestanden die het vond en niet gebruikte; om met Base te scannen verplaats je het Small-bestand uit `models/`.

## VGGT - alleen offline reconstructie {#vggt---offline-reconstruction-only}

| Model | Licentie | Beschikbaarheid |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - alleen niet-commercieel**; reconstructies die ermee zijn gemaakt erven dat | openbaar; de standaard |
| `facebook/VGGT-1B-Commercial` | apart gelicentieerd; controleer de voorwaarden die je hebt gekregen | afgeschermd: toegang wordt bij Meta aangevraagd en per account verleend; zonder toegang mislukt het downloaden. Kies je met `reconstruct --model vggt-1b-commercial` |

VGGT wordt alleen door `python -m heat3d_capture reconstruct` gebruikt; de live scanner laadt het nooit. De opdracht drukt de licentieregel af voordat hij begint. Reconstructie uit video is het deel van dit project dat een speler zou draaien, en niet-commerciële voorwaarden passen daarbij; voor commercieel werk is een engine-export of de game-bestandsexporter de route, en beide zijn toch al exact.

## Frames vinden - `locate` {#locating-frames---locate}

| Model | Licentie | Rol |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | vindt de renders die dezelfde plek tonen |
| ALIKED `aliked-n16` | BSD-3-Clause | keypoints en descriptors |
| LightGlue (ALIKED-variant) | Apache-2.0 | koppelt ze |

Alle drie staan commercieel gebruik toe en worden bij het eerste gebruik opgehaald. SuperPoint, de gewone partner van LightGlue, wordt niet gebruikt: de gewichten ervan zijn niet-commercieel. Zie [Frames in een level vinden](locate.md).

## Python-pakketten {#python-packages}

| Pakket | Licentie | Rol |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | rekenwerk, gladstrijken, marching cubes |
| opencv-python | Apache-2.0 | video, kenmerken, optische stroming |
| onnxruntime, onnxruntime-directml | MIT | diepte-inferentie |
| windows-capture | MIT | live opnames via Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | het venster |
| pytest | MIT | alleen voor ontwikkeling |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | eenmalige modelconversie; het offline-pad |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | het offline-pad (`requirements-offline.txt`) |
| vggt | Meta's "VGGT License" (onderzoeksmateriaalovereenkomst met een gebruiksbeleid) | het offline-pad; geïnstalleerd vanaf GitHub met `--no-deps` |
| moderngl, glcontext | MIT | `locate`: het level offscreen renderen (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: keypoints en matching |

**PySide6 heeft voorwaarden.** LGPL-3.0 staat gesloten en commercieel gebruik toe, mits Qt een *vervangbare* bibliotheek blijft. Het wordt hier gebruikt als een gewone, dynamisch gelinkte import, wat daaraan voldoet, en de licentievermelding ervan moet met elke distributie meegaan. Het hele programma in één uitvoerbaar bestand bundelen zou Qt vervangbaar moeten houden.

De eigen licentie van het pakket `vggt` is afgelezen uit het bestand `LICENSE.txt` en staat in `LICENSES.md`; die dekt de code, los van de CC-BY-NC-4.0 van de gewichten.

## De games {#the-games}

Telemetrie komt alleen uit interfaces die de games publiceren; frames komen van het scherm. Zie [De regels](rules.md). Waar een gebruiker de tools op richt, blijft onderworpen aan de licentie en EULA van dat spel, en die verplichting ligt bij wie de tool draait.
