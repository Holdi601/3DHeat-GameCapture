---
title: Assetto Corsa oyunları
nav_order: 2
lang: "tr"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO ve AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kod: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testler: `tests/test_kunos.py` (sahte sayfalar). Henüz canlı oyunlara karşı çalıştırılmadı.

## Veri nereden gelir {#where-the-data-comes-from}

Kunos'un oyunları, uygulamalar için **adlandırılmış Windows paylaşılan bellek sayfaları** yayımlar; oyun bunlara yazar ve herkes okuyabilir. Kaydedici bunları salt okunur açar (bir etiket adıyla `mmap`), bu yüzden oyunun çalıştığı PC'de, Windows'ta çalışmalıdır; başka yerde bir mesajla çıkar. Sayfalar, kaydedici başladığında bir kez açılır. Önce oyunu başlatıp arabaya binmek güvenli sıradır; kaydediciyi oyundan önce başlatmanın işe yarayıp yaramadığı kontrol edilmedi.

| `--game` | Fizik sayfası | Grafik sayfası (tur sayacı) | Statik sayfa (adlar) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | kullanılmıyor | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | kullanılmıyor | `Local\acevo_pmf_static` |

Fizik sayfası saniyede 200 kez okunur (`hz=200`); yeni bir örnek yalnızca `packetId` değiştiğinde ve sıfır değilse alınır. Fizik sayfasının ilk 800 baytı dört oyunda tek bir düzeni paylaşır; ilk oyunun sayfası yalnızca 580 bayt garanti eder, bu yüzden 800 baytlık bir eşleme açılamazsa kaydedici 580'e düşer ve bunun ötesindeki alanlar yoktur.

## Konum {#position}

Sayfaların hiçbiri bir araba konumunu doğrudan taşımaz, ama fizik sayfası **her lastiğin dünya koordinatlarındaki temas noktasını** taşır (ofset 420, dört XYZ üçlüsü). Arabanın konumu, dördünün ortalamasıdır. Dört temas noktasının hepsi sıfır olan bir sayfa (menü, garaj) örnek üretmez.

## Kanallar {#channels}

| Kanal | Kaynak | Notlar |
|---|---|---|
| `time` | kaydedicinin kendi saati | kaydın başlangıcından beri saniye, turun ilk örneğine göre kaydırılmış |
| `x`, `y`, `z` | ortalama lastik temas noktası | dünya metresi |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | oyunun birimleri; tur, kullandığı en büyük mutlak değere göre -1..1 aralığına ölçeklenir, **yalnızca** bu değer 1,05'i aşarsa (zaten -1..1 olan bir girdi olduğu gibi bırakılır) |
| `gear` | `gear - 1` | oyun 0 geri, 1 boşta, 2 birinci sayar; -1, 0, 1 ... olarak yazılır |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, çarpı 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | ofset 568'deki yerel hız | araç çerçevesi; yalnızca sıfır değilse. x'in hangi yana baktığı iki yönde de belgelenmiştir, bu yüzden işarete değil, savrulma açısının büyüklüğüne bakın |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | ofset 564 | yalnızca 800 baytlık sayfa |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: ofsetler 204 ve 252, 0'ın üstündeyse 1 olarak yazılır; AC: `tcInAction`/`absInAction`, varsa 800 baytlık sayfadan | yardımcı sistemler devrede |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | türetilmiş | bu turun kullandığı hareketin 0..1'i (`suspensionM`'nin en küçüğü ile en büyüğü) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | ofsetler 640, 656 (800 baytlık sayfa) | tipik bir tepe değerine bölünmüş - aşağıya bakın |
| `slipRatioRaw.*`, `slipAngleRaw.*` | aynısı | fiziksel değerler, ölçeklenmemiş |
| `padLife.*`, `discLife.*` | ofsetler 740, 756 | yalnızca 800 baytlık sayfa |

AC Rally, lastik ve fren sıcaklıklarını kelvin olarak gönderir: `--game acrally` için bu değerlerden 200'ün üstündekilerden 273,15 çıkarılır.

`wheelSlip` (ofset 56) çözülür ama yazılmaz.

## Kayma ölçeklendirmesi {#slip-scaling}

Forza kaymayı, 1'in tutuşun kenarı olacak şekilde normalleştirilmiş gönderir. Kunos fiziksel kayma oranını ve kayma açısını gönderir. Bu yüzden kaydedici, bunları tipik bir asfalt tepe değerine böler - kayma oranı için **0,12** ve kayma açısı için **0,14 rad (yaklaşık 8 derece)** - böylece görüntüleyicinin "1'in üstü kaymak demektir" okuması yaklaşık olarak geçerli kalır, ham değerler yanlarında tutulur ve `"meta": {"slip": "scaled"}` yazılır. Tutuşun gerçekte nerede bittiği, görüntüleyici tarafından arabaya göre turlardan ölçülür. Bkz. [Kayma, savrulma ve türetilen kanallar](slip-and-drift.md).

## Turlar {#laps}

- **AC ve ACC** turları grafik sayfasında sayar (`completedLaps`, ofset 132; son turun süresi milisaniye olarak 144'te). `CounterSplitter`, sayaç değiştiğinde bir turu kapatır; yalnızca sayaç tam olarak bir arttıysa, oyunun tur süresiyle tamamlanmış olarak işaretlenir.
- **AC EVO ve AC Rally** tur için okunmaz (EVO'nun grafik sayfası farklı ve daha büyük bir düzendir; AC Rally etap sürer). `LineSplitter`, kaydın başladığı noktayı çizgi olarak kullanır: araç, aynı yöne giderek ona en yakın yeniden geçtiğinde bir tur kapanır ve bir etap ya da herhangi bir koşu, araç 8 saniye durduğunda kapanır.

Eşikler ve ayrıntılar: [Tur ve etap bölme](lap-splitting.md).

## Pist ve araç adları {#track-and-car-names}

Statik sayfadan, ilk örnek geldiğinde bir kez okunur: AC, ACC ve AC Rally için araç (UTF-16, ofset 68) ve pist (ofset 134); AC EVO için pist ve konfigürasyonu (ofset 136 ve 169'da tek baytlık metin, bir boşlukla birleştirilmiş) ve araç yok. Dosyaya `track` ve `car: {"name": ...}` olarak yazılırlar.

## Tur dosyası {#the-lap-file}

`game`, `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ya da `assetto-corsa-rally`'dir; `meta`, AC Rally için `{"slip": "scaled", "discipline": "rally"}` ve diğer üçü için `{"slip": "scaled", "discipline": "circuit"}`dir. `surface` yazılmaz.

## Kaynaklar {#sources}

AC1 paylaşılan bellek SDK'sı; ACC paylaşılan bellek belgesi (v1.8); AC EVO'nun düzeni `albertowd/live-telemetry-evo` içinde ölçüldüğü gibi; AC Rally'nin düzeni `LuizZak/AssettoCorsaRallyTelemetryReader` tarafından okunduğu gibi. Bkz. [Oyunlar](games.md).
