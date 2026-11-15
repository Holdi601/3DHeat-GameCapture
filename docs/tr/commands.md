---
title: "Komut başvurusu"
nav_order: 5
lang: "tr"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Komut başvurusu {#command-reference}

Bütün komutlar depo klasöründen, projenin ortamıyla çalıştırılır:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Komut | Ne yapar |
|---|---|
| [`route`](#route) | Forza turunun yalnızca konumlarını kaydeder; haritayı oyunun dosyalarında bulmak için kullanılır |
| [`telemetry`](#telemetry) | Her kanalı, tur başına bir tur dosyası olarak kaydeder; Yarış analizi sekmesi için |
| [`laps`](#laps) | Bir FH Companion tur kitaplığını okur ve bir pistin rotasını ve örneklerini yazar |
| [`reconstruct`](#reconstruct) | Bir kaydı çevrimdışı çözer ve bir `.glb` yazar |
| [`hud`](#hud) | Kayıttan oyuncunun kendi eylemlerini, ölümlerini ve mini harita izini, ayrıca öldürme akışını okur |
| [`locate`](#locate) | Kaydın her karesinin nereden çekildiğini, bölümün render'larına göre bulur |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Tarama penceresi |
| [`python -m heat3d_update`](#updates) | Güncelleme arar ve uygular |
| [`python tools/export_onnx.py`](#the-model-converter) | Derinlik modelini ONNX'e dönüştürür |

`python -m heat3d_capture` olarak başlatıldığında araç önce daha yeni bir sürüm olup olmadığına bakar (bkz.
[Güncellemeler](updates.md); kapatmak için `HEAT3D_NO_UPDATE=1` kullanın). Herhangi bir komuttan sonra
`--help` yazarsanız o komutun seçenekleri listelenir:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Forza Data Out'u dinler ve yalnızca arabanın konumlarını tutar, başka bir şey tutmaz: derinlik modeli yok,
GPU yok, yakalama yok. Kod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `-o`, `--out` | zorunlu | Çıktı yolu; sonekiyle değiştirilir, yani `-o lap` `lap.npz` ve `lap.json` yazar. |
| `--port` | `5300` | Oyunun veri gönderdiği bağlantı noktası (127.0.0.1 üzerinde dinlenir). |
| `--seconds` | `0` | Bu kadar saniyeden sonra durur; `0` Ctrl+C'ye kadar çalışır. |

Bir konum yalnızca oyun bir yarış bildirdiğinde (`isRaceOn`), araba 0,5 m/s'den hızlı hareket ettiğinde ve
son tutulan konumdan en az 0,5 m uzaktaysa tutulur. Aksi halde menüde 60 paket/saniye ile oturmak dosyayı
başlangıç çizgisiyle doldururdu. Her örneğin zamanı oyunun yarış zamanıdır; o sıfırsa duvar saati kullanılır.
Düzen `telemetry` ile aynı şekilde algılanır (araba önce hareket etmelidir; bkz. [Forza](telemetry-forza.md)).

Saniyede bir kez alınan paketleri, tutulan konumları ve geçerli konumu yazar; ya da
`nothing on port 5300 yet - is Data Out on?` (5300 numaralı bağlantı noktasında henüz bir şey yok - Data Out açık mı?)
yazar. Rota **sürülürken kaydedilir**: yeni bir konum geldikten sonra her 2 saniyede bir (aralık, son kaydın
sürdüğü sürenin yirmi katına kadar büyür; böylece çok uzun bir oturum zamanının yirmide birinden fazlasını
yazmaya harcamaz) ve kayıt durduğunda bir kez daha - Ctrl+C, `--seconds` ya da bir istisna, sebep ne olursa olsun.
Her kayıt önce `lap.npz.partial` / `lap.json.partial` yazar, sonra bunları gerçek dosyanın üstüne taşır; böylece
diskteki dosyalar her zaman bütündür. Bir çökme ya da öldürülen bir süreç en fazla son birkaç saniyeyi kaybettirir.
Hiçbir konum tutulmadıysa Data Out'un nasıl açılacağını yazar ve çıkış koduyla 1 ile sonlanır.

Çıktı:

- `lap.npz` - NumPy dizileri `positions` (n x 3, metre), `times`, `speeds` (m/s);
- `lap.json` - bu proje olmadan okunabilir:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Konumlar oyunun kendi dünya koordinatlarıdır; bu sayede aynı zemini oyunun dosyalarında bulmak için bir tutamaç
olurlar: [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) projesinin `course` komutu bu JSON'u
alır ve turun geçtiği pisti dışa aktarır.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Her seçenek ve oyun [Telemetri kaydediciler](telemetry.md) sayfasında anlatılır.

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

FH Companion'ın tuttuğu tur kitaplığını okur ve bir pist için iki dosya yazar: oyunun arşivinden hangi harita
parçasının kesileceğini söyleyen bir rota ve her turun her örneğinin bir tablosu. İkisi birlikte yazılır, böylece
birbirinden kopamazlar. Kod:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `course` | yok | Pist adı, esnek eşleştirilir. Kitaplığı listelemek için atlayın. |
| `-o`, `--out` | pist adı, küçük harfle, boşluklar `_` olarak | Çıktı yolu; `.json` ve `.csv` yan yana yazılır. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Pist klasörlerinin bulunduğu yer. |
| `--margin` | `80` | Rotanın `bounds` değerinde, pistin x ve z yönündeki kapsamına eklenen metre. |

### Listeleme {#listing}

Pist olmadan, pist klasörlerinin sayısını ve her biri için tur dosyası sayısını (`course.json` hariç, altındaki
her `*.json`) ve pist adını yazar; ardından `Name one to write it out:  -o <file> <course>` satırını yazar.

### Pisti bulmak {#finding-a-course}

Pist klasörleri `<name> (course_<x>_<z>_to_<x>_<z>)` biçiminde adlandırılır - başlangıç ve bitiş, yuvarlanmış.
Bir pist şu sırayla aranır: tam klasör adı; klasör adının ad kısmı, büyük/küçük harf duyarsız; metni içeren tek
bir klasör. Birden fazla eşleşme bir hatadır ve eşleşenleri listeler.

### Okuma {#reading-it}

- Klasördeki `course.json`, okunabiliyorsa adı ve yuvarlanmamış başlangıç ile bitişi verir (`Name`, `StartX`,
  `StartZ`, `FinishX`, `FinishZ`); aksi halde bunlar klasör adından alınır. Başlangıç ile bitiş 10 m'den az
  aralıklıysa pist devre olarak bildirilir.
- Klasörün altındaki diğer her `*.json` bir turdur (turlar birkaç klasör derinliğinde durur - sınıfa, arabaya,
  ayara, etikete göre - ve arama yinelemeli yapılır). Dosyalar BOM'lu UTF-8 olarak okunur. Okunamayan bir tur
  atlanır. Turlar kayıt zamanına göre sıralanır.
- Tur başına: `Lap.samples` (her biri `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`, `LongG`,
  `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds` ile) ve arabanın sınıfı, sırası, performans
  endeksi, tur saniyesi, uzunluk, kayıt zamanı ve durağan başlangıç.

Bir özet yazar (tur, örnek, en iyi tur ve sınıfı, x/y/z kapsamı).

### Çıktı {#output}

**`<out>.json`** - `route`'un yazdığı rota biçiminin aynısı; böylece harita çıkarıcı ikisini de alır:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (x ve z yönünde `--margin` kadar genişletilmiş) ve
**en hızlı** turun `positions` değerleri (her turun bulanıklığı yerine tek bir çizgi).

**`<out>.csv`** - her turun her örneği, her biri bir satır:

| Sütun | Anlamı |
|---|---|
| `course` | pist adı |
| `lap` | tur başına bir etiket: kayıt tarihi ve saati dakikaya kadar, ve tur süresi |
| `car` | araba sırası |
| `car_class` | performans sınıfı harfi |
| `pi` | performans endeksi |
| `lap_seconds` | turun süresi |
| `speed_kmh` | km/s cinsinden hız |
| `x`, `y`, `z` | dünya konumu, metre, 3 ondalık |
| `speed_ms` | hız, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | FH Companion'ın kaydettiği gibi |
| `metres` | turun boyunca mesafe, 3 ondalık |
| `elapsed` | turun kendi başlangıcından beri saniye, 3 ondalık |

Konum dışındaki değerler 4 anlamlı rakama yazılır; konumlar ise sabit ondalıkla yazılır, çünkü 4 anlamlı rakam
bir pisti bir metrelik bir ızgaraya oturtur. Sütun adları, görüntüleyicinin dosyayı kendisine bir şey söylenmeden
eşlemesi için seçilmiştir: `lap` oturum olur (aynı arabanın iki turu hiçbir zaman birleşmez), `car` hareket eden
şey, `car_class` renklendirme grubu, `elapsed` zaman ekseni (her tur kendi başlangıcında hizalanır).

En sonda, haritayı GameFiles ile oyundan kesmek için bir ipucu yazar; rota dosyasını ya da açık bir kutuyu verir.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Bir kaydı çevrimdışı yeniden oluşturur; kamera yolu VGGT ile bir seferde çözülür. Yavaştır: masaüstü bir GPU'da
pencere başına dakikalar. PyTorch, Hugging Face `transformers` ve `vggt` paketi gerekir; tarayıcı bunlara ihtiyaç
duymaz. Bunlar `requirements-offline.txt` dosyasında listelenmiştir ve komut lisans satırını yazdıktan sonra
eksik olanları denetler ve kurmayı önerir (reddedilirse çıkış kodu 1). Tam açıklama:
[Çevrimdışı yeniden oluşturma](reconstruction-offline.md).

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `video` | zorunlu | Kayıt. Yoksa çıkış kodu 2. |
| `-o`, `--out` | zorunlu | Yazılacak `.glb`. |
| `--solve-budget` | `260` | Çözücüye verilecek en çok kare. Kareler saate göre değil, resmin ne kadar hareket ettiğine göre aralıklandırılır. Daha fazlası daha doğru ama çok daha yavaş demektir. Planlanan 400 kareyi aşan değer reddedilir. |
| `--fuse-interval` | `0.4` | Geometriye birleştirilen kareler arasındaki saniye. |
| `--model` | `vggt-1b` | Çözümde kullanılacak VGGT ağırlıkları: `vggt-1b` (`facebook/VGGT-1B`, ticari olmayan) ya da `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, kapılı; Meta'nın erişim vermesi gerekir). Önce yazdırılan lisans satırı o modelin lisansıdır. |

Önce modelin lisans satırını yazar, sonra her aşamayı (`masking`, `planning`, `solving`, `fusing`, `exporting`)
geçen saniye ve ilerlemeyle yazar, ve en sonda bir özet: çözülen kameralar, kapanma hatası, en kötü dikiş, notlar
ve yazılan dosya. Çıkış kodu yalnızca bir dosya yazıldıysa 0 olur.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Oyunun HUD'unu oyuncunun kendi kaydından, maçtan sonra okur: oyuncunun puan açılır penceresinden kendi
eylemleri, aşağı ve konuşlanma ekranlarından ölümleri ve dirilmeleri, mini haritadaki izi ve öldürme akışını.
`<out>.parquet` (iz ve olaylar, bir 3DHeat tablosu), `<out>.events.jsonl`, `<out>.summary.json` ve
`<out>.map.png` + `.map.json` (mini haritanın mozaiği ve görüntüleyicinin Harita görüntüsü için çapaları) yazar.
Battlefield 6 (`bf6`) şimdilik tek profildir.

PATH üzerinde **ffmpeg ve ffprobe** gerekir (`winget install Gyan.FFmpeg`, ardından yeni bir terminal).

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `video` | zorunlu | Kayıt. |
| `-o`, `--out` | videonun adı | Uzantısız çıktı yolu. |
| `--game` | `bf6` | Hangi oyunun HUD'u okunacak. |
| `--player` | tahmin edilir | Öldürme akışının gösterdiği biçimde oyuncunun adı; esnek eşleştirilir. |
| `--fps` | `5` | Saniyedeki mini harita örneği. |
| `--start`, `--seconds` | bütün video | Okunacak kayıt bölümü. |
| `--metres-per-pixel` | yok | Mini haritanın ölçeği, biliniyorsa; yoksa konumlar mini harita pikselleri olarak kalır. |
| `--cpu` | kapalı | NVIDIA kartı olsa bile CPU'da çöz. |

Tam açıklama: [Kayıttan HUD okumak](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build`, bölümü bir oyuncunun durabileceği her yerden render eder ve render'ları dizine koyar; `frames` her
örneklenmiş kareyi, resme göre bölüme yerleştirir ve yedek olarak `hud` komutunun mini harita izini kullanır;
`eval` bir sonucu bilinen kamera pozlarıyla karşılaştırır; `train`, `build --head` için bölüme özgü bir yer
modeli eğitir (bölümün render'ları ve bir çalıştırmanın zaten yerleştirdiği kareler üzerinde); `refmap`, oyunun
kendi haritasını (konuşlanma ekranı) bölüme yerleştirir ve `minimap`, bir kaydın mini haritasını bunun karşısında
kare kare okur - `frames --minimap` ile verilebilecek önseldir. PyTorch ve `requirements-locate.txt` gerekir.
**Deneysel:** gerçek kayıtlarda şimdilik karelerin yalnızca küçük bir kısmını yerleştirir. Her seçenek, çıktılar
ve yöntem: [Kareleri bir bölümde bulmak](locate.md); tam seçenek listesi: [Komut başvurusu](../cli-reference.md).

## Tarama penceresi {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ya da `scan.bat` dosyasına çift tıklayın. Seçenek yok. Bkz. [Tarama penceresi](reconstruction-scan-ui.md).

## Güncellemeler {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Bkz. [Güncellemeler](updates.md).

## Model dönüştürücü {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Bir Depth Anything V2 kontrol noktasını, tarayıcının çalıştırdığı ONNX dosyasına dönüştürür. PyTorch,
`transformers` ve `onnxscript` gerekir. Bkz. [Derinlik](reconstruction-depth.md#building-the-model).
