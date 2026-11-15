---
title: "Djup"
nav_order: 3
lang: "sv"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Djup {#depth}

Det enda som extern bildtagning inte kan ge är geometri. Spelet känner varje pixels djup och det ligger i en buffer som det här projektet medvetet inte rör, så djup **härleds ur bilden**. Det är hela metodens noggrannhetstak.

Kod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(det skannern kör),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch-vägen och skalanpassningen),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Modellen {#the-model}

**Depth Anything V2**, relativ variant. Den förutsäger *relativt inversdjup*: ett disparitetsliknande fält som bara är korrekt upp till en okänd affin transform, `metric_disparity = a * predicted + b`, olika för varje bildruta. Nätverket är bra på det som är svårt att veta från en enda bild (relativ form, kanter, tunn struktur) och tyst om det det inte kan veta, nämligen skalan. Skalan kommer från någon annanstans - se [Kamerapose och skala](reconstruction-pose.md).

| Storlek | Hugging Face-id | Licens |
|---|---|---|
| **Liten** (standard) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - kommersiell användning tillåten |
| Bas | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - endast icke-kommersiell |
| Stor | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - endast icke-kommersiell |

En rekonstruktion ärver licensen för modellen som gjorde den. Liten är standard överallt just för att en skanning inte ska ha någon begränsning om inte någon väljer annat. De metriska varianterna (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) nämns i koden men används inte av skannern. Se [Modeller och licenser](models-and-licences.md).

## Bygga modellen {#building-the-model}

Skannern kör en ONNX-fil och importerar aldrig PyTorch. Filen måste göras en gång:

- **Från fönstret**: "Set up the depth model" (se [Skanningsfönstret](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), som kör kommandot nedan med `--size small`.
- **För hand**, i en miljö med PyTorch, `transformers` och `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Alternativ | Standard | Betydelse |
|---|---|---|
| `--size` | `small` | `small`, `base` eller `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | utfil |
| `--side` | `518` | fyrkantig indatastorlek; måste vara en multipel av 14 (ViT-patchstorleken); 518 = 14 x 37 är träningsupplösningen |
| `--opset` | `17` | ONNX-opset; 17 stöds brett av DirectML och CUDA |

Konverteraren gör följande:

- Hämtar checkpointet från Hugging Face (`AutoModelForDepthEstimation`).
- Lindar in modellen så att **ImageNet-normaliseringen finns inne i grafen**: modellen tar RGB i intervallet 0-255 som flyttal (`pixels`, form `batch x 3 x side x side`) och ger `inverse_depth`. Det finns exakt en kopia av medelvärdet och standardavvikelsen, så de inte kan glida ifrån checkpointet.
- **Fast rumslig storlek**, dynamisk batch. DirectML och TensorRT kompilerar per form; en dynamisk höjd och bredd skulle kompilera om vid första bildrutan i varje ny upplösning, en synlig hängning i en live-fångst.
- Exporterar via **TorchScript-vägen** (`dynamo=False`): dynamo-grafen föll på DirectML vid en Reshape-nod, och den skriver vikterna i en separat `.onnx.data`-fil. TorchScript-vägen ger en självständig fil.
- Skriver ut filen och dess storlek. Tracerns varningar om inbakade former är väntade.

Skannern letar efter `models/depth-*.onnx` och väljer efter licens, inte filnamn: Liten när den finns, en större storlek bara när den är den enda. Skanningsfönstrets rad anger filen, dess licens och eventuell annan modell som lämnades oanvänd.

## Köra den: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` bygger en ONNX Runtime-session, lat, med full grafoptimering, på den backend som stegen valde. CPU läggs till som reserv, så att en leverantör som misslyckas vid sessionsskapandet (en gammal drivrutin) ger en långsam skanning, inte en krasch. Se [Körmiljö](runtime.md#inference-backends).

- `warm_up()` bygger sessionen och kör en tom bildruta (första inferensen på en ny graf är flera gånger långsammare än i jämnt läge).
- `measure_throughput(frames)` tar tid på så många tomma bildrutor efter uppvärmningen; fönstret använder 6 och anger resultatet som vyer per sekund.

### Letterboxing, inte sträckning {#letterboxing-not-stretching}

Grafen tar en fast kvadrat; spelbilden är 16:9. Att pressa en bildruta till en kvadrat skulle ändra det synliga formatet på allt, och eftersom utdata är en geometrisk uppskattning skulle den fusioneras som verklig felaktig geometri. Så varje bildruta:

1. skalas för att passa kvadraten, med bibehållet bildförhållande (areainterpolation neråt, kubisk uppåt);
2. fylls med **mellangrått (114)** - svart eller vitt läses som en stark kant och läcker in ett falskt djupbrott i innehållet bredvid;
3. körs genom modellen;
4. utfyllnaden beskärs från förutsägelsen **innan** den skalas tillbaka (kubiskt) till bildrutans upplösning, så att marginalen aldrig läcker in i riktiga pixlar.

Resultatet är en `DepthMap` med `metric=False` i källbildrutans storlek.

## PyTorch-vägen {#the-pytorch-path}

`DepthEstimator` kör Hugging Face-modellen direkt (fp16 på CUDA, fp32 på CPU), batchad efter bildrutestorlek, varje förutsägelse skalad tillbaka bikubiskt. Skannern använder den inte. Det gör däremot den offline-`reconstruct`-kommandot (se [Offline-rekonstruktion](reconstruction-offline.md)), vilket är en anledning till att det kommandot behöver PyTorch och `transformers`.

## Från relativt till metriskt: `fit_scale` och `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Att göra förutsagt inversdjup till meter kräver den affina `scale * predicted + shift`. När ankare med känt djup finns (särdragspunkter triangulerade mellan kända poser, eller föregående bildrutas ankrade djup) löser `fit_scale` den:

- minsta kvadrat **i disparitet**, inte i djup. Nätverkets fel är ungefär jämnt i disparitet, medan några avlägsna ankare på djup (där en pixel disparitet är tiotals meter) skulle dominera;
- **iterativt viktad** (12 iterationer, Cauchy-liknande vikter `1 / (1 + (r / 3 MAD)^2)`), eftersom ankare bär grova extremvärden (en matchning på en rörlig bil, ett spårningsfel) och ett sådant ankare i en vanlig anpassning drar hela bildrutan;
- kräver minst 2 användbara ankare; rapporterar medianen av absolutresidualen och antalet inlier (residual inom 3 x medianen).

`AffineFit.apply` returnerar djup i meter med **+inf** för himlen. Den kontrollerar det förutsagda värdet såväl som det ankrade: en himmelspixel som förutsäger noll hamnar på `shift` (litet, positivt, ändligt) och skulle annars lägga varje himmelspixel på ett falskt skal på ett enda avstånd. Allt som förutsägs till eller under `1e-4` är himmel, oavsett vad anpassningen säger.

Fusionen behåller sedan bara djup mellan 0,35 m och 60 m (se [Fusion](reconstruction-fusion-and-texture.md#from-depth-to-points)).
