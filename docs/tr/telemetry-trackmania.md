---
title: Trackmania (2020)
nav_order: 5
lang: "tr"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kod: Openplanet eklentisi
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Eklenti henüz oyunda çalıştırılmadı**; görüntüleyicinin CSV okuyucusu test
edilmiştir.

## Dosya yazan bir eklenti neden {#why-a-plugin-that-writes-files}

Trackmania'nın kendi telemetri çıktısı yoktur. Oyunun eklenti platformu Openplanet, izlenen arabanın araç
durumunu eklentilere açar; ama Openplanet eklentileri UDP gönderemez. Bu yüzden eklenti, koşu başına bir CSV
dosyasını kendi depolama klasörüne yazar ve görüntüleyici bu dosyaları olduğu gibi okur. Bir kayıt cihazı
süreci yoktur: `telemetry --game trackmania` yalnızca eklentiyi kurar (`--install` ile) ve dosyaların nerede
görüneceğini yazdırır.

## Kurma ve yükleme {#installing-and-loading}

- `--install`, `mods/trackmania/Heat3dRecorder` dosyasını
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` konumuna kopyalar ve eski kopyanın yerine geçer.
  `--install` olmadan hiçbir şey kopyalanmaz.
- Oyunda: **Openplanet > Developer > Load plugin** yolunu izleyin ve `3DHeat recorder` seçin.
- Eklenti, Openplanet'in **VehicleState** eklentisine bağlıdır (`info.toml` içinde
  `dependencies = ["VehicleState"]`).
- İmzasız eklentiler yalnızca **Openplanet'in geliştirici modunda** yüklenir; bu da çevrimiçi oyunu
  sınırlar. Eklenti openplanet.dev üzerinde imzalanabilir; burada imzalı değildir.

Koşular `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder` klasörüne yazılır. Bu CSV dosyalarını
görüntüleyicinin Yarış analizi sekmesine yükleyin. Trackmania için `-o` ve `--port` yok sayılır.

## Eklentinin kaydettikleri {#what-the-plugin-records}

Eklenti yalnızca Openplanet'in açtığı şeyleri okur - izlenen arabanın araç durumunu
(`VehicleState::ViewingPlayerState()`) ve oyuncunun yarış süresini ile yeniden doğma sayısını
(`CSmScriptPlayer`) - hiçbir yere bir şey göndermez ve oyunda hiçbir şeyi değiştirmez. Her karede
(`Update`) bir satır yazılır; yani örnekleme hızı oyunun kare hızıdır.

| Sütun | Kaynak |
|---|---|
| `time` | `CurrentRaceTime` / 1000, saniye |
| `x`, `y`, `z` | `Position` (dünya, Y yukarı) |
| `speed` | `WorldVel` uzunluğu |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ya da 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | her tekerleğin `SlipCoef` değeri (0..1 arası bir kayma ölçüsü) |
| `loose` | herhangi bir tekerleğin zemin malzemesi Grass, Ice, Sand, Dirt, Green veya RoadIce ise 1 |
| `airborne` | arabanın zeminle teması yoksa 1 |
| `respawns` | koşu başladığından beri yeniden doğma sayısı |

## Koşular {#runs}

- Bir koşu, yarış süresinin negatif olmadığı ilk karede **başlar** (geri sayım kaydedilmez).
- Oyun alanının UI sırası bitiş sırası (değer 11) olduğunda **biter**: dosya tamamlanmış olarak yazılır, son
  yarış süresi `seconds` değeri olur.
- Yarış saati yarım saniyeden fazla geriye giderse (yeniden başlatma) ya da oyuncu oyun alanından çıkarsa
  **terk edilir** - adında `_partial` olan ve `"complete": false` içeren bir dosya olarak yazılır.
- 20 satırdan az olan bir koşu yazılmaz.

## Dosya {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Adı `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` biçimindedir. Harita adındaki biçimlendirme kodları çıkarılır ve
çift tırnaklar tek tırnakla değiştirilir. Değerler dört ondalıkla yazılır. Biçim,
[heat3d tur dosyası](lap-format.md#the-csv-form) sayfasında anlatılır.

Başlıktaki `meta`, `"slip": "index"` içerir - `slipIndex.*` kanalları Trackmania'nın kendi 0..1 kayma
ölçüsüdür, fiziksel bir kayma değildir - ve `"discipline": "arcade"`.
