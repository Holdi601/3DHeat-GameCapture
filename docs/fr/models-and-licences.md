---
title: Modèles et licences
nav_order: 7
lang: fr
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modèles et licences {#models-and-licences}

Tout ce qui est écrit pour ce dépôt est sous **licence MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Ce que la MIT ne peut
pas couvrir, ce sont les éléments avec lesquels les outils fonctionnent : les paquets qu'ils importent,
les modèles qu'utilise la reconstruction, et les jeux qu'ils lisent. Le relevé complet, avec les
sources, se trouve dans
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md) ; ses licences
ont été relevées sur les métadonnées des paquets et les fiches des modèles en septembre 2026. Si les
conditions d'un composant ont changé depuis, c'est la source qui fait foi, pas cette page. Rien ici ne
constitue un avis juridique.

## Le modèle de profondeur - celui qui décide de l'usage commercial {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 n'est **pas sous la même licence selon sa taille**, et une reconstruction hérite de
la licence du modèle qui l'a produite :

| Modèle | Licence | Usage commercial | Utilisé par |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **autorisé** | le modèle par défaut : le modèle converti du scanner (`tools/export_onnx.py` le prend par défaut, et le bouton « Set up the depth model » de la fenêtre le construit toujours), et la profondeur de la voie hors ligne (fusion) ; VGGT en fournit les poses |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | non commercial uniquement | seulement si vous le convertissez vous-même (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | non commercial uniquement | seulement si vous le convertissez vous-même (`--size large`) |

Base et Large donnent une meilleure profondeur. Les convertir est permis ; cela rend ce fichier de
modèle, et toute reconstruction faite avec lui, non commerciaux. C'est une décision de celui qui
l'exécute, pas une valeur par défaut à reprendre. Le scanner choisit parmi les fichiers
`models/depth-*.onnx` **selon la licence, et non selon le nom** : `depth-small-*` dès qu'il y en a un,
puis Base, puis Large (`choose_model` dans
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
La fenêtre indique le fichier retenu, sa licence, et les autres fichiers de modèle trouvés qu'elle n'a
pas utilisés ; pour scanner avec Base, sortez le fichier Small de `models/`.

## VGGT - reconstruction hors ligne uniquement {#vggt---offline-reconstruction-only}

| Modèle | Licence | Disponibilité |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - non commercial uniquement** ; les reconstructions faites avec lui en héritent | public ; le défaut |
| `facebook/VGGT-1B-Commercial` | licence distincte ; vérifiez les conditions qui vous ont été accordées | réservé : l'accès se demande à Meta et est accordé par compte ; sans lui le téléchargement échoue. Choisi avec `reconstruct --model vggt-1b-commercial` |

VGGT n'est utilisé que par `python -m heat3d_capture reconstruct` ; le scanner en direct ne le charge
jamais. La commande affiche la ligne de licence avant de démarrer. La reconstruction à partir de vidéo
est la partie de ce projet qu'un joueur lancerait, et des conditions non commerciales lui conviennent ;
pour un travail commercial, un export du moteur ou l'exportateur de fichiers de jeu est la voie à
suivre, et les deux sont de toute façon exacts.

## Localiser les images - `locate` {#locating-frames---locate}

| Modèle | Licence | Rôle |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | trouve les rendus qui montrent le même endroit |
| ALIKED `aliked-n16` | BSD-3-Clause | points-clés et descripteurs |
| LightGlue (variante ALIKED) | Apache-2.0 | les met en correspondance |

Ces trois modèles autorisent l'usage commercial et sont téléchargés à la première utilisation.
SuperPoint, le partenaire habituel de LightGlue, n'est pas utilisé : ses poids sont non commerciaux.
Voir [Localiser les images dans un niveau](locate.md).

## Paquets Python {#python-packages}

| Paquet | Licence | Rôle |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | calcul, lissage, marching cubes |
| opencv-python | Apache-2.0 | vidéo, caractéristiques, flux optique |
| onnxruntime, onnxruntime-directml | MIT | inférence de profondeur |
| windows-capture | MIT | capture en direct par Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | la fenêtre |
| pytest | MIT | développement uniquement |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | conversion de modèle ponctuelle ; la voie hors ligne |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | la voie hors ligne (`requirements-offline.txt`) |
| vggt | « VGGT License » de Meta (accord sur les matériaux de recherche avec une politique d'usage acceptable) | la voie hors ligne ; installé depuis GitHub avec `--no-deps` |
| moderngl, glcontext | MIT | `locate` : rendu du niveau hors écran (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate` : points-clés et mise en correspondance |

**PySide6 a des conditions.** La LGPL-3.0 permet l'usage propriétaire et commercial à condition que Qt
reste une bibliothèque *remplaçable*. Ici, il est utilisé comme un import ordinaire, lié dynamiquement,
ce qui satisfait cette condition, et son avis de licence doit accompagner toute distribution. Regrouper
l'outil dans un seul exécutable obligerait à garder Qt remplaçable.

La licence du paquet `vggt` lui-même a été relevée sur son `LICENSE.txt` et figure dans `LICENSES.md` ;
elle couvre le code, séparément des poids, qui sont en CC-BY-NC-4.0.

## Les jeux {#the-games}

La télémétrie ne vient que des interfaces que les jeux publient ; les images viennent de l'écran. Voir
[Les règles](rules.md). Ce que l'utilisateur fait pointer vers les outils reste soumis à la licence et
au CLUF de ce jeu, et cette obligation incombe à celui qui exécute l'outil.
