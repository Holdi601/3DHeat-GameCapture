---
title: Ralli oyunları
nav_order: 3
lang: "tr"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # ya da dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testler: `tests/test_rally.py`, belgelenmiş düzenlerden oluşturulmuş paketler üzerinde. **Henüz canlı oyunlara karşı çalıştırılmadı.**

Hepsi, oyunun kendi ayar dosyalarından açtığı UDP gönderir. Kaydedici, `--port` başka bir port vermedikçe oyunun varsayılan portunda tüm arayüzlerde (`0.0.0.0`) dinler: `wrc`, `dirtrally2`, `dirtrally`, `dirt4` için **20777**; `rbr` için **6776**.

## EA SPORTS WRC {#ea-sports-wrc}

### Açmak {#switching-it-on}

Oyun `Documents\My Games\WRC\telemetry\config.json` dosyasını okur. Varsayılan `wrc` yapısının `session_update` paketinin bu makineye doğru açık olması gerekir:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<config.json yolu>"
```

`--configure` (`configure_wrc` fonksiyonu):

- JSON'u okur, `udp.packets`'i ve `"structure": "wrc"` ile `"packet": "session_update"` olan girdiyi bulur;
- kullanılan porta `127.0.0.1` ya da `localhost` için zaten açıksa `already on` yazdırır ve hiçbir şey değiştirmez;
- aksi halde `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` ayarlar ve girdinin `frequencyHz` değerini korur (yoksa `-1`); böyle bir girdi yoksa bir tane ekler;
- orijinal metni yanına `config.json.bak` olarak yazar, sonra yeni dosyayı yazar (4 boşlukla girintili).

Dosyayı değiştirdikten sonra oyun değişikliği almazsa oyunu yeniden başlatın (denenmedi).

### Ne gönderir {#what-it-sends}

Varsayılan `wrc` yapısı 237 bayttır, little-endian, başlık yok: dünya konumu, hızı ve ivmesi (X sol, Y yukarı, Z ileri), arabanın sol / ileri / yukarı birim vektörleri, tekerlek başına (arka sol, arka sağ, ön sol, ön sağ) göbeğin yüksekliği ve dikey hızı ile temas yüzeyinin ileri hızı, fren sıcaklıkları, yardımlardan sonraki pedallar, direksiyon (-1 sol, +1 sağ), el freni, rpm, vites ve etap saati, mesafe ve uzunluk. 237 bayttan kısa bir paket yok sayılır ve bir kez bildirilir.

| Kanal | Kaynak |
|---|---|
| `x`, `y`, `z` | dünya konumu |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | dünya hızı ileri üzerine, sol'un eksisi üzerine (böylece pozitif sağdır), yukarı üzerine izdüşümü |
| `longAcc`, `latAcc`, `vertAcc` | dünya ivmesi aynı şekilde izdüşümü |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | gönderildiği gibi |
| `gear` | `gear_index`; geri vites indeksine eşitse -1, boşta indeksine eşitse 0 |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | göbek konumu |
| `wheelSurfaceSpeed.*` | temas yüzeyinin ileri hızı |
| `brakeTemp.*` | fren sıcaklığı |

Kontrol: `speed` 10'un üstündeyse ve dünya hızının uzunluğu ondan %20'den fazla farklıysa, kaydedici düzenin varsayılan `wrc` yapısı olmayabileceğini bir kez yazdırır.

Bir etap, etap uzunluğu pozitif olduğunda ve mesafe uzunluğun 0,5 m eksiğine ulaştığında **bitmiş** sayılır. Bölme ve `time` için kullanılan saat `stage_time`'dır.

Kaynaklar: EA'nın UDP Telemetry Guide v1.3 belgesi; oyunun `readme/channels.json` dosyasına yazdığı kanal listesi; nobonobo/obs-codemasters-telemetry ve SpaceMonkey tarafından çözülen ofsetler. Varsayılan port belgelenmemiştir; kaydedici 20777 kullanır.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Açmak {#switching-it-on-1}

`Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` dosyasını düzenleyin (DiRT Rally ve DiRT 4 de bir `hardware_settings_config.xml` kullanır; bu ikisinin tam klasörü burada kontrol edilmedi) ve `udp` öğesi şöyle okunsun:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"`, konumları, tekerlekleri ve etap uzunluğunu pakete koyan şeydir. Kaydedici bu dosyayı düzenlemez.

### Ne gönderir {#what-it-sends-1}

66 little-endian float (DiRT Rally: 64); 64 float'tan kısa paketler yok sayılır ve 64 float'lık bir paket sıfırlarla doldurulur. Kullanılan indeksler:

| İndeks | Alan | Kanal |
|---|---|---|
| 1 | etap (tur) zamanı | bölme saati ve `time` |
| 2 | tur mesafesi | `stageDistance` |
| 4-6 | dünya konumu | `x`, `y`, `z` |
| 7 | hız | `speed` |
| 8-10 | dünya hızı | `longVel` (ileri üzerine), `latVel` (yan vektör üzerine) |
| 11-13 | yan vektör | |
| 14-16 | ileri vektör | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | süspansiyon konumu RL RR FL FR | `suspensionM.*` |
| 25-28 | tekerlek temas hızı RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gaz, direksiyon, fren, kavrama, vites | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ya da üstü geri demektir, -1 yazılır) |
| 34, 35 | yanal, boyuna g | `latAcc`, `longAcc` (çarpı 9,80665) |
| 37 | rpm / 10 | `rpm` (çarpı 10) |
| 51-54 | fren sıcaklıkları | `brakeTemp.*` |
| 59, 60, 61, 62 | tamamlanan tur, toplam tur, pist uzunluğu, son tur süresi | bölme |

**El freni kanalı yoktur.** Yan vektörün yönü iki yönde de belgelenmiştir, bu yüzden `latVel`'in işaretine güvenilmemelidir (görüntüleyici savrulma açısının büyüklüğünü okur).

Bir etap, tamamlanan tur sayısı başlangıçtaki değerinin üstüne çıktığında (her seferinde bir rallycross turu), ya da tek turluk bir etkinlikte tur mesafesi pist uzunluğunun %99,9'una ulaştığında **bitmiş** sayılır. Etabın süresi, pozitifse oyunun son tur süresidir. Kontrol: EA WRC'deki gibi hız ile hızın karşılaştırılması, "is extradata set to 3?" mesajıyla.

Kaynaklar: Codemasters'ın DiRT 4 UDP belgesi; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Açmak {#switching-it-on-2}

`RichardBurnsRally.ini` dosyasında, `[NGP]` bölümünde: `udpTelemetry=1` ve uç nokta (127.0.0.1, `--port` ile başka bir port vermediğiniz sürece port 6776). Kaydedici bu dosyayı düzenlemez.

### Ne gönderir {#what-it-sends-2}

664 bayt (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): etap saati ve bitişe mesafe, pedallar, direksiyon, vites, dünya konumu, tutum, arabanın kendi hızları (ileri-sürüş, yanal kayma, dikey hareket), ivmeler, rpm ve dört 128 baytlık tekerlek bloğu (LF, RF, LB, RB) yay sapması ve yay kuvveti ile. Tekerlek hızı yok.

| Kanal | Kaynak |
|---|---|
| `x`, `y`, `z` | konum, gönderildiği eksenlerle, sonra yeniden sıralanmış (aşağıda) |
| `longVel`, `latVel`, `vertVel` | ileri hız, yanal kayma, dikey hareket |
| `longAcc`, `latAcc` | ivme x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | gönderildiği gibi |
| `gear` | `gear - 1` (0 geri, 1 boşta, 2 birinci) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | yay sapması |
| `wheelLoad.*` | yay kuvveti |
| `speed` | konumlardan hesaplanır, ±2 örnek üzerinden, paketten alınmaz |

RBR'nin konum eksenleri, tutum birimleri ve hız birimi belgelenmemiştir; bu yüzden bir etap yazıldığında: etabın en az değiştiği eksen yukarı kabul edilir ve `y`'ye takas edilir (`orient_up`, en az 10 örnek gerekir) ve hız konumlardan yeniden hesaplanır (`speed_from_positions`). Tutum çözülür ama yazılmaz, bu yüzden RBR dosyalarında `yaw` yoktur.

Bir etap, yarış saati çalışıyorken ve bitişe olan mesafe sıfıra ulaştığında **bitmiş** sayılır. Saat `race_time`'dır.

Kaynaklar: NGP'nin `rbr.telemetry.data.TelemetryData.h` dosyası; mika-n/RBRUDPTelemetryLogger ve groybe/rbr-udp-telem üzerinden.

## Etaplar {#stages}

Beşi de oyunun etap saati üzerinde `StageSplitter` kullanır: saat başladığında bir etap açılır, oyun aracın bittiğini söylediğinde tamamlanmış olarak kapanır ve geriye giden bir saat (bir yeniden başlatma ya da bir sonraki etap) açık etabı terk eder - 10'dan fazla örneği ve en az 300 m'si varsa `_partial` dosyası olarak tutulur. 300 m'den kısa bitmiş etaplar yazılmaz. Ayrıntılar: [Tur ve etap bölme](lap-splitting.md).

## Tur dosyası {#the-lap-file}

`game`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ya da `richard-burns-rally`'dir. `meta`, `{"discipline": "rally", "slip": null}`'dur; `--surface` verildiğinde `"surface": "<değer>"` eklenir. `slip` null'dur çünkü bu oyunların hiçbiri lastik kaymasını göndermez. Her tekerleğin temas yüzeyi hızı (EA WRC, DiRT) bunun yerine dosyadadır; kayma ve savrulma açısı görüntüleyici tarafından bunlardan ve arabanın eksenlerinden türetilir; bkz. [Kayma, savrulma ve türetilen kanallar](slip-and-drift.md). `suspension.*` kanalları (kullanılan hareketin 0..1'i), `suspensionM.*`'den eklenir.

`--surface` verilmediğinde dosyada hiç yüzey yoktur, kasıtlı olarak: buraya yazılmış bir varsayılan, görüntüleyicinin kendi çıkarımını geçersiz kılardı. Görüntüleyici yüzeyi, etabın ya da etkinliğin adından (asfalt ralliler, kış ralliler, Monte karışık), yoksa arabanın üstündeki sürüş biçiminden alır (sert virajlar ve küçük savrulma açıları asfalttır) ve hiçbir şey söylemezse gevşek (loose) - bir ralli etabının en sık olduğu şey. Bildiğiniz bir şey varsa `--surface` verin.
