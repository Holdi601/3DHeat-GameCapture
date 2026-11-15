---
title: Razvoj
nav_order: 11
lang: "sl"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Razvoj {#development}

## Postavitev repozitorija {#repository-layout}

| Pot | Vsebina |
|---|---|
| `heat3d_capture/__main__.py` | ukazna vrstica: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (postavitev Data Out), `fulllap.py` (datoteke krogov Forza, posredovanje), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (skupni dokument kroga) |
| `heat3d_capture/capture/` | `sources.py` (zajem v živo, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (kar zažene skener), `estimator.py` (pot PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (pisalnik), `reference.py` (sintetični referenčni nivo) |
| `heat3d_capture/scan/` | `session.py` (skeniranje), `reconstruct.py` (ključne okvirje v geometrijo), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: HUD posnetka – pojavno okno točk, zasloni smrti, mini zemljevid proge, seznam ubojev (`profiles.py` za vsako igro) |
| `heat3d_capture/locate/` | `locate`: upodobitve nivoja, zbirka podatkov, ujemanje, model za vsak zemljevid, mini zemljevid |
| `heat3d_capture/ui/` | `__main__.py` (vstop in preverjanje odvisnosti), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | preverjanje izdaje in posodobitev |
| `mods/beamng/heat3d/` | modifikacija protokola za BeamNG |
| `mods/trackmania/Heat3dRecorder/` | vtičnik Openplanet |
| `tools/export_onnx.py` | pretvornik modela globine |
| `tools/gen_docs_reference.py` | zapiše `docs/cli-reference.md` iz `--help`; `--check` pove, ali je zastarel |
| `tools/docs_diagrams.py` | nariše diagrame v `docs/assets/img/` (po jeziku z `--lang`) |
| `tools/sync_wiki.py` | ponovno ustvari `docs/wiki/` iz `docs/` |
| `models/` | pretvorjene datoteke `.onnx` (niso v nadzoru različic) |
| `tests/` | sklop testov; `scene.py` in `track_scene.py` upodobita sintetične prizore z znano geometrijo |
| `docs/` | ta dokumentacija; `docs/wiki/` je ustvarjen iz nje |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Logika skeniranja nima Qt. `ScanSession` in `Reconstructor` sprejmeta navadne klicne
objekte in ju lahko poganjate iz skripte ali testa. Primer:

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

## Okolje {#the-environment}

Projekt uporablja virtualno okolje v `.venv` (ustvari ga `scan.bat` ali ročno). Testi, ki se
dotikajo vmesnika, potrebujejo **PySide6** v njem, ki ga `requirements.txt` namesti kot
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Za pretvornik modela, teste globine s PyTorch in pot brez povezave namestite PyTorch (ustrezen
grafični kartici) **pred** `requirements.txt`; nato `requirements-offline.txt` in njegovo vrstico
`vggt` za reševalnik brez povezave ter `onnxscript` za pretvornik. Glejte
[Izvajanje in odvisnosti](runtime.md#installing-by-hand).

## Zagon testov {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` nastavi `testpaths = tests` in utiša opozorila `UserWarning` iz `huggingface_hub`.
Sklop ima nekaj sto preverjanj; večina ne potrebuje ne igre ne grafične kartice ne strojne
opreme za zajem.

Kaj se preskoči samo od sebe in zakaj:

| Testi | Preskočijo se, kadar |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, testi, ki upravljajo okno, v `test_ui_drives_a_scan.py` | ni datoteke `models/depth-*.onnx` - najprej zaženite `tools/export_onnx.py` |
| testi ocenjevalnika na grafični kartici v `test_depth.py` | PyTorch ni nameščen ali ni naprave CUDA; testi `fit_scale` in `AffineFit` tečejo vedno |
| nekateri primeri v `test_offline.py` in `test_solveprep.py` | OpenCV nima kodirnika za video, s katerim bi zapisal sintetični posnetek |
| `test_hotkeys.py` | testi registracije potrebujejo Windows; test rezervne poti teče drugje |
| `test_course_ground.py` | `HEAT3D_COURSE` ni nastavljena |
| nekateri testi zlivanja | sintetični primer ni zlil ničesar |

### Test zagona {#the-launch-test}

`tests/test_launch.py` zažene pravi vstopno točko, `python -m heat3d_capture.ui`, kot podproces
(z `QT_QPA_PLATFORM=offscreen`) in preveri, da doseže zanko dogodkov in ostane zagnan. Nastal je
zato, ker je prva različica ob vsakem zagonu padla, medtem ko so vsi drugi testi uspeli: vsi sami
ustvarijo `QApplication` in nato zgradijo okno, s čimer preskočijo zaporedje, ki ga uporabnik res
izvede – preverjanje odvisnosti najprej ustvari aplikacijo. Preizkus komponente, ki sam gradi svoje
okolje, ne more videti napake v tem, kako je okolje zgrajeno.

### Referenčni podatki (ground truth) {#ground-truth}

- `tests/test_accuracy.py` - sintetična soba z znano potjo in analitično globino; glejte
  [Rekonstrukcija nivoja](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - širina ceste, izvlečenje merila proge, mreža pokritosti,
  prebrana med zapisovanjem, in zakaj ostane zapiranje zanke izklopljeno.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - postavitve telemetrije na paketih in
  straneh, zgrajenih iz dokumentiranih struktur, ter datoteke krogov, ki jih zapisujejo (kanonična
  imena kanalov, `meta`, brez `NaN` v JSON). `tests/test_trackmania_plugin.py` prebere izvorno kodo
  vtičnika Openplanet, da preveri, kaj zapiše v opis vsakega teka.
- `tests/test_route_record.py` - datoteka `route` je na disku cela, preden se snemalnik ustavi.
- `tests/test_telemetry_pose.py` - položaji Forze v lastnih koordinatah igre, smeri zasuka,
  nagiba in valjanja ter vrzel v telemetriji, premoščena vizualno v zrcaljenem svetu.
- `tests/test_glb.py` - pogodba GLB; lastni testi pregledovalnika razčlenijo referenčni nivo, ki ga zapiše
  ta pisalnik, zato je format preizkušen na obeh straneh.

### Preverjanje izvožene proge z krogi {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` preveri, ali proga, izvožena z
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles), res leži pod posneto vozilo –
vozilo mora biti na višini vožnje nad površino tik pod njim. Usmerite ga na osnovno ime izvožene
proge (datoteka `.glb` in njena `.json` ob njej):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Proga z velikimi skoki lahko zaradi zasnove odpove: vozilo je v zraku nad tlemi, ki so tam.

## Dogovori {#conventions}

- Koda pod `heat3d_capture/` uvaža težke odvisnosti (OpenCV, ONNX Runtime, PyTorch, Qt) leno,
  znotraj funkcij, zato uvoz modula, zagon `--help` ali zagon snemalnikov telemetrije ne porabi
  ničesar.
- Delovne niti se nikoli ne dotikajo gradnikov Qt; rezultati do niti vmesnika pridejo kot signali Qt.
- Posnetki, datoteke krogov, mreže, uteži modelov in video so z `.gitignore` izločeni iz gita – po
  mapi in po vrsti datoteke.
- Predaje (commiti) in izdaje: različica je v datoteki `VERSION`; izdaje so GitHub izdaje
  repozitorija [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), ki jih
  bere posodabljalnik ([Posodobitve](updates.md)).
