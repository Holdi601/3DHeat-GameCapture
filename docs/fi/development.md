---
title: Kehittäminen
nav_order: 11
lang: "fi"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Kehittäminen {#development}

## Repositorion rakenne {#repository-layout}

| Polku | Sisältö |
|---|---|
| `heat3d_capture/__main__.py` | komentorivi: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out -asettelu), `fulllap.py` (Forza-kierrostiedostot, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (yhteinen kierrosasiakirja) |
| `heat3d_capture/capture/` | `sources.py` (suora tallennus, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (mitä skanneri ajaa), `estimator.py` (PyTorch-polku, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (kirjoittaja), `reference.py` (synteettinen vertailutaso) |
| `heat3d_capture/scan/` | `session.py` (yksi skannaus), `reconstruct.py` (avainkehykset geometriaksi), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: tallenteen HUD - pistepopup, kuolemanäytöt, pienoiskartan rata, tappovirta (`profiles.py` pelikohtaisesti) |
| `heat3d_capture/locate/` | `locate`: tason renderöinnit, tietokanta, sovittaminen, pelikohtainen malli, pienoiskartta |
| `heat3d_capture/ui/` | `__main__.py` (käynnistys ja riippuvuustarkistus), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | julkaisutarkistus ja päivitin |
| `mods/beamng/heat3d/` | BeamNG-protokollamodi |
| `mods/trackmania/Heat3dRecorder/` | Openplanet-liitännäinen |
| `tools/export_onnx.py` | syvyysmallin muunnin |
| `tools/gen_docs_reference.py` | kirjoittaa `docs/cli-reference.md`-tiedoston kohdasta `--help`; `--check` kertoo, onko se vanhentunut |
| `tools/docs_diagrams.py` | piirtää kaaviot kansioon `docs/assets/img/` (kielikohtaisesti `--lang`-valinnalla) |
| `tools/sync_wiki.py` | luo `docs/wiki/`-kansion uudelleen kansiosta `docs/` |
| `models/` | muunnetut `.onnx`-tiedostot (ei versioida) |
| `tests/` | testisarja; `scene.py` ja `track_scene.py` renderöivät synteettisiä kohtauksia tunnetulla geometrialla |
| `docs/` | tämä dokumentaatio; `docs/wiki/` luodaan siitä |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Skannauslogiikassa ei ole Qt:tä: `ScanSession` ja `Reconstructor` ottavat vastaan tavallisia funktioita, ja niitä voi ajaa skriptistä tai testistä. Esimerkki:

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

## Ympäristö {#the-environment}

Projekti käyttää virtuaaliympäristöä kansiossa `.venv` (luodaan `scan.bat`-tiedostolla tai käsin). Käyttöliittymään koskevat testit tarvitsevat siihen **PySide6**-paketin, jonka `requirements.txt` asentaa nimellä `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Mallimuuntimelle, PyTorch-syvyystesteille ja offline-polulle asenna PyTorch (näytönohjaimen mukaan) **ennen** `requirements.txt`-tiedostoa. Sen jälkeen asenna `requirements-offline.txt` ja sen `vggt`-rivi offline-ratkaisijalle sekä `onnxscript` muuntimelle. Katso [Ajoaika ja riippuvuudet](runtime.md#installing-by-hand).

## Testien ajaminen {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` asettaa `testpaths = tests` ja vaientaa `huggingface_hub`-kirjaston `UserWarning`-varoitukset. Sarjassa on useita satoja tarkistuksia. Useimmat eivät tarvitse peliä, näytönohjainta eivätkä tallennuslaitteistoa.

Mitkä testit ohittavat itsensä ja miksi:

| Testit | Ohitetaan, kun |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, ikkunaa ohjaavat testit tiedostossa `test_ui_drives_a_scan.py` | `models/depth-*.onnx`-tiedostoa ei ole - aja ensin `tools/export_onnx.py` |
| GPU-arvioijan testit tiedostossa `test_depth.py` | PyTorchia ei ole asennettu tai CUDA-laitetta ei ole; `fit_scale`- ja `AffineFit`-testit ajetaan aina |
| joitakin tapauksia tiedostoista `test_offline.py` ja `test_solveprep.py` | OpenCV:ssä ei ole videokooderia synteettisen klipin kirjoittamiseen |
| `test_hotkeys.py` | rekisteröintitestit vaativat Windowsin; varatesti ajetaan muualla |
| `test_course_ground.py` | `HEAT3D_COURSE` ei ole asetettu |
| muutama fuusiotesti | synteettinen tapaus ei yhdistänyt mitään |

### Käynnistystesti {#the-launch-test}

`tests/test_launch.py` ajaa oikean käynnistyskohdan, `python -m heat3d_capture.ui`, aliprosessina (`QT_QPA_PLATFORM=offscreen` asetettuna). Se tarkistaa, että ohjelma pääsee tapahtumasilmukkaan ja pysyy käynnissä. Testi on olemassa, koska ensimmäinen versio kaatui joka käynnistyksellä, vaikka kaikki muut testit menivät läpi. Ne kaikki luovat itse `QApplication`-olion ja rakentavat sitten ikkunan. Näin ohitetaan se yksi järjestys, jonka käyttäjä tekee: riippuvuustarkistus luo ensin sovelluksen. Komponenttitesti, joka rakentaa oman ympäristönsä, ei näe vikaa siinä, miten ympäristö rakennetaan.

### Vertailutieto {#ground-truth}

- `tests/test_accuracy.py` - synteettinen huone tunnetulta polulta analyyttisellä syvyydellä; katso [Tason rekonstruktio](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - tien leveys, radan mittakaavan poiminta, peittoruudukko luettuna kirjoituksen aikana ja se, miksi silmukan sulkeminen on pois päältä.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - telemetrian asettelut paketeilla ja sivuilla, jotka on rakennettu dokumentoiduista rakenteista, sekä niiden kirjoittamat kierrostiedostot (kanoniset kanavanimet, `meta`, ei `NaN`-arvoja JSONissa). `tests/test_trackmania_plugin.py` lukee Openplanet-liitännäisen lähdekoodia selvittääkseen, mitä se kirjoittaa kunkin ajon kuvaukseen.
- `tests/test_route_record.py` - `route`-tiedosto on levyllä kokonaisena ennen kuin tallennin pysähtyy.
- `tests/test_telemetry_pose.py` - Forza-asennot pelin omissa koordinaateissa, kiertymien (yaw, pitch, roll) suunnat ja telemetria-aukko, joka silloitetaan kuvallisesti peilatussa maailmassa.
- `tests/test_glb.py` - GLB-sopimus. Katselimen omat testit lukevat tältä kirjoittajalta tulleen vertailutason, joten tiedostomuotoa testataan molemmin puolin.

### Viedyn radan tarkistaminen kierroksia vasten {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` tarkistaa, että [3DHeat GameFilesin](https://github.com/Holdi601/3DHeat-GameFiles) viemä rata todella on tallennetun auton alla. Auton pitäisi olla ajokorkeuden verran sen pinnan yläpuolella, joka on suoraan sen alla. Osoita testi viedyn radan kantanimeen (sen vieressä ovat `.glb` ja sen `.json`):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Rata, jossa on isoja hyppyjä, voi epäonnistua tarkoituksella: auto on ilmassa maan yllä, joka siellä todella on.

## Käytännöt {#conventions}

- Koodi kansiossa `heat3d_capture/` tuo raskaat riippuvuudet (OpenCV, ONNX Runtime, PyTorch, Qt) laiskasti funktioiden sisällä. Siksi moduulin tuominen, `--help`-komennon ajaminen tai telemetrian tallentimien ajaminen ei maksa mitään.
- Työsäikeet eivät koskaan kosketa Qt-widgetejä. Tulokset siirtyvät käyttöliittymäsäikeeseen Qt-signaaleina.
- `.gitignore` pitää tallenteet, kierrostiedostot, verkot, mallipainot ja videot poissa gitistä kansioiden ja tiedostotyyppien mukaan.
- Commitit ja julkaisut: versio on tiedosto `VERSION`. Julkaisut ovat [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture):n GitHub-julkaisuja, jotka päivitin lukee ([Päivitykset](updates.md)).
