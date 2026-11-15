---
title: "Avant de commencer"
nav_order: 1.5
lang: fr
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Avant de commencer {#before-you-start}

Vous débutez avec la ligne de commande ? Cette page vous mène de zéro à une première commande qui fonctionne.
Cela prend une dizaine de minutes, une seule fois.

## 1. Installer Python {#install-python}

GameCapture est un programme Python. Il vous faut **Python 3.10 ou plus récent**.

1. Allez sur [python.org/downloads](https://www.python.org/downloads/) et téléchargez la dernière
   version de Python pour Windows.
2. Lancez l'installeur. Sur le premier écran, **cochez « Add python.exe to PATH »**. Sans cette case,
   le terminal ne trouvera pas Python.
3. Cliquez sur *Install Now*.

Ou, dans un terminal : `winget install Python.Python.3.12`.

## 2. Installer Git {#install-git}

Git télécharge l'outil. Récupérez-le sur [git-scm.com](https://git-scm.com/download/win), ou lancez
`winget install Git.Git`. Si vous ne voulez pas de Git, utilisez *Code > Download ZIP* sur la
[page GitHub](https://github.com/Holdi601/3DHeat-GameCapture) et décompressez-le.

## 3. Ouvrir un terminal dans un dossier {#open-a-terminal-in-a-folder}

Un terminal est une fenêtre dans laquelle vous tapez des commandes. Ces pages utilisent **PowerShell**,
que tous les PC Windows possèdent.

- Ouvrez le dossier dans l'Explorateur de fichiers, cliquez dans la barre d'adresse, tapez `powershell`
  et appuyez sur Entrée. PowerShell s'ouvre **dans ce dossier**.
- Ou ouvrez PowerShell depuis le menu Démarrer et allez dans un dossier avec `cd` :

```powershell
cd "C:\Games\Tools"
```

## 4. Lire les commandes de ces pages {#read-the-commands-on-these-pages}

- Tapez chaque ligne de commande et appuyez sur Entrée.
- Le texte entre chevrons est un **espace réservé** : mettez-y votre propre valeur, sans les chevrons.
  `<enregistrement>.mp4` signifie un nom de fichier tel que `match1.mp4`.
- Le texte entre crochets, comme `[--fps 5]`, est **facultatif**.
- Un chemin qui contient des espaces demande des guillemets : `"C:\Mes Vidéos\match1.mp4"`.
- Les lignes qui commencent par `#` sont des commentaires. Vous ne les tapez pas.

## 5. Récupérer l'outil et ses paquets {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` crée un dossier privé pour les paquets de l'outil, afin qu'ils ne se mélangent pas
à autre chose sur votre PC. Chaque commande commence ensuite par `.venv\Scripts\python`.

**Vous devez voir** la dernière ligne indiquer `Successfully installed ...`. Vérifiez que l'outil fonctionne :

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Vous devez voir** une liste de commandes, commençant par `usage: heat3d_capture`.

![La liste des commandes qu'affiche --help](../assets/img/cli-help.svg)

Vous pouvez aussi *activer* le dossier une fois, puis taper simplement `python` :

| Terminal | Activer | Puis |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Si PowerShell répond *running scripts is disabled*, lancez une fois
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou passez l'activation.

## 6. Programmes supplémentaires dont certaines commandes ont besoin {#extra-programs-some-commands-need}

| Commande | Besoin | Installation |
|---|---|---|
| `hud` | **ffmpeg** et **ffprobe** (lisent les fichiers vidéo) | `winget install Gyan.FFmpeg`, puis ouvrez un nouveau terminal. Vérifiez avec `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installé avant les autres paquets | la commande de [pytorch.org](https://pytorch.org/get-started/locally/) pour votre carte graphique |

## Quand quelque chose ne va pas {#when-something-goes-wrong}

| Vous voyez | Cela signifie | Faites ceci |
|---|---|---|
| `'python' is not recognized` | Python n'est pas dans le PATH | Réinstallez Python en cochant PATH, puis ouvrez un nouveau terminal. |
| `No module named heat3d_capture` | le terminal n'est pas dans le dossier de l'outil | `cd` jusqu'au dossier `3DHeat-GameCapture`. |
| `No module named numpy` (ou un autre paquet) | les paquets ne sont pas installés, ou vous avez utilisé un autre Python | Relancez la ligne `pip install -r requirements.txt` avec `.venv\Scripts\python`. |
| `'.venv' is not recognized` | vous avez tapé `/` dans cmd | Utilisez des barres obliques inverses : `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg est absent | Voir l'étape 6, puis ouvrez un nouveau terminal. |

Suite : [Accueil](index.md) donne un premier exemple pour chaque tâche.
