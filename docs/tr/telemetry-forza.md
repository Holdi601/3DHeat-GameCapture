---
title: Forza
nav_order: 1
lang: "tr"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon ve Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # oyun -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # ve FH Companion çalışmaya devam eder
```

Kod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(düzen algılama),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(her kanal, tur dosyaları, aktarma).

## Oyunda açmak {#switching-it-on-in-the-game}

Oyun içinde **Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (ya da `--port` ile verdiğiniz her ne ise). Forza Motorsport ayrıca bir paket biçimi sunar: **Dash** olmalıdır, Sled değil. Sled hiçbir konum taşımaz ve kaydedici onu reddeder.

Kaydedici `127.0.0.1`'e bağlanır, bu yüzden oyun aynı PC'de çalışmalıdır.

## Oyunun ne gönderdiği ve düzenin nasıl bulunduğu {#what-the-game-sends-and-how-the-layout-is-found}

Data Out, simülasyon tikinde bir UDP paketidir (saniyede yaklaşık 60), bu boyutlarda düz bir little-endian C yapısı:

| Uzunluk | Varyant |
|---|---|
| 232 bayt | Motorsport "Sled": konum yok. Dash'e geçmeniz gerektiğini söyleyen bir mesajla reddedilir. |
| 311 bayt | Motorsport "Dash": Sled bloğu artı 79 baytlık dash bloğu |
| 324 bayt | Horizon "Dash": aynısı, iki blok arasında dolgu ile |
| 331 bayt | Forza Motorsport (2023): Dash artı 20 bayt lastik aşınması ve pist kimliği |

Sled bloğu (ofsetler 0-231) sabittir. Horizon varyantında dash bloğunun nerede başladığı yayımlanmış kaynaklarda tutarsız biçimde anlatılır ve yanlış tahmin etmek hata vermez - yanlış alanlardan makul görünen float'lar üretir. Bu yüzden başlangıç **keşfedilir**:

1. Aday başlangıçlar sırayla denenir: `length - 79` (dash bloğu, belgelenmiş her varyantta son bayta kadar uzanır), 232, 244 ve 4'er adımla 232'den 260'a.
2. Her aday, hareket eden bir arabadan gelen paketlerde puanlanır (bir hız bileşeni 1 m/s'nin üstünde): Sled bloğunun hız vektörü ile dash bloğunun skaler `Speed` değeri, iki yerde aynı niceliktir; bu yüzden `| |velocity| - Speed |` yalnızca doğru başlangıçta sıfıra yakındır.
3. En küçük en kötü durum uyuşmazlığına sahip aday kazanır, eğer bu uyuşmazlık en fazla **1 m/s** ise. Değilse algılama beklemeye devam eder.

Araba park halindeyken her aday sıfır okur ve hepsi uyuşur; bu bir şey kanıtlamaz, bu yüzden **algılama araba hareket edene kadar bekler**: çıktı beklemeden önce birkaç metre sürün. Algılama beklerken en fazla 600 paket tutulur (en son 300'e kırpılır). Düzen bilindiğinde, tutulan paketler de çözülür, böylece ilk turun başlangıcı kaybolmaz. Algılanan düzenden farklı uzunluktaki paketler, 311 bayttan kısa paketler ve sonlu olmayan bir konum ya da hıza sahip paketler tur dosyaları için yok sayılır.

Hangi Forza olduğu düzenden anlaşılır: bir Horizon düzeni `"game": "forza-horizon"`, bir Motorsport ya da 331 baytlık düzen `"forza-motorsport"`, başka her şey `"forza"` verir. Algılanan düzenin adı (`Horizon dash`, `Motorsport dash`, `331-byte dash`) `layout` olarak yazılır.

## Kaydedilen kanallar {#channels-recorded}

Paketin her alanı çözülür (`decode_full`) ve dönüştürülür:

- pedallar `throttle`, `brake`, `clutch`, `handbrake` 0..255'ten 0..1'e;
- `steer` -127..127'den -1..1'e; `drivingLine` ve `aiBrakeDifference` da 127'ye bölünür;
- `tireTemp.FL` ... `.RR` Fahrenheit'ten Celsius'a;
- `latAcc`, `longAcc`, `vertAcc` ve `yawRate`, `accelX`, `accelZ`, `accelY` ve `angVelY`'nin kanonik adlar altındaki kopyalarıdır (araç çerçevesi: x sağa, y yukarı, z ileri);
- Sled hızı, aracın kendi çerçevesindedir (x sağa, y yukarı, z ileri - dünyanın değil), doğrudan kanonik `latVel`, `vertVel` ve `longVel` adları altında yazılır; böylece görüntüleyici savrulma açısını yönelimden ve yoldan tahmin etmek yerine bundan okur.

Tur dosyasının kanalları, tur başına alanlar dışındakilerin tümüdür:

| Grup | Kanallar |
|---|---|
| Zaman ve yer | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Hareket | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Sürücü | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Tekerlek başına (`.FL .FR .RL .RR`) | `suspension` (0 uzamış .. 1 sıkışmış), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalleştirilmiş: 1'in üstü lastiğin bıraktığı anlamına gelir), `wheelSpeed` (rad/s), `rumble` (titreşim şeridinde), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Yalnızca Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time`, oyunun geçerli tur zamanlayıcısı eksi turun ilk örneğindeki değerdir; `distance`, oyunun kat ettiği mesafe eksi ilk değeridir. Konumlar, metre cinsinden Forza'nın dünya koordinatlarıdır, değiştirilmemiş (y yukarı; dünya sol elli).

Örnek başına değil, tur başına bir kez alınan ve `car` altında yazılanlar: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. FM2023'ün pist kimliği de bir kez, `lap.trackOrdinal` olarak eklenir. Örnek başına tutulmayanlar: `isRaceOn` (bir turun her karesinde 1). `timestampMs`, `raceTime`, `bestLap` ve `lastLap` kanal olarak tutulur.

Dosyanın geri kalanı, diğer her kaydedici gibi doldurulur:

- `"track": null` - Forza Horizon pisti adlandırmaz, Forza Motorsport yalnızca numaralar;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kayma kanalları, 1'in üstü lastiğin bıraktığı anlamına gelecek şekilde normalleştirilmiştir;
- `units` yalnızca dosyada olan kanalları listeler (tekerlek başına olanlar temel adlarıyla);
- sonlu bir sayı olmayan bir değer, asla `NaN` değil, `null` olarak yazılır.

Bkz. [heat3d-lap dosyası](lap-format.md).

## Turlar nasıl bölünür {#how-laps-are-split}

`LapSplitter` (bkz. [Tur ve etap bölme](lap-splitting.md)): oyunun tur sayacı ilerlediğinde bir tur kapanır ve süresi o zaman oyunun kendi `lastLap` değeridir (oyunun gösterdiği). Noktadan noktaya bir yarış ya da tur ortasında biten bir oturum, oyun yarıştan çıktığında (`isRaceOn` düşer), paketler 2 saniye durduğunda ya da oyunun zaman damgası geriye sıçradığında kapanır; en az 400 m kapsadıysa bir `run` olarak tutulur.

## FH Companion'a aktarma {#relaying-to-fh-companion}

Oyun Data Out'u yalnızca bir adrese gönderir. `--forward host:port` ile kaydedici, aldığı **her paketi değiştirmeden** iletir; bunu, hiçbir şeyi çözmeden önce yapar (düzen algılanırken bekleme sırasında da), böylece akışı okuyan başka bir uygulama çalışmaya devam eder: oyunu 5300'e, diğer uygulamayı 5301'e ayarlayın ve `--forward 127.0.0.1:5301` ile çalıştırın.

FH Companion, 3DHeat'in parçası olmayan ayrı bir uygulamadır. `%LOCALAPPDATA%\FHCompanion\laps` altında bir tur kütüphanesi tutar: parkur başına bir klasör, her turun yaklaşık her beş metrede bir örneklenmiş bir tur dosyası, ve her tur dosyasının yanında `<lap>.json.tele.gz`, turun oyunun hızında tüm Data Out'u. 3DHeat her ikisini de okur:

- **Görüntüleyici `.tele.gz` dosyalarını doğrudan okur**, bunu Yarış analizi (Race analysis) sekmesine bıraktığınızda (tur dosyasıyla ya da onsuz). Forza'nın kendi alan adlarını (`PositionX`, `VelocityX`, `TireSlipRatio` + tekerlek, ...) kanonik kanallara eşler, araç-yerel `VelocityX/Y/Z`'yi `latVel`, `vertVel`, `longVel`'e çevirir, lastik sıcaklıklarını Fahrenheit'ten dönüştürür, kaydedicinin saati dışında önceki satırı tekrar eden satırları atar ve kaymayı `peak` olarak işaretler. Tur dosyası da verilirse, tur arabasını ve tur süresini oradan alır. Bu okuyucu bu depoda değil, görüntüleyicidedir (`src/race/adapters.ts`, `readForzaTelemetry`).
- **`laps` komutu** tur kütüphanesini okur ve bir parkurun rotasını ve her örneğin bir CSV'sini yazar; bkz. [Komut başvurusu](commands.md#laps).

## Aynı akışın diğer kullanımları {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` yalnızca konumları kaydeder, sürerken birkaç saniyede bir kaydedilir; bkz. [Komut başvurusu](commands.md#route).
- Tarama penceresinin "Racing telemetry (Forza)" seçeneği, akışı yeniden oluşturma için kesin kamera pozları olarak kullanır; bkz. [Kamera konumu ve ölçek](reconstruction-pose.md#telemetry-poses).

## Notlar ve uyarılar {#notes-and-caveats}

- Forza'nın kaymayı neye göre normalleştirdiği belgelenmemiştir. `1` tutuşun kenarı olarak okunur, ama görüntüleyici her arabanın tutuşunun gerçekte nerede azaldığını ölçer.
- Sled hızı, aracın kendi yerel çerçevesindedir; Forza'nın Data Out belgesinin dediği gibi ve kaydedilmiş turların doğruladığı gibi (ileri bileşeni hızı taşır, yan bileşeni sıfıra yakın kalır). Düzen algılama yalnızca uzunluğunu kullanır, o da her karede aynıdır.
- Konumlar oyunun dünyasıdır, Y yukarı ve sol elli. `yaw`, `pitch` ve `roll`'un yönleri kaydedilmiş turlarda doğrulandı: yaw, seyir yönüne `atan2(dx, dz)` eşittir, pozitif pitch burun aşağıdır ve pozitif roll sağ tarafı düşürür.
