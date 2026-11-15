---
title: "Jeux"
nav_order: 4
lang: "fr"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Jeux : enregistrement et parcours {#games-recording-and-courses}

Comment chaque jeu pris en charge est enregistré, ce qu'il envoie, et lesquels de ses parcours
peuvent être exportés à partir de ses propres fichiers.

Les règles sont les mêmes pour chaque jeu : un parcours provient de fichiers que l'utilisateur
possède, ou est reconstitué à partir de sa propre partie. Les archives chiffrées ne s'ouvrent
qu'avec une clé que l'utilisateur possède déjà : rien ici ne fournit de clés ni n'en récupère, et
rien ne s'injecte dans le processus d'un jeu. La télémétrie provient uniquement des interfaces que
les jeux publient pour elle (sorties UDP, mémoire partagée, leurs propres interfaces de mods et de
plugins). Ce vers quoi un utilisateur dirige les outils reste soumis à la licence de ce jeu.

## Télémétrie {#telemetry}

Chaque jeu aboutit à des fichiers `heat3d-lap` ([`lap-format.md`](lap-format.md)), avec des noms de
canaux canoniques et un bloc `meta` qui indique ce que signifient ses nombres : comment son glissement
est mis à l'échelle, circuit, rallye ou arcade, la surface si elle est connue. Ainsi, un lecteur les
traite tous de la même façon. Toutes les commandes sont `python -m heat3d_capture ...` dans ce dépôt.

| Jeu | Comment enregistrer | Position | Pneus et glissement | Angle de dérive | Statut |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out par UDP : `heat3d_capture telemetry` (transmet à FH Companion), ou le `.tele.gz` de FH Companion à côté de chaque tour, chargé avec le fichier de tour | XYZ du monde | taux de glissement, angle de glissement, glissement combiné par roue, normalisés ; vibration de surface | vitesse dans le repère de la voiture | enregistreur testé ; lecteur `.tele.gz` vérifié sur de vrais tours |
| Forza Motorsport (y compris 2023) | le même ; distingué par la longueur des paquets | XYZ du monde | idem | idem | enregistreur testé |
| Assetto Corsa, ACC, AC EVO | mémoire partagée : `telemetry --game ac / acc / acevo` | moyenne des points de contact des pneus | taux et angle de glissement (physiques, mis à l'échelle par un pic d'adhérence sur asphalte) ; ABS et antipatinage en action (ACC, EVO) | vitesse dans le repère de la voiture | enregistreur testé sur des pages synthétiques |
| Assetto Corsa Rally | `telemetry --game acrally` | idem | idem ; charges des roues ; températures converties depuis les kelvins | vitesse dans le repère de la voiture | enregistreur testé sur des pages synthétiques |
| EA SPORTS WRC | UDP : `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` active le paquet `wrc` par défaut (le fichier est d'abord sauvegardé) | XYZ du monde | vitesse de l'aire de contact par roue ; glissement déduit | à partir des axes de la voiture et de sa vitesse | enregistreur testé sur des paquets construits selon la disposition documentée |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP : régler `<udp enabled="true" extradata="3" port="20777" delay="1" />` dans `hardware_settings_config.xml`, puis `telemetry --game dirtrally2` (ou `dirtrally`, `dirt4`) | XYZ du monde | vitesse de l'aire de contact par roue ; glissement déduit. Pas de canal de frein à main | à partir des axes de la voiture et de sa vitesse | idem |
| Richard Burns Rally (RSF/NGP) | UDP de NGP (`udpTelemetry=1`) : `telemetry --game rbr` | monde, axe vertical trouvé à partir de l'étape | déflexion et force de ressort par roue ; pas de vitesses de roue | les vitesses propres de la voiture | idem ; axes et unités de vitesse non documentés, déduits des données |
| BeamNG.drive | le mod de protocole `heat3d` : `telemetry --game beamng --install`, puis Options > Autre > Protocoles > « others » | monde, tourné pour avoir Y vers le haut | vitesse de surface de roue, rotation, charge, contact avec le sol ; glissement déduit | à partir des axes de la voiture et de sa vitesse | enregistreur testé sur des paquets construits à partir de la structure du mod ; le mod n'est pas testé dans le jeu |
| Trackmania (2020) | le plugin Openplanet `Heat3dRecorder` : `telemetry --game trackmania --install`, chargé en mode développeur d'Openplanet ; un CSV par course dans son dossier de stockage | XYZ du monde | coefficient de glissement de Trackmania par roue ; sol meuble d'après le matériau des roues ; en l'air | vitesses avant et latérale | lecteur testé ; le plugin n'est pas testé dans le jeu |
| iRacing | ses propres fichiers `.ibt` ; pas d'enregistreur nécessaire | latitude, longitude, altitude, projetées sur un plan tangent | pas de glissement (non enregistré) ; vitesse de lacet et accélération latérale | à partir de la vitesse de lacet par rapport à la trajectoire | lecteur testé sur un fichier synthétique |

Ce qu'aucun des jeux de rallye n'envoie, le glissement des pneus, un lecteur le calcule : à partir de
l'aire de contact ou de la vitesse de surface de chaque roue comparée à la vitesse de la voiture là où
un jeu en envoie une (`(roue - voiture) / voiture`), ou à partir de sa rotation et d'un rayon de
roulement mesuré sur le tour lui-même là où il n'envoie que la rotation. L'angle de dérive vient de la
vitesse propre de la voiture (Forza, les jeux AC, Trackmania, RBR), de la vitesse du monde projetée
sur les axes de la voiture (EA WRC, DiRT, BeamNG), ou du cap par rapport à la trajectoire. Le fait
que la voiture soit en l'air vient du contact, des charges ou de la suspension de ses roues.

Lorsque le monde d'un jeu est gaucher (celui de Forza l'est), le parcours sort en miroir dans une
visionneuse droitière ; la direction et la suspension propres aux tours le révèlent. Les jeux dont la
latéralité n'est pas documentée (RBR, BeamNG, Trackmania) sont traités de la même façon : mesurée,
pas supposée.

Au-delà des canaux de conduite, les enregistreurs gardent ce que chaque jeu ajoute : l'action de
l'ABS et de l'antipatinage dans les jeux AC, la répartition du freinage, le DRS, le limiteur de vitesse des
stands, le turbo, et la durée de vie des plaquettes et des disques de frein ; les réglages d'aide, la
répartition du freinage, le carburant, les températures d'huile et d'eau d'iRacing, et tout autre
canal qu'il enregistre sous son propre nom.

### Sources et ce qui n'est pas encore confirmé {#sources-and-what-is-not-yet-confirmed}

- **Forza :** la documentation officielle Data Out (Forza Motorsport ; Forza Horizon 6) pour les
  champs, leurs unités et le repère de la voiture (x à droite, y vers le haut, z vers l'avant -
  gaucher). Ce à quoi Forza normalise son glissement n'est pas documenté : mesurez où l'adhérence de
  chaque voiture lâche réellement, plutôt que de supposer que 1 est la limite.
- **Kunos :** le SDK d'AC1, la documentation de la mémoire partagée d'ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, mesuré ; AC Rally utilise la disposition d'ACC, « confirmée
  octet par octet »), `LuizZak/AssettoCorsaRallyTelemetryReader`. Le côté vers lequel pointe l'axe x
  du repère de la voiture est documenté dans les deux sens : utilisez la taille de l'angle de dérive,
  pas son signe.
- **EA SPORTS WRC :** le guide UDP Telemetry v1.3 d'EA et la liste des canaux que le jeu écrit dans
  `readme/channels.json` ; les décalages du paquet `wrc` par défaut tels que décodés par
  nobonobo/obs-codemasters-telemetry. Le port d'origine par défaut n'est pas documenté ; l'enregistreur
  active le paquet sur le port 20777.
- **DiRT :** le document UDP de DiRT 4 de Codemasters, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Le sens du vecteur latéral et l'unité de la position de
  suspension sont documentés dans les deux sens ; aucun des deux ne tranche une conclusion.
- **RBR :** `rbr.telemetry.data.TelemetryData.h` de NGP (via mika-n/RBRUDPTelemetryLogger,
  groybe/rbr-udp-telem). Les axes de position, les unités d'attitude et l'unité de vitesse ne sont pas
  documentés : l'enregistreur prend le haut à partir de l'étape, et la vitesse à partir des positions.
- **BeamNG :** documentation.beamng.com (protocoles ; refNodes : véhicule +X gauche, -Y avant, Z vers
  le haut), et les fichiers `lua/vehicle/protocols.lua` et `wheels.lua` du jeu. OutSim est un bouchon
  dans les versions actuelles ; OutGauge n'a pas de position et MotionSim pas de roues, d'où le mod.
- **Trackmania :** `CSceneVehicleVisState` d'Openplanet et le plugin VehicleState, le temps de course de
  `CSmScriptPlayer`. Les plugins Openplanet ne peuvent pas envoyer d'UDP, donc le plugin écrit des
  fichiers. Les plugins non signés ne se chargent qu'en mode développeur, ce qui limite le jeu en
  ligne ; le plugin peut être signé sur openplanet.dev.

Aucun des enregistreurs n'a encore été lancé contre les jeux en direct ici ; la première vraie session
de chacun est le test qui compte, et `tests/test_kunos.py`, `test_rally.py` et `test_beamng.py`
figent les dispositions pour lesquelles ils ont été conçus. Chaque enregistreur vérifie ses paquets au
fur et à mesure qu'ils arrivent - la vitesse par rapport à la vitesse indiquée, la taille de la
structure - et le signale lorsqu'une disposition ne correspond pas.

## Parcours : ce qui est exporté, par jeu {#courses-what-is-exported-per-game}

Un parcours ajoute les bordures, les murs et les dégagements qui expliquent une trajectoire. Les
parcours sont exportés par [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <lap>`), à partir des fichiers du jeu, lorsque cela a été construit
et vérifié sur une copie installée. Les détails figurent dans la
[documentation de GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Jeu | Parcours à partir d'un tour |
|---|---|
| Forza Horizon | oui |
| BeamNG.drive | oui |
| Assetto Corsa Rally | oui |
| Assetto Corsa EVO | non : son contenu n'est pas lisible sous forme de fichiers |
| iRacing | non : les modèles de circuits sont dans un format protégé |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | pas encore : chacun a besoin d'une copie installée pour être construit et vérifié |

En attendant, la voie par le gameplay ci-dessous fonctionne pour tous.

## La voie qui fonctionne pour chaque jeu {#the-route-that-works-for-every-game}

GameCapture reconstitue un niveau à partir d'une vidéo de partie. Sa partie difficile est le trajet
de la caméra, et pour Forza elle est exacte, parce que la télémétrie donne la pose de la voiture à
chaque image. Chaque jeu ci-dessus dispose désormais de la même chose : position et attitude, en
direct, à partir d'une interface documentée. Les transmettre à `pose/telemetry_pose.py` à la place de
celles de Forza est l'unique élément qui rend la voie par le gameplay exacte pour tous ; le reste de
ce pipeline (profondeur, fusion, texturage) ne se soucie pas du jeu qui a dessiné les images.
