---
title: Güncellemeler
nav_order: 10
lang: "tr"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Güncellemeler {#updates}

3DHeat GameCapture, başladığında bu deponun GitHub sürümlerini denetler, daha yeni bir sürüm çıktığını
söyler ve güncellemeyi önerir. Kod:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Denetim ne zaman çalışır {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - komut çalışmadan önce.
- `python -m heat3d_capture.ui` (ve `scan.bat`) - pencere açılmadan önce.
- `python -m heat3d_update` - istek üzerine; her seferinde GitHub'a yeniden sorar.

## Denetim nasıl çalışır {#how-the-check-works}

- Kurulu sürüm, depo kökündeki `VERSION` dosyasıdır (örneğin `1.0.1`).
- En yeni sürüm `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest` adresinden sorulur;
  zaman aşımı **5 saniyedir**. Yavaş bir ağ aracı bundan uzun süre durdurmaz.
- Yanıt, `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` dosyasında **6 saat** önbelleğe alınır
  (`LOCALAPPDATA` yoksa `~/.cache/3DHeat/...`). Her 3DHeat aracının kendi önbellek dosyası vardır. "Henüz sürüm
  yok" (HTTP 404) bir yanıt gibi önbelleğe alınır; diğer hatalar önbelleğe alınmaz ve yalnızca bildirim
  olmadığı anlamına gelir.
- Sürümler sayısal olarak karşılaştırılır (`v1.2.3` ya da `1.2.3`; `-` ya da `+` sonrasındaki her şey yok sayılır).
- Çevrimdışıysanız, hız sınırına takıldıysanız ya da bir proxy arkasındaysanız, araç sahip olduğu sürümle
  çalışmaya devam eder.

## Daha yeni bir sürüm çıktığında ne olur {#what-happens-when-a-newer-release-is-out}

Başlangıçta, hata akışına şunu yazdırır:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Yanıtlayabileceğiniz bir terminal varsa `Update now? [Y/n]` sorusunu sorar (Enter, `y`, `yes`, `j`, `ja`
  evet anlamına gelir). Başarılı bir güncellemeden sonra **aynı komut yeniden başlatılır**, yeni kodla.
- Terminal yoksa (bir boru hattı, zamanlanmış bir çalıştırma), `Run python -m heat3d_update in <folder> to update.`
  yazdırır ve değişmeden devam eder.

## Güncelleme nasıl uygulanır {#how-an-update-is-applied}

Araçların nasıl kurulduğuna bağlıdır:

- **Bir git kopyası** (bir `.git` klasörü ve PATH üzerinde `git`): `git pull --ff-only`. Kopyada izli dosyalarda
  yerel değişiklikler varken reddedilir - bunlar birinin çalışmasıdır; önce commit edin ya da saklayın.
- **İndirilmiş bir kopya**: sürümün kaynak arşivi indirilir, geçici bir klasöre açılır (arşivin kendi klasörünün
  dışındaki girdiler atlanır) ve `VERSION` dosyasından iddia ettiği sürümde olduğu **denetlenir**. Sonra dosyaları
  bu klasörün üzerine kopyalanır. Sürümün kendi Python paketlerinin içinde (depo kökündeki `heat3d_*` klasörleri ve
  eski tek depo düzeni için bir seviye aşağıda), sürümde artık olmayan `.py` modülleri silinir; böylece eski bir
  modül yerine geçen modülü gölgeleyemez.

Kendi dosyalarınıza - kayıtlar, tur dosyaları, ayarlar, dışa aktarımlar, `.venv` - hiçbir zaman dokunulmaz: yalnızca
sürümün parçası olan dosyalar yazılır.

## Elle {#by-hand}

```bash
python -m heat3d_update            # denetle ve güncelle
python -m heat3d_update --check    # yalnızca daha yeni bir sürüm olup olmadığını söyle
```

`Up to date: <version>.`, `No release found ... offline, or nothing published yet.` ya da yeni sürümü ve ne yaptığını
yazdırır. Güncelleme uygulanamazsa çıkış kodu 1'dir.

## Kapatma {#switching-it-off}

**`HEAT3D_NO_UPDATE=1`** ayarlayın (boş, `0`, `false`, `no` dışındaki herhangi bir değer). Bu, başlangıç denetimini ve
bildirimini kapatır. `python -m heat3d_update` elle çalıştırıldığında yine denetler.
