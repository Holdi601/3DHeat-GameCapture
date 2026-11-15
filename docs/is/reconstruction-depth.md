---
title: "Dýpt"
nav_order: 3
lang: "is"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Dýpt {#depth}

Eitt sem ytri upptaka getur ekki gefið er rúmfræði. Leikurinn þekkir dýpt hvers punkts og hún
situr í biðminni sem þetta verkefni snertir viljandi ekki, svo dýptin er **ályktuð út frá
myndinni**. Það er nákvæmnismörk allrar aðferðarinnar.

Kóði: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(það sem skanninn keyrir),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch leiðin og kvarðaaðlögunin),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Líkanið {#the-model}

**Depth Anything V2**, afstæða útgáfan. Það spáir *afstæðri andhverfri dýpt*: sviði líkt ósamræmi (disparity)
sem er aðeins rétt upp að óþekktri affín vörpun,
`metric_disparity = a * predicted + b`, ólík fyrir hvern ramma. Netið er gott í því sem er
erfitt út frá einni mynd (afstætt form, jaðrar, fín bygging) og þegir um það sem það getur ekki
vitað (kvarða). Kvarðinn kemur annars staðar frá - sjá [Staða myndavélar og kvarði](reconstruction-pose.md).

| Stærð | Hugging Face auðkenni | Leyfi |
|---|---|---|
| **Small** (sjálfgefið) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - verslunarnotkun leyfð |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - aðeins ekki-viðskiptaleg notkun |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - aðeins ekki-viðskiptaleg notkun |

Endurgerð erfir leyfi líkansins sem bjó hana til. Small er sjálfgefið alls staðar einmitt
svo skönnun beri engar takmarkanir nema einhver velji annað.
Metrísku útgáfurnar (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) eru
nefndar í kóðanum en ekki notaðar af skannanum. Sjá [Líkön og leyfi](models-and-licences.md).

## Að smíða líkanið {#building-the-model}

Skanninn keyrir ONNX skrá og flytur aldrei inn PyTorch. Skrána þarf að búa til einu sinni:

- **Úr glugganum**: „Set up the depth model“ (sjá [Skannglugginn](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  sem keyrir skipunina hér að neðan með `--size small`.
- **Í höndunum**, í umhverfi með PyTorch, `transformers` og `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `--size` | `small` | `small`, `base` eða `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | úttaksskrá |
| `--side` | `518` | ferningslaga inntaksstærð; verður að vera margfeldi af 14 (ViT reitastærð); 518 = 14 x 37 er þjálfunarupplausnin |
| `--opset` | `17` | ONNX opset; 17 er víða studd af DirectML og CUDA |

Hvað umbreytirinn gerir:

- Sækir þjálfunarpunktinn (checkpoint) frá Hugging Face (`AutoModelForDepthEstimation`).
- Vefur honum þannig að **ImageNet-stöðlunin er inni í netinu**: líkanið tekur RGB á bilinu
  0-255 sem fleytitölu (`pixels`, lögun `batch x 3 x side x side`) og skilar
  `inverse_depth`. Til er nákvæmlega eitt eintak af meðaltali og staðalfráviki, svo þau geta ekki
  vikið frá þjálfunarpunktinum.
- **Föst rýmisstærð**, kvik lotustærð (batch). DirectML og TensorRT þýða fyrir hverja lögun; kvik
  hæð og breidd myndi þýða aftur á fyrsta ramma hverrar nýrrar upplausnar, sýnilegt hik
  í beinni upptöku.
- Flytur út um **TorchScript leiðina** (`dynamo=False`): dynamo netið brást
  í DirectML við Reshape hnút, og það skrifar þyngdirnar sem sérstaka `.onnx.data` skrá.
  TorchScript leiðin býr til eina sjálfstæða skrá.
- Prentar skrána og stærð hennar. Viðvaranir rekjarans um innbakaðar lögun eru væntanlegar.

Skanninn leitar að `models/depth-*.onnx` og velur eftir leyfi, ekki skráarheiti: Small
þegar það er til staðar, stærri stærð aðeins þegar hún er sú eina. Lína skannagluggans
nefnir skrána, leyfi hennar og öll önnur líkön sem hann lét ónotuð.

## Keyrsla: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` smíðar eina ONNX Runtime setu (session), letilega, með fullri fínstillingu netsins, á
bakenda sem stiginn valdi, með CPU bætt aftan við sem varaleið svo veitandi sem bregst við
smíði setu (gamall rekill) þýði hæga skönnun, ekki hrun. Sjá
[Keyrsluumhverfi og ósjálfstæði](runtime.md#inference-backends).

- `warm_up()` smíðar setuna og keyrir einn auðan ramma (fyrsta ályktun á nýju
  neti er nokkrum sinnum hægari en stöðugt ástand).
- `measure_throughput(frames)` tímamælir svo marga auða ramma eftir upphitun; glugginn notar 6
  og birtir niðurstöðuna sem sýnir á sekúndu.

### Svartir kantar, ekki teygja {#letterboxing-not-stretching}

Netið tekur fastan ferning; leikjamyndefni er 16:9. Að kremja ramma í ferning myndi breyta
sýnilegri lögun alls, og þar sem úttakið er rúmfræðileg ágiskun yrði það samrunnið
sem raunveruleg röng rúmfræði. Því er hver rammi:

1. skalaður til að passa í ferninginn, með hlutföllum haldið (flatarmálsinnskot niður, kúbískt upp);
2. fylltur með **miðgráu (114)** - svart eða hvítt lesast sem sterkur jaðar og blæða rangri
   dýptarósamfellu inn í innihaldið við hliðina;
3. keyrður í gegnum líkanið;
4. fyllingin er skorin af spánni **áður** en henni er breytt (kúbískt) aftur í upplausn
   rammans, svo jaðarinn blæði aldrei inn í raunverulega punkta.

Niðurstaðan er `DepthMap` með `metric=False` í stærð upprunarammans.

## PyTorch leiðin {#the-pytorch-path}

`DepthEstimator` keyrir Hugging Face líkanið beint (fp16 á CUDA, fp32 á CPU), í lotum eftir
rammastærð, hver spá stækkuð aftur með bikúbísku innskoti. Skanninn notar það ekki; offline
`reconstruct` skipunin gerir það (sjá [Offline endurgerð](reconstruction-offline.md)), sem er
ein ástæða þess að sú skipun þarf PyTorch og `transformers`.

## Frá afstæðu í metrískt: `fit_scale` og `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Til að breyta spáðri andhverfri dýpt í metra þarf affín vörpunina `scale * predicted + shift`. Þegar
akkeri með þekkta dýpt eru til (eiginleikapunktar þríhyrningsmældir milli þekktra staða, eða
dýpt fyrri ramma sem fest var), leysir `fit_scale` það:

- minnstu kvaðrata **í ósamræmi (disparity)**, ekki í dýpt - skekkja netsins er nokkurn veginn jöfn í
  ósamræmi, en í dýpt myndu nokkur fjarlæg akkeri (þar sem einn punktur ósamræmis er tugir
  metra) ráða öllu;
- **endurtekið endurvigtað** (12 umferðir, Cauchy-lík vigt `1 / (1 + (r / 3 MAD)^2)`),
  því akkeri bera grófar útlagagildi (samsvörun á bíl á hreyfingu, rekningargalli) og eitt slíkt
  akkeri í venjulegri aðlögun dregur allan rammann með sér;
- þarf að minnsta kosti 2 nothæf akkeri; skilar miðgildi absólút leifa og fjölda
  innlagagilda (leif innan 3 x miðgildisins).

`AffineFit.apply` skilar dýpt í metrum með **+inf** fyrir himin. Það athugar spáða gildið
jafnt sem akkerisgildið: himinpunktur sem spáir núlli endar á `shift` - litlu, jákvæðu,
endanlegu - og myndi annars setja alla himinpunkta á draugaskel í einni fjarlægð. Allt
sem er spáð við `1e-4` eða minna er himinn, hvað sem aðlögunin segir.

Samruni geymir síðan aðeins dýpt milli 0,35 m og 60 m (sjá
[Samruni](reconstruction-fusion-and-texture.md#from-depth-to-points)).
