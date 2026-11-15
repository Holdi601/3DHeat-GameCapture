---
title: "Capture, masques et qualité des images"
nav_order: 2
lang: fr
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Capture, masques et qualité des images {#capture-masks-and-frame-quality}

Code : [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## D'où viennent les images {#where-frames-come-from}

Une cible de source est l'une de ces trois :

| Cible | Source | Remarques |
|---|---|---|
| `monitor:<n>` | un écran entier, en direct | l'option « Whole screen » de la fenêtre, avec le numéro dans « Which » |
| `window:<title>` | une fenêtre, en direct | l'option « A window » de la fenêtre, avec son titre |
| un chemin de fichier | un fichier vidéo | l'option « A video file » ; tout format qu'OpenCV sait lire |

### Capture en direct : Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` utilise le paquet `windows-capture`, qui encapsule **Windows Graphics Capture** -
l'API publique qu'utilisent les enregistreurs d'écran. Rien n'est injecté dans le jeu. Le curseur n'est
pas capturé et aucune bordure jaune de capture n'est dessinée.

La bibliothèque de capture remet les images à une fonction de rappel sur le fil du compositeur, et
attend qu'elle rende la main aussitôt. La fonction de rappel se contente donc de copier l'image (le
tampon est réutilisé), de la convertir de BGRA en RGB, de la redimensionner, de l'horodater et de la
placer dans une file de **4 images**. Lorsque la file est pleine, **la plus ancienne image est
abandonnée** et un compteur augmente : prendre du retard doit coûter des images, pas de la mémoire ni la
justesse, et la vue en direct doit montrer où le joueur se trouve maintenant. Les images abandonnées
sont affichées dans la ligne de statistiques de la fenêtre, et plus de la moitié abandonnée déclenche un
conseil.

Chaque image porte `t` (secondes depuis le début de la capture) et `monotonic` (la valeur brute de
`time.monotonic()` au moment de la capture), l'horloge à laquelle les paquets de télémétrie sont aussi
horodatés - c'est ce qui permet d'aligner les poses Forza sur les images.

`windows-capture` est optionnel dans le contrôle des dépendances : sans lui, un fichier vidéo peut encore
être analysé.

### Fichiers vidéo {#video-files}

`VideoSource` lit avec OpenCV, convertit en RGB et redimensionne. Un conteneur sans fréquence d'images
est traité comme 30 i/s. Les horodatages sont l'indice de l'image divisé par la fréquence ; un fichier
n'a pas d'heure réelle, donc la télémétrie ne peut pas être alignée sur une vidéo.

### Résolution {#resolution}

Les images sont redimensionnées à la source pour que leur plus grand côté soit la taille de capture du
préréglage (Draft 640, Balanced 960, Detailed 1280 px), par interpolation par zones. Une image 4K compte
trente fois plus de pixels que ceux qu'utilise le modèle de profondeur.

## Images clés {#keyframes}

Presque chaque image d'une capture est redondante : rester immobile produit des centaines de vues
d'une même chose. La reconstruction a besoin de *parallaxe*. Une image est donc conservée selon **la
quantité dont l'image a changé depuis la dernière image conservée**, et non selon un minuteur.

`picture_change(a, b)` :

1. les deux images sont passées en gris et réduites à une grille de 16 x 16 moyennes de blocs (les
   moyennes de blocs réagissent au mouvement de l'image, pas au grain, au feuillage, au scintillement ni
   à l'ATH) ;
2. la différence absolue moyenne, en fraction de 255 ;
3. lorsqu'un masque du monde est connu, chaque bloc est pondéré par la part de lui qui est le monde et
   non le cockpit, de sorte qu'un bloc à moitié tableau de bord compte pour moitié (utilisé une fois que
   le masque couvre plus de 5 % du poids de la grille).

Le seuil **s'adapte à la capture** : pendant les 30 premières images, c'est la valeur de départ du
préréglage (0,020 / 0,010 / 0,004), puis c'est le quantile du préréglage (0,85 / 0,65 / 0,40) des 240
derniers changements mesurés, jamais en dessous de 0,0001. Une image est conservée lorsque son changement
atteint le seuil ; la première image est toujours conservée. Un seuil fixe ne peut pas marcher d'une scène
à l'autre - le changement d'une image à l'autre dans une scène de cockpit sombre est une petite fraction
de celui d'une pièce lumineuse et texturée - alors que « garder le tiers le plus animé » signifie la même
chose dans les deux cas. Le seuil utilisé est transmis avec chaque mise à jour de progression
(`ScanProgress.threshold`), et les barres de vitesse de marche de la fenêtre et de la superposition mesurent
le dernier changement par rapport à lui (`ScanProgress.toward_next_view`).

Seules les images conservées passent dans le modèle de profondeur et la reconstruction. Les images ne
sont pas stockées sauf si un appelant le demande (`keep_frames`) ; 160 d'entre elles sont gardées pour
colorier le maillage (voir [couleur](reconstruction-fusion-and-texture.md#colour)).

Un scan se termine lorsqu'il est arrêté, lorsqu'une vidéo arrive à sa fin, ou à la limite de temps ou
d'images clés.

## Ce qui n'est pas le monde {#what-is-not-the-world}

Deux choses dans une image de jeu ne font pas partie de la géométrie du niveau, et les deux abîment une
reconstruction :

- **L'ATH.** Un réticule est le repère le plus répétable de toute image. Un appariement de points
  l'adore : il correspond parfaitement entre chaque paire d'images, et chaque correspondance est une
  preuve que la caméra n'a pas bougé - ce qui compresse toute la reconstruction.
- **Ce qui est fixé à la caméra.** Une arme, un capot, un montant de cockpit, un tableau de bord. C'est
  une vraie géométrie dans le mauvais système de coordonnées : fusionnée, elle s'étire sur tout le
  trajet parcouru.

Deux détecteurs les trouvent. Tous deux produisent un masque (255 = monde, 0 = pas le monde) ou `None`
tant qu'il n'y a pas assez de preuves ; `None` signifie toujours « utiliser tout », jamais « n'utiliser
rien ».

Le masque est appliqué :

- à la **détection des points** dans l'odométrie visuelle (masquer un réticule dans la sortie tout en le
  laissant voter sur la pose corrigerait le symptôme visible et garderait celui qui fait des dégâts) ;
- aux **pixels fusionnés**, pour qu'aucune géométrie de cockpit ne soit fusionnée ;
- à la mesure de **netteté et de luminosité**, parce qu'un cockpit est toujours parfaitement net ;
- au **changement d'image** qui décide des images clés.

Il **n'est pas** appliqué aux images données au solveur VGGT hors ligne (voir
[Reconstruction hors ligne](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask : ce qui ne change pas {#screenmask-what-does-not-change}

Utilisé depuis la première image clé jusqu'à ce que FlowMask soit prêt.

- Chaque image est convertie en gris, réduite de moitié et floutée (gaussien 3 x 3) pour qu'un
  décalage d'un pixel d'un élément fixe de l'ATH ne soit pas lu comme un mouvement.
- La différence absolue par pixel avec l'image précédente est intégrée dans une moyenne exponentielle
  (décroissance 0,9), de sorte que le masque suit un ATH qui apparaît ou disparaît en cours de scan.
- Il n'apprend qu'à partir des images où l'on sait que la caméra bouge (dans le scan : une fois qu'au
  moins une image a été suivie) - une caméra immobile rend tout statique.
- Après **12** images d'apprentissage, un pixel est statique lorsque son changement moyen est inférieur à
  **0,22** du changement médian de l'image - relatif, donc le seuil suit la vitesse du joueur.
- Si plus de **45 %** de l'image est lue comme statique, la prémisse a échoué (un menu, une scène
  coupée) et rien n'est masqué.
- Le masque est érodé d'un pixel (les bords crénelés de l'ATH n'appartiennent ni à un côté ni à l'autre)
  puis remis à la taille réelle.

Sa note dans la fenêtre : `learning what is HUD (n/12 frames)` (apprentissage de l'ATH, n/12 images),
`no HUD or attached geometry detected` (aucun ATH ni géométrie fixée détecté), ou
`ignoring N% of the frame — HUD or camera-mounted` (on ignore N % de l'image - ATH ou fixé à la caméra).

### FlowMask : ce qui ne se déplace jamais {#flowmask-what-never-travels}

Un cockpit n'est pas statique : les aiguilles balaient, le compte-tours tressaute, la mini-carte tourne,
donc un détecteur de changement prend ces pixels pour du monde - et ce sont les pires points à donner à
un solveur de pose. FlowMask pose la meilleure question : **quels points persistent sans se déplacer ?**

- Dans le scan en direct, il apprend une seule fois, à partir des **40 premières images clés** (en gris) ;
  puis il remplace ScreenMask pour le reste du scan.
- Les images sont découpées en fenêtres de **30** images, qui se chevauchent à moitié. Dans chaque
  fenêtre, jusqu'à 800 coins sont semés (`goodFeaturesToTrack`, qualité 0,01, 8 px d'écart) puis suivis
  par Lucas-Kanade pyramidal (21 x 21, 4 niveaux) avec une **vérification aller-retour** : une trace dont
  le flux retour n'atterrit pas à moins de 1 px de son point de départ est écartée, car un suiveur qui
  dérive sur un motif voisin fabriquerait exactement la signature « persistant mais immobile » que l'on
  cherche. Les fenêtres de moins de 20 images sont ignorées. Les fenêtres courtes comptent : sur une
  longue course, presque tous les éléments du monde sortent du cadre et la preuve s'amincit jusqu'à
  disparaître.
- Le déplacement net de chaque point survivant est comparé à **2 % de la largeur de l'image** : en
  dessous, il est « figé » ; au-dessus, « en mouvement ». Les comptes sont accumulés sur une grille de
  **24 x 24** cellules de l'écran, selon l'endroit où chaque point a commencé.
- Une cellule est bloquée lorsqu'elle contient au moins 2 points figés et plus de points figés que de
  points en mouvement, **et** lorsqu'au moins 3 de ses 8 voisines sont bloquées aussi (une cellule isolée
  est du bruit ; les images sombres en produisent beaucoup).
- Seules les régions bloquées **reliées au bord de l'image** sont conservées. Tout ce qui est fixé à la
  caméra atteint un bord de l'écran ; ce qui se trouve au milieu et ne bouge pas est le point de fuite -
  en roulant droit devant, la route qui se trouve droit devant n'a pas de flux et c'est la géométrie la
  plus recherchée.
- La région retenue est agrandie d'une cellule (le bord d'un tableau de bord est un dégradé).
- Si plus de **60 %** de l'image serait masquée, rien n'est masqué : sur des images de nuit, la plupart
  des cellules ne contiennent aucun point suivable, ce qui ressemble à un cadran.

Sa note : `watching what moves` (observation de ce qui bouge), `nothing attached to the camera` (rien
de fixé à la caméra), `ignoring N% of the frame — it never travels` (on ignore N % de l'image - il ne se
déplace jamais), ou, au-delà de 60 %, un message expliquant qu'il ne masque rien.

Le chemin hors ligne apprend le même FlowMask à partir de 4 séquences de 90 images consécutives réparties
sur la vidéo, en 960 x 540 ([Hors ligne](reconstruction-offline.md)).

## Qualité des images et conseils {#frame-quality-and-advice}

`QualityWatcher` juge chaque image clé et choisit **une** instruction, afin que la superposition puisse dire
« ralentissez » pendant qu'il est encore temps.

Pour chaque image, il mesure, sur les seuls pixels du monde (tous les pixels si le masque en laisse moins
de 5 %) :

- **netteté** : variance du Laplacien - la mesure standard en une passe, et elle réagit à exactement ce
  que détruit le flou de mouvement ;
- **luminance** : niveau de gris moyen, de 0 à 255.

La netteté n'a pas d'échelle absolue (une étape de nuit et une rue ensoleillée diffèrent d'un ordre de
grandeur, toutes deux nettes), donc elle est jugée par rapport à la **médiane glissante de cette
capture** : les 90 dernières images, qui exigent 20 images avant tout jugement. Chaque image est comparée
à l'historique *avant* de l'y ajouter, afin qu'une longue portion floue ne tire pas la médiane vers elle.

| Condition | Test |
|---|---|
| plat | netteté d'au plus 1,0 (un écran de chargement, un mur, le ciel) |
| sombre | luminance inférieure à 26 |
| flou | netteté inférieure à 0,55 de la médiane, et pas plat |

Le conseil, première correspondance gagnante (classées selon ce qui bloque le plus le scan) :

| Situation | Conseil | Niveau |
|---|---|---|
| moins de 20 images | Prise en main de l'image… | ok |
| plat | Rien à mesurer - visez le niveau, pas le ciel. | stop |
| sombre | Trop sombre pour reconstruire. Phares allumés, ou parcourez ce tronçon en plein jour. | stop |
| flou | Flou - ralentissez. | warn |
| moins de la moitié des images suivies | Perte de suivi - ralentissez et gardez davantage du niveau dans le champ. | warn |
| moins de 40 % des images suivies fusionnées | Les positions sont bonnes mais la profondeur ne prend pas. Roulez plus près du décor. | warn |
| des zones faibles existent | N zones faibles - la carte les marque. | ok |
| sinon | Bien - continuez. | ok |

Le niveau colore le conseil de la superposition (vert / ambre / rouge). La barre de **netteté** de
la superposition est la netteté de l'image par rapport à la médiane. (Le code contient aussi « Blurred, and
the camera is not moving. Check the capture. » pour une caméra immobile ; le scan signale toujours la
caméra comme mobile, donc ce message n'apparaît pas.)
