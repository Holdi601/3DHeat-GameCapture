---
title: "Ανάπτυξη"
nav_order: 11
lang: "el"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Ανάπτυξη {#development}

## Διάταξη του αποθετηρίου {#repository-layout}

| Διαδρομή | Περιεχόμενο |
|---|---|
| `heat3d_capture/__main__.py` | η γραμμή εντολών: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (διάταξη Data Out), `fulllap.py` (αρχεία γύρων Forza, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (το κοινό έγγραφο γύρου) |
| `heat3d_capture/capture/` | `sources.py` (ζωντανή καταγραφή, βίντεο), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (αυτό που τρέχει ο σαρωτής), `estimator.py` (διαδρομή PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (ο εγγραφέας), `reference.py` (συνθετικό επίπεδο αναφοράς) |
| `heat3d_capture/scan/` | `session.py` (μία σάρωση), `reconstruct.py` (καρέ-κλειδιά σε γεωμετρία), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: το HUD μιας εγγραφής - αναδυόμενο παράθυρο πόντων, οθόνες θανάτου, μίνι-χάρτης της πίστας, ροή φόνων (`profiles.py` για κάθε παιχνίδι) |
| `heat3d_capture/locate/` | `locate`: οι αποδόσεις του επιπέδου, η βάση δεδομένων, η αντιστοίχιση, το μοντέλο ανά χάρτη, ο μίνι-χάρτης |
| `heat3d_capture/ui/` | `__main__.py` (είσοδος και έλεγχος εξαρτήσεων), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | ο έλεγχος κυκλοφορίας και ο ενημερωτής |
| `mods/beamng/heat3d/` | το mod πρωτοκόλλου για το BeamNG |
| `mods/trackmania/Heat3dRecorder/` | το plugin για το Openplanet |
| `tools/export_onnx.py` | ο μετατροπέας του μοντέλου βάθους |
| `tools/gen_docs_reference.py` | γράφει το `docs/cli-reference.md` από το `--help`· το `--check` λέει αν είναι παλιό |
| `tools/docs_diagrams.py` | σχεδιάζει τα διαγράμματα στο `docs/assets/img/` (ανά γλώσσα με `--lang`) |
| `tools/sync_wiki.py` | ξαναφτιάχνει το `docs/wiki/` από το `docs/` |
| `models/` | μετατρεπόμενα αρχεία `.onnx` (δεν είναι υπό έλεγχο έκδοσης) |
| `tests/` | το σύνολο των δοκιμών· τα `scene.py` και `track_scene.py` αποδίδουν συνθετικές σκηνές με γνωστή γεωμετρία |
| `docs/` | αυτή η τεκμηρίωση· το `docs/wiki/` παράγεται από αυτήν |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

Η λογική σάρωσης δεν έχει Qt μέσα της: το `ScanSession` και ο `Reconstructor` δέχονται απλές
συναρτήσεις και μπορούν να τρέξουν από ένα σενάριο ή μια δοκιμή. Παράδειγμα:

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

## Το περιβάλλον {#the-environment}

Το έργο χρησιμοποιεί ένα εικονικό περιβάλλον στο `.venv` (δημιουργείται από το `scan.bat` ή με το χέρι).
Οι δοκιμές που αγγίζουν τη διεπαφή χρειάζονται το **PySide6** μέσα του, το οποίο το `requirements.txt`
εγκαθιστά ως `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Για τον μετατροπέα μοντέλου, τις δοκιμές βάθους PyTorch και τη διαδρομή χωρίς σύνδεση, εγκαταστήστε
το PyTorch (ταιριαγμένο με την κάρτα γραφικών) **πριν** από το `requirements.txt`· μετά το
`requirements-offline.txt` και τη γραμμή `vggt` του για τον λύτη χωρίς σύνδεση, και το `onnxscript`
για τον μετατροπέα. Δείτε [Runtime and dependencies](runtime.md#installing-by-hand).

## Εκτέλεση των δοκιμών {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

Το `pytest.ini` ορίζει `testpaths = tests` και σιωπά τα `UserWarning` από το `huggingface_hub`. Το
σύνολο έχει αρκετές εκατοντάδες ελέγχους· οι περισσότεροι δεν χρειάζονται ούτε παιχνίδι, ούτε κάρτα
γραφικών, ούτε υλικό καταγραφής.

Τι παρακάμπτεται μόνο του, και γιατί:

| Δοκιμές | Παρακάμπτονται όταν |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, οι δοκιμές οδήγησης παραθύρου στο `test_ui_drives_a_scan.py` | δεν υπάρχει `models/depth-*.onnx` - τρέξτε πρώτα το `tools/export_onnx.py` |
| οι δοκιμές του estimator GPU στο `test_depth.py` | δεν είναι εγκατεστημένο το PyTorch, ή δεν υπάρχει συσκευή CUDA· οι δοκιμές `fit_scale` και `AffineFit` τρέχουν πάντα |
| μερικές περιπτώσεις των `test_offline.py` και `test_solveprep.py` | το OpenCV δεν έχει κωδικοποιητή βίντεο για να γράψει το συνθετικό κλιπ |
| `test_hotkeys.py` | οι δοκιμές καταχώρισης θέλουν Windows· η δοκιμή εναλλακτικής τρέχει παντού αλλού |
| `test_course_ground.py` | δεν έχει οριστεί το `HEAT3D_COURSE` |
| μερικές δοκιμές συγχώνευσης | μια συνθετική περίπτωση δεν συγχώνευσε τίποτα |

### Η δοκιμή εκκίνησης {#the-launch-test}

Το `tests/test_launch.py` τρέχει το πραγματικό σημείο εισόδου, το `python -m heat3d_capture.ui`, ως
υποδιεργασία (με `QT_QPA_PLATFORM=offscreen`) και ελέγχει ότι φτάνει στον βρόχο συμβάντων και μένει
ανοιχτό. Υπάρχει επειδή η πρώτη έκδοση κρασάρισε σε κάθε εκκίνηση, ενώ όλες οι άλλες δοκιμές
περνούσαν: όλες δημιουργούσαν μόνες τους ένα `QApplication` και μετά έχτιζαν το παράθυρο, παρακάμπτοντας
την μία ακολουθία που κάνει ένας χρήστης - τον έλεγχο εξαρτήσεων που δημιουργεί πρώτα μια εφαρμογή. Μια
δοκιμή συστατικού που χτίζει το δικό της περιβάλλον δεν μπορεί να δει σφάλμα στον τρόπο που χτίζεται το
περιβάλλον.

### Αλήθεια εδάφους {#ground-truth}

- `tests/test_accuracy.py` - ένα συνθετικό δωμάτιο από γνωστή διαδρομή με αναλυτικό βάθος· δείτε
  [Level reconstruction](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - το πλάτος του δρόμου, η εξαγωγή κλίμακας πίστας, ο χάρτης
  κάλυψης που διαβάζεται ενώ γράφεται, και γιατί το κλείσιμο βρόχου μένει ανοιχτό.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - οι διατάξεις τηλεμετρίας, σε πακέτα και
  σελίδες χτισμένα από τις τεκμηριωμένες δομές, και τα αρχεία γύρων που γράφουν (κανονικά ονόματα
  καναλιών, `meta`, χωρίς `NaN` στο JSON). Το `tests/test_trackmania_plugin.py` διαβάζει τον πηγαίο
  κώδικα του plugin του Openplanet για το τι γράφει στην περιγραφή κάθε διαδρομής.
- `tests/test_route_record.py` - το αρχείο `route` είναι ολόκληρο στον δίσκο πριν σταματήσει η
  καταγραφή.
- `tests/test_telemetry_pose.py` - στάσεις Forza στις δικές του συντεταγμένες του παιχνιδιού, οι
  φορές των yaw, pitch και roll, και ένα κενό τηλεμετρίας γεφυρωμένο οπτικά στον καθρεφτισμένο κόσμο.
- `tests/test_glb.py` - το συμβόλαιο GLB· οι δικές του δοκιμές του προβολέα διαβάζουν ένα επίπεδο
  αναφοράς γραμμένο από αυτόν τον εγγραφέα, οπότε η μορφή ελέγχεται και από τις δύο πλευρές.

### Έλεγχος ενός εξαχθέντος κύκλου έναντι γύρων {#checking-an-exported-course-against-laps}

Το `tests/test_course_ground.py` ελέγχει ότι μια πίστα που εξήχθη από το
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) βρίσκεται πράγματι κάτω από το
καταγεγραμμένο αυτοκίνητο - το αυτοκίνητο πρέπει να βρίσκεται ένα ύψος οδήγησης πάνω από την
επιφάνεια ακριβώς από κάτω του. Δείξτε το στο όνομα (χωρίς κατάληξη) μιας εξαγόμενης πίστας (το
`.glb` και το `.json` δίπλα του):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Μια πίστα με μεγάλα άλματα μπορεί να αποτύχει εσκεμμένα: το αυτοκίνητο είναι στον αέρα πάνω από έδαφος
που υπάρχει.

## Συμβάσεις {#conventions}

- Ο κώδικας κάτω από το `heat3d_capture/` φορτώνει τις βαριές εξαρτήσεις (OpenCV, ONNX Runtime,
  PyTorch, Qt) με καθυστέρηση, μέσα στις συναρτήσεις, ώστε η εισαγωγή μιας μονάδας, το `--help` ή οι
  εγγραφείς τηλεμετρίας να μην κοστίζουν τίποτα.
- Τα νήματα εργασίας δεν αγγίζουν ποτέ γραφικά στοιχεία Qt· τα αποτελέσματα περνούν στο νήμα της
  διεπαφής ως σήματα Qt.
- Οι εγγραφές, τα αρχεία γύρων, τα πλέγματα, τα βάρη μοντέλων και το βίντεο μένουν έξω από το git
  από το `.gitignore`, κατά φάκελο και κατά τύπο αρχείου.
- Υποβολές και εκδόσεις: η έκδοση είναι το αρχείο `VERSION`· οι εκδόσεις είναι GitHub releases του
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), τα οποία διαβάζει ο
  ενημερωτής ([Ενημερώσεις](updates.md)).
