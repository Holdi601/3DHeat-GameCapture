---
title: "Adâncimea"
nav_order: 3
lang: "ro"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Adâncimea {#depth}

Un lucru pe care captura externă nu îl poate da este geometria. Jocul cunoaște adâncimea fiecărui pixel și ea stă într-un buffer în care acest proiect se abține în mod deliberat să intervină, deci adâncimea este **dedusă din imagine**. Acesta este plafonul de precizie al întregii abordări.

Cod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(ce rulează scanerul),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(calea PyTorch și potrivirea scării),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Modelul {#the-model}

**Depth Anything V2**, varianta relativă. Prezice *inversa adâncimii relative*: un câmp asemănător disparității, corect doar până la o transformare afină necunoscută, `metric_disparity = a * predicted + b`, diferită pentru fiecare cadru. Rețeaua este bună la ce este greu de știut dintr-o singură imagine (forma relativă, muchiile, structura subțire) și tace în privința a ce nu poate ști (scara). Scara vine din altă parte - vezi [Poziția camerei și scara](reconstruction-pose.md).

| Mărime | Identificator Hugging Face | Licență |
|---|---|---|
| **Small** (implicit) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - utilizare comercială permisă |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - doar necomercial |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - doar necomercial |

O reconstrucție moștenește licența modelului care a făcut-o. Small este implicit peste tot tocmai ca o scanare să nu aibă nicio restricție, decât dacă cineva alege altfel. Variantele metrice (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) sunt numite în cod, dar nu sunt folosite de scaner. Vezi [Modele și licențe](models-and-licences.md).

## Construirea modelului {#building-the-model}

Scanerul rulează un fișier ONNX și nu importă niciodată PyTorch. Fișierul trebuie făcut o singură dată:

- **Din fereastră**: „Set up the depth model" (vezi [Fereastra de scanare](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), care rulează comanda de mai jos cu `--size small`.
- **Manual**, într-un mediu cu PyTorch, `transformers` și `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opțiune | Implicit | Înțeles |
|---|---|---|
| `--size` | `small` | `small`, `base` sau `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | fișierul de ieșire |
| `--side` | `518` | dimensiunea pătrată a intrării; trebuie să fie multiplu de 14 (dimensiunea petecului ViT); 518 = 14 x 37 este rezoluția de antrenare |
| `--opset` | `17` | setul de operatori ONNX; 17 este bine suportat de DirectML și CUDA |

Ce face convertorul:

- Descarcă punctul de control de pe Hugging Face (`AutoModelForDepthEstimation`).
- Îl învelește astfel încât **normalizarea ImageNet să fie în interiorul grafului**: modelul primește RGB în intervalul 0-255 ca float (`pixels`, forma `lot x 3 x side x side`) și scoate `inverse_depth`. Există exact o copie a mediei și a abaterii standard, deci nu pot devia de la punctul de control.
- **Dimensiune spațială fixă**, lot dinamic. DirectML și TensorRT compilează pentru fiecare formă; o înălțime și o lățime dinamice ar recompila la primul cadru al fiecărei noi rezoluții, o pauză vizibilă într-o captură în direct.
- Exportă pe **calea TorchScript** (`dynamo=False`): graful dynamo a eșuat pe DirectML la un nod Reshape, iar scrie greutățile într-un fișier separat `.onnx.data`. Calea TorchScript produce un singur fișier autonom.
- Afișează fișierul și dimensiunea lui. Avertismentele trasorului despre formele fixate în graf sunt normale.

Scanerul caută `models/depth-*.onnx` și alege după licență, nu după numele fișierului: Small ori de câte ori există, o mărime mai mare doar când este singura. Linia ferestrei de scanare numește fișierul, licența lui și orice alt model pe care l-a lăsat nefolosit.

## Rulare: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` construiește o singură sesiune ONNX Runtime, leneș, cu optimizare completă a grafului, pe backend-ul ales de scară, cu CPU adăugat ca rezervă, astfel încât un furnizor care eșuează la crearea sesiunii (un driver vechi) înseamnă o scanare lentă, nu un crash. Vezi [Rulare și backend-uri de inferență](runtime.md#inference-backends).

- `warm_up()` construiește sesiunea și rulează un cadru gol (prima inferență pe un graf nou este de câteva ori mai lentă decât regimul stabil).
- `measure_throughput(frames)` cronometrează atâtea cadre goale după încălzire; fereastra folosește 6 și afișează rezultatul ca vederi pe secundă.

### Letterboxing, nu întindere {#letterboxing-not-stretching}

Graful primește un pătrat fix; jocul este 16:9. Turtirea unui cadru într-un pătrat ar schimba forma aparentă a tuturor lucrurilor, iar cum rezultatul este o estimare geometrică, ar fi fuzionat ca geometrie greșită reală. Deci fiecare cadru este:

1. scalat ca să încapă în pătrat, păstrându-și raportul de aspect (interpolare de arie la micșorare, cubică la mărire);
2. completat cu **gri mediu (114)** - negrul sau albul se citește ca o muchie puternică și scurge o discontinuitate falsă de adâncime în conținutul de lângă el;
3. trecut prin model;
4. completarea este decupată din predicție **înainte** de a fi readus (cubic) la rezoluția cadrului, astfel încât marginea să nu se scurgă în pixelii reali.

Rezultatul este un `DepthMap` cu `metric=False` la dimensiunea cadrului sursă.

## Calea PyTorch {#the-pytorch-path}

`DepthEstimator` rulează direct modelul Hugging Face (fp16 pe CUDA, fp32 pe CPU), în loturi după dimensiunea cadrului, fiecare predicție fiind readusă bicubic. Scanerul nu o folosește; comanda offline `reconstruct` o folosește (vezi [Reconstrucție offline](reconstruction-offline.md)), ceea ce este unul dintre motivele pentru care această comandă are nevoie de PyTorch și `transformers`.

## De la relativ la metric: `fit_scale` și `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Transformarea inversei adâncimii prezise în metri are nevoie de afinul `scale * predicted + shift`. Când sunt disponibile ancore de adâncime cunoscută (trăsături triangulate între poziții cunoscute, sau adâncimea ancorată a cadrului anterior), `fit_scale` o rezolvă:

- cele mai mici pătrate **în disparitate**, nu în adâncime - eroarea rețelei este cam uniformă în disparitate, în timp ce în adâncime câteva ancore îndepărtate (unde un pixel de disparitate înseamnă zeci de metri) ar domina;
- **reponderat iterativ** (12 iterații, ponderi de tip Cauchy `1 / (1 + (r / 3 MAD)^2)`), pentru că ancorele au valori aberante grosolane (o potrivire pe o mașină în mișcare, o eroare de urmărire) și o singură astfel de ancoră într-o potrivire simplă trage tot cadrul;
- are nevoie de cel puțin 2 ancore utilizabile; raportează reziduul absolut median și numărul de inliere (reziduu sub 3 x mediana).

`AffineFit.apply` întoarce adâncimea în metri, cu **+inf** pentru cer. Verifică și valoarea prezisă, nu doar cea ancorată: un pixel de cer care prezice zero iese la `shift` - mic, pozitiv, finit - și ar pune altfel fiecare pixel de cer pe o coajă fantomă la o singură distanță. Orice prezis la sau sub `1e-4` este cer, indiferent ce spune potrivirea.

Fuziunea păstrează apoi doar adâncimile între 0,35 m și 60 m (vezi [Fuziune](reconstruction-fusion-and-texture.md#from-depth-to-points)).
