---
title: Reconstruction de niveau
nav_order: 6
lang: "fr"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Reconstruction de niveau à partir du gameplay {#level-reconstruction-from-gameplay}

Parcourez un niveau lentement, ou conduisez sur une piste, et le scanner transforme ce que l'écran a
montré en un `.glb` que la visionneuse 3DHeat charge comme contexte sous la télémétrie - le même contrat
de fichier que celui qu'écrit l'exportateur Unreal. Il sert au cas où personne n'a exporté la carte et
où les fichiers du jeu ne peuvent pas être lus ; un export du moteur ou un export des fichiers de jeu
est exact, celui-ci est une estimation.

## Le pipeline {#the-pipeline}

```text
 images              images clés          profondeur           pose                 fusion              sortie
 ------              -----------          ----------           ----                 ------              ------
 Windows Graphics -> seuil de changement -> Depth Anything V2 -> odométrie visuelle -> volume            -> marching cubes
 Capture, ou un       d'image (adaptatif)   (ONNX Runtime,       (ORB + PnP), ou      d'occupation        -> sol/structure
 fichier vidéo                             letterboxé)          télémétrie Forza,    + grille de         -> couleur des sommets
                                                                or une solution      couverture (carte   -> .glb
                                                                VGGT                 en direct, zones    
                                                                                     faibles)            
                     masques HUD / cockpit, conseils sur la qualité d'image, échelle par plan de sol
```

| Étape | Scan en direct (`heat3d_capture.ui`) | Hors ligne (`reconstruct`) | Page |
|---|---|---|---|
| Images | écran, fenêtre ou vidéo, redimensionnées au plus grand côté du préréglage | vidéo, échantillonnée deux fois (plan de résolution et intervalle de fusion) | [Capture](reconstruction-capture.md) |
| Images clés | conservées selon l'ampleur du changement d'image, seuil adapté à la capture | toutes les `--fuse-interval` secondes | [Capture](reconstruction-capture.md#keyframes) |
| Masques | `ScreenMask` fondé sur les changements, puis `FlowMask` fondé sur le flux après 40 images clés | `FlowMask` appris sur quatre passes de la vidéo ; non appliqué au solveur | [Capture](reconstruction-capture.md#what-is-not-the-world) |
| Profondeur | modèle ONNX sur le meilleur backend GPU | Depth Anything V2 Small en PyTorch | [Profondeur](reconstruction-depth.md) |
| Pose | odométrie visuelle, ou télémétrie Forza exacte | fenêtres VGGT recollées en une seule trajectoire, interpolée | [Pose](reconstruction-pose.md), [Hors ligne](reconstruction-offline.md) |
| Échelle | hauteur de la caméra au-dessus du sol (1,15 m) une seule fois, ou télémétrie | les unités propres de la trajectoire résolue | [Pose](reconstruction-pose.md#scale) |
| Fusion | occupation pondérée, voxels épars ; grille de couverture | la même | [Fusion](reconstruction-fusion-and-texture.md) |
| Sortie | `.glb`, parties sol/structure, couleur des sommets, centimètres | la même | [Le fichier .glb](glb-output.md) |

Code : [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - réglages et cadence d'un scan ; `reconstruct.py` - images clés transformées en
géométrie ; `offline.py` - la voie hors ligne), les étapes se trouvant dans `capture/`, `depth/`, `pose/`,
`fusion/` et `geometry/`.

## D'où vient la précision {#where-accuracy-comes-from}

La profondeur monoculaire n'est juste qu'à une échelle inconnue près - la photo d'une pièce et celle
d'une maison de poupée sont la même image. On laisse donc le réseau faire ce qu'il sait bien (forme
relative, bords, structures fines), et l'échelle ainsi que la trajectoire de la caméra viennent d'une
source qui les connaît :

| Jeu | Trajectoire de la caméra | Échelle |
|---|---|---|
| Forza Horizon / Motorsport avec la télémétrie activée | exacte, issue de Data Out, interpolée au moment de capture de chaque image | exacte : la profondeur est ancrée par la triangulation de points entre deux poses connues |
| Tout autre jeu, en direct | odométrie visuelle, enchaînée image après image | fixée une fois à partir d'une hauteur de caméra supposée au-dessus du sol |
| Un enregistrement, hors ligne | VGGT, résolu sur des fenêtres qui se recouvrent | les unités de la résolution (pas métriques) |

Le seul nombre que le scanner reçoit au lieu de le mesurer est le **champ de vision horizontal** du
jeu (90 degrés par défaut dans la fenêtre ; les jeux de course sont plutôt autour de 65). S'il est trop
étroit, le niveau se reconstruit plus profond qu'il ne l'est ; trop large, il s'aplatit.

## Prévenir l'utilisateur tôt {#telling-the-user-early}

Un scan est un acte physique - quelqu'un parcourt un niveau pendant plusieurs minutes - et l'échec
coûteux est de finir la marche pour découvrir qu'elle ne valait rien. La fenêtre mesure donc le débit
de profondeur de cette machine avant que quoi que ce soit ne puisse démarrer, et annonce à quoi
ressemblera le scan ([Exécution](runtime.md#what-to-expect-from-this-machine)) ; pendant le scan, elle
affiche une carte de couverture avec des zones faibles numérotées, la santé du suivi, une barre de
vitesse de marche, une barre de netteté, et une seule consigne à la fois, dans la fenêtre et dans une
superposition cliquable au-dessus du jeu ([La fenêtre de scan](reconstruction-scan-ui.md)).

## Mesuré sur une vérité de référence synthétique {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` rend une pièce de 12 x 8 m (4 m de haut) à partir d'une trajectoire de caméra
connue, avec une profondeur analytique (et non celle du réseau), puis la reconstruit avec des voxels de
0,2 m. Il vérifie que plus de 90 % des images sont placées, que l'erreur moyenne de trajectoire est
inférieure à 0,35 m (la pire inférieure à 1 m), que la distance parcourue est à 10 % près de la réalité,
que la pièce sort à la bonne largeur à 1,5 m près, que plus de 75 % de la surface des murs se trouve à
moins de 0,45 m d'un vrai mur, qu'une marche de type relevé obtient une couverture nettement meilleure
qu'une marche droit devant soi, et qu'une scène sans aspérités est refusée plutôt qu'inventée.
La profondeur analytique isole la pose, l'échelle et la fusion du réseau ; la façon dont le réseau se
comporte sur du gameplay réel est une question à part qu'aucune scène synthétique ne répond.
`tests/test_track_width.py` vérifie qu'un tour conduit hors centre sur une route de largeur connue
reconstruit la largeur de la route, et pas seulement la ligne conduite.

## Pages {#pages}

- [La fenêtre de scan](reconstruction-scan-ui.md) - chaque commande, raccourci et élément de superposition
- [Capture, masques et qualité d'image](reconstruction-capture.md)
- [Profondeur](reconstruction-depth.md)
- [Pose de la caméra et échelle](reconstruction-pose.md)
- [Fusion, couverture et couleur](reconstruction-fusion-and-texture.md)
- [Le fichier .glb](glb-output.md)
- [Reconstruction hors ligne](reconstruction-offline.md)
