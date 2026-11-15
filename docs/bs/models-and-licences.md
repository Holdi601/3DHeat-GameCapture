---
title: "Modeli i licence"
nav_order: 7
lang: "bs"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modeli i licence {#models-and-licences}

Sve što je napisano za ovaj repozitorij je pod **MIT licencom**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). MIT ne može
pokriti ono s čim alati rade: pakete koje uvoze, modele koje rekonstrukcija koristi
i igre koje čitaju. Cjelovit zapis, s izvorima, je
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); njegove
licence očitane su iz metapodataka paketa i kartica modela u septembru 2026. Gdje su se uslovi neke komponente
od tada promijenili, vrijedi izvor, a ne ova stranica. Ništa ovdje nije pravni savjet.

## Model dubine - onaj koji odlučuje o komercijalnoj upotrebi {#the-depth-model-the-one-that-decides-commercial-use}

Depth Anything V2 **nije jednako licenciran u svim veličinama**, a rekonstrukcija nasljeđuje
licencu modela koji ju je napravio:

| Model | Licenca | Komercijalna upotreba | Koristi ga |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **dozvoljena** | zadani: skenerov pretvoreni model (`tools/export_onnx.py` ga uzima kao zadani, a "Set up the depth model" u prozoru uvijek gradi njega) i dubina offline putanje (fuzija); VGGT daje njegove poze |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | samo nekomercijalno | samo ako ga sami pretvorite (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | samo nekomercijalno | samo ako ga sami pretvorite (`--size large`) |

Base i Large daju bolju dubinu. Njihovo pretvaranje je dozvoljeno; ono tu datoteku modela i
svaku rekonstrukciju napravljenu s njom čini nekomercijalnom. To je odluka onoga ko to pokreće, a ne
zadana postavka koja se nasljeđuje. Skener bira između datoteka `models/depth-*.onnx` **po licenci, ne po
imenu**: `depth-small-*` kad god postoji, zatim Base, pa Large (`choose_model` u
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Prozor navodi datoteku koju je uzeo, njenu licencu i sve druge datoteke modela koje je našao i nije
koristio; da skenirate s Base, premjestite Small datoteku iz `models/`.

## VGGT - samo offline rekonstrukcija {#vggt-offline-reconstruction-only}

| Model | Licenca | Dostupnost |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - samo nekomercijalno**; rekonstrukcije napravljene s njim to nasljeđuju | javan; zadani |
| `facebook/VGGT-1B-Commercial` | zasebno licenciran; provjerite uslove koji su vam odobreni | zaključan: pristup se traži od Mete i odobrava po nalogu; bez njega preuzimanje ne uspijeva. Bira se sa `reconstruct --model vggt-1b-commercial` |

VGGT koristi samo `python -m heat3d_capture reconstruct`; skener uživo ga nikad ne učitava. Komanda
ispisuje liniju o licenci prije početka. Rekonstrukcija iz videa je dio ovog
projekta koji bi igrač pokretao, a nekomercijalni uslovi tome odgovaraju; za komercijalni rad put je
izvoz iz engine-a ili izvoznik datoteka igre, a oba su ionako tačni.

## Lociranje kadrova - `locate` {#locating-frames-locate}

| Model | Licenca | Uloga |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | nalazi rendere koji prikazuju isto mjesto |
| ALIKED `aliked-n16` | BSD-3-Clause | ključne tačke i deskriptori |
| LightGlue (ALIKED varijanta) | Apache-2.0 | uparuje ih |

Sva tri dozvoljavaju komercijalnu upotrebu i preuzimaju se pri prvom korištenju. SuperPoint, uobičajeni
partner LightGlue-a, nije u upotrebi: njegove težine su nekomercijalne. Pogledajte [Lociranje kadrova u nivou](locate.md).

## Python paketi {#python-packages}

| Paket | Licenca | Uloga |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, zaglađivanje, marching cubes |
| opencv-python | Apache-2.0 | video, karakteristike, optički tok |
| onnxruntime, onnxruntime-directml | MIT | zaključivanje dubine |
| windows-capture | MIT | snimanje uživo kroz Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | prozor |
| pytest | MIT | samo za razvoj |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | jednokratno pretvaranje modela; offline putanja |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | offline putanja (`requirements-offline.txt`) |
| vggt | Metina "VGGT License" (ugovor o istraživačkim materijalima s politikom prihvatljive upotrebe) | offline putanja; instalira se s GitHuba sa `--no-deps` |
| moderngl, glcontext | MIT | `locate`: renderiranje nivoa van ekrana (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: ključne tačke i uparivanje |

**PySide6 ima uslove.** LGPL-3.0 dozvoljava vlasničku i komercijalnu upotrebu pod uslovom da Qt ostane
*zamjenjiva* biblioteka. Ovdje se koristi kao običan dinamički povezan uvoz, što to
zadovoljava, a obavijest o njegovoj licenci mora ići uz svaku distribuciju. Pakiranje alata u jedan
izvršni datoteka moralo bi zadržati Qt zamjenjivim.

Licenca samog paketa `vggt` očitana je iz njegovog `LICENSE.txt` i zabilježena u `LICENSES.md`;
pokriva kod, odvojeno od CC-BY-NC-4.0 licence težina.

## Igre {#the-games}

Telemetrija dolazi samo iz sučelja koja igre objavljuju; kadrovi dolaze sa ekrana. Pogledajte
[Pravila](rules.md). Ono na šta korisnik usmjeri alate i dalje podliježe licenci i EULA-i te
igre, a ta obaveza je na onome ko pokreće alat.
