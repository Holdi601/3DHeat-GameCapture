---
title: "Sınırlar ve doğrulama"
nav_order: 9
lang: "tr"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Sınırlar ve neyin doğrulandığı {#limits-and-what-is-verified}

Dürüst bir liste: araçların yapmadığı şeyler ve bir çalışan oyuna karşı henüz kontrol edilmemiş olanlar.

## Telemetri {#telemetry}

| Kaydedici | Durum |
|---|---|
| Forza | Resmi Data Out belgelerine göre yapıldı; düzen paketlerin kendisinden algılanır. Görüntüleyicinin FH Companion `.tele.gz` okuyucusu gerçek turlarda denendi. |
| AC, ACC, AC EVO, AC Rally | Yayımlanmış düzenlerden yapılmış sentetik sayfalarda test edildi. **Henüz canlı oyunlara karşı çalıştırılmadı.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Belgelenmiş düzenlerden yapılmış paketlerde test edildi. **Henüz canlı oyunlara karşı çalıştırılmadı.** RBR'nin eksenleri, duruşu ve hız birimleri belgelenmemiştir; veriden ele alınır. |
| BeamNG.drive | Kaydedici, modun yapısından yapılmış paketlerde test edildi. **Mod oyunda hiç çalıştırılmadı.** |
| Trackmania | Görüntüleyicinin CSV okuyucusu test edildi. **Eklenti oyunda hiç çalıştırılmadı.** Yalnızca Openplanet'in geliştirici modunda yüklenir. |
| iRacing | Görüntüleyicinin `.ibt` okuyucusu sentetik bir dosyada test edildi. |

Diğer telemetri sınırları:

- Forza'nın kayma normalleştirmesi belgelenmemiştir; Kunos kayması, tipik bir asfalt tepe değeriyle ölçeklenir, bu bir yaklaşıktır.
- Bazı Kunos ve DiRT araç gövdesi yanal eksenlerinin yönü iki şekilde de belgelenmiştir; sürüş açısının büyüklüğü güvenilirdir, işareti değildir.
- Hiçbir ralli oyunu tekerlek kaymasını göndermez; o görüntüleyicide türetilir. RBR tekerlek hızlarını göndermez.
- Bir ralli etabının zemini yalnızca `--surface` verildiğinde yazılır; aksi halde dosya hiçbirini adlandırmaz ve görüntüleyici bunu çıkarır (etap ya da etkinlik adı, sonra sürüş tarzı; varsayılan olarak gevşek).
- Tur sayacı olmayan oyunlarda tur algılama (AC EVO, AC Rally, BeamNG), kaydın başladığı noktayı çizgi olarak kullanır; bu yüzden kaydı başlangıç çizgisinde başlatın.
- Bir BeamNG araç sıfırlaması, o anda açık olan turu kapatır: en az 300 m kat ettiyse kısmi bir koşu olarak yazılır, değilse atılır.
- `route` yaklaşık her 2 saniyede bir kaydeder; bir çökme ya da öldürülen bir süreç, son kayıttan sonraki konumları en fazla kaybeder.
- Forza Horizon bir pist adı göndermez, bu yüzden Forza tur dosyalarında `"track": null` vardır; Forza Motorsport (2023) yalnızca bir numara gönderir, `lap.trackOrdinal` olarak tutulur.

## Yeniden oluşturma {#reconstruction}

- **Derinlik tahmin edilir, okunmaz.** Yaklaşımın tavanı ve oyun sürecine hiç dokunmamanın bedeli.
- **Görüş alanı varsayılır, ölçülmez.** Çok dar olursa bölüm olduğundan daha derin yeniden oluşturulur.
- **Global ölçek**, varsayılan bir kamera yüksekliğinden (pencerede 1,15 m) ya da telemetriden gelir. İlk anahtar karede ölçülür; orada kullanılabilir zemin yoksa sonraki anahtar kareler denenir (en fazla 30 kare) ve sonradan bulunan bir ölçek, yazıldığında bütün bölüme uygulanır. Pencerenin "Size:" satırı hangisinin olduğunu söyler; hiç zemin bulunamazsa tarama birimsiz kalır. Bu durumda voksel boyutu ilk karenin birimlerindedir, bu yüzden metre cinsinden boyutu ayarlanan değerden farklıdır. Çevrimdışı yeniden oluşturmalar, çözümün kendi birimlerindedir.
- **Döngü kapatma kapalıdır** ve kodda açıldığında bile bir poz grafiği değildir; sürüklenme yalnızca kareden kareye izlemenin kalitesiyle sınırlanır.
- **Pencere düzeltmesi (windowed bundle adjustment) vardır ama bağlı değildir**; gerçek görüntüde çöktü.
- **Yüzey, ağırlıklı doluluktur, TSDF değildir**: ince yapılar ve boş alan bir TSDF'nin olacağından daha kötüdür.
- **Doku atlası yoktur.** Renk köşe başına (`COLOR_0`) tutulur ve 160 tutulmuş kare arasından en iyi 4 görüşten karıştırılır. Görünürlük testi kabadır: ağın kendi köşelerine karşı 2 piksellik bir derinlik tamponunda test eder; bu yüzden ağın içermediği bir engel (geçen bir araba) yakalanmaz.
- **Su hiçbir zaman etiketlenmez**; her şey zemin ya da yapıdır.
- **Telemetri pozları** kamerayı arabaya koyar (bir takip kamerasının ofseti bilinmez). Konumlar Forza'nın gönderdiği gibi alınır (Y yukarı, tur dosyalarındaki gibi); sapma, yalpa ve yuvarlanmanın yönleri, çalışan oyunun kamerasına bakılarak değil, kaydedilmiş turlardan okundu (hareket yönü, eğim, hangi tarafın süspansiyonunun sıkıştığı).
- Kaplama, **tam ekran özel** modunda çizilemez; kenarlıksız pencere modunu kullanın.
- Genel kısayollar, tıklamaya geçirgen kaplama ve canlı yakalama **yalnızca Windows'ta** çalışır.
- Pencereyi kapatmak kaydetmeyi sormaz.

## Ölçülenler {#what-is-measured}

- `tests/test_accuracy.py`: bilinen bir yolu ve analitik derinliği olan sentetik bir oda - yerleştirilen kareler, yol hatası, yürünen mesafe, oda boyutu, duvarlardaki yüzey ([Seviye yeniden oluşturma](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: bilinen genişlikte, merkezden kaymış sürülen bir yol, genişliğini yeniden oluşturur.
- `tests/test_track_scale.py`: pist ölçeğinde yüzey çıkarma, bellek taranana orantılı, bloklar tek bir yüzeye birleşir.
- `tests/test_glb.py` ve görüntüleyicinin kendi testleri: `.glb` sözleşmesi iki taraftan da.
- Derinlik ağının gerçek oyun üzerinde nasıl performans gösterdiği sentetik bir sahnenin cevaplayabileceği bir şey değildir ve test paketi tarafından ölçülmez.
