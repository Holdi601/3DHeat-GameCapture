---
title: Kurallar
nav_order: 2
lang: "tr"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Bu aracın altında çalıştığı kurallar {#the-rules-this-is-built-under}

3DHeat GameCapture'ın her parçası aynı kısıtlara uyar. Bunlar tasarım kararlarıdır, sorumluluk reddi
değildir; birkaçı bilerek doğruluktan ödün verir.

## Hiçbir şey enjekte edilmez, hiçbir şey kancalanmaz {#nothing-is-injected-nothing-is-hooked}

Bunun hiçbir parçası bir oyun işlemine bağlanmaz, onun belleğini okumaz ve grafik API'sine dokunmaz.

- **Kareler** Windows Graphics Capture'dan gelir - ekran kayıt programlarının kullandığı herkese açık
  API (`windows-capture` paketi üzerinden) - ya da bir video dosyasından. Bkz.
  [Yakalama, maskeler ve kare kalitesi](reconstruction-capture.md).
- **Telemetri** yalnızca oyunların bunun için yayımladığı arayüzlerden gelir:
  - Forza'nın Data Out UDP akışı, oyunun ayarlarında açıldığında;
  - Kunos oyunlarının uygulamalar için yayımladığı, adlandırılmış paylaşımlı bellek sayfaları
    (`Local\acpmf_physics` ve benzerleri). Salt okunur `mmap` ile açılırlar; bu, uygulamaların onları
    okumasının belgelenmiş yoludur, oyun sürecinin belleğini okumak değildir;
  - EA SPORTS WRC, DiRT oyunları ve Richard Burns Rally'nin (RSF/NGP eklentisi üzerinden) kendi ayar
    dosyalarında açıldığında gönderdiği UDP telemetrisi;
  - BeamNG'nin protokol arayüzü, oyunun kendi `lua/vehicle/protocols.lua` dosyasının yüklediği ve
    gönderdiği küçük bir Lua "protokol" modu üzerinden;
  - Trackmania'nın Openplanet eklenti arayüzü, yalnızca Openplanet'in açtığını okuyan ve dosya
    yazan bir eklenti üzerinden;
  - iRacing'in kendi `.ibt` telemetri dosyaları.

## Neden önemli {#why-it-matters}

Oyun her pikselin derinliğini kesin olarak bilir ve kancalanmış bir derinlik tamponu seviye yeniden
oluşturmayı neredeyse mükemmel ve önemsiz kılardı. Ama bu, anti-hile korumalı olabilecek süreçlere
enjekte etmek anlamına da gelirdi; bunu çalıştıran herkesin hesabını riske atar. Bu yüzden derinlik
görüntüden *tahmin edilir* ([Derinlik](reconstruction-depth.md)) ve yeniden oluşturma boru hattının
büyük kısmı, kaybolan doğruluğun mümkün olduğunca fazlasını serbestçe kullanılabilir kaynaklardan geri
kazanmak için vardır: oyunların yayımladığı yerlerde telemetri pozları, yayımlamadıklarında zemin düzlemi
ölçeği ve HUD ile kokpitin çözümün dışında kalmasını sağlayan maskeler.

ReShade'in derinlik tamponu düşünüldü ve kullanılmadı. ReShade, çok oyunculu oturumlarda tasarım gereği
derinlik erişimini kapatır; bu yüzden yalnızca tek oyunculu oyunlara yardımcı olurdu (bkz.
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Araçın makinenizde değiştirdikleri, yalnızca istenince {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Eylem | Ne zaman | Tam olarak ne |
|---|---|---|
| Python paketlerini kurar | tarama penceresinin ilk çalıştırması, bir iletişim kutusu ve evetten sonra | aracı çalıştıran yorumlayıcıya `pip install` - `scan.bat` ile, yanındaki özel `.venv`'e. Kendi başına asla sistem genelinde değil. |
| Derinlik modelini dönüştürür | "Derinlik modelini kur" düğmesi, PyTorch ve benzerleri için ikinci bir iletişim kutusundan sonra | `models/depth-small-518.onnx` yazar |
| EA SPORTS WRC'nin `config.json` dosyasını düzenler | `telemetry --game wrc --configure <file>` | `wrc` / `session_update` paketini 127.0.0.1'e açar; eski dosya `config.json.bak` olarak saklanır |
| BeamNG modunu kopyalar | `telemetry --game beamng --install` | `mods/beamng/heat3d` dosyasını `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` konumuna kopyalar (eski kopyanın yerine) |
| Trackmania eklentisini kopyalar | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` dosyasını `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` konumuna kopyalar (eski kopyanın yerine) |
| Genel kısayol tuşlarını kaydeder | tarama penceresi açıkken (Windows) | Ctrl+Alt+F9 / F10 / F11; pencere kapanınca serbest bırakılır |
| Aracı günceller | güncelleme isteminde evet dedikten sonra ya da `python -m heat3d_update` ile | bkz. [Güncellemeler](updates.md) |

DiRT oyunlarının `hardware_settings_config.xml` dosyası ve Richard Burns Rally'nin
`RichardBurnsRally.ini` dosyası aracın **değiştirmediği** dosyalardır; UDP çıktısını siz kendiniz açarsınız
(bkz. [Ralli oyunları](telemetry-rally.md)).

## Neyin okunduğu ve makinenizde ne kaldığı {#what-is-read-and-what-stays-on-your-machine}

Araçlar, oyunun ekranda gösterdiğini ve oyunun bunun için yayımladığı telemetri ile dosyaları kendi bilgisayarınızda okur. Bir oyundan hiçbir şey birlikte dağıtılmaz veya yeniden dağıtılmaz: oyun varlıkları yok, oyun kodu yok, DLL yok. Tur dosyaları, kayıtlar, yeniden yapılandırmalar ve dışa aktarılan pistler makinenizde kalır; deponun `.gitignore` dosyası kayıtları, tur dosyalarını, ağları, model ağırlıklarını ve videoyu klasöre ve dosya türüne göre sürüm denetiminin dışında tutar.

3DHeat GameCapture hiçbir oyun yayıncısıyla bağlantılı değildir ve hiçbiri tarafından onaylanmamıştır. Oyun adları ve ilgili ticari markalar sahiplerine aittir. Hak sahipleri: [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) adresinde bir issue açın - hızlı yanıt veririz ve istek üzerine her şeyi kaldırırız.
