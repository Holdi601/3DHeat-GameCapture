---
title: Les règles
nav_order: 2
lang: "fr"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Les règles sur lesquelles ceci est construit {#the-rules-this-is-built-under}

Chaque partie de 3DHeat GameCapture suit les mêmes contraintes. Ce sont des décisions de conception, pas
des avertissements, et plusieurs d'entre elles coûtent de la précision à dessein.

## Rien n'est injecté, rien n'est accroché {#nothing-is-injected-nothing-is-hooked}

Aucune partie de ceci ne se rattache à un processus de jeu, ne lit sa mémoire, ni ne touche à son API
graphique.

- Les **images** viennent de Windows Graphics Capture, l'API publique qu'utilisent les enregistreurs
  d'écran (via le paquet `windows-capture`), ou d'un fichier vidéo. Voir
  [Capture, masques et qualité d'image](reconstruction-capture.md).
- La **télémétrie** ne vient que des interfaces que les jeux publient à cet effet :
  - le flux UDP Data Out de Forza, activé dans les réglages du jeu ;
  - les pages de mémoire partagée nommées que publient les jeux Kunos à l'intention des applications
    (`Local\acpmf_physics` et autres). Elles sont ouvertes en lecture seule avec `mmap` ; c'est la façon
    documentée dont les applications les lisent, et non une lecture de la mémoire du processus de jeu ;
  - l'UDP qu'envoient EA SPORTS WRC, les jeux DiRT et Richard Burns Rally (par le plugin RSF/NGP), une
    fois activé dans leurs propres fichiers de réglages ;
  - l'interface de protocole de BeamNG, par un petit « protocole » Lua qui est chargé et envoyé par le
    `lua/vehicle/protocols.lua` du jeu lui-même ;
  - l'interface de plugin Openplanet de Trackmania, par un plugin qui ne lit que ce qu'Openplanet expose
    et n'écrit que des fichiers ;
  - les fichiers de télémétrie `.ibt` propres à iRacing.

## Pourquoi cela compte {#why-it-matters}

Le jeu connaît exactement la profondeur de chaque pixel, et un tampon de profondeur accroché rendrait la
reconstruction de niveau presque parfaite et triviale. Cela impliquerait aussi d'injecter du code dans
des processus qui peuvent être protégés par un système anti-triche, ce qui met en danger le compte de
quiconque l'exécute. La profondeur est donc **estimée** à partir de l'image ([Profondeur](reconstruction-depth.md)),
et une grande partie du pipeline de reconstruction existe pour retrouver le plus possible de cette
précision perdue à partir de sources librement utilisables : les poses de télémétrie là où un jeu les
publie, une échelle fondée sur le plan de sol là où il ne les publie pas, et des masques qui gardent le
HUD et le cockpit hors de la résolution.

Le tampon de profondeur de ReShade a été envisagé et n'a pas été retenu. ReShade désactive l'accès à la
profondeur dans les sessions multijoueur par conception ; il n'aiderait donc que les titres solo (voir
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Ce que l'outil modifie sur votre machine, et seulement sur demande {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Action | Quand | Ce qui exactement |
|---|---|---|
| Installe des paquets Python | la première exécution de la fenêtre de scan, après une boîte de dialogue et un oui | `pip install` dans l'interpréteur qui exécute l'outil - avec `scan.bat`, le `.venv` privé à côté de lui. Jamais à l'échelle du système par lui-même. |
| Convertit le modèle de profondeur | le bouton « Set up the depth model », après une seconde boîte de dialogue pour PyTorch et consorts | écrit `models/depth-small-518.onnx` |
| Modifie le `config.json` de EA SPORTS WRC | `telemetry --game wrc --configure <fichier>` | active le paquet `wrc` / `session_update` vers 127.0.0.1 ; l'ancien fichier est conservé sous le nom `config.json.bak` |
| Copie le mod BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` vers `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (remplace une copie plus ancienne) |
| Copie le plugin Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` vers `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (remplace une copie plus ancienne) |
| Enregistre des raccourcis globaux | pendant que la fenêtre de scan est ouverte (Windows) | Ctrl+Alt+F9 / F10 / F11, libérés à la fermeture de la fenêtre |
| Met à jour l'outil | après un oui à la question de mise à jour, ou en lançant `python -m heat3d_update` | voir [Mises à jour](updates.md) |

Les fichiers `hardware_settings_config.xml` des jeux DiRT et `RichardBurnsRally.ini` de Richard Burns
Rally ne sont **pas** modifiés par l'outil ; vous activez vous-même leur sortie UDP (voir
[Jeux de rallye](telemetry-rally.md)).

## Ce qui reste de la responsabilité de l'utilisateur {#what-stays-the-users-responsibility}

Ce que l'utilisateur fait pointer vers les outils reste soumis à la licence et au CLUF de ce jeu. Les
fichiers de tour, les enregistrements, les reconstructions et les parcours exportés appartiennent à celui
qui possède le jeu et les données ; le `.gitignore` du dépôt tient les enregistrements, fichiers de tour,
maillages, poids de modèles et vidéos hors du contrôle de version, par dossier et par type de fichier.
