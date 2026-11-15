---
title: Trackmania
nav_order: 5
lang: fr
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Code : le plugin Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Le plugin n'a pas encore été lancé dans le jeu** ; le lecteur de son CSV dans
la visionneuse est testé.

## Pourquoi un plugin qui écrit des fichiers {#why-a-plugin-that-writes-files}

Trackmania n'a pas de sortie de télémétrie propre. Openplanet, la plateforme de plugins du jeu, expose à
ceux-ci l'état du véhicule regardé, mais les plugins Openplanet ne peuvent pas envoyer d'UDP. Le plugin
écrit donc un fichier CSV par course dans son propre dossier de stockage, et la visionneuse lit ces
fichiers tels quels. Il n'y a pas de processus d'enregistrement : `telemetry --game trackmania` se contente
d'installer le plugin (avec `--install`) et d'indiquer où apparaîtront les fichiers.

## Installation et chargement {#installing-and-loading}

- `--install` copie `mods/trackmania/Heat3dRecorder` vers
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, en remplaçant une copie plus ancienne. Sans
  `--install`, rien n'est copié.
- Dans le jeu : **Openplanet > Developer > Load plugin**, puis choisissez `3DHeat recorder`.
- Le plugin dépend du plugin **VehicleState** d'Openplanet (`dependencies = ["VehicleState"]` dans
  `info.toml`).
- Les plugins non signés ne se chargent que dans le **mode développeur d'Openplanet**, qui limite le jeu en
  ligne. Le plugin peut être signé sur openplanet.dev ; il ne l'est pas ici.

Les courses sont écrites dans `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Chargez ces
fichiers CSV dans l'onglet Analyse de course de la visionneuse. `-o` et `--port` sont ignorés pour
Trackmania.

## Ce que le plugin enregistre {#what-the-plugin-records}

Il ne lit que ce qu'Openplanet expose - l'état du véhicule regardé
(`VehicleState::ViewingPlayerState()`) et le temps de course du joueur ainsi que son nombre de
réapparitions (`CSmScriptPlayer`) - n'envoie rien nulle part et ne modifie rien dans le jeu. Une ligne est
écrite à chaque image (`Update`), si bien que la fréquence d'échantillonnage est celle du jeu.

| Colonne | Source |
|---|---|
| `time` | `CurrentRaceTime` / 1000, en secondes |
| `x`, `y`, `z` | `Position` (monde, Y vers le haut) |
| `speed` | longueur de `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ou 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` de chaque roue (une mesure de glissement de 0 à 1) |
| `loose` | 1 lorsqu'une roue touche un matériau Grass, Ice, Sand, Dirt, Green ou RoadIce |
| `airborne` | 1 lorsque la voiture ne touche plus le sol |
| `respawns` | réapparitions depuis le début de la course |

## Courses {#runs}

- Une course **commence** à la première image où le temps de course n'est pas négatif (le compte à rebours
  n'est pas enregistré).
- Elle **se termine** lorsque la séquence d'interface du playground est la séquence d'arrivée (valeur 11) :
  le fichier est écrit comme complet, avec le dernier temps de course comme `seconds`.
- Elle est **abandonnée** - écrite avec `_partial` dans le nom et `"complete": false` - lorsque l'horloge de
  course recule de plus d'une demi-seconde (un redémarrage), ou lorsque le joueur quitte le playground.
- Une course de moins de 20 lignes n'est pas écrite.

## Le fichier {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Nommé `run_<AAAA-MM-JJ_HH-MM-SS>[_partial].csv`. Le nom de la map a ses codes de mise en forme retirés, et
ses guillemets doubles sont remplacés par des guillemets simples. Les valeurs sont écrites avec quatre
décimales. Le format est décrit dans [Le fichier heat3d-lap](lap-format.md#the-csv-form).

Le `meta` de l'en-tête porte `"slip": "index"` - les canaux `slipIndex.*` sont la mesure de glissement de
0 à 1 propre à Trackmania, et non un glissement physique - et `"discipline": "arcade"`.
