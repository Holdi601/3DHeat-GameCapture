---
title: heat3d-lap dosyası
nav_order: 9
lang: "tr"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# `heat3d-lap` dosyası {#the-heat3d-lap-file}

Bu depodaki her telemetri kaydedicisi, oyun ne olursa olsun, her tur ya da ralli etabı için aynı biçimde bir dosya yazar. [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) içindeki parkur dışa aktarımı bu dosyayı okuyarak oyunu, seviyeyi ve sürülen çizgiyi bulur. JSON okuyabilen her şey bu dosyayı okuyabilir.

![Sentetik bir Forza akışından yazılmış bir tur dosyasının alanları ve kanalları](../assets/img/lap-file.svg)

## Belge {#the-document}

Tek bir JSON nesnesi. Kanallar sütun olarak saklanır: kanal başına bir dizi, hepsi aynı uzunlukta, örnek başına bir giriş.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Alan | Anlamı |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | turun hangi oyundan olduğu; aşağıdaki listeye bakın |
| `track` | pist, etap ya da harita adı, oyun bunu gönderdiğinde |
| `layout` | yalnızca Forza: çözülen Data Out paket düzeni |
| `car` | oyunun araç hakkında söylediği her şey; serbest biçimli |
| `lap` | turun numarası, oyunun saydığı süre (ya da örneklerin açıklığı), bitirilip bitirilmediği, uzunluğu |
| `meta` | sayıların nasıl okunacağı; aşağıya bakın |
| `units` | mevcut her kanalın birimi, aşağıdaki tabloyu bilmeyen bir okuyucu için |
| `channels` | örnekler |
| `unparsed` | yalnızca Forza, paketin hiçbir alan adı olmayan baytları olduğunda: `ranges` (paketteki `[başlangıç, bitiş)` bayt ofsetleri) ve `hex` (örnek başına, bu baytların onaltılık hali); böylece dosya tek başına tüm paketi taşır |

`game` şunlardan biridir: `forza-horizon`, `forza-motorsport`, `forza` (paket düzeni ayırt edilmemiş), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta`, oyunlar farklılaştığında sayıların ne anlama geldiğini söyler:

- `slip`: kayma kanallarının neyi tuttuğu, eğer oyun herhangi bir kayma gönderiyorsa - `peak` (normalleştirilmiş; 1'in üstünde lastik bırakır: Forza), `scaled` (fiziksel bir kayma, tipik bir asfalt tepe değerine bölünmüş: Assetto Corsa oyunları), `physical` (bir kesir ve radyan), `index` (0..1 arası kayan bir ölçü: Trackmania);
- `discipline`: `circuit` (pist), `rally` (ralli) ya da `arcade`;
- `surface`: biliniyorsa `tarmac` (asfalt), `loose` (gevşek), `snow` (kar), `ice` (buz) ya da `mixed` (karışık) (ralli kaydediciler bunu `--surface` ile alır).

## Kanallar {#channels}

Bir oyunun göndermediği kanal yoktur, sıfırlarla doldurulmaz. Tekerlek başına kanallar, tekerleğin adını bir nokta sonrasında taşır: `.FL`, `.FR`, `.RL`, `.RR`.

Konumlar oyunun dünyasındadır, metre cinsinden, `y` yukarı. Dünyası Z-yukarı olan bir oyun, kaydedicisi tarafından Y-yukarı çevrilir; başka hiçbir şey değiştirilmez, böylece sol elli bir dünya (Forza'nınki) sol elli kalır.

| Kanal | Birim | Anlamı |
|---|---|---|
| `time` | s | turun ilk örneğinden beri |
| `distance` | m | ilk örnekten beri izlenen yol boyunca |
| `x`, `y`, `z` | m | konum; `y` yüksekliktir |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedallar ve kol |
| `steer` | -1..1 | pozitif sağa |
| `gear` | | oyunun saydığı gibi |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | araç çerçevesi |
| `yaw`, `pitch`, `roll` | rad | yön ve tutum |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | aracın çerçevesinde hız: sağ, ileri, yukarı |
| `bodySlip` | rad | savrulma açısı, oyunun gönderdiği yerde |
| `loose` | 0/1 | gevşek zeminde (Trackmania) |
| `airborne` | 0/1 | hiçbir tekerlek yerde değil |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | oyunun gönderdiği gibi |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | yardımcı sistemler devrede |
| `absLevel`, `tcLevel` | | yardım ayarları |
| `brakeBias` | 0..1 | ön pay |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | tekerlek başına |
| `tirePressure` | psi | tekerlek başına |
| `tireWear` | 0..1 | tekerlek başına |
| `slipRatio`, `slipAngle`, `combinedSlip` | bkz. `meta.slip` | tekerlek başına |
| `slipIndex` | 0..1 | tekerlek başına kayan ölçü (Trackmania) |
| `camber` | rad | tekerlek başına |
| `brakeTemp` | °C | tekerlek başına |
| `padLife`, `discLife` | | tekerlek başına |
| `suspensionM` | m | tekerlek başına süspansiyon hareketi |
| `suspension` | 0..1 | tekerlek başına süspansiyon hareketi, bu turun kullandığı aralıkta |
| `wheelLoad` | N | tekerlek başına |
| `wheelSpeed` | rad/s | tekerlek başına dönüş |
| `wheelSurfaceSpeed` | m/s | tekerlek başına temas yüzeyi hızı |
| `groundContact` | 0/1 | tekerlek başına |
| `rumble`, `surfaceRumble` | | tekerlek başına: titreşim şeridinde mi; yüzeyin titreşimi |
| `puddle` | | tekerlek başına durgun su derinliği |

Bir kaydedici kendi kanallarını tabloda olmayan adlarla ekleyebilir; bir okuyucu bilmediği kanalları tutar.

Hiçbir rally oyunu tekerlek kaymasını göndermez. Bir okuyucu bunu, her tekerleğin temas yüzeyi ya da yüzey hızının aracın hızına karşı farkından, `(wheel - car) / car`, ya da yalnızca dönüş gönderildiğinde, dönüşünden ve turda ölçülen bir yuvarlanma yarıçapından hesaplayabilir. Savrulma açısı, `latVel` ve `longVel` gibi aracın kendi hızından gelir; bu gönderilmediğinde dünya hızının aracın eksenlerine izdüşümünden hesaplanır.

## CSV biçimi {#the-csv-form}

Trackmania eklentisi bunun yerine `heat3d-lap-csv` yazar: `# ` ile başlayan ilk satır ve bir JSON nesnesi (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), bir kanal adları satırı, sonra örnek başına bir satır. Kanal adları yukarıdakilerle aynıdır.

## Kaydedicilerin gerçekte yazdıkları {#what-each-recorder-actually-writes}

Yukarıdaki biçim sözleşmedir; kaydediciler onu biraz farklı doldurur ve bir okuyucu bunların hepsine tolerans göstermelidir (kodla karşılaştırılarak kontrol edildi):

| Kaydedici | `track` | `layout` | `meta` | `units` | Tablonun dışındaki kanallar |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (Forza Motorsport 2023'ün pist numarası `lap.trackOrdinal` içindedir) | algılanan paket düzeni | `slip: peak`, `discipline: circuit` | yalnızca mevcut kanalların birimleri | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, oyunun saati `timestampMs`, `raceTime`, `bestLap`, `lastLap`; araç-yerel hız kanonik `latVel`, `vertVel`, `longVel` adları altındadır; `unparsed` kanalların yanında |
| Assetto Corsa oyunları (`kunos.py`) | statik sayfadan, ya da `null` | yok | `slip: scaled`, `discipline: circuit` ya da `rally` | sabit bir liste | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (gönderildiği gibi), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rally oyunları (`rally.py` via `lapfile.py`) | `null` | yok | `discipline: rally`, `slip: null`, `surface` yalnızca `--surface` verildiğinde (yoksa görüntüleyici çıkarır) | yalnızca mevcut kanalların birimleri | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, adı kesinleşmemiş kayanlar için `float<i>`; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | yok | `discipline: circuit` | yalnızca mevcut kanalların birimleri | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania eklentisi (CSV) | harita adı | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car`, Forza'nın araç bloğudur (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`); Kunos oyunları için statik sayfa bir ad verdiğinde `{"name": ...}`, aksi halde `{}`. `lap.metres`, Forza için oyunun kat ettiği mesafe farkıdır; diğerlerinde örnekler arasındaki toplam 3B mesafedir. Değerler yazılırken yuvarlanır: `time` 4 ondalığa, `distance` 3 ondalığa, diğer ondalıklı sayılar 5 ondalığa. JSON sıkıştırılmış yazılır (boşluk yok).

Kaydedicinin aldığı her paket ya da sayfa - yalnızca turlara ait olanlar değil - bütün olarak, tur dosyalarının yanında `<stamp>_<game>.raw.parquet` içinde tutulur; kendini denetleme `<stamp>_<game>.summary.json` içindedir (README'deki "Completeness" bölümü).

Bir kanalın değeri olmayan bir örnek - karede eksik, ya da oyunun gönderdiği biçimiyle sonlu bir sayı olmayan - her kaydedici tarafından `null` olarak yazılır (`lapfile.clean`); ondan türetilen süspansiyon kesri de `null`dur. `NaN` ve `Infinity` hiçbir zaman yazılmaz: JSON değildirler ve bir tarayıcının `JSON.parse` komutu, birinden dolayı tüm dosyayı reddeder. Bir okuyucu, bir kanalın dizisinde `null` görmeyi beklemelidir.

Forza dosyaları, algılanan düzene göre `"game": "forza-horizon"`, `"forza-motorsport"` ya da `"forza"` taşır. Görüntüleyicinin FH Companion `.tele.gz` dosyalarını okuyan okuyucusu `"game": "forza-horizon"` ve `meta.slip = "peak"` ile turlar üretir; o okuyucu bu depoda değil, görüntüleyicidedir. iRacing turları (görüntüleyicide `.ibt` dosyasından okunur) `"game": "iracing"` taşır; bu değer yukarıdaki kaydedici `game` listesinde yoktur, çünkü hiçbir kaydedici bunu yazmaz.

`lap.number`, `lap.seconds` ve `lap.complete` değerlerinin nasıl belirlendiği için [Tur ve etap bölme](lap-splitting.md) sayfasına, görüntüleyicinin bu kanallardan neyi türettiği için [Kayma, savrulma ve türetilen kanallar](slip-and-drift.md) sayfasına bakın.
