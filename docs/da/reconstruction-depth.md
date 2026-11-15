---
title: "Dybde"
nav_order: 3
lang: "da"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Dybde {#depth}

Det ene, en ekstern optagelse ikke kan give, er geometri. Spillet kender dybden for hver pixel, og den ligger i en buffer, dette projekt bevidst ikke rører. Dybden **udledes af billedet**. Det er loftet for nøjagtigheden i hele fremgangsmåden.

Kode: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(det scanneren kører),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch-stien og skalatilpasningen),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Modellen {#the-model}

**Depth Anything V2**, den relative variant. Den forudsiger *relativ invers dybde*: et felt, der ligner ulighed, og som kun er korrekt op til en ukendt affin transformation, `metric_disparity = a * predicted + b`, forskellig for hvert billede. Netværket er godt til det, der er svært ud fra ét billede (relativ form, kanter, tynd struktur), og tavst om det, det ikke kan vide (skala). Skalaen kommer et andet sted fra - se [Kameraposition og skala](reconstruction-pose.md).

| Størrelse | Hugging Face-id | Licens |
|---|---|---|
| **Small** (standard) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - kommerciel brug tilladt |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - kun ikke-kommerciel |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - kun ikke-kommerciel |

En rekonstruktion arver licensen for den model, der lavede den. Small er standard alle steder, netop så en scanning ikke bærer nogen begrænsning, medmindre nogen vælger det andet. De metriske varianter (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) er nævnt i koden, men bruges ikke af scanneren. Se [Modeller og licenser](models-and-licences.md).

## Opbygning af modellen {#building-the-model}

Scanneren kører en ONNX-fil og importerer aldrig PyTorch. Filen skal laves én gang:

- **Fra vinduet**: "Set up the depth model" (se [Scanvinduet](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), som kører kommandoen nedenfor med `--size small`.
- **I hånden**, i et miljø med PyTorch, `transformers` og `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `--size` | `small` | `small`, `base` eller `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | outputfil |
| `--side` | `518` | kvadratisk inputstørrelse; skal være et multiplum af 14 (ViT-patchstørrelsen); 518 = 14 x 37 er træningsopløsningen |
| `--opset` | `17` | ONNX-opset; 17 er bredt understøttet af DirectML og CUDA |

Det konverteren gør:

- Henter checkpointet fra Hugging Face (`AutoModelForDepthEstimation`).
- Pakker det ind, så **ImageNet-normaliseringen er inde i grafen**: modellen tager RGB i området 0-255 som decimaltal (`pixels`, form `batch x 3 x side x side`) og giver `inverse_depth` ud. Der er præcis én kopi af middelværdien og standardafvigelsen, så de ikke kan afvige fra checkpointet.
- **Fast rumlig størrelse**, dynamisk batch. DirectML og TensorRT kompilerer pr. form; en dynamisk højde og bredde ville kompilere om ved første billede i hver ny opløsning, en synlig hakken i en live-optagelse.
- Eksporterer via **TorchScript-stien** (`dynamo=False`): dynamo-grafen fejlede på DirectML ved en Reshape-node, og den skriver vægtene i en separat `.onnx.data`-fil. TorchScript-stien giver én selvstændig fil.
- Skriver filen og dens størrelse ud. Tracerens advarsler om indbagte former er forventede.

Scanneren leder efter `models/depth-*.onnx` og vælger efter licens, ikke efter filnavn: Small, når den findes, og en større størrelse kun, når den er den eneste. Scanvinduets linje navngiver filen, dens licens og eventuelle andre modeller, den lod være ubrugt.

## Kørsel: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` bygger én ONNX Runtime-session, dovent, med fuld grafoptimering, på den backend stigen valgte, med CPU tilføjet som reserve, så en udbyder, der fejler ved oprettelse af sessionen (en gammel driver), betyder en langsom scanning, ikke et nedbrud. Se [Kørsel og afhængigheder](runtime.md#inference-backends).

- `warm_up()` bygger sessionen og kører ét tomt billede (den første inferens på en frisk graf er flere gange langsommere end den stabile tilstand).
- `measure_throughput(frames)` tager tid på så mange tomme billeder efter opvarmningen; vinduet bruger 6 og angiver resultatet som billeder pr. sekund.

### Letterboxing, ikke strækning {#letterboxing-not-stretching}

Grafen tager et fast kvadrat; spilbilledet er 16:9. At presse et billede ind i et kvadrat ville ændre udseendet af alt, og da outputtet er et geometrisk estimat, ville det blive fusioneret som reel forkert geometri. Så hvert billede bliver:

1. skaleret, så det passer i kvadratet, med bevaret billedforhold (arealinterpolation ned, kubisk op);
2. polstret med **mellemgråt (114)** - sort eller hvid læses som en stærk kant og lækker en falsk dybdespringning ind i indholdet ved siden af;
3. kørt gennem modellen;
4. polstringen beskæres fra forudsigelsen **før** den skaleres tilbage (kubisk) til billedets opløsning, så marginen aldrig løber ind i de rigtige pixels.

Resultatet er en `DepthMap` med `metric=False` i kildebilledets størrelse.

## PyTorch-stien {#the-pytorch-path}

`DepthEstimator` kører Hugging Face-modellen direkte (fp16 på CUDA, fp32 på CPU), batchet efter billedstørrelse, hver forudsigelse skaleret tilbage bikubisk. Scanneren bruger den ikke; den offline `reconstruct`-kommando gør (se [Offline-rekonstruktion](reconstruction-offline.md)), hvilket er én grund til, at den kommando kræver PyTorch og `transformers`.

## Fra relativ til metrisk: `fit_scale` og `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

At omregne forudsagt invers dybde til meter kræver den affine `scale * predicted + shift`. Når der findes ankre med kendt dybde (featurepunkter trianguleret mellem kendte positioner, eller det forrige billedes ankrede dybde), løser `fit_scale` den:

- mindste kvadraters metode **i uligheden**, ikke i dybden - netværkets fejl er nogenlunde ens i ulighed, mens få fjerne ankre i dybde (hvor én pixel i ulighed er titals meter) ville dominere;
- **iterativt vægtet** (12 iterationer, Cauchy-agtige vægte `1 / (1 + (r / 3 MAD)^2)`), fordi ankre bærer grove udliggere (et match på en kørende bil, et sporingsglitch), og ét sådant anker i en simpel tilpasning trækker hele billedet med sig;
- kræver mindst 2 brugbare ankre; rapporterer den mediane absolutte rest og antallet af inliers (rest inden for 3 x medianen).

`AffineFit.apply` returnerer dybde i meter med **+inf** for himmel. Den tjekker den forudsagte værdi såvel som den ankrede: en himmelpixel, der forudsiger nul, kommer ud på `shift` - lille, positiv, endelig - og ville ellers lande alle himmelpixels på en falsk skal i én afstand. Alt, der forudsiges til eller under `1e-4`, er himmel, uanset hvad tilpasningen siger.

Fusion beholder så kun dybder mellem 0,35 m og 60 m (se [Fusion](reconstruction-fusion-and-texture.md#from-depth-to-points)).
