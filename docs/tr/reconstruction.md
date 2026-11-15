---
title: Oynanıştan seviye yeniden oluşturma
nav_order: 6
lang: "tr"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Oynanıştan seviye yeniden oluşturma {#level-reconstruction-from-gameplay}

Bir seviyeyi yavaşça yürüyün ya da bir parkurda sürün; tarayıcı, ekranda görünenleri 3DHeat
görüntüleyicisinin telemetrinin altında bağlam olarak yüklediği bir `.glb` dosyasına çevirir. Dosya
sözleşmesi, Unreal dışa aktarıcısının yazdığıyla aynıdır. Bu, haritayı kimsenin dışa aktarmadığı ve
oyunun dosyalarının okunamadığı durumlar içindir; bir motor dışa aktarımı ya da oyun dosyası dışa
aktarımı kesindir, bu ise bir tahmindir.

## Boru hattı {#the-pipeline}

```text
 kareler              anahtar kareler      derinlik             poz                  birleştirme         çıktı
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> resim değişimi   ->  Depth Anything V2 -> görsel odometri   -> doluluk hacmi    -> marching cubes
 Capture ya da bir   eşiği (uyarlanabilir) (ONNX Runtime,       (ORB + PnP), ya da   + kapsama ızgarası -> zemin/yapı
 video dosyası                            harflendirilmiş)     Forza telemetrisi,   (canlı harita,     -> tepe rengi
                                                               ya da bir VGGT       zayıf noktalar)     -> .glb
                     HUD / kokpit maskeleri, kare kalitesi önerileri, zemin düzlemi ölçeği
```

| Aşama | Canlı tarama (`heat3d_capture.ui`) | Çevrimdışı (`reconstruct`) | Sayfa |
|---|---|---|---|
| Kareler | monitör, pencere ya da video, ön ayarın en uzun kenarına göre yeniden boyutlandırılmış | video, iki kez örneklenmiş (çözüm planı ve birleştirme aralığı) | [Yakalama](reconstruction-capture.md) |
| Anahtar kareler | resmin ne kadar değiştiğine göre tutulur, eşik yakalamaya göre uyarlanır | her `--fuse-interval` saniyede bir | [Yakalama](reconstruction-capture.md#keyframes) |
| Maskeler | değişime dayalı `ScreenMask`, sonra 40 anahtar kareden sonra akışa dayalı `FlowMask` | videonun dört çalıştırmasından öğrenilmiş `FlowMask`; çözücüye uygulanmaz | [Yakalama](reconstruction-capture.md#what-is-not-the-world) |
| Derinlik | en iyi GPU arka ucunda ONNX modeli | PyTorch Depth Anything V2 Small | [Derinlik](reconstruction-depth.md) |
| Poz | görsel odometri ya da tam Forza telemetrisi | bir yol olarak birleştirilmiş, aradeğerlenmiş VGGT pencereleri | [Poz](reconstruction-pose.md), [Çevrimdışı](reconstruction-offline.md) |
| Ölçek | bir kez, sabit bir kamera yüksekliği (1,15 m) ya da telemetri | çözülmüş yolun kendi birimleri | [Poz](reconstruction-pose.md#scale) |
| Birleştirme | ağırlıklı doluluk, seyrek voksel; kapsama ızgarası | aynısı | [Birleştirme](reconstruction-fusion-and-texture.md) |
| Çıktı | `.glb`, zemin/yapı parçaları, tepe rengi, santimetre | aynısı | [.glb çıktısı](glb-output.md) |

Kod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - bir taramanın ayarları ve temposu; `reconstruct.py` - anahtar kareleri geometriye
çevirir; `offline.py` - çevrimdışı yol), aşamalar `capture/`, `depth/`, `pose/`, `fusion/` ve
`geometry/` içindedir.

## Doğruluk nereden gelir {#where-accuracy-comes-from}

Tek görüntülü derinlik yalnızca bilinmeyen bir ölçeğe kadar doğrudur - bir odanın fotoğrafı ile bir
oyuncak evin fotoğrafı aynı resimdir. Bu yüzden ağ, iyi yaptığı işi yapar (göreli şekil, kenarlar, ince
yapılar), ölçek ve kamera yolu ise bunları bilen bir yerden gelir:

| Oyun | Kamera yolu | Ölçek |
|---|---|---|
| Telemetri açıkken Forza Horizon / Motorsport | kesin; Data Out'tan, her karenin yakalama zamanına aradeğerlenmiş | kesin: derinlik, bilinen iki poz arasında özellikleri üçgenleyerek sabitlenir |
| Başka her şey, canlı | görsel odometri, kare kare zincirlenmiş | bir kez, zemin üstündeki varsayılan bir kamera yüksekliğinden sabitlenir |
| Bir kayıt, çevrimdışı | VGGT, örtüşen pencerelerde çözülmüş | çözümün kendi birimleri (metrik değil) |

Tarayıcının ölçmek yerine kendisine **söylediği** tek sayı, oyunun **yatay görüş alanı**dır (pencerede
varsayılan 90 derece; yarış oyunları için 65'e daha yakın). Çok dar olursa seviye olduğundan derin
yeniden oluşturulur; çok geniş olursa düzleşir.

## Kullanıcıya erken bildirmek {#telling-the-user-early}

Bir tarama fiziksel bir eylemdir - biri bir seviyeyi birkaç dakika yürür - ve pahalı olan hata, yürüyüşü
bitirip işe yaramadığını keşfetmektir. Bu yüzden pencere, herhangi bir şey başlamadan önce bu makinenin
derinlik işlem hızını ölçer ve taramanın nasıl olacağını söyler
([Çalışma zamanı](runtime.md#what-to-expect-from-this-machine)); tarama sırasında, pencerede ve oyunun
üzerindeki tıklanabilir bir kaplamada, numaralı zayıf noktaları olan bir kapsama haritası, izleme sağlığı,
bir yürüyüş hızı çubuğu, bir keskinlik çubuğu ve her seferinde tek bir talimat gösterir
([Tarama penceresi](reconstruction-scan-ui.md)).

## Bilinen sentetik doğruluk üzerinde ölçüldü {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py`, bilinen bir kamera yolundan, analitik (ağ değil) derinlikle 12 x 8 m'lik bir
odayı (4 m yüksekliğinde) çizer ve 0,2 m vokselle yeniden oluşturur. Şunları doğrular: karelerin %90'ından
fazlası yerleştirilir; ortalama yol hatası 0,35 m'nin altındadır (en kötüsü 1 m'nin altında); yürünen
mesafe gerçeğin %10'u içindedir; oda, 1,5 m içinde doğru genişlikte çıkar; duvar yüzeyinin %75'inden
fazlası gerçek bir duvarın 0,45 m'si içinde kalır; araştırma tarzı bir yürüyüş, düz ileriye yürümekten
belirgin şekilde daha iyi kapsama alır; özellik içermeyen bir sahne, uydurulmak yerine reddedilir.
Analitik derinlik, pozu, ölçeği ve birleştirmeyi ağdan ayırır; ağın gerçek oynanışta nasıl davrandığı ise
hiçbir sentetik sahnenin yanıtlamadığı ayrı bir sorudur. `tests/test_track_width.py`, bilinen genişlikte bir
yolda merkezden kaydırılarak sürülen bir turun yalnızca sürülen çizgiyi değil, yolun genişliğini yeniden
oluşturduğunu denetler.

## Sayfalar {#pages}

- [Tarama penceresi](reconstruction-scan-ui.md) - her denetim, kısayol ve kaplama öğesi
- [Yakalama, maskeler ve kare kalitesi](reconstruction-capture.md)
- [Derinlik](reconstruction-depth.md)
- [Kamera pozu ve ölçek](reconstruction-pose.md)
- [Birleştirme, kapsama ve renk](reconstruction-fusion-and-texture.md)
- [.glb çıktısı](glb-output.md)
- [Çevrimdışı yeniden oluşturma](reconstruction-offline.md)
