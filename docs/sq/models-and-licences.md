---
title: "Modelet dhe licencat"
nav_order: 7
lang: "sq"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modelet dhe licencat {#models-and-licences}

Gjithçka e shkruar për këtë repozitor është nën **licencën MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Ajo që MIT nuk mund ta
mbulojë është ajo me të cilën punojnë mjetet: paketat që importojnë, modelet që përdor rindërtimi dhe
lojërat që lexojnë. Regjistri i plotë, me burimet, është
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); licencat e tij
u lexuan nga metadatat e paketave dhe kartat e modeleve në shtator 2026. Kur kushtet e një përbërësi kanë
ndryshuar që atëherë, vlen burimi, jo kjo faqe. Asgjë këtu nuk është këshillë juridike.

## Modeli i thellësisë - ai që vendos për përdorimin komercial {#the-depth-model-the-one-that-decides-commercial-use}

Depth Anything V2 **nuk është i licencuar njësoj në të gjitha madhësitë**, dhe një rindërtim e trashëgon
licencën e modelit që e bëri:

| Modeli | Licenca | Përdorim komercial | Përdoret nga |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **lejohet** | parazgjedhja: modeli i konvertuar i skanerit (`tools/export_onnx.py` e ka parazgjedhje, dhe "Set up the depth model" e dritares e ndërton gjithmonë), dhe thellësia e rrugës offline (bashkimi); VGGT jep pozat e tij |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | vetëm jokomercial | vetëm nëse e konverton vetë (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | vetëm jokomercial | vetëm nëse e konverton vetë (`--size large`) |

Base dhe Large japin thellësi më të mirë. Konvertimi i tyre lejohet; por e bën atë skedar modeli, dhe
çdo rindërtim të bërë me të, jokomercial. Ky është vendim i atij që e ekzekuton, jo një
parazgjedhje për t'u trashëguar. Skaneri zgjedh mes skedarëve `models/depth-*.onnx` **sipas licencës, jo sipas
emrit**: `depth-small-*` sa herë që ka një, pastaj Base, pastaj Large (`choose_model` te
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Dritarja emërton skedarin që mori, licencën e tij dhe çdo skedar tjetër modeli që gjeti dhe nuk
e përdori; për të skanuar me Base, zhvendose skedarin Small jashtë `models/`.

## VGGT - vetëm rindërtimi offline {#vggt-offline-reconstruction-only}

| Modeli | Licenca | Disponueshmëria |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - vetëm jokomercial**; rindërtimet e bëra me të e trashëgojnë | publik; parazgjedhja |
| `facebook/VGGT-1B-Commercial` | i licencuar veçmas; kontrollo kushtet që të janë dhënë | me hyrje të kufizuar: qasja kërkohet nga Meta dhe jepet për çdo llogari; pa të shkarkimi dështon. Zgjidhet me `reconstruct --model vggt-1b-commercial` |

VGGT përdoret vetëm nga `python -m heat3d_capture reconstruct`; skaneri i drejtpërdrejtë nuk e ngarkon kurrë. Komanda
e printon rreshtin e licencës para se të nisë. Rindërtimi nga video është pjesa e këtij projekti që do ta ekzekutonte një lojtar,
dhe kushtet jokomerciale i përshtaten kësaj; për punë komerciale rruga është një eksport i motorit
ose eksportuesi i skedarëve të lojës, dhe të dyja janë të sakta gjithsesi.

## Gjetja e kuadrove - `locate` {#locating-frames-locate}

| Modeli | Licenca | Roli |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | gjen pamjet që tregojnë të njëjtin vend |
| ALIKED `aliked-n16` | BSD-3-Clause | pikat kyçe dhe përshkruesit |
| LightGlue (varianti ALIKED) | Apache-2.0 | i përputh ato |

Të tre lejojnë përdorim komercial, dhe shkarkohen në përdorimin e parë. SuperPoint, partneri i zakonshëm i LightGlue,
nuk përdoret: peshat e tij janë jokomerciale. Shih [Gjetja e kuadrove në një nivel](locate.md).

## Paketat Python {#python-packages}

| Paketa | Licenca | Roli |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, zbutja, marching cubes |
| opencv-python | Apache-2.0 | video, veçori, rrjedhë optike |
| onnxruntime, onnxruntime-directml | MIT | nxjerrja e thellësisë |
| windows-capture | MIT | kapje e drejtpërdrejtë përmes Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | dritarja |
| pytest | MIT | vetëm për zhvillim |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | konvertim një herë i modelit; rruga offline |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | rruga offline (`requirements-offline.txt`) |
| vggt | "VGGT License" e Meta-s (marrëveshje materialesh kërkimore me politikë përdorimi të pranueshëm) | rruga offline; instalohet nga GitHub me `--no-deps` |
| moderngl, glcontext | MIT | `locate`: vizatimi i nivelit jashtë ekranit (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: pikat kyçe dhe përputhja |

**PySide6 ka kushte.** LGPL-3.0 lejon përdorim pronësor dhe komercial me kusht që Qt të mbetet një
bibliotekë *e zëvendësueshme*. Këtu përdoret si një import i zakonshëm i lidhur në mënyrë dinamike, gjë që e
plotëson këtë, dhe njoftimi i licencës së tij duhet të udhëtojë me çdo shpërndarje. Paketimi i mjetit në një
skedar të vetëm ekzekutues duhet ta mbajë Qt të zëvendësueshëm.

Licenca e vetë paketës `vggt` u lexua nga `LICENSE.txt` i saj dhe është e shënuar te `LICENSES.md`;
ajo mbulon kodin, veçmas nga CC-BY-NC-4.0 e peshave.

## Lojërat {#the-games}

Telemetria vjen vetëm nga ndërfaqet që publikojnë lojërat; kuadrot vijnë nga ekrani. Shih
[Rregullat](rules.md). Ajo ku i drejton përdoruesi mjetet mbetet nën licencën dhe EULA-n e asaj loje,
dhe ky detyrim i takon atij që e ekzekuton mjetin.
