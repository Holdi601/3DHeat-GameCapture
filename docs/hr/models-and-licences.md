---
title: Modeli i licence
nav_order: 7
lang: "hr"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modeli i licence {#models-and-licences}

Sve napisano za ovaj repozitorij je pod **MIT licencom**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Što MIT ne može
pokriti jest ono s čim alati rade: paketi koje uvoze, modeli koje rekonstrukcija koristi, i igre
koje čitaju. Potpuni zapis, s izvorima, je
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); njegove licence
su pročitane s metapodataka paketa i kartica modela u rujnu 2026. Ako su se uvjeti komponente
kasnije promijenili, vrijedi izvor, a ne ova stranica. Ništa ovdje nije pravni savjet.

## Model dubine - onaj koji odlučuje o komercijalnoj upotrebi {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **nije licenciran jednako za sve svoje veličine**, a rekonstrukcija nasljeđuje
licencu modela koji ju je napravio:

| Model | Licenca | Komercijalna upotreba | Koristi ga |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **dopuštena** | zadani: pretvoreni model skenera (`tools/export_onnx.py` zadano ga koristi, a gumb prozora "Set up the depth model" uvijek gradi njega), i dubina izvanmrežnog puta (spajanje); VGGT daje njegove položaje |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | samo nekomercijalna | samo ako ga sami pretvorite (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | samo nekomercijalna | samo ako ga sami pretvorite (`--size large`) |

Base i Large daju bolju dubinu. Pretvaranje im je dopušteno; to stvara datoteku tog modela, a svaka
rekonstrukcija napravljena njime postaje nekomercijalna. To je odluka onoga tko to pokreće, a ne
zadano nasljeđivanje. Skener bira među datotekama `models/depth-*.onnx` **po licenci, a ne po
nazivu**: `depth-small-*` kad god postoji, zatim Base, pa Large (`choose_model` u
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Prozor navodi datoteku koju je uzeo, njezinu licencu i sve druge datoteke modela koje je pronašao, a
nije ih koristio; za skeniranje s Base-om premjestite datoteku Small iz `models/`.

## VGGT - samo izvanmrežna rekonstrukcija {#vggt---offline-reconstruction-only}

| Model | Licenca | Dostupnost |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - samo nekomercijalna**; rekonstrukcije napravljene njime to nasljeđuju | javno; zadani |
| `facebook/VGGT-1B-Commercial` | zasebno licenciran; provjerite uvjete koje ste dobili | ograničen: pristup se traži od Metae i dodjeljuje po računu; bez njega preuzimanje ne uspije. Bira se s `reconstruct --model vggt-1b-commercial` |

VGGT koristi samo `python -m heat3d_capture reconstruct`; živi skener ga nikad ne učitava. Naredba
ispiše liniju licence prije početka. Rekonstrukcija iz videa je dio ovog projekta koji bi igrač
pokrenuo, a nekomercijalni uvjeti tome odgovaraju; za komercijalni rad put je izvoz iz motora ili
izvoznik datoteka igre, a oba su svakako točna.

## Lociranje kadrova - `locate` {#locating-frames---locate}

| Model | Licenca | Uloga |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | pronalazi prikaze koji pokazuju isto mjesto |
| ALIKED `aliked-n16` | BSD-3-Clause | ključne točke i deskriptori |
| LightGlue (varijanta ALIKED) | Apache-2.0 | uparuje ih |

Sva tri dopuštaju komercijalnu upotrebu i preuzimaju se pri prvoj uporabi. SuperPoint, uobičajeni
partner LightGluea, se ne koristi: njegove težine su nekomercijalne. Vidi
[Lociranje kadrova u razini](locate.md).

## Python paketi {#python-packages}

| Paket | Licenca | Uloga |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, zaglađivanje, marching cubes |
| opencv-python | Apache-2.0 | video, značajke, optički tok |
| onnxruntime, onnxruntime-directml | MIT | zaključivanje dubine |
| windows-capture | MIT | snimanje uživo kroz Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | prozor |
| pytest | MIT | samo za razvoj |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | jednokratna pretvorba modela; izvanmrežni put |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | izvanmrežni put (`requirements-offline.txt`) |
| vggt | Metaina "VGGT License" (sporazum o istraživačkim materijalima s pravilima prihvatljive upotrebe) | izvanmrežni put; instalira se s GitHuba s `--no-deps` |
| moderngl, glcontext | MIT | `locate`: iscrtavanje razine izvan zaslona (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: ključne točke i uparivanje |

**PySide6 ima uvjete.** LGPL-3.0 dopušta vlasničku i komercijalnu upotrebu pod uvjetom da Qt ostane
*zamjenjiva* biblioteka. Ovdje se koristi kao običan dinamički povezan uvoz, što to zadovoljava, a
obavijest o licenci mora pratiti svaku distribuciju. Spajanje alata u jednu izvršnu datoteku moralo
bi zadržati Qt zamjenjivim.

Licenca samostalnog paketa `vggt` pročitana je iz njegove datoteke `LICENSE.txt` i zapisana je u
`LICENSES.md`; pokriva kod, odvojeno od težina pod CC-BY-NC-4.0.

## Igre {#the-games}

Telemetrija dolazi samo iz sučelja koja igre objavljuju; kadrovi dolaze s ekrana. Vidi
[Pravila](rules.md). Ništa iz igre ne isporučuje se niti dalje distribuira, a ono što alati izrade ostaje na računalu korisnika. 3DHeat GameCapture nije povezan ni s jednim izdavačem igara niti ga on podržava; nazivi igara i povezani žigovi pripadaju njihovim vlasnicima.
