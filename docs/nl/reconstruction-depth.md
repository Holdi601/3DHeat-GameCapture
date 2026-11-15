---
title: "Diepte"
nav_order: 3
lang: "nl"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Diepte {#depth}

Wat externe opname nooit kan geven, is geometrie. Het spel kent de diepte van elke pixel en die zit in een buffer die dit project bewust niet aanraakt, dus wordt de diepte **afgeleid uit het beeld**. Dat is het nauwkeurigheidsplafond van de hele aanpak.

Code: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py) (wat de scanner draait), [`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py) (het PyTorch-pad en de schaalfit), [`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Het model {#the-model}

**Depth Anything V2**, de relatieve variant. Het voorspelt *relatieve inverse diepte*: een disparity-achtig veld dat alleen juist is tot op een onbekende affiene transformatie, `metric_disparity = a * predicted + b`, en anders voor elk frame. Het netwerk is goed in wat moeilijk is uit één beeld (relatieve vorm, randen, dunne structuren) en stil over wat het niet kan weten (schaal). De schaal komt van elders - zie [Cameraposities en schaal](reconstruction-pose.md).

| Grootte | Hugging Face-id | Licentie |
|---|---|---|
| **Small** (standaard) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - commercieel gebruik toegestaan |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - alleen niet-commercieel |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - alleen niet-commercieel |

Een reconstructie erft de licentie van het model dat haar maakte. Small is overal de standaard, precies zodat een scan geen beperking heeft tenzij iemand iets anders kiest. De metrische varianten (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) staan in de code maar worden door de scanner niet gebruikt. Zie [Modellen en licenties](models-and-licences.md).

## Het model bouwen {#building-the-model}

De scanner draait een ONNX-bestand en importeert nooit PyTorch. Het bestand moet één keer worden gemaakt:

- **Vanuit het venster**: "Set up the depth model" (zie [Het scanvenster](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), wat het commando hieronder draait met `--size small`.
- **Met de hand**, in een omgeving met PyTorch, `transformers` en `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Optie | Standaard | Betekenis |
|---|---|---|
| `--size` | `small` | `small`, `base` of `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | uitvoerbestand |
| `--side` | `518` | vierkante invoergrootte; moet een veelvoud van 14 zijn (de patchgrootte van de ViT); 518 = 14 x 37 is de trainingsresolutie |
| `--opset` | `17` | ONNX-opset; 17 wordt breed ondersteund door DirectML en CUDA |

Wat de converter doet:

- Downloadt het checkpoint van Hugging Face (`AutoModelForDepthEstimation`).
- Verpakt het zo dat de **ImageNet-normalisatie binnen de graaf zit**: het model neemt RGB in het bereik 0-255 als float (`pixels`, vorm `batch x 3 x side x side`) en levert `inverse_depth`. Er is precies één kopie van het gemiddelde en de standaardafwijking, dus die kunnen niet afwijken van het checkpoint.
- **Vaste ruimtelijke grootte**, dynamische batch. DirectML en TensorRT compileren per vorm; een dynamische hoogte en breedte zou bij het eerste frame van elke nieuwe resolutie opnieuw compileren, een zichtbare stilstand in een live opname.
- Exporteert via het **TorchScript-pad** (`dynamo=False`): de dynamo-graaf faalde op DirectML bij een Reshape-knoop, en die schrijft de gewichten als apart `.onnx.data`-bestand. Het TorchScript-pad levert één op zichzelf staand bestand.
- Drukt het bestand en de grootte af. De waarschuwingen van de tracer over ingebakken vormen zijn normaal.

De scanner zoekt naar `models/depth-*.onnx` en kiest op licentie, niet op bestandsnaam: Small wanneer die er is, een grotere grootte alleen als het de enige is. De regel van het scanvenster noemt het bestand, zijn licentie en elk ander model dat het ongebruikt liet.

## Draaien: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` bouwt één ONNX Runtime-sessie, lui, met volledige graafoptimalisatie, op de backend die de ladder koos, met CPU als terugval zodat een provider die bij het aanmaken van de sessie faalt (een oud stuurprogramma) een trage scan betekent, geen crash. Zie [Runtime en afhankelijkheden](runtime.md#inference-backends).

- `warm_up()` bouwt de sessie en draait één leeg frame (de eerste inferentie op een verse graaf is meerdere keren trager dan de stationaire toestand).
- `measure_throughput(frames)` meet zoveel lege frames na de opwarming; het venster gebruikt er 6 en geeft het resultaat als beelden per seconde.

### Letterboxen, niet uitrekken {#letterboxing-not-stretching}

De graaf neemt een vast vierkant; gameplay is 16:9. Een frame in een vierkant persen zou de schijnbare vorm van alles veranderen, en omdat de uitvoer een geometrische schatting is, zou het als echte foute geometrie worden samengevoegd. Dus wordt elk frame:

1. geschaald om in het vierkant te passen, met behoud van de beeldverhouding (gebiedsinterpolatie naar beneden, kubisch naar boven);
2. opgevuld met **middelgrijs (114)** - zwart of wit leest als een sterke rand en lekt een valse dieptesprong in de inhoud ernaast;
3. door het model gehaald;
4. de opvulling wordt van de voorspelling afgesneden **vóórdat** die kubisch terug wordt geschaald naar de resolutie van het frame, zodat de marge nooit in echte pixels bloedt.

Het resultaat is een `DepthMap` met `metric=False` op de grootte van het bronframe.

## Het PyTorch-pad {#the-pytorch-path}

`DepthEstimator` draait het Hugging Face-model rechtstreeks (fp16 op CUDA, fp32 op CPU), gebundeld per framegrootte, elke voorspelling bicubisch teruggeschaald. De scanner gebruikt het niet; het offline commando `reconstruct` wel (zie [Offline reconstructie](reconstruction-offline.md)), en dat is een van de redenen dat dat commando PyTorch en `transformers` nodig heeft.

## Van relatief naar metrisch: `fit_scale` en `AffineFit` {#from-relative-to-metric-fit_scale-and-affinefit}

Om voorspelde inverse diepte in meters om te zetten, is de affiene `scale * predicted + shift` nodig. Wanneer ankers met bekende diepte beschikbaar zijn (featurepunten die getrianguleerd zijn tussen bekende posities, of de geankerde diepte van het vorige frame), lost `fit_scale` die op:

- kleinste kwadraten **in disparity**, niet in diepte - de fout van het netwerk is ruwweg gelijkmatig in disparity, terwijl in diepte een paar verre ankers (waar één pixel disparity tientallen meters is) de boventoon zouden voeren;
- **iteratief herwogen** (12 iteraties, Cauchy-achtige gewichten `1 / (1 + (r / 3 MAD)^2)`), omdat ankers grove uitschieters dragen (een match op een bewegende auto, een trackingfout) en één zo'n anker in een gewone fit het hele frame meesleept;
- heeft minstens 2 bruikbare ankers nodig; meldt de mediane absolute residu en het aantal inliers (residu binnen 3 x de mediaan).

`AffineFit.apply` levert diepte in meters met **+inf** voor de lucht. Het controleert de voorspelde waarde net zo goed als de geankerde: een lucht-pixel die nul voorspelt, komt uit op `shift` - klein, positief, eindig - en zou anders alle luchtpixels op een schijnschil op één afstand zetten. Alles wat op of onder `1e-4` wordt voorspeld, is lucht, wat de fit ook zegt.

Samenvoegen houdt daarna alleen dieptes tussen 0,35 m en 60 m aan (zie [Samenvoegen](reconstruction-fusion-and-texture.md#from-depth-to-points)).
