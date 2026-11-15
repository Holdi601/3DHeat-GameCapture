---
title: "Hĺbka"
nav_order: 3
lang: "sk"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Hĺbka {#depth}

Jedna vec, ktorú externé zachytávanie nedokáže dať, je geometria. Hra pozná hĺbku každého pixelu
a je v bufferi, do ktorého tento projekt zámerne nezasahuje, takže hĺbka sa **odvodzuje z obrazu**.
To je strop presnosti celého prístupu.

Kód: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(čo spúšťa skener),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(cesta PyTorch a prifitovanie mierky),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, relatívna varianta. Predpovedá *relatívnu inverznú hĺbku*: pole podobné
disparite, správne len až do neznámej afinnej transformácie, `metric_disparity = a * predicted + b`,
iná pre každú snímku. Sieť je dobrá v tom, čo je z jedného obrazu ťažké (relatívny tvar, hrany,
tenké štruktúry), a mlčí o tom, čo nemôže vedieť (mierka). Mierka sa berie inde – pozrite
[Poloha kamery a mierka](reconstruction-pose.md).

| Veľkosť | Identifikátor na Hugging Face | Licencia |
|---|---|---|
| **Small** (predvolená) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** – komerčné použitie povolené |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 – len nekomerčne |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 – len nekomerčne |

Rekonštrukcia dedí licenciu modelu, ktorý ju vytvoril. Small je všade predvolená práve preto, aby
sken nemal žiadne obmedzenie, pokiaľ si ho niekto nevyberie inak. Metrické varianty
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) sú v kóde pomenované, ale skener
ich nepoužíva. Pozrite [Modely a licencie](models-and-licences.md).

## Vytvorenie modelu {#building-the-model}

Skener spúšťa súbor ONNX a nikdy neimportuje PyTorch. Súbor sa musí vytvoriť raz:

- **z okna**: „Set up the depth model“ (pozrite [Okno skenovania](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  čo spustí príkaz nižšie s `--size small`.
- **ručne**, v prostredí s PyTorch, `transformers` a `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Voľba | Predvolené | Význam |
|---|---|---|
| `--size` | `small` | `small`, `base` alebo `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | výstupný súbor |
| `--side` | `518` | štvorcová veľkosť vstupu; musí byť násobkom 14 (veľkosť záplaty ViT); 518 = 14 x 37 je trénovacie rozlíšenie |
| `--opset` | `17` | opset ONNX; 17 je široko podporovaný v DirectML a CUDA |

Čo konvertor robí:

- Stiahne kontrolný bod z Hugging Face (`AutoModelForDepthEstimation`).
- Obalí ho tak, že **normalizácia ImageNet je vnútri grafu**: model berie RGB v rozsahu 0–255 ako
  float (`pixels`, tvar `batch x 3 x side x side`) a vracia `inverse_depth`. Je presne jedna kópia
  strednej hodnoty a smerodajnej odchýlky, takže sa nemôžu odchýliť od kontrolného bodu.
- **Pevná priestorová veľkosť**, dynamická dávka. DirectML a TensorRT kompilujú pre každý tvar;
  dynamická výška a šírka by sa prekompilovala pri prvej snímke každého nového rozlíšenia, čo je
  viditeľné zaseknutie v živom zachytávaní.
- Exportuje cez **cestu TorchScript** (`dynamo=False`): graf dynamo na DirectML zlyhal pri uzle
  Reshape a zapisuje váhy do samostatného súboru `.onnx.data`. Cesta TorchScript dá jeden samostatný
  súbor.
- Vypíše súbor a jeho veľkosť. Varovania tracera o zapečených tvaroch sú očakávané.

Skener hľadá `models/depth-*.onnx` a vyberá podľa licencie, nie podľa názvu súboru: Small vždy, keď
je k dispozícii, väčšiu veľkosť len vtedy, keď je jediná. Riadok okna skenera pomenuje súbor, jeho
licenciu a všetky ďalšie nepoužité modely.

## Spúšťanie: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` vytvorí jednu reláciu ONNX Runtime, lenivo, s plnou optimalizáciou grafu, na
backende, ktorý vybral rebrík, s CPU pripojeným ako záložné, takže poskytovateľ, ktorý zlyhá pri
vytváraní relácie (starý ovládač), znamená pomalý sken, nie pád. Pozrite
[Runtime a závislosti](runtime.md#inference-backends).

- `warm_up()` vytvorí reláciu a spustí jednu prázdnu snímku (prvá inferencia na novom grafe je
  niekoľkonásobne pomalšia než ustálený stav).
- `measure_throughput(frames)` odmeria toľko prázdnych snímok po zahriatí; okno použije 6 a výsledok
  uvádza ako pohľady za sekundu.

### Letterboxing, nie roztiahnutie {#letterboxing-not-stretching}

Graf berie pevný štvorec; hranie je 16:9. Stlačenie snímky do štvorca by zmenilo zdanlivý tvar
všetkého, a keďže výstup je geometrický odhad, zlúčil by sa ako skutočná zlá geometria. Preto každá
snímka je:

1. zmenená tak, aby sa zmestila do štvorca so zachovaným pomerom strán (interpolácia podľa plochy
   dolu, kubická hore);
2. doplnená **strednou sivou (114)** – čierna alebo biela sa číta ako silná hrana a prenesie falošný
   skok hĺbky do obsahu vedľa;
3. prebehne cez model;
4. výplň sa z predikcie odreže **pred** tým, než sa zväčší späť (kubicky) na rozlíšenie snímky, takže
   okraj nikdy nezasiahne skutočné pixely.

Výsledkom je `DepthMap` s `metric=False` vo veľkosti zdrojovej snímky.

## Cesta PyTorch {#the-pytorch-path}

`DepthEstimator` spúšťa model Hugging Face priamo (fp16 na CUDA, fp32 na CPU), dávkovaný podľa
veľkosti snímky, každá predikcia sa bikubicky vracia na veľkosť. Skener ju nepoužíva; offline príkaz
`reconstruct` áno (pozrite [Offline rekonštrukcia](reconstruction-offline.md)), čo je jeden z dôvodov,
prečo ten príkaz potrebuje PyTorch a `transformers`.

## Z relatívnej na metrickú: `fit_scale` a `AffineFit` {#from-relative-to-metric-fit_scale-and-affinefit}

Premena predikovanej inverznej hĺbky na metre potrebuje afinné `scale * predicted + shift`. Keď
sú k dispozícii kotvy so známou hĺbkou (body čŕt triangulované medzi známymi polohami, alebo
zakotvená hĺbka predchádzajúcej snímky), `fit_scale` ho vyrieši:

- metódou najmenších štvorcov **v disparite**, nie v hĺbke – chyba siete je zhruba rovnomerná v
  disparite, kým v hĺbke by niekoľko vzdialených kotiev (kde je jeden pixel disparity desiatky metrov)
  dominovalo;
- **iteratívne prevážené** (12 iterácií, váhy typu Cauchy `1 / (1 + (r / 3 MAD)^2)`), lebo kotvy nesú
  hrubé odľahlé hodnoty (zhoda na pohybujúcom sa aute, chyba sledovania) a jedna taká kotva v
  jednoduchom prifitovaní ťahá celú snímku;
- potrebuje aspoň 2 použiteľné kotvy; hlási medián absolútneho rezidua a počet vnútorných bodov
  (rezíduum do 3 x mediánu).

`AffineFit.apply` vráti hĺbku v metroch s **+inf** pre oblohu. Overuje predikovanú hodnotu aj
zakotvenú: pixel oblohy s predikciou nula vyjde na `shift` – malý, kladný, konečný – a inak by
pristál každý pixel oblohy na fantómovej škrupine v jednej vzdialenosti. Všetko, čo je predikované
na alebo pod `1e-4`, je obloha, nech hovorí fit čokoľvek.

Fúzia potom ponechá len hĺbky medzi 0,35 m a 60 m (pozrite
[Fúzia](reconstruction-fusion-and-texture.md#from-depth-to-points)).
