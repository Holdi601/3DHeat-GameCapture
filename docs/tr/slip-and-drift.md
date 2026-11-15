---
title: Kayma, savrulma ve türetilen kanallar
nav_order: 8
lang: "tr"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Kayma, savrulma ve türetilen kanallar {#slip-drift-and-derived-channels}

Görüntüleyicinin Yarış analizi (Race analysis) sekmesindeki araç kontrolü analizi, her oyundan aynı birkaç büyüklüğü ister: her lastiğin ne kadar kaydığı, aracın gittiği yerden ne kadar uzağa baktığı (savrulma açısı), havada olup olmadığı, gevşek zeminde olup olmadığı. Oyunlar bunları çok farklı biçimlerde gönderir ya da hiç göndermez. Buradaki kaydediciler, her oyunun gönderdiğini standart adlarla yazar, artı kayma sayılarının neyi ifade ettiğini söyleyen bir `meta.slip` notu; görüntüleyici eksik olanı, bir tur yüklendiğinde bir kez türetir. **Bir oyunun kendi değeri her zaman türetilmiş olana üstündür.**

## Kaydedicilerin yazdıkları {#what-the-recorders-write}

| Oyun | Kayma kanalları | `meta.slip` | Savrulma açısı girdileri |
|---|---|---|---|
| Forza | tekerlek başına `slipRatio`, `slipAngle`, `combinedSlip`, gönderildiği gibi | `peak` (kaydedici yazar; görüntüleyicinin `.tele.gz` okuyucusu aynısını ayarlar) | araç-yerel hızdan `latVel`, `longVel` |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0.12, `slipAngle` / 0.14 rad, artı `slipRatioRaw`, `slipAngleRaw` | `scaled` | araç çerçevesi hızından `latVel`, `longVel` |
| EA SPORTS WRC, DiRT oyunları | yok; bunun yerine tekerlek başına `wheelSurfaceSpeed` | `null` | `latVel`, `longVel` = dünya hızının aracın eksenlerine izdüşümü |
| Richard Burns Rally | yok; tekerlek hızı da yok | yok | `latVel`, `longVel` = aracın kendi sallanması ve ilerlemesi |
| BeamNG.drive | yok; tekerlek başına `wheelSurfaceSpeed` ve `wheelSpeed` | yok | `latVel`, `longVel` = dünya hızının aracın eksenlerine izdüşümü |
| Trackmania | tekerlek başına `slipIndex` (0..1 arası kayan bir ölçü) | `index` | `latVel` (yan hız), `longVel` (ön hız) |
| iRacing | yok (kaydedilmiyor) | yok | `yaw` ve yol, `yawRate` |

`meta.slip` değerleri [heat3d-lap dosyası](lap-format.md) sayfasında tanımlıdır: `peak` (1'in üstü lastiğin bıraktığı anlamına gelecek şekilde normalleştirilmiş), `scaled` (fiziksel bir kayma, tipik bir asfalt tepe değerine bölünmüş), `physical` (bir kesir ve radyan), `index` (0..1 arası kayan bir ölçü).

### Kunos kaymasının neden ölçeklendiği {#why-kunos-slip-is-scaled}

Forza'nın kayması, 1'in tutuşun kenarı olacak şekilde normalleştirilmiştir; neye göre normalleştirdiği belgelenmemiştir. Kunos, fiziksel kayma oranını (bir kesir) ve kayma açısını (radyan) gönderir. Tipik bir asfalt tepe değerine - oran için 0,12, açı için 0,14 rad (yaklaşık 8 derece) - bölmek, "1'in üstü kaymak demektir" yorumunu iki aile için de kabaca doğru kılar ve görüntüleyicinin göstergeleri için tek bir okuma tutar. Bu bir yaklaşımdır: gerçek tepe değerleri lastik ve yüzeye göre değişir; ham değerlerin ölçeklenmişlerin yanında tutulmasının ve görüntüleyicinin her arabanın tutuşunun gerçekte nerede azaldığını turların kendisinden ölçmesinin nedeni budur.

## Görüntüleyicinin türettikleri (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Bunlar bu depoda değil, görüntüleyicide çalışır (3DHeat görüntüleyicisindeki `src/race/derive.ts`).

### Savrulma açısı, `bodySlip` {#drift-angle-bodyslip}

- **Araç çerçevesi hızından**, `latVel` ve `longVel` mevcutsa: `atan2(latVel, |longVel|)`, ve 3 m/s'nin altında 0 (yana doğru duran bir araba savrulmuyor değildir).
  İşareti oyunun yanal hızını izler; bu, bazı oyunlarda iki yönde de belgelenmiştir - büyüklüğe bakın.
- **Aksi halde yönelimden yola karşı**: seyir yönü, her örneğin iki yanındaki yaklaşık 2 m'deki konumlardan alınır (`atan2(dx, dz)`); oyunun `yaw` değeri, bununla bir işaret ve bir ofsetle uydurulur (her oyunun kendi sıfırı ve dönüş yönü vardır), 10 m/s'nin üstündeki örnekler kullanılarak, ve yalnızca sonra yakından uyuşursa güvenilir (dairesel yayılım en fazla 0,05, en az 20 örnek). Savrulma açısı farktır, 3 m/s'nin altında 0.

### Tekerleklerden kayma oranı {#slip-ratio-from-the-wheels}

Bir turda `slipRatio.*` yoksa ama tekerlek hızları varsa, kayma oranı her tekerlek için `(wheel - car) / car`dır, şuradan:

- `wheelSurfaceSpeed.*` (temas yüzeyinin hızı, m/s) gönderildiğinde doğrudan (EA WRC, DiRT, BeamNG);
- aksi halde `wheelSpeed.*` (dönüş, rad/s) çarpı **turda ölçülen bir yuvarlanma yarıçapı**: aracın düz bir çizgide boşta gittiği örneklerde (10 m/s'nin üstünde, havada değil, gaz 0,3'ün altında, fren 0,05'in altında, boyuna ivme 3 m/s²'nin altında) `speed / |omega|`'nın medyanı; bu tür 20'den az örnek varsa, 10 m/s'nin üstündeki her örnek. 0,1-1 m dışındaki bir yarıçap reddedilir.

Yalnızca dört tekerleğin hepsi türetilebildiğinde; turun `meta.slip` değeri o zaman `physical` olur. 3 m/s'nin altında kayma 0'dır.

### Havada {#airborne}

`airborne`, her tekerleğin yerde olmadığı yerde 1'dir; bunu, turun dört tekerlek için sahip olduğu ilk şu kaynak yargılar:

1. `groundContact.*` (BeamNG): hiçbir tekerlek 0,5'in üstünde değil;
2. `wheelLoad.*` (AC oyunları, RBR, BeamNG): hiçbir tekerlek kendi medyan yükünün %5'inin üstünde değil;
3. `suspension.*` (0..1 hareket): hiçbir tekerlek 0,02'nin üstünde değil, yani hepsi tamamen uzamış.

Tek başına izole bir havada örneği silinir. Trackmania `airborne`'ı kendisi yazar.

### Gevşek zemin {#loose-ground}

Bir turda `surfaceRumble.*` (Forza) varsa, `loose`, en az iki tekerleğin üçte bir saniye boyunca titreşim bildirdiği yerde 1'dir; bir saniyeden kısa boşluklar köprülenir (gravel bir yoldaki pürüzsüz bir yama hâlâ gravel yoldur). Trackmania `loose`'u tekerleklerin zemin malzemelerinden kendisi yazar.

### Yaw oranı {#yaw-rate}

Bir turda `yaw` var ama `yawRate` yoksa, o komşu örnekler arasındaki yaw değişimidir.

## Kaydedicilerin kendileri türettikleri {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): Forza dışındaki her kaydedici (Forza onu gönderir) bunu `suspensionM.*`'den yazar; bu, bu turun kullandığı aralık içindeki konumdur (en küçük ile en büyük). Aracın süspansiyon çubukları içindir ve havada asılı bir tekerleği fark etmek için; mutlak bir hareket kesri değildir.
- Kunos oyunları için **`steer`**, tur başına ölçeklenmiş (bkz. [Assetto Corsa oyunları](telemetry-assetto-corsa.md)).
- BeamNG için **ivmeler**, dünya hızındaki değişimden ([BeamNG.drive](telemetry-beamng.md)).
- Richard Burns Rally için **`speed`** ve yukarı ekseni, konumlardan ([Ralli oyunları](telemetry-rally.md)).

## Sağ-sol elli yapı {#handedness}

Bir oyunun dünyası sol elli ise - Forza'nınki öyledir - parkur sağ elli bir görüntüleyicide aynalanmış çıkar; turların kendi direksiyon ve süspansiyonu bunu ortaya çıkarır. Kaydediciler elliliği değiştirmez: Z-yukarı bir dünya (BeamNG) bir dönüşle Y-yukarıya çevrilir, bu da elliliği korur, ve diğer her şey gönderildiği gibi yazılır.
