---
title: "Dubina"
nav_order: 3
lang: "hr"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Dubina {#depth}

Jedna stvar koju vanjsko snimanje ne može dati je geometrija. Igra zna dubinu svakog piksela
i ona se nalazi u međuspremniku koji ovaj projekt namjerno ne dira, pa se **dubina zaključuje
iz slike**. To je granica točnosti cijelog pristupa.

Kod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(što pokreće skener),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch put i procjena mjerila),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, relativna varijanta. Predviđa *relativnu inverznu dubinu*: polje
nalik disparitetu, točno samo do na nepoznatu afinu transformaciju,
`metric_disparity = a * predicted + b`, različitu za svaki kadar. Mreža je dobra u onome što
je teško iz jedne slike (relativni oblik, rubovi, tanka struktura), a šuti o onome što ne može
znati (mjerilo). Mjerilo dolazi odnekud drugdje - vidi [Položaj kamere i mjerilo](reconstruction-pose.md).

| Veličina | Hugging Face id | Licenca |
|---|---|---|
| **Small** (zadano) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - komercijalna upotreba dopuštena |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - samo nekomercijalno |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - samo nekomercijalno |

Rekonstrukcija nasljeđuje licencu modela koji ju je napravio. Small je zadani svugdje upravo
zato da skeniranje ne nosi nikakvo ograničenje, osim ako ga netko ne odabere drukčije. Metrički
varijante (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) navedene su u kodu,
ali ih skener ne koristi. Vidi [Modeli i licence](models-and-licences.md).

## Izrada modela {#building-the-model}

Skener pokreće ONNX datoteku i nikad ne uvozi PyTorch. Datoteka se mora napraviti jednom:

- **Iz prozora**: „Set up the depth model” (vidi [Prozor skeniranja](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  koji pokreće naredbu niže s `--size small`.
- **Ručno**, u okruženju s PyTorchom, `transformers` i `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opcija | Zadano | Značenje |
|---|---|---|
| `--size` | `small` | `small`, `base` ili `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | izlazna datoteka |
| `--side` | `518` | veličina ulaza u kvadratu; mora biti višekratnik od 14 (veličina ViT zakrpe); 518 = 14 x 37 je razlučivost učenja |
| `--opset` | `17` | ONNX opset; 17 je široko podržan u DirectML-u i CUDA-i |

Što pretvarač radi:

- Preuzima kontrolnu točku s Hugging Facea (`AutoModelForDepthEstimation`).
- Omata je tako da je **ImageNet normalizacija unutar grafa**: model prima RGB u rasponu
  0-255 kao float (`pixels`, oblik `batch x 3 x side x side`) i daje `inverse_depth`. Postoji
  točno jedna kopija srednje vrijednosti i standardne devijacije, pa se ne mogu razići s
  kontrolne točke.
- **Fiksna prostorna veličina**, dinamička serija. DirectML i TensorRT prevode za svaki oblik;
  dinamička visina i širina prevodila bi se na prvom kadru svake nove razlučivosti, što je
  vidljivo zaustavljanje u živom snimanju.
- Izvozi se putem **TorchScript puta** (`dynamo=False`): dinamo graf je pao na DirectML-u kod
  čvora Reshape, a on zapisuje težine kao zasebnu datoteku `.onnx.data`. TorchScript put daje
  jednu samostalnu datoteku.
- Ispisuje datoteku i njezinu veličinu. Upozorenja tragača o ugrađenim oblicima su očekivana.

Skener traži `models/depth-*.onnx` i bira prema licenci, a ne prema nazivu datoteke: Small
kad god je tu, a veću veličinu samo kad je jedina. Redak prozora imenuje datoteku, njezinu
licencu i sve druge modele koje je ostavio neiskorištene.

## Pokretanje: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` izrađuje jednu ONNX Runtime sesiju, lijeno, uz punu optimizaciju
grafa, na pozadini koju je odabrala ljestvica, s CPU-om dodanim kao rezerva, pa pružatelj koji
padne pri stvaranju sesije (stari upravljački program) znači spor sken, a ne rušenje. Vidi
[Pokretanje i ovisnosti](runtime.md#inference-backends).

- `warm_up()` izrađuje sesiju i pokreće jedan prazan kadar (prvo zaključivanje na svježem
  grafu je nekoliko puta sporije od ustaljenog stanja).
- `measure_throughput(frames)` mjeri toliko praznih kadrova nakon zagrijavanja; prozor koristi 6
  i rezultat navodi kao poglede u sekundi.

### Prilagodba pisma, ne rastezanje {#letterboxing-not-stretching}

Graf prima fiksni kvadrat; igra je 16:9. Stiskanje kadra u kvadrat promijenilo bi prividni oblik
svega, a budući da je izlaz geometrijska procjena, bio bi spojen kao stvarna kriva geometrija.
Zato se svaki kadar:

1. skalira da stane u kvadrat, uz očuvanje omjera stranica (interpolacija po površini prema
   dolje, kubična prema gore);
2. popunjava **srednje sivom (114)** - crna ili bijela čitaju se kao jak rub i prelijevaju
   lažni prekid dubine u sadržaj uz sebe;
3. pokreće kroz model;
4. ispuna se odreže s predikcije **prije** nego što se vrati (kubično) na razlučivost kadra, pa
   se rub ne prelijeva u stvarne piksele.

Rezultat je `DepthMap` s `metric=False` na veličini izvornog kadra.

## PyTorch put {#the-pytorch-path}

`DepthEstimator` pokreće Hugging Face model izravno (fp16 na CUDA-i, fp32 na CPU-u), grupiran
po veličini kadra, svaka predikcija se vraća bikubično. Skener ga ne koristi; izvanmrežna
naredba `reconstruct` ga koristi (vidi [Izvanmrežna rekonstrukcija](reconstruction-offline.md)),
što je jedan od razloga zašto ta naredba treba PyTorch i `transformers`.

## Od relativnog do metričkog: `fit_scale` i `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Pretvaranje predviđene inverzne dubine u metre treba afino `scale * predicted + shift`. Kad
su dostupna sidra poznate dubine (značajke točaka trianguliranih između poznatih položaja ili
prethodno usidrena dubina prethodnog kadra), `fit_scale` ga rješava:

- najmanji kvadrati **u disparitetu**, a ne u dubini - pogreška mreže je otprilike jednolika u
  disparitetu, dok bi u dubini nekoliko udaljenih sidara (gdje je jedan piksel dispariteta
  desetke metara) dominiralo;
- **iterativno ponovno vagano** (12 iteracija, Cauchyjevi težinski faktori `1 / (1 + (r / 3 MAD)^2)`),
  jer sidra nose grube izvanredne vrijednosti (podudaranje na pokretnom automobilu, greška
  praćenja) i jedno takvo sidro u običnom prilagođavanju vuče cijeli kadar;
- treba najmanje 2 upotrebljiva sidra; javlja medijansku apsolutnu rezidualnu grešku i broj
  unutarnjih točaka (rezidual unutar 3 x medijan).

`AffineFit.apply` vraća dubinu u metrima s **+inf** za nebo. Provjerava predviđenu vrijednost
kao i usidrenu: piksel neba koji predviđa nulu izlazi kao `shift` - mali, pozitivan, konačan -
i inače bi sve piksele neba smjestio na lažnu ljusku na jednoj udaljenosti. Sve što je
predviđeno na ili ispod `1e-4` je nebo, što god prilagodba kaže.

Spajanje zatim zadržava samo dubine između 0,35 m i 60 m (vidi
[Spajanje](reconstruction-fusion-and-texture.md#from-depth-to-points)).
