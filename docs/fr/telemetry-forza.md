---
title: "Forza"
nav_order: 1
lang: "fr"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon et Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # jeu -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # et FH Companion continue de fonctionner
```

Code : [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(détection de la disposition),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(tous les canaux, fichiers de tour, relais).

## Activer dans le jeu {#switching-it-on-in-the-game}

**Paramètres -> HUD et jeu -> Data Out** : `ON`, IP `127.0.0.1`, port `5300` (ou ce que vous passez avec `--port`). Forza Motorsport
propose aussi un format de paquet : il doit être **Dash**, pas Sled. Sled ne contient aucune position, et l'enregistreur le refuse.

L'enregistreur se lie à `127.0.0.1`, donc le jeu doit tourner sur le même PC.

## Ce que le jeu envoie, et comment la disposition est trouvée {#what-the-game-sends-and-how-the-layout-is-found}

Data Out est un paquet UDP par tick de simulation (environ 60 par seconde), une structure C plate en little-endian, dans ces tailles :

| Longueur | Variante |
|---|---|
| 232 octets | Motorsport « Sled » : aucune position. Rejeté avec un message vous demandant de passer à Dash. |
| 311 octets | Motorsport « Dash » : le bloc Sled plus le bloc tableau de bord de 79 octets |
| 324 octets | Horizon « Dash » : le même, avec du remplissage entre les deux blocs |
| 331 octets | Forza Motorsport (2023) : Dash plus 20 octets d'usure des pneus et l'identifiant de circuit |

Le bloc Sled (décalages 0-231) est stable. Là où commence le bloc tableau de bord dans la variante Horizon est décrit de façon
incohérente dans les sources publiées, et se tromper ne fait pas échouer : on obtient des flottants plausibles provenant des mauvais
champs. Le début est donc **découvert** :

1. Les débuts candidats sont essayés dans l'ordre : `longueur - 79` (le bloc tableau de bord va jusqu'au dernier octet dans toutes les
   variantes documentées), 232, 244, et 232 à 260 par pas de 4.
2. Chaque candidat est noté sur les paquets d'une voiture en mouvement (une composante de vitesse au-dessus de 1 m/s) : le vecteur vitesse du
   bloc Sled et le scalaire `Speed` du bloc tableau de bord sont la même grandeur à deux endroits, donc `| |velocity| - Speed |` n'est proche
   de zéro que pour le bon début.
3. Le candidat avec le plus petit désaccord dans le pire cas l'emporte, si ce désaccord est d'au plus **1 m/s**. Sinon, la détection continue
   d'attendre.

Pendant que la voiture est à l'arrêt, chaque candidat lit zéro et tous concordent, ce qui ne prouve rien ; **la détection attend donc que la
voiture bouge** : roulez quelques mètres avant de vous attendre à une sortie. Jusqu'à 600 paquets sont retenus pendant l'attente (réduits aux 300
derniers). Une fois la disposition connue, les paquets retenus sont aussi décodés, de sorte que le début du premier tour n'est pas perdu. Les
paquets d'une longueur différente de la disposition détectée, les paquets de moins de 311 octets, et les paquets dont la position ou la vitesse
n'est pas finie sont ignorés pour les fichiers de tour.

Le jeu de Forza est déduit de la disposition : une disposition Horizon donne `"game": "forza-horizon"`, une disposition Motorsport ou de 331
octets donne `"forza-motorsport"`, toute autre `"forza"`. Le nom de la disposition détectée (`Horizon dash`, `Motorsport dash`, `331-byte dash`)
est écrit sous `layout`.

## Canaux enregistrés {#channels-recorded}

Chaque champ du paquet est décodé (`decode_full`) et converti :

- les pédales `throttle`, `brake`, `clutch`, `handbrake` de 0..255 à 0..1 ;
- `steer` de -127..127 à -1..1 ; `drivingLine` et `aiBrakeDifference` de même, divisés par 127 ;
- `tireTemp.FL` ... `.RR` de Fahrenheit en Celsius ;
- `latAcc`, `longAcc`, `vertAcc` et `yawRate` sont des copies de `accelX`, `accelZ`, `accelY` et `angVelY` sous les noms canoniques (repère de
  la voiture : x à droite, y vers le haut, z vers l'avant) ;
- la vitesse du bloc Sled, qui est dans le repère propre à la voiture (x à droite, y vers le haut, z vers l'avant - et non celui du monde), est
  écrite telle quelle sous les noms canoniques `latVel`, `vertVel` et `longVel`, de sorte que la visionneuse lit l'angle de dérive directement au
  lieu de l'estimer à partir du cap et de la trajectoire.

Les canaux du fichier de tour sont tous ceux-ci, sauf les champs par tour :

| Groupe | Canaux |
|---|---|
| Temps et lieu | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Mouvement | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Moteur | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Conducteur | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Par roue (`.FL .FR .RL .RR`) | `suspension` (0 détendue .. 1 comprimée), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalisés : au-delà de 1 le pneu lâche), `wheelSpeed` (rad/s), `rumble` (sur une bande sonore), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Forza Motorsport 2023 seulement | `tireWear.FL` ... `.RR` |

`time` est le chronomètre du tour en cours du jeu moins sa valeur au premier échantillon du tour ; `distance` est la distance parcourue du jeu
moins sa première valeur. Les positions sont les coordonnées du monde de Forza en mètres, sans modification (y vers le haut ; le monde est gaucher).

Relevés une fois par tour plutôt qu'à chaque échantillon, sous `car` : `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`,
`rpmIdle`. L'identifiant de circuit de FM2023 est aussi noté une fois, sous `lap.trackOrdinal`. Non conservé par échantillon : `isRaceOn` (1 dans
chaque image d'un tour). `timestampMs`, `raceTime`, `bestLap` et `lastLap` sont conservés comme canaux.

Le reste du document est rempli comme pour tous les autres enregistreurs :

- `"track": null` - Forza Horizon ne nomme pas le parcours, et Forza Motorsport ne fait que le numéroter ;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - les canaux de glissement sont normalisés pour qu'au-delà de 1 le pneu lâche ;
- `units` ne liste que les canaux que le fichier contient (les canaux par roue par leur nom de base) ;
- une valeur qui n'est pas un nombre fini est écrite `null`, jamais `NaN`.

Voir [Le fichier heat3d-lap](lap-format.md).

## Comment les tours sont découpés {#how-laps-are-split}

`LapSplitter` (voir [Découpage des tours et des étapes](lap-splitting.md)) : un tour se ferme lorsque le compteur de tours du jeu avance, et son
temps est alors le `lastLap` propre au jeu (celui qu'il affiche). Une course point à point, ou une session qui se termine en plein tour, se
ferme lorsque le jeu quitte la course (`isRaceOn` retombe), lorsque les paquets s'arrêtent pendant 2 secondes, ou lorsque l'horodatage du jeu
recule ; il est conservé comme `run` s'il couvre au moins 400 m.

## Relais vers FH Companion {#relaying-to-fh-companion}

Le jeu n'envoie Data Out qu'à une seule adresse. Avec `--forward hôte:port`, l'enregistreur transmet **chaque paquet reçu sans modification**,
avant de rien décoder (y compris pendant qu'il attend la détection de la disposition), afin qu'une autre application lisant le flux continue de
fonctionner : réglez le jeu sur 5300, l'autre application sur 5301, et lancez avec `--forward 127.0.0.1:5301`.

FH Companion est une application séparée, et non une partie de 3DHeat. Elle tient une bibliothèque de tours dans `%LOCALAPPDATA%\FHCompanion\laps` :
un dossier par parcours, un fichier de tour par tour échantillonné environ tous les cinq mètres, et à côté de chaque fichier de tour
`<lap>.json.tele.gz`, la totalité du Data Out du tour au débit du jeu. 3DHeat lit les deux :

- **La visionneuse lit directement les `.tele.gz`** lorsque vous les déposez (avec ou sans leur fichier de tour) dans l'onglet Analyse de course. Elle
  fait correspondre les noms de champs propres à Forza (`PositionX`, `VelocityX`, `TireSlipRatio` + roue, ...) aux canaux canoniques, transforme les
  `VelocityX/Y/Z` locales à la voiture en `latVel`, `vertVel`, `longVel`, convertit les températures des pneus depuis les Fahrenheit, supprime les lignes
  qui répètent la précédente à l'exception de l'horloge de l'enregistreur, et marque le glissement comme `peak`. Si le fichier de tour est aussi fourni,
  le tour prend sa voiture et son temps de tour à partir de lui. Ce lecteur est dans la visionneuse (`src/race/adapters.ts`, `readForzaTelemetry`), et
  non dans ce dépôt.
- **La commande `laps`** lit la bibliothèque de tours et écrit le tracé d'un parcours ainsi qu'un CSV de chaque échantillon ; voir
  [Référence des commandes](commands.md#laps).

## Autres usages du même flux {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` n'enregistre que les positions, sauvegardées toutes les deux secondes environ pendant la conduite ; voir
  [Référence des commandes](commands.md#route).
- L'option « Racing telemetry (Forza) » de la fenêtre de scan utilise le flux comme poses de caméra exactes pour la reconstruction ; voir
  [Pose et échelle de la caméra](reconstruction-pose.md#telemetry-poses).

## Remarques et réserves {#notes-and-caveats}

- Ce à quoi Forza normalise son glissement n'est pas documenté. `1` est lu comme le bord de l'adhérence, mais la visionneuse mesure l'endroit où
  l'adhérence de chaque voiture lâche réellement.
- La vitesse du bloc Sled est locale à la voiture, comme l'indique la documentation Data Out de Forza et comme le confirment les tours enregistrés
  (sa composante avant porte la vitesse, sa composante latérale reste proche de zéro). La détection de la disposition n'utilise que sa longueur, qui
  est la même dans n'importe quelle trame.
- Les positions sont celles du monde du jeu, Y vers le haut et gaucher. Les sens de `yaw`, `pitch` et `roll` ont été vérifiés sur des tours enregistrés :
  le lacet égale la direction de marche `atan2(dx, dz)`, un tangage positif est le nez vers le bas, et un roulis positif fait descendre le côté droit.
