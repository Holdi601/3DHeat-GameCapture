---
title: Modeller och licenser
nav_order: 7
lang: "sv"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modeller och licenser {#models-and-licences}

Allt skrivet för det här förrådet är under **MIT-licensen**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Det MIT inte
kan täcka är det verktygen körs med: de paket de importerar, modellerna som rekonstruktionen
använder, och spelen de läser. Hela underlaget, med källor, finns i
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); dess
licenser lästes av från paketmetadata och modellkort i september 2026. Där en komponents villkor
ändrats sedan dess gäller källan, inte den här sidan. Inget här är juridisk rådgivning.

## Djupmodellen - den som avgör kommersiell användning {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 är **inte licensierad lika för alla sina storlekar**, och en rekonstruktion ärver
licensen för modellen som gjorde den:

| Modell | Licens | Kommersiell användning | Används av |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **tillåten** | standard: skannerns konverterade modell (`tools/export_onnx.py` väljer den som standard, och fönstrets "Set up the depth model" bygger alltid den), och djupet i offline-vägen (fusion); VGGT levererar dess poser |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | endast icke-kommersiell | bara om du konverterar den själv (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | endast icke-kommersiell | bara om du konverterar den själv (`--size large`) |

Base och Large ger bättre djup. Att konvertera dem är tillåtet; det gör just den modellfilen, och
varje rekonstruktion gjord med den, icke-kommersiell. Det är ett beslut för den som kör den, inte
ett standardvärde att ärva. Skannern väljer bland filerna `models/depth-*.onnx` **efter licens, inte
efter namn**: `depth-small-*` när det finns en, sedan Base, sedan Large (`choose_model` i
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Fönstret anger vilken fil det tog, dess licens, och andra modellfiler det hittade men inte använde;
för att skanna med Base, flytta Small-filen ur `models/`.

## VGGT - endast offline-rekonstruktion {#vggt---offline-reconstruction-only}

| Modell | Licens | Tillgänglighet |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - endast icke-kommersiell**; rekonstruktioner gjorda med den ärver det | offentlig; standard |
| `facebook/VGGT-1B-Commercial` | licensierad separat; kontrollera villkoren du fått | spärrad: åtkomst begärs från Meta och beviljas per konto; utan den misslyckas nedladdningen. Väljs med `reconstruct --model vggt-1b-commercial` |

VGGT används bara av `python -m heat3d_capture reconstruct`; den live-skannern laddar den aldrig.
Kommandot skriver ut licensraden innan det startar. Rekonstruktion från video är den del av projektet
en spelare skulle köra, och icke-kommersiella villkor passar det; för kommersiellt arbete är en
motorexport eller spelfilsexportören vägen, och båda är ändå exakta.

## Lokalisera bildrutor - `locate` {#locating-frames---locate}

| Modell | Licens | Roll |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | hittar renderingarna som visar samma plats |
| ALIKED `aliked-n16` | BSD-3-Clause | nyckelpunkter och deskriptorer |
| LightGlue (ALIKED-varianten) | Apache-2.0 | matchar dem |

Alla tre tillåter kommersiell användning, och hämtas vid första användning. SuperPoint, LightGlues
vanliga partner, används inte: dess vikter är icke-kommersiella. Se
[Lokalisera bildrutor i en nivå](locate.md).

## Python-paket {#python-packages}

| Paket | Licens | Roll |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetik, utjämning, marching cubes |
| opencv-python | Apache-2.0 | video, särdrag, optiskt flöde |
| onnxruntime, onnxruntime-directml | MIT | djupinferens |
| windows-capture | MIT | live-inspelning via Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | fönstret |
| pytest | MIT | endast utveckling |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | engångskonvertering av modeller; offline-vägen |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | offline-vägen (`requirements-offline.txt`) |
| vggt | Metas "VGGT License" (avtal för forskningsmaterial med en policy för godtagbar användning) | offline-vägen; installeras från GitHub med `--no-deps` |
| moderngl, glcontext | MIT | `locate`: rendering av nivån offscreen (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: nyckelpunkter och matchning |

**PySide6 har villkor.** LGPL-3.0 tillåter proprietär och kommersiell användning under förutsättning
att Qt förblir ett *utbytbart* bibliotek. Här används det som en vanlig dynamiskt länkad import, vilket
uppfyller det, och dess licensnotis måste följa med varje distribution. Att paketera verktyget i en
enda körbar fil skulle kräva att Qt hålls utbytbart.

Paketet `vggt` egen licens lästes av från dess `LICENSE.txt` och finns i `LICENSES.md`; den gäller
koden, separat från vikternas CC-BY-NC-4.0.

## Spelen {#the-games}

Telemetri kommer bara från gränssnitt som spelen publicerar; bilder kommer från skärmen. Se
[Reglerna](rules.md). Inget från ett spel levereras med eller vidaredistribueras, och det verktygen tar fram stannar på användarens dator. 3DHeat GameCapture är inte knutet till eller godkänt av någon spelutgivare; spelnamn och tillhörande varumärken tillhör sina ägare.
