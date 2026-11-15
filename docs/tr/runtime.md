---
title: Çalışma zamanı ve bağımlılıklar
nav_order: 8
lang: "tr"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Çalışma zamanı, bağımlılıklar ve performans {#runtime-dependencies-and-performance}

Kod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Çift tıklayın. Kendi başına yalnızca iki şey yapar:

1. **Python'u bulur** (önce `python`, sonra `py`). Hiçbiri yoksa `Install it now with winget [Y,N]?` diye sorar; Y ise `winget install -e --id Python.Python.3.12` çalıştırır, sonra Windows'un yeni PATH'i görmesi için pencereyi kapatıp `scan.bat` dosyasını yeniden çalıştırmanızı ister. N ise hiçbir şey kurulmaz.
2. Yoksa **özel bir ortam** oluşturur, `scan.bat` yanında `.venv`, ve pip'ini yükseltir - böylece hiçbir şey sistem Python'una kurulmaz.

Sonra `.venv\Scripts\python.exe -m heat3d_capture.ui` çalıştırır. Geri kalan her şey - eksik olanı bulmak, neye yaradığını söylemek, sormak - Python'da, bir diyalog olarak gerçekleşir.

## İlk çalıştırma denetimi {#first-run-preflight}

Pencere ağır bir şey içe aktarmadan önce, her gereksinim denetlenir (`importlib.util.find_spec` ile, böylece yarım kaldırılmış bir paket eksik sayılır). Kurallar:

- **Her şey önce denetlenir.** Bir şey söylenmeden önce tam liste toplanır, böylece bir paketi düzeltmek bir sonraki hataya doğrudan götürmez.
- **Sor, varsayma.** Diyalog, eksik her paketi, neye yaradığını ve toplam indirmeyi listeler ve **Download and install** olmadan hiçbir şey yapmaz. Cancel çıkar: "Nothing was installed and nothing was changed."
- **Sessizlik onay değildir.** Qt olmadan denetim konsola döner ve `Install them now? [Y/n]` diye sorar (Enter, `y`, `yes`, `j`, `ja` evet demektir); yanıtlayacak bir terminal yoksa (girdi sonu), hiçbir şey kurmaz.
- **Bu aracın kendi ortamına.** Kurulum, bir alt süreç olarak `<çalışan python> -m pip install ...` biçimindedir - `scan.bat` ile özel `.venv`. Başarısız olursa diyalog, pip çıktısının son satırını ve elle denenecek komutu gösterir.

| Paket | İçe aktarılan ad | Ne için olduğu olarak gösterilen | Yaklaşık indirme |
|---|---|---|---|
| numpy | `numpy` | diğer her şeyin üzerine kurulu olduğu aritmetik | 20 MB |
| opencv-python | `cv2` | video dosyalarını ve kamera karelerini okuma | 40 MB |
| Windows'ta onnxruntime-directml, diğerlerinde onnxruntime | `onnxruntime` | derinlik modelini grafik kartınızda çalıştırma | 120 MB |
| PySide6-Essentials | `PySide6` | pencere ve kontrolleri | 90 MB |
| scipy | `scipy` | yeniden oluşturulan yüzeyi düzgünleştirme | 45 MB |
| scikit-image | `skimage` | ölçümleri bir 3B yüzeye çevirme | 30 MB |
| windows-capture | `windows_capture` | bir oyun penceresini canlı yakalama (isteğe bağlı: onsuz video dosyaları yine çalışır) | 5 MB |

Derinlik modelini dönüştürmek üç tane daha gerektirir; bunlar ayrıca ve yalnızca "Set up the depth model" tuşuna basınca sorulur: `torch` (yaklaşık 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Tarayıcı bunları asla içe aktarmaz.

`reconstruct` çevrimdışı komutunun kendi denetimi vardır; lisans satırını yazdırdıktan sonra ve yalnızca terminalde çalışır: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow` ve Meta'nın GitHub deposundan `vggt` (`--no-deps` ile kurulur, çünkü meta verisi numpy'yi 2'nin altına sabitler). Aynı liste `requirements-offline.txt` içindedir; bkz. [Çevrimdışı yeniden oluşturma](reconstruction-offline.md#requirements).

`requirements.txt`'in platform için seçtiği ONNX Runtime paketi sunulur: Windows'ta `onnxruntime-directml`, diğerlerinde `onnxruntime`. `onnxruntime` zaten içe aktarılabiliyorsa (örneğin `onnxruntime-gpu`), hiçbir şey kurulmaz: denetim modül adıyla yapılır.

## Elle kurulum {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` şunları sabitler: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (yalnızca Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, Windows'ta `onnxruntime-directml>=1.19` ve diğerlerinde `onnxruntime>=1.19`.

`requirements-offline.txt`, yalnızca `reconstruct`'ın ihtiyaç duyduklarını ekler: `transformers`, `einops`, `safetensors`, `huggingface_hub` ve `Pillow`; `vggt` kurulum satırıyla (`--no-deps`) ve başlığında VGGT lisans notuyla birlikte. PyTorch onda da yoktur; nedeni aşağıda.

**PyTorch bilerek yoktur.** Doğru wheel GPU'ya ve CUDA sürümüne bağlıdır; bunu sabitlemek, en çok GPU sürümüne ihtiyacı olan makinelere CPU sürümünü kurardı. İstiyorsanız (model dönüştürme, çevrimdışı `reconstruct` yolu), `requirements.txt`'ten **önce** kurun: torch wheel'leri numpy 1.x'e yerleşebilir ve scipy bununla çalışmayı reddeder; hata, nedeninden çok uzakta, scipy'nin içinden `module numpy has no attribute long` olarak görünür.

`onnxruntime-directml` ve `onnxruntime-gpu` çakışır: yalnızca birini kurun.

Geliştirici tarafından doğrulandı: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, bir NVIDIA RTX 5080 üzerinde ve hiçbir NVIDIA'ya özgü paket olmayan aynı ortamda.

## Çıkarım arka uçları {#inference-backends}

ONNX Runtime, GPU'lara sağlayıcılar (execution provider) üzerinden ulaşır ve hangilerinin var olduğu donanıma değil, onnxruntime'ın nasıl kurulduğuna bağlıdır. Bu yüzden kullanılabilirlik, en iyiden başlayarak keşfedilir:

| Sıra | Sağlayıcı | Gösterilen | Donanım |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | Direct3D 12 destekleyen her GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | her şey |

**DirectML varsayılan kurulumdur**, çünkü AMD ve Intel GPU'larına da NVIDIA gibi ulaşır. NVIDIA kendi sağlayıcılarıyla daha hızlıdır - `onnxruntime-gpu` kurmak CUDA ekler ve pencere, bir NVIDIA kartı DirectML üzerinde çalışırken bunu söyler - ama NVIDIA tek seçenek olmak zorunda değildir. CPU her zaman sondadır, böylece kullanılabilir GPU'su olmayan bir makine hızlı olmayan bir tarama alır, hiç taramamaz; bir GPU oturumu oluşturulduğunda yedek olarak eklenir.

Adaptörün adı, Windows görüntü adaptörü sınıf anahtarındaki kayıt defterinden okunur (`nvidia-smi` gibi bir satıcı aracından değil, çünkü o yalnızca bazı makinelerde vardır); Basic Render Driver atlanır. Satıcıya kilitli sağlayıcılar eşleşen adaptörü adlandırır; DirectML, numaralandırılan ilk adaptörde, yani sistem varsayılanında gösterilir. Ad yalnızca görüntüleme içindir.

`ScanSettings.prefer_backend` (yalnızca betikler), bir sağlayıcıyı ya da kısa adını verebilir.

## Bu makinede beklenenler {#what-to-expect-from-this-machine}

Pencere, depth modelinin bu makinedeki gerçek verimini başlangıçta ölçer (ısınmadan sonra 6 kare) - GPU'yu bir tabloda aramak yerine, çünkü termal durum, dizüstü güç profilleri ve sürücü sürümleri onu çok fazla değiştirir - ve bir taramanın nasıl olacağını, başlamadan önce söyler:

| Ölçülen saniyedeki görünüm | Kademe | Başlık | Öneri |
|---|---|---|---|
| 25 ya da daha fazla | gerçek zamanlı | Tam ayrıntıda canlı tarama. | Normal bir hızda yürüyün; üst katman yetişecek. |
| 12 ila 25 | kullanılabilir | Canlı tarama, tam hızdakinden daha az tutulan görünümle. | Yavaş yürüyün ve nazikçe dönün - hızlı dönüşler boşluk bırakır. Draft daha az görünüm tutar, bu da derinlik modelinin yetişmesine yardımcı olur. |
| 2 ila 12 | yavaş | Önce kaydedin, sonra yeniden oluşturun. | Yürüyüşün bir videosunu kaydedin ve sonra dosyadan yeniden oluşturun. Sonuç aynıdır; yalnızca geri bildirim canlı değildir. |
| 2'nin altı | pratik değil | Bu makine faydalı tarama için çok yavaş. | Daha kısa bir rota ya da daha küçük bir model. **Başlatma devre dışıdır.** |

CPU üzerinde not, Windows'ta `onnxruntime-directml` kurmanın genellikle bunu düzelttiğini ekler. Yakalama çözünürlüğünü tek başına hiçbir şey değiştirmez: yardımcı olmazdı, çünkü derinlik modeli kendisine verilen her şeyde sabit giriş boyutunda çalışır; daha yavaş bir makineyi ayakta tutan şey, daha az görünüm tutmaktır, ki Draft bunu yapar.

### Geliştirici tarafından ölçüldü {#measured-by-the-developer}

Aynı ONNX dosyası, aynı çıktı, RTX 5080:

| Arka uç | Derinlik verimi |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Sevk edilen ONNX yolundan bir test klibi:

| Ön ayar | Tutulan görünümler | Derinlik verimi |
|---|---|---|
| Draft | yaklaşık 7'de 1 | yaklaşık 50 /s |
| Balanced | yaklaşık 4'te 1 | yaklaşık 50 /s |
| Detailed | yaklaşık 2'de 1 | yaklaşık 40 /s |

Derinlik yakalamadan rahatça daha hızlıdır, bu yüzden canlı tarama derinlik tarafından sınırlanmaz. Uygulamanın ortamı PyTorch olmadan yaklaşık 349 MiB, oysa CUDA'lı torch yaklaşık 3,5 GB.

Çevrimdışı `reconstruct` yolu farklıdır: bir masaüstü GPU'da 16 karelik pencere başına dakikalar.

## Bellek {#memory}

- Füzyondan sonra kareler tutulmaz; mesh'i renklendirmek için **160** tanesi hariç.
- Bir tarama, varsayılan olarak **3000** tutulan görünümde durur ("Views kept"), bir koruma olarak.
- Canlı yakalama kuyruğu 4 kare tutar; telemetri poz tamponu 30 saniye.
- Her iki voksel ızgarası da seyrektir ve mesh blok blok çıkarılır; bellek, sınırlayıcı kutuya değil taranan şeye göre büyür.

## Platform {#platform}

Tarayıcı ve Assetto Corsa kaydedicileri pratikte yalnızca Windows'tadır: canlı yakalama Windows Graphics Capture kullanır, kısayol tuşları ve tıklanabilir-geçen katman Win32 API kullanır ve Kunos sayfaları Windows paylaşılan belleğidir. Video dosyaları taranabilir ve UDP kaydedicileri başka yerlerde çalışır, ama bu kontrol edilmedi.
