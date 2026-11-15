---
title: "Limites et vérification"
nav_order: 9
lang: fr
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Limites et ce qui est vérifié {#limits-and-what-is-verified}

Une liste franche : ce que les outils ne font pas, et ce qui n'a pas été contrôlé sur un jeu en cours d'exécution.

## Télémétrie {#telemetry}

| Enregistreur | État |
|---|---|
| Forza | Construit d'après la documentation officielle de Data Out ; la disposition est détectée à partir des paquets eux-mêmes. Le lecteur de `.tele.gz` de FH Companion dans le visualiseur a été contrôlé sur de vrais tours. |
| AC, ACC, AC EVO, AC Rally | Testé sur des pages synthétiques construites à partir des dispositions publiées. **Pas encore exécuté contre les jeux en direct.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testé sur des paquets construits à partir des dispositions documentées. **Pas encore exécuté contre les jeux en direct.** Les axes, l'attitude et les unités de vitesse de RBR ne sont pas documentés et sont traités à partir des données. |
| BeamNG.drive | L'enregistreur est testé sur des paquets construits à partir de la structure du mod. **Le mod n'a pas été exécuté dans le jeu.** |
| Trackmania | Le lecteur du visualiseur pour le CSV est testé. **Le plugin n'a pas été exécuté dans le jeu.** Il ne se charge qu'en mode développeur d'Openplanet. |
| iRacing | Le lecteur `.ibt` du visualiseur est testé sur un fichier synthétique. |

Autres limites de la télémétrie :

- La normalisation du glissement de Forza n'est pas documentée ; le glissement Kunos est mis à l'échelle par un pic de
  référence typique sur asphalte, une approximation.
- Le sens de certains axes latéraux du repère de la voiture (Kunos, DiRT) est documenté dans les deux sens ; la taille de
  l'angle de dérive est fiable, son signe ne l'est pas.
- Aucun des jeux de rallye n'envoie le glissement des pneus ; il est calculé dans le visualiseur. RBR n'envoie pas la
  vitesse des roues.
- La surface d'une épreuve de rallye n'est écrite que si `--surface` est donné ; sinon le fichier n'en nomme aucune et le
  visualiseur la déduit (nom de l'épreuve ou de l'événement, puis style de conduite, souple par défaut).
- La détection des tours sans compteur de tours (AC EVO, AC Rally, BeamNG) prend comme ligne le point où
  l'enregistrement a commencé ; commencez donc à enregistrer sur la ligne de départ.
- Une remise à zéro du véhicule dans BeamNG ferme le tour ouvert à ce moment : il est écrit comme une partie partielle
  quand il a couvert la distance minimale (300 m), et abandonné sinon.
- `route` sauvegarde environ toutes les 2 secondes pendant la conduite ; un plantage ou un processus tué perd au plus les
  positions depuis la dernière sauvegarde.
- Forza Horizon n'envoie pas de nom de circuit ; les fichiers de tours Forza ont donc `"track": null`. Forza Motorsport
  (2023) n'envoie qu'un numéro, conservé comme `lap.trackOrdinal`.

## Reconstruction {#reconstruction}

- **La profondeur est estimée, non lue.** C'est le plafond de toute l'approche, et le prix de ne jamais toucher au
  processus du jeu.
- **Le champ de vision est supposé, non mesuré.** Trop étroit, et le niveau se reconstruit plus profond qu'il ne l'est.
- **L'échelle globale** vient d'une hauteur de caméra supposée (1,15 m dans la fenêtre), ou de la télémétrie. Elle est
  mesurée sur la première image clé ; quand celle-ci n'a pas de sol exploitable, les images clés suivantes sont essayées
  (jusqu'à 30 images), et une échelle trouvée plus tard est appliquée à tout le niveau à l'écriture. La ligne « Size: » de
  la fenêtre indique ce qui s'est passé ; si aucun sol n'est trouvé, le scan reste sans unité. La taille du voxel est alors
  dans les unités de la première image, donc sa taille en mètres diffère du réglage. Les reconstructions hors ligne sont
  dans les unités propres du solveur.
- **La fermeture de boucle est désactivée** et n'est pas un graphe de poses quand on l'active dans le code ; la dérive
  n'est bornée que par la qualité du suivi d'image à image.
- **L'ajustement de faisceaux par fenêtre existe mais n'est pas branché** ; il s'est effondré sur de vraies images.
- **La surface est une occupation pondérée, non un TSDF** : les structures fines et l'espace libre sont moins bien rendus
  qu'avec un TSDF.
- **Pas d'atlas de textures.** La couleur est par sommet (`COLOR_0`), mélangée à partir des 4 meilleures vues parmi
  160 images gardées. Le test d'occlusion est grossier : il se fait contre les sommets du maillage lui-même dans un tampon de
  profondeur de 2 pixels, donc un obstacle que le maillage ne contient pas (une voiture qui passe) n'est pas détecté.
- **L'eau n'est jamais étiquetée** ; tout est du sol ou de la structure.
- **La résolution à partir de l'avant n'est pas en direct** : elle a besoin de l'enregistrement d'abord. La re-résolution
  adaptative des sections difficiles n'est pas construite.
- **Les poses de télémétrie** placent la caméra sur la voiture (le décalage d'une caméra-poursuite est inconnu). Les
  positions sont prises telles que Forza les envoie (Y vers le haut, comme dans les fichiers de tours) ; les sens du lacet,
  du tangage et du roulis ont été lus sur des tours enregistrés (sens de la marche, pente, côté dont la suspension se
  comprime), et non sur la caméra du jeu en cours d'exécution.
- La superposition ne peut pas dessiner par-dessus le **plein écran exclusif** ; utilisez le fenêtré sans bordure.
- Les raccourcis globaux, la superposition traversable aux clics et la capture en direct ne fonctionnent que sous
  **Windows**.
- Fermer la fenêtre ne propose pas d'enregistrer.

## Ce qui est mesuré {#what-is-measured}

- `tests/test_accuracy.py` : une pièce synthétique avec un chemin connu et une profondeur analytique - images placées,
  erreur de chemin, distance parcourue, taille de la pièce, surface sur les murs ([Reconstruction du niveau](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py` : une route de largeur connue parcourue hors centre reconstruit sa largeur.
- `tests/test_track_scale.py` : extraction de surface à l'échelle d'un circuit, mémoire proportionnelle à ce qui a été
  scanné, blocs qui se joignent en une seule surface.
- `tests/test_glb.py` ainsi que les propres tests du visualiseur : le contrat `.glb` vu des deux côtés.
- La façon dont le réseau de profondeur se comporte sur du vrai jeu n'est pas une question à laquelle une scène
  synthétique peut répondre, et elle n'est pas mesurée par la suite de tests.
