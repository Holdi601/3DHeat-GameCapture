---
title: Birleştirme, kapsam ve renk
nav_order: 5
lang: "tr"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Birleştirme, kapsam ve renk {#fusion-coverage-and-colour}

Kod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Yerleştirilmiş her anahtar kare, aynı anda iki seyrek ızgarayı günceller: mesh'e dönüşen **yüzey hacmi** ve ona ne kadar güvenileceğini ve nereye geri dönüleceğini söyleyen **kapsam ızgarası**. İkisi de tarama sonunda değil, her anahtar karede güncellenir, çünkü kapsam haritası oyuncunun yönünü bulduğu şeydir.

## Derinlikten noktalara {#from-depth-to-points}

Konumu bilinen **ve** derinliği bir ölçeği olan her anahtar kare için:

1. Her yönde her ikinci piksel kullanılır (`PIXEL_STRIDE = 2`; tek bir yüzeyin komşu pikselleri bağımsız ölçümler değildir).
2. Derinlik, karenin afin uydurmasıyla metreye çevrilir.
3. Yalnızca **0,35 m** ile **60 m** arasında tutulur (0,35 m'den yakını silah, HUD, kaput demektir; 60 m, tek göz hatasının mesafenin karesiyle kabaca büyümesi ve uzak noktaların geometri biçimli gürültü olmasıdır) ve yalnızca maskenin dünya piksellerinde.
4. Kamera modelinden geçirilir ve poza göre dünyaya taşınır.
5. Her nokta pikselin rengini taşır.

Konumlanmış ama derinlik ölçeği olmayan bir kare *yerleştirilmiş* sayılır ama *birleştirilmiş* sayılmaz.

## Yüzey hacmi {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voksel, pencerenin "Surface detail" ayarıdır.

### TSDF değil, ağırlıklı doluluk {#weighted-occupancy-not-a-tsdf}

Bir işaretli mesafe alanı (TSDF), her pikselin ışını boyunca oyar ve ince yapıları ile boş alanı doğru alır, çünkü ışının boş alanın *içinden* geçtiğini bilir. Bu, yüz milyonlarca pikselin her biri için ışını yürümek demektir. Bu hacim bunun yerine voksel başına **ağırlıklı doluluğu** biriktirir ve düzgünleştirilmiş sonuca marching cubes uygular: tarama sırasında çalışacak kadar hızlı, kullanılabilir bir GPU olmayan bir makinede bile, ve çıktı bir nokta bulutu değil kapalı bir yüzeydir. Bedeli: ince yapılar ve boş alan bir TSDF'ninkinden daha kötü çıkar.

### Bir kareyi bütünleştirmek {#integrating-a-frame}

- Noktalar vokseller içine yerleştirilir (`floor(point / voxel)`).
- Dokunulan her voksel `weight x sqrt(count / max_count)` alır; burada `count`, karenin noktalarından kaçının o voksele düştüğü ve `weight = max(0.1, pose confidence)`. Karekök: bir noktadan sonra, aynı yerden aynı yüzeyin daha fazla pikseli kanıt olmaktan çıkar; poz güvenine göre ağırlıklandırmak, şüpheli bir pozun yüzeyi itmesini engeller.
- Renk, voksel başına çalışan bir ağırlıklı ortalamadır.

Izgara **seyrektir**: yürünen bir güzergâh, sınırlayıcı kutusunun küçük bir kesrine dokunur. Voksel koordinatları tek bir 64 bitlik anahtara paketlenir (eksen başına 21 bit, ±1.048.575 voksele kadar - 0,25 m'de yaklaşık ±262 km) ve sıralı bir dizi ile ikili arama ile, tamamen vektörleştirilmiş olarak aranır.

### Mesh'i çıkarmak {#extracting-the-mesh}

1. **0,35**'in altında ağırlığı olan vokseller atılır (siluet kenarlarındaki dağınık tek noktalar dikenlere dönüşürdü).
2. Ağırlıklar taramanın **75. yüzdeliğine** göre ölçeklenir ve 1'e kırpılır.
3. Dolu alan, her kenarı **64 voksel** olan bloklara bölünür; her biri, komşularının verisinden **3 voksel'lik bir yarı-alan** ile gerçekleştirilir (bu olmadan her blok sınırı bir duvara kapanır ve bir yol bir kutu sırası olarak çıkardı).
4. Her bloğun alanı, derinlik gürültüsünün bıraktığı kıvrımları gidermek için bir Gauss ile düzgünleştirilir (sigma 0,8 voksel).
5. **Birinci geçiş**: tüm bloklar boyunca örneklenen düzgünleştirilmiş alanın 99. yüzdeliği (en fazla 2 milyon değer) tek bir genel seviye ölçeğini belirler. Blok başına normalleştirmek, tek bir aykırı değeri kendi boş bloğunda tam bir yüzeye yükseltirdi.
6. **İkinci geçiş**: her bloğun alanı bu ölçeğe bölünür, marching cubes **0,5** değerinde. Bir üçgen, **ağırlık merkezinin** düştüğü bloğa aittir; böylece bir dikişi kesen üçgenler tam olarak bir kez üretilir.
7. Köşeler, voksel merkezlerinde dünya birimlerine taşınır; her köşe kendi vokselinin rengini alır (dolu bir vokselin dışına düşerse orta gri).

Blok bazlı çıkarım, iz boyutunda bir taramayı mümkün kılan şeydir: 0,25 m'de bir kilometre karelik kutu üzerinde tek bir yoğun dizi milyarlarca hücre olurdu. `tests/test_track_scale.py`, bunun bu ölçekte çalıştığını ve belleğin taranan şeyle orantılı olduğunu sabitler.

### Zemin ve yapı {#ground-and-structure}

`classify`, her üçgeni normaline göre etiketler (çıkarılan köşe normallerine göre yönlendirilmiş): yukarıya doğru **35 derece** içindeyse `ground`, geri kalan her şey `structure`. Görüntüleyici zemini düz, yapıları neredeyse saydam çizer. **Su asla iddia edilmez** - şekle bakarak düz zeminden ayrılamaz ve yanlış bir etiket bir avluyu göl gibi gösterirdi. Her etiket `.glb`'nin bir parçası olur ([.glb çıktısı](glb-output.md)).

## Kapsam {#coverage}

`CoverageGrid(voxel=0.5)` her yarım metrelik hücre için, aynı şey olmayan dört şeyi kaydeder:

| Terim | Saklanan | Puan (her biri 0..1'e kırpılır) | Neden ayrı sayılır |
|---|---|---|---|
| Kaç kez görüldü | hücreyi gören anahtar kare sayısı | `count / 3` | bir kez bir tahmindir, karşılaştırılacak bir şey yoktur |
| Kaç yönden | birim görüş yönlerinin toplamı | `(1 - spread) / (1 - 0.93)`, burada spread = toplamın uzunluğu / sayı | düz bir duvara doğru yürüyen yirmi kare aralarında paralaks taşımaz; birbirinden otuz derece farklı iki görüş daha değerlidir |
| Ne kadar uzaktan | en yakın görüş mesafesi | `1 - nearest / 40 m` | derinlik hatası kabaca mesafenin karesiyle büyür |
| Kamera ne kadar iyi konumlandı | en iyi poz güveni | güvenin kendisi | şüpheli bir pozla birleştirilmiş geometri yanlış yere düşer |

Bir karenin noktaları önce hücre başına gruplanır; böylece bir duvarın on bin pikseli, tek bir yönden tek bir gözlem sayılır.

**Kalite = dört terimin çarpımı**, ortalaması değil: her biri sağlanması gereken bir koşuldur. Altmış metreden tek bir yönden iki yüz kez görülmüş bir yer kötü gözlemlenmiştir ve bir ortalama, bunu tek bir mükemmel terimin arkasına gizlerdi.

Başlıca rakamlar (`summary`): dolu hücreler, kalitesi en az 0,5 olanların payı (pencerede "% well seen"), ortalama kalite ve hacim.

### Zayıf noktalar {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. kalitesi 0,35'in altındaki hücreler zayıftır;
2. zayıf hücreler **bağlantıya** göre gruplanır (26 komşuluk, yalnızca dolu hücreler üzerinde birleşim-bul - sınırlayıcı kutu üzerinde bir raster değil, uzun bir sürüşte milyonlarca boş hücre olabilir);
3. 8'den az hücresi olan gruplar yok sayılır;
4. her grubun nedeni, hücrelerinin en yaygın *en zayıf terimi*dir ve konumu hücrelerinin ortalamasıdır;
5. en büyükten başlayarak (sonra en kötü kaliteye göre) sıralanır, en fazla 8.

| Neden | Gösterilen öneri |
|---|---|
| az görüş | Yalnızca bir ya da iki kez görüldü - yanından tekrar geçin. |
| tek yön | Yalnızca tek bir açıdan görüldü. Yana adım atın ve tekrar bakın. |
| uzak | Yalnızca uzaktan görüldü. Yaklaşın. |
| zayıf izleme | Kamera burada iyi konumlandırılamadı. Daha yavaş yaklaşın. |

Bağlantı önemlidir: sabit bir blok ızgarasıyla gruplamak, ihmal edilmiş tek bir yan odayı birçok ayrı halka olarak bildirir ve kimse sekiz yeri bir yerden, bir yer sekiz kez sayılmış olarak ayırt edemez.

### Plan görünümü {#the-plan-view}

`top_down(resolution)`, hücreleri x/z'ye yansıtır ve sütun başına **en iyi** kaliteyi tutar (bir odada duran biri tavanı kötü, zemini mükemmel görür; ortalama odayı kehribar renge boyardı). Hiç gözlemlenmemiş sütunlar ayrıca işaretlenir. Pencere 200 x 200, üst katman 120 x 120 çizer ([Tarama penceresi](reconstruction-scan-ui.md#the-coverage-map)).

### Bu yeniden oluşturulabilir mi? {#is-this-reconstructable}

En az 500 hücre olduğunda, her 25 birleştirilmiş karede bir:

| Bulgu | Karar | Mesaj (kısaltılmış) |
|---|---|---|
| hücrelerin %2'sinden azının görüş yayılımı 0,93'ün altında | yeniden oluşturulamaz | Neredeyse hiç paralaks yok. Ya kamera hiç yana bakmıyor, ya da izleme kayıyor ve aynı yüzey aynı yere iki kez düşmüyor. Yerleştirilmiş kare sayısına bakın: yüksekse, kaymadır. |
| hücrelerin en yakın mesafesinin medyanı 25 m'nin üstünde | yeniden oluşturulamaz | Her şey N m ya da daha uzaktan görüldü ... İstediğinize yaklaşın. |
| iyi yayılımı olan %6'dan az | yeniden oluşturulabilir, uyarılı | İnce paralaks - geometri kaba olacak. Baktığınız şeye göre yana hareket etmek en çok yardımcı olur. |

Bu, ayırt edemediği iki nedenden düşük paralaks vardır; mesaj ikisini de adlandırmasının nedeni budur.

## Renk {#colour}

Birleştirmenin voksel başına rengi ucuz ve canlıdır, ama bulanıktır: çeyrek metrelik bir hücredeki her piksel ortalanır, otuz metreden kenardan görülenler dahil. Bu yüzden dışa aktarımda mesh, bir kez daha, karelerin kendisinden renklendirilir:

- **Tutulan kareler**: en fazla **160** anahtar kare (resim ve poz), rezervuar örneklemesiyle seçilir; böylece tarama kuyruğunda değil, tüm taramaya yayılırlar.
- **Köşe başına** (`project_colours`), her tutulan kare, köşe kameranın önündeyse ve resmin içindeyse, yüzey kameraya doğrudan bakmaya göre yaklaşık 70 dereceden fazla dönük değilse (`|normal . view| > 0.34`), **35 m**'den yakınsa ve aşağıdakinden (aşağıda) daha yakın bir şey önünde durmuyorsa katkıda bulunur.
- Böyle her görüş `facing x (1 - distance / 35)` ile puanlanır; böylece yakın, doğrudan bir görüş, uzak, eğik bir görüşü yener. Her köşenin **en yüksek puanlı 4 görüşü** tutulur - karelerin sırası ne olursa olsun, daha iyi bir görüş en zayıf dördün yerine geçer - ve aynı puanla ağırlıklandırılarak harmanlanır.
- **Görüş engelleme**: her karede mesh'in kendi görünen köşeleri, 2 piksellik hücrelerden oluşan bir derinlik tamponuna çizilir ve hücre başına en yakın tutulur. Kendi hücresindeki en yakın olandan, mesafesinin `0,3 m + %5`'inden fazla arkada kalan bir köşe o karede gizlenmiştir - kamera ile yoldaki arasında bir duvar - ve o görüş hiçbir şey saymaz. Test yalnızca mesh'i bilir: hiç birleştirilmemiş bir engel (geçen bir araba, HUD maskesinin dışındaki bir kokpit sütunu) yakalanmaz.
- Hiçbir karenin görmediği bir köşe voksel rengini korur; ikisi de yoksa orta gri (siyah bir delik gibi okunurdu).

Renk, bir doku atlası yerine köşe başına `COLOR_0` olarak yazılır. Görüntüleyicinin varsayılan görünümü, doygun ısının altında gri bir haritadır; renk, taranmış bir pistte yolu bulmak içindir, çünkü orada geometri tek başına yolu kenardan ayıramaz ve görüntüleyicinin Arka plan / bölüm panelindeki *Yakalanan renk* anahtarının arkasında gösterilir. Bir atlas dosya boyutunu katlayacak ve bir açıcı gerektirirdi; bu da kasıtlı olarak varsayılan olmayan bir görünüm içindi. Blender ve diğer glTF araçları `COLOR_0`'ı okur.
