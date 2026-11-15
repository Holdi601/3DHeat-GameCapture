---
title: Oyunlar
nav_order: 4
lang: "tr"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Oyunlar: kayıt ve parkurlar {#games-recording-and-courses}

Desteklenen her oyunun nasıl kaydedildiği, neler gönderdiği ve parkurlarının hangilerinin oyunun kendi dosyalarından dışa aktarılabileceği.

Kurallar her oyun için aynıdır: bir parkur, kullanıcının sahip olduğu dosyalardan çıkar ya da kullanıcının kendi oynanışından yeniden oluşturulur. Şifreli arşivler yalnızca kullanıcının zaten sahip olduğu bir anahtarla açılır - burada hiçbir şey anahtar içermez, anahtarları kurtarmaz ve hiçbir şey bir oyunun işlemine enjekte edilmez. Telemetri yalnızca oyunların bunun için yayımladığı arayüzlerden gelir (UDP çıkışları, paylaşılan bellek, oyunların kendi mod ve eklenti arayüzleri). Kullanıcının araçları yönlendirdiği her şey o oyunun lisansına tabidir.

## Telemetri {#telemetry}

Her oyun sonunda `heat3d-lap` dosyalarına dönüşür ([`lap-format.md`](lap-format.md)). Bu dosyalarda standart kanal adları ve sayıların ne anlama geldiğini söyleyen bir `meta` bloğu bulunur: kaymanın nasıl ölçeklendiği, pist mi ralli mi arcade mi olduğu ve biliniyorsa yüzey. Böylece bir okuyucu hepsini aynı şekilde ele alır. Tüm komutlar bu depoda `python -m heat3d_capture ...` biçimindedir.

| Oyun | Nasıl kaydedilir | Konum | Lastikler ve kayma | Savrulma açısı | Durum |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | UDP üzerinden Data Out: `heat3d_capture telemetry` (FH Companion'a iletir) - ya da her turun yanındaki FH Companion'un kendi `.tele.gz` dosyası, tur dosyasıyla birlikte yüklenir | dünya XYZ | tekerlek başına kayma oranı, kayma açısı, birleşik kayma, normalleştirilmiş; yüzey titreşimi | araç çerçevesinde hız | kaydedici test edildi; `.tele.gz` okuyucusu gerçek turlarda denetlendi |
| Forza Motorsport (2023 dahil) | aynı; paket uzunluğuna göre ayırt edilir | dünya XYZ | aynı | aynı | kaydedici test edildi |
| Assetto Corsa, ACC, AC EVO | paylaşılan bellek: `telemetry --game ac / acc / acevo` | lastik temas noktalarının ortalaması | kayma oranı ve açısı (fiziksel, bir asfalt tepe değerine göre ölçeklenmiş); ABS ve TC devrede (ACC, EVO) | araç çerçevesinde hız | kaydedici sahte sayfalar üzerinde test edildi |
| Assetto Corsa Rally | `telemetry --game acrally` | aynı | aynı; tekerlek yükleri; sıcaklıklar kelvinden çevrildi | araç çerçevesinde hız | kaydedici sahte sayfalar üzerinde test edildi |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Belgeler>/My Games/WRC/telemetry/config.json"` varsayılan `wrc` paketini açar (dosya önce yedeklenir) | dünya XYZ | tekerlek başına temas yüzeyi hızı; kayma türetilir | aracın eksenlerinden ve hızından | kaydedici, belgelenmiş düzenden oluşturulmuş paketler üzerinde test edildi |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: `hardware_settings_config.xml` içinde `<udp enabled="true" extradata="3" port="20777" delay="1" />`, sonra `telemetry --game dirtrally2` (ya da `dirtrally`, `dirt4`) | dünya XYZ | tekerlek başına temas yüzeyi hızı; kayma türetilir. El freni kanalı yok | aracın eksenlerinden ve hızından | aynı |
| Richard Burns Rally (RSF/NGP) | NGP'nin UDP telemetrisi (`udpTelemetry=1`): `telemetry --game rbr` | dünya; yukarı ekseni etaptan bulunur | tekerlek başına yay sapması ve kuvveti; tekerlek hızı yok | aracın kendi hızları | aynı; eksenler ve hız birimleri belgelenmemiş, veriden ele alınır |
| BeamNG.drive | `heat3d` protokol modu: `telemetry --game beamng --install`, sonra oyunda Options > Other > Protocols > "others" | dünya, Y yukarı olacak şekilde çevrilmiş | tekerlek yüzey hızı, dönüş, yük, yere temas; kayma türetilir | aracın eksenlerinden ve hızından | kaydedici, modun yapısından oluşturulmuş paketler üzerinde test edildi; mod oyunda test edilmedi |
| Trackmania (2020) | Openplanet eklentisi `Heat3dRecorder`: `telemetry --game trackmania --install`, Openplanet'in geliştirici modunda yüklenir; her koşu için depolama klasöründe bir CSV | dünya XYZ | Trackmania'nın tekerlek başına kayma katsayısı; tekerleklerin malzemelerinden gevşek zemin; havada olma | ön ve yan hız | okuyucu test edildi; eklenti oyunda test edilmedi |
| iRacing | kendi `.ibt` dosyaları; kaydediciye gerek yok | enlem/boylam/yükseklik, bir teğet düzleme yerleştirilmiş | kayma yok (kaydedilmiyor); yaw oranı ve yanal ivme | yaw oranından, yola karşı | okuyucu sentetik bir dosya üzerinde test edildi |

Hiçbir rally oyununun göndermediği - lastik kayması - bir okuyucu tarafından hesaplanır: bir oyun temas yüzeyi ya da yüzey hızı gönderiyorsa her tekerleğin bu hızının aracın hızına karşı (`(wheel - car) / car`) farkından, yalnızca dönüş gönderiyorsa dönüşünden ve turun kendisinde ölçülen bir yuvarlanma yarıçapından. Savrulma açısı aracın kendi hızından gelir (Forza, AC oyunları, Trackmania, RBR), dünya hızının aracın eksenlerine izdüşümünden (EA WRC, DiRT, BeamNG) ya da yönelimin yola karşı açısından. Aracın havada olup olmadığı tekerleklerinin temasından, yüklerinden ya da süspansiyonundan anlaşılır.

Bir oyunun dünyası sol elli ise - Forza'nınki öyledir - parkur, sağ elli bir görüntüleyicide aynalanmış çıkar; turların kendi direksiyon ve süspansiyon verileri bunu ortaya çıkarır. Yönü belgelenmemiş oyunlar (RBR, BeamNG, Trackmania) aynı şekilde ele alınır: varsayılmaz, ölçülür.

Sürüş kanallarının ötesinde kaydediciler, her oyunun eklediklerini de tutar: AC oyunlarının ABS ve çekiş kontrolünün devrede olması, fren dağılımı, DRS, pit limiter, turbo ve fren balatası ile disk ömrü; iRacing'in yardım ayarları, fren dağılımı, yakıt, yağ ve su sıcaklıkları ve kendi adıyla kaydettiği her diğer kanal.

### Kaynaklar ve henüz doğrulanmamış olanlar {#sources-and-what-is-not-yet-confirmed}

- **Forza:** alanlar, birimleri ve araç çerçevesi (x sağa, y yukarı, z ileri - sol elli) için Forza'nın resmi Data Out belgeleri (Forza Motorsport; Forza Horizon 6). Forza'nın kaymayı neye göre normalleştirdiği belgelenmemiştir: 1'in sınır olduğunu varsaymak yerine her aracın tutuşunun gerçekte nerede azaldığını ölçün.
- **Kunos:** AC1 SDK, ACC paylaşılan bellek belgesi v1.8.12, `albertowd/live-telemetry-evo` (EVO, ölçülmüş; AC Rally ACC'nin düzenini kullanır, "byte-by-byte probe ile doğrulandı"), `LuizZak/AssettoCorsaRallyTelemetryReader`. Aracın x ekseninin hangi tarafı gösterdiği iki yönde de belgelenmiştir: işaretine değil, savrulma açısının büyüklüğüne bakın.
- **EA SPORTS WRC:** EA'nın UDP Telemetry Guide v1.3 belgesi ve oyunun `readme/channels.json` dosyasına yazdığı kanal listesi; varsayılan `wrc` paketinin ofsetleri nobonobo/obs-codemasters-telemetry tarafından çözülmüştür. Varsayılan port belgelenmemiştir; kaydedici paketi 20777'de açar.
- **DiRT:** Codemasters'ın DiRT 4 UDP belgesi, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Yan vektörün yönü ve süspansiyon konumunun birimi iki yönde de belgelenmiştir; hiçbiri bir bulguyu belirlemez.
- **RBR:** NGP'nin `rbr.telemetry.data.TelemetryData.h` dosyası (mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem üzerinden). Konum eksenleri, tutum birimleri ve hız birimi belgelenmemiştir: kaydedici yukarıyı etaptan, hızı konumlardan alır.
- **BeamNG:** documentation.beamng.com (protokoller; refNodes: araç +X sol, -Y ileri, Z yukarı) ve oyunun kendi `lua/vehicle/protocols.lua` ile `wheels.lua` dosyaları. OutSim güncel sürümlerde bir taslaktır; OutGauge'da konum, MotionSim'de tekerlek yoktur, bu yüzden mod gerekir.
- **Trackmania:** Openplanet'in `CSceneVehicleVisState` ve VehicleState eklentisi, `CSmScriptPlayer` yarış süresi. Openplanet eklentileri UDP gönderemez, bu yüzden eklenti dosya yazar. İmzasız eklentiler yalnızca geliştirici modunda yüklenir; bu da çevrimiçi oynamayı sınırlar. Eklenti openplanet.dev üzerinde imzalanabilir.

Kaydedicilerin hiçbiri henüz burada canlı oyunlara karşı çalıştırılmadı; her birinin ilk gerçek oturumu asıl sınavdır. `tests/test_kunos.py`, `test_rally.py` ve `test_beamng.py` dosyaları, kaydedicilerin yazıldığı düzenleri sabitler. Her kaydedici paketlerini geldikçe denetler - hızla karşılaştırılan hız vektörünü, yapının boyutunu - ve bir düzen uymadığında bunu söyler.

## Parkurlar: oyun başına neyin dışa aktarıldığı {#courses-what-is-exported-per-game}

Bir parkur, bir çizgiyi açıklayan bordürleri, duvarları ve kaçış alanlarını ekler. Parkurlar, oyunun kendi dosyalarından [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) tarafından dışa aktarılır (`python -m heat3d_gamefiles course <lap>`); bu yalnızca kurulu bir kopya üzerinde oluşturulup denetlenmiş olduğu yerlerde yapılır. Ayrıntılar [GameFiles belgelerinde](https://holdi601.github.io/3DHeat-GameFiles/) bulunur.

| Oyun | Bir turdan parkur |
|---|---|
| Forza Horizon | evet |
| BeamNG.drive | evet |
| Assetto Corsa Rally | evet |
| Assetto Corsa EVO | hayır: içeriği dosya olarak okunamaz |
| iRacing | hayır: pist modelleri korumalı bir biçimde gelir |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | henüz değil: her biri oluşturulup denetlenmek için kurulu bir kopyaya ihtiyaç duyar |

Bu arada aşağıdaki oynanış yolu hepsi için çalışır.

## Her oyun için çalışan yol {#the-route-that-works-for-every-game}

GameCapture bir seviyeyi oyun videosundan yeniden oluşturur. En zor kısmı kamera yoludur ve Forza için kesindir, çünkü telemetri aracın konumunu her karede verir. Yukarıdaki her oyun artık aynı şeye sahip: belgelenmiş canlı bir arayüzden konum ve tutum. Bunları Forza'nınkinin yerine `pose/telemetry_pose.py` dosyasına beslemek, oynanış yolunu tüm bu oyunlar için kesin yapan tek parçadır. Bu hattın geri kalanı (derinlik, birleştirme, dokulandırma) karelerin hangi oyun tarafından çizildiğini umursamaz.
