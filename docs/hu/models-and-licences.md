---
title: Modellek és licencek
nav_order: 7
lang: "hu"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modellek és licencek {#models-and-licences}

Minden, ami ehhez a tárhoz készült, az **MIT licenc** alatt áll
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Amit az MIT nem fed le,
az az, amivel az eszközök futnak: az importált csomagok, a rekonstrukcióhoz használt modellek és a
kiolvasott játékok. A teljes nyilvántartás, a forrásokkal együtt, a
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md) fájlban van; a
licenceket 2026 szeptemberében a csomagok metaadataiból és a modellkártyákról olvastuk le. Ha egy
összetevő feltételei azóta változtak, a forrás számít, nem ez az oldal. Ez nem jogi tanács.

## A mélységmodell - ez dönti el a kereskedelmi használatot {#the-depth-model---the-one-that-decides-commercial-use}

A Depth Anything V2 **mérettől függően más licenc alatt áll**, és a rekonstrukció örökli annak a modellnek
a licencét, amely elkészítette:

| Modell | Licenc | Kereskedelmi használat | Felhasználja |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **megengedett** | az alapértelmezés: a szkenner átalakított modellje (a `tools/export_onnx.py` ezt használja alapértelmezésben, az ablak „Mélységmodell beállítása” gombja pedig mindig ezt építi), és az offline útvonal mélysége (fúzió); a VGGT adja a pozíciókat |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | csak nem kereskedelmi célra | csak ha ön maga alakítja át (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | csak nem kereskedelmi célra | csak ha ön maga alakítja át (`--size large`) |

A Base és a Large jobb mélységet ad. Átalakításuk megengedett; ettől azonban az a modellfájl, és minden vele
készült rekonstrukció, nem kereskedelmi lesz. Ez annak a döntése, aki futtatja, nem alapértelmezés, amit
örökölni kell. A szkenner a `models/depth-*.onnx` fájlok közül **licenc szerint választ, nem név szerint**:
mindig a `depth-small-*` fájlt veszi, ha van ilyen, utána a Base-t, végül a Large-t (`choose_model` a
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
fájlban). Az ablak megnevezi a fájlt, amelyet választott, annak licencét, és a többi talált, de nem használt
modellfájlt; ha Base-zel szeretne szkennelni, vigye ki a Small fájlt a `models/` mappából.

## VGGT - csak offline rekonstrukcióhoz {#vggt---offline-reconstruction-only}

| Modell | Licenc | Elérhetőség |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - csak nem kereskedelmi célra**; az ezzel készült rekonstrukciók is ezt örökölik | nyilvános; az alapértelmezés |
| `facebook/VGGT-1B-Commercial` | külön licencelt; ellenőrizze a kapott feltételeket | zárt: a hozzáférést a Metától kell kérni, fiókonként adják meg; enélkül a letöltés meghiúsul. A `reconstruct --model vggt-1b-commercial` kapcsolóval választható |

A VGGT-t csak a `python -m heat3d_capture reconstruct` használja; az élő szkenner sosem tölti be. A parancs
az indulás előtt kiírja a licencsort. A videóból való rekonstrukció az a rész, amelyet egy játékos futtatna,
és a nem kereskedelmi feltételek ehhez illenek; kereskedelmi munkához motorexport vagy a játékfájl-exportáló
az út, mindkettő amúgy is pontos.

## Képkockák megtalálása - `locate` {#locating-frames---locate}

| Modell | Licenc | Szerep |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | megtalálja azokat a renderelt képeket, amelyek ugyanazt a helyet mutatják |
| ALIKED `aliked-n16` | BSD-3-Clause | kulcspontok és leírók |
| LightGlue (ALIKED-változat) | Apache-2.0 | illeszti őket |

Mindhárom megengedi a kereskedelmi használatot, és első használatkor töltődik le. A SuperPoint, a LightGlue
szokásos párja, nincs használatban: súlyai nem kereskedelmiek. Lásd: [Képkockák megtalálása a pályán](locate.md).

## Python-csomagok {#python-packages}

| Csomag | Licenc | Szerep |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | számítás, simítás, marching cubes |
| opencv-python | Apache-2.0 | videó, jellemzők, optikai áramlás |
| onnxruntime, onnxruntime-directml | MIT | mélységi következtetés |
| windows-capture | MIT | élő rögzítés a Windows Graphics Capture-rel |
| **PySide6-Essentials** | **LGPL-3.0** | az ablak |
| pytest | MIT | csak fejlesztéshez |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | egyszeri modellátalakítás; az offline útvonal |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | az offline útvonal (`requirements-offline.txt`) |
| vggt | Meta „VGGT License” (kutatási anyagokra vonatkozó megállapodás, elfogadható használati szabályzattal) | az offline útvonal; GitHubról, `--no-deps` kapcsolóval telepítve |
| moderngl, glcontext | MIT | `locate`: a pálya renderelése offscreen (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: kulcspontok és illesztés |

**A PySide6-nak vannak feltételei.** Az LGPL-3.0 megengedi a zárt forrású és kereskedelmi használatot, ha a
Qt *cserélhető* könyvtár marad. Itt szokásos, dinamikusan linkelt importként használjuk, ez ezt teljesíti, és
a licencértesítését minden terjesztéssel együtt kell adni. Ha az eszközt egyetlen futtatható fájlba csomagolnánk,
a Qt cserélhetőségét meg kellene őrizni.

A `vggt` csomag saját licencét a `LICENSE.txt` fájlból olvastuk le, és a `LICENSES.md` tartalmazza; a
súlyokra vonatkozó CC-BY-NC-4.0-tól külön áll.

## A játékok {#the-games}

A telemetria csak olyan felületekről származik, amelyeket a játékok közzétesznek; a képkockák a képernyőről
jönnek. Lásd: [A szabályok](rules.md). Hogy mire irányítja a felhasználó az eszközöket, az továbbra is az adott
játék licencére és EULA-jára tartozik, és ez a kötelezettség azt terheli, aki az eszközt futtatja.
