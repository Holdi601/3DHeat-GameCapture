---
title: Sviluppo
nav_order: 11
lang: "it"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Sviluppo {#development}

## Struttura del repository {#repository-layout}

| Percorso | Contenuto |
|---|---|
| `heat3d_capture/__main__.py` | la riga di comando: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (layout di Data Out), `fulllap.py` (file di giro di Forza, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (il documento condiviso del giro) |
| `heat3d_capture/capture/` | `sources.py` (cattura dal vivo, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (quello che usa lo scanner), `estimator.py` (percorso PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (il writer), `reference.py` (livello di riferimento sintetico) |
| `heat3d_capture/scan/` | `session.py` (una scansione), `reconstruct.py` (fotogrammi chiave in geometria), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: l'HUD di una registrazione - popup dei punti, schermate di morte, tracciato della minimappa, feed delle uccisioni (`profiles.py` per gioco) |
| `heat3d_capture/locate/` | `locate`: i render del livello, il database, il matching, il modello per mappa, la minimappa |
| `heat3d_capture/ui/` | `__main__.py` (ingresso e controllo delle dipendenze), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | il controllo delle versioni e l'aggiornamento |
| `mods/beamng/heat3d/` | la mod del protocollo per BeamNG |
| `mods/trackmania/Heat3dRecorder/` | il plugin per Openplanet |
| `tools/export_onnx.py` | il convertitore del modello di profondità |
| `tools/gen_docs_reference.py` | scrive `docs/cli-reference.md` da `--help`; `--check` dice se è superato |
| `tools/docs_diagrams.py` | disegna i diagrammi in `docs/assets/img/` (per lingua con `--lang`) |
| `tools/sync_wiki.py` | rigenera `docs/wiki/` da `docs/` |
| `models/` | file `.onnx` convertiti (non sono sotto controllo di versione) |
| `tests/` | la suite di test; `scene.py` e `track_scene.py` disegnano scene sintetiche con geometria nota |
| `docs/` | questa documentazione; `docs/wiki/` è generata da qui |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

La logica di scansione non contiene Qt: `ScanSession` e `Reconstructor` accettano semplici
callable e possono essere guidati da uno script o da un test. Esempio:

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

## L'ambiente {#the-environment}

Il progetto usa un ambiente virtuale in `.venv` (creato da `scan.bat` o a mano). I test che
toccano l'interfaccia richiedono **PySide6** al suo interno, che `requirements.txt` installa come
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Per il convertitore del modello, i test del percorso di profondità PyTorch e il percorso offline,
installa PyTorch (adatto alla GPU) **prima** di `requirements.txt`; poi `requirements-offline.txt`
e la sua riga `vggt` per il solutore offline, e `onnxscript` per il convertitore. Vedi
[Runtime e dipendenze](runtime.md#installing-by-hand).

## Eseguire i test {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` imposta `testpaths = tests` e silenzia i `UserWarning` di `huggingface_hub`. La
suite contiene diverse centinaia di controlli; la maggior parte non richiede né un gioco, né una
GPU, né hardware di cattura.

Quali test si saltano da soli, e perché:

| Test | Saltato quando |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, i test della finestra in `test_ui_drives_a_scan.py` | manca `models/depth-*.onnx` - esegui prima `tools/export_onnx.py` |
| i test dello stimatore GPU in `test_depth.py` | PyTorch non è installato, oppure non c'è un dispositivo CUDA; i test di `fit_scale` e `AffineFit` girano comunque |
| alcuni casi di `test_offline.py` e `test_solveprep.py` | OpenCV non ha un encoder video per scrivere il clip sintetico |
| `test_hotkeys.py` | i test di registrazione richiedono Windows; il test di ripiego gira altrove |
| `test_course_ground.py` | `HEAT3D_COURSE` non è impostato |
| alcuni test di fusione | un caso sintetico non ha fuso nulla |

### Il test di avvio {#the-launch-test}

`tests/test_launch.py` esegue il vero punto di ingresso, `python -m heat3d_capture.ui`, come
sottoprocesso (con `QT_QPA_PLATFORM=offscreen`) e verifica che arrivi al ciclo degli eventi e
resti in funzione. Esiste perché la prima versione andava in crash a ogni avvio mentre tutti gli
altri test passavano: loro creano tutti un `QApplication` da soli e poi costruiscono la finestra,
saltando l'unica sequenza che un utente esegue davvero - il controllo delle dipendenze che crea
per primo un'applicazione. Un test di componente che costruisce il proprio ambiente non può
vedere un guasto nel modo in cui l'ambiente viene costruito.

### Verità di riferimento {#ground-truth}

- `tests/test_accuracy.py` - una stanza sintetica da un percorso noto con profondità analitica;
  vedi [Ricostruzione del livello](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - larghezza della strada, estrazione della scala del tracciato,
  la griglia di copertura letta mentre viene scritta, e perché la chiusura del loop resta
  disattivata.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - i layout di telemetria, su pacchetti e
  pagine costruiti dalle strutture documentate, e i file di giro che scrivono (nomi canonici dei
  canali, `meta`, nessun `NaN` nel JSON). `tests/test_trackmania_plugin.py` legge il codice
  sorgente del plugin per Openplanet per vedere cosa scrive nella descrizione di ogni run.
- `tests/test_route_record.py` - il file `route` è su disco, intero, prima che il registratore si
  fermi.
- `tests/test_telemetry_pose.py` - pose di Forza nelle coordinate del gioco, i sensi di yaw, pitch
  e roll, e un buco di telemetria colmato visivamente nel mondo specchiato.
- `tests/test_glb.py` - il contratto GLB; i test del visualizzatore leggono un livello di riferimento
  scritto da questo writer, quindi il formato è testato da entrambi i lati.

### Verificare un tracciato esportato con i giri {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` controlla che un tracciato esportato con
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) stia davvero sotto l'auto
registrata - l'auto dovrebbe trovarsi a un'altezza da terra sopra la superficie che ha
direttamente sotto. Punta il test al nome base di un tracciato esportato (il `.glb` e il suo
`.json` accanto):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Un tracciato con salti grandi può fallire per progetto: l'auto è in aria sopra un terreno che
esiste.

## Convenzioni {#conventions}

- Il codice in `heat3d_capture/` importa le dipendenze pesanti (OpenCV, ONNX Runtime, PyTorch, Qt)
  in modo pigro, dentro le funzioni, così importare un modulo, eseguire `--help` o far girare i
  registratori di telemetria non costa nulla.
- I thread di lavoro non toccano mai i widget di Qt; i risultati arrivano al thread dell'interfaccia
  come segnali di Qt.
- Registrazioni, file di giro, mesh, pesi dei modelli e video restano fuori da git grazie a
  `.gitignore`, per cartella e per tipo di file.
- Commit e rilasci: la versione è il file `VERSION`; i rilasci sono release su GitHub di
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), che l'aggiornatore
  legge ([Aggiornamenti](updates.md)).
