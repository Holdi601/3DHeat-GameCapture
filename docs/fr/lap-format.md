---
title: "Le fichier heat3d-lap"
nav_order: 9
lang: "fr"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Le fichier `heat3d-lap` {#the-heat3d-lap-file}

Chaque enregistreur de télémétrie de ce dépôt écrit un fichier par tour ou par étape de rallye, dans
la même forme quel que soit le jeu. L'export de parcours de [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
le relit pour retrouver le jeu, le niveau et la trajectoire parcourue. Tout ce qui sait lire le JSON
peut le lire.

![Les champs et canaux d'un fichier de tour écrit à partir d'un flux Forza synthétique](../assets/img/lap-file.svg)

## Le document {#the-document}

Un seul objet JSON. Les canaux sont stockés en colonnes : un tableau par canal, tous de la même
longueur, une entrée par échantillon.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Champ | Signification |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | le jeu d'où vient le tour ; voir la liste ci-dessous |
| `track` | le nom du circuit, de l'étape ou de la carte, lorsque le jeu en envoie un |
| `layout` | Forza seulement : quelle disposition de paquet Data Out a été décodée |
| `car` | ce que le jeu dit de la voiture ; forme libre |
| `lap` | le numéro du tour, son temps tel que le jeu l'a compté (ou l'étendue des échantillons), s'il a été terminé, sa longueur |
| `meta` | comment lire les nombres ; voir plus bas |
| `units` | l'unité de chaque canal présent, pour un lecteur qui ne connaît pas le tableau ci-dessous |
| `channels` | les échantillons |
| `unparsed` | Forza seulement, lorsque le paquet contient des octets qu'aucun champ ne nomme : `ranges` (leurs décalages d'octets `[début, fin)` dans le paquet) et `hex` (par échantillon, ces octets en hexadécimal), pour que le fichier seul contienne le paquet entier |

`game` est l'une de ces valeurs : `forza-horizon`, `forza-motorsport`, `forza` (disposition du paquet
non distinguée), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`,
`assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`,
`richard-burns-rally`, `beamng`, `trackmania`.

`meta` indique ce que signifient les nombres là où les jeux diffèrent :

- `slip` : ce que contiennent les canaux de glissement, lorsque le jeu en envoie - `peak` (normalisé,
  donc au-delà de 1 le pneu lâche : Forza), `scaled` (un glissement physique divisé par un pic typique
  sur asphalte : les jeux Assetto Corsa), `physical` (une fraction et des radians), `index` (une mesure
  de glissement de 0 à 1 : Trackmania) ;
- `discipline` : `circuit`, `rally` ou `arcade` ;
- `surface` : `tarmac`, `loose`, `snow`, `ice` ou `mixed`, lorsqu'elle est connue (les enregistreurs de
  rallye la prennent de `--surface`).

## Canaux {#channels}

Un canal que le jeu n'envoie pas est absent, jamais rempli de zéros. Les canaux par roue portent la
roue après un point : `.FL`, `.FR`, `.RL`, `.RR`.

Les positions sont celles du monde du jeu, en mètres, avec `y` vers le haut. Un jeu dont le monde a Z
vers le haut est tourné pour avoir Y vers le haut par son enregistreur ; rien d'autre n'est modifié,
donc un monde gaucher (celui de Forza) reste gaucher.

| Canal | Unité | Signification |
|---|---|---|
| `time` | s | depuis le premier échantillon du tour |
| `distance` | m | le long du trajet parcouru depuis le premier échantillon |
| `x`, `y`, `z` | m | position ; `y` est la hauteur |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pédales et levier |
| `steer` | -1..1 | positif à droite |
| `gear` | | comme le jeu les compte |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | repère de la voiture |
| `yaw`, `pitch`, `roll` | rad | cap et attitude |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | vitesse dans le repère de la voiture : droite, avant, haut |
| `bodySlip` | rad | angle de dérive, lorsque le jeu l'envoie |
| `loose` | 0/1 | sur sol meuble (Trackmania) |
| `airborne` | 0/1 | aucune roue au sol |
| `rpm` | tr/min | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | comme le jeu les envoie |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | aides en action, systèmes activés |
| `absLevel`, `tcLevel` | | réglages d'aide |
| `brakeBias` | 0..1 | part à l'avant |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | par roue |
| `tirePressure` | psi | par roue |
| `tireWear` | 0..1 | par roue |
| `slipRatio`, `slipAngle`, `combinedSlip` | voir `meta.slip` | par roue |
| `slipIndex` | 0..1 | mesure de glissement par roue (Trackmania) |
| `camber` | rad | par roue |
| `brakeTemp` | °C | par roue |
| `padLife`, `discLife` | | par roue |
| `suspensionM` | m | débattement de la roue |
| `suspension` | 0..1 | débattement par roue, sur la plage utilisée dans ce tour |
| `wheelLoad` | N | par roue |
| `wheelSpeed` | rad/s | rotation par roue |
| `wheelSurfaceSpeed` | m/s | vitesse de l'aire de contact par roue |
| `groundContact` | 0/1 | par roue |
| `rumble`, `surfaceRumble` | | par roue : sur une bande sonore ; la vibration de la surface |
| `puddle` | | par roue : profondeur d'eau stagnante |

Un enregistreur peut ajouter ses propres canaux sous d'autres noms ; un lecteur conserve ceux qu'il ne
connaît pas.

Aucun jeu de rallye n'envoie le glissement des pneus. Un lecteur peut le calculer à partir de l'aire de
contact ou de la vitesse de surface de chaque roue comparée à la vitesse de la voiture,
`(roue - voiture) / voiture`, ou à partir de sa rotation et d'un rayon de roulement mesuré sur le tour
lui-même lorsque seule la rotation est envoyée. L'angle de dérive vient de la vitesse propre de la
voiture (`latVel`, `longVel`) lorsqu'elle est envoyée, ou de la vitesse du monde projetée sur les axes
de la voiture.

## La forme CSV {#the-csv-form}

Le plugin Trackmania écrit `heat3d-lap-csv` à la place : une première ligne commençant par `# ` suivie
d'un objet JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), une ligne de noms
de canaux, puis une ligne par échantillon. Les noms de canaux sont les mêmes que ci-dessus.

## Ce que chaque enregistreur écrit réellement {#what-each-recorder-actually-writes}

Le format ci-dessus est le contrat ; les enregistreurs le remplissent un peu différemment, et un
lecteur doit tolérer toutes ces variantes (vérifiées dans le code) :

| Enregistreur | `track` | `layout` | `meta` | `units` | Canaux au-delà du tableau |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (le numéro de circuit de Forza Motorsport 2023 est `lap.trackOrdinal`) | la disposition de paquet détectée | `slip: peak`, `discipline: circuit` | seulement les unités des canaux présents | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, l'horloge du jeu `timestampMs`, `raceTime`, `bestLap`, `lastLap` ; la vitesse locale à la voiture est sous les noms canoniques `latVel`, `vertVel`, `longVel` ; `unparsed` à côté des canaux |
| Jeux Assetto Corsa (`kunos.py`) | depuis la page statique, ou `null` | absent | `slip: scaled`, `discipline: circuit` ou `rally` | une liste fixe | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (tel qu'envoyé), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Jeux de rallye (`rally.py` via `lapfile.py`) | `null` | absent | `discipline: rally`, `slip: null`, `surface` seulement lorsque `--surface` a été donné (sinon la visionneuse le déduit) | seulement les unités des canaux présents | `stageDistance` ; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z` ; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` pour les flottants sans nom établi ; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | absent | `discipline: circuit` | seulement les unités des canaux présents | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Plugin Trackmania (CSV) | le nom de la carte | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` est le bloc voiture de Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` pour les jeux Kunos lorsque la page statique donne un nom, et
`{}` sinon. `lap.metres` est la différence de distance parcourue du compteur du jeu pour Forza, et la
somme des distances 3D entre échantillons ailleurs. Les valeurs sont arrondies à l'écriture : `time` à
4 décimales, `distance` à 3, les autres flottants à 5. Le JSON est écrit de façon compacte (sans espaces).

Chaque paquet ou page reçu par l'enregistreur - pas seulement ceux des tours - est conservé en entier à
côté des fichiers de tour, dans `<stamp>_<game>.raw.parquet`, avec un autocontrôle dans
`<stamp>_<game>.summary.json` (la section « Completeness » du README).

Un échantillon pour lequel un canal n'a pas de valeur - absent de cette image, ou pas un nombre fini tel
qu'envoyé par le jeu - est écrit `null` par chaque enregistreur (`lapfile.clean`), et la fraction de
suspension qui en découle est `null` aussi. `NaN` et `Infinity` ne sont jamais écrits : ce ne sont pas
du JSON, et le `JSON.parse` d'un navigateur refuse tout le fichier à cause de l'un d'eux. Un lecteur
doit s'attendre à trouver `null` dans le tableau d'un canal.

Les fichiers Forza portent `"game": "forza-horizon"`, `"forza-motorsport"` ou `"forza"` selon la
disposition détectée. Le lecteur de la visionneuse pour les fichiers `.tele.gz` de FH Companion produit
des tours avec `"game": "forza-horizon"` et `meta.slip = "peak"` ; ce lecteur est dans la visionneuse,
pas ici. Les tours iRacing (lus depuis `.ibt` dans la visionneuse) portent `"game": "iracing"`, qui ne
figure pas dans la liste des valeurs `game` des enregistreurs ci-dessus, car aucun enregistreur
n'écrit cette valeur.

Voir [Découpage des tours et des étapes](lap-splitting.md) pour la façon dont `lap.number`, `lap.seconds`
et `lap.complete` sont décidés, et [Glissement, dérive et canaux dérivés](slip-and-drift.md) pour ce que
la visionneuse déduit de ces canaux.
