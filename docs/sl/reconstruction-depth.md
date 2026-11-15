---
title: "Globina"
nav_order: 3
lang: "sl"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Globina {#depth}

Ena stvar, ki je zunanji zajem ne more dati, je geometrija. Igra pozna globino vsakega piksla, a ta je v medpomnilniku, ki se ga ta projekt namenoma ne dotika, zato se globina **sklepa iz slike**. To je zgornja meja natančnosti celotnega pristopa.

Koda: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py) (kar zažene skener), [`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py) (pot PyTorch in prilagoditev merila), [`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, relativna različica. Napoveduje *relativno inverzno globino*: polje, podobno disparitati, pravilno le do neznane afine transformacije, `metric_disparity = a * predicted + b`, ki je različna za vsak okvir. Mreža je dobra v tem, kar je težko iz ene slike (relativna oblika, robovi, tanka struktura), in tiha glede tega, česar ne more vedeti (merilo). Merilo pride od drugod – glejte [Položaj kamere in merilo](reconstruction-pose.md).

| Velikost | Hugging Face id | Licenca |
|---|---|---|
| **Small** (privzeto) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** – komercialna uporaba dovoljena |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 – samo nekomercialno |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 – samo nekomercialno |

Rekonstrukcija podeduje licenco modela, ki jo je naredil. Small je privzeta povsod prav zato, da rekonstrukcija nima omejitve, razen če se nekdo odloči drugače. Metrične različice (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) so v kodi navedene, skener jih ne uporablja. Glejte [Modeli in licence](models-and-licences.md).

## Gradnja modela {#building-the-model}

Skener zažene datoteko ONNX in nikoli ne uvozi PyTorcha. Datoteko je treba enkrat narediti:

- **Iz okna**: "Set up the depth model" (glejte [Okno za pregled](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), ki zažene spodnji ukaz z `--size small`.
- **Ročno**, v okolju s PyTorchom, `transformers` in `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Možnost | Privzeto | Pomen |
|---|---|---|
| `--size` | `small` | `small`, `base` ali `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | izhodna datoteka |
| `--side` | `518` | kvadratna vhodna velikost; mora biti večkratnik 14 (velikost zaplate ViT); 518 = 14 x 37 je učna ločljivost |
| `--opset` | `17` | različica ONNX; 17 je široko podprta v DirectML in CUDA |

Kaj pretvornik naredi:

- Prenese kontrolno točko s Hugging Face (`AutoModelForDepthEstimation`).
- Ovije jo tako, da je **normalizacija ImageNet znotraj grafa**: model sprejme RGB v območju 0–255 kot float (`pixels`, oblika `batch x 3 x side x side`) in vrne `inverse_depth`. Obstaja natanko ena kopija povprečja in standardnega odklona, zato se ne moreta razlikovati od kontrolne točke.
- **Fiksna prostorska velikost**, dinamičen batch. DirectML in TensorRT prevajata po obliki; dinamična višina in širina bi se na prvem okviru vsake nove ločljivosti znova prevedla, kar bi bilo vidno kot zastoj v živem zajemu.
- Izvozi se prek **poti TorchScript** (`dynamo=False`): graf dynamo je na DirectML padel pri vozlišču Reshape, poleg tega zapiše uteži v ločeno datoteko `.onnx.data`. Pot TorchScript da eno samostojno datoteko.
- Izpiše datoteko in njeno velikost. Opozorila sledilnika o vgrajenih oblikah so pričakovana.

Skener išče `models/depth-*.onnx` in izbira po licenci, ne po imenu datoteke: Small kadarkoli je na voljo, večja velikost samo, če je edina. Vrstica v oknu za pregled navede datoteko, njeno licenco in morebitne druge modele, ki jih ni uporabila.

## Zagon: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` ustvari eno sejo ONNX Runtime, leno, s polno optimizacijo grafa, na izvajalniku, ki ga je izbrala lestvica, s CPU kot rezervo, da ponudnik, ki pade ob ustvarjanju seje (star gonilnik), pomeni počasno skeniranje, ne zrušitve. Glejte [Izvajalniki in odvisnosti](runtime.md#inference-backends).

- `warm_up()` ustvari sejo in požene en prazen okvir (prvo sklepanje na svežem grafu je večkrat počasnejše od ustaljenega stanja).
- `measure_throughput(frames)` časi toliko praznih okvirjev po ogrevanju; okno uporabi 6 in rezultat navede kot poglede na sekundo.

### Letterboxing, ne raztezanje {#letterboxing-not-stretching}

Graf sprejme fiksen kvadrat; igranje je 16:9. Stiskanje okvira v kvadrat bi spremenilo videz vsega, in ker je izhod geometrijska ocena, bi se zlil kot resnična napačna geometrija. Zato je vsak okvir:

1. prilagojen kvadratu z ohranjenim razmerjem stranic (interpolacija po površini navzdol, kubična navzgor);
2. zapolnjen s **srednje sivo (114)** – črna ali bela se bereta kot močan rob in v vsebino ob njih pošljeta lažno nezveznost globine;
3. zagnan skozi model;
4. zapolnitev se odreže od napovedi **preden** se spet poveča (kubično) na ločljivost okvira, da rob ne preliva v prave piksle.

Rezultat je `DepthMap` z `metric=False` pri velikosti izvornega okvira.

## Pot PyTorch {#the-pytorch-path}

`DepthEstimator` zažene model Hugging Face neposredno (fp16 na CUDA, fp32 na CPU), v paketih po velikosti okvira, vsaka napoved pa se kubično vrne na velikost. Skener ga ne uporablja; offline ukaz `reconstruct` ga uporablja (glejte [Rekonstrukcija po snemanju](reconstruction-offline.md)), kar je eden od razlogov, da ta ukaz potrebuje PyTorch in `transformers`.

## Od relativne do metrične: `fit_scale` in `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Pretvorba napovedane inverzne globine v metre potrebuje afin `scale * predicted + shift`. Kadar so na voljo sidra znane globine (značilne točke, triangulirane med znanimi pozami, ali prejšnji okvir z zasidrano globino), `fit_scale` to reši:

- najmanjši kvadrati **v disparitati**, ne v globini – napaka mreže je približno enakomerna v disparitati, v globini pa bi nekaj oddaljenih sider (kjer je en piksel disparitete deset metrov) prevladalo;
- **iterativno ponovno utežena** (12 iteracij, Cauchyjevi-podobne uteži `1 / (1 + (r / 3 MAD)^2)`), ker imajo sidra grobe osamelce (ujemanje na premikajočem se avtomobilu, napaka sledenja), in en tak sidro v navadnem prilagajanju potegne cel okvir;
- potrebuje vsaj 2 uporabni sidri; poroča mediano absolutnega ostanka in število notranjih točk (ostanek znotraj 3 x mediane).

`AffineFit.apply` vrne globino v metrih z **+inf** za nebo. Preveri napovedano vrednost in tudi zasidrano: nebesni piksel, ki napove nič, bi prišel na `shift` – majhen, pozitiven, končen – in bi vsak nebesni piksel postavil na fantomsko lupino pri eni razdalji. Vse, kar je napovedano na vrednost `1e-4` ali manj, je nebo, ne glede na to, kaj reče prilagoditev.

Zlivanje nato obdrži samo globine med 0,35 m in 60 m (glejte [Zlivanje](reconstruction-fusion-and-texture.md#from-depth-to-points)).
