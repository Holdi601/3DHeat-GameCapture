---
title: "Exécution et dépendances"
nav_order: 8
lang: fr
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Exécution, dépendances et performances {#runtime-dependencies-and-performance}

Code : [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Double-cliquez dessus. Il ne fait que deux choses lui-même :

1. **Trouve Python** (`python`, puis `py`). S'il n'existe pas, il demande
   `Install it now with winget [Y,N]?` (« L'installer maintenant avec winget [O,N] ? ») ; si vous répondez O, il lance
   `winget install -e --id Python.Python.3.12`, puis vous demande de fermer la fenêtre et de relancer `scan.bat` pour que
   Windows prenne en compte le nouveau PATH. Si vous répondez N, rien n'est installé.
2. **Crée un environnement privé**, `.venv` à côté de `scan.bat`, s'il n'existe pas, et met à jour son pip - rien n'est donc
   installé dans le Python du système.

Il lance ensuite `.venv\Scripts\python.exe -m heat3d_capture.ui`. Tout le reste - repérer ce qui manque, expliquer à quoi cela
sert, poser des questions - se passe dans Python, sous forme de boîte de dialogue.

## Première vérification {#first-run-preflight}

Avant que la fenêtre n'importe quoi de lourd, chaque dépendance est vérifiée (avec `importlib.util.find_spec`, donc un paquet
à moitié supprimé compte comme manquant). Les règles :

- **Tout est vérifié d'abord.** La liste complète est établie avant que quoi que ce soit ne soit dit, afin que réparer un paquet
  ne mène pas directement à l'erreur suivante.
- **Demander, ne jamais supposer.** La boîte de dialogue liste chaque paquet manquant, à quoi il sert et le téléchargement total,
  et ne fait rien sans **Download and install** (Télécharger et installer). Annuler quitte : « Nothing was installed and nothing
  was changed. » (Rien n'a été installé et rien n'a été modifié.)
- **Le silence n'est pas un accord.** Sans Qt, la vérification se replie sur la console et demande `Install them now? [Y/n]`
  (Entrée, `y`, `yes`, `j`, `ja` valent oui) ; sans terminal pour répondre (fin de l'entrée), rien n'est installé.
- **Dans l'environnement propre à cet outil.** L'installation est `<python en cours> -m pip install ...` lancé comme sous-processus
  - avec `scan.bat`, le `.venv` privé. En cas d'échec, la boîte de dialogue affiche la dernière ligne de sortie de pip et la
  commande à essayer à la main.

| Paquet | Importé comme | Affiché comme ce à quoi il sert | Téléchargement approximatif |
|---|---|---|---|
| numpy | `numpy` | le calcul sur lequel tout le reste est bâti | 20 Mo |
| opencv-python | `cv2` | lecture des fichiers vidéo et des images de caméra | 40 Mo |
| onnxruntime-directml sous Windows, onnxruntime ailleurs | `onnxruntime` | exécuter le modèle de profondeur sur votre carte graphique | 120 Mo |
| PySide6-Essentials | `PySide6` | la fenêtre et ses commandes | 90 Mo |
| scipy | `scipy` | lisser la surface reconstruite | 45 Mo |
| scikit-image | `skimage` | transformer des mesures en surface 3D | 30 Mo |
| windows-capture | `windows_capture` | capturer une fenêtre de jeu en direct (optionnel : sans lui, les fichiers vidéo fonctionnent toujours) | 5 Mo |

Convertir le modèle de profondeur en exige trois de plus, demandés séparément et seulement lorsque vous appuyez sur « Set up
the depth model » (Installer le modèle de profondeur) : `torch` (environ 900 Mo), `transformers` (30 Mo), `onnxscript` (15 Mo).
Le scanner lui-même ne les importe jamais.

La commande hors ligne `reconstruct` a sa propre vérification, lancée après l'affichage de la ligne de licence, et seulement dans
le terminal : `torch` (900 Mo), `transformers` (30 Mo), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, et `vggt` depuis le
dépôt GitHub de Meta (installé avec `--no-deps`, car ses métadonnées épinglent numpy sous la version 2). La même liste figure dans
`requirements-offline.txt` ; voir [Reconstruction hors ligne](reconstruction-offline.md#requirements).

Le paquet ONNX Runtime proposé est celui que `requirements.txt` choisit pour la plateforme : `onnxruntime-directml` sous Windows,
`onnxruntime` ailleurs. Si `onnxruntime` est déjà importable (par exemple `onnxruntime-gpu`), rien n'est installé : la vérification
se fait par nom de module.

## Installer à la main {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` épingle : `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (Windows seulement), `scipy>=1.11`,
`scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` sous Windows et `onnxruntime>=1.19`
ailleurs.

`requirements-offline.txt` ajoute ce dont seul `reconstruct` a besoin : `transformers`, `einops`, `safetensors`, `huggingface_hub`
et `Pillow`, avec la ligne d'installation de `vggt` (`--no-deps`) et la note de licence VGGT dans son en-tête. PyTorch n'y figure pas
non plus, pour la raison exposée ci-dessous.

**PyTorch est volontairement absent.** La bonne roue dépend du GPU et de la version de CUDA ; en épingler une installerait une version
CPU sur les machines qui ont le plus besoin de la version GPU. Si vous le voulez (conversion du modèle, voie hors ligne `reconstruct`),
installez-le **avant** `requirements.txt` : les roues torch peuvent se fixer sur numpy 1.x, avec lequel scipy refuse de tourner, et
l'échec apparaît sous la forme `module numpy has no attribute long` depuis l'intérieur de scipy, loin de sa cause.

`onnxruntime-directml` et `onnxruntime-gpu` sont en conflit : n'en installez qu'un.

Vérifié par le développeur : Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, sur une NVIDIA RTX 5080, et le même environnement
sans paquet spécifique à NVIDIA.

## Backends d'inférence {#inference-backends}

ONNX Runtime accède aux GPU par des fournisseurs d'exécution, et ceux qui existent dépendent de la façon dont onnxruntime a été
installé, pas du matériel. La disponibilité est donc découverte, du meilleur au moins bon :

| Rang | Fournisseur | Affiché comme | Matériel |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | tout GPU Direct3D 12 : AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | n'importe lequel |

**DirectML est l'installation par défaut** parce qu'il atteint les GPU AMD et Intel aussi bien que NVIDIA. NVIDIA est plus rapide avec
ses propres fournisseurs - installer `onnxruntime-gpu` ajoute CUDA, et la fenêtre le dit lorsqu'elle voit une carte NVIDIA tourner sous
DirectML - mais NVIDIA n'a pas le droit d'être la seule option. Le CPU vient toujours en dernier, donc une machine sans GPU utilisable
obtient un scan lent plutôt qu'aucun scan, et il est ajouté comme secours lorsqu'une session GPU est créée.

Le nom de l'adaptateur est lu dans la clé de classe des adaptateurs d'affichage Windows du registre (et non depuis un outil du
constructeur comme `nvidia-smi`, qui n'existe que sur certaines machines), en sautant le Basic Render Driver. Les fournisseurs liés à
un constructeur désignent l'adaptateur correspondant ; DirectML est affiché sur le premier adaptateur énuméré, qui est celui par défaut
du système. Le nom ne sert qu'à l'affichage.

`ScanSettings.prefer_backend` (scripts seulement) peut nommer un fournisseur ou un nom court.

## Ce qu'il faut attendre de cette machine {#what-to-expect-from-this-machine}

La fenêtre mesure au démarrage le débit réel du modèle de profondeur sur cette machine (6 images après un échauffement), au lieu de
chercher le GPU dans un tableau - l'état thermique, les profils d'alimentation des portables et les versions de pilotes font trop
varier le résultat - et indique à quoi ressemblera un scan avant que quoi que ce soit ne puisse démarrer :

| Vues mesurées par seconde | Niveau | Titre | Conseil |
|---|---|---|---|
| 25 ou plus | temps réel | Scan en direct à pleine précision. | Marchez d'un pas normal ; la superposition suivra. |
| 12 à 25 | praticable | Scan en direct, avec moins de vues conservées qu'à pleine vitesse. | Marchez lentement et tournez doucement - les virages rapides laisseront des trous. Draft conserve moins de vues, ce qui aide le modèle de profondeur à suivre. |
| 2 à 12 | lent | Enregistrer d'abord, reconstruire ensuite. | Enregistrez une vidéo de la marche et reconstruisez à partir du fichier ensuite. Le résultat est identique ; seule la rétroaction n'est pas en direct. |
| moins de 2 | impraticable | Cette machine est trop lente pour scanner utilement. | Un parcours plus court, ou un modèle plus petit. **Le démarrage est désactivé.** |

Sur CPU, la note ajoute que l'installation de `onnxruntime-directml` règle généralement le problème sous Windows. Rien ne change la
résolution de capture à lui seul : cela n'aiderait pas, car le modèle de profondeur tourne à sa taille d'entrée fixe quoi qu'on lui
donne ; ce qui permet à une machine plus lente de suivre, c'est de conserver moins de vues, ce que fait Draft.

### Mesuré par le développeur {#measured-by-the-developer}

Même fichier ONNX, même sortie, RTX 5080 :

| Backend | Débit de profondeur |
|---|---|
| DirectML | 54 i/s |
| CPU | 3,5 i/s |

Un clip de test passé par le chemin ONNX livré :

| Préréglage | Vues conservées | Débit de profondeur |
|---|---|---|
| Draft | environ 1 sur 7 | environ 50 /s |
| Balanced | environ 1 sur 4 | environ 50 /s |
| Detailed | environ 1 sur 2 | environ 40 /s |

La profondeur est nettement plus rapide que la capture, donc le scan en direct n'est pas limité par la profondeur. L'environnement de
l'application fait environ 349 Mio sans PyTorch, contre environ 3,5 Go pour torch avec CUDA.

La voie hors ligne `reconstruct` est différente : quelques minutes par fenêtre de 16 images sur un GPU de bureau.

## Mémoire {#memory}

- Les images ne sont pas conservées après la fusion, sauf **160** pour colorier le maillage.
- Un scan s'arrête à **3000** vues conservées par défaut (« Views kept »), comme garde-fou.
- La file de capture en direct contient 4 images ; le tampon de poses de télémétrie 30 secondes.
- Les deux grilles de voxels sont creuses, et le maillage est extrait bloc par bloc, donc la mémoire suit ce qui a été scanné,
  et non la boîte englobante.

## Plateforme {#platform}

Le scanner et les enregistreurs Assetto Corsa ne fonctionnent en pratique que sous Windows : la capture en direct utilise Windows
Graphics Capture, les raccourcis et la superposition transparente au clic utilisent l'API Win32, et les pages Kunos sont de la mémoire
partagée Windows. Les fichiers vidéo peuvent être scannés et les enregistreurs UDP fonctionnent ailleurs, mais cela n'a pas été vérifié.
