---
title: "Mélység"
nav_order: 3
lang: "hu"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Mélység {#depth}

Amit a külső rögzítés nem tud megadni, az a geometria. A játék ismeri minden pixel mélységét, az pedig egy pufferben van, amelybe ez a projekt szándékosan nem nyúl, ezért a mélységet **a képből következtetjük**. Ez a teljes megközelítés pontosságának határa.

Kód: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(amit a szkenner futtat),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(a PyTorch-út és a skálailleszkedés),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## A modell {#the-model}

**Depth Anything V2**, a relatív változat. *Relatív inverz mélységet* jósol: egy diszparitásszerű mezőt, amely csak egy ismeretlen affin transzformációig helyes, `metrikus_diszparitás = a * jósolt + b`, és ez képkockánként más. A hálózat jó abban, ami egy képből nehéz (relatív alak, élek, vékony szerkezetek), és néma abban, amit nem tud (a skála). A skála máshonnan jön – lásd [Kamera pózai és mérete](reconstruction-pose.md).

| Méret | Hugging Face azonosító | Licenc |
|---|---|---|
| **Small** (alapértelmezett) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** – kereskedelmi használat engedélyezett |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 – csak nem kereskedelmi célra |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 – csak nem kereskedelmi célra |

A rekonstrukció örökli annak a modellnek a licencét, amely elkészítette. A Small mindenhol az alapértelmezett, pontosan azért, hogy egy szkennelés ne hordozzon korlátozást, hacsak valaki nem választ mást. A metrikus változatok (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) a kódban szerepelnek, de a szkenner nem használja. Lásd [Modellek és licencek](models-and-licences.md).

## A modell elkészítése {#building-the-model}

A szkenner egy ONNX-fájlt futtat, és soha nem importálja a PyTorchot. A fájlt egyszer el kell készíteni:

- **Az ablakból**: „Set up the depth model” (Mélységmodell beállítása) (lásd [A szkennelő ablak](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), amely a lenti parancsot futtatja `--size small` opcióval.
- **Kézzel**, olyan környezetben, amelyben van PyTorch, `transformers` és `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opció | Alapértelmezés | Jelentése |
|---|---|---|
| `--size` | `small` | `small`, `base` vagy `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | a kimeneti fájl |
| `--side` | `518` | a négyzet alakú bemenet mérete; 14 többszöröse kell legyen (a ViT-tapméret); 518 = 14 x 37 a tanítási felbontás |
| `--opset` | `17` | az ONNX-opset; a 17 széles körben támogatott a DirectML-ben és a CUDA-ban |

Amit a konverter csinál:

- Letölti az ellenőrzőpontot a Hugging Face-ről (`AutoModelForDepthEstimation`).
- Úgy csomagolja be, hogy az **ImageNet-normalizálás a gráfban van**: a modell 0–255 tartományú RGB-t kap lebegőpontos számként (`pixels`, alak `köteg x 3 x side x side`), és `inverse_depth`-et ad vissza. A középérték és a szórás egyetlen példányban van, így nem térhetnek el az ellenőrzőponttól.
- **Rögzített térbeli méret**, dinamikus köteg. A DirectML és a TensorRT alakonként fordít; egy dinamikus magasság és szélesség minden új felbontás első képkockájánál újrafordítást okozna, ami élő rögzítésnél látható megakadást.
- A **TorchScript-úton** exportál (`dynamo=False`): a dynamo-gráf a DirectML-en elhasalt egy Reshape-csomópontnál, és a súlyokat külön `.onnx.data` fájlba írja. A TorchScript-út egyetlen, önálló fájlt ad.
- Kiírja a fájlt és a méretét. A tracer figyelmeztetései a beépített alakokról várhatóak.

A szkenner a `models/depth-*.onnx` fájlokat keresi, és licenc szerint választ, nem fájlnév szerint: a Small-t, amint az ott van, egy nagyobb méretet csak akkor, ha az az egyetlen. Az ablak sora megnevezi a fájlt, a licencét és bármely más, nem használt modellt.

## Futtatás: ONNX Runtime {#running-it-onnx-runtime}

Az `OnnxDepthEstimator` egyetlen ONNX Runtime-munkamenetet épít, késleltetetten, teljes gráfoptimalizálással, a létra által kiválasztott háttéren, a CPU-t tartalékként hozzáfűzve, így az a szolgáltató, amely a munkamenet létrehozásakor elhasal (egy régi illesztőprogram), lassú szkennelést jelent, nem összeomlást. Lásd [Futtatás és függőségek](runtime.md#inference-backends).

- A `warm_up()` felépíti a munkamenetet, és lefuttat egy üres képkockát (az első következtetés egy friss gráfon többszörösen lassabb, mint az állandósult állapot).
- A `measure_throughput(frames)` a bemelegítés után ennyi üres képkockát mér; az ablak 6-ot használ, és az eredményt képkocka/másodperc egységben adja meg.

### Letterboxing, nem nyújtás {#letterboxing-not-stretching}

A gráf rögzített négyzetet vesz be; a játékmenet 16:9. Ha egy képkockát négyzetbe nyomnánk, minden látszólagos alakja megváltozna, és mivel a kimenet geometriai becslés, valódi, rossz geometriaként olvadna össze. Ezért minden képkocka:

1. úgy skálázódik, hogy beleférjen a négyzetbe, megtartva az oldalarányt (területi interpolációval lefelé, köbösen felfelé);
2. **közepesszürke (114)** szegéllyel egészül ki – a fekete vagy a fehér erős élnek látszik, és hamis mélységugrást visz a mellette lévő tartalomba;
3. átmegy a modellen;
4. a kitöltést a jóslatról **azelőtt** vágjuk le, hogy visszaméretezzük (köbösen) a képkocka felbontására, így a szegély sosem szivárog át a valódi pixelekbe.

Az eredmény egy `DepthMap` `metric=False` jelzéssel, a forrásképkocka méretében.

## A PyTorch-út {#the-pytorch-path}

A `DepthEstimator` közvetlenül futtatja a Hugging Face modellt (fp16 CUDA-n, fp32 CPU-n), képkockaméret szerint kötegelve, minden jóslatot köbösen visszaméretezve. A szkenner nem ezt használja; az offline `reconstruct` parancs igen (lásd [Offline rekonstrukció](reconstruction-offline.md)), és ez az egyik oka annak, hogy ehhez a parancshoz PyTorch és `transformers` kell.

## A relatívról a metrikusra: `fit_scale` és `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

A jósolt inverz mélység méterekbe váltásához az affin `skála * jósolt + eltolás` kell. Ha ismert mélységű horgonyok rendelkezésre állnak (ismert pózok között háromszögelt jellemzőpontok, vagy az előző képkocka horgonyzott mélysége), a `fit_scale` megoldja:

- legkisebb négyzetek **diszparitásban**, nem mélységben – a hálózat hibája nagyjából egyenletes a diszparitásban, míg a mélységben néhány távoli horgony (ahol a diszparitás egy pixelnyi változása tíz méter) uralná az illesztést;
- **iteratívan újrasúlyozva** (12 iteráció, Cauchy-jellegű súlyok `1 / (1 + (r / 3 MAD)^2)`), mert a horgonyokban durva kiugrók vannak (egy mozgó autóra illeszkedő pont, egy követési hiba), és egyetlen ilyen horgony egy egyszerű illesztésben az egész képkockát elhúzza;
- legalább 2 használható horgony kell; jelenti a medián abszolút reziduumot és a belső pontok számát (a reziduum a medián 3-szorosán belül).

Az `AffineFit.apply` métert ad vissza, az égre **+inf** értékkel. Ellenőrzi a jósolt értéket is, nem csak a horgonyzottat: egy égpixel, amely nullát jósol, `shift`-nél jönne ki – kicsi, pozitív, véges –, és az összes égpixelt egy fantomhéjra tenné egyetlen távolságban. Minden, amit a modell `1e-4` vagy az alatt jósol, ég, bármit mond is az illesztés.

Az összeillesztés ezután csak a 0,35 m és 60 m közötti mélységeket tartja meg (lásd [Összeillesztés](reconstruction-fusion-and-texture.md#from-depth-to-points)).
