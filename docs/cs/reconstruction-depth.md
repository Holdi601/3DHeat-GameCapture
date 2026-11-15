---
title: "Hloubka"
nav_order: 3
lang: "cs"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Hloubka {#depth}

Jedinou věc, kterou vnější záznam nedá, je geometrie. Hra zná hloubku každého pixelu
a je v vyrovnávací paměti, do které se tento projekt záměrně nedotýká, takže hloubka
se **odvozuje z obrazu**. To je strop přesnosti celého přístupu.

Kód: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(co skener spouští),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(cesta PyTorch a přizpůsobení měřítka),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, relativní varianta. Předpovídá *relativní inverzní hloubku*:
pole podobné disparitě, správné jen až na neznámou afinní transformaci,
`metrická_disparita = a * předpověď + b`, různou pro každý snímek. Síť je dobrá v tom,
co je z jednoho obrazu těžké (relativní tvar, hrany, tenké struktury), a mlčí o tom,
co nemůže vědět (měřítko). Měřítko přichází odjinud - viz
[Poloha kamery a měřítko](reconstruction-pose.md).

| Velikost | Identifikátor na Hugging Face | Licence |
|---|---|---|
| **Malý** (výchozí) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - komerční použití povoleno |
| Základní | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - jen nekomerční |
| Velký | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - jen nekomerční |

Rekonstrukce dědí licenci modelu, který ji vytvořil. Malý je všude výchozí právě proto,
aby sken nesl žádné omezení, pokud si někdo nezvolí jinak. Metrické varianty
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) jsou v kódu
pojmenované, ale skener je nepoužívá. Viz [Modely a licence](models-and-licences.md).

## Sestavení modelu {#building-the-model}

Skener spouští soubor ONNX a nikdy neimportuje PyTorch. Soubor se musí vyrobit jednou:

- **z okna**: „Nastavit model hloubky“ (viz [Okno skenování](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  které spustí příkaz níže s `--size small`.
- **ručně**, v prostředí s PyTorch, `transformers` a `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Volba | Výchozí | Význam |
|---|---|---|
| `--size` | `small` | `small`, `base` nebo `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | výstupní soubor |
| `--side` | `518` | čtvercová vstupní velikost; musí být násobek 14 (velikost záplaty ViT); 518 = 14 x 37 je trénovací rozlišení |
| `--opset` | `17` | sada operací ONNX; 17 je široce podporována DirectML a CUDA |

Co konvertor dělá:

- Stáhne kontrolní bod z Hugging Face (`AutoModelForDepthEstimation`).
- Obalí ho tak, že **normalizace ImageNet je uvnitř grafu**: model bere RGB v rozsahu
  0-255 jako float (`pixels`, tvar `dávka x 3 x side x side`) a vrací
  `inverse_depth`. Existuje přesně jedna kopie průměru a směrodatné odchylky, takže
  se nemohou odchýlit od kontrolního bodu.
- **Pevná prostorová velikost**, dynamická dávka. DirectML a TensorRT kompilují podle
  tvaru; dynamická výška a šířka by se zkompilovala na prvním snímku každého nového
  rozlišení, což je v živém záznamu vidět jako zadrhnutí.
- Exportuje přes **cestu TorchScript** (`dynamo=False`): graf dynamo na DirectML
  selhal u uzlu Reshape a zapisuje váhy do samostatného souboru `.onnx.data`. Cesta
  TorchScript vyrobí jeden soubor, který je samostatný.
- Vypíše soubor a jeho velikost. Varování tracer o zapečených tvarech jsou očekávaná.

Skener hledá `models/depth-*.onnx` a vybírá podle licence, ne podle názvu souboru:
Malý, kdykoli je k dispozici, větší velikost jen tehdy, když je jediná. Řádek okna
pojmenuje soubor, jeho licenci a případný další model, který nepoužil.

## Spuštění: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` vytvoří jednu relaci ONNX Runtime, líně, s plnou optimalizací
grafu, na backendu, který vybral žebřík, s CPU připojeným jako záložní, takže
poskytovatel, který selže při vytváření relace (starý ovladač), znamená pomalý sken,
ne pád. Viz [Běh a závislosti](runtime.md#inference-backends).

- `warm_up()` vytvoří relaci a spustí jeden prázdný snímek (první inference na čerstvém
  grafu je několikrát pomalejší než ustálený stav).
- `measure_throughput(frames)` změří tolik prázdných snímků po zahřátí; okno použije 6
  a výsledek uvede jako pohledy za sekundu.

### Letterbox, ne roztahování {#letterboxing-not-stretching}

Graf bere pevný čtverec, hra je 16:9. Stlačení snímku do čtverce by změnilo zdánlivý
tvar všeho, a protože výstup je geometrický odhad, sloučil by se jako skutečná
špatná geometrie. Každý snímek se proto:

1. zmenší tak, aby se vešel do čtverce, s zachovaným poměrem stran (plošná interpolace
   dolů, kubická nahoru);
2. doplní **střední šedou (114)** - černá nebo bílá se čte jako silná hrana a přenese
   falešnou hloubkovou nespojitost do obsahu vedle sebe;
3. proženou modelem;
4. výplň se z předpovědi ořízne **před** tím, než se zvětší zpět (kubicky) na
   rozlišení snímku, takže okraj nikdy nezasáhne skutečné pixely.

Výsledkem je `DepthMap` s `metric=False` ve velikosti zdrojového snímku.

## Cesta PyTorch {#the-pytorch-path}

`DepthEstimator` spouští přímo model Hugging Face (fp16 na CUDA, fp32 na CPU), dávkovaně
podle velikosti snímku, každou předpověď zvětšuje zpět bikubicky. Skener ji nepoužívá;
offline příkaz `reconstruct` ano (viz [Offline rekonstrukce](reconstruction-offline.md)),
což je jeden z důvodů, proč tento příkaz potřebuje PyTorch a `transformers`.

## Od relativní k metrické: `fit_scale` a `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Převod předpovězené inverzní hloubky na metry potřebuje afinní `scale * předpověď + shift`.
Když jsou k dispozici kotvy známé hloubky (body rysů triangulované mezi známými
polohami, nebo kotvená hloubka předchozího snímku), `fit_scale` ji vyřeší:

- nejmenší čtverce **v disparitě**, ne v hloubce - chyba sítě je zhruba stejná v
  disparitě, zatímco v hloubce by pár vzdálených kotev (kde jeden pixel disparity znamená
  desítky metrů) dominoval;
- **iterativně převážené** (12 iterací, váhy typu Cauchy `1 / (1 + (r / 3 MAD)^2)`),
  protože kotvy nesou hrubé odlehlé hodnoty (shoda na pohybujícím se autě, výpadek
  sledování) a jedna taková kotva v prostém přizpůsobení táhne celý snímek;
- potřebuje alespoň 2 použitelné kotvy; hlásí medián absolutního rezidua a počet
  inlierů (reziduum do 3 x medián).

`AffineFit.apply` vrací hloubku v metrech s **+inf** pro oblohu. Kontroluje předpovězenou
hodnotu i kotvenou: pixel oblohy s předpovědí nula by vyšel na `shift` - malý, kladný,
konečný - a jinak by všechny pixely oblohy přistály na falešné slupce v jedné
vzdálenosti. Cokoli předpovězeného na `1e-4` nebo níž je obloha, bez ohledu na to, co
přizpůsobení říká.

Sloučení pak ponechá jen hloubky mezi 0,35 m a 60 m (viz
[Sloučení](reconstruction-fusion-and-texture.md#from-depth-to-points)).
