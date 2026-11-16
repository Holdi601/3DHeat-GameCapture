---
title: "Modele și licențe"
nav_order: 7
lang: "ro"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modele și licențe {#models-and-licences}

Tot ce este scris pentru acest depozit este sub **licența MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Ce nu poate acoperi
MIT este ceea ce rulează uneltele: pachetele pe care le importă, modelele pe care le folosește
reconstrucția și jocurile pe care le citesc. Înregistrarea completă, cu surse, este
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); licențele ei
au fost citite din metadatele pachetelor și din fișele modelelor în septembrie 2026. Dacă termenii
unei componente s-au schimbat de atunci, conta sursa, nu această pagină. Nimic de aici nu este
consiliere juridică.

## Modelul de adâncime - cel care decide utilizarea comercială {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **nu are aceeași licență pentru toate dimensiunile**, iar o reconstrucție moștenește
licența modelului care a făcut-o:

| Model | Licență | Utilizare comercială | Folosit de |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **permisă** | implicitul: modelul convertit al scanerului (`tools/export_onnx.py` îl alege implicit, iar „Set up the depth model” din fereastră îl construiește mereu), și adâncimea căii offline (fuziune); VGGT furnizează pozele |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | doar necomercială | doar dacă îl convertiți singur (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | doar necomercială | doar dacă îl convertiți singur (`--size large`) |

Base și Large dau o adâncime mai bună. Convertirea lor este permisă; face ca fișierul modelului și
fiecare reconstrucție făcută cu el să fie necomerciale. Aceasta este o decizie a celui care le
rulează, nu un implicit de moștenit. Scanerul alege între fișierele `models/depth-*.onnx` **după
licență, nu după nume**: `depth-small-*` ori de câte ori există unul, apoi Base, apoi Large
(`choose_model` în
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Fereastra spune ce fișier a luat, licența lui și orice alte fișiere de model găsite și nefolosite; ca
să scanați cu Base, mutați fișierul Small afară din `models/`.

## VGGT - doar pentru reconstrucția offline {#vggt---offline-reconstruction-only}

| Model | Licență | Disponibilitate |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - doar necomercial**; reconstrucțiile făcute cu el moștenesc asta | public; implicitul |
| `facebook/VGGT-1B-Commercial` | licență separată; verificați termenii care v-au fost acordați | cu acces restricționat: accesul se cere de la Meta și se acordă per cont; fără el descărcarea eșuează. Se alege cu `reconstruct --model vggt-1b-commercial` |

VGGT este folosit doar de `python -m heat3d_capture reconstruct`; scanerul live nu îl încarcă
niciodată. Comanda afișează linia de licență înainte să pornească. Reconstrucția din video este partea
din proiect pe care o rulează un jucător, iar termenii necomerciali se potrivesc; pentru lucru
comercial, o cale este exportul din motor sau exportatorul de fișiere de joc, iar ambele sunt oricum
exacte.

## Localizarea cadrelor - `locate` {#locating-frames---locate}

| Model | Licență | Rol |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | găsește randările care arată același loc |
| ALIKED `aliked-n16` | BSD-3-Clause | puncte-cheie și descriptori |
| LightGlue (varianta ALIKED) | Apache-2.0 | le potrivește |

Toate trei permit utilizarea comercială și se descarcă la prima folosire. SuperPoint, partenerul
obișnuit al LightGlue, nu este folosit: greutățile lui sunt necomerciale. Vezi
[Localizarea cadrelor într-un nivel](locate.md).

## Pachete Python {#python-packages}

| Pachet | Licență | Rol |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetică, netezire, marching cubes |
| opencv-python | Apache-2.0 | video, trăsături, flux optic |
| onnxruntime, onnxruntime-directml | MIT | inferența adâncimii |
| windows-capture | MIT | captură live prin Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | fereastra |
| pytest | MIT | doar pentru dezvoltare |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | conversia unică a modelelor; calea offline |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | calea offline (`requirements-offline.txt`) |
| vggt | „VGGT License” al Meta (acord pentru materiale de cercetare cu o politică de utilizare acceptabilă) | calea offline; instalat din GitHub cu `--no-deps` |
| moderngl, glcontext | MIT | `locate`: randarea nivelului în afara ecranului (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: puncte-cheie și potrivire |

**PySide6 are condiții.** LGPL-3.0 permite utilizarea proprietară și comercială, cu condiția ca Qt să
rămână o bibliotecă *înlocuibilă*. Aici este folosit ca un import obișnuit, legat dinamic, ceea ce
satisface această condiție, iar anunțul lui de licență trebuie să însoțească orice distribuire.
Împachetarea uneltei într-un singur executabil ar trebui să păstreze Qt înlocuibil.

Licența pachetului `vggt` a fost citită din `LICENSE.txt` al lui și este consemnată în `LICENSES.md`;
ea acoperă codul, separat de CC-BY-NC-4.0 al greutăților.

## Jocurile {#the-games}

Telemetria vine doar din interfețele pe care jocurile le publică; cadrele vin de pe ecran. Vezi
[Regulile](rules.md). Nimic dintr-un joc nu este livrat sau redistribuit, iar ce produc uneltele rămâne pe calculatorul utilizatorului. 3DHeat GameCapture nu este afiliat cu niciun editor de jocuri și nu este aprobat de vreunul; numele jocurilor și mărcile asociate aparțin proprietarilor lor.
