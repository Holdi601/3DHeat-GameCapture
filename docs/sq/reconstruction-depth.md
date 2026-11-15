---
title: "Thellësia"
nav_order: 3
lang: "sq"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Thellësia {#depth}

Gjëja e vetme që kapja e jashtme nuk mund ta japë është gjeometria. Loja e di thellësinë e çdo pikseli dhe ajo
qëndron në një bufer që ky projekt qëllimisht nuk e prek, prandaj thellësia **nxirret nga
pamja**. Ky është kufiri i saktësisë së gjithë qasjes.

Kodi: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(ajo që ekzekuton skaneri),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(rruga PyTorch dhe përshtatja e shkallës),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Modeli {#the-model}

**Depth Anything V2**, varianti relativ. Ai parashikon *thellësi të anasjellë relative*: një fushë
tipi disparitet e saktë vetëm deri në një transformim afin të panjohur,
`metric_disparity = a * predicted + b`, i ndryshëm për çdo kuadër. Rrjeti është i mirë në atë që është
e vështirë nga një imazh i vetëm (forma relative, skajet, struktura e hollë) dhe hesht për atë që nuk
mund ta dijë (shkallën). Shkalla vjen nga gjetkë - shih [Poza e kamerës dhe shkalla](reconstruction-pose.md).

| Madhësia | ID në Hugging Face | Licenca |
|---|---|---|
| **Small** (e paracaktuar) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - përdorimi komercial lejohet |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - vetëm jokomercial |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - vetëm jokomercial |

Një rindërtim trashëgon licencën e modelit që e bëri. Small është e paracaktuar kudo pikërisht që një
skanim të mos mbajë kufizim përveç nëse dikush zgjedh ndryshe.
Variantet metrike (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) përmenden në
kod por nuk përdoren nga skaneri. Shih [Modelet dhe licencat](models-and-licences.md).

## Ndërtimi i modelit {#building-the-model}

Skaneri ekzekuton një skedar ONNX dhe nuk importon kurrë PyTorch. Skedari duhet bërë një herë:

- **Nga dritarja**: "Set up the depth model" (shih [Dritarja e skanimit](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  që ekzekuton komandën më poshtë me `--size small`.
- **Me dorë**, në një mjedis me PyTorch, `transformers` dhe `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opsioni | E paracaktuara | Kuptimi |
|---|---|---|
| `--size` | `small` | `small`, `base` ose `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | skedari dalës |
| `--side` | `518` | madhësia katrore e hyrjes; duhet të jetë shumëfish i 14 (madhësia e copës ViT); 518 = 14 x 37 është rezolucioni i stërvitjes |
| `--opset` | `17` | opset i ONNX; 17 mbështetet gjerësisht nga DirectML dhe CUDA |

Çfarë bën konvertuesi:

- Shkarkon checkpoint-in nga Hugging Face (`AutoModelForDepthEstimation`).
- E mbështjell që **normalizimi ImageNet të jetë brenda grafit**: modeli merr RGB në intervalin
  0-255 si float (`pixels`, forma `batch x 3 x side x side`) dhe jep `inverse_depth`. Ka saktësisht një
  kopje të mesatares dhe devijimit standard, kështu që nuk mund të largohen nga checkpoint-i.
- **Madhësi hapësinore e fiksuar**, batch dinamik. DirectML dhe TensorRT kompilojnë për çdo formë; një
  lartësi dhe gjerësi dinamike do të rikompilonte në kuadrin e parë të çdo rezolucioni të ri, një ngecje e
  dukshme në një kapje të drejtpërdrejtë.
- Eksporton nëpërmjet **rrugës TorchScript** (`dynamo=False`): grafi dynamo dështoi në
  DirectML te një nyje Reshape, dhe i shkruan peshat si një skedar `.onnx.data` të veçantë. Rruga
  TorchScript prodhon një skedar të vetëmjaftueshëm.
- Printon skedarin dhe madhësinë e tij. Paralajmërimet e gjurmuesit për forma të ngulitura priten.

Skaneri kërkon `models/depth-*.onnx` dhe zgjedh sipas licencës, jo sipas emrit të skedarit: Small
sa herë që është aty, një madhësi më e madhe vetëm kur është e vetmja. Rreshti i dritares së skanimit
emërton skedarin, licencën e tij dhe çdo model tjetër që la pa përdorur.

## Ekzekutimi: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` ndërton një seancë ONNX Runtime, në mënyrë të vonuar, me optimizim të plotë të grafit,
në backend-in që zgjodhi shkalla, me CPU të shtuar si rezervë, kështu që një ofrues që dështon në
krijimin e seancës (një drajver i vjetër) do të thotë një skanim i ngadaltë, jo një rrëzim. Shih
[Runtime dhe varësitë](runtime.md#inference-backends).

- `warm_up()` ndërton seancën dhe ekzekuton një kuadër bosh (inferenca e parë mbi një graf të ri është
  disa herë më e ngadaltë se gjendja e qëndrueshme).
- `measure_throughput(frames)` kohëson aq kuadro boshe pas ngrohjes; dritarja përdor 6
  dhe e citon rezultatin si pamje në sekondë.

### Letterbox, jo shtrirje {#letterboxing-not-stretching}

Grafi merr një katror të fiksuar; loja është 16:9. Ngjeshja e një kuadri në një katror do të ndryshonte
formën e dukshme të gjithçkaje, dhe meqë dalja është një vlerësim gjeometrik, ajo do të bashkohej si
gjeometri e vërtetë e gabuar. Prandaj çdo kuadër:

1. shkallëzohet që të futet në katror, duke mbajtur raportin e tij (interpolim sipërfaqeje poshtë, kubik lart);
2. mbushet me **gri të mesme (114)** - e zeza ose e bardha lexohet si skaj i fortë dhe rrjedh një
   ndërprerje të rreme thellësie në përmbajtjen pranë saj;
3. kalon nëpër model;
4. mbushja pritet nga parashikimi **para** se ai të ndryshohet përsëri (kubik) në rezolucionin e
   kuadrit, kështu që margjina nuk rrjedh kurrë në piksele të vërteta.

Rezultati është një `DepthMap` me `metric=False` në madhësinë e kuadrit burim.

## Rruga PyTorch {#the-pytorch-path}

`DepthEstimator` ekzekuton drejtpërdrejt modelin e Hugging Face (fp16 në CUDA, fp32 në CPU), në batch sipas
madhësisë së kuadrit, çdo parashikim ndryshohet përsëri në madhësi në mënyrë bikubike. Skaneri nuk e përdor; komanda
offline `reconstruct` po (shih [Rindërtimi offline](reconstruction-offline.md)), që është një arsye pse ajo komandë
ka nevojë për PyTorch dhe `transformers`.

## Nga relative në metrike: `fit_scale` dhe `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Kthimi i thellësisë së anasjellë të parashikuar në metra ka nevojë për afinin `scale * predicted + shift`. Kur
ka ankora me thellësi të njohur (pika tiparesh të triangulara mes pozave të njohura, ose thellësia e ankoruar e
kuadrit të mëparshëm), `fit_scale` e zgjidh:

- katrorët më të vegjël **në disparitet**, jo në thellësi - gabimi i rrjetit është afërsisht uniform në
  disparitet, ndërsa në thellësi disa ankora të largëta (ku një piksel disparitet është dhjetëra
  metra) do të dominonin;
- **me ripeshim përsëritës** (12 përsëritje, pesha të tipit Cauchy `1 / (1 + (r / 3 MAD)^2)`),
  sepse ankorat mbartin outlier-a të rëndë (një përputhje në një makinë në lëvizje, një defekt gjurmimi) dhe një
  ankorë e tillë në një përshtatje të thjeshtë e tërheq gjithë kuadrin;
- ka nevojë për të paktën 2 ankora të përdorshme; raporton mbetjen absolute mediane dhe numrin e inlier-ave
  (mbetja brenda 3 x medianës).

`AffineFit.apply` kthen thellësinë në metra me **+inf** për qiellin. Kontrollon vlerën e parashikuar po aq sa
atë të ankoruar: një piksel qielli që parashikon zero del te `shift` - i vogël, pozitiv,
i fundëm - dhe përndryshe do t'i vendoste të gjithë pikselat e qiellit në një guaskë fantazmë në një largësi.
Çdo gjë e parashikuar në `1e-4` ose më pak është qiell, çfarëdo që thotë përshtatja.

Bashkimi pastaj mban vetëm thellësi mes 0.35 m dhe 60 m (shih
[Bashkimi](reconstruction-fusion-and-texture.md#from-depth-to-points)).
