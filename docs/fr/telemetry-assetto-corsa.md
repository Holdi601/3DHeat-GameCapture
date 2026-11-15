---
title: "Assetto Corsa, ACC, AC EVO et AC Rally"
nav_order: 2
lang: "fr"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO et AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Code : [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tests : `tests/test_kunos.py` (pages synthétiques). Pas encore lancé contre les jeux en direct.

## D'où viennent les données {#where-the-data-comes-from}

Les jeux de Kunos publient leur télémétrie pour les applications sous forme de **pages de mémoire partagée Windows nommées**, que
le jeu écrit et que n'importe qui peut lire. L'enregistreur les ouvre en lecture seule (`mmap` avec un nom d'étiquette), il doit donc
tourner **sur le PC où tourne le jeu**, sous Windows ; ailleurs, il quitte avec un message. Les pages sont ouvertes une seule fois, au
démarrage de l'enregistreur. Lancer le jeu et monter dans la voiture avant est l'ordre sûr ; que lancer l'enregistreur avant le jeu
fonctionne n'a pas été vérifié.

| `--game` | Page physique | Page graphique (compteur de tours) | Page statique (noms) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | non utilisée | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | non utilisée | `Local\acevo_pmf_static` |

La page physique est lue 200 fois par seconde (`hz=200`) ; un nouvel échantillon n'est pris que lorsque son `packetId` a changé et
n'est pas nul. Les 800 premiers octets de la page physique ont la même disposition dans les quatre jeux ; la page du premier jeu n'est
garantie que sur 580 octets, donc si un mappage de 800 octets ne peut pas être ouvert, l'enregistreur retombe sur 580, et les champs
au-delà sont absents.

## Position {#position}

Aucune page ne porte la position de la voiture en tant que telle, mais la page physique contient **le point de contact de chaque pneu en
coordonnées du monde** (décalage 420, quatre triplets XYZ). La position de la voiture est la moyenne des quatre. Une page dont tous les
points de contact sont à zéro (menu, garage) ne produit aucun échantillon.

## Canaux {#channels}

| Canal | Source | Remarques |
|---|---|---|
| `time` | l'horloge propre de l'enregistreur | secondes depuis le début de l'enregistrement, recalées sur le premier échantillon du tour |
| `x`, `y`, `z` | point de contact moyen des pneus | mètres du monde |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | les unités du jeu, mises à l'échelle par tour à -1..1 selon la plus grande valeur absolue utilisée dans le tour, **seulement si** cette valeur dépasse 1,05 (une commande déjà entre -1 et 1 est laissée telle quelle) |
| `gear` | `gear - 1` | le jeu compte 0 marche arrière, 1 point mort, 2 première ; écrit -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, multiplié par 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | vitesse locale au décalage 568 | repère de la voiture ; seulement lorsqu'elle est non nulle. Le côté vers lequel pointe x est documenté dans les deux sens : lisez donc la taille de l'angle de dérive, pas son signe |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | décalage 564 | page de 800 octets seulement |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally : décalages 204 et 252, écrits 1 lorsqu'ils sont supérieurs à 0 ; AC : `tcInAction`/`absInAction` de la page de 800 octets lorsqu'elle est présente | aides en action |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | dérivé | 0..1 du débattement utilisé dans ce tour (min à max de `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | décalages 640, 656 (page de 800 octets) | divisés par un pic typique - voir plus bas |
| `slipRatioRaw.*`, `slipAngleRaw.*` | les mêmes | les valeurs physiques, non mises à l'échelle |
| `padLife.*`, `discLife.*` | décalages 740, 756 | page de 800 octets seulement |

AC Rally envoie ses températures de pneus et de freins en kelvins : pour `--game acrally`, toute valeur de ces températures supérieure à
200 a 273,15 retranché.

`wheelSlip` (décalage 56) est décodé mais non écrit.

## Mise à l'échelle du glissement {#slip-scaling}

Forza envoie le glissement normalisé pour que 1 soit le bord de l'adhérence. Kunos envoie le taux et l'angle de glissement physiques.
L'enregistreur les divise donc par un pic typique sur asphalte - **0,12** pour le taux de glissement et **0,14 rad (environ 8 degrés)** pour
l'angle de glissement - afin que la lecture « au-delà de 1 signifie qu'il glisse » de la visionneuse reste à peu près vraie, conserve les
valeurs brutes à côté, et écrit `"meta": {"slip": "scaled"}`. Là où l'adhérence cède réellement, la visionneuse la mesure voiture par
voiture à partir des tours. Voir [Glissement, dérive et canaux dérivés](slip-and-drift.md).

## Tours {#laps}

- **AC et ACC** comptent les tours sur la page graphique (`completedLaps` au décalage 132, le temps du dernier tour en millisecondes à 144).
  `CounterSplitter` ferme un tour lorsque le compteur change ; il est marqué complet, avec le temps du jeu, seulement si le compteur a
  augmenté exactement de un.
- **AC EVO et AC Rally** ne sont pas lus pour les tours (la page graphique d'EVO est une disposition différente et plus grande ; AC Rally
  conduit des étapes). `LineSplitter` utilise comme ligne le point où l'enregistrement a commencé : un tour se ferme lorsque la voiture
  repasse au plus près de ce point en roulant dans le même sens, et une étape ou une course quelconque se ferme lorsque la voiture reste
  immobile pendant 8 secondes.

Détails et seuils : [Découpage des tours et des étapes](lap-splitting.md).

## Noms de la piste et de la voiture {#track-and-car-names}

Lus une fois, à partir de la page statique, à l'arrivée du premier échantillon : pour AC, ACC et AC Rally, la voiture (UTF-16, décalage 68)
et la piste (décalage 134) ; pour AC EVO, la piste et sa configuration (texte sur un octet aux décalages 136 et 169, réunis par un espace)
et pas de voiture. Ils sont écrits dans le fichier sous `track` et `car: {"name": ...}`.

## Le fichier de tour {#the-lap-file}

`game` vaut `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ou `assetto-corsa-rally` ; `meta` vaut
`{"slip": "scaled", "discipline": "rally"}` pour AC Rally et `{"slip": "scaled", "discipline": "circuit"}` pour les trois autres. Aucun
`surface` n'est écrit.

## Sources {#sources}

Le SDK de mémoire partagée d'AC1 ; la documentation de mémoire partagée d'ACC (v1.8) ; la disposition d'AC EVO telle que mesurée dans
`albertowd/live-telemetry-evo` ; celle d'AC Rally telle que lue par `LuizZak/AssettoCorsaRallyTelemetryReader`. Voir [Jeux](games.md).
