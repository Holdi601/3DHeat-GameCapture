---
title: "Profondeur"
nav_order: 3
lang: "fr"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Profondeur {#depth}

La seule chose qu'une capture externe ne peut pas donner est la géométrie. Le jeu connaît la profondeur
de chaque pixel, et elle se trouve dans un tampon que ce projet ne touche délibérément pas ; la
profondeur est donc **déduite de l'image**. C'est la limite de précision de toute l'approche.

Code : [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(ce que lance le scanner),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(le chemin PyTorch et l'ajustement d'échelle),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Le modèle {#the-model}

**Depth Anything V2**, variante relative. Il prédit une *inverse de profondeur relative* : un champ de
type disparité, juste à une transformation affine inconnue près,
`metric_disparity = a * predicted + b`, différente pour chaque image. Le réseau est bon pour ce qui est
difficile à partir d'une seule image (forme relative, bords, structure fine) et muet sur ce qu'il ne peut
pas savoir (l'échelle). L'échelle vient d'ailleurs - voir [Pose et échelle de la caméra](reconstruction-pose.md).

| Taille | Identifiant Hugging Face | Licence |
|---|---|---|
| **Small** (par défaut) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - usage commercial permis |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - non commercial uniquement |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - non commercial uniquement |

Une reconstruction hérite de la licence du modèle qui l'a faite. Small est le choix par défaut partout,
précisément pour qu'un scan ne porte aucune restriction, sauf si quelqu'un choisit autre chose. Les
variantes métriques (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) sont citées dans
le code mais ne sont pas utilisées par le scanner. Voir [Modèles et licences](models-and-licences.md).

## Construire le modèle {#building-the-model}

Le scanner exécute un fichier ONNX et n'importe jamais PyTorch. Le fichier doit être fabriqué une seule
fois :

- **Depuis la fenêtre** : « Set up the depth model » (voir [La fenêtre de scan](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  qui lance la commande ci-dessous avec `--size small`.
- **À la main**, dans un environnement avec PyTorch, `transformers` et `onnxscript` :

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Option | Par défaut | Signification |
|---|---|---|
| `--size` | `small` | `small`, `base` ou `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | fichier de sortie |
| `--side` | `518` | taille carrée de l'entrée ; doit être un multiple de 14 (la taille de patch du ViT) ; 518 = 14 x 37 est la résolution d'entraînement |
| `--opset` | `17` | version d'opset ONNX ; 17 est largement pris en charge par DirectML et CUDA |

Ce que fait le convertisseur :

- Télécharge le point de contrôle depuis Hugging Face (`AutoModelForDepthEstimation`).
- L'enveloppe pour que la **normalisation ImageNet soit dans le graphe** : le modèle reçoit du RGB dans la
  plage 0-255 en flottant (`pixels`, de forme `batch x 3 x side x side`) et produit `inverse_depth`. Il
  n'existe qu'un seul exemplaire de la moyenne et de l'écart type, donc ils ne peuvent pas diverger du
  point de contrôle.
- **Taille spatiale fixe**, batch dynamique. DirectML et TensorRT compilent par forme ; une hauteur et une
  largeur dynamiques recompileraient à la première image de chaque nouvelle résolution, un arrêt visible
  pendant une capture en direct.
- Exporte par le **chemin TorchScript** (`dynamo=False`) : le graphe dynamo échouait sur DirectML à un
  nœud Reshape, et il écrit les poids dans un fichier `.onnx.data` séparé. Le chemin TorchScript produit un
  fichier unique et autonome.
- Affiche le fichier et sa taille. Les avertissements du traceur sur les formes figées sont attendus.

Le scanner cherche `models/depth-*.onnx` et choisit selon la licence, pas selon le nom de fichier : le
modèle Small dès qu'il est là, une taille plus grande seulement s'il est le seul. La ligne de la fenêtre
d'analyse nomme le fichier, sa licence et tout autre modèle laissé de côté.

## Exécution : ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` crée une seule session ONNX Runtime, de façon paresseuse, avec l'optimisation complète
du graphe, sur le backend choisi par l'échelle, avec le CPU ajouté en secours : si un fournisseur échoue à
la création de session (un vieux pilote), le scan sera lent au lieu de planter. Voir
[Exécution et dépendances](runtime.md#inference-backends).

- `warm_up()` crée la session et exécute une image vide (la première inférence sur un graphe neuf est
  plusieurs fois plus lente que le régime établi).
- `measure_throughput(frames)` chronomètre ce nombre d'images vides après l'échauffement ; la fenêtre en
  utilise 6 et affiche le résultat en vues par seconde.

### Remplissage, pas étirement {#letterboxing-not-stretching}

Le graphe prend un carré fixe ; le jeu est en 16:9. Écraser une image dans un carré changerait la forme
apparente de tout, et comme la sortie est une estimation géométrique, elle serait fusionnée comme une vraie
géométrie fausse. Chaque image est donc traitée ainsi :

1. mise à l'échelle pour tenir dans le carré, en conservant son rapport d'aspect (interpolation par zones
   pour réduire, cubique pour agrandir) ;
2. complétée par du **gris moyen (114)** - le noir ou le blanc se lisent comme un bord marqué et font
   déborder une fausse discontinuité de profondeur sur le contenu voisin ;
3. passée dans le modèle ;
4. le remplissage est rogné de la prédiction **avant** le redimensionnement retour (cubique) à la
   résolution de l'image, pour que la marge ne déborde jamais sur de vrais pixels.

Le résultat est un `DepthMap` avec `metric=False` à la taille de l'image source.

## Le chemin PyTorch {#the-pytorch-path}

`DepthEstimator` exécute directement le modèle Hugging Face (fp16 sur CUDA, fp32 sur CPU), par lots selon la
taille de l'image, chaque prédiction étant redimensionnée en bicubique. Le scanner ne l'utilise pas ; la
commande hors ligne `reconstruct` l'utilise (voir [Reconstruction hors ligne](reconstruction-offline.md)),
ce qui est l'une des raisons pour lesquelles cette commande a besoin de PyTorch et de `transformers`.

## De relatif à métrique : `fit_scale` et `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Pour passer de l'inverse de profondeur prédite à des mètres, il faut l'affine `scale * predicted + shift`.
Lorsque des ancres de profondeur connue sont disponibles (des points caractéristiques triangulés entre des
poses connues, ou la profondeur ancrée de l'image précédente), `fit_scale` la résout :

- moindres carrés **en disparité**, pas en profondeur - l'erreur du réseau est à peu près uniforme en
  disparité, alors qu'en profondeur quelques ancres lointaines (où un pixel de disparité vaut des dizaines
  de mètres) domineraient ;
- **repondérée itérativement** (12 itérations, poids de type Cauchy `1 / (1 + (r / 3 MAD)^2)`), car les
  ancres portent des valeurs aberrantes grossières (un appariement sur une voiture en mouvement, un
  incident de suivi), et une seule de ces ancres dans un ajustement simple tirerait toute l'image ;
- il faut au moins 2 ancres utilisables ; il rapporte l'erreur résiduelle absolue médiane et le nombre
  d'inliers (résidu inférieur à 3 x la médiane).

`AffineFit.apply` renvoie une profondeur en mètres, avec **+inf** pour le ciel. Il vérifie la valeur prédite
aussi bien que la valeur ancrée : un pixel de ciel qui prédit zéro sort à `shift` - petit, positif, fini - et
ferait sinon atterrir tous les pixels de ciel sur une coquille fantôme à une seule distance. Tout ce qui est
prédit à `1e-4` ou moins est du ciel, quoi que dise l'ajustement.

La fusion ne garde ensuite que les profondeurs entre 0,35 m et 60 m (voir
[Fusion](reconstruction-fusion-and-texture.md#from-depth-to-points)).
