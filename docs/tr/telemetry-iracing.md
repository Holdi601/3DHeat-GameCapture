---
title: iRacing
nav_order: 6
lang: "tr"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing için **kayıt cihazı gerekmez**. Telemetri kaydı açıkken (araçta Alt+L) simülatör kendi telemetri
dosyalarını, `.ibt` dosyalarını yazar: oturumun tamamı 60 Hz'de, simülatörün gösterdiği her kanal ve yanında
oturumun YAML açıklaması. `.ibt` dosyasını görüntüleyicinin Yarış analizi sekmesine bırakın.

Okuyucu bu depoda değil, görüntüleyicinin içindedir (3DHeat görüntüleyicisinde `src/race/ibt.ts`). Sentetik
bir dosya üzerinde test edilmiştir; burada, aynı tur kaydetme hikâyesinin iRacing tarafı olduğu için
belgelenmiştir.

## Dosyada ne var ve nasıl okunur {#what-the-file-holds-and-how-it-is-read}

Dosya, simülatörün belgelenmiş bellek düzeninin diske yazılmış hâlidir:

| Bölüm | Boyut | İçerik |
|---|---|---|
| Üstbilgi | 112 bayt | sürüm, tik hızı, YAML'in ve değişken tablosunun nerede olduğu, bir örnek satırının uzunluğu, satırların nerede başladığı |
| Disk alt üstbilgisi | 32 bayt | başlangıç tarihi ve saati, tur sayısı, satır sayısı |
| Değişken tablosu | kanal başına 144 bayt | tür, satırdaki ofset, sayı, ad, açıklama, birim |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Satırlar | tik başına bir | |

Dosya şu durumlarda reddedilir: 144 bayttan kısaysa; üstbilgisi makul değilse (değişken yoksa, değişken
tablosu dosyanın dışındaysa ya da satır uzunluğu sıfırsa); `SessionTime`, `Lap`, `Lat`, `Lon` değerlerinden
herhangi biri yoksa; ya da hiçbir örnekte konum bilgisi yoksa.

## Konum {#position}

iRacing, parkurun kendi çerçevesinde bir konum değil, enlem, boylam ve yükseklik bildirir. Konumlar, ilk
konum bilgisi olan örnekte teğet bir düzlemde metre cinsinden hesaplanır (Dünya yarıçapı 6.371.008,8 m): `x`
doğu, `z` güney, `y` yükseklik - böylece yukarıdan, görüntüleyici kamerasının varsayılan yönüyle, kuzey ekranın
yukarısındadır.

## Turlar {#laps}

Oturum simülatörün `Lap` sayacına göre bölünür. Bir tur yalnızca 60'tan fazla örnek içeriyorsa, `LapDistPct`
değeri %5'in altında başlıyorsa ve %95'in üstünde bitiyorsa tutulur - yani çizgiden çizgiye sürülen turlar. Hiçbir
tur uymazsa dosya, YAML'deki parkur uzunluğunu belirten bir mesajla reddedilir. `distance`, turun başlangıcına
göre yeniden tabanlanmış `LapDist` değeridir; `LapDist` yoksa konumlardan hesaplanan sürülen mesafedir; `time`,
turun başlangıcından itibaren `SessionTime` değeridir.

## Kanallar {#channels}

| iRacing | Kanal | Dönüşüm |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | yok |
| `Clutch` | `clutch` | `1 - değer` (iRacing debriyajı devrede sayar; kanal pedaldır) |
| `SteeringWheelAngle` | `steer` | `-açı / SteeringWheelAngleMax` (radyan, saat yönünün tersi pozitif, -1..1 sağ pozitif; maksimum yoksa pi) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | yok |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | yok |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | yardımcı ayarlar |
| `dcBrakeBias` | `brakeBias` | bazı arabalarda yüzde olduğu için 1,5'in üstündeyse 100'e bölünür |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | ortasından ölçülen gövde sıcaklığı |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa çarpı 0,145038, psi'ye |
| `..wearM` | `tireWear.*` | `1 - değer` |

Örnek başına tek değeri olan ve tek bayt olmayan diğer her kanal kendi adıyla geçirilir; tekerlek öneki
(`LF`, `RF`, `LR`, `RR`) bir sonek olur (`.FL`, `.FR`, `.RL`, `.RR`). Böylece görüntüleyicinin grafikleri,
kimse tarif etmeden onları sunar.

Araba `DriverInfo` bölümünden gelir: `CarIdx` değeri `DriverCarIdx` ile eşleşen girdi `CarScreenName`,
`CarID` ve `CarClassShortName` değerlerini verir. Parkur `TrackDisplayName` (ya da `TrackName`) değeridir.

## iRacing'in vermediği şeyler {#what-iracing-does-not-give}

Lastik kayması kaydedilmez, bu yüzden kayma kanalı yoktur. Sürüklenme açısı, yaw oranından yola göre
türetilir (bkz. [Kayma, drift ve türetilmiş kanallar](slip-and-drift.md)). Parkur modelleri korumalı bir
biçimde dağıtılır ve dosya çıkarma hedefi değildir (bkz. [Oyunlar](games.md)).
