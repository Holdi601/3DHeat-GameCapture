---
title: "Razvoj"
nav_order: 11
lang: "bs"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Razvoj {#development}

## Raspored repozitorija {#repository-layout}

| Putanja | Sadržaj |
|---|---|
| `heat3d_capture/__main__.py` | komandna linija: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (raspored Data Out), `fulllap.py` (Forza datoteke krugova, relej), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (zajednički dokument kruga) |
| `heat3d_capture/capture/` | `sources.py` (snimanje uživo, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (ono što skener pokreće), `estimator.py` (PyTorch putanja, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (pisač), `reference.py` (sintetički referentni nivo) |
| `heat3d_capture/scan/` | `session.py` (jedno skeniranje), `reconstruct.py` (ključni kadrovi u geometriju), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD snimka - skočni prozor s bodovima, ekrani smrti, staza na mini-mapi, kill feed (`profiles.py` po igri) |
| `heat3d_capture/locate/` | `locate`: renderi nivoa, baza podataka, uparivanje, model po mapi, mini-mapa |
| `heat3d_capture/ui/` | `__main__.py` (ulaz i provjera zavisnosti), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | provjera izdanja i ažurirač |
| `mods/beamng/heat3d/` | BeamNG protokolni mod |
| `mods/trackmania/Heat3dRecorder/` | Openplanet dodatak |
| `tools/export_onnx.py` | pretvarač modela dubine |
| `tools/gen_docs_reference.py` | piše `docs/cli-reference.md` iz `--help`; `--check` kaže je li zastario |
| `tools/docs_diagrams.py` | crta dijagrame u `docs/assets/img/` (po jeziku sa `--lang`) |
| `tools/sync_wiki.py` | iznova generira `docs/wiki/` iz `docs/` |
| `models/` | pretvorene `.onnx` datoteke (nisu u verzioniranju) |
| `tests/` | skup testova; `scene.py` i `track_scene.py` renderiraju sintetičke scene poznate geometrije |
| `docs/` | ova dokumentacija; `docs/wiki/` se generira iz nje |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skeniranja nema Qt: `ScanSession` i `Reconstructor` primaju obične pozive (callable) i mogu se
pokretati iz skripte ili testa. Primjer:

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

Projekat koristi virtualno okruženje u `.venv` (pravi ga `scan.bat` ili se pravi ručno). Testovi
koji diraju sučelje u njemu trebaju **PySide6**, koji `requirements.txt` instalira kao
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Za pretvarač modela, PyTorch testove dubine i offline putanju instalirajte PyTorch (usklađen s
grafičkom karticom) **prije** `requirements.txt`; zatim `requirements-offline.txt` i njegovu `vggt` liniju za
offline rješavač, te `onnxscript` za pretvarač. Pogledajte
[Runtime i zavisnosti](runtime.md#installing-by-hand).

## Pokretanje testova {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` postavlja `testpaths = tests` i utišava `UserWarning` iz `huggingface_hub`. Skup
ima nekoliko stotina provjera; većini ne trebaju ni igra, ni grafička kartica, ni oprema za snimanje.

Šta se samo preskače i zašto:

| Testovi | Preskaču se kada |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testovi koji upravljaju prozorom u `test_ui_drives_a_scan.py` | nema `models/depth-*.onnx` - prvo pokrenite `tools/export_onnx.py` |
| testovi GPU procjenjivača u `test_depth.py` | PyTorch nije instaliran ili nema CUDA uređaja; testovi `fit_scale` i `AffineFit` rade bez obzira na to |
| neki slučajevi u `test_offline.py` i `test_solveprep.py` | OpenCV nema video enkoder za pisanje sintetičkog klipa |
| `test_hotkeys.py` | testovi registracije trebaju Windows; rezervni test radi i drugdje |
| `test_course_ground.py` | `HEAT3D_COURSE` nije postavljen |
| nekoliko testova fuzije | sintetički slučaj nije ništa fuzionirao |

### Test pokretanja {#the-launch-test}

`tests/test_launch.py` pokreće pravu ulaznu tačku, `python -m heat3d_capture.ui`, kao podproces
(sa `QT_QPA_PLATFORM=offscreen`) i provjerava da dođe do petlje događaja i da ostane živa. Postoji
jer se prvi build rušio pri svakom pokretanju dok su svi ostali testovi prolazili: svi oni sami prave
`QApplication` i tek onda grade prozor, čime preskaču jedini slijed koji korisnik
izvodi - provjeru zavisnosti koja prva pravi aplikaciju. Test komponente koja sam gradi
svoje okruženje ne može vidjeti grešku u načinu na koji se okruženje gradi.

### Referentna istina {#ground-truth}

- `tests/test_accuracy.py` - sintetička soba iz poznate putanje s analitičkom dubinom; pogledajte
  [Rekonstrukcija nivoa](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - širina puta, izvlačenje razmjera staze, mreža pokrivenosti
  koja se čita dok se piše, i zašto zatvaranje petlje ostaje isključeno.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - rasporedi telemetrije, na paketima i
  stranicama izgrađenim iz dokumentiranih struktura, te datoteke krugova koje pišu (kanonska imena
  kanala, `meta`, bez `NaN` u JSON-u). `tests/test_trackmania_plugin.py` čita izvorni kod
  Openplanet dodatka da vidi šta upisuje u opis svake vožnje.
- `tests/test_route_record.py` - datoteka `route` je na disku, cijela, prije nego što snimač stane.
- `tests/test_telemetry_pose.py` - Forza poze u koordinatama same igre, smjerovi skretanja (yaw),
  posrtanja (pitch) i valjanja (roll), te prekid telemetrije vizualno premošten u zrcaljenom svijetu.
- `tests/test_glb.py` - GLB ugovor; vlastiti testovi preglednika parsiraju referentni nivo koji
  piše ovaj pisač, pa je format testiran s obje strane.

### Provjera izvezene staze prema krugovima {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` provjerava da staza izvezena iz
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) zaista leži ispod snimljenog
auta - auto treba biti na visini klirensa iznad površine direktno ispod sebe. Usmjerite ga na
korijen imena izvezene staze (`.glb` i njegov `.json` pored njega):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Staza s velikim skokovima može pasti namjerno: auto je u zraku iznad tla koje postoji.

## Konvencije {#conventions}

- Kod u `heat3d_capture/` uvozi teške zavisnosti (OpenCV, ONNX Runtime, PyTorch, Qt)
  lijeno, unutar funkcija, pa uvoz modula, pokretanje `--help` ili pokretanje telemetrijskih
  snimača ne košta ništa.
- Radne niti nikad ne diraju Qt widgete; rezultati prelaze u nit sučelja kao Qt signali.
- Snimke, datoteke krugova, mreže, težine modela i video drži izvan gita `.gitignore`, po
  folderu i po tipu datoteke.
- Commitovi i izdanja: verzija je datoteka `VERSION`; izdanja su GitHub izdanja
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), koja ažurirač
  čita ([Ažuriranja](updates.md)).
