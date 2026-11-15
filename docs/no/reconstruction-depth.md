---
title: "Dybde"
nav_order: 3
lang: "no"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Dybde {#depth}

Det ene ekstern opptak ikke kan gi er geometri. Spillet kjenner dybden til hver piksel,
og den ligger i en buffer dette prosjektet bevisst ikke rører, så dybden **utledes fra bildet**.
Det er taket for nøyaktighet for hele tilnærmingen.

Kode: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(det skanneren kjører),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch-banen og skalatilpasningen),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Modellen {#the-model}

**Depth Anything V2**, relativ variant. Den predikerer *relativ invers dybde*: et disparitetslignende
felt som bare er riktig opp til en ukjent affin transformasjon,
`metrisk_disparitet = a * predikert + b`, forskjellig for hvert bilde. Nettverket er godt på det
som er vanskelig fra ett enkelt bilde (relativ form, kanter, tynn struktur) og taus om det det ikke
kan vite (skala). Skala kommer fra et annet sted - se [Kameraposisjon og skala](reconstruction-pose.md).

| Størrelse | Hugging Face-id | Lisens |
|---|---|---|
| **Liten** (standard) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - kommersiell bruk tillatt |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - bare ikke-kommersiell bruk |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - bare ikke-kommersiell bruk |

En rekonstruksjon arver lisensen til modellen som laget den. Liten er standard overalt nettopp slik at
en skanning ikke bærer noen begrensning med mindre noen velger annerledes. De metriske variantene
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) er nevnt i koden, men brukes ikke av
skanneren. Se [Modeller og lisenser](models-and-licences.md).

## Bygge modellen {#building-the-model}

Skanneren kjører en ONNX-fil og importerer aldri PyTorch. Filen må lages én gang:

- **Fra vinduet**: "Sett opp dybdemodellen" (se [Skanningsvinduet](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  som kjører kommandoen under med `--size small`.
- **For hånd**, i et miljø med PyTorch, `transformers` og `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Valg | Standard | Betydning |
|---|---|---|
| `--size` | `small` | `small`, `base` eller `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | utdatafil |
| `--side` | `518` | kvadratisk inndatastørrelse; må være et multiplum av 14 (ViT-patchstørrelsen); 518 = 14 x 37 er treningsoppløsningen |
| `--opset` | `17` | ONNX-opset; 17 er bredt støttet av DirectML og CUDA |

Det konverteringsprogrammet gjør:

- Laster ned sjekkpunktet fra Hugging Face (`AutoModelForDepthEstimation`).
- Pakker det inn slik at **ImageNet-normaliseringen er inne i grafen**: modellen tar RGB i
  området 0-255 som flyttall (`pixels`, form `batch x 3 x side x side`) og gir ut
  `inverse_depth`. Det finnes nøyaktig én kopi av gjennomsnittet og standardavviket, så de
  ikke kan drive fra sjekkpunktet.
- **Fast romlig størrelse**, dynamisk batch. DirectML og TensorRT kompilerer per form; en dynamisk
  høyde og bredde ville kompilert på nytt for første bilde i hver ny oppløsning, en synlig hakk i et
  live-opptak.
- Eksporterer via **TorchScript-banen** (`dynamo=False`): dynamo-grafen feilet på
  DirectML ved en Reshape-node, og den skriver vektene som en egen `.onnx.data`-fil. TorchScript-banen
  gir én selvstendig fil.
- Skriver ut filen og størrelsen. Sporerens advarsler om innbakte former er forventet.

Skanneren ser etter `models/depth-*.onnx` og velger etter lisens, ikke etter filnavn: Liten
hvis den finnes, en større størrelse bare når den er den eneste. Skannevinduets linje
nevner filen, lisensen og eventuelle andre modeller den lot være ubrukt.

## Kjøring: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` bygger én ONNX Runtime-sesjon, late, med full grafoptimalisering, på
backenden stigen valgte, med CPU lagt til som reserve, slik at en leverandør som feiler ved
sesjonsoppretting (en gammel driver) gir en treg skanning, ikke en krasj. Se
[Kjøretid og avhengigheter](runtime.md#inference-backends).

- `warm_up()` bygger sesjonen og kjører ett tomt bilde (første inferens på en fersk graf er flere
  ganger tregere enn i steady state).
- `measure_throughput(frames)` tar tiden på så mange tomme bilder etter oppvarmingen; vinduet bruker 6
  og oppgir resultatet som bilder per sekund.

### Letterboxing, ikke strekking {#letterboxing-not-stretching}

Grafen tar en fast kvadrat; spill er 16:9. Å presse et bilde inn i en kvadrat ville endre den
synlige formen på alt, og siden utdataene er et geometrisk anslag ville de bli sammensmeltet som
ekte, feil geometri. Så hvert bilde blir:

1. skalert til å passe kvadratet, med beholdt sideforhold (arealinterpolasjon ned, kubisk opp);
2. utfylt med **mellomgrå (114)** - svart eller hvitt leses som en sterk kant og lekker et falskt
   dybdesprang inn i innholdet ved siden av;
3. kjørt gjennom modellen;
4. utfyllingen beskjæres av prediksjonen **før** den skaleres tilbake (kubisk) til bildets
   oppløsning, så margen aldri lekker inn i ekte piksler.

Resultatet er et `DepthMap` med `metric=False` i kildebildets størrelse.

## PyTorch-banen {#the-pytorch-path}

`DepthEstimator` kjører Hugging Face-modellen direkte (fp16 på CUDA, fp32 på CPU), batchet etter
bildestørrelse, og hver prediksjon skaleres tilbake bikubisk. Skanneren bruker den ikke; den offline
`reconstruct`-kommandoen gjør det (se [Offline rekonstruksjon](reconstruction-offline.md)), og
det er en av grunnene til at den kommandoen trenger PyTorch og `transformers`.

## Fra relativ til metrisk: `fit_scale` og `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

For å gjøre predikert invers dybde om til meter trengs den affine `scale * predikert + shift`. Når
ankre med kjent dybde finnes (trekkpunkter triangulert mellom kjente posisjoner, eller forrige bildes
ankrede dybde), løser `fit_scale` den:

- minste kvadrater **i disparitet**, ikke i dybde - nettverkets feil er omtrent jevn i disparitet,
  mens i dybde ville noen få fjerne ankre (der én piksel disparitet er titalls meter) dominere;
- **iterativt revektet** (12 iterasjoner, Cauchy-lignende vekter `1 / (1 + (r / 3 MAD)^2)`),
  fordi ankre bærer grove avvik (et treff på en bevegelig bil, et sporingsfeil), og ett slikt anker
  i en enkel tilpasning drar hele bildet med seg;
- trenger minst 2 brukbare anker; rapporterer den median absolutte residualen og antallet
  innliggere (residual innenfor 3 x medianen).

`AffineFit.apply` gir dybde i meter med **+inf** for himmelen. Den sjekker den predikerte verdien
så vel som den ankrede: en himmelpiksel som predikerer null kommer ut på `shift` - liten, positiv,
endelig - og ville ellers lande alle himmelpiksler på et falskt skall i én avstand. Alt som
predikeres til eller under `1e-4` er himmel, uansett hva tilpasningen sier.

Sammensmeltingen beholder deretter bare dybder mellom 0,35 m og 60 m (se
[Sammensmelting](reconstruction-fusion-and-texture.md#from-depth-to-points)).
