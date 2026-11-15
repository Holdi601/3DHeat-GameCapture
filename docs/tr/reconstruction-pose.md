---
title: Kamera konumu ve ölçek
nav_order: 4
lang: "tr"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kamera konumu ve ölçek {#camera-pose-and-scale}

Bir derinlik haritası, her şeyin *bir* bakış noktasından ne kadar uzakta olduğunu söyler. Bunlardan birçoğunu tek bir seviyeye dönüştürmek için her bakış noktasının nerede ve hangi birimde olduğunu bilmek gerekir. Bu sayfa canlı yolları kapsar; çevrimdışı ileri beslemeli çözüm [Çevrimdışı yeniden oluşturma](reconstruction-offline.md) sayfasındadır.

Kod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Kamera modeli {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)`, pencerede ayarladığınız **yatay görüş alanından** bir delik kamera kurar: `fx = (width / 2) / tan(fov / 2)`, kare pikseller (`fy = fx`), ana nokta karenin merkezinde. Bir oyun kendi projeksiyonunu yayımlamaz, bu yüzden bu tek varsayılan sayıdır: çok dar olursa sahne olduğundan daha derin okunur. Çevrimdışı yol 65 derece kullanır.

Bir `Pose`, **dünyadan-kameraya** saklanır: `rotation` (3 x 3) ve `translation` = dünyadaki kameranın merkezi; yol, ısı haritası ve üst katman hepsi bunu ister.

## Görsel odometri (varsayılan) {#visual-odometry-the-default}

`VisualOdometry`, her anahtar kareyi bir öncekine karşı izler:

1. **Özellikler**: ORB, kare başına en fazla 1500, yalnızca dünya maskesi üzerinde tespit edilir (bkz. [Yakalama](reconstruction-capture.md#what-is-not-the-world)).
2. Önceki anahtar kareye **eşleştirmeler**: kaba kuvvet, Hamming uzaklığı, çapraz kontrollü (yalnızca karşılıklı en iyi çiftler).
3. **3B'ye kaldırma**: önceki karenin derinliği zaten dünya birimlerindedir, bu yüzden eşleşen pikselleri dünya noktaları olur.
4. **Kamerayı yerleştirme**: bu noktalar arasında `solvePnPRansac` (yeniden projeksiyon hatası 3 px, güven 0,999, 200 yineleme). Öteleme aynı birimlerde çıkar, bu yüzden **ölçek boşluğu geçer**.
5. **Bu karenin derinliğini çapalama**: kendi tahmin edilen ters derinliği, PnP iç noktalarının derinliklerine karşı uydurulur (`fit_scale`) ve döngü tekrarlanır.

**İlk kare** başlangıç noktasıdır: birim poz, ve derinlik afinesi ya aşağıdaki zemin kalibrasyonudur ya da, o olmadan, birim (yeniden oluşturma o zaman kendi içinde tutarlıdır ama birimsizdir).

Bir pozun en az **18 RANSAC iç noktası** gerekir - PnP'nin minimumu olan altıdan açıkça fazla, çünkü tam olarak yeterli kadar noktadan gelen bir çözüm, tam olarak emin bir yanlış olandır.

### Güven {#confidence}

Yerleştirilmiş her kare, birleştirmesini ve kapsamını ağırlıklandıran 0..1 arası bir güven alır:

| Poz kaynağı | Güven |
|---|---|
| telemetri | 1.0 |
| ileri beslemeli bir çözüm | 0.85 |
| görsel izleme | `inliers / matches x min(1, inliers / 60)` |

### İzleme koptuğunda {#when-tracking-breaks}

Yerleştirilemeyen bir kare bildirilir, tahmin edilmez: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Hiçbir poz kaydedilmez ve hiçbir şey birleştirilmez. Son pozdan devam etmek ya da yeni bir başlangıç noktası açmak, bir sonraki seviye parçasını keyfi bir ofsete koyardı - gerçek geometri gibi görünen bir dikiş.

Bir kopuştan sonra, her yeni kare, geçmiş anahtar karelerden oluşan bir veritabanına karşı **yeniden konumlandırılır** (izlenen her 4. kare eklenir, en fazla 120, en eskisi düşer), en yeniden başlayandan başlayarak, aynı eşleştir-ve-PnP adımıyla. Biri başarılı olana kadar kareler atılır. Yeniden konumlanan bir kare aynı koordinat çerçevesinde devam eder. Yeniden konumlanmalar sayılır ve pencerede gösterilir (`N recovered`).

### Döngü kapatma: kapalı {#loop-closure-off}

Aynı veritabanı döngü kapatmayı destekler: çok önceki anahtar karelere karşı eşleştirip bir yeniden ziyareti tespit etmek ve izi üzerine geri oturtmak. **Varsayılan olarak kapalıdır ve tarayıcı asla açmaz** (`Reconstructor(loop_closure=False)`). Tekrarlayan manzarada - bir ralli etabı, bir koridor, bir sıra ağaç - her parça diğerine benzer ve özellik eşleştirmesi sahte yeniden ziyaretleri onaylar; bu, kamerayı ilerlerken başladığı yere yakın tutar. Bunu düzgünce yapmak, bir yer tanıma (bir kelime torbası sözlüğü ya da öğrenilmiş bir tanımlayıcı) ve bir harariteye karşı geometrik doğrulama gerektirir; bu yapılmadı.

Koddan etkinleştirildiğinde bir kapatma şunları gerektirir: mevcut poza 6 m içinde, en az 60 anahtar kare yaşında bir anahtar kare, en az 90 iç noktayla eşleşmiş, pozu 0,02 m'den fazla ve 6 m'den az hareket ettiren. Yine de yalnızca mevcut pozu değiştirir; bir poz grafiği değildir ve önceki kareleri ya da birleştirilmiş geometriyi hareket ettirmez.

## Telemetri pozları {#telemetry-poses}

**Racing telemetry (Forza) -> Listen for position data** açıkken, kamera yolu resimlerden değil Forza'nın Data Out'undan gelir (`ForzaPoseSource`):

- Bir iş parçacığı `127.0.0.1:<port>` üzerinde dinler (varsayılan 5300), kaydediciler gibi aynı düzen algılamasıyla ([Forza](telemetry-forza.md)); paketler `isRaceOn` ayarlıyken kullanılır. Meşgul bir port bildirilir, yükseltilmez: telemetri bir iyileştirmedir ve tarama görsel olarak devam eder.
- Her paket, **geldiği monotonik zamanla** damgalanır - kareleri damgalayan aynı saat. Oyunun kendi zaman damgası ilgisiz bir şeyden saydığı için hizalama için kullanılmaz. Döngü geri beslemesinin bir iki milisaniyelik jitter'ı 200 km/s'de yaklaşık 6 cm'dir.
- Yuvarlanan bir 30 saniyelik tampon tutulur. Bir karenin pozu, yakalama zamanının iki yanındaki örneklerden **enterpole** edilir: konum doğrusal, dönüş küresel enterpolasyonla (karışık bir matris bir dönüş değildir ve her noktayı çarpıtırdı). **0,35 s**'den uzun bir boşlukta ya da tampon dışında poz yoktur.
- `pose_from_forza`: kamera arabanın üzerine konur (bir takip kamerasının ofseti yayımlanmaz). **Konumlar oyunun gönderdiği gibi tutulur**: Forza'nın dünyası zaten Y-yukarıdır (x ve z haritanın üzerinde, y yükseklik); bu, tur dosyalarının ve rota dosyalarının yazdığı biçimdir, böylece yüzey, üzerine kaydedilen turlarla aynı koordinatlara oturur. (Önceki bir sürüm, "Z-yukarı" bir dünya için y ve z'yi değiştirdi ve parçayı yan yatırdı.)
- Dönüş, yaw, sonra pitch, sonra roll; yönler kaydedilmiş turlardan okunmuştur: seyir yönü `atan2(dx, dz)` yaw'a eşittir, tırmanılan eğim pitch'in eksi değerine eşittir (pozitif burun aşağıdır) ve roll, sağ süspansiyon sıkıştığında pozitiftir (pozitif, sağ tarafı düşürür). Aracın eksenleri (x sağa, y yukarı, z ileri), y'yi çevirerek kameranın eksenlerine (x sağa, y aşağı, z ileri) dönüştürülür.
- Forza'nın dünyası **sol elli**dir ve kameranın çerçevesi değildir; bu yüzden ortaya çıkan dünyadan-kameraya matris bir yansımadır (determinant -1) ve tarama, tur dosyaları gibi sol elli çıkar. Enterpolasyon etkilenmez (bu tür iki poz arasındaki dönüş, uygun bir dönüştür).
- Bir karenin telemetri pozu yoksa (bir boşluk), yeniden oluşturucu o kare için **görsel izlemeye** geri döner, son telemetri pozundan devam ederek, ve besleme pozlarına, besleme yanıt verir vermez geri döner. PnP yalnızca dönüşler verir, bu yüzden ters bir dünyada dünya z üzerinden aynalanmış olarak çözülür ve ayna geri katlanır; kare oyunun koordinatlarına düşer. Görsel izleme de başarısız olursa, kare izlenmemiş olur.

### Telemetriden derinlik ölçeği {#depth-scale-from-telemetry}

Oyun kameranın nerede olduğunu söyler, ama hiçbir şeyin ne kadar uzakta olduğunu söylemez; bu yüzden her karenin derinliği yine çapalanmalıdır - ama 0. kareden zincirleyerek değil, birimi keyfi olan oysa pozlar metre cinsinden olan. Bunun yerine, önceki ve mevcut kare arasında eşleşen özellikler (en az 8), **bilinen iki pozdan doğrudan** metre cinsinden üçgenlenir ve derinlik haritası kameranın önündeki noktalara uydurulur. Her kare telemetriye karşı çapalanır, bu yüzden sürüklenen bir zincir yoktur.

İki poz **0,05 m**'den daha az aralıklıysa ışınlar neredeyse paraleldir ve üçgenleme gürültüdür; bu yüzden kare çapalanmamış bırakılır: tam olarak konumlanmış ama birleştirilmemiş ("positioned, but its depth has no scale yet"). Pencerenin *yerleştirilmiş* ve *birleştirilmiş* kareleri ayrı saymasının nedeni budur.

## Ölçek {#scale}

Görsel odometri göreli ölçeği doğru zincirler, ama tüm seviye yine bilinmeyen bir çarpan üzerinde yüzer. Depth Anything'in göreli çıktısı keyfi birimlerde gelir, bu yüzden ilk kareyi birim poza bırakmak dünyayı kameranın birkaç metre içine, keyfi bir boyutta koyar.

`GroundCalibrator`, bu çarpanı kameranın zeminden **ne kadar yüksekte** olduğundan sabitler; ölçüm **ilk anahtar karede** ve, orada kullanılabilir zemin yoksa, sonraki karelerde yapılır:

- Kamera yüksekliği: **1,15 m** (bir sürücünün göz hizası) - pencere her zaman bunu kullanır; betikler 1,70 m (`WALKING_HEIGHT`, ayakta duran bir oyuncu) ya da `None` (kalibrasyon yok) verebilir.
- Zemin örneği: karenin yukarıdan %62-92 satırları (ufkun altında, kaputun ya da silahın üstünde) ve %30-70 sütunları (kenarlardan uzakta).
- Kullanılabilir bir tahmini olan her piksel, `1 / predicted` derinliğiyle ağın birimlerinde kaldırılır; optik eksenin altındaki noktalar kameranın altında bir yükseklik verir. Medyanları, ağ birimlerinde kamera yüksekliğidir; bu yüzden `metres per unit = 1.15 / median` ve karenin afinesi `scale = 1 / metres_per_unit`, öteleme 0.
- En az 200 zemin örneği ve **dağılım** (medyan mutlak sapma / medyan) **0,60**'ın altında olduğunda güvenilir.
- İlk anahtar karede uydurma, orijinin birimi olur, böylece tarama baştan itibaren metredir. İlk anahtar karede kullanılabilir zemin yoksa, tarama birimsiz başlar ve izlenen her sonraki anahtar kare denenir, en fazla **30 kare** boyunca. Kalibre eden ilk kare *metre başına birimi* verir: zemininin ima ettiği derinliğin, zincirin o kare için verdiği derinliğe oranının, zemin bandı üzerindeki medyanı. Şimdiye kadar birleştirilmiş her şey ilk karenin birimindedir, bu yüzden çarpan zincire geri beslenmez; yazılırken bütün seviyeye (ve işaretli noktalara) uygulanır, ve o zamana kadar görünen mesafeye. Voksel boyutu da ilk karenin birimlerindedir, bu yüzden metre cinsinden boyutu ayarlanan değerden o çarpan kadar farklıdır.
- 30 kare zeminsiz geçerse tarama birimsiz kalır ve bunu söyler.
- Telemetriyle, sonraki anahtar kareler denenmez: derinlik telemetrinin metrelerine çapalanmıştır.

Gerçek boyutun yüzde on içinde olmak, bin kat yanlış olmaktan iyidir; telemetri, varsa, bunu gereksiz kılar. Not, izleme satırının altında pencerede `Size: ...` olarak gösterilir: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (daha geç geldiğinde `found on frame N, so the level is scaled by F when it is written` ile), `no usable ground in the first N frames - sizes are relative, not metres` ya da `in metres, from the telemetry's positions`.

## Demet ayarlaması ve uzun izler (bağlı değil) {#bundle-adjustment-and-long-tracks-not-wired-in}

Gelecekteki bir pencereli çözücü için iki parça vardır ve tarayıcı **tarafından kullanılmaz**:

- **`FeatureTracks`**, Lucas-Kanade izlemesiyle yüzlerce kare boyunca özellik kimliğini tutar (600 özellik, %60'ın altına düşünce yeniden tohumlanır, ileri-geri toleransı 1 px, yeni özellikler mevcut olanlardan 10 px uzakta), ki demet ayarlaması bunu ister - ardışık kareler arasında tanımlayıcı eşleştirmesi yalnızca çiftler verir.
- **`bundle_adjust`**, bir pencere pozunu ve noktalarını `scipy.optimize.least_squares` ile birlikte iyileştirir (güven bölgesi, 2 px ölçekli soft-L1 kaybı, açık bir Jacobian seyreklik deseni, sabit kameralar tam olarak geri yüklenir). `tests/test_bundle.py` içinde bilinen gerçeğe karşı test edilmiştir.

`WindowedOdometry` ikisini birleştirir (12 anahtar karelik pencereler, her 3 anahtar karede bir çözüm, ilk iki kamera sabit, 6 px'ten fazla hatası olan noktalar atılır, son adımın 6 katından büyük sıçramalar reddedilir). Docstring'i, gerçek görüntüde onun **yolu çökerttiğini ve kare-kare izlemeden çok daha yavaş olduğunu** kaydeder; nedenler olarak ölçek serbestliği (gauge freedom) ve derinlik tabanlı önyükleme bilinir, üçüncü bir neden tanımlanamamıştır. Bu yüzden kare-kare görsel odometri varsayılan olarak kalır; kodda not edilen olası düzeltme, zemin düzlemi kalibrasyonundan sabitlenmiş bir taban çizgisiyle iki görüşlü temel matris önyüklemesidir.
