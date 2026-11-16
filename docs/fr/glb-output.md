---
title: Le fichier .glb produit
nav_order: 6
lang: "fr"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Le fichier .glb produit {#the-glb-output}

Une reconstruction est écrite sous forme de fichier glTF 2.0 binaire (`.glb`) que le visualiseur
3DHeat charge par son panneau Arrière-plan / niveau, sans traitement particulier - le même contrat
que celui qu'écrit l'exportateur Unreal. Code : [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Il est écrit à la main plutôt qu'avec une bibliothèque glTF : la sortie est un sous-ensemble étroit
(un seul tampon, compacté, sans animation, sans squelette), et une dépendance capable d'écrire tout
glTF apporterait ses problèmes de version pour quelques centaines de lignes.

## Ce qui figure dans le fichier d'un scan {#what-is-in-a-scans-file}

| Partie (nom du nœud et du maillage) | Contenu |
|---|---|
| `ground:<name>` | triangles orientés à moins de 35 degrés vers le haut |
| `structure:<name>` | tout le reste |

`<name>` est le nom du fichier sans extension lorsqu'on enregistre depuis la fenêtre, ou le nom de la
vidéo pour `reconstruct`. Une partie sans triangle est omise. Aucune partie `water:` n'est jamais
écrite par un scan. `asset.generator` vaut `heat3d-capture-scan`.

## Le contrat {#the-contract}

- **Un nœud par partie**, nommé avec l'étiquette de la partie ; le maillage reprend le même nom. La
  visualiseur lit d'abord le nom du *nœud* : ne nommer que les maillages ferait perdre la
  classification.
- L'étiquette est `<classe>:<nom>`, la classe étant `ground`, `structure` ou `water` - le préfixe que
  le visualiseur reconnaît (`^(ground|structure|water)\s*[:|]`) pour prendre la classe telle quelle au
  lieu de la deviner à partir de la géométrie. Le sol s'affiche plein, les structures presque
  transparentes.
- **Les coordonnées sont dans l'espace du visualiseur** : Y vers le haut, système droitier, et
  **mises à l'échelle en centimètres** (mètres x 100) pour correspondre à l'exportateur Unreal : une
  capture et un export du moteur d'un même lieu se chargent à la même taille, avec les mêmes réglages
  de caméra par défaut. Le champ `extras.unit_metres` du fichier vaut `0.01` (une unité est un
  centimètre), si bien qu'un lecteur qui travaille en mètres, comme [`locate`](locate.md), le prend à sa
  taille réelle. Un scan placé par la télémétrie Forza fait exception quant au système de
  coordonnées : il reste dans le monde propre au jeu, Y vers le haut et gaucher, exactement comme les
  fichiers de tour, afin que les tours enregistrés par-dessus se posent dessus. Lorsque l'échelle d'un
  scan a été trouvée sur une image clé ultérieure ([Échelle](reconstruction-pose.md#scale)), ce
  facteur est intégré à l'échelle écrite.
- `COLOR_0` est lu par le visualiseur, qui colore le sol avec lui lorsque l'interrupteur
  *Couleur capturée* du panneau Arrière-plan / niveau est activé (désactivé par défaut).
- Un scan dont certains points ont été marqués à la main reçoit un fichier `<name>.marks.json` à côté
  de lui ; voir [Enregistrement](reconstruction-scan-ui.md#saving).
- Par primitive : `POSITION` (VEC3 flottant, avec `min` et `max`, à partir desquels le visualiseur
  cadre sa caméra), `NORMAL` (VEC3 flottant), `COLOR_0` facultatif (VEC3 flottant, 0..1),
  `TEXCOORD_0` facultatif ; indices en 16 bits quand chaque indice est inférieur à 65 536, sinon en 32
  bits ; mode triangles.
- Chaque vue de tampon commence à un multiple de 4 octets ; le bloc JSON est complété par des espaces
  et le bloc BIN par des zéros jusqu'à 4 octets.

## Vérifications avant l'écriture {#checks-before-writing}

Chaque partie est validée et refusée, avec un message qui la nomme, si elle n'a aucun sommet, si son
nombre d'indices ne forme pas un nombre entier de triangles, si un indice est hors plage ou négatif,
si des positions ne sont pas finies, ou si des normales ou des couleurs ne correspondent pas au nombre
de sommets. Les normales manquantes sont calculées, **pondérées par l'aire** (le marching cubes laisse
des fines lamelles à côté des grandes faces, et une moyenne non pondérée laisserait de minuscules
triangles faire voter contre la face sur laquelle ils reposent) ; un sommet dégénéré reçoit « vers le
haut ». Ne rien écrire du tout est une erreur.

L'export ne renvoie rien - et la fenêtre affiche « Rien à enregistrer » - lorsque le volume ne donne
aucune surface, plutôt que d'écrire un fichier vide qui passerait pour un scan réussi.

## Textures {#textures}

L'écrivain prend en charge une texture PNG de couleur de base par partie (avec les UV, un matériau
double face, non métallique et entièrement rugueux). Les scans ne l'utilisent pas ; ils portent une
couleur par sommet. Voir [couleur](reconstruction-fusion-and-texture.md#colour).

## Le niveau de référence {#the-reference-level}

`geometry/reference.py` construit un niveau synthétique de taille exactement connue avec le même
écrivain : un sol subdivisé de 400 m, trois bâtiments de 20 x 20 x 12 m et un étang de 50 m situé 1,5 m
sous le sol, chaque classe ayant une couleur plate et distincte. Les tests du visualiseur le
génèrent et l'analysent avec le vrai analyseur du visualiseur : le format du fichier est ainsi testé
des deux côtés, sans jeu ni matériel de capture.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
