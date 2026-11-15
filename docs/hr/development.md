---
title: Razvoj
nav_order: 11
lang: "hr"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Razvoj {#development}

## Raspored repozitorija {#repository-layout}

| Putanja | Sadržaj |
|---|---|
| `heat3d_capture/__main__.py` | naredbeni redak: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (raspored Data Out), `fulllap.py` (datoteke krugova Forze, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (zajednički dokument krugova) |
| `heat3d_capture/capture/` | `sources.py` (snimanje uživo, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (ono što pokreće skener), `estimator.py` (put s PyTorchom, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (pisac), `reference.py` (sintetička referentna razina) |
| `heat3d_capture/scan/` | `session.py` (jedno skeniranje), `reconstruct.py` (ključni kadrovi u geometriju), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD snimke - skočni prozor bodova, zasloni smrti, put na mini karti, popis eliminacija (`profiles.py` po igri) |
| `heat3d_capture/locate/` | `locate`: prikazi razine, baza podataka, uparivanje, model po karti, mini karta |
| `heat3d_capture/ui/` | `__main__.py` (ulaz i provjera ovisnosti), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | provjera izdanja i ažuriranje |
| `mods/beamng/heat3d/` | mod BeamNG protokola |
| `mods/trackmania/Heat3dRecorder/` | dodatak Openplanet |
| `tools/export_onnx.py` | pretvarač modela dubine |
| `tools/gen_docs_reference.py` | piše `docs/cli-reference.md` iz `--help`; `--check` kaže je li zastarjelo |
| `tools/docs_diagrams.py` | crta dijagrame u `docs/assets/img/` (po jeziku s `--lang`) |
| `tools/sync_wiki.py` | ponovno stvara `docs/wiki/` iz `docs/` |
| `models/` | pretvorene `.onnx` datoteke (nisu u verziji) |
| `tests/` | skup testova; `scene.py` i `track_scene.py` iscrtavaju sintetičke scene poznate geometrije |
| `docs/` | ova dokumentacija; `docs/wiki/` nastaje iz nje |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skeniranja nema Qt: `ScanSession` i `Reconstructor` primaju obične pozive funkcija i mogu
se pokretati iz skripte ili testa. Primjer:

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

## Okruženje {#the-environment}

Projekt koristi virtualno okruženje u `.venv` (stvara ga `scan.bat` ili ručno). Testovi koji diraju
sučelje trebaju **PySide6** u njemu, koji `requirements.txt` instalira kao `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Za pretvarač modela, testove dubine s PyTorchom i izvanmrežni put instalirajte PyTorch (prilagođen
grafičkoj kartici) **prije** `requirements.txt`; zatim `requirements-offline.txt` i njegov redak
`vggt` za izvanmrežni rješavač te `onnxscript` za pretvarač. Vidi
[Runtime i ovisnosti](runtime.md#installing-by-hand).

## Pokretanje testova {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` postavlja `testpaths = tests` i utišava `UserWarning` upozorenja iz `huggingface_hub`.
Skup ima nekoliko stotina provjera; većina ne treba ni igru, ni grafičku karticu ni hardver za snimanje.

Što se samo preskače i zašto:

| Testovi | Preskače se kad |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testovi upravljanja prozorom u `test_ui_drives_a_scan.py` | nema `models/depth-*.onnx` - prvo pokrenite `tools/export_onnx.py` |
| testovi GPU procjenitelja u `test_depth.py` | PyTorch nije instaliran ili nema CUDA uređaja; testovi `fit_scale` i `AffineFit` izvode se uvijek |
| neki slučajevi u `test_offline.py` i `test_solveprep.py` | OpenCV nema video kodirnik za zapisivanje sintetičkog isječka |
| `test_hotkeys.py` | testovi registracije trebaju Windows; test zamjenskog rješenja izvodi se drugdje |
| `test_course_ground.py` | `HEAT3D_COURSE` nije postavljen |
| nekoliko testova spajanja | sintetički slučaj nije spojio ništa |

### Test pokretanja {#the-launch-test}

`tests/test_launch.py` pokreće pravu ulaznu točku, `python -m heat3d_capture.ui`, kao podproces
(s `QT_QPA_PLATFORM=offscreen`) i provjerava da dođe do petlje događaja i ostane pokrenuta. Postoji
zato što je prva verzija padala pri svakom pokretanju, dok su svi ostali testovi prolazili: svi sami
stvaraju `QApplication` pa zatim grade prozor, čime preskaču jedan slijed koji korisnik izvodi -
provjeru ovisnosti koja prvo stvara aplikaciju. Test komponente koji sam gradi vlastito okruženje ne
može vidjeti grešku u tome kako se okruženje gradi.

### Referentna istina {#ground-truth}

- `tests/test_accuracy.py` - sintetička soba iz poznate putanje s analitičkom dubinom; vidi
  [Rekonstrukcija razine](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - širina ceste, izdvajanje mjerila staze, mreža pokrivenosti
  čitana dok se piše, i zašto zatvaranje petlje ostaje isključeno.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - rasporedi telemetrije, na paketima i
  stranicama izgrađenima iz dokumentiranih struktura, i datoteke krugova koje pišu (kanonski nazivi
  kanala, `meta`, bez `NaN` u JSON-u). `tests/test_trackmania_plugin.py` čita izvorni kod dodatka
  Openplanet za ono što piše u opis svake vožnje.
- `tests/test_route_record.py` - datoteka `route` je cijela na disku prije nego snimač stane.
- `tests/test_telemetry_pose.py` - položaji Forze u koordinatama same igre, smjerovi zakreta, nagiba
  i valjanja, te praznina u telemetriji premošćena vizualno u zrcaljenom svijetu.
- `tests/test_glb.py` - ugovor GLB-a; vlastiti testovi preglednika čitaju referentnu razinu koju
  piše ovaj pisac, pa se format testira s obiju strana.

### Provjera izvezene staze prema krugovima {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` provjerava da staza izvezena pomoću
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) stvarno leži pod snimljenim
automobilom - automobil bi trebao biti na visini vožnje iznad površine neposredno ispod njega.
Usmjerite ga na osnovni naziv izvezene staze (`.glb` i njegov `.json` uz nju):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Staza s velikim skokovima može namjerno pasti: automobil je u zraku iznad tla koje tu stvarno jest.

## Konvencije {#conventions}

- Kod pod `heat3d_capture/` uvozi teške ovisnosti (OpenCV, ONNX Runtime, PyTorch, Qt) tek unutar
  funkcija, pa uvoz modula, pokretanje `--help` ili pokretanje snimača telemetrije ne troši ništa.
- Radne niti nikad ne diraju Qt widgete; rezultati dolaze do niti sučelja kao Qt signali.
- Snimke, datoteke krugova, mreže, težine modela i video drži izvan gita `.gitignore`, po mapi i po
  vrsti datoteke.
- Commitovi i izdanja: verzija je datoteka `VERSION`; izdanja su GitHub izdanja repozitorija
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), koja ažuriranje
  čita ([Ažuriranja](updates.md)).
