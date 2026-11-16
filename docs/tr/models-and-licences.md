---
title: Modeller ve lisanslar
nav_order: 7
lang: "tr"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modeller ve lisanslar {#models-and-licences}

Bu depo için yazılan her şey **MIT lisansı** altındadır
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). MIT'in kapsayamadığı
şey, araçların çalıştığı şeylerdir: içe aktardıkları paketler, yeniden oluşturmanın kullandığı modeller
ve okudukları oyunlar. Kaynaklarıyla birlikte tam kayıt
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md) dosyasındadır; bu
lisanslar paket meta verileri ve model kartları okunarak Eylül 2026'da çıkarıldı. Bir bileşenin koşulları
o tarihten sonra değiştiyse kaynak geçerlidir, bu sayfa değil. Burada hukuki tavsiye yoktur.

## Derinlik modeli - ticari kullanımı belirleyen {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2, **boyutlarına göre aynı lisansla gelmez**; bir yeniden oluşturma, onu üreten modelin
lisansını devralır:

| Model | Lisans | Ticari kullanım | Kullanan |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **izinli** | varsayılan: tarayıcının dönüştürülmüş modeli (`tools/export_onnx.py` varsayılan olarak bunu kullanır ve pencerenin "Derinlik modelini kur" düğmesi her zaman bunu kurar) ve çevrimdışı yolun derinliği (birleştirme); VGGT pozları sağlar |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | yalnızca ticari olmayan | yalnızca kendiniz dönüştürürseniz (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | yalnızca ticari olmayan | yalnızca kendiniz dönüştürürseniz (`--size large`) |

Base ve Large daha iyi derinlik verir. Bunları dönüştürmek izinlidir; ancak bu, o model dosyasını ve onunla
yapılan her yeniden oluşturmayı ticari olmayan hâle getirir. Bu, çalıştıranın vereceği bir karardır, devralınacak
bir varsayılan değildir. Tarayıcı `models/depth-*.onnx` dosyaları arasından **adına göre değil, lisansa göre**
seçim yapar: varsa `depth-small-*`, yoksa Base, sonra Large (`choose_model`,
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
içinde). Pencere, aldığı dosyayı, onun lisansını ve kullanmadığı diğer model dosyalarını gösterir; Base ile
taramak için Small dosyasını `models/` klasöründen dışarı taşıyın.

## VGGT - yalnızca çevrimdışı yeniden oluşturma {#vggt---offline-reconstruction-only}

| Model | Lisans | Erişim |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - yalnızca ticari olmayan**; onunla yapılan yeniden oluşturmalar bunu devralır | herkese açık; varsayılan |
| `facebook/VGGT-1B-Commercial` | ayrı lisanslı; aldığınız koşulları denetleyin | kapılı: erişim Meta'dan istenir ve hesap başına verilir; bu olmadan indirme başarısız olur. `reconstruct --model vggt-1b-commercial` ile seçilir |

VGGT yalnızca `python -m heat3d_capture reconstruct` tarafından kullanılır; canlı tarayıcı onu hiç yüklemez.
Komut, başlamadan önce lisans satırını yazdırır. Videodan yeniden oluşturma, bu projenin bir oyuncunun
çalıştıracağı kısmıdır ve ticari olmayan koşullar buna uyar; ticari işler için bir motor dışa aktarımı ya da
oyun dosyası dışa aktarıcısı yolu kullanılır, ikisi de zaten kesindir.

## Karelerin yerini bulma - `locate` {#locating-frames---locate}

| Model | Lisans | Görevi |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | aynı yeri gösteren render'ları bulur |
| ALIKED `aliked-n16` | BSD-3-Clause | anahtar noktalar ve betimleyiciler |
| LightGlue (ALIKED varyantı) | Apache-2.0 | onları eşleştirir |

Üçü de ticari kullanıma izin verir ve ilk kullanımda indirilir. SuperPoint, LightGlue'un olağan eşi, kullanılmaz:
ağırlıkları ticari olmayandır. Bkz. [Bir seviyede kareleri bulma](locate.md).

## Python paketleri {#python-packages}

| Paket | Lisans | Görevi |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetik, düzleştirme, marching cubes |
| opencv-python | Apache-2.0 | video, özellikler, optik akış |
| onnxruntime, onnxruntime-directml | MIT | derinlik çıkarımı |
| windows-capture | MIT | Windows Graphics Capture ile canlı yakalama |
| **PySide6-Essentials** | **LGPL-3.0** | pencere |
| pytest | MIT | yalnızca geliştirme |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | tek seferlik model dönüştürme; çevrimdışı yol |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | çevrimdışı yol (`requirements-offline.txt`) |
| vggt | Meta'nın "VGGT License"ı (kabul edilebilir kullanım politikasıyla bir araştırma malzemesi anlaşması) | çevrimdışı yol; GitHub'dan `--no-deps` ile kurulur |
| moderngl, glcontext | MIT | `locate`: seviyeyi ekran dışında render etmek (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: anahtar noktalar ve eşleştirme |

**PySide6'nın koşulları vardır.** LGPL-3.0, Qt'nin *değiştirilebilir* bir kitaplık olarak kalması şartıyla
özel ve ticari kullanıma izin verir. Burada sıradan, dinamik bağlanan bir içe aktarma olarak kullanılır; bu
bunu karşılar ve lisans bildirimi her dağıtımla birlikte gitmelidir. Aracı tek bir çalıştırılabilir dosyaya
paketlemek, Qt'nin değiştirilebilir kalmasını gerektirirdi.

`vggt` paketinin kendi lisansı, `LICENSE.txt` dosyasından okunmuştur ve `LICENSES.md` içinde kayıtlıdır; ağırlıkların
CC-BY-NC-4.0 lisansından ayrı olarak kodu kapsar.

## Oyunlar {#the-games}

Telemetri yalnızca oyunların bunun için yayımladığı arayüzlerden gelir; kareler ekrandan gelir. Bkz.
[Kurallar](rules.md). Bir oyundan hiçbir şey birlikte dağıtılmaz veya yeniden dağıtılmaz ve araçların ürettikleri kullanıcının makinesinde kalır. 3DHeat GameCapture hiçbir oyun yayıncısıyla bağlantılı değildir ve hiçbiri tarafından onaylanmamıştır; oyun adları ve ilgili ticari markalar sahiplerine aittir.
