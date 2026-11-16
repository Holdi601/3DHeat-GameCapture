---
title: Profondità
nav_order: 3
lang: "it"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Profondità {#depth}

Ciò che la cattura esterna non può dare è la geometria. Il gioco conosce la profondità di ogni
pixel e la tiene in un buffer che questo progetto deliberatamente non tocca, quindi la profondità
viene **dedotta dall'immagine**. Questo è il limite di precisione dell'intero approccio.

Codice: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(quello che esegue lo scanner),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(il percorso PyTorch e l'adattamento della scala),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Il modello {#the-model}

**Depth Anything V2**, variante relativa. Prevede la *profondità inversa relativa*: un campo simile
alla disparità, corretto solo a meno di una trasformazione affine sconosciuta,
`metric_disparity = a * predicted + b`, diversa per ogni fotogramma. La rete è brava in ciò che è
difficile da un'unica immagine (forma relativa, bordi, strutture sottili) e tace su ciò che non
può sapere (la scala). La scala arriva da un'altra parte - vedi [Posa della camera e scala](reconstruction-pose.md).

| Dimensione | Id su Hugging Face | Licenza |
|---|---|---|
| **Small** (predefinito) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - uso commerciale consentito |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - solo non commerciale |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - solo non commerciale |

Una ricostruzione eredita la licenza del modello che l'ha prodotta. Small è il predefinito
ovunque proprio perché una scansione non porti alcuna restrizione, a meno che qualcuno non scelga
diversamente. Le varianti metriche (`Depth-Anything-V2-Metric-Outdoor-Small-hf`,
`...-Indoor-Small-hf`) sono nominate nel codice ma non usate dallo scanner. Vedi
[Modelli e licenze](models-and-licences.md).

## Costruire il modello {#building-the-model}

Lo scanner esegue un file ONNX e non importa mai PyTorch. Il file va creato una volta sola:

- **Dalla finestra**: "Set up the depth model" (vedi [La finestra di scansione](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  che esegue il comando sotto con `--size small`.
- **A mano**, in un ambiente con PyTorch, `transformers` e `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opzione | Predefinito | Significato |
|---|---|---|
| `--size` | `small` | `small`, `base` o `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | file di output |
| `--side` | `518` | dimensione quadrata dell'ingresso; deve essere un multiplo di 14 (la dimensione della patch ViT); 518 = 14 x 37 è la risoluzione di addestramento |
| `--opset` | `17` | opset ONNX; 17 è ampiamente supportato da DirectML e CUDA |

Cosa fa il convertitore:

- Scarica il checkpoint da Hugging Face (`AutoModelForDepthEstimation`).
- Lo avvolge in modo che la **normalizzazione ImageNet sia dentro il grafo**: il modello riceve
  RGB nell'intervallo 0-255 come float (`pixels`, forma `batch x 3 x side x side`) e restituisce
  `inverse_depth`. C'è esattamente una copia della media e della deviazione standard, quindi non
  possono discostarsi dal checkpoint.
- **Dimensione spaziale fissa**, batch dinamico. DirectML e TensorRT compilano per forma; un'altezza
  e una larghezza dinamiche ricompilerebbero al primo fotogramma di ogni nuova risoluzione, un
  blocco visibile in una cattura in diretta.
- Esporta tramite il **percorso TorchScript** (`dynamo=False`): il grafo dynamo falliva su
  DirectML in un nodo Reshape, e scrive i pesi in un file `.onnx.data` separato. Il percorso
  TorchScript produce un file unico e autosufficiente.
- Stampa il file e la sua dimensione. Gli avvisi del tracciatore sulle forme fissate nel codice
  sono previsti.

Lo scanner cerca `models/depth-*.onnx` e sceglie in base alla licenza, non al nome del file: Small
ogni volta che c'è, una dimensione maggiore solo quando è l'unica. La riga della finestra di
scansione indica il file, la sua licenza e ogni altro modello lasciato inutilizzato.

## Esecuzione: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` crea una sessione ONNX Runtime, al primo uso, con piena ottimizzazione del
grafo, sul backend scelto dalla graduatoria, con la CPU aggiunta come ripiego così che un provider che
fallisce alla creazione della sessione (un driver vecchio) significhi una scansione lenta, non un
crash. Vedi [Runtime e dipendenze](runtime.md#inference-backends).

- `warm_up()` crea la sessione ed esegue un fotogramma vuoto (la prima inferenza su un grafo
  nuovo è diverse volte più lenta dello stato stabile).
- `measure_throughput(frames)` cronometra quel numero di fotogrammi vuoti dopo il riscaldamento;
  la finestra usa 6 e riporta il risultato come viste al secondo.

### Letterbox, non deformazione {#letterboxing-not-stretching}

Il grafo accetta un quadrato fisso; il gioco è 16:9. Schiacciare un fotogramma in un quadrato
cambierebbe la forma apparente di tutto, e poiché l'output è una stima geometrica verrebbe fuso
come geometria reale ma sbagliata. Quindi ogni fotogramma viene:

1. scalato per entrare nel quadrato, mantenendo il rapporto d'aspetto (interpolazione per area quando si riduce,
   cubica quando si ingrandisce);
2. riempito con **grigio medio (114)** - il nero o il bianco si leggono come un bordo forte e
   trascinano una falsa discontinuità di profondità nel contenuto accanto;
3. passato al modello;
4. il riempimento viene ritagliato dalla previsione **prima** del ridimensionamento cubico alla
   risoluzione del fotogramma, così il margine non sconfina nei pixel reali.

Il risultato è un `DepthMap` con `metric=False` alla dimensione del fotogramma sorgente.

## Il percorso PyTorch {#the-pytorch-path}

`DepthEstimator` esegue direttamente il modello di Hugging Face (fp16 su CUDA, fp32 su CPU), in
batch per dimensione del fotogramma, con ogni previsione riportata alla dimensione originale in
modo bicubico. Lo scanner non lo usa; lo usa il comando offline `reconstruct` (vedi
[Ricostruzione offline](reconstruction-offline.md)), che è uno dei motivi per cui quel comando
richiede PyTorch e `transformers`.

## Da relativo a metrico: `fit_scale` e `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Trasformare la profondità inversa prevista in metri richiede l'affine `scale * predicted + shift`.
Quando sono disponibili ancore di profondità nota (punti caratteristici triangolati tra pose note,
o la profondità ancorata del fotogramma precedente), `fit_scale` la risolve:

- minimi quadrati **in disparità**, non in profondità - l'errore della rete è più o meno uniforme in
  disparità, mentre in profondità alcune ancore lontane (dove un pixel di disparità vale decine di
  metri) dominerebbero;
- **pesate iterativamente** (12 iterazioni, pesi in stile Cauchy `1 / (1 + (r / 3 MAD)^2)`), perché
  le ancore contengono valori anomali grossolani (una corrispondenza su un'auto in movimento, un
  errore di tracciamento) e una sola di queste in un adattamento semplice trascina l'intero
  fotogramma;
- richiede almeno 2 ancore utilizzabili; riporta l'errore assoluto mediano residuo e il numero di
  inlier (residuo entro 3 x la mediana).

`AffineFit.apply` restituisce la profondità in metri con **+inf** per il cielo. Controlla il valore
previsto oltre a quello ancorato: un pixel di cielo che prevede zero uscirebbe a `shift` - piccolo,
positivo, finito - e porterebbe altrimenti ogni pixel di cielo su un guscio fantasma a una
distanza. Tutto ciò che è previsto a `1e-4` o meno è cielo, qualunque cosa dica l'adattamento.

La fusione tiene poi solo profondità tra 0,35 m e 60 m (vedi
[Fusione](reconstruction-fusion-and-texture.md#from-depth-to-points)).
