---
title: iRacing
nav_order: 6
lang: "fr"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing n'a besoin **d'aucun enregistreur**. Le simulateur écrit lui-même ses fichiers de télémétrie,
`.ibt`, lorsque l'enregistrement de télémétrie est activé (Alt+L dans la voiture) : toute la session à 60
Hz, chaque canal que le simulateur expose, avec la description YAML de la session à côté. Déposez le
fichier `.ibt` dans l'onglet Analyse de course du visualiseur.

Le lecteur se trouve dans le visualiseur, et non dans ce dépôt (`src/race/ibt.ts` dans le visualiseur
3DHeat). Il est testé sur un fichier synthétique ; il est documenté ici parce qu'il constitue la partie
iRacing du même enregistrement de tours.

## Ce que contient le fichier, et comment il est lu {#what-the-file-holds-and-how-it-is-read}

Le fichier est la disposition mémoire documentée du simulateur, écrite sur le disque :

| Partie | Taille | Contenu |
|---|---|---|
| En-tête | 112 octets | version, fréquence de ticks, où se trouvent le YAML et la table des variables, la longueur d'une ligne d'échantillon, où commencent les lignes |
| Sous-en-tête du disque | 32 octets | date et heure de début, nombre de tours, nombre de lignes |
| Table des variables | 144 octets par canal | type, décalage dans la ligne, nombre, nom, description, unité |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Lignes | une par tick | |

Un fichier est refusé lorsqu'il fait moins de 144 octets, lorsque son en-tête n'est pas cohérent (aucune
variable, une table de variables hors du fichier, une longueur de ligne nulle), lorsqu'il lui manque l'un
des champs `SessionTime`, `Lap`, `Lat`, `Lon`, ou lorsqu'aucun échantillon ne contient de position.

## Position {#position}

iRacing donne la latitude, la longitude et l'altitude, et non une position dans le repère propre de la
piste. Les positions sont exprimées en mètres sur un plan tangent au premier échantillon disposant d'une
position (rayon de la Terre 6 371 008,8 m) : `x` vers l'est, `z` vers le sud, `y` l'altitude - de sorte que,
vue d'en haut avec le cap par défaut de la caméra du visualiseur, le nord soit en haut de l'écran.

## Tours {#laps}

La session est découpée d'après le compteur `Lap` du simulateur. Un tour n'est retenu que s'il compte plus
de 60 échantillons, commence avant 5 % de la distance du tour (`LapDistPct`) et finit après 95 % - c'est-
à-dire les tours menés de ligne à ligne. Si aucun tour ne remplit ces conditions, le fichier est refusé avec
un message qui indique la longueur de piste lue dans le YAML. `distance` est `LapDist` ramené au départ du
tour, ou la distance parcourue calculée à partir des positions lorsque `LapDist` manque ; `time` est
`SessionTime` depuis le départ du tour.

## Canaux {#channels}

| iRacing | Canal | Conversion |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | aucune |
| `Clutch` | `clutch` | `1 - valeur` (iRacing compte l'embrayage comme enclenché ; le canal est la pédale) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radians, sens antihoraire positif, ramené à -1..1 avec droite positive ; pi lorsque le maximum manque) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | aucune |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | aucune |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | réglages des aides |
| `dcBrakeBias` | `brakeBias` | divisé par 100 lorsqu'il dépasse 1,5 (un pourcentage sur certaines voitures) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | température de la carcasse au milieu de la bande de roulement |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa multipliés par 0,145038, en psi |
| `..wearM` | `tireWear.*` | `1 - valeur` |

Tout autre canal à une valeur par échantillon (et qui n'est pas un simple octet) est repris sous son propre
nom ; le préfixe de roue (`LF`, `RF`, `LR`, `RR`) devient un suffixe (`.FL`, `.FR`, `.RL`, `.RR`), si bien que
les graphiques du visualiseur le proposent sans que quiconque le décrive.

La voiture vient de `DriverInfo` : l'entrée dont `CarIdx` correspond à `DriverCarIdx` donne `CarScreenName`,
`CarID` et `CarClassShortName`. La piste est `TrackDisplayName` (ou `TrackName`).

## Ce qu'iRacing ne fournit pas {#what-iracing-does-not-give}

Aucun glissement de pneu n'est enregistré, il n'y a donc pas de canaux de glissement. L'angle de dérive est
calculé à partir de la vitesse de lacet par rapport à la trajectoire (voir [Glissement, dérive et canaux
dérivés](slip-and-drift.md)). Les modèles de piste sont fournis dans un format protégé et ne sont pas une
cible d'extraction de fichiers (voir [Jeux](games.md)).
