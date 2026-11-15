---
title: ".glb çıktısı"
nav_order: 6
lang: "tr"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# .glb çıktısı {#the-glb-output}

Bir yeniden oluşturma, ikili glTF 2.0 dosyası (`.glb`) olarak yazılır. 3DHeat görüntüleyicisi bu
dosyayı Arka plan / bölüm paneli üzerinden özel bir işlem olmadan yükler - Unreal dışa aktarıcısının
yazdığı sözleşmenin aynısı. Kod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Bir glTF kitaplığıyla değil, elle yazılmıştır: çıktı dar bir alt kümedir (tek tampon, sıkıca
paketlenmiş, animasyon yok, skinning yok) ve glTF'in tamamını yazabilen bir bağımlılık, birkaç yüz
satır için sürüm kaymasını da beraberinde getirirdi.

## Bir taramanın dosyasında ne var {#what-is-in-a-scans-file}

| Parça (düğüm ve ağ adı) | İçerik |
|---|---|
| `ground:<name>` | yukarı bakmaya 35 dereceden daha yakın açıdaki üçgenler |
| `structure:<name>` | geri kalan her şey |

`<name>`, pencereden kaydederken dosya adının uzantısız hâlidir; `reconstruct` için videonun adıdır.
Üçgeni olmayan bir parça dışarıda bırakılır. Bir tarama hiçbir zaman `water:` parçası yazmaz.
`asset.generator` değeri `heat3d-capture-scan`'dir.

## Sözleşme {#the-contract}

- **Parça başına bir düğüm**, parçanın etiketiyle adlandırılır; ağ aynı adı tekrarlar. Görüntüleyici
  önce **düğüm** adına bakar; yalnızca ağları adlandırmak sınıflandırmayı kaybettirirdi.
- Etiket `<class>:<name>` biçimindedir; sınıf `ground`, `structure` ya da `water` olur. Görüntüleyici
  bu öneki (`^(ground|structure|water)\s*[:|]`) eşleştirir ve sınıfı geometriden tahmin etmek yerine
  olduğu gibi kabul eder. Zemin katı çizilir, yapılar neredeyse saydam.
- **Koordinatlar görüntüleyici uzayındadır**: Y yukarı, sağ elli ve **santimetreye ölçeklenmiştir**
  (metre x 100). Bu, Unreal dışa aktarıcısıyla aynıdır; böylece aynı yerin bir yakalaması ve bir motor
  dışa aktarımı aynı boyutta ve aynı kamera varsayılanlarıyla yüklenir. Dosyanın üst düzey
  `extras.unit_metres` değeri `0.01`'dir (bir birim bir santimetredir); metre ile çalışan bir okuyucu,
  örneğin [`locate`](locate.md), bunu gerçek boyutuyla alır. Forza telemetrisiyle yerleştirilen bir
  tarama bir istisnadır: el yapısı konusunda, oyunun kendi dünyasında kalır (Y yukarı, sol elli),
  tıpkı tur dosyaları gibi; böylece üzerine kaydedilen turlar ona oturur. Bir taramanın ölçeği sonraki
  bir anahtar karede bulunduysa ([Ölçek](reconstruction-pose.md#scale)), bu çarpan yazılan ölçeğe
  eklenir.
- `COLOR_0` görüntüleyici tarafından okunur; görüntüleyici zemini bunla boyar; bunun için Arka plan /
  bölüm panelindeki *Yakalanan renk* anahtarının açık olması gerekir (varsayılan kapalıdır).
- Elle işaretlenmiş noktaları olan bir tarama, yanında `<name>.marks.json` dosyası alır; bkz.
  [Kaydetme](reconstruction-scan-ui.md#saving).
- Her ilkel için: `POSITION` (float VEC3, `min` ve `max` ile - görüntüleyici kamerasını bunlara göre
  çerçeveler), `NORMAL` (float VEC3), isteğe bağlı `COLOR_0` (float VEC3, 0..1), isteğe bağlı
  `TEXCOORD_0`; indeksler, her indeks 65.536'nın altındaysa 16 bit, değilse 32 bit; mod triangles.
- Her buffer view 4 bayt hizalı başlar; JSON parçası boşluklarla, BIN parçası sıfırlarla 4 bayta
  doldurulur.

## Yazmadan önce denetimler {#checks-before-writing}

Her parça doğrulanır. Tepe noktası yoksa, indeks sayısı tam üçgenler oluşturmuyorsa, bir indeks aralık
dışındaysa ya da negatifse, konumlar sonlu değilse, ya da normaller veya renkler tepe noktası sayısıyla
eşleşmiyorsa, parça adı belirtilerek reddedilir. Eksik normaller hesaplanır; bu normaller **alana göre
ağırlıklıdır** (marching cubes büyük yüzlerin yanına ince parçalar bırakır ve ağırlıksız bir ortalama
bu küçük üçgenlerin üzerinde durdukları yüzü geçersiz kılardı). Dejenere bir tepe noktası "yukarı"
alır. Hiç parça yazılmaması bir hatadır.

Hacim hiç yüzey üretmediğinde dışa aktarma hiçbir şey döndürmez ve pencere "Kaydedilecek bir şey yok"
der; böylece başarılı bir tarama gibi görünecek boş bir dosya yazılmaz.

## Dokular {#textures}

Yazıcı, parça başına bir PNG temel renk dokusunu destekler (UV'ler, çift taraflı, metalik olmayan,
tamamen pürüzlü bir malzemeyle). Taramalar bunu kullanmaz; tepe noktası başına renk taşırlar. Bkz.
[renk](reconstruction-fusion-and-texture.md#colour).

## Referans seviyesi {#the-reference-level}

`geometry/reference.py`, tam olarak bilinen boyutta sentetik bir seviye kurar; aynı yazıcıdan geçer:
400 m alt bölünmüş bir zemin, üç adet 20 x 20 x 12 m bina ve zemin altında 1,5 m derinlikte 50 m
bir gölet; her sınıf ayrı bir düz renkte. Görüntüleyicinin kendi testleri bunu üretir ve görüntüleyicinin
gerçek ayrıştırıcısıyla çözer; böylece dosya biçimi oyun ve yakalama donanımı olmadan iki tarafta da
test edilmiş kalır.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
