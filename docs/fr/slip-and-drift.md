---
title: "Glissement, dérive et canaux dérivés"
nav_order: 8
lang: fr
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Glissement, dérive et canaux dérivés {#slip-drift-and-derived-channels}

L'analyse de la conduite de la voiture, dans l'onglet Analyse de course de la visionneuse, veut les mêmes quelques grandeurs
pour chaque jeu : de combien chaque pneu glisse, de combien la voiture pointe ailleurs que là où elle va (l'angle de dérive), si
elle est en l'air, si elle roule sur un sol meuble. Les jeux les envoient sous des formes très différentes, ou pas du tout. Les
enregistreurs d'ici écrivent ce que chaque jeu envoie, sous des noms canoniques, plus une note `meta.slip` qui indique ce que
signifient les nombres de glissement ; la visionneuse déduit ensuite ce qui manque, une fois, au chargement d'un tour. **La valeur
propre d'un jeu l'emporte toujours sur une valeur dérivée.**

## Ce que les enregistreurs écrivent {#what-the-recorders-write}

| Jeu | Canaux de glissement | `meta.slip` | Données de l'angle de dérive |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` par roue, tels qu'envoyés | `peak` (écrit par l'enregistreur ; le lecteur `.tele.gz` de la visionneuse met la même valeur) | `latVel`, `longVel` à partir de la vitesse locale à la voiture |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` à partir de la vitesse dans le repère de la voiture |
| EA SPORTS WRC, jeux DiRT | aucun ; `wheelSurfaceSpeed` par roue à la place | `null` | `latVel`, `longVel` = vitesse du monde projetée sur les axes de la voiture |
| Richard Burns Rally | aucun ; pas non plus de vitesses de roue | aucun | `latVel`, `longVel` = le balancement et l'avance propres de la voiture |
| BeamNG.drive | aucun ; `wheelSurfaceSpeed` et `wheelSpeed` par roue | aucun | `latVel`, `longVel` = vitesse du monde projetée sur les axes de la voiture |
| Trackmania | `slipIndex` par roue (une mesure de glissement de 0 à 1) | `index` | `latVel` (vitesse latérale), `longVel` (vitesse avant) |
| iRacing | aucun (non enregistré) | aucun | `yaw` et la trajectoire, `yawRate` |

Les valeurs de `meta.slip` sont définies dans [Le fichier heat3d-lap](lap-format.md) : `peak` (normalisé, donc au-delà de 1 le pneu
lâche), `scaled` (un glissement physique divisé par un pic typique sur asphalte), `physical` (une fraction et des radians), `index`
(une mesure de glissement de 0 à 1).

### Pourquoi le glissement de Kunos est mis à l'échelle {#why-kunos-slip-is-scaled}

Le glissement de Forza est normalisé pour que 1 soit le bord de l'adhérence ; ce à quoi il se normalise n'est pas documenté. Kunos envoie
le taux de glissement physique (une fraction) et l'angle de glissement (en radians). En divisant par un pic typique sur asphalte - 0,12
pour le taux, 0,14 rad (environ 8 degrés) pour l'angle - on rend à peu près vraie la règle « au-delà de 1 signifie qu'il glisse » pour les
deux familles, ce qui garde une seule lecture pour les affichages de la visionneuse. C'est une approximation : les vrais pics varient selon
le pneu et la surface, ce qui explique pourquoi les valeurs brutes sont conservées à côté des valeurs mises à l'échelle, et pourquoi la
visionneuse mesure, à partir des tours eux-mêmes, l'endroit où l'adhérence de chaque voiture lâche réellement.

## Ce que la visionneuse dérive (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Ces calculs se font dans la visionneuse (`src/race/derive.ts` dans la visionneuse 3DHeat), et non dans ce dépôt.

### Angle de dérive, `bodySlip` {#drift-angle-bodyslip}

- **À partir de la vitesse dans le repère de la voiture** lorsque `latVel` et `longVel` sont présents :
  `atan2(latVel, |longVel|)`, et 0 en dessous de 3 m/s (une voiture arrêtée de travers ne dérive pas).
  Son signe suit la vitesse latérale du jeu, dont le sens est documenté dans les deux sens pour certains jeux - lisez la taille.
- **Sinon à partir du cap par rapport à la trajectoire** : la direction de marche est prise à partir des positions à environ 2 m de
  part et d'autre de chaque échantillon (`atan2(dx, dz)`) ; le `yaw` du jeu est ajusté sur elle avec un signe et un décalage (chaque
  jeu a son propre zéro et son propre sens de rotation) en utilisant les échantillons au-dessus de 10 m/s, et n'est retenu que s'il
  concorde ensuite étroitement (étalement circulaire d'au plus 0,05, au moins 20 échantillons). L'angle de dérive est la différence,
  0 en dessous de 3 m/s.

### Taux de glissement à partir des roues {#slip-ratio-from-the-wheels}

Lorsqu'un tour n'a pas de `slipRatio.*` mais a des vitesses de roue, le taux de glissement est `(roue - voiture) / voiture` par roue, à
partir de :

- `wheelSurfaceSpeed.*` (la vitesse de l'aire de contact, en m/s) directement, lorsqu'elle est envoyée (EA WRC, DiRT, BeamNG) ;
- sinon `wheelSpeed.*` (rotation, rad/s) multipliée par un **rayon de roulement mesuré sur le tour** : la médiane de `vitesse / |omega|`
  sur les échantillons où la voiture roule sans frein sur une ligne droite (au-delà de 10 m/s, pas en l'air, accélérateur sous 0,3, frein
  sous 0,05, accélération longitudinale sous 3 m/s²) ; avec moins de 20 de ces échantillons, chaque échantillon au-delà de 10 m/s. Un rayon
  hors de 0,1-1 m est rejeté.

Seulement lorsque les quatre roues peuvent être dérivées ; le `meta.slip` du tour devient alors `physical`. En dessous de 3 m/s, le
glissement vaut 0.

### En l'air {#airborne}

`airborne` vaut 1 lorsque chaque roue est hors du sol, jugé d'après le premier de ces critères dont le tour dispose pour les quatre roues :

1. `groundContact.*` (BeamNG) : aucune roue au-dessus de 0,5 ;
2. `wheelLoad.*` (jeux AC, RBR, BeamNG) : aucune roue au-dessus de 5 % de sa propre charge médiane ;
3. `suspension.*` (0..1 du débattement) : aucune roue au-dessus de 0,02, c'est-à-dire toutes entièrement détendues.

Un échantillon isolé en l'air est effacé. Trackmania écrit `airborne` lui-même.

### Sol meuble {#loose-ground}

Lorsqu'un tour a `surfaceRumble.*` (Forza), `loose` vaut 1 là où au moins deux roues signalent une vibration pendant au moins un tiers de
seconde, les trous de moins d'une seconde étant comblés (une zone lisse sur une route de gravier reste la route de gravier). Trackmania
écrit `loose` lui-même, à partir des matériaux du sol sous les roues.

### Vitesse de lacet {#yaw-rate}

Lorsqu'un tour a `yaw` mais pas `yawRate`, c'est la variation du lacet sur les échantillons voisins.

## Ce que les enregistreurs dérivent eux-mêmes {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1) : tous les enregistreurs sauf Forza (qui l'envoie) l'écrivent à partir de `suspensionM.*` comme la position dans
  la plage utilisée par ce tour (minimum à maximum). Elle sert aux barres de suspension de la voiture et à repérer une roue qui pend en l'air ;
  ce n'est pas une fraction absolue de débattement.
- **`steer`** pour les jeux Kunos, mis à l'échelle par tour (voir [Jeux Assetto Corsa](telemetry-assetto-corsa.md)).
- **Accélérations** pour BeamNG, à partir de la variation de la vitesse du monde ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** et l'axe vertical pour Richard Burns Rally, à partir des positions ([Jeux de rallye](telemetry-rally.md)).

## Latéralité {#handedness}

Lorsque le monde d'un jeu est gaucher - celui de Forza l'est - un parcours sort en miroir dans une visionneuse droitière ; la direction et la
suspension des tours le révèlent. Les enregistreurs ne modifient pas la latéralité : un monde Z vers le haut (BeamNG) est tourné pour avoir Y
vers le haut par une rotation, ce qui conserve la latéralité, et tout le reste est écrit tel qu'envoyé.
