---
title: "Référence des commandes"
nav_order: 5
lang: "fr"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Référence des commandes {#command-reference}

Toutes les commandes s'exécutent depuis le dossier du dépôt, avec l'environnement du projet :

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Commande | Rôle |
|---|---|
| [`route`](#route) | Enregistre uniquement les positions d'un tour Forza, pour trouver la carte dans les fichiers du jeu |
| [`telemetry`](#telemetry) | Enregistre toutes les voies, un fichier par tour, pour l'onglet Analyse de course |
| [`laps`](#laps) | Lit une bibliothèque de tours FH Companion et écrit le tracé et les échantillons d'un seul circuit |
| [`reconstruct`](#reconstruct) | Résout un enregistrement hors ligne et écrit un `.glb` |
| [`hud`](#hud) | Lit les actions du joueur, ses morts, la piste de la mini-carte et le fil des éliminations dans un enregistrement |
| [`locate`](#locate) | Où a été pris chaque image d'un enregistrement, par rapport aux rendus du niveau |
| [`python -m heat3d_capture.ui`](#the-scan-window) | La fenêtre de scan |
| [`python -m heat3d_update`](#updates) | Vérifie et installe une mise à jour |
| [`python tools/export_onnx.py`](#the-model-converter) | Convertit le modèle de profondeur en ONNX |

Lancé avec `python -m heat3d_capture`, l'outil vérifie d'abord si une version plus récente existe (voir
[Mises à jour](updates.md) ; `HEAT3D_NO_UPDATE=1` désactive cette vérification). `--help` après
n'importe quelle commande affiche ses options :

![heat3d_capture --help](../assets/img/cli-help.svg)

Code : [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Écoute les données envoyées par Forza Data Out et ne garde que les positions de la voiture, rien d'autre : pas de modèle de profondeur, pas de GPU, pas de capture. Code : [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Option | Défaut | Signification |
|---|---|---|
| `-o`, `--out` | obligatoire | Chemin de sortie ; son suffixe est remplacé, donc `-o lap` écrit `lap.npz` et `lap.json`. |
| `--port` | `5300` | Port vers lequel le jeu envoie (écoute sur 127.0.0.1). |
| `--seconds` | `0` | Arrête après ce nombre de secondes ; `0` tourne jusqu'à Ctrl+C. |

Une position n'est gardée que lorsque le jeu signale une course (`isRaceOn`), que la voiture roule à plus de
0,5 m/s, et qu'elle est à au moins 0,5 m de la dernière position gardée. Sinon, rester dans un menu à
60 paquets par seconde remplirait le fichier avec la ligne de départ. L'heure de chaque échantillon est
l'heure de course du jeu, ou l'heure de l'horloge quand celle-ci vaut 0. La disposition est détectée comme pour
`telemetry` (la voiture doit d'abord bouger ; voir [Forza](telemetry-forza.md)).

Une fois par seconde, il affiche les paquets reçus, les positions gardées et la position actuelle, ou
`nothing on port 5300 yet - is Data Out on?`. Le tracé est **sauvegardé pendant la conduite** : toutes les
2 secondes dès qu'une nouvelle position est arrivée (l'intervalle grandit jusqu'à vingt fois la durée de la
dernière sauvegarde, pour qu'une très longue session ne passe jamais plus d'un vingtième de son temps à écrire),
et une fois de plus quand l'enregistreur s'arrête pour une raison quelconque : Ctrl+C, `--seconds` ou une
exception. Chaque sauvegarde écrit `lap.npz.partial` / `lap.json.partial` puis les remplace par les vrais
fichiers ; les fichiers sur le disque sont donc toujours complets. Un plantage ou un processus tué ne perd que
les dernières secondes. Si rien n'a été gardé, il affiche comment activer Data Out et quitte avec le code 1.

Sortie :

- `lap.npz` - tableaux NumPy `positions` (n x 3, en mètres), `times`, `speeds` (m/s) ;
- `lap.json` - lisible sans ce projet :

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Les positions sont les coordonnées mondiales du jeu, ce qui permet de retrouver le même sol dans les fichiers du
jeu : la commande `course` de [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) lit ce JSON et
exporte le circuit parcouru par le tour.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Chaque option et chaque jeu est décrit sur [Enregistreurs de télémétrie](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Lit la bibliothèque de tours que FH Companion conserve et écrit deux fichiers pour un circuit : un tracé qui
indique quel morceau de carte découper dans l'archive du jeu, et un tableau de chaque échantillon de chaque
tour. Ils sont écrits ensemble pour ne jamais se désynchroniser. Code :
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Option | Défaut | Signification |
|---|---|---|
| `course` | aucun | Nom du circuit, reconnu sans exigence de casse ni de forme exacte. Omettre pour lister la bibliothèque. |
| `-o`, `--out` | le nom du circuit, en minuscules, espaces remplacés par `_` | Chemin de sortie ; `.json` et `.csv` sont écrits côte à côte. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Où se trouvent les dossiers des circuits. |
| `--margin` | `80` | Mètres ajoutés autour de l'étendue du circuit en x et z, dans les `bounds` du tracé. |

### Liste {#listing}

Sans circuit, la commande affiche le nombre de dossiers de circuits et, pour chacun, le nombre de fichiers de
tours (`*.json` à n'importe quelle profondeur, sauf `course.json`) et le nom du circuit, puis
`Name one to write it out:  -o <file> <course>`.

### Trouver un circuit {#finding-a-course}

Les dossiers de circuits se nomment `<nom> (course_<x>_<z>_to_<x>_<z>)` : le départ et l'arrivée, arrondis.
Un circuit est trouvé ainsi, dans l'ordre : le nom exact du dossier ; la partie nom du dossier, sans tenir
compte de la casse ; un dossier unique dont le nom contient le texte. Plusieurs correspondances constituent
une erreur, qui les liste.

### Lecture {#reading-it}

- `course.json` dans le dossier, s'il est lisible, donne le nom et le départ et l'arrivée non arrondis
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`) ; sinon ils viennent du nom du dossier. Un circuit est
  considéré comme une boucle lorsque le départ et l'arrivée sont à moins de 10 m l'un de l'autre.
- Chaque autre `*.json` sous le dossier est un tour (les tours se trouvent plusieurs dossiers plus bas -
  par classe, voiture, réglage, étiquette - et la recherche est simplement récursive). Les fichiers sont lus
  en UTF-8 avec une marque d'ordre des octets. Un tour illisible est ignoré. Les tours sont triés par leur
  heure d'enregistrement.
- Pour chaque tour : `Lap.samples` (chacun avec `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), ainsi que la classe de la
  voiture, son numéro d'ordre, l'indice de performance, la durée du tour, sa longueur, l'heure
  d'enregistrement et le départ arrêté.

Elle affiche un résumé (tours, échantillons, meilleur tour et sa classe, l'étendue en x/y/z).

### Sortie {#output}

**`<out>.json`** - la même forme de tracé que celle écrite par `route`, pour que l'extracteur de carte accepte
l'un ou l'autre : `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (agrandi de `--margin` en x et
z), et `positions` du tour **le plus rapide** (une seule ligne au lieu d'un nuage de tous les tours).

**`<out>.csv`** - chaque échantillon de chaque tour, une ligne chacun :

| Colonne | Signification |
|---|---|
| `course` | nom du circuit |
| `lap` | un libellé par tour : date et heure d'enregistrement à la minute près, et le temps du tour |
| `car` | numéro d'ordre de la voiture |
| `car_class` | lettre de la classe de performance |
| `pi` | indice de performance |
| `lap_seconds` | le temps du tour |
| `speed_kmh` | vitesse en km/h |
| `x`, `y`, `z` | position dans le monde, en mètres, 3 décimales |
| `speed_ms` | vitesse, en m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | tels que FH Companion les enregistre |
| `metres` | distance parcourue le long du tour, 3 décimales |
| `elapsed` | secondes depuis le départ propre au tour, 3 décimales |

Les valeurs qui ne sont pas des positions sont écrites avec 4 chiffres significatifs ; les positions ont un
nombre fixe de décimales, car 4 chiffres significatifs colleraient un circuit à une grille d'un mètre. Les
noms de colonnes sont choisis pour que le visualiseur lise le fichier sans qu'on le lui dise : `lap` devient la
session (deux tours d'une même voiture ne sont jamais réunis), `car` l'objet qui se déplace, `car_class` le
groupe à colorer, `elapsed` l'axe du temps (chaque tour s'aligne sur son propre départ).

Enfin, elle affiche une indication pour découper la carte dans le jeu avec GameFiles, avec le fichier de tracé
ou une boîte explicite.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Reconstruit un enregistrement hors ligne, avec la trajectoire de la caméra résolue d'un seul coup par VGGT.
Lent : plusieurs minutes par fenêtre sur une carte graphique de bureau. Il faut PyTorch, Hugging Face
`transformers` et le paquet `vggt`, dont le scanner n'a pas besoin : ils sont listés dans
`requirements-offline.txt`, et la commande les vérifie après avoir affiché la ligne de licence, puis propose
d'installer ce qui manque (code de sortie 1 si on refuse). Description complète :
[Reconstruction hors ligne](reconstruction-offline.md).

| Option | Défaut | Signification |
|---|---|---|
| `video` | obligatoire | L'enregistrement. Code de sortie 2 s'il n'existe pas. |
| `-o`, `--out` | obligatoire | Le `.glb` à écrire. |
| `--solve-budget` | `260` | Nombre maximal d'images confiées au solveur. Elles sont espacées selon le mouvement de l'image, pas selon l'horloge. Plus il y en a, plus c'est précis et beaucoup plus lent. Plus de 400 images prévues sont refusées. |
| `--fuse-interval` | `0.4` | Secondes entre les images fusionnées dans la géométrie. |
| `--model` | `vggt-1b` | Les poids VGGT avec lesquels résoudre : `vggt-1b` (`facebook/VGGT-1B`, non commercial) ou `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, accès restreint ; il faut un accès accordé par Meta). La ligne de licence affichée en premier est celle de ce modèle. |

Elle affiche d'abord la ligne de licence du modèle, puis chaque étape (`masking`, `planning`, `solving`,
`fusing`, `exporting`) avec le temps écoulé et la progression, et enfin un résumé : caméras résolues, erreur de
fermeture, pire raccord, remarques et fichier écrit. Le code de sortie vaut 0 seulement si un fichier a été écrit.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Lit le HUD du jeu dans l'enregistrement du joueur, après la partie : les actions du joueur lui-même, d'après la
fenêtre de points, ses morts et réanimations, d'après les écrans de chute et de déploiement, la piste de la
mini-carte et le fil des éliminations. Il écrit `<out>.parquet` (piste et événements, une table 3DHeat),
`<out>.events.jsonl`, `<out>.summary.json`, et `<out>.map.png` + `.map.json` (la mosaïque de la mini-carte et ses
ancres, pour l'option Image de carte du visualiseur). Battlefield 6 (`bf6`) est pour l'instant le seul profil.

Il faut **ffmpeg et ffprobe** dans le PATH (`winget install Gyan.FFmpeg`, puis un nouveau terminal).

| Option | Défaut | Signification |
|---|---|---|
| `video` | obligatoire | L'enregistrement. |
| `-o`, `--out` | le nom de la vidéo | Chemin de sortie sans extension. |
| `--game` | `bf6` | Le HUD de quel jeu lire. |
| `--player` | deviné | Le nom du joueur tel que le fil des éliminations l'affiche, reconnu sans exigence stricte. |
| `--fps` | `5` | Échantillons de mini-carte par seconde. |
| `--start`, `--seconds` | toute la vidéo | La partie de l'enregistrement à lire. |
| `--metres-per-pixel` | aucun | L'échelle de la mini-carte, si elle est connue ; sans elle, les positions sont en pixels de mini-carte. |
| `--cpu` | désactivé | Décoder sur le processeur même quand une carte NVIDIA est présente. |

Documentation complète : [Lire le HUD depuis un enregistrement](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` dessine un niveau depuis chaque endroit où un joueur peut se tenir, et indexe les rendus ; `frames` place
chaque image échantillonnée d'un enregistrement dans ce niveau, d'après l'image, avec la piste de la mini-carte de la
commande `hud` comme solution de secours ; `eval` compare un résultat à des poses de caméra connues ; `train` entraîne
un modèle de lieux propre à une carte, sur les rendus du niveau (et sur les images qu'une exécution a déjà localisées),
pour `build --head` ; `refmap` place la carte du jeu elle-même (son écran de déploiement) sur le niveau, et `minimap`
lit la mini-carte d'un enregistrement par rapport à elle, image par image - l'a priori que `frames --minimap` peut
prendre. Il faut PyTorch et `requirements-locate.txt`. **Expérimental :** sur de vrais enregistrements, il ne place pour
l'instant qu'une faible part des images. Chaque option, les sorties et la méthode :
[Localiser des images dans un niveau](locate.md) ; la liste complète des options : [Référence des commandes](../cli-reference.md).

## La fenêtre de scan {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ou double-cliquez sur `scan.bat`. Aucune option. Voir [La fenêtre de scan](reconstruction-scan-ui.md).

## Mises à jour {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Voir [Mises à jour](updates.md).

## Convertisseur du modèle {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Convertit un point de contrôle Depth Anything V2 vers le fichier ONNX que le scanner exécute. Il faut PyTorch,
`transformers` et `onnxscript`. Voir [Profondeur](reconstruction-depth.md#building-the-model).
