---
title: "Dubina"
nav_order: 3
lang: "bs"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Dubina {#depth}

Jedino što vanjsko snimanje ne može dati je geometrija. Igra zna dubinu svakog piksela i
ona je u međuspremniku koji ovaj projekat namjerno ne dira, pa se dubina **zaključuje iz
slike**. To je gornja granica tačnosti cijelog pristupa.

Kod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(ono što skener pokreće),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch putanja i podešavanje skale),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, relativna varijanta. Predviđa *relativnu inverznu dubinu*: polje nalik disparitetu,
tačno samo do nepoznate afine transformacije,
`metric_disparity = a * predicted + b`, različite za svaki kadar. Mreža je dobra u onome što
je teško iz jedne slike (relativni oblik, ivice, tanke strukture), a šuti o onome što ne može
znati (skala). Skala dolazi odnekud drugdje - pogledajte [Poza kamere i skala](reconstruction-pose.md).

| Veličina | Hugging Face id | Licenca |
|---|---|---|
| **Small** (zadano) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - komercijalna upotreba dozvoljena |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - samo nekomercijalno |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - samo nekomercijalno |

Rekonstrukcija nasljeđuje licencu modela koji ju je napravio. Small je svugdje zadan
upravo zato da skeniranje ne nosi nikakvo ograničenje osim ako neko ne odabere drugačije.
Metričke varijante (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) su
navedene u kodu, ali ih skener ne koristi. Pogledajte [Modeli i licence](models-and-licences.md).

## Izgradnja modela {#building-the-model}

Skener pokreće ONNX datoteku i nikad ne uvozi PyTorch. Datoteku treba napraviti jednom:

- **Iz prozora**: "Set up the depth model" (pogledajte [Prozor za skeniranje](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  koji pokreće donju komandu s `--size small`.
- **Ručno**, u okruženju s PyTorchom, `transformers` i `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opcija | Zadano | Značenje |
|---|---|---|
| `--size` | `small` | `small`, `base` ili `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | izlazna datoteka |
| `--side` | `518` | kvadratna ulazna veličina; mora biti višekratnik od 14 (veličina ViT zakrpe); 518 = 14 x 37 je rezolucija treniranja |
| `--opset` | `17` | ONNX opset; 17 je široko podržan u DirectML-u i CUDA-i |

Šta konverter radi:

- Preuzima checkpoint s Hugging Facea (`AutoModelForDepthEstimation`).
- Omotava ga tako da je **ImageNet normalizacija unutar grafa**: model prima RGB u rasponu
  0-255 kao float (`pixels`, oblik `batch x 3 x side x side`) i daje
  `inverse_depth`. Postoji tačno jedna kopija srednje vrijednosti i standardne devijacije, pa ne mogu
  odstupiti od checkpointa.
- **Fiksna prostorna veličina**, dinamična serija. DirectML i TensorRT kompiliraju po obliku; dinamična
  visina i širina bi rekompilirale na prvom kadru svake nove rezolucije, što je vidljivo
  zastajkivanje u snimanju uživo.
- Izvozi preko **TorchScript putanje** (`dynamo=False`): dynamo graf je pao na
  DirectML-u na Reshape čvoru, a težine zapisuje kao zasebnu `.onnx.data` datoteku.
  TorchScript putanja daje jednu samostalnu datoteku.
- Ispisuje datoteku i njenu veličinu. Upozorenja trasera o ugrađenim oblicima su očekivana.

Skener traži `models/depth-*.onnx` i bira prema licenci, a ne prema imenu datoteke: Small
kad god postoji, veća veličina samo ako je jedina. Linija prozora za skeniranje
imenuje datoteku, njenu licencu i svaki drugi model koji je ostavila neiskorišten.

## Pokretanje: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` gradi jednu ONNX Runtime sesiju, lijeno, s punom optimizacijom grafa, na
pozadini koju je odabrala ljestvica, s CPU-om dodanim kao rezervom, pa pružatelj koji ne uspije pri
kreiranju sesije (stari drajver) znači sporo skeniranje, a ne pad. Pogledajte
[Runtime i zavisnosti](runtime.md#inference-backends).

- `warm_up()` gradi sesiju i pokreće jedan prazan kadar (prvi zaključak na svježem
  grafu je nekoliko puta sporiji od ustaljenog stanja).
- `measure_throughput(frames)` mjeri toliko praznih kadrova nakon zagrijavanja; prozor koristi 6
  i navodi rezultat kao poglede u sekundi.

### Letterbox, ne razvlačenje {#letterboxing-not-stretching}

Graf prima fiksni kvadrat; igra je 16:9. Stiskanje kadra u kvadrat promijenilo bi
prividni oblik svega, a pošto je izlaz geometrijska procjena, to bi se
spojilo kao prava pogrešna geometrija. Zato se svaki kadar:

1. skalira da stane u kvadrat, uz očuvanje omjera stranica (interpolacija po površini pri smanjenju, kubna pri povećanju);
2. dopunjava **srednje sivom (114)** - crna ili bijela se čita kao jaka ivica i prelijeva lažni
   prekid dubine u sadržaj pored;
3. propušta kroz model;
4. dopuna se odrezuje s predviđanja **prije** vraćanja (kubno) na rezoluciju
   kadra, tako da margina nikad ne prelijeva u prave piksele.

Rezultat je `DepthMap` s `metric=False` veličine izvornog kadra.

## PyTorch putanja {#the-pytorch-path}

`DepthEstimator` pokreće Hugging Face model direktno (fp16 na CUDA-i, fp32 na CPU-u), u serijama prema
veličini kadra, svako predviđanje vraćeno bikubično. Skener je ne koristi; offline
komanda `reconstruct` koristi (pogledajte [Offline rekonstrukcija](reconstruction-offline.md)), što je
jedan od razloga zašto ta komanda treba PyTorch i `transformers`.

## Od relativnog do metričkog: `fit_scale` i `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Pretvaranje predviđene inverzne dubine u metre traži afinu `scale * predicted + shift`. Kada su
dostupna sidra poznate dubine (karakteristične tačke triangulirane između poznatih poza, ili
sidrena dubina prethodnog kadra), `fit_scale` to rješava:

- metoda najmanjih kvadrata **u disparitetu**, ne u dubini - greška mreže je otprilike ujednačena u
  disparitetu, dok bi u dubini nekoliko dalekih sidara (gdje je jedan piksel dispariteta desetine
  metara) dominiralo;
- **iterativno ponderisano** (12 iteracija, težine u stilu Cauchyja `1 / (1 + (r / 3 MAD)^2)`),
  jer sidra nose grube izuzetke (poklapanje na automobilu u pokretu, greška praćenja) i jedno takvo
  sidro u običnom podešavanju povlači cijeli kadar;
- treba najmanje 2 upotrebljiva sidra; javlja medijan apsolutnog reziduala i broj
  unutrašnjih tačaka (rezidual unutar 3 x medijana).

`AffineFit.apply` vraća dubinu u metrima s **+inf** za nebo. Provjerava predviđenu vrijednost
kao i sidrenu: piksel neba koji predviđa nulu ispadne na `shift` - malo, pozitivno,
konačno - i inače bi svaki piksel neba završio na fantomskoj ljusci na jednoj udaljenosti. Sve
predviđeno na `1e-4` ili ispod je nebo, šta god podešavanje kaže.

Fuzija zatim zadržava samo dubine između 0,35 m i 60 m (pogledajte
[Fuzija](reconstruction-fusion-and-texture.md#from-depth-to-points)).
