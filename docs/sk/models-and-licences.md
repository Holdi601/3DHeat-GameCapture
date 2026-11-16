---
title: "Modely a licencie"
nav_order: 7
lang: "sk"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modely a licencie {#models-and-licences}

Všetko napísané pre tento repozitár je pod **licenciou MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Čo MIT nemôže
pokryť, je to, s čím nástroje bežia: balíky, ktoré importujú, modely, ktoré rekonštrukcia používa,
a hry, ktoré čítajú. Úplný záznam so zdrojmi je v
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); jeho
licencie boli prečítané z metadát balíkov a z kariet modelov v septembri 2026. Ak sa podmienky
komponentu odvtedy zmenili, rozhoduje zdroj, nie táto stránka. Nie je to právne poradenstvo.

## Model hĺbky - ten, ktorý rozhoduje o komerčnom použití {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **nemá rovnakú licenciu pre všetky veľkosti**, a rekonštrukcia dedí licenciu
modelu, ktorý ju vytvoril:

| Model | Licencia | Komerčné použitie | Používa ho |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **povolené** | predvolený: prevedený model skenera (`tools/export_onnx.py` predvolene použije tento a tlačidlo okna "Set up the depth model" ho vždy vytvorí), a hĺbka offline cesty (fúzia); VGGT dodáva jeho pózy |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | iba nekomerčné | len ak ho prevediete sami (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | iba nekomerčné | len ak ho prevediete sami (`--size large`) |

Base a Large dávajú lepšiu hĺbku. Previesť ich je povolené; vytvorí to súbor modelu a každú
rekonštrukciu urobenú s ním - tá sa stane nekomerčnou. Je to rozhodnutie toho, kto to spúšťa,
nie predvolená vec, ktorú treba prevziať. Skener vyberá medzi súbormi `models/depth-*.onnx`
**podľa licencie, nie podľa názvu**: `depth-small-*`, kedykoľvek je k dispozícii, potom Base, potom
Large (`choose_model` v
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Okno uvedie názov súboru, ktorý zobralo, jeho licenciu a všetky ďalšie nájdené súbory modelov,
ktoré nepoužilo; ak chcete skenovať s Base, presuňte súbor Small mimo `models/`.

## VGGT - iba offline rekonštrukcia {#vggt---offline-reconstruction-only}

| Model | Licencia | Dostupnosť |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - iba nekomerčné**; rekonštrukcie s ním to dedia | verejný; predvolený |
| `facebook/VGGT-1B-Commercial` | samostatne licencovaný; skontrolujte podmienky, ktoré ste dostali | s obmedzeným prístupom: prístup sa žiada od Meta a udeľuje sa na účet; bez neho sťahovanie zlyhá. Vyberá sa s `reconstruct --model vggt-1b-commercial` |

VGGT používa iba `python -m heat3d_capture reconstruct`; živý skener ho nikdy nenačíta. Príkaz
pred štartom vypíše riadok s licenciou. Rekonštrukcia z videa je časť projektu, ktorú by hráč
spúšťal sám, a nekomerčné podmienky jej vyhovujú; na komerčnú prácu je cestou export z motora
alebo exportér herných súborov, a obe sú aj tak presné.

## Hľadanie snímok - `locate` {#locating-frames---locate}

| Model | Licencia | Úloha |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | nájde rendery, ktoré ukazujú to isté miesto |
| ALIKED `aliked-n16` | BSD-3-Clause | kľúčové body a deskriptory |
| LightGlue (variant ALIKED) | Apache-2.0 | páruje ich |

Všetky tri povoľujú komerčné použitie a sťahujú sa pri prvom použití. SuperPoint, obvyklý
partner LightGlue, sa nepoužíva: jeho váhy sú nekomerčné. Pozrite [Hľadanie snímok v leveli](locate.md).

## Balíky Python {#python-packages}

| Balík | Licencia | Úloha |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, vyhladzovanie, marching cubes |
| opencv-python | Apache-2.0 | video, príznaky, optický tok |
| onnxruntime, onnxruntime-directml | MIT | inferencia hĺbky |
| windows-capture | MIT | živé snímanie cez Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | okno |
| pytest | MIT | iba pre vývoj |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | jednorazový prevod modelu; offline cesta |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | offline cesta (`requirements-offline.txt`) |
| vggt | "VGGT License" od Meta (dohoda o výskumných materiáloch so zásadami prijateľného použitia) | offline cesta; inštaluje sa z GitHubu s `--no-deps` |
| moderngl, glcontext | MIT | `locate`: vykresľovanie levelu mimo obrazovky (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: kľúčové body a párovanie |

**PySide6 má podmienky.** LGPL-3.0 povoľuje proprietárne a komerčné použitie za predpokladu, že Qt
zostane *nahraditeľná* knižnica. Tu sa používa ako bežný dynamicky prepojený import, čo to spĺňa,
a jej licenčné upozornenie musí putovať s každou distribúciou. Zabalenie nástroja do jedného
spustiteľného súboru by muselo zachovať Qt nahraditeľné.

Licencia samotného balíka `vggt` bola prečítaná z jeho `LICENSE.txt` a je zapísaná v
`LICENSES.md`; vzťahuje sa na kód, oddelene od CC-BY-NC-4.0 váh.

## Hry {#the-games}

Telemetria prichádza len z rozhraní, ktoré hry zverejňujú; snímky prichádzajú z obrazovky. Pozrite
[Pravidlá](rules.md). Nič z hry sa nedodáva ani ďalej nešíri a to, čo nástroje vytvoria, zostáva na počítači používateľa. 3DHeat GameCapture nie je spojený so žiadnym vydavateľom hier ani ním schválený; názvy hier a súvisiace ochranné známky patria ich vlastníkom.
