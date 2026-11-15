---
title: Développement
nav_order: 11
lang: fr
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Développement {#development}

## Structure du dépôt {#repository-layout}

| Chemin | Contenu |
|---|---|
| `heat3d_capture/__main__.py` | la ligne de commande : `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (disposition Data Out), `fulllap.py` (fichiers de tour Forza, relais), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (le document de tour commun) |
| `heat3d_capture/capture/` | `sources.py` (capture en direct, vidéo), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (ce que lance le scanner), `estimator.py` (voie PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (l'écrivain), `reference.py` (niveau de référence synthétique) |
| `heat3d_capture/scan/` | `session.py` (un scan), `reconstruct.py` (images clés transformées en géométrie), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud` : le HUD d'un enregistrement - fenêtre des points, écrans de mort, mini-carte du tracé, fil des éliminations (`profiles.py` par jeu) |
| `heat3d_capture/locate/` | `locate` : les rendus du niveau, la base de données, la mise en correspondance, le modèle par carte, la mini-carte |
| `heat3d_capture/ui/` | `__main__.py` (point d'entrée et vérification des dépendances), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | la vérification des versions et la mise à jour |
| `mods/beamng/heat3d/` | le mod de protocole BeamNG |
| `mods/trackmania/Heat3dRecorder/` | le plugin Openplanet |
| `tools/export_onnx.py` | le convertisseur du modèle de profondeur |
| `tools/gen_docs_reference.py` | écrit `docs/cli-reference.md` à partir de `--help` ; `--check` indique si le fichier est périmé |
| `tools/docs_diagrams.py` | dessine les schémas de `docs/assets/img/` (par langue avec `--lang`) |
| `tools/sync_wiki.py` | régénère `docs/wiki/` à partir de `docs/` |
| `models/` | fichiers `.onnx` convertis (non versionnés) |
| `tests/` | la suite de tests ; `scene.py` et `track_scene.py` rendent des scènes synthétiques à géométrie connue |
| `docs/` | cette documentation ; `docs/wiki/` est généré à partir d'elle |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

La logique de scan ne contient pas de Qt : `ScanSession` et `Reconstructor` acceptent de simples
fonctions et peuvent être pilotés depuis un script ou un test. Exemple :

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

## L'environnement {#the-environment}

Le projet utilise un environnement virtuel dans `.venv` (créé par `scan.bat` ou à la main). Les
tests qui touchent à l'interface ont besoin de **PySide6** dans cet environnement ; `requirements.txt`
l'installe sous le nom `PySide6-Essentials` :

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Pour le convertisseur de modèle, les tests de profondeur PyTorch et la voie hors ligne, installez
PyTorch (adapté à la carte graphique) **avant** `requirements.txt` ; puis `requirements-offline.txt` et
sa ligne `vggt` pour le solveur hors ligne, et `onnxscript` pour le convertisseur. Voir
[Exécution et dépendances](runtime.md#installing-by-hand).

## Lancer les tests {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` définit `testpaths = tests` et masque les `UserWarning` venant de `huggingface_hub`. La
suite compte plusieurs centaines de vérifications ; la plupart n'ont besoin ni de jeu, ni de carte
graphique, ni de matériel de capture.

Ce qui s'ignore tout seul, et pourquoi :

| Tests | Ignorés quand |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, les tests de pilotage de fenêtre dans `test_ui_drives_a_scan.py` | aucun `models/depth-*.onnx` - lancez d'abord `tools/export_onnx.py` |
| les tests de l'estimateur GPU dans `test_depth.py` | PyTorch n'est pas installé, ou il n'y a pas de périphérique CUDA ; les tests `fit_scale` et `AffineFit` s'exécutent dans tous les cas |
| certains cas de `test_offline.py` et `test_solveprep.py` | OpenCV n'a pas d'encodeur vidéo pour écrire le clip synthétique |
| `test_hotkeys.py` | les tests d'enregistrement exigent Windows ; le test de repli s'exécute ailleurs |
| `test_course_ground.py` | `HEAT3D_COURSE` n'est pas défini |
| quelques tests de fusion | un cas synthétique n'a rien fusionné |

### Le test de lancement {#the-launch-test}

`tests/test_launch.py` lance le vrai point d'entrée, `python -m heat3d_capture.ui`, comme sous-processus
(avec `QT_QPA_PLATFORM=offscreen`) et vérifie qu'il atteint la boucle d'événements et qu'il reste en
marche. Il existe parce que la première version plantait à chaque lancement alors que tous les autres
tests réussissaient : ils créent tous eux-mêmes une `QApplication` puis construisent la fenêtre, ce
qui saute la seule séquence qu'un utilisateur exécute - la vérification des dépendances qui crée
d'abord une application. Un test de composant qui construit son propre environnement ne peut pas voir
une faute dans la façon dont l'environnement est construit.

### Vérité de référence {#ground-truth}

- `tests/test_accuracy.py` - une pièce synthétique d'un parcours connu avec une profondeur analytique ;
  voir [Reconstruction de niveau](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - largeur de route, extraction de l'échelle de piste, la grille de
  couverture lue pendant son écriture, et la raison pour laquelle la fermeture de boucle reste désactivée.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - les dispositions de télémétrie, sur des paquets
  et des pages construits à partir des structures documentées, et les fichiers de tour qu'elles
  écrivent (noms de canaux canoniques, `meta`, aucun `NaN` dans le JSON). `tests/test_trackmania_plugin.py`
  lit le code source du plugin Openplanet pour savoir ce qu'il écrit dans la description de chaque
  course.
- `tests/test_route_record.py` - le fichier `route` est sur le disque, complet, avant l'arrêt de
  l'enregistreur.
- `tests/test_telemetry_pose.py` - poses Forza dans les propres coordonnées du jeu, le sens du lacet,
  du tangage et du roulis, et un trou de télémétrie comblé visuellement dans le monde miroir.
- `tests/test_glb.py` - le contrat GLB ; les tests de la visionneuse analysent un niveau de référence
  écrit par cet écrivain, si bien que le format est testé des deux côtés.

### Vérifier un parcours exporté par rapport aux tours {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` vérifie qu'un parcours exporté par
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) se trouve bien sous la voiture
enregistrée - la voiture doit être à une hauteur de suspension au-dessus de la surface située juste
en dessous d'elle. Indiquez-lui la racine d'un parcours exporté (le `.glb` et le `.json` qui
l'accompagne) :

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Un parcours avec de gros sauts peut échouer par conception : la voiture est dans les airs au-dessus
d'un sol qui existe bel et bien.

## Conventions {#conventions}

- Le code sous `heat3d_capture/` importe les grosses dépendances (OpenCV, ONNX Runtime, PyTorch, Qt)
  de façon paresseuse, à l'intérieur des fonctions : importer un module, lancer `--help` ou lancer les
  enregistreurs de télémétrie ne coûte donc rien.
- Les threads de travail ne touchent jamais aux widgets Qt ; les résultats passent au thread de
  l'interface par des signaux Qt.
- Les enregistrements, fichiers de tour, maillages, poids de modèles et vidéos sont tenus hors de git
  par `.gitignore`, par dossier et par type de fichier.
- Commits et versions : la version est donnée par le fichier `VERSION` ; les versions sont des
  publications GitHub de [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture),
  que lit la mise à jour ([Mises à jour](updates.md)).
