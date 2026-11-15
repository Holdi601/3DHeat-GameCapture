---
title: "Pose et échelle de la caméra"
nav_order: 4
lang: "fr"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Pose et échelle de la caméra {#camera-pose-and-scale}

Une carte de profondeur indique à quelle distance se trouvent les choses depuis *un* point de vue. Pour en
faire un seul niveau, il faut savoir où était chaque point de vue, et dans quelles unités. Cette page couvre
les voies en direct ; la résolution hors ligne par modèle à propagation directe est décrite dans
[Reconstruction hors ligne](reconstruction-offline.md).

Code : [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Le modèle de caméra {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` construit une caméra sténopé à partir du **champ de vision horizontal**
que vous réglez dans la fenêtre : `fx = (width / 2) / tan(fov / 2)`, pixels carrés (`fy = fx`), point principal
au centre de l'image. Un jeu ne publie pas sa projection : c'est donc le seul chiffre supposé. Trop étroit, et la
scène paraît plus profonde qu'elle ne l'est. La voie hors ligne utilise 65 degrés.

Une `Pose` est stockée **monde-depuis-caméra** : `rotation` (3 x 3) et `translation` = le centre de la caméra dans
le monde, ce que veulent la trajectoire, la carte de couverture et la superposition.

## Odométrie visuelle (par défaut) {#visual-odometry-the-default}

`VisualOdometry` suit chaque image clé par rapport à la précédente :

1. **Points** : ORB, jusqu'à 1500 par image, détectés seulement sur le masque du monde (voir
   [Capture](reconstruction-capture.md#what-is-not-the-world)).
2. **Correspondances** avec l'image clé précédente : force brute, distance de Hamming, vérification croisée (seules
   les paires mutuellement les meilleures).
3. **Remontée en 3D** : la profondeur de l'image précédente est déjà en unités du monde, donc ses pixels appariés
   deviennent des points du monde.
4. **Placer la caméra** : `solvePnPRansac` parmi ces points (erreur de reprojection 3 px, confiance 0,999, 200
   itérations). La translation sort dans les mêmes unités, donc **l'échelle traverse l'écart**.
5. **Ancrer la profondeur de cette image** : sa propre inverse de profondeur prédite est ajustée (`fit_scale`)
   contre les profondeurs des inliers de PnP, et le cycle recommence.

La **première image** est l'origine : pose identité, et son affine de profondeur est soit l'étalonnage au sol
ci-dessous, soit, sans lui, l'identité (la reconstruction est alors cohérente en elle-même mais sans unité).

Une pose exige au moins **18 inliers RANSAC** - nettement plus que le minimum de PnP, qui est de six, car une
solution tirée de points tout juste suffisants est exactement celle qui se trompe avec assurance.

### Confiance {#confidence}

Chaque image placée reçoit une confiance entre 0 et 1 qui pondère sa fusion et sa couverture :

| Pose issue de | Confiance |
|---|---|
| télémétrie | 1.0 |
| un solveur à propagation directe | 0,85 |
| suivi visuel | `inliers / matches x min(1, inliers / 60)` |

### Lorsque le suivi se rompt {#when-tracking-breaks}

Une image qui ne peut pas être placée est signalée, jamais devinée : `no features in the frame (N found)` (aucun point
dans l'image, N trouvés), `too few matches to place the camera` (trop peu de correspondances pour placer la caméra),
`could not relocalise` (relocalisation impossible). Aucune pose n'est enregistrée, et rien n'est fusionné. Continuer
depuis la dernière pose, ou repartir d'une nouvelle origine, placerait le tronçon suivant du niveau à un décalage
arbitraire - une couture qui ressemble à une vraie géométrie.

Après une rupture, chaque nouvelle image est **relocalisée** par rapport à une base d'images clés passées (une image
suivie sur quatre est ajoutée, jusqu'à 120, la plus ancienne étant retirée), la plus récente d'abord, avec la même
étape de correspondance et de PnP. Tant qu'aucune n'aboutit, les images sont abandonnées. Une image récupérée continue
dans le même repère de coordonnées. Les récupérations sont comptées et affichées dans la fenêtre (`N recovered`).

### Fermeture de boucle : désactivée {#loop-closure-off}

La même base permet la fermeture de boucle : comparer avec des images clés très anciennes pour détecter un retour
sur un lieu déjà vu et recaler la trajectoire dessus. **Elle est désactivée par défaut, et le scanner ne l'active
jamais** (`Reconstructor(loop_closure=False)`). Sur un décor répétitif - une épreuve de rallye, un couloir, une rangée
d'arbres - chaque tronçon ressemble à tous les autres, et la mise en correspondance des points confirme de faux
retours, ce qui cloue la caméra près de son point de départ pendant qu'elle continue de rouler. Le faire correctement
exige une reconnaissance de lieux (un vocabulaire de sacs de mots ou un descripteur appris) et une vérification
géométrique contre une carte, ce qui n'est pas construit.

Lorsqu'elle est activée depuis du code, une fermeture exige : une image clé d'au moins 60 images clés, à moins de 6 m
de la pose courante, appariée avec au moins 90 inliers, déplaçant la pose de plus de 0,02 m et de moins de 6 m. Même
alors, elle ne fait que remplacer la pose courante ; ce n'est pas un graphe de poses et elle ne déplace ni les images
précédentes ni la géométrie déjà fusionnée.

## Poses issues de la télémétrie {#telemetry-poses}

Avec **Racing telemetry (Forza) -> Listen for position data** activé, la trajectoire de la caméra vient du Data Out de
Forza au lieu des images (`ForzaPoseSource`) :

- Un fil écoute sur `127.0.0.1:<port>` (5300 par défaut) avec la même détection de disposition que les enregistreurs
  ([Forza](telemetry-forza.md)) ; les paquets sont utilisés tant que `isRaceOn` est activé. Un port occupé est signalé,
  pas levé : la télémétrie est un bonus et le scan continue visuellement.
- Chaque paquet est horodaté avec **l'instant monotone où il est arrivé** - la même horloge que celle qui horodate les
  images de la capture. L'horodatage du jeu compte à partir d'une origine sans rapport, donc il n'est pas utilisé pour
  l'alignement. Une gigue de bouclage d'une ou deux millisecondes représente environ 6 cm à 200 km/h.
- Un tampon glissant de 30 secondes est conservé. La pose d'une image est **interpolée** à partir des échantillons de
  part et d'autre de son instant de capture : la position linéairement, la rotation par interpolation sphérique (une
  matrice mélangée n'est pas une rotation et fausserait chaque point). Au-delà d'un trou de plus de **0,35 s**, ou hors
  du tampon, il n'y a pas de pose.
- `pose_from_forza` : la caméra est placée à la voiture (le décalage d'une caméra-poursuite n'est pas publié).
  **Les positions sont conservées exactement telles que le jeu les envoie** : le monde de Forza est déjà Y vers le haut
  (x et z sur la carte, y la hauteur), comme l'écrivent les fichiers de tour et de trajet ; la surface tombe donc sur
  les mêmes coordonnées que les tours enregistrés par-dessus. (Une version antérieure échangeait y et z pour un monde
  « Z vers le haut » et couchait le tracé sur le côté.)
- La rotation est lacet, puis tangage, puis roulis, avec les sens relevés sur de vrais tours : la direction de marche
  `atan2(dx, dz)` égale le lacet, la pente gravie égale moins le tangage (positif = nez vers le bas), et le roulis est
  positif lorsque la suspension droite est comprimée (positif fait descendre le côté droit). Les axes de la voiture (x
  à droite, y vers le haut, z vers l'avant) sont ensuite transformés en ceux de la caméra (x à droite, y vers le bas,
  z vers l'avant) en retournant y.
- Le monde de Forza est **gaucher** et le repère de la caméra ne l'est pas, donc la matrice monde-depuis-caméra
  résultante est une réflexion (déterminant -1), et le scan sort gaucher comme les fichiers de tour. L'interpolation
  n'est pas affectée (la rotation entre deux de ces poses est une vraie rotation).
- Lorsqu'une image n'a pas de pose de télémétrie (un trou), le reconstructeur retombe sur le **suivi visuel** pour cette
  image, en repartant de la dernière pose de télémétrie, puis revient aux poses du flux dès qu'il répond de nouveau.
  PnP ne renvoie que des rotations ; dans un monde miroir, il est donc résolu avec le monde reflété par z, la réflexion
  étant réintégrée ensuite ; l'image atterrit dans les coordonnées du jeu. Seulement si le suivi visuel échoue aussi,
  l'image n'est pas suivie.

### Échelle de profondeur à partir de la télémétrie {#depth-scale-from-telemetry}

Le jeu dit où est la caméra, pas à quelle distance se trouve chaque chose ; la profondeur de chaque image doit donc
encore être ancrée - mais pas en enchaînant depuis la première image, dont l'unité est arbitraire alors que les poses
sont en mètres. À la place, les points appariés entre l'image précédente et la courante (au moins 8) sont **triangulés
directement à partir des deux poses connues**, en mètres, et la carte de profondeur est ajustée sur les points devant
la caméra. Chaque image est ancrée contre la télémétrie, il n'y a donc aucune chaîne qui dérive.

Si les deux poses sont à moins de **0,05 m** l'une de l'autre, les rayons sont presque parallèles et la triangulation
n'est que du bruit ; l'image reste donc sans ancrage : positionnée exactement, mais non fusionnée (« positioned, but its
depth has no scale yet », positionnée, mais sa profondeur n'a pas encore d'échelle). C'est pourquoi la fenêtre compte
séparément les images *placées* et les images *fusionnées*.

## Échelle {#scale}

L'odométrie visuelle enchaîne correctement l'échelle relative, mais tout le niveau flotte sur un facteur inconnu. La
sortie relative de Depth Anything est en unités arbitraires ; laisser la première image à l'identité place donc le
monde à quelques mètres de la caméra, à une taille arbitraire.

`GroundCalibrator` fixe ce facteur à partir de **la hauteur de la caméra au-dessus du sol**, mesurée sur la **première
image clé** et, lorsqu'elle n'a pas de sol utilisable, sur les suivantes :

- Hauteur de la caméra : **1,15 m** (la ligne des yeux d'un conducteur) - la fenêtre l'utilise toujours ; les scripts
  peuvent passer 1,70 m (`WALKING_HEIGHT`, un joueur debout) ou `None` (pas d'étalonnage).
- Échantillon de sol : les lignes situées à 62-92 % de la hauteur de l'image (sous l'horizon, au-dessus du capot ou de
  l'arme) et les colonnes à 30-70 % de la largeur (loin des accotements).
- Chaque pixel de cette zone ayant une prédiction utilisable est relevé avec la profondeur `1 / predicted` dans les
  unités du réseau ; les points situés sous l'axe optique donnent une hauteur sous la caméra. Leur médiane est la hauteur
  de la caméra dans les unités du réseau, donc `mètres par unité = 1,15 / médiane`, et l'affine de l'image est
  `scale = 1 / mètres_par_unité`, décalage 0.
- Accepté seulement avec au moins 200 échantillons de sol et une **dispersion** (écart absolu médian divisé par la
  médiane) inférieure à **0,60**.
- Sur la première image clé, l'ajustement devient l'unité de l'origine, donc le scan est en mètres dès le départ. Lorsque
  la première image clé n'a pas de sol utilisable, le scan démarre sans unité et chaque image clé suivie est essayée,
  jusqu'à **30 images** au total. Le premier qui s'étalonne donne le *mètres par unité* : la médiane, sur la bande de sol,
  de la profondeur que son sol implique divisée par la profondeur que la chaîne a donnée à cette image. Tout ce qui est
  déjà fusionné est dans l'unité de la première image, donc le facteur n'est pas réinjecté dans la chaîne ; il est appliqué
  à tout le niveau (et aux repères marqués) lorsqu'il est écrit, et à la distance affichée entre-temps. La taille du voxel
  est alors dans l'unité de la première image, donc sa taille en mètres diffère du réglage de ce facteur.
- Après 30 images sans sol, le scan reste sans unité, et il le signale.
- Avec la télémétrie, les images clés suivantes ne sont pas essayées : la profondeur est ancrée sur les mètres de la
  télémétrie.

Être à dix pour cent près de la vraie taille vaut mieux que d'être faux d'un facteur mille ; la télémétrie, lorsqu'elle est
disponible, rend cela inutile. La note est affichée dans la fenêtre sous la ligne de suivi, sous la forme `Size: ...` :
`measuring the ground` (mesure du sol), `no flat ground in view yet - still looking (N frames tried)` (pas encore de sol plat
en vue - on cherche toujours, N images essayées), `scaled from a 1.15 m camera height, ...` (mise à l'échelle depuis une
hauteur de caméra de 1,15 m, ...; avec `found on frame N, so the level is scaled by F when it is written` lorsque cela est
venu plus tard), `no usable ground in the first N frames - sizes are relative, not metres` (pas de sol utilisable dans les N
premières images - tailles relatives, pas des mètres), ou `in metres, from the telemetry's positions` (en mètres, d'après les
positions de la télémétrie).

## Ajustement de faisceau et longues trajectoires (non branché) {#bundle-adjustment-and-long-tracks-not-wired-in}

Deux pièces existent pour un futur solveur par fenêtre et ne sont **pas utilisées par le scanner** :

- **`FeatureTracks`** garde l'identité des points sur des centaines d'images avec le suivi Lucas-Kanade (600 points,
  réensemencés sous 60 %, tolérance aller-retour de 1 px, nouveaux points à 10 px des points existants), ce dont
  l'ajustement de faisceau a besoin - la mise en correspondance des descripteurs entre images consécutives ne donne que
  des paires.
- **`bundle_adjust`** affine une fenêtre de poses et de points ensemble avec `scipy.optimize.least_squares` (région de
  confiance, perte soft-L1 à l'échelle de 2 px, motif de parcimonie explicite du jacobien, caméras fixes restaurées
  exactement). Testé contre une vérité connue dans `tests/test_bundle.py`.

`WindowedOdometry` combine les deux (fenêtres de 12 images clés, une résolution toutes les 3 images clés, les deux
premières caméras fixes, points de plus de 6 px d'erreur écartés, sauts de plus de 6 fois le pas récent refusés). Sa
docstring note que, sur de vraies images, il **a écrasé la trajectoire et a été beaucoup plus lent** que le suivi d'image
à image, avec pour causes connues la liberté de jauge (l'échelle) et un amorçage fondé sur la profondeur, et une troisième
cause non identifiée. L'odométrie d'image à image reste donc la valeur par défaut ; la correction probable notée dans le code
est un amorçage à deux vues par matrice essentielle, avec la base fixée depuis l'étalonnage du plan du sol.
