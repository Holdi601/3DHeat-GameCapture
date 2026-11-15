---
title: "Tarama penceresi"
nav_order: 1
lang: "tr"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Tarama penceresi {#the-scan-window}

```bash
python -m heat3d_capture.ui        # ya da scan.bat dosyasına çift tıklayın
```

Kod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Pencere, `scan/session.py` ve `scan/reconstruct.py` üzerinde ince bir görünümdür; kendi tarama ya da geometri
mantığı yoktur.

## Başlangıç {#starting-up}

1. **Güncelleme denetimi** - bkz. [Güncellemeler](updates.md).
2. **Bağımlılık denetimi** - tarayıcının ihtiyaç duyduğu her paket, hiçbir şey içe aktarılmadan önce denetlenir;
   eksik olanlar ne için olduklarıyla ve indirme boyutuyla listelenir ve yalnızca "Download and install" seçilince kurulur.
   İptal, hiçbir şeyi değiştirmeden çıkar. Bkz. [Çalışma zamanı ve bağımlılıklar](runtime.md#first-run-preflight).
3. **Pencere** - "3DHeat — Level scanner", 1420 x 900, Qt'nin Fusion stili.
4. **Donanım denetimi** - en iyi çıkarım arka ucu seçilir, derinlik modeli yüklenir ve verimi 6 karede ölçülür; sol üstteki
   karar kutusu taramanın nasıl olacağını söyler (bkz. [Çalışma zamanı](runtime.md#what-to-expect-from-this-machine)).
5. **Genel kısayollar** en son kaydedilir.

### Henüz bir derinlik modeli yoksa {#when-there-is-no-depth-model-yet}

`models/` klasöründe bir `depth-*.onnx` yoksa karar kutusu **"One more thing to set up."** (Bir şey daha kurmanız gerekiyor.)
yazar, Başlat devre dışı kalır ve bir **Set up the depth model** (Derinlik modelini kur) düğmesi görünür. Bu düğme:

- PyTorch, `transformers` ve `onnxscript` paketlerini denetler (birlikte yaklaşık 945 MB) ve kurmadan önce sorar;
- `tools/export_onnx.py --size small` komutunu ayrı bir süreç olarak çalıştırır (böylece PyTorch hiçbir zaman tarayıcının
  belleğinde kalmaz), 30 dakikalık bir sınırla. Çalışırken pencere yanıt vermez;
- başarılıysa donanım denetimini yeniden çalıştırır; başarısızsa dönüştürücünün çıktısının son 600 karakterini gösterir.

Birden çok model varsa seçim **dosya adına göre değil, lisansa göre** yapılır: `depth-small-*` (Apache-2.0, ticari kullanıma izinli)
varsa her zaman o; sonra Base; sonra Large (ikisi de ticari olmayan). Karar kutusu ve düğmelerin altındaki gri satır, kullanılan
dosyayı, lisansını ve mevcut ama kullanılmayan diğer model dosyalarını adlandırır - örneğin `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Base ile taramak için Small dosyasını `models/` dışına taşıyın.

## Sol sütun: ayarlar {#left-column-settings}

| Grup | Denetim | Varsayılan | Aralık / değerler | Ne yapar |
|---|---|---|---|---|
| (üst) | Karar kutusu | "Checking your graphics card…" | yeşil, sarı ya da kırmızı, kademeye göre renkli | Başlık, `<device> via <API> — N views per second`, bir not ve `Depth model: <file> (<licence>)` |
| Ne taranacak | Kaynak | Whole screen (Tüm ekran) | Whole screen, A window, A video file | Karelerin nereden geldiği |
| | Hangisi | `1` | monitör numarası / pencere başlığı / bir video yolu | `monitor:<n>`, `window:<title>` ya da bir dosya yolu |
| | Choose file… (Dosya seç…) | video için gösterilir | `*.mp4 *.mkv *.avi *.mov` | Yolu doldurur |
| Ne kadar dikkatle | Ön ayar | Balanced (Dengeli) | Draft (Taslak), Balanced (Dengeli), Detailed (Ayrıntılı) | Yakalama çözünürlüğü ve anahtar karenin ne kadar seçici alındığı (aşağıda); altında tek satırlık bir özet gösterilir |
| | Game field of view (Oyun görüş alanı) | 90° | 30-140° | Oyunun **yatay** görüş alanı. Çok dar olursa bölüm olduğundan daha derin yeniden oluşturulur; çok geniş olursa düzleşir. Yarış oyunları 65° yakınındadır |
| | Surface detail (Yüzey ayrıntısı) | 0.25 m | 0.05-2.0 m, 0.05 adımla | Yüzeyin voksel boyutu. Küçük olması daha ince ama daha ağır demektir |
| Şuradan sonra dur | Süre | sınır yok | 0-120 dk | Taramayı bu kadar uzun sürdükten sonra bitirir (0 = sınır yok) |
| | Views kept (Tutulan görünümler) | 3000 | 0-100,000 | Taramayı bu kadar anahtar kareden sonra bitirir, bellek koruması olarak (0 = sınır yok) |
| Neyi yok say | Ignore HUD and anything on the camera (HUD ve kameradaki her şeyi yok say) | açık | | HUD'u, nişangâhı, silahı, kaputu, kokpiti öğrenir ve maskeler ([Yakalama](reconstruction-capture.md#what-is-not-the-world)). Altındaki satır, dedektörün şu an ne karar verdiğini söyler |
| Oynarken | Show feedback over the game (Oyunun üstünde geri bildirim göster) | açık | | Tarama sırasında tıklamaya geçirgen kaplamayı açar. Altındaki ipucu: oyunu **borderless windowed** (kenarlıksız pencere) modunda çalıştırın; tam ekran özel modunun üstüne hiçbir şey çizilemez |
| Yarış telemetrisi (Forza) | Listen for position data (Konum verisi dinle) | kapalı | | Kamera yolunu tahmin etmek yerine Forza'nın Data Out'undan alır ([Poz](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Data Out bağlantı noktası |
| | (durum satırı) | | | `N packets — poses come from the game, not from the picture` ya da `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** (Taramayı başlat / Taramayı durdur) | | | Başlatır ya da durdurur; kayıt edildiyse kısayolu gösterir |
| | **Set up the depth model** (Derinlik modelini kur) | gizli | | Yukarıya bakın |
| | **Save level…** (Bölümü kaydet…) | devre dışı | | Yüzey vokselleri üreten bir taramadan sonra etkinleşir; bir dosya adı sorar (varsayılan `scan.glb`) |
| | (gri satır) | | | `Model: <file> (<licence>) · Available: <backends>`, artı `onnxruntime-gpu` kurmak gibi kurulum notları |

### Ön ayarlar {#the-presets}

| Ön ayar | Yakalama en uzun kenarı | Tutma çeyreği | Başlangıç eşiği | Gösterilen özet |
|---|---|---|---|---|
| Draft (Taslak) | 640 px | 0.85 | 0.020 | Hızlı ve kaba. Gerçek bir taramadan önce bir rotayı kontrol etmek için iyi. |
| Balanced (Dengeli) | 960 px | 0.65 | 0.010 | Olağan seçim. Normal bir hızda yürüyün. |
| Detailed (Ayrıntılı) | 1280 px | 0.40 | 0.004 | Yavaş ve titiz. Kasıtlı yürüyün ve yavaşça dönün. |

Tutma çeyreği, "son 240 karenin değişikliklerinin bu çeyreğinden fazla değiştiğinde bir kareyi tut" anlamına gelir - Draft kabaca en
yoğun %15'i, Detailed en yoğun %60'ı tutar. Bkz. [Anahtar kareler](reconstruction-capture.md#keyframes).

### Pencerede sabit olan ayarlar {#settings-that-are-fixed-in-the-window}

Pencere taramada her zaman yeniden oluşturur, zemin-düzlemi ölçeği için **1,15 m** bir kamera yüksekliği kullanır (yürüme değeri 1,70 m
seçilebilir değildir) ve arka uç merdiveninin GPU'yu seçmesine izin verir. Bunlar yalnızca bir betiğin değiştirebildiği `ScanSettings`
alanlarıdır (`camera_height`, `prefer_backend`).

## Sağ sütun: taramanın ne yaptığı {#right-column-what-the-scan-is-doing}

| Öğe | Gösterdiği |
|---|---|
| **What the camera sees** (Kameranın gördükleri) | son anahtar kare |
| **Shape it is reading** (Okuduğu şekil) | tahmin edilen derinliği, Turbo renk haritasıyla renklendirilmiş, o karenin 2. ve 98. yüzdelikleri arasında normalleştirilmiş (böylece tek bir gökyüzü pikseli aralığı düzleştirmez) |
| **Coverage — where you have been, and how well** (Kapsam - nerede bulundunuz ve ne kadar iyi) | bir plan görünümü (aşağıya bakın) |
| **Worth another look** (Tekrar bakmaya değer) | zayıf noktalar, haritadaki halkalarla eşleşen numaralı, her biri bir talimatla; en kötüden (en büyük) başlayarak, en çok 8; sonra sizin işaretlediğiniz noktalar (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Yürüme hızı çubuğu | `walk speed — N% of the way to the next view`: son karenin resim değişikliği, **kullanımdaki eşiğe** bölünmüş - ilk 30 kare için ön ayarın başlangıç değeri, sonrasında uyarlanmış olan ([Anahtar kareler](reconstruction-capture.md#keyframes)) |
| Sağlık satırı | izleme sağlığı ya da bir yakalama uyarısı (aşağıda) |
| Boyut satırı | `Size: ...`, bölümün ölçeğinin nasıl sabitlendiği ya da neden sabitlenemediği ([Ölçek](reconstruction-pose.md#scale)) |
| İstatistik satırı | `views  frames  dropped  depth-per-second  seconds`, ve yeniden oluştururken `placed  cells  % well seen  metres`, ayrıca biri sıfır değilse `recovered` ve `loops closed` |
| Kısayol satırı | kayıtlı tuşlar ya da tuşların neden kaydedilemediği |
| İpucu satırı (sarı) | canlı tavsiye (aşağıda), taramanın son mesajı ve işaretler |

### Kapsam haritası {#the-coverage-map}

Her 900 ms'de bir arka plan iş parçacığında yeniden çizilir (asla arayüz iş parçacığında değil), 200 x 200 hücrede, 420 px'e ölçeklenmiş:

- kapsam ızgarasının her sütunu içindeki **en iyi** gözlem kalitesini alır (böylece iyi görülen bir zemin, üstündeki kötü görülen bir tavan
  tarafından sarıya boyanmaz);
- renk aralığı kırmızıdan (kötü) - sarımsı turuncu (ince) - sarı (kabul edilebilir) - yeşile (iyi) gider;
- hiç gözlenmemiş hücreler ayrı bir koyu gridir, böylece keşfedilmemiş bir köşe kötü taranmış gibi okunmaz;
- yürünen yol ince bir açık çizgiyle, geçerli konum beyaz bir noktayla çizilir;
- zayıf noktalar numaralarıyla beyaz halkalardır;
- işaretlediğiniz noktalar `M1`, `M2`, … etiketli turuncu karelerdir.

Kalite ve zayıf noktaların nasıl hesaplandığı: [Birleştirme, kapsam ve renk](reconstruction-fusion-and-texture.md#coverage).

### Sağlık satırı {#the-health-line}

| İzleme sağlığı (yerleştirilen kareler / kareler) | Metin | Renk |
|---|---|---|
| henüz kare yok | Waiting for the first frame. (İlk kare bekleniyor.) | gri |
| %90 veya daha fazla | Tracking well — N of M frames placed. (İzleme iyi - M karenin N'i yerleştirildi.) | yeşil |
| %60 veya daha fazla | Tracking is patchy — N of M frames could not be placed. Turn more slowly. (İzleme düzensiz - M karenin N'i yerleştirilemedi. Daha yavaş dönün.) | sarı |
| %60'ın altı | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. (İz kaybediliyor - M karenin yalnızca N'i yerleştirildi. Yavaş hareket edin ve boş duvarlardan ve gökyüzünden kaçının.) | kırmızı |

Kapsam ızgarasından gelen bir yakalama uyarısı bunun yerini alır (tarama yeniden oluşturulamaz bulunursa kırmızı, aksi halde sarı):
neredeyse hiç paralaks yok, her şey 25 m'den uzaktan görülmüş ya da ince paralaks. Bkz. [Kapsam](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### İpucu satırı {#the-hint-line}

| Koşul | İpucu |
|---|---|
| 6 sn sonra, karelerin yarısından fazla düşürüldüğünde | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. (Geride kalınıyor - N kare düşürüldü ... Draft kalitesini ya da daha kaba bir yüzey ayrıntısını deneyin.) |
| 8 sn sonra, saniyede 0,3 görünümden az tutulduğunda | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. (Çok az tutuluyor - hareketsiz duruyor ya da özelliksiz bir şeye bakıyor olabilirsiniz. Yerinizde dönmek yerine yana doğru hareket edin.) |
| 8 sn sonra, saniyede 8 görünümden fazla tutulduğunda | Keeping a lot. Slow down a little for cleaner geometry. (Çok şey tutuluyor. Daha temiz geometri için biraz yavaşlayın.) |
| tarama bittiğinde | oturumun mesajı: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` ya da `failed: <error>` |

## Kısayollar {#hotkeys}

Windows ile kaydedilir (`RegisterHotKey`), bu yüzden oyun odaktayken de çalışırlar. Tam ekran bir oyundan alt-tab yapmak, bir yakalamayı tam olarak bozan şeydir.

| Tuşlar | Eylem |
|---|---|
| **Ctrl+Alt+F9** | Taramayı başlat / durdur |
| **Ctrl+Alt+F10** | Bu noktayı tekrar ziyaret etmek için işaretle (tararken) |
| **Ctrl+Alt+F11** | Kaplamayı göster / gizle ("Show feedback over the game" kutusunu açıp kapatır) |

- Pencere açıldığında bir kez kaydedilirler ve kapandığında bırakılırlar; kayıtlı oldukları sürece bu tuş
  kombinasyonları oyun dahil diğer bütün programlardan alınır. İki değiştiricili F tuşları, oyunların nadiren bağladığı için seçildi.
- Otomatik tekrar bastırılır (`MOD_NOREPEAT`), böylece bir tuşu basılı tutmak taramayı düzinelerce kez açıp kapatmaz.
- Başka bir programın zaten tuttuğu bir tuş bildirilir (`... unavailable: another program already has this key`) ve diğerleri
  çalışmaya devam eder. Bir düğme, yalnızca gerçekten kaydedilmiş bir tuşu gösterir.
- Tuşlar kodda sabittir (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); ayrıştırıcı `ctrl`, `alt` ve `shift` ile F1-F12'yi kabul eder.
  Windows dışında genel kısayol yoktur ve pencere bunu söyler.
- **Mark** (İşaretle) geçerli kamera konumunu kaydeder (en son yerleştirilmiş karenin) ve "Marked MN. Marked spots are on the map and saved
  with the level." (MN işaretlendi. İşaretli noktalar haritada ve bölümle birlikte kaydedilir.) gösterir. Henüz hiçbir kare yerleştirilmemişse
  işaretlenecek bir yer olmadığını söyler. İşaretli noktalar pencerenin haritasında ve kaplamada `M1`, `M2`, … etiketli turuncu kareler olarak
  çizilir, zayıf noktaların altında listelenir, kaplamanın istatistik satırında sayılır ve bölümle birlikte kaydedilir (aşağıda).

## Kaplama {#the-overlay}

Geri bildirim oyun üzerinde olsun diye, oyunun üstüne sabitlenmiş küçük bir panel.

- Çerçevesiz, her zaman üstte, bir araç penceresi (görev çubuğunda ya da alt-tab'da değil), Qt'de girdiye saydam ve Windows'ta tıklamaya
  geçirgen (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), böylece oyuna yönelik bir tıklama asla yutulmaz. Odak almadan gösterilir.
- Birincil ekranın sağ üst köşesinde, kenarlardan 18 px uzakta; 214 x 358 px.
- Bir tarama başladığında açılır (eğer "Show feedback over the game" açıksa), durduğunda kapanır.
- **Borderless windowed modu gerektirir**: tam ekran özel modunun üstüne hiçbir şey çizilemez - ne bu, ne Steam'in kaplaması, ne Discord'unki.

Üstten alta şunları gösterir:

| Öğe | İçerik |
|---|---|
| Kapsam haritası | 190 px, pencereyle aynı harita, daha kaba 120 x 120 ile, yol, zayıf nokta halkaları ve işaretli noktalarla |
| Sağlık | pencerenin sağlık satırıyla aynı metin ve renk |
| İstatistikler | `N placed · M to revisit · X m`, herhangi biri işaretliyse `· K marked` ile |
| **hareket** çubuğu | pencerenin yürüme hızı çubuğuyla aynı: son karenin resim değişikliği kullanımdaki eşiğe bölünmüş, bir sonraki kare tutulacaksa tam |
| **keskinlik** çubuğu | keskinlik, bu yakalamanın kendi medyanına göre: 0,75'ten yeşil, 0,45'ten sarı, altında kırmızı |
| Tavsiye | tek bir talimat, yeşil / sarı / kırmızı (tamam değilse kalın) - bkz. [kare kalitesi](reconstruction-capture.md#frame-quality-and-advice) |
| Kısayollar | kayıtlı tuşlar |

Kaplamayı güncellemek bir noktada hata verirse, kırmızı bir **"Feedback stopped" (Geri bildirim durdu)** paneline geçer; bu panel,
daha önce gösterilenlerin güncel olmadığını, taramanın hâlâ çalıştığını ve ana pencerenin hâlâ doğru olduğunu, hatayı ve sayısını söyler.
Yeşilken donmuş bir panel, aksi halde onay olarak okunmaya devam ederdi.

## Kaydetme {#saving}

**Save level…** (Bölümü kaydet…) yeniden oluşturmayı bir `.glb` olarak yazar (bkz. [.glb çıktısı](glb-output.md)).
Hacim hiçbir yüzey üretmezse "Nothing to save" (Kaydedilecek bir şey yok), izlemenin taramanın büyük kısmında muhtemelen kaybedildiğini
açıklar. Başarılıysa: "Written to <path> ... Load it in 3DHeat through the Level panel." (<path> yoluna yazıldı ... 3DHeat'te Level panel
üzerinden yükleyin.), işaretli noktalar varsa işaret dosyasını da adlandırarak.

İşaretli noktalar bölümün yanına **`<name>.marks.json`** olarak yazılır:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position`, bölümün kendi koordinatlarındadır (GLB'nin ölçeği uygulanmış, böylece bir işaret üzerinde yapıldığı ağın üstünde durur),
`metres` metre cinsindendir; `number`, pencerede `M1`, `M2`, … ile eşleşir. Ölçek sonraki bir anahtar karede bulunduğunda
([Ölçek](reconstruction-pose.md#scale)), ikisi de bu çarpanı içerir.

Bir taramayı durdurmak, toplananları tutar; yeni bir **Start** önceki taramayı atar.
**Pencereyi kapatmak kaydetmeyi sormaz**: taramayı durdurur, kısayolları bırakır ve kaplamayı kapatır.
