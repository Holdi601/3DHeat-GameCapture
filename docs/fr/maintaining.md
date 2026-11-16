---
title: "Maintenance de ces pages"
nav_order: 96
lang: "fr"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Maintenance de ces pages {#maintaining-these-docs}

La liste de contrôle de chaque version, pour que le code, les pages anglaises et leurs traductions restent
alignés. Faites les étapes dans l'ordre.

1. **Régénérer les pages générées.**
   - `python tools/gen_docs_reference.py` réécrit [Référence des commandes](../cli-reference.md) à partir de
     `--help` et des listes de colonnes du code. `--check` renvoie 1 quand la page est périmée : lancez-le
     avant chaque version.
   - `python tools/docs_diagrams.py` redessine les schémas dans `docs/assets/img/` ;
     `--strings` rafraîchit aussi `docs/assets/i18n/en.json`, les étiquettes à traduire.
   - `python tools/sync_wiki.py` régénère la copie du wiki GitHub dans `docs/wiki/`.
2. **Lister ce qui a changé depuis la dernière version.** `git log --oneline v$(cat VERSION)..` (la dernière
   étiquette est `v` + la version de `VERSION`). Pour chaque commande, option, colonne de sortie ou
   comportement nouveau ou modifié : mettez sa page à jour et ajoutez une ligne au tableau *Docs* de `CHANGELOG.md`.
3. **Relecture indépendante.** Quelqu'un qui n'a pas écrit la modification lit les pages et les
   schémas modifiés comme trois lecteurs : un **débutant** (n'a jamais utilisé de ligne de commande : peut-il installer et lancer
   l'outil ?), un **enfant de 8 ans** (la page dit-elle en mots simples ce que c'est et pourquoi ?) et un **pro**
   (les options, valeurs par défaut et colonnes correspondent-elles au code ?). Vérifiez qu'aucune page ne nomme de vrais niveaux,
   cartes, joueurs ou enregistrements : les exemples sont synthétiques, les affirmations de vérification donnent seulement la méthode et
   la tolérance.
4. **Corriger les constats.**
5. **Traduire.** Chaque page traduite garde le hash de la page anglaise dont elle vient. Retraduisez
   les pages dont le hash de la source anglaise a changé, et les étiquettes de schéma qui ont changé ;
   relisez ensuite chaque langue : claire pour les trois lecteurs, étiquettes de schéma justes, mots conformes à
   l'interface localisée du visualiseur.
6. **Ne publier qu'après l'accord du propriétaire.** Étiquetez ensuite la version `v<VERSION>`.

Vous découvrez ces commandes ? [Avant de commencer](before-you-start.md) couvre Python et le
terminal.

## Traductions : les commandes {#translations-the-commands}

Le site est traduit dans les 40 langues du visualiseur 3DHeat : l'anglais dans `docs/`, chaque autre
langue dans `docs/<lang>/` avec les mêmes noms de fichiers. `tools/docs_i18n.py` tient la comptabilité :

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Ne traduisez que ce que `todo` liste : gardez le Markdown, les liens, le code, les noms de fichiers et de colonnes tels quels,
traduisez les titres et les descriptions d'images, et utilisez les mots propres au visualiseur 3DHeat pour ses boutons
et ses panneaux (son dossier `src/i18n/locales/<lang>/`). Les pages de référence générées et les images de terminal restent
en anglais. Sur le site, une traduction périmée le dit et renvoie vers la page anglaise ; une page manquante
retombe sur l'anglais. Le menu de langue de l'en-tête et la redirection de la page d'accueil selon la langue du navigateur
viennent de `docs/_includes/`.
