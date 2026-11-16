---
title: "Enregistreurs de télémétrie"
nav_order: 3
lang: "fr"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Enregistreurs de télémétrie {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` enregistre chaque canal qu'un jeu envoie, découpe le flux en tours ou en étapes, et écrit un fichier JSON
[`heat3d-lap`](lap-format.md) par tour dans un dossier. L'onglet Analyse de course du visualiseur lit ces fichiers.
L'enregistrement continue jusqu'à ce que vous appuyiez sur **Ctrl+C** ; le tour ou l'étape ouvert à ce moment-là est écrit
s'il est assez long pour être conservé (voir [Découpage des tours et des étapes](lap-splitting.md)).

Code : [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
et les modules de [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Options {#options}

| Option | Par défaut | Signification |
|---|---|---|
| `--game` | `forza` | L'un de `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Dossier où les fichiers de tour sont écrits. Créé s'il n'existe pas. Ignoré par `trackmania`, dont le plugin écrit lui-même les fichiers. |
| `--port` | `5300` | Port UDP d'écoute. **Pour tous les jeux sauf Forza, la valeur 5300 signifie « le port par défaut du jeu » : 20777 pour `wrc` et les jeux DiRT, 6776 pour `rbr`, 4460 pour `beamng`.** Donnez un autre nombre pour le modifier. Non utilisé par les jeux Assetto Corsa (mémoire partagée) ni par Trackmania (fichiers). |
| `--forward` | aucun | Forza seulement : `hôte:port` vers lequel transmettre chaque paquet reçu, sans modification. `127.0.0.1:5301` pour FH Companion. Un simple `:5301` signifie `127.0.0.1:5301`. |
| `--install` | désactivé | `beamng` : copie d'abord le mod de protocole dans les mods décompressés de BeamNG. `trackmania` : copie le plugin Openplanet dans le dossier des plugins d'Openplanet. Ignoré par les autres jeux. |
| `--configure` | aucun | `wrc` seulement : chemin vers le `config.json` de télémétrie d'EA SPORTS WRC ; active le paquet `wrc` par défaut avant l'enregistrement (sauvegardé d'abord). |
| `--surface` | aucun | Jeux de rallye (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`) : `tarmac`, `loose`, `snow`, `ice` ou `mixed`, écrit dans `meta.surface` du fichier de tour. Sans lui, aucune surface n'est écrite. |

## Les jeux en un coup d'œil {#the-games-at-a-glance}

| `--game` | Jeu | Source | Port par défaut | Découpage | `game` dans le fichier | Page |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (y compris 2023) | UDP Data Out | 5300 | le compteur de tours du jeu (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, ou `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | mémoire partagée `acpmf_*` | - | compteur de tours (`CounterSplitter`) | `assetto-corsa` | [Jeux Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | mémoire partagée `acpmf_*` | - | compteur de tours (`CounterSplitter`) | `assetto-corsa-competizione` | [Jeux Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | mémoire partagée `acevo_pmf_*` | - | ligne de départ (`LineSplitter`) | `assetto-corsa-evo` | [Jeux Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | mémoire partagée `acpmf_*` | - | ligne de départ / arrêt (`LineSplitter`) | `assetto-corsa-rally` | [Jeux Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, structure `wrc` | 20777 | horloge d'étape (`StageSplitter`) | `ea-sports-wrc` | [Jeux de rallye](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | horloge d'étape (`StageSplitter`) | `dirt-rally-2` | [Jeux de rallye](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | horloge d'étape (`StageSplitter`) | `dirt-rally` | [Jeux de rallye](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | horloge d'étape (`StageSplitter`) | `dirt-4` | [Jeux de rallye](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | UDP NGP | 6776 | horloge d'étape (`StageSplitter`) | `richard-burns-rally` | [Jeux de rallye](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod de protocole `heat3d`, UDP | 4460 | ligne de départ (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanet, fichiers CSV | - | par course, dans le plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | ses propres fichiers `.ibt`, lus par le visualiseur | - | le compteur de tours du simulateur | `iracing` | [iRacing](telemetry-iracing.md) |

## État {#status}

L'enregistreur Forza est celui qui a été le plus exercé. Les enregistreurs Kunos, rallye, BeamNG et Trackmania sont construits à partir des
dispositions publiées et testés sur des paquets synthétiques et des pages construites à partir de ces dispositions (`tests/test_kunos.py`,
`tests/test_rally.py`, `tests/test_beamng.py`) ; **aucun d'eux n'a encore été lancé contre le jeu en direct**. Les enregistreurs capables de
vérifier leur entrée le font au fur et à mesure de l'arrivée des paquets, et affichent une seule fois une `note:` lorsque quelque chose ne
correspond pas (EA WRC et DiRT comparent la vitesse du monde à la vitesse ; EA WRC signale aussi un paquet plus court que la structure par défaut
de 237 octets). [Jeux](games.md) liste les sources et ce qui n'est pas encore confirmé pour chaque jeu.

## Pendant l'enregistrement {#while-it-runs}

- **Forza** affiche une ligne d'état chaque seconde : paquets reçus, et le numéro du tour en cours, le nombre d'échantillons et les mètres, ou
  `waiting for a race` (en attente d'une course). Chaque tour terminé affiche `wrote <file>`.
- **Les jeux Assetto Corsa** affichent le nom de chaque fichier de tour à mesure qu'il est écrit.
- **Les jeux de rallye** affichent `listening for <game> on port <port>` (à l'écoute de <jeu> sur le port <port>), puis `stage written: <file>` ;
  à Ctrl+C, une étape ouverte assez longue pour être conservée est écrite sous `partial stage written: <file>`.
- **BeamNG** affiche `lap written: <file>`, et à Ctrl+C `run written: <file>`.
- **Trackmania** n'affiche rien par course : le plugin écrit lui-même ses fichiers CSV.
- À la fin, chaque enregistreur affiche le nombre de fichiers qu'il a écrits.

Un enregistrement Forza, ici alimenté par des paquets Data Out Forza synthétiques d'une voiture qui fait deux tours d'un cercle de 150 m (les fichiers
de tour, le fichier brut annexe et le résumé d'autocontrôle qu'il laisse) :

![Enregistrement de télémétrie de deux tours d'un flux Forza synthétique](../assets/img/telemetry-run.svg)

## Noms de fichiers {#file-names}

| Enregistreur | Modèle |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Jeux Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Jeux de rallye, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, où `<game>` est le nom long (`ea-sports-wrc`, `beamng`, ...), `stage` pour le rallye et `lap` pour BeamNG |
| Plugin Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` contre `run` (Forza, Assetto Corsa) et le suffixe `_partial` (rallye, BeamNG) indiquent si le tour ou l'étape a été terminé. L'horodatage est
celui de l'écriture du fichier, et non celui du début du tour.

À côté des fichiers de tour, chaque enregistreur écrit `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - chaque paquet ou page reçu, conservé en entier, y
compris dans les menus et entre les tours - et `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, l'autocontrôle : pour chaque type de paquet, combien sont
arrivés, combien sont entrés dans des fichiers de tour, et `lost`, qui vaut 0. Le visualiseur ignore ces deux fichiers lorsqu'un dossier est chargé.
Voir [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) dans le README.

## Pages de cette rubrique {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Jeux Assetto Corsa](telemetry-assetto-corsa.md)
- [Jeux de rallye](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Découpage des tours et des étapes](lap-splitting.md)
- [Glissement, dérive et canaux dérivés](slip-and-drift.md)
- [Le fichier heat3d-lap](lap-format.md)
