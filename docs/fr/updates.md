---
title: Mises à jour
nav_order: 10
lang: "fr"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Mises à jour {#updates}

3DHeat GameCapture consulte les publications GitHub de ce dépôt au démarrage, indique si une version plus
récente est disponible, et propose la mise à jour. Code :
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Quand la vérification a lieu {#when-the-check-runs}

- `python -m heat3d_capture <commande>` - avant l'exécution de la commande.
- `python -m heat3d_capture.ui` (et `scan.bat`) - avant l'ouverture de la fenêtre.
- `python -m heat3d_update` - sur demande, en interrogeant toujours GitHub à nouveau.

## Comment la vérification fonctionne {#how-the-check-works}

- La version installée est celle du fichier `VERSION` à la racine du dépôt (par exemple `1.0.1`).
- La dernière publication est demandée à
  `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, avec un délai d'attente de
  **5 secondes**. Un réseau lent ne bloque jamais l'outil plus longtemps que cela.
- La réponse est gardée en cache pendant **6 heures** dans
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` sans
  `LOCALAPPDATA`). Chaque outil 3DHeat a son propre fichier de cache. « Aucune publication » (HTTP 404) est
  mise en cache comme une réponse ; les autres échecs ne le sont pas et signifient simplement qu'aucun avis
  n'est affiché.
- Les versions sont comparées numériquement (`v1.2.3` ou `1.2.3` ; tout ce qui suit `-` ou `+` est ignoré).
- Hors ligne, limité en débit ou derrière un proxy, l'outil continue avec la version qu'il a.

## Ce qui se passe quand une version plus récente est disponible {#what-happens-when-a-newer-release-is-out}

Au démarrage, il affiche, sur le flux d'erreur :

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Si un terminal est disponible pour répondre, il demande `Update now? [Y/n]` (Entrée, `y`, `yes`, `j`, `ja`
  signifient oui). Après une mise à jour réussie, **la même commande est relancée**, sur le nouveau code.
- Sans terminal (un tube, une exécution planifiée), il affiche
  `Run python -m heat3d_update in <dossier> to update.` et poursuit sans changement.

## Comment une mise à jour est appliquée {#how-an-update-is-applied}

Cela dépend de la façon dont les outils ont été installés :

- **Un clone git** (un dossier `.git` et `git` dans le PATH) : `git pull --ff-only`. Refusé tant que la copie
  de travail comporte des modifications locales dans les fichiers suivis - ce sont des travaux de quelqu'un ;
  validez-les ou mettez-les de côté d'abord.
- **Une copie téléchargée** : l'archive source de la publication est téléchargée, extraite dans un dossier
  temporaire (les entrées situées hors du dossier propre de l'archive sont ignorées), et **vérifiée comme
  étant la version qu'elle annonce** d'après son fichier `VERSION`. Ses fichiers sont ensuite copiés sur ce
  dossier. Dans les paquets Python propres à la publication (les dossiers `heat3d_*` en haut du dépôt, et un
  niveau plus bas pour l'ancienne disposition monorepo), les modules `.py` que la publication ne contient plus
  sont supprimés, afin qu'un module périmé ne masque pas son remplaçant.

Vos propres fichiers - enregistrements, fichiers de tour, réglages, exports, le `.venv` - ne sont jamais
touchés : seuls les fichiers qui font partie de la publication sont écrits.

## À la main {#by-hand}

```bash
python -m heat3d_update            # vérifie et met à jour
python -m heat3d_update --check    # indique seulement si une version plus récente est disponible
```

Il affiche `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, ou la
nouvelle version et ce qu'il a fait. Code de sortie 1 si la mise à jour n'a pas pu être appliquée.

## Le désactiver {#switching-it-off}

Définissez **`HEAT3D_NO_UPDATE=1`** (toute valeur sauf vide, `0`, `false`, `no`). Cela désactive la
vérification et l'avis au démarrage. `python -m heat3d_update` lancé à la main vérifie toujours.
