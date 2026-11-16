---
title: "EA SPORTS WRC, DiRT Rally 2.0, DiRT Rally, DiRT 4, Richard Burns Rally"
nav_order: 3
lang: "fr"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # ou dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Code : [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tests : `tests/test_rally.py`, sur des paquets construits à partir des dispositions documentées. **Pas encore lancé contre
les jeux en direct.**

Tous envoient de l'UDP que le jeu active depuis ses propres fichiers de réglages. L'enregistreur écoute sur toutes les interfaces
(`0.0.0.0`) sur le port par défaut du jeu, sauf si `--port` en donne un autre : **20777** pour `wrc`, `dirtrally2`, `dirtrally`, `dirt4` ;
**6776** pour `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Activer {#switching-it-on}

Le jeu lit `Documents\My Games\WRC\telemetry\config.json`. Le paquet `session_update` de la structure `wrc` par défaut doit être activé
vers cette machine :

```bash
python -m heat3d_capture telemetry --game wrc --configure "<chemin vers config.json>"
```

`--configure` (fonction `configure_wrc`) :

- lit le JSON, trouve `udp.packets` et l'entrée avec `"structure": "wrc"` et `"packet": "session_update"` ;
- si elle est déjà activée vers `127.0.0.1` ou `localhost` sur le port utilisé, affiche `already on` et ne change rien ;
- sinon, règle `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, et conserve le `frequencyHz` de l'entrée (ou `-1` s'il n'y en a pas) ;
  s'il n'existe pas d'entrée de ce type, en ajoute une ;
- écrit le texte d'origine dans `config.json.bak` à côté, puis écrit le nouveau fichier (indentation de 4 espaces).

Redémarrez le jeu après avoir modifié le fichier s'il ne le prend pas en compte (non vérifié).

### Ce qu'il envoie {#what-it-sends}

La structure `wrc` par défaut fait 237 octets, en little-endian, sans en-tête : position, vitesse et accélération du monde (X à gauche, Y
vers le haut, Z vers l'avant) dans le monde, les vecteurs unitaires gauche / avant / haut de la voiture, par roue (arrière gauche, arrière
droite, avant gauche, avant droite) la hauteur du moyeu et sa vitesse verticale ainsi que la vitesse avant de l'aire de contact, les températures
de freins, les pédales après les aides, la direction (-1 gauche, +1 droite), le frein à main, le régime, le rapport, et l'horloge d'étape, la
distance et la longueur. Un paquet de moins de 237 octets est ignoré et signalé une seule fois.

| Canal | Source |
|---|---|
| `x`, `y`, `z` | position du monde |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | vitesse du monde projetée sur l'avant, sur la droite, l'opposé de la gauche (donc positive vers la droite), sur le haut |
| `longAcc`, `latAcc`, `vertAcc` | accélération du monde projetée de la même façon |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | tels qu'envoyés |
| `gear` | `gear_index` ; -1 lorsqu'il égale l'indice de marche arrière, 0 lorsqu'il égale l'indice du point mort |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | position du moyeu |
| `wheelSurfaceSpeed.*` | vitesse avant de l'aire de contact |
| `brakeTemp.*` | température des freins |

Contrôle : si `speed` dépasse 10 et que la longueur de la vitesse du monde diffère de plus de 20 % de cette valeur, l'enregistreur affiche
une seule fois que la disposition n'est peut-être pas la structure `wrc` par défaut.

Une étape est **terminée** lorsque la longueur d'étape est positive et que la distance a atteint la longueur moins 0,5 m. L'horloge utilisée pour
le découpage et pour `time` est `stage_time`.

Sources : EA's UDP Telemetry Guide v1.3 ; la liste des canaux que le jeu écrit dans `readme/channels.json` ; les décalages tels que décodés par
nobonobo/obs-codemasters-telemetry et SpaceMonkey. Le port par défaut d'origine n'est pas documenté ; l'enregistreur utilise 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Activer {#switching-it-on-1}

Modifiez `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally et DiRT 4 utilisent aussi un
`hardware_settings_config.xml` ; leur dossier exact pour ces deux-là n'a pas été vérifié ici) pour que l'élément `udp` soit :

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` fait entrer les positions, les roues et la longueur d'étape dans le paquet. L'enregistreur ne modifie pas ce fichier.

### Ce qu'il envoie {#what-it-sends-1}

66 flottants en little-endian (DiRT Rally : 64) ; les paquets de moins de 64 flottants sont ignorés, et un paquet de 64 flottants est complété
de zéros. Les indices utilisés :

| Indice | Champ | Canal |
|---|---|---|
| 1 | temps de tour (étape) | l'horloge de découpage et `time` |
| 2 | distance du tour | `stageDistance` |
| 4-6 | position du monde | `x`, `y`, `z` |
| 7 | vitesse | `speed` |
| 8-10 | vitesse du monde | `longVel` (sur l'avant), `latVel` (sur le vecteur latéral) |
| 11-13 | vecteur latéral | |
| 14-16 | vecteur avant | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | position de suspension arrière gauche, arrière droite, avant gauche, avant droite | `suspensionM.*` |
| 25-28 | vitesse de l'aire de contact des roues arrière gauche, arrière droite, avant gauche, avant droite | `wheelSurfaceSpeed.*` |
| 29-33 | accélérateur, direction, frein, embrayage, rapport | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ou plus signifie la marche arrière, écrit -1) |
| 34, 35 | accélérations latérale et longitudinale en g | `latAcc`, `longAcc` (multipliés par 9,80665) |
| 37 | régime / 10 | `rpm` (multiplié par 10) |
| 51-54 | températures de freins | `brakeTemp.*` |
| 59, 60, 61, 62 | tours effectués, tours totaux, longueur de circuit, temps du dernier tour | découpage |

Il n'y a **pas de canal de frein à main**. Le sens du vecteur latéral est documenté dans les deux sens, donc le signe de `latVel` ne doit pas
être utilisé tel quel (le visualiseur lit la taille de l'angle de dérive).

Une étape est **terminée** lorsque le nombre de tours effectués dépasse sa valeur au départ de l'étape (un tour de rallycross à chaque fois), ou,
pour un événement d'un seul tour, lorsque la distance du tour atteint 99,9 % de la longueur du circuit. Le temps de l'étape est le temps du dernier
tour du jeu lorsqu'il est positif. Contrôle : vitesse comparée à `speed` comme pour EA WRC, avec le message « is extradata set to 3? » (extradata
est-il réglé sur 3 ?).

Sources : le document UDP de DiRT 4 de Codemasters ; ErlerPhilipp/dr2_logger ; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Activer {#switching-it-on-2}

Dans `RichardBurnsRally.ini`, section `[NGP]` : `udpTelemetry=1` et l'adresse de destination (127.0.0.1, port 6776 sauf si vous passez un autre
`--port`). L'enregistreur ne modifie pas ce fichier.

### Ce qu'il envoie {#what-it-sends-2}

664 octets (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`) : horloge d'étape et distance jusqu'à l'arrivée, pédales, direction, rapport,
position du monde, attitude, les vitesses propres de la voiture (avance vers l'avant, balancement latéral, pilonnement), accélérations, régime, et
quatre blocs de roue de 128 octets (AV gauche, AV droite, AR gauche, AR droite) avec la déflexion et la force des ressorts. Pas de vitesses de roue.

| Canal | Source |
|---|---|
| `x`, `y`, `z` | position, axes tels qu'envoyés, puis réordonnés (ci-dessous) |
| `longVel`, `latVel`, `vertVel` | avance, balancement, pilonnement |
| `longAcc`, `latAcc` | accélération x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | tels qu'envoyés |
| `gear` | `gear - 1` (0 marche arrière, 1 point mort, 2 première) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | déflexion du ressort |
| `wheelLoad.*` | force du ressort |
| `speed` | **calculée à partir des positions** sur ±2 échantillons, non reprise du paquet |

Les axes de position, les unités d'attitude et l'unité de vitesse de RBR ne sont pas documentés ; donc, à l'écriture d'une étape, l'axe le moins
variable le long de l'étape est pris pour le haut et permuté dans `y` (`orient_up`, il faut au moins 10 échantillons), et la vitesse est recalculée
à partir des positions (`speed_from_positions`). L'attitude est décodée mais non écrite, donc les fichiers RBR n'ont pas de `yaw`.

Une étape est **terminée** lorsque l'horloge de course tourne et que la distance jusqu'à l'arrivée atteint zéro. L'horloge est `race_time`.

Sources : `rbr.telemetry.data.TelemetryData.h` de NGP, via mika-n/RBRUDPTelemetryLogger et groybe/rbr-udp-telem.

## Étapes {#stages}

Les cinq utilisent `StageSplitter` sur l'horloge d'étape du jeu : une étape s'ouvre lorsque l'horloge démarre, se ferme complète lorsque le jeu
indique que la voiture a terminé, et une horloge qui recule (un redémarrage, ou l'étape suivante) abandonne l'étape ouverte - conservée comme
fichier `_partial` si elle compte plus de 10 échantillons et au moins 300 m. Les étapes terminées de moins de 300 m ne sont pas écrites. Détails :
[Découpage des tours et des étapes](lap-splitting.md).

## Le fichier de tour {#the-lap-file}

`game` vaut `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ou `richard-burns-rally`. `meta` vaut
`{"discipline": "rally", "slip": null}`, plus `"surface": "<valeur>"` lorsque `--surface` a été donné. `slip` est nul parce qu'aucun de ces jeux
n'envoie de glissement des pneus. La vitesse de l'aire de contact de chaque roue (EA WRC, DiRT) est en revanche dans le fichier ; le visualiseur en
déduit le glissement et l'angle de dérive à partir d'elle et des axes de la voiture ; voir [Glissement, dérive et canaux dérivés](slip-and-drift.md).
Les canaux `suspension.*` (0..1 du débattement utilisé) sont ajoutés à partir de `suspensionM.*`.

Lorsque aucun `--surface` n'est donné, le fichier ne contient volontairement aucune surface : une valeur par défaut écrite ici remplacerait l'inférence
propre au visualiseur. Celui-ci prend alors la surface du nom de l'étape ou de l'événement (rallyes sur asphalte, rallyes d'hiver, le Monte en mixte),
sinon d'après la façon dont la voiture a été conduite sur elle (les virages appuyés à petit angle de dérive indiquent l'asphalte), et « meuble » lorsque rien
ne l'indique - ce qu'est le plus souvent une étape de rallye. Donnez `--surface` lorsque vous en savez davantage.
