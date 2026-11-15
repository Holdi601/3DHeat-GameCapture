---
title: Bu belgelerin bakımı
nav_order: 96
lang: "tr"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Bu belgelerin bakımı {#maintaining-these-docs}

Her sürüm için kontrol listesi; böylece kod, İngilizce sayfalar ve çevirileri birlikte kalır. Adımları
sırayla yapın.

1. **Üretilen sayfaları yeniden üretin.**
   - `python tools/gen_docs_reference.py`, [Komut başvurusu](../cli-reference.md) sayfasını `--help` ve
     koddaki sütun listelerinden yeniden yazar. `--check` sayfa eskiyse 1 ile çıkar: her sürümden önce
     çalıştırın.
   - `python tools/docs_diagrams.py`, `docs/assets/img/` içindeki şemaları yeniden çizer;
     `--strings`, çevrilecek etiketler olan `docs/assets/i18n/en.json` dosyasını da yeniler.
   - `python tools/sync_wiki.py`, GitHub wiki'sinin `docs/wiki/` içindeki kopyasını yeniden üretir.
2. **Son sürümden beri neyin değiştiğini listeleyin.** `git log --oneline v$(cat VERSION)..` (son etiket,
   `VERSION` içindeki sürümün başına `v` eklenmiş hâlidir). Her yeni ya da değişen komut, seçenek, çıktı
   sütunu veya davranış için: sayfasını güncelleyin ve `CHANGELOG.md` içindeki *Docs* tablosuna bir satır
   ekleyin.
3. **Bağımsız inceleme.** Değişikliği yazmamış biri, değişen sayfaları ve şemaları üç okur olarak okur:
   bir **yeni başlayan** (hiç komut satırı kullanmamış: kurup çalıştırabiliyor mu?), bir **8 yaşındaki
   çocuk** (sayfa ne olduğunu ve neden var olduğunu sade sözlerle söylüyor mu?) ve bir **uzman** (seçenekler,
   varsayılanlar ve sütunlar koda uyuyor mu?). Hiçbir sayfanın gerçek seviyeleri, haritaları, oyuncuları ya
   da kayıtları adlandırmadığını denetleyin: örnekler sentetiktir, doğrulama iddiaları yalnızca yöntemi ve
   toleransı verir.
4. **Bulguları düzeltin.**
5. **Çevirin.** Her çevrilmiş sayfa, üretildiği İngilizce sayfanın karmasını kaydeder. Kaynak karması
   değişen sayfaları ve değişen şema etiketlerini yeniden çevirin; sonra her dili inceleyin: üç okur için
   açık mı, şema etiketleri doğru mu, sözcükler görüntüleyicinin yerelleştirilmiş arayüzüyle eşleşiyor mu.
6. **Yalnızca sahibinin onayıyla gönderin.** Sonra sürümü `v<VERSION>` olarak etiketleyin.

Bu komutları ilk kez mi çalıştırıyorsunuz? [Başlamadan önce](before-you-start.md), Python ve terminali
anlatır.

## Çeviriler: komutlar {#translations-the-commands}

Site, 3DHeat görüntüleyicisinin 40 diline çevrilmiştir: İngilizce `docs/` içinde, her diğer dil
`docs/<lang>/` içinde aynı dosya adlarıyla. `tools/docs_i18n.py` kayıt işlerini yapar:

```bash
python tools/docs_i18n.py hashes             # İngilizce bir değişiklikten sonra: her sayfanın karmasını kaydeder
python tools/docs_i18n.py svg-strings        # bir şema değişikliğinden sonra: çevrilecek etiketler
python tools/docs_i18n.py status             # dil başına: güncel, eski ve eksik sayfalar
python tools/docs_i18n.py todo --lang de     # (yeniden) çevrilecek Almanca sayfalar
python tools/docs_i18n.py svg-build --lang de    # docs/assets/i18n/svg/de.json dosyasından Almanca şemalar
python tools/docs_i18n.py finish --lang de   # Almanca sayfaları İngilizce karmalarıyla damgalar
python tools/docs_i18n.py check              # karmalar ya da etiketler eskiyse 1 ile çıkar
```

Yalnızca `todo`'nun listelediğini çevirin: Markdown'ı, bağlantıları, kodu, dosya ve sütun adlarını olduğu
gibi bırakın; başlıkları ve şema açıklamalarını çevirin; düğmeler ve paneller için görüntüleyicinin kendi
sözcüklerini kullanın (`src/i18n/locales/<lang>/` klasörü). Üretilmiş başvuru sayfaları ve terminal
resimleri İngilizce kalır. Sitede, eski bir çeviri bunu söyler ve İngilizce sayfaya bağlanır; eksik bir
çeviri İngilizceye döner. Üstbilgideki dil menüsü ve ana sayfadaki tarayıcı diline göre yönlendirme
`docs/_includes/` klasöründen gelir.
