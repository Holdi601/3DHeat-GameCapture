---
title: Telemetri kaydediciler
nav_order: 3
lang: "tr"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetri kaydediciler {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry`, bir oyunun gönderdiği her kanalı kaydeder, akışı turlara ya da etaplara böler ve bir klasöre tur başına bir [`heat3d-lap`](lap-format.md) JSON dosyası yazar. Görüntüleyicinin Yarış analizi (Race analysis) sekmesi bu dosyaları okur. Kayıt **Ctrl+C** tuşuna basana kadar sürer; o an açık olan tur ya da etap, saklanacak kadar uzunsa yazılır (bkz. [Tur ve etap bölme](lap-splitting.md)).

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
ve [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry) içindeki modüller.

## Seçenekler {#options}

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `--game` | `forza` | `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania` değerlerinden biri. |
| `-o`, `--out` | `laps` | Tur dosyalarının yazıldığı klasör. Yoksa oluşturulur. `trackmania` için yok sayılır, çünkü eklentisi dosyaları kendisi yazar. |
| `--port` | `5300` | Dinlenecek UDP portu. **Forza dışındaki her oyun için 5300 değeri "oyunun kendi varsayılanı" anlamına gelir**: `wrc` ve DiRT oyunları için 20777, `rbr` için 6776, `beamng` için 4460. Farklı bir sayı vererek geçersiz kılın. Assetto Corsa oyunları (paylaşılan bellek) ya da Trackmania (dosyalar) için kullanılmaz. |
| `--forward` | yok | Yalnızca Forza: alınan her paketi değiştirmeden iletmek için `host:port`. FH Companion için `127.0.0.1:5301`. Yalnız `:5301` yazmak `127.0.0.1:5301` demektir. |
| `--install` | kapalı | `beamng`: önce koruma modunu BeamNG'nin açılmış modlarına kopyalar. `trackmania`: Openplanet eklentisini Openplanet'in eklenti klasörüne kopyalar. Diğer oyunlar için yok sayılır. |
| `--configure` | yok | Yalnızca `wrc`: EA SPORTS WRC'nin telemetri `config.json` dosyasının yolu; kaydetmeden önce varsayılan `wrc` paketini açar (önce yedeklenir). |
| `--surface` | yok | Ralli oyunları (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ya da `mixed`, tur dosyasının `meta.surface` alanına yazılır. Verilmezse hiçbir yüzey yazılmaz. |

## Oyunlara bakış {#the-games-at-a-glance}

| `--game` | Oyun | Kaynak | Varsayılan port | Bölme | Dosyada `game` | Sayfa |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (2023 dahil) | Data Out UDP | 5300 | oyunun tur sayacı (`LapSplitter`) | `forza-horizon`, `forza-motorsport` ya da `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | paylaşılan bellek `acpmf_*` | - | tur sayacı (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa oyunları](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | paylaşılan bellek `acpmf_*` | - | tur sayacı (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa oyunları](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | paylaşılan bellek `acevo_pmf_*` | - | başlangıç çizgisi (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa oyunları](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | paylaşılan bellek `acpmf_*` | - | başlangıç çizgisi / durma (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa oyunları](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc` yapısı | 20777 | etap saati (`StageSplitter`) | `ea-sports-wrc` | [Ralli oyunları](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | etap saati (`StageSplitter`) | `dirt-rally-2` | [Ralli oyunları](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | etap saati (`StageSplitter`) | `dirt-rally` | [Ralli oyunları](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | etap saati (`StageSplitter`) | `dirt-4` | [Ralli oyunları](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | etap saati (`StageSplitter`) | `richard-burns-rally` | [Ralli oyunları](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d` protokol modu, UDP | 4460 | başlangıç çizgisi (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet eklentisi, CSV dosyaları | - | koşu başına, eklentide | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | kendi `.ibt` dosyaları, görüntüleyici okur | - | simülasyonun tur sayacı | `iracing` | [iRacing](telemetry-iracing.md) |

## Durum {#status}

Forza kaydedicisi en çok denenen olanıdır. Kunos, ralli, BeamNG ve Trackmania kaydedicileri yayımlanmış düzenlere göre yazılmıştır ve bu düzenlerden oluşturulmuş sahte paketler ve sayfalar üzerinde test edilmiştir (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **hiçbiri henüz canlı oyuna karşı çalıştırılmadı**. Girdisini denetleyebilen kaydediciler, paketler geldikçe bunu yapar ve bir şey uymadığında bir kez `note:` yazdırır (EA WRC ve DiRT dünya hızını hızla karşılaştırır; EA WRC ayrıca 237 baytlık varsayılan yapıdan kısa bir paketi bildirir). [Oyunlar](games.md) sayfası kaynakları ve oyun başına henüz doğrulanmamış olanları listeler.

## Çalışırken {#while-it-runs}

- **Forza** saniyede bir durum satırı yazdırır: alınan paketler ve açık turun numarası, örnek sayısı ve metresi ya da `waiting for a race`. Biten her tur `wrote <file>` yazdırır.
- **Assetto Corsa oyunları** yazılırken her tur dosyasının adını yazdırır.
- **Ralli oyunları** `listening for <game> on port <port>` yazdırır, sonra `stage written: <file>`; Ctrl+C'de saklanacak kadar uzun açık bir etap `partial stage written: <file>` olarak yazılır.
- **BeamNG** `lap written: <file>` yazdırır, Ctrl+C'de `run written: <file>`.
- **Trackmania** koşu başına hiçbir şey yazdırmaz: eklenti CSV dosyalarını kendisi yazar.
- Sonunda her kaydedici kaç dosya yazdığını yazdırır.

Synthetic Forza verisiyle, 150 m'lik bir çemberde iki tur süren bir Forza kaydı (tur dosyaları, ham yan dosya ve bıraktığı kendini denetleme özeti):

![Sentetik bir Forza akışından iki turu kaydeden telemetri](../assets/img/telemetry-run.svg)

## Dosya adları {#file-names}

| Kaydedici | Desen |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa oyunları | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Ralli oyunları, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`; burada `<game>` uzun addır (`ea-sports-wrc`, `beamng`, ...), ralli için `stage`, BeamNG için `lap` |
| Trackmania eklentisi | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

Forza ve Assetto Corsa'da `lap` ile `run` ve ralli ile BeamNG'de `_partial` eki, turun ya da etabın bitirilip bitirilmediğini işaretler. Zaman damgası, dosyanın yazıldığı andır, turun başladığı an değil.

Tur dosyalarının yanında her kaydedici `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` yazar - gelen her paket ya da sayfa, bütün olarak, menülerde ve turlar arasında bile - ve `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, kendini denetleme: paket türü başına kaç tane geldiği, kaçının tur dosyalarına girdiği ve `lost`, ki bu 0'dır. Görüntüleyici bir klasör yüklendiğinde ikisini de atlar. Bkz. README'deki [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) bölümü.

## Bu sayfanın alt sayfaları {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa oyunları](telemetry-assetto-corsa.md)
- [Ralli oyunları](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Tur ve etap bölme](lap-splitting.md)
- [Kayma, savrulma ve türetilen kanallar](slip-and-drift.md)
- [heat3d-lap dosyası](lap-format.md)
