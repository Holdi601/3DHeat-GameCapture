---
title: Yakalama, maskeler ve kare kalitesi
nav_order: 2
lang: "tr"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Yakalama, maskeler ve kare kalitesi {#capture-masks-and-frame-quality}

Kod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Kareler nereden gelir {#where-frames-come-from}

Bir kaynak hedefi şunlardan biridir:

| Hedef | Kaynak | Notlar |
|---|---|---|
| `monitor:<n>` | tüm bir monitör, canlı | pencerenin "Whole screen" seçeneği, "Which" alanındaki numarayla |
| `window:<title>` | tek bir pencere, canlı | pencerenin "A window" seçeneği, başlığıyla |
| bir dosya yolu | bir video dosyası | pencerenin "A video file" seçeneği; OpenCV'nin okuyabildiği her biçim |

### Canlı yakalama: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource`, **Windows Graphics Capture**'ı saran `windows-capture` paketini kullanır - ekran kayıt programlarının kullandığı herkese açık API. Oyunun içine hiçbir şey enjekte edilmez. İmleç yakalanmaz ve sarı yakalama çerçevesi çizilmez.

Yakalama kitaplığı kareleri bileşimcinin iş parçacığında bir geri çağırmaya teslim eder ve bunun hemen dönmesini bekler; bu yüzden geri çağırma yalnızca kareyi kopyalar (arabellek yeniden kullanılır), BGRA'dan RGB'ye çevirir, boyutunu değiştirir, zaman damgası koyar ve **4 kareli** bir kuyruğa koyar. Kuyruk dolduğunda **en eski kare atılır** ve bir sayaç artar: geride kalmanın bedeli kareler olmalı, bellek ya da doğruluk değil; canlı görünüm oyuncunun şu an nerede olduğunu göstermelidir. Atılan kareler pencerenin istatistik satırında gösterilir; atılanların yarısından fazlası bir ipucu tetikler.

Her kare, `t` (yakalama başladığından beri saniye) ve `monotonic` (yakalama anındaki ham `time.monotonic()`) taşır; telemetri paketlerinin de damgalandığı saat budur - Forza konumlarının karelerle hizalanmasını sağlayan şey de budur.

`windows-capture`, bağımlılık denetiminde isteğe bağlıdır: o olmadan da bir video dosyası taranabilir.

### Video dosyaları {#video-files}

`VideoSource`, OpenCV ile okur, RGB'ye çevirir ve boyutunu değiştirir. Kare hızı olmayan bir kap 30 fps kabul edilir. Zaman damgaları kare numarasının kare hızına bölümüdür; bir dosyanın duvar saati zamanı yoktur, bu yüzden telemetri bir videoya hizalanamaz.

### Çözünürlük {#resolution}

Kareler kaynakta, en uzun kenarları ön ayarın yakalama boyutu olacak şekilde küçültülür (Draft 640, Balanced 960, Detailed 1280 px), alan enterpolasyonuyla. 4K bir kare, derinlik modelinin kullandığı piksellerin otuz katıdır.

## Anahtar kareler {#keyframes}

Bir yakalamadaki neredeyse her kare gereksizdir: durup beklemek, bir şeyin yüzlerce görünümünü üretir. Yeniden oluşturmanın istediği şey *paralaksdır*. Bu yüzden bir kare, zamana göre değil, **son tutulan kareden bu yana resmin ne kadar değiştiğine** göre tutulur.

`picture_change(a, b)`:

1. iki kare de griye çevrilir ve 16 x 16'lık bir blok ortalamaları ızgarasına indirilir (blok ortalamaları resmin hareketine tepki verir, tanelenmeye, yapraklara, titremeye ya da HUD'a değil);
2. ortalama mutlak fark, 255'in bir kesri olarak;
3. bir dünya maskesi bilindiğinde, her blok, dünyaya ait olan payına göre ağırlıklandırılır; bu sayede yarım gösterge tablosu olan bir blok yarım sayılır (maske ızgaranın ağırlığının %5'inden fazlasını kapsadığında kullanılır).

Eşik **yakalamaya uyum sağlar**: ilk 30 kare için ön ayarın başlangıç değeridir (0,020 / 0,010 / 0,004), sonra son 240 ölçülen değişimin ön ayarın kantili (0,85 / 0,65 / 0,40) olur ve asla 0,0001'in altına düşmez. Bir kare, değişimi eşiğe eriştiğinde tutulur; ilk kare her zaman tutulur. Sabit bir eşik sahnelerde çalışmaz - karanlık bir kokpit turunun kareden kareye değişimi, parlak dokulu bir odanın değişiminin küçük bir kesridir - oysa "en yoğun üçte birini tut" her iki durumda da aynı anlama gelir. Kullanımdaki eşik her ilerleme güncellemesiyle birlikte gider (`ScanProgress.threshold`), pencerenin ve üst katmanın yürüme hızı çubukları son değişimi buna göre ölçer (`ScanProgress.toward_next_view`).

Yalnızca tutulan kareler derinlik modelinden ve yeniden oluşturmadan geçer. Kareler, bir çağıran istemedikçe saklanmaz (`keep_frames`); mesh'i renklendirmek için 160 tanesi tutulur (bkz. [renk](reconstruction-fusion-and-texture.md#colour)).

Bir tarama, durdurulduğunda, bir videonun sonuna gelindiğinde ya da zaman ya da anahtar kare sınırına ulaşıldığında biter.

## Dünya olmayan şeyler {#what-is-not-the-world}

Bir oyun karesindeki iki şey seviye geometrisi değildir ve ikisi de bir yeniden oluşturmayı bozar:

- **HUD.** Bir nişangah, herhangi bir karedeki en tekrarlanabilir özelliktir. Bir özellik eşleştirici ona bayılır, her iki kare arasında mükemmel eşleşir ve her eşleşme kameranın hareket etmediğinin kanıtıdır - bu da tüm yeniden oluşturmayı sıkıştırır.
- **Kameraya sabitlenmiş şeyler.** Bir silah, motor kaputu, bir kokpit çerçevesi, bir gösterge tablosu. Yanlış koordinat sisteminde gerçek geometri: birleştirildiğinde, yürünen yol boyunca kayar.

Bunları bulan iki dedektör vardır. İkisi de bir maske üretir (255 = dünya, 0 = dünya değil) ya da yeterli kanıt yokken `None`; `None` her zaman "her şeyi kullan" anlamına gelir, asla "hiçbir şey kullanma" değil.

Maske şuralarda uygulanır:

- görsel odometrideki **özellik tespitinde** (bir nişangahı çıktıdan maskelemek, ama duruşu oylamasına izin vermek, görünen belirtiyi düzeltir ve zararlı olanı korur);
- **birleştirilmiş piksellere**, böylece kokpit geometrisi birleştirilmez;
- **keskinlik ve parlaklık ölçüsüne**, çünkü bir kokpit her zaman mükemmel keskindir;
- anahtar kareleri belirleyen **resim değişimine**.

Ancak VGGT çevrimdışı çözücüye verilen karelere **uygulanmaz** (bkz. [Çevrimdışı yeniden oluşturma](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: neyin değişmediği {#screenmask-what-does-not-change}

İlk anahtar kareden FlowMask hazır olana kadar kullanılır.

- Her kare griye çevrilir, yarıya indirilir ve bulanıklaştırılır (3 x 3 Gauss), böylece sabit bir HUD öğesindeki bir piksellik titreme hareket gibi okunmaz.
- Önceki kareden piksel başına mutlak fark, üstel bir ortalamaya (sönümleme 0,9) katlanır; böylece maske, tarama sırasında beliren ya da kaybolan bir HUD'u izler.
- Yalnızca kameranın hareket ettiği bilinen karelerden öğrenir (taramada: en az bir kare izlendikten sonra) - park halindeki bir kamera her şeyi durağan gösterir.
- **12** öğrenme karesinden sonra, bir piksel ortalama değişimi karenin medyan değişiminin **0,22**'sinin altındaysa durağandır - göreceli, bu yüzden eşik oyuncunun ne kadar hızlı hareket ettiğini izler.
- Karenin %**45**'inden fazlası durağan görünüyorsa, varsayım başarısız olmuştur (bir menü, bir ara sahne) ve hiçbir şey maskelenmez.
- Maske bir piksel aşındırılır (kenar yumuşatmalı HUD kenarları ikisine de ait değildir) ve tam boyuta geri ölçeklenir.

Penceredeki notu: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` ya da `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: asla hareket etmeyen şey {#flowmask-what-never-travels}

Bir kokpit durağan değildir: iğneler süpürür, devir göstergesi seğirir, mini harita döner; bu yüzden bir değişim dedektörü bu pikselleri dünya sayar - ve bunlar bir poz çözücüye verilecek en kötü özelliklerdir. FlowMask daha iyi bir soru sorar: **hangi özellikler hareket etmeden devam eder?**

- Canlı taramada bir kez, ilk **40 anahtar kareden** öğrenir (gri tonlamalı); ardından taramanın geri kalanında ScreenMask'in yerini alır.
- Kareler, yarısı örtüşen **30** karelik pencerelere bölünür. Her pencerede en fazla 800 köşe tohumlanır (`goodFeaturesToTrack`, kalite 0,01, 8 px aralıklı) ve piramidal Lucas-Kanade ile izlenir (21 x 21, 4 seviye) ve **ileri-geri denetimle**: geri akışı başladığı yerin 1 px içine düşmeyen bir iz düşürülür, çünkü komşu bir desene kayan bir izleyici tam olarak aranan "kalıcı ama durağan" imzasını üretirdi. 20 kareden kısa pencereler atlanır. Kısa pencereler önemlidir: uzun bir koşuda neredeyse her dünya özelliği kareden çıkar ve kanıt hiçbir şeye kalmaz.
- Hayatta kalan her özelliğin net yolu, **kare genişliğinin %2'si** ile karşılaştırılır: altındaysa "takılı", üstündeyse "hareketli". Sayımlar, özelliklerin başladığı yere göre bir **24 x 24** ekran hücresi ızgarasında biriktirilir.
- Bir hücre, en az 2 takılı özellik ve takılı sayısı hareketlinin üstündeyse **ve** 8 komşusunun en az 3'ü de engelliyse, engellenmiş sayılır (tek bir hücre gürültüdür; karanlık görüntüler bunu bolca üretir).
- Yalnızca **kare kenarına bağlı** engellenmiş bölgeler tutulur. Kameraya sabitlenmiş her şey ekranın bir kenarına ulaşır; ortada duran ve hareket etmeyen şey kaçış noktasıdır - ileriye sürerken, önündeki yol hiç akış göstermez ve en çok istenen geometridir.
- Kalan bölge bir hücre büyütülür (bir gösterge panelinin kenarı bir gradyandır).
- Karenin %**60**'ından fazlası maskelenecekse hiçbir şey maskelenmez: gece görüntülerinde hücrelerin çoğunda izlenebilir bir özellik yoktur; bu da bir kadrandan farksızdır.

Notu: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels` ya da %60'ı geçtiğinde hiçbir şeyi maskelemediğini açıklayan bir mesaj.

Çevrimdışı yol, FlowMask'i aynı şekilde, video boyunca dağılmış 4 çalıştırmadan (her biri 90 ardışık kare, 960 x 540) öğrenir ([Çevrimdışı](reconstruction-offline.md)).

## Kare kalitesi ve öneriler {#frame-quality-and-advice}

`QualityWatcher` her anahtar kareyi değerlendirir ve **tek** bir talimat seçer; böylece üst katman, hâlâ zamanı varken "yavaşla" diyebilir.

Her kare için yalnızca dünya pikselleri üzerinde ölçülür (maske 5%'ten az bırakırsa tüm pikseller):

- **keskinlik**: Laplacian'ın varyansı - standart tek geçişli ölçü ve tam olarak hareket bulanıklığının yok ettiği şeye tepki verir;
- **parlaklık**: ortalama gri seviye, 0-255.

Keskinliğin mutlak bir ölçeği yoktur (gece bir etap ile parlak bir cadde, ikisi de odakta olsa bile bir büyüklük sırası farklıdır), bu yüzden **bu yakalamanın çalışan medyanına** göre değerlendirilir: son 90 kare, herhangi bir değerlendirme yapmadan önce 20 kare gerekir. Her kare, eklenmeden **önceki** geçmişle karşılaştırılır; böylece uzun, bulanık bir bölüm medyanı kendine doğru çekemez.

| Koşul | Test |
|---|---|
| düz | keskinlik en fazla 1,0 (bir yükleme ekranı, bir duvar, gökyüzü) |
| karanlık | parlaklık 26'nın altında |
| bulanık | keskinlik medyanın 0,55'inin altında ve düz değil |

Öneri, ilk eşleşen kazanır (en çok taramayı engelleyen şeye göre sıralı):

| Durum | Öneri | Seviye |
|---|---|---|
| 20 kareden az | Resmi tanıyorum… | ok |
| düz | Ölçülecek bir şey yok - kamerayı göğe değil seviyeye çevirin. | stop |
| karanlık | Yeniden oluşturmak için fazla karanlık. Farlar açık, ya da bu bölümü gün ışığında sürün. | stop |
| bulanık | Bulanık - yavaşlayın. | warn |
| izlenen karelerin yarısından azı takip edildi | Takibi kaybediyor - yavaşlayın ve seviyenin daha fazlasını görüşte tutun. | warn |
| izlenen karelerin %40'ından azı birleştirildi | Konumlar iyi, ama derinlik tutmuyor. Sahnelere daha yakın sürün. | warn |
| zayıf noktalar var | N zayıf nokta - harita onları işaretler. | ok |
| aksi halde | İyi - devam edin. | ok |

Seviye, üst katmanın önerisini renklendirir (yeşil / sarı / kırmızı). Üst katmandaki **keskinlik** çubuğu, karenin keskinliğinin medyana göre oranıdır. (Kodda, kamera durağanken "Bulanık ve kamera hareket etmiyor. Yakalamayı kontrol edin." mesajı da vardır; tarama kamerayı her zaman hareket halinde bildirdiği için bu gösterilmez.)
