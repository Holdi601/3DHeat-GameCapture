---
title: BeamNG.drive
nav_order: 4
lang: "tr"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # modu kopyala, sonra kaydet
python -m heat3d_capture telemetry --game beamng -o laps      # kaydet
```

Sonra oyunda: **Seçenekler > Diğer > Protokoller** yolunu izleyin ve **"others"** seçeneğini açın.

Kod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
ve mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testler: `tests/test_beamng.py`, modun yapısından kurulmuş paketler üzerinde. **Mod henüz oyunda
çalıştırılmadı.**

## Neden bir mod {#why-a-mod}

BeamNG, telemetriyi "protokoller" üzerinden gönderir: aracın içindeki, oyunun kendi
`lua/vehicle/protocols.lua` dosyasının paketlediği ve oyuncunun sürdüğü arabadan UDP üzerinden gönderdiği
Lua modülleri. Hazır olanlar bir araba kontrol analizinin ihtiyaç duyduğunu taşımaz - OutGauge'un konumu
yoktur, MotionSim'in tekerleği yoktur ve OutSim güncel sürümlerde bir taslaktır. Bu yüzden proje kendi
protokolünü, `heat3d`'yi getirir. Aracın kendi Lua'sının dışındaki hiçbir şeye dokunmaz.

## Kurulum {#installing}

`--install`, `mods/beamng/heat3d` klasörünü
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` konumuna kopyalar (BeamNG 0.30 ve sonrası
kullanıcı modlarını orada tutar), önce eski bir kopyayı siler ve nereye gittiğini yazdırır. `LOCALAPPDATA`
yoksa ev klasörüne geri döner. Klasörü elle de kopyalayabilirsiniz.

Ardından `--install`, doğrudan kayda devam eder.

## Mod {#the-mod}

| Ayar (`heat3d.lua` içinde) | Değer |
|---|---|
| Adres | `127.0.0.1` |
| Bağlantı noktası | `4460` - burada değiştirin ve kayıt cihazına aynı `--port` değerini verin |
| En yüksek güncelleme hızı | 100 Hz |
| Fizik adımı | kullanılır (`isPhysicsStepUsed` true döndürür) |

Her paket, 4 baytlık `H3D1` işaretiyle başlar, ardından 39 little-endian float gelir (toplam 160 bayt):

| Alan | Sayı | Araç Lua'sındaki kaynak |
|---|---|---|
| `time` | 1 | modun kendi saati: fizik adımlarının toplamı, araç sıfırlanınca sıfırlanır |
| konum | 3 | `obj:getPositionXYZ()` |
| hız | 3 | `obj:getVelocityXYZ()` (dünya) |
| ileri | 3 | `obj:getDirectionVector()` |
| yukarı | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex` ve `absActive` ile `tcsActive` değerinden 1/0 |
| `wheelSpeed` | 4 | her tekerleğin yüzey hızı (m/s) |
| `wheelAngular` | 4 | açısal hız çarpı tekerleğin yönü (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`; yerden kesilmişse -1 |

Dört tekerlek **adlarına göre değil, araba üzerindeki konumlarına göre** seçilir (adlar araçtan araca
değişir): ön ya da arka, düğümün arabanın boyunca konumuna göre; sol ya da sağ, arabanın genişliği boyunca
(araç çerçevesinde +X sol, -Y ileri); her köşe için merkezden en uzaktaki tekerlek alınır. Eksik bir köşe
sıfırlar ve -1 malzemeyle gönderilir.

## Kaydediciyi bunu nasıl kullanır {#what-the-recorder-does-with-it}

BeamNG'nin dünyası Z yukarı, görüntüleyicinin dünyası Y yukarıdır. Konumlar ve vektörler X ekseni etrafında
döndürülür, `(x, y, z) -> (x, z, -y)`; bu, dünyanın el yapısını korur. Sonra:

| Kanal | Türetilmesi |
|---|---|
| `x`, `y`, `z` | döndürülmüş konum |
| `speed` | döndürülmüş hızın uzunluğu |
| `longVel`, `latVel`, `vertVel` | hızın ileri, sağ (= ileri x yukarı) ve yukarı eksenlerine izdüşümü |
| `longAcc`, `latAcc`, `vertAcc` | dünya hızındaki değişim, ±2 örnek üzerinden, aynı eksenlere izdüşürülmüş (arabanın kendi sensörlerinin çerçevesi belgelenmemiştir, bu yüzden kullanılmazlar) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | gönderildiği gibi |
| `absActive`, `tcActive` | ABS ve TC lambaları, arabanın sahip olduğu yerlerde |
| `wheelSurfaceSpeed.*` | tekerleğin yüzey hızının mutlak değeri |
| `wheelSpeed.*` | dönüş |
| `wheelLoad.*` | yük |
| `groundContact.*` | malzeme negatifse 0, değilse 1 |

Başında işaret olmayan ya da 160 bayttan kısa paketler yok sayılır.

## Turlar {#laps}

`LineSplitter`, AC EVO'da olduğu gibi: kaydın başladığı nokta çizgidir; bir tur, arabanın aynı yönde
giderken en yakın geçtiği noktada, en az 300 m sonra kapanır; bir koşu, araba 8 saniye boyunca durduğunda
kapanır. Bir tur, yalnızca 5 m/s'den hızlı başladıysa tam sayılır; bu yüzden durgun bir başlangıçtan gelen
ilk tur kısmidir. Modun saati yarım saniyeden fazla geriye giderse (araba sıfırlanmıştır), o anda açık olan
koşu önce kapanır - en az 300 m kat ettiyse kısmi bir koşu olarak yazılır, kaydın sonunda olduğu gibi - ve
sonra ayırıcı baştan başlar. Bkz. [Tur ve etap ayırma](lap-splitting.md).

## Tur dosyası {#the-lap-file}

`game` değeri `beamng`, `meta` değeri `{"discipline": "circuit"}` dir; dosyalar
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json` adıyla adlandırılır. Kayma yazılmaz; görüntüleyici
bunu tekerlek yüzey hızlarından türetir (bkz. [Kayma, drift ve türetilmiş kanallar](slip-and-drift.md)).
Konumlar, GameFiles BeamNG parkur dışa aktarımının yazdığı çerçevededir; böylece kaydedilen bir tur,
dışa aktarılan bir parkurun üzerine oturur.
