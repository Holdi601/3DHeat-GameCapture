---
title: BeamNG.drive
nav_order: 4
lang: "fr"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copie le mod, puis enregistre
python -m heat3d_capture telemetry --game beamng -o laps      # enregistre
```

Ensuite, dans le jeu : **Options > Autre > Protocoles**, activez **« others »**.

Code : [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
et le mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tests : `tests/test_beamng.py`, sur des paquets construits à partir de la structure du mod. **Le mod n'a
pas encore été lancé dans le jeu.**

## Pourquoi un mod {#why-a-mod}

BeamNG envoie sa télémétrie par des « protocoles » : des modules Lua dans le véhicule, que le fichier
`lua/vehicle/protocols.lua` du jeu lui-même empaquette et envoie en UDP depuis la voiture conduite par le
joueur. Les protocoles d'origine ne contiennent pas ce qu'exige l'analyse de conduite - OutGauge n'a pas
de position, MotionSim n'a pas les roues, et OutSim n'est qu'un squelette dans les versions actuelles. Ce
projet livre donc son propre protocole, `heat3d`. Il ne touche à rien en dehors du Lua du véhicule.

## Installation {#installing}

`--install` copie `mods/beamng/heat3d` vers
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 et les versions
ultérieures y rangent les mods de l'utilisateur), en supprimant d'abord une copie plus ancienne, et
affiche l'endroit où elle a été copiée. Sans `LOCALAPPDATA`, il se replie sur le dossier personnel. Vous
pouvez aussi copier le dossier à la main.

`--install` enchaîne ensuite directement sur l'enregistrement.

## Le mod {#the-mod}

| Réglage (dans `heat3d.lua`) | Valeur |
|---|---|
| Adresse | `127.0.0.1` |
| Port | `4460` - modifiez-le ici et passez le même `--port` à l'enregistreur |
| Fréquence de mise à jour maximale | 100 Hz |
| Pas de physique | utilisé (`isPhysicsStepUsed` renvoie vrai) |

Chaque paquet est composé du marqueur de 4 octets `H3D1`, suivi de 39 flottants en petit-boutiste (160
octets au total) :

| Champ | Nombre | Source dans le Lua du véhicule |
|---|---|---|
| `time` | 1 | l'horloge propre du mod : somme des pas de physique, remise à zéro quand le véhicule est réinitialisé |
| position | 3 | `obj:getPositionXYZ()` |
| vitesse | 3 | `obj:getVelocityXYZ()` (monde) |
| avant | 3 | `obj:getDirectionVector()` |
| haut | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values` : `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, et 1/0 issus de `absActive` et `tcsActive` |
| `wheelSpeed` | 4 | vitesse de surface de chaque roue (m/s) |
| `wheelAngular` | 4 | vitesse angulaire multipliée par le sens de rotation de la roue (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 lorsque la roue ne touche pas le sol |

Les quatre roues sont choisies selon **leur place sur la voiture**, et non selon leur nom (les noms
diffèrent d'un véhicule à l'autre) : avant ou arrière selon la position du nœud le long de la voiture,
gauche ou droite selon sa position en travers (repère du véhicule : +X à gauche, -Y vers l'avant), en
prenant pour chaque coin la roue la plus éloignée du centre. Un coin manquant est envoyé à zéro, avec le
matériau -1.

## Ce que fait l'enregistreur {#what-the-recorder-does-with-it}

Le monde de BeamNG a Z vers le haut ; celui du visualiseur a Y vers le haut. Les positions et les
vecteurs tournent autour de X, `(x, y, z) -> (x, z, -y)`, ce qui conserve le sens du système du monde.
Ensuite :

| Canal | Calculé comme |
|---|---|
| `x`, `y`, `z` | position tournée |
| `speed` | longueur de la vitesse tournée |
| `longVel`, `latVel`, `vertVel` | vitesse projetée sur l'avant, sur la droite (= avant x haut), sur le haut |
| `longAcc`, `latAcc`, `vertAcc` | variation de la vitesse monde sur ±2 échantillons, projetée sur les mêmes axes (le repère des capteurs de la voiture n'est pas documenté, ils ne sont donc pas utilisés) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | tels qu'envoyés |
| `absActive`, `tcActive` | les témoins ABS et TC, lorsque la voiture en a |
| `wheelSurfaceSpeed.*` | valeur absolue de la vitesse de surface de la roue |
| `wheelSpeed.*` | rotation |
| `wheelLoad.*` | charge |
| `groundContact.*` | 0 lorsque le matériau est négatif, sinon 1 |

Les paquets sans le marqueur, ou plus courts que 160 octets, sont ignorés.

## Tours {#laps}

`LineSplitter`, comme pour AC EVO : le point où l'enregistrement a commencé est la ligne ; un tour se
ferme au moment où la voiture repasse au plus près de ce point en roulant dans le même sens, au moins 300
m plus tard ; une course se ferme lorsque la voiture reste immobile pendant 8 secondes. Un tour ne compte
comme complet que s'il a commencé à plus de 5 m/s, si bien que le premier tour parti de l'arrêt est
partiel. Lorsque l'horloge du mod recule de plus d'une demi-seconde (la voiture a été réinitialisée), la
course ouverte à cet instant est d'abord fermée - écrite comme course partielle si elle a couvert au moins
300 m, comme à la fin d'un enregistrement - puis le découpage recommence. Voir
[Découpage des tours et des étapes](lap-splitting.md).

## Le fichier de tour {#the-lap-file}

`game` vaut `beamng`, `meta` vaut `{"discipline": "circuit"}`, et les fichiers portent le nom
`beamng_<horodatage>_lap<n>_<secondes>s[_partial].json`. Aucun glissement n'est écrit ; le visualiseur le
calcule à partir des vitesses de surface des roues (voir [Glissement, dérive et canaux dérivés](slip-and-drift.md)).
Les positions sont dans le même repère que celui qu'écrit l'export de parcours BeamNG de GameFiles ; un tour
enregistré se pose donc sur un parcours exporté.
