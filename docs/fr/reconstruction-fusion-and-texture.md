---
title: "Fusion, couverture et couleur"
nav_order: 5
lang: fr
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusion, couverture et couleur {#fusion-coverage-and-colour}

Code : [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Chaque image clé placée met à jour deux grilles creuses à la fois : le **volume de surface**, qui devient
le maillage, et la **grille de couverture**, qui indique la confiance à lui accorder et où revenir. Les deux
sont mises à jour à chaque image clé, et non à la fin, car la carte de couverture est ce selon quoi le
joueur se guide.

## De la profondeur aux points {#from-depth-to-points}

Pour chaque image clé dont la pose est connue **et** dont la profondeur a une échelle :

1. Un pixel sur deux dans chaque direction est utilisé (`PIXEL_STRIDE = 2` ; les pixels voisins d'une même
   surface ne sont pas des mesures indépendantes).
2. La profondeur est convertie en mètres par l'ajustement affine de l'image.
3. Elle n'est conservée qu'entre **0,35 m** (plus près, c'est l'arme, l'ATH, le capot) et **60 m** (l'erreur
   monoculaire croît à peu près avec le carré de la distance, donc les points lointains sont du bruit en
   forme de géométrie), et seulement sur les pixels du monde du masque.
4. Il est relevé par le modèle de caméra et placé dans le monde par la pose.
5. Chaque point porte la couleur du pixel.

Une image positionnée mais sans échelle de profondeur est comptée comme *placée* mais non *fusionnée*.

## Le volume de surface {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - le voxel est le « Surface detail » de la fenêtre.

### Occupation pondérée, pas un TSDF {#weighted-occupancy-not-a-tsdf}

Un champ de distance signée tronqué (TSDF) creuse le long de chaque rayon de pixel et obtient bien les
structures fines et l'espace libre net, car il sait qu'un rayon est *passé à travers* un espace vide. Cela
oblige à parcourir le rayon pour chacun des centaines de millions de pixels. Ce volume accumule à la place
une **occupation pondérée** par voxel, puis applique les cubes de marche sur le résultat lissé : assez rapide
pour tourner pendant le scan, sur une machine sans GPU utilisable, et la sortie est une surface fermée
plutôt qu'un nuage de points. Le coût : les structures fines et l'espace libre sont moins bien rendus
qu'avec un TSDF.

### Intégrer une image {#integrating-a-frame}

- Les points sont rangés dans des voxels (`floor(point / voxel)`).
- Chaque voxel touché reçoit `poids x sqrt(count / max_count)`, où `count` est le nombre de points de l'image
  tombés dans lui, et `poids = max(0.1, confiance de la pose)`. Racine carrée : au-delà d'un certain point,
  davantage de pixels de la même surface vus du même endroit cessent d'être une preuve ; pondérer par la
  confiance de la pose empêche une pose douteuse de déplacer la surface.
- La couleur est une moyenne pondérée courante par voxel.

La grille est **creuse** : un trajet parcouru ne touche qu'une minuscule fraction de sa boîte englobante. Les
coordonnées de voxel sont rassemblées dans une clé de 64 bits (21 bits par axe, jusqu'à +-1 048 575 voxels -
à 0,25 m, environ +-262 km) et recherchées par un tableau trié et une recherche dichotomique, entièrement
vectorisées.

### Extraire le maillage {#extracting-the-mesh}

1. Les voxels de poids inférieur à **0,35** sont retirés (des points isolés aux bords de silhouette
   deviendraient des pointes).
2. Les poids sont mis à l'échelle par le **75e centile** de tout le scan, puis écrêtés à 1.
3. L'espace occupé est découpé en **blocs de 64 voxels** par côté, chacun reconstitué avec une **couronne de
   3 voxels** des données de ses voisins (sans elle, chaque bord de bloc se refermerait en mur, et une route
   sortirait sous forme de rangée de boîtes).
4. Le champ de chaque bloc est lissé par une gaussienne (sigma 0,8 voxel) pour retirer les plis que laisse le
   bruit de profondeur.
5. **Première passe** : le 99e centile du champ lissé, échantillonné sur tous les blocs (au plus 2 millions de
   valeurs), fixe une seule échelle de niveau globale. Normaliser bloc par bloc ferait monter un point
   aberrant isolé au rang de surface complète dans son propre bloc vide.
6. **Seconde passe** : le champ de chaque bloc divisé par cette échelle, cubes de marche au niveau **0,5**. Un
   triangle appartient au bloc où tombe son **centroïde**, ainsi les triangles à cheval sur une couture ne sont
   émis qu'une seule fois.
7. Les sommets passent en unités du monde aux centres des voxels ; chaque sommet prend la couleur de son voxel
   (gris moyen là où il tombe hors d'un voxel occupé).

L'extraction bloc par bloc rend possible un scan à l'échelle d'un circuit : un seul tableau dense sur une boîte
d'un kilomètre de côté à 0,25 m compterait des milliards de cellules. `tests/test_track_scale.py` garantit que
cela fonctionne à cette échelle, avec une mémoire proportionnelle à ce qui a été scanné.

### Sol et structure {#ground-and-structure}

`classify` étiquette chaque triangle selon sa normale (orientée par les normales des sommets extraits) : à
moins de **35 degrés de la verticale** vers le haut, c'est `ground` (sol), tout le reste est `structure`. La
visionneuse dessine le sol plein et les structures presque transparentes. **L'eau n'est jamais revendiquée** :
elle ne se distingue pas du sol plat par sa forme, et une mauvaise étiquette ferait apparaître une cour comme
un lac. Chaque étiquette devient une partie du `.glb` ([La sortie .glb](glb-output.md)).

## Couverture {#coverage}

`CoverageGrid(voxel=0.5)` enregistre, pour chaque cellule d'un demi-mètre, quatre choses qui ne sont pas la
même chose :

| Terme | Stocké | Score (chacun écrêté entre 0 et 1) | Pourquoi il compte à part |
|---|---|---|---|
| Combien de fois vue | nombre d'images clés ayant vu la cellule | `count / 3` | une seule fois n'est qu'une supposition, sans rien pour la comparer |
| Depuis combien de directions | somme des directions de vue unitaires | `(1 - spread) / (1 - 0,93)`, où spread = longueur de la somme / count | vingt images qui foncent droit sur un mur n'ont aucune parallaxe entre elles ; deux vues séparées de trente degrés valent davantage |
| Depuis quelle distance | distance de vue la plus proche | `1 - nearest / 40 m` | l'erreur de profondeur croît à peu près avec le carré de la distance |
| Dans quelle mesure la caméra était bien placée | meilleure confiance de pose | la confiance | la géométrie fusionnée avec une pose douteuse tombe au mauvais endroit |

Les points d'une image sont d'abord regroupés par cellule, de sorte que dix mille pixels d'un même mur comptent
pour une seule observation depuis une seule direction.

**Qualité = le produit des quatre termes**, et non leur moyenne : ce sont des conditions qui doivent toutes être
remplies. Un endroit vu deux cents fois depuis une seule direction à soixante mètres est mal observé, et une
moyenne le masquerait derrière un terme excellent.

Chiffres principaux (`summary`) : cellules occupées, la part dont la qualité est au moins 0,5 (« % bien vu » dans
la fenêtre), qualité moyenne et volume.

### Zones faibles {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)` :

1. les cellules de qualité inférieure à 0,35 sont faibles ;
2. les cellules faibles sont regroupées par **connexité** (voisinage 26, union-find sur les seules cellules
   occupées - pas un balayage raster de la boîte englobante, qui sur une longue route représente des millions de
   cellules vides) ;
3. les groupes de moins de 8 cellules sont ignorés ;
4. la raison de chaque groupe est le *terme le plus faible* le plus fréquent parmi ses cellules, et sa position est
   la moyenne de ses cellules ;
5. triés du plus grand au plus petit (puis par pire qualité), au plus 8.

| Raison | Conseil affiché |
|---|---|
| peu de vues | Vu une ou deux fois seulement - repassez devant. |
| une seule direction | Vu sous un seul angle. Faites un pas de côté et regardez-le à nouveau. |
| lointain | Vu seulement de loin. Approchez-vous. |
| mauvais suivi | La caméra n'était pas bien localisée ici. Approchez-vous plus lentement. |

La connexité compte : regrouper par une grille de blocs fixe présenterait une pièce annexe négligée comme
plusieurs anneaux séparés, et personne ne pourrait distinguer huit endroits d'un seul compté huit fois.

### La vue de dessus {#the-plan-view}

`top_down(resolution)` projette les cellules sur x/z et garde la **meilleure** qualité par colonne (quelqu'un
debout dans une pièce a une mauvaise couverture du plafond et une excellente couverture du sol ; une moyenne
peindrait la pièce en ambre). Les colonnes jamais observées sont marquées à part. La fenêtre la dessine en 200 x 200,
la superposition en 120 x 120 ([La carte de couverture](reconstruction-scan-ui.md#the-coverage-map)).

### Est-ce reconstructible ? {#is-this-reconstructable}

Tous les 25 images fusionnées, dès qu'il y a au moins 500 cellules :

| Constat | Verdict | Message (raccourci) |
|---|---|---|
| moins de 2 % des cellules ont un étalement de vue inférieur à 0,93 | non reconstructible | Presque aucune parallaxe. Soit la caméra ne regarde jamais de côté, soit le suivi dérive, de sorte que la même surface ne tombe jamais deux fois au même endroit. Vérifiez le nombre d'images placées : s'il est élevé, c'est une dérive. |
| distance médiane au plus proche supérieure à 25 m | non reconstructible | Tout a été vu depuis N m ou plus loin ... Approchez-vous de ce que vous voulez. |
| moins de 6 % avec un bon étalement | reconstructible, avec avertissement | Parallaxe faible - la géométrie sera grossière. Se déplacer latéralement par rapport à ce que l'on regarde aide le plus. |

Une faible parallaxe a deux causes que ce contrôle ne peut pas distinguer, c'est pourquoi le message les nomme
toutes les deux.

## Couleur {#colour}

La couleur par voxel de la fusion est peu coûteuse et en direct, mais floue : chaque pixel d'une cellule d'un
quart de mètre est moyenné, y compris ceux vus de biais depuis trente mètres. À l'export, le maillage est donc
colorié une seconde fois, une seule fois, à partir des images elles-mêmes :

- **Images conservées** : jusqu'à **160** images clés (image et pose), choisies par échantillonnage à réservoir pour
  se répartir sur tout le scan plutôt que sur sa fin.
- **Par sommet** (`project_colours`), chaque image conservée contribue si le sommet est devant la caméra et dans
  l'image, si la surface est tournée d'au plus environ 70 degrés par rapport à la caméra de face (`|normal . view| > 0.34`),
  si elle est plus proche que **35 m**, et si rien de plus proche ne se trouvait devant lui (voir plus bas).
- Chaque vue ainsi retenue est notée `facing x (1 - distance / 35)`, de sorte qu'une vue de face proche bat une vue
  lointaine et rasante. Les **4 vues les mieux notées** de chaque sommet sont conservées - quel que soit l'ordre des
  images, une meilleure vue remplace la plus faible des quatre - et mélangées, pondérées par ce même score.
- **Occlusion** : dans chaque image, les propres sommets du maillage visibles sont dessinés dans un tampon de
  profondeur de cellules de 2 pixels, en gardant le plus proche par cellule. Un sommet plus de `0,3 m + 5 %` de sa
  distance derrière le plus proche de sa cellule était caché dans cette image - un mur entre la caméra et la route
  au-delà - et cette vue ne compte pour rien. Le test ne connaît que le maillage : un occultant jamais fusionné (une
  voiture qui passe, un montant de cockpit hors du masque de l'ATH) n'est pas détecté.
- Un sommet qu'aucune image n'a vu garde sa couleur de voxel ; un sommet sans l'un ni l'autre est gris moyen (le
  noir se lirait comme un trou).

La couleur est écrite en `COLOR_0` par sommet, et non en atlas de texture. L'aspect par défaut de la visionneuse
est une carte grise sous une chaleur saturée ; la couleur sert à repérer la route sur un circuit scanné, là où la
géométrie seule ne la distingue pas de l'accotement, et elle s'affiche derrière l'interrupteur « Couleur capturée » de
la visionneuse, dans son panneau Arrière-plan / niveau. Un atlas multiplierait la taille du fichier et exigerait un
dépliage des UV, pour une vue qui n'est volontairement pas celle par défaut. Blender et les autres outils glTF lisent
`COLOR_0`.
