---
title: Derinlik
nav_order: 3
lang: "tr"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Derinlik {#depth}

Dış yakalamanın veremediği tek şey geometridir. Oyun her pikselin derinliğini bilir, ama bu bilgi bu projenin bilerek dokunmadığı bir tamponda durur; bu yüzden derinlik **resimden çıkarılır**. Tüm yaklaşımın doğruluk tavanı budur.

Kod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(tarayıcının çalıştırdığı),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch yolu ve ölçek uydurma),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, göreli varyant. **Göreli ters derinliği** tahmin eder: bilinmeyen bir afin dönüşüme kadar yalnızca doğru olan, disparite benzeri bir alan, `metric_disparity = a * predicted + b`; her kare için farklı. Ağ, tek bir resimden zor olan şeylerde (göreli şekil, kenarlar, ince yapılar) iyidir ve bilemeyeceği şeylerde (ölçek) sessizdir. Ölçek başka bir yerden gelir - bkz. [Kamera konumu ve ölçek](reconstruction-pose.md).

| Boyut | Hugging Face kimliği | Lisans |
|---|---|---|
| **Small** (varsayılan) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - ticari kullanıma izin verilir |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - yalnızca ticari olmayan |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - yalnızca ticari olmayan |

Bir yeniden oluşturma, onu üreten modelin lisansını miras alır. Small her yerde varsayılandır, tam olarak bir tarama, biri başka bir şey seçmedikçe hiçbir kısıtlama taşımasın diye. Metrik varyantlar (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) kodda adı geçer ama tarayıcı tarafından kullanılmaz. Bkz. [Modeller ve lisanslar](models-and-licences.md).

## Modeli oluşturmak {#building-the-model}

Tarayıcı bir ONNX dosyası çalıştırır ve asla PyTorch içe aktarmaz. Dosya bir kez yapılmalıdır:

- **Pencereden**: "Set up the depth model" (bkz. [Tarama penceresi](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)); bu, aşağıdaki komutu `--size small` ile çalıştırır.
- **Elle**, PyTorch, `transformers` ve `onnxscript` bulunan bir ortamda:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `--size` | `small` | `small`, `base` ya da `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | çıktı dosyası |
| `--side` | `518` | kare giriş boyutu; 14'ün katı olmalı (ViT yama boyutu); 518 = 14 x 37 eğitim çözünürlüğüdür |
| `--opset` | `17` | ONNX opset; 17, DirectML ve CUDA tarafından geniş biçimde desteklenir |

Dönüştürücünün yaptıkları:

- Kontrol noktasını Hugging Face'ten indirir (`AutoModelForDepthEstimation`).
- Modeli, **ImageNet normalleştirmesi grafın içinde** kalacak şekilde sarar: model, 0-255 aralığında float olarak RGB alır (`pixels`, şekil `batch x 3 x side x side`) ve `inverse_depth` çıkarır. Ortalama ve standart sapmanın tek bir kopyası vardır, bu yüzden kontrol noktasından ayrılamazlar.
- **Sabit uzamsal boyut**, dinamik batch. DirectML ve TensorRT şekil başına derler; dinamik yükseklik ve genişlik, her yeni çözünürlüğün ilk karesinde yeniden derlenirdi - canlı bir yakalamada görünür bir duraksama.
- **TorchScript yolundan** (`dynamo=False`) dışa aktarır: dynamo grafı DirectML'de bir Reshape düğümünde başarısız oldu ve ağırlıkları ayrı bir `.onnx.data` dosyasına yazar. TorchScript yolu tek, kendi içinde tam bir dosya üretir.
- Dosyayı ve boyutunu yazdırır. İzleyicinin sabit şekiller hakkındaki uyarıları beklenen türdendir.

Tarayıcı `models/depth-*.onnx` dosyalarını arar ve dosya adına göre değil, lisansa göre seçer: Small varsa o, yalnızca tek seçenek ise daha büyük bir boyut. Tarama penceresinin satırı dosyayı, lisansını ve kullanılmayan diğer modelleri adlandırır.

## Çalıştırma: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator`, tembel olarak, tam grafik optimizasyonuyla ve sürücünün seçtiği arka uçta tek bir ONNX Runtime oturumu kurar; CPU yedek olarak eklenir, böylece oturum oluşturulurken başarısız olan bir sağlayıcı (eski bir sürücü) yavaş bir tarama anlamına gelir, çökme değil. Bkz. [Çalışma zamanı ve bağımlılıklar](runtime.md#inference-backends).

- `warm_up()` oturumu kurar ve bir boş kareyi çalıştırır (yeni bir grafta ilk çıkarım, kararlı duruma göre birkaç kat yavaştır).
- `measure_throughput(frames)`, ısınmadan sonra o kadar boş kareyi ölçer; pencere 6 kullanır ve sonucu saniyedeki görünüm sayısı olarak verir.

### Esnetme değil, kutuya oturtma {#letterboxing-not-stretching}

Grafik sabit bir kare alır; oyun 16:9'dur. Bir kareyi kareye sıkıştırmak her şeyin görünen şeklini değiştirirdi ve çıktı bir geometrik tahmin olduğundan, gerçek yanlış geometri olarak birleştirilirdi. Bu yüzden her kare:

1. En boy oranı korunarak kareye sığacak şekilde ölçeklenir (aşağı alan enterpolasyonuyla, yukarı kübik);
2. **orta gri (114)** ile doldurulur - siyah ya da beyaz güçlü bir kenar gibi okunur ve yanındaki içeriğe sahte bir derinlik süreksizliği sızdırır;
3. modelden geçirilir;
4. dolgu, tahminden, kaynak karenin çözünürlüğüne **geri boyutlandırılmadan önce** kırpılır (kübik), böylece kenar boşluğu gerçek piksellere sızmaz.

Sonuç, kaynak karenin boyutunda, `metric=False` bir `DepthMap`'tir.

## PyTorch yolu {#the-pytorch-path}

`DepthEstimator`, Hugging Face modelini doğrudan çalıştırır (CUDA'da fp16, CPU'da fp32), kare boyutuna göre toplu olarak ve her tahmin kübik olarak geri boyutlandırılır. Tarayıcı bunu kullanmaz; çevrimdışı `reconstruct` komutu kullanır (bkz. [Çevrimdışı yeniden oluşturma](reconstruction-offline.md)). Bu, o komutun PyTorch ve `transformers` gerektirmesinin bir nedenidir.

## Göreliden metriğe: `fit_scale` ve `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Tahmin edilen ters derinliği metreye çevirmek, `scale * predicted + shift` afinesini gerektirir. Bilinen derinlikte çapalar mevcut olduğunda (bilinen duruşlar arasında üçgenlenmiş özellik noktaları ya da önceki karenin çapalanmış derinliği), `fit_scale` bunu çözer:

- **disparite içinde** en küçük kareler, derinlikte değil - ağın hatası disparitede kabaca düzgündür, derinlikte ise birkaç uzak çapa (bir pikselin disparitesinin on metreler olduğu yerde) hakimiyet kurardı;
- **yinelemeli olarak ağırlıklandırılmış** (12 yineleme, Cauchy tarzı ağırlıklar `1 / (1 + (r / 3 MAD)^2)`), çünkü çapalar kaba aykırı değerler taşır (hareket eden bir arabaya eşleşme, bir izleme aksaklığı) ve düz bir uydurmada tek bir böyle çapa tüm kareyi çeker;
- en az 2 kullanılabilir çapa gerekir; medyan mutlak artığı ve iç nokta sayısını bildirir (artık, 3 x medyan içinde).

`AffineFit.apply`, gökyüzü için **+inf** ile metre cinsinden derinlik döndürür. Hem tahmin edilen hem çapalanmış değere bakar: sıfır tahmin eden bir gökyüzü pikseli `shift` değerinde çıkar - küçük, pozitif, sonlu - ve aksi halde her gökyüzü pikselini tek bir uzaklıkta hayali bir kabuğa koyardı. Sıfır ya da altında (`1e-4`) tahmin edilen her şey, uydurmanın ne dediğinden bağımsız olarak gökyüzüdür.

Birleştirme, yalnızca 0,35 m ile 60 m arasındaki derinlikleri tutar (bkz. [Birleştirme](reconstruction-fusion-and-texture.md#from-depth-to-points)).
