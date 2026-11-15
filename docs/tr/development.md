---
title: Geliştirme
nav_order: 11
lang: "tr"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Geliştirme {#development}

## Depo düzeni {#repository-layout}

| Yol | İçerik |
|---|---|
| `heat3d_capture/__main__.py` | komut satırı: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out düzeni), `fulllap.py` (Forza tur dosyaları, aktarma), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (ortak tur belgesi) |
| `heat3d_capture/capture/` | `sources.py` (canlı yakalama, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (tarayıcının çalıştırdığı), `estimator.py` (PyTorch yolu, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (yazıcı), `reference.py` (sentetik referans seviyesi) |
| `heat3d_capture/scan/` | `session.py` (bir tarama), `reconstruct.py` (anahtar kareler geometriye), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: bir kaydın HUD'u - puan açılır penceresi, ölüm ekranları, mini harita parkuru, öldürme akışı (`profiles.py`, oyun başına) |
| `heat3d_capture/locate/` | `locate`: seviyenin görüntüleri, veritabanı, eşleştirme, oyun başına model, mini harita |
| `heat3d_capture/ui/` | `__main__.py` (giriş ve bağımlılık denetimi), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | sürüm denetimi ve güncelleyici |
| `mods/beamng/heat3d/` | BeamNG protokol modu |
| `mods/trackmania/Heat3dRecorder/` | Openplanet eklentisi |
| `tools/export_onnx.py` | derinlik modeli dönüştürücüsü |
| `tools/gen_docs_reference.py` | `--help` çıktısından `docs/cli-reference.md` dosyasını yazar; `--check` dosyanın eski olup olmadığını söyler |
| `tools/docs_diagrams.py` | `docs/assets/img/` içindeki şemaları çizer (dil başına `--lang` ile) |
| `tools/sync_wiki.py` | `docs/wiki/` klasörünü `docs/` klasöründen yeniden üretir |
| `models/` | dönüştürülmüş `.onnx` dosyaları (sürüm kontrolünde değil) |
| `tests/` | test paketi; `scene.py` ve `track_scene.py` bilinen geometriye sahip sentetik sahneleri çizer |
| `docs/` | bu belgeler; `docs/wiki/` buradan üretilir |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Tarama mantığında Qt yoktur: `ScanSession` ve `Reconstructor` düz çağrılabilirler alır ve bir
betikten ya da bir testten yönetilebilirler. Örnek:

```python
from heat3d_capture.depth.onnx_estimator import OnnxDepthEstimator
from heat3d_capture.scan.session import Quality, ScanSession, ScanSettings

settings = ScanSettings(source="walk.mp4", quality=Quality.BALANCED, field_of_view=90.0,
                        camera_height=1.70)
session = ScanSession(settings, estimator=OnnxDepthEstimator("models/depth-small-518.onnx"))
session.start()
session.wait()
print(session.progress.message, session.export("walk.glb"))
```

## Ortam {#the-environment}

Proje, `.venv` klasöründeki bir sanal ortam kullanır (`scan.bat` tarafından ya da elle
oluşturulur). Arayüze dokunan testler bu ortamda **PySide6** ister; `requirements.txt` bunu
`PySide6-Essentials` olarak kurar:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Model dönüştürücüsü, PyTorch derinlik testleri ve çevrimdışı yol için PyTorch'u (GPU'nuza uygun
olanı) **`requirements.txt` kurulmadan önce** yükleyin; ardından çevrimdışı çözücü için
`requirements-offline.txt` ve onun `vggt` satırını, dönüştürücü için de `onnxscript`'i kurun. Bkz.
[Çalışma zamanı ve bağımlılıklar](runtime.md#installing-by-hand).

## Testleri çalıştırma {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini`, `testpaths = tests` ayarını yapar ve `huggingface_hub` kaynaklı `UserWarning`
uyarılarını susturur. Paket birkaç yüz denetim içerir; çoğu ne bir oyun, ne bir GPU, ne de yakalama
donanımı gerektirir.

Hangi testlerin neden atlandığı:

| Testler | Atlanma nedeni |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, `test_ui_drives_a_scan.py` içindeki pencere süren testler | `models/depth-*.onnx` yok - önce `tools/export_onnx.py` çalıştırın |
| `test_depth.py` içindeki GPU tahmincisi testleri | PyTorch kurulu değil ya da CUDA aygıtı yok; `fit_scale` ve `AffineFit` testleri her durumda çalışır |
| bazı `test_offline.py` ve `test_solveprep.py` durumları | sentetik klibi yazmak için OpenCV'de video kodlayıcı yok |
| `test_hotkeys.py` | kayıt testleri Windows ister; yedek testi başka yerlerde çalışır |
| `test_course_ground.py` | `HEAT3D_COURSE` ayarlı değil |
| birkaç birleştirme (fusion) testi | bir sentetik durum hiçbir şeyi birleştirmedi |

### Başlatma testi {#the-launch-test}

`tests/test_launch.py`, gerçek giriş noktası olan `python -m heat3d_capture.ui` komutunu
`QT_QPA_PLATFORM=offscreen` ortam değişkeniyle bir alt süreç olarak çalıştırır ve olay döngüsüne
ulaşıp ayakta kaldığını denetler. Bu testin nedeni şudur: ilk sürüm her açılışta çöküyordu, ama
diğer bütün testler geçiyordu. Çünkü onların hepsi kendi `QApplication` nesnesini kurar ve sonra
pencereyi oluşturur. Bu da bir kullanıcının her zaman yaptığı tek sırayı atlar: bağımlılık
denetimi önce bir uygulama nesnesi oluşturur. Kendi ortamını kuran bir bileşen testi, ortamın
kurulmasındaki bir hatayı göremez.

### Doğru değer (ground truth) {#ground-truth}

- `tests/test_accuracy.py` - bilinen bir yoldan, analitik derinlikle çizilmiş sentetik bir oda; bkz.
  [Seviye yeniden oluşturma](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - yol genişliği, parkur ölçeğinin çıkarılması, yazılırken okunan
  kapsama ızgarası ve döngü kapatmanın neden kapalı kaldığı.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - telemetri düzenleri; belgelenmiş yapılardan
  kurulan paketler ve sayfalar üzerinde, ve yazdıkları tur dosyaları (standart kanal adları, `meta`,
  JSON içinde `NaN` yok). `tests/test_trackmania_plugin.py`, Openplanet eklentisinin kaynağını okur ve
  her koşunun açıklamasına ne yazdığını denetler.
- `tests/test_route_record.py` - `route` dosyası, kayıt cihazı durmadan önce tamamen diskte olur.
- `tests/test_telemetry_pose.py` - Forza pozları oyunun kendi koordinatlarında, yaw, pitch ve roll
  yönleri ve aynalanmış dünyada görsel olarak köprülenen bir telemetri boşluğu.
- `tests/test_glb.py` - GLB sözleşmesi; görüntüleyicinin kendi testleri, bu yazıcının yazdığı bir
  referans seviyesini ayrıştırır, yani biçim iki tarafta da test edilir.

### Dışa aktarılan bir parkuru turlara karşı denetlemek {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py`, [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
ile dışa aktarılan bir parkurun gerçekten kaydedilen arabanın altında olduğunu denetler: araba,
kendisinin tam altındaki yüzeyin bir sürüş yüksekliği üstünde olmalıdır. Dışa aktarılmış bir
parkurun kökünü (`.glb` ve yanındaki `.json`) gösterin:

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Büyük sıçramaları olan bir parkur, tasarım gereği başarısız olabilir: araba, orada olan bir zeminin
üzerinde havadadır.

## Kurallar {#conventions}

- `heat3d_capture/` altındaki kod, ağır bağımlılıkları (OpenCV, ONNX Runtime, PyTorch, Qt) işlevlerin
  içinde tembel olarak içe aktarır; böylece bir modülü içe aktarmak, `--help` çalıştırmak ya da
  telemetri kayıt cihazlarını çalıştırmak bir şeye mal olmaz.
- Arka plan iş parçacıkları Qt bileşenlerine hiç dokunmaz; sonuçlar Qt sinyalleriyle arayüz
  iş parçacığına geçer.
- Kayıtlar, tur dosyaları, ağlar, model ağırlıkları ve video, `.gitignore` ile klasöre ve dosya
  türüne göre git dışında tutulur.
- İşleme ve sürümler: sürüm `VERSION` dosyasındadır; sürümler, güncelleyicinin okuduğu
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) GitHub
  sürümleridir ([Güncellemeler](updates.md)).
