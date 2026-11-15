---
title: "La fenêtre de scan"
nav_order: 1
lang: fr
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# La fenêtre de scan {#the-scan-window}

```bash
python -m heat3d_capture.ui        # ou double-cliquez sur scan.bat
```

Code : [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
La fenêtre n'est qu'une vue sur `scan/session.py` et `scan/reconstruct.py` ; elle ne contient aucune logique de scan
ni de géométrie.

## Démarrage {#starting-up}

1. **Vérification des mises à jour** - voir [Mises à jour](updates.md).
2. **Vérification des dépendances** - chaque paquet dont le scanner a besoin est vérifié avant toute importation ; les
   paquets manquants sont listés avec leur rôle et leur taille de téléchargement, et installés seulement après
   « Télécharger et installer ». Annuler quitte sans rien modifier. Voir [Exécution et dépendances](runtime.md#first-run-preflight).
3. **Fenêtre** - « 3DHeat — Level scanner », 1420 x 900, style Fusion de Qt.
4. **Vérification du matériel** - le meilleur moteur d'inférence est choisi, le modèle de profondeur est chargé et son
   débit est mesuré sur 6 images ; la boîte de verdict en haut à gauche indique à quoi ressemblera le scan (voir
   [Exécution](runtime.md#what-to-expect-from-this-machine)).
5. **Les raccourcis globaux** sont enregistrés en dernier.

### Quand le modèle de profondeur n'est pas encore là {#when-there-is-no-depth-model-yet}

Si `models/` ne contient aucun `depth-*.onnx`, le verdict affiche **« One more thing to set up. »**, le bouton Démarrer est
désactivé, et un bouton **Set up the depth model** apparaît. Il :

- vérifie PyTorch, `transformers` et `onnxscript` (environ 945 Mo au total), et demande avant de les installer ;
- lance `tools/export_onnx.py --size small` comme processus séparé (pour que PyTorch ne reste jamais dans la mémoire du
  scanner), avec une limite de 30 minutes. La fenêtre ne répond pas pendant ce temps ;
- en cas de succès, relance la vérification du matériel ; en cas d'échec, affiche les 600 derniers caractères de la
  sortie du convertisseur.

Quand plusieurs modèles sont présents, le choix se fait **selon la licence, et non selon le nom du fichier** : `depth-small-*`
(Apache-2.0, usage commercial autorisé) dès qu'il existe, puis Base, puis Large (tous deux non commerciaux). La boîte de
verdict et la ligne grise sous les boutons nomment le fichier utilisé, sa licence, et les autres fichiers de modèle présents
mais non utilisés - par exemple `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Pour scanner avec Base, sortez le fichier Small de `models/`.

## Colonne de gauche : réglages {#left-column-settings}

| Groupe | Commande | Défaut | Plage / valeurs | Ce qu'elle fait |
|---|---|---|---|---|
| (haut) | Boîte de verdict | « Checking your graphics card… » | colorée en vert, orange ou rouge selon le niveau | Titre, `<device> via <API> — N views per second`, une remarque, et `Depth model: <file> (<licence>)` |
| Quoi scanner | Source | Tout l'écran | Tout l'écran, Une fenêtre, Un fichier vidéo | D'où viennent les images |
| | Lequel | `1` | numéro d'écran / titre de fenêtre / chemin vers une vidéo | `monitor:<n>`, `window:<title>`, ou un chemin de fichier |
| | Choisir le fichier… | affiché pour la vidéo | `*.mp4 *.mkv *.avi *.mov` | Remplit le chemin |
| Avec quel soin | Préréglage | Équilibré | Brouillon, Équilibré, Détaillé | Résolution de capture et sévérité du choix des images-clés (ci-dessous) ; un résumé d'une ligne s'affiche dessous |
| | Champ de vision du jeu | 90° | 30-140° | Le champ de vision **horizontal** du jeu. Trop étroit, et le niveau se reconstruit plus profond qu'il ne l'est ; trop large, et il s'aplatit. Les jeux de course sont plutôt autour de 65° |
| | Détail de surface | 0,25 m | 0,05-2,0 m, pas de 0,05 | Taille du voxel de la surface. Plus petit est plus fin et plus lourd |
| Arrêter après | Durée | pas de limite | 0-120 min | Termine le scan après cette durée (0 = pas de limite) |
| | Vues gardées | 3000 | 0-100 000 | Termine le scan après ce nombre d'images-clés, comme garde-fou de mémoire (0 = pas de limite) |
| Quoi ignorer | Ignorer le HUD et tout ce qui est sur la caméra | activé | | Apprend et masque le HUD, le réticule, l'arme, le capot, le cockpit ([Capture](reconstruction-capture.md#what-is-not-the-world)). La ligne sous la case dit ce que le détecteur décide en ce moment |
| Pendant le jeu | Afficher le retour sur le jeu | activé | | Ouvre la superposition traversable aux clics pendant le scan. L'indication en dessous : lancez le jeu en **fenêtré sans bordure** ; le plein écran exclusif ne peut être dessiné par rien |
| Télémétrie de course (Forza) | Écouter les données de position | désactivé | | Prend le chemin de la caméra depuis Data Out de Forza au lieu de l'estimer depuis l'image ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Le port de Data Out |
| | (ligne d'état) | | | `N packets — poses come from the game, not from the picture`, ou `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Démarrer le scan** / **Arrêter le scan** | | | Démarre ou arrête ; affiche le raccourci quand il a pu être enregistré |
| | **Set up the depth model** | caché | | Voir plus haut |
| | **Enregistrer le niveau…** | désactivé | | Activé après un scan qui a produit des voxels de surface ; demande un nom de fichier (par défaut `scan.glb`) |
| | (ligne grise) | | | `Model: <file> (<licence>) · Available: <backends>`, plus des notes de configuration, comme l'installation de `onnxruntime-gpu` |

### Les préréglages {#the-presets}

| Préréglage | Côté le plus long de la capture | Quantile de conservation | Seuil de départ | Résumé affiché |
|---|---|---|---|---|
| Brouillon | 640 px | 0,85 | 0,020 | Rapide et approximatif. Bon pour vérifier un parcours avant un vrai scan. |
| Équilibré | 960 px | 0,65 | 0,010 | Le choix habituel. Marchez à allure normale. |
| Détaillé | 1280 px | 0,40 | 0,004 | Lent et minutieux. Marchez délibérément et tournez doucement. |

Le quantile de conservation signifie « garder une image quand elle a changé davantage que ce quantile des changements des 240
dernières images » - Brouillon garde à peu près les 15 % les plus actifs, Détaillé les 60 % les plus actifs. Voir
[Images-clés](reconstruction-capture.md#keyframes).

### Réglages fixes dans la fenêtre {#settings-that-are-fixed-in-the-window}

La fenêtre reconstruit toujours pendant le scan, utilise une hauteur de caméra de **1,15 m** pour l'échelle du plan du sol (la
valeur de marche, 1,70 m, n'est pas réglable), et laisse l'échelle des moteurs choisir le GPU. Ce sont des champs de
`ScanSettings` (`camera_height`, `prefer_backend`) que seul un script peut modifier.

## Colonne de droite : ce que fait le scan {#right-column-what-the-scan-is-doing}

| Élément | Affiche |
|---|---|
| **Ce que voit la caméra** | la dernière image-clé |
| **Forme lue** | sa profondeur prédite, colorée avec la palette Turbo, normalisée entre le 2e et le 98e centile de cette image (pour qu'un seul pixel de ciel n'aplatisse pas l'échelle) |
| **Couverture - où vous êtes passé, et avec quelle qualité** | une vue en plan (voir ci-dessous) |
| **À revoir** | les points faibles, numérotés pour correspondre aux anneaux de la carte, chacun avec une consigne ; du plus grand au plus petit, au plus 8 ; puis les points que vous avez marqués (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Barre de vitesse de marche | `walk speed — N% of the way to the next view` : le changement d'image de la dernière image divisé par le **seuil utilisé** - la valeur de départ du préréglage pour les 30 premières images, la valeur adaptée ensuite ([Images-clés](reconstruction-capture.md#keyframes)) |
| Ligne d'état | la santé du suivi, ou un avertissement de capture (ci-dessous) |
| Ligne de taille | `Size: ...`, comment l'échelle du niveau a été fixée, ou pourquoi elle ne l'a pas été ([Échelle](reconstruction-pose.md#scale)) |
| Ligne de statistiques | `views  frames  dropped  depth-per-second  seconds`, et pendant la reconstruction `placed  cells  % well seen  metres`, plus `recovered` et `loops closed` quand l'un d'eux n'est pas nul |
| Ligne de raccourcis | les touches enregistrées, ou la raison pour laquelle elles n'ont pas pu l'être |
| Ligne d'indication (orange) | conseils en direct (ci-dessous), le message final du scan, et les marques |

### La carte de couverture {#the-coverage-map}

Redessinée toutes les 900 ms sur un thread d'arrière-plan (jamais sur le thread de l'interface), sur 200 x 200 cellules mises
à l'échelle en 420 px :

- chaque colonne de la grille de couverture prend la **meilleure** qualité d'observation qu'elle contient (ainsi un sol bien
  vu n'est pas peint en orange par un plafond mal vu au-dessus) ;
- la progression va du rouge (mauvais) à l'orange (mince), au jaune (acceptable) et au vert (bon) ;
- les cellules jamais observées sont d'un gris foncé distinct, pour qu'un coin inexploré ne ressemble pas à un coin mal scanné ;
- le chemin parcouru est tracé en fine ligne claire, la position actuelle en point blanc ;
- les points faibles sont des anneaux blancs avec leur numéro ;
- les points que vous avez marqués sont des carrés orange étiquetés `M1`, `M2`, …

Le calcul de la qualité et des points faibles : [Fusion, couverture et couleur](reconstruction-fusion-and-texture.md#coverage).

### La ligne de santé {#the-health-line}

| Santé du suivi (images placées / images) | Texte | Couleur |
|---|---|---|
| aucune image pour l'instant | Waiting for the first frame. | gris |
| 90 % ou plus | Tracking well — N of M frames placed. | vert |
| 60 % ou plus | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | orange |
| moins de 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rouge |

Un avertissement de capture venant de la grille de couverture remplace cette ligne (rouge quand le scan est jugé non
reconstructible, orange sinon) : presque pas de parallaxe, tout vu à plus de 25 m, ou parallaxe mince. Voir
[Couverture](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### La ligne d'indication {#the-hint-line}

| Condition | Indication |
|---|---|
| plus de la moitié des images écartées, après 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| moins de 0,3 vue gardée par seconde, après 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| plus de 8 vues gardées par seconde, après 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| scan terminé | le message de la session : `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, ou `failed: <error>` |

## Raccourcis {#hotkeys}

Enregistrés auprès de Windows (`RegisterHotKey`), donc ils fonctionnent pendant que le jeu a le focus. Faire Alt+Tab hors
d'un jeu en plein écran est exactement ce qui gâche une capture.

| Touches | Action |
|---|---|
| **Ctrl+Alt+F9** | Démarrer / arrêter le scan |
| **Ctrl+Alt+F10** | Marquer cet endroit pour y revenir (pendant le scan) |
| **Ctrl+Alt+F11** | Afficher / masquer la superposition (bascule la case « Afficher le retour sur le jeu ») |

- Ils sont enregistrés une fois, à l'ouverture de la fenêtre, et libérés à sa fermeture ; tant qu'ils sont enregistrés, ces
  combinaisons de touches sont retirées à tous les autres programmes, jeu compris. Les touches de fonction avec deux modificateurs
  ont été choisies parce que les jeux les lient rarement.
- La répétition automatique est supprimée (`MOD_NOREPEAT`), donc maintenir une touche n'active pas le scan des dizaines de fois.
- Une touche déjà prise par un autre programme est signalée (`... unavailable: another program already has this key`) et les
  autres fonctionnent toujours. Un bouton n'annonce que la touche qui a réellement été enregistrée.
- Les touches sont fixées dans le code (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`) ; l'analyseur accepte F1-F12 avec
  `ctrl`, `alt` et `shift`. Hors de Windows, il n'y a pas de raccourcis globaux, et la fenêtre l'indique.
- **Marquer** enregistre la position actuelle de la caméra (celle de la dernière image placée) et affiche « Marked MN.
  Marked spots are on the map and saved with the level. » Avant qu'une image ait été placée, il indique qu'il n'y a nulle
  part où marquer. Les points marqués sont dessinés sur la carte de la fenêtre et de la superposition, sous forme de carrés
  orange étiquetés `M1`, `M2`, …, listés sous les points faibles, comptés dans la ligne de statistiques de la superposition,
  et enregistrés avec le niveau (ci-dessous).

## La superposition {#the-overlay}

Un petit panneau épinglé au-dessus du jeu, pour que le retour soit là où les yeux sont déjà.

- Sans cadre, toujours au premier plan, une fenêtre d'outil (absente de la barre des tâches et d'Alt+Tab), traversable aux clics
  dans Qt et rendue traversable aux clics sous Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), pour qu'un clic destiné au jeu ne
  soit jamais avalé. Affichée sans prendre le focus.
- Dans le coin supérieur droit de l'écran principal, à 18 px des bords ; 214 x 358 px.
- S'ouvre au démarrage d'un scan (si « Afficher le retour sur le jeu » est activé), se ferme à son arrêt.
- **Demande le mode fenêtré sans bordure** : rien ne peut être dessiné par-dessus le plein écran exclusif - ni ceci, ni
  la superposition de Steam, ni celle de Discord.

De haut en bas, elle affiche :

| Élément | Contenu |
|---|---|
| Carte de couverture | 190 px, la même carte que la fenêtre à une résolution plus faible de 120 x 120, avec le chemin, les anneaux des points faibles et les points marqués |
| Santé | le même texte et la même couleur que la ligne de santé de la fenêtre |
| Statistiques | `N placed · M to revisit · X m`, avec `· K marked` quand il y en a |
| Barre **mouvement** | la même que la barre de vitesse de marche de la fenêtre : le changement d'image de la dernière image divisé par le seuil utilisé, plein quand la prochaine image sera gardée |
| Barre de **netteté** | netteté relative à la médiane de cette capture : vert à partir de 0,75, orange à partir de 0,45, rouge en dessous |
| Conseil | une consigne, en vert / orange / rouge (en gras quand ce n'est pas « ok ») - voir [qualité d'image](reconstruction-capture.md#frame-quality-and-advice) |
| Raccourcis | les touches enregistrées |

Si la mise à jour de la superposition échoue, elle passe à un panneau rouge **« Feedback stopped »** qui indique que ce qui
était affiché avant est périmé, que le scan continue et que la fenêtre principale reste exacte, avec l'erreur et un compteur.
Un panneau figé en vert continuerait sinon d'être lu comme une confirmation.

## Enregistrement {#saving}

**Enregistrer le niveau…** écrit la reconstruction sous forme de `.glb` (voir [La sortie .glb](glb-output.md)). Si le volume ne
produit aucune surface, « Nothing to save » explique que le suivi a sans doute été perdu pendant la plus grande partie du scan.
En cas de succès : « Written to <path> ... Load it in 3DHeat through the Level panel. », en nommant aussi le fichier des marques
quand il y a des points marqués.

Les points marqués sont écrits à côté du niveau sous **`<name>.marks.json`** :

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` est dans les coordonnées propres du niveau (l'échelle du GLB appliquée, de sorte qu'une marque tombe sur le maillage
au-dessus duquel elle a été faite), `metres` en mètres ; `number` correspond à `M1`, `M2`, … dans la fenêtre. Quand l'échelle a été
trouvée sur une image-clé plus tardive ([Échelle](reconstruction-pose.md#scale)), les deux incluent ce facteur.

Arrêter un scan conserve ce qui a été recueilli ; un nouveau **Démarrer** efface le scan précédent.
**Fermer la fenêtre ne demande pas d'enregistrer** : cela arrête le scan, libère les raccourcis et ferme la superposition.
