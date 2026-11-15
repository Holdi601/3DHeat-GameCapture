---
title: Modely a licence
nav_order: 7
lang: "cs"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modely a licence {#models-and-licences}

Všechno napsané pro tento repozitář je pod **licencí MIT** ([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Co MIT nepokrývá, je to, s čím nástroje běží: balíčky, které importují, modely, které rekonstrukce používá, a hry, které čtou. Úplný záznam se zdroji je v [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md). Jeho licence byly zjištěny z metadat balíčků a z karet modelů v září 2026. Kde se podmínky komponenty od té doby změnily, rozhoduje zdroj, ne tato stránka. Nic zde není právní poradenství.

## Model hloubky: ten, který rozhoduje o komerčním použití {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **nemá licenci stejnou pro všechny velikosti**. Rekonstrukce dědí licenci modelu, který ji vytvořil:

| Model | Licence | Komerční použití | Používá se |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **povoleno** | výchozí: převedený model skeneru (`tools/export_onnx.py` ho bere automaticky a tlačítko okna „Nastavit model hloubky“ ho vždy vytvoří) a hloubka offline cesty (fúze); VGGT dodává jeho pózy |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | jen nekomerčně | jen když ho převedete sami (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | jen nekomerčně | jen když ho převedete sami (`--size large`) |

Base a Large mají lepší hloubku. Jejich převod je povolen, ale vytvoří soubor modelu a každou rekonstrukci s ním udělá nekomerční. To je rozhodnutí toho, kdo ho spouští, ne výchozí hodnota, kterou je třeba převzít. Skener vybírá mezi soubory `models/depth-*.onnx` **podle licence, ne podle názvu**: vždy `depth-small-*`, když existuje, pak Base, pak Large (`choose_model` v [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). Okno pojmenuje soubor, který vzalo, jeho licenci a všechny další nalezené soubory modelů, které nepoužilo. Pro skenování s Base přesuňte soubor Small z `models/`.

## VGGT: jen pro offline rekonstrukci {#vggt---offline-reconstruction-only}

| Model | Licence | Dostupnost |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0, jen nekomerčně**; rekonstrukce s ním tuto licenci dědí | veřejný; výchozí |
| `facebook/VGGT-1B-Commercial` | licencovaný zvlášť; zkontrolujte podmínky, které jste dostali | uzavřený: přístup se žádá u Meta a uděluje se pro každý účet; bez něj stahování selže. Vybírá se s `reconstruct --model vggt-1b-commercial` |

VGGT používá jen `python -m heat3d_capture reconstruct`; živý skener ho nikdy nenačte. Příkaz před startem vypíše řádek s licencí. Rekonstrukce z videa je část tohoto projektu, kterou by hráč spouštěl, a nekomerční podmínky se k tomu hodí. Pro komerční práci je cestou export z enginu nebo exportér herních souborů; obě jsou tak jako tak přesné.

## Vyhledávání snímků: `locate` {#locating-frames---locate}

| Model | Licence | Úloha |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | najde vykreslení, která ukazují stejné místo |
| ALIKED `aliked-n16` | BSD-3-Clause | klíčové body a deskriptory |
| LightGlue (varianta ALIKED) | Apache-2.0 | páruje je |

Všechny tři dovolují komerční použití a stahují se při prvním použití. SuperPoint, obvyklý partner LightGlue, se nepoužívá: jeho váhy jsou nekomerční. Viz [Vyhledávání snímků v úrovni](locate.md).

## Balíčky Pythonu {#python-packages}

| Balíček | Licence | Úloha |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetika, vyhlazování, pochodující kostky |
| opencv-python | Apache-2.0 | video, rysy, optický tok |
| onnxruntime, onnxruntime-directml | MIT | inference hloubky |
| windows-capture | MIT | živé zachytávání přes Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | okno |
| pytest | MIT | jen vývoj |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | jednorázový převod modelu; offline cesta |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | offline cesta (`requirements-offline.txt`) |
| vggt | „VGGT License“ od Meta (smlouva o výzkumných materiálech s zásadami přijatelného použití) | offline cesta; instaluje se z GitHubu s `--no-deps` |
| moderngl, glcontext | MIT | `locate`: vykreslování úrovně mimo obrazovku (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: klíčové body a párování |

**PySide6 má podmínky.** LGPL-3.0 dovoluje proprietární a komerční použití za podmínky, že Qt zůstane *nahraditelnou* knihovnou. Tady se používá jako obyčejný dynamicky propojený import, což to splňuje, a její oznámení o licenci musí jít s každou distribucí. Sbalení nástroje do jediného spustitelného souboru by muselo zachovat Qt nahraditelné.

Vlastní licence balíčku `vggt` byla přečtena z jeho souboru `LICENSE.txt` a je zapsána v `LICENSES.md`. Vztahuje se na kód odděleně od vah CC-BY-NC-4.0.

## Hry {#the-games}

Telemetrie pochází jen z rozhraní, která hry zveřejňují. Snímky pocházejí z obrazovky. Viz [Pravidla](rules.md). Co uživatel nasměruje nástroje na, zůstává podřízeno licenci a EULA dané hry; ta povinnost patří tomu, kdo nástroj spouští.
