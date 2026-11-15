---
title: Vzdrževanje teh dokumentov
nav_order: 96
lang: "sl"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Vzdrževanje teh dokumentov {#maintaining-these-docs}

Kontrolni seznam za vsako izdajo, da kodo, angleške strani in njihovi prevodi ostanejo usklajeni.
Koraki naj si sledijo po vrsti.

1. **Ponovno ustvarite ustvarjene strani.**
   - `python tools/gen_docs_reference.py` ponovno napiše [Ukazna referenca](../cli-reference.md) iz
     `--help` in seznamov stolpcev v kodi. `--check` konča s kodo 1, kadar je stran zastarela: pred
     vsako izdajo ga zaženite.
   - `python tools/docs_diagrams.py` ponovno nariše diagrame v `docs/assets/img/`; `--strings` pa
     osveži tudi `docs/assets/i18n/en.json`, oznake za prevod.
   - `python tools/sync_wiki.py` ponovno ustvari kopijo wikija GitHub v `docs/wiki/`.
2. **Našteti, kaj se je spremenilo od zadnje izdaje.** `git log --oneline v$(cat VERSION)..` (zadnja
   oznaka je `v` + različica v `VERSION`). Za vsak novi ali spremenjeni ukaz, možnost, izhodni
   stolpec ali vedenje: posodobite njegovo stran in dodajte vrstico v tabelo *Docs* v
   `CHANGELOG.md`.
3. **Neodvisni pregled.** Nekdo, ki spremembe ni napisal, prebere spremenjene strani in diagrame kot
   tri bralce: **začetnik** (nikoli ni uporabljal ukazne vrstice: ali lahko namesti in zažene?),
   **osemletnik** (ali stran z enostavnimi besedami pove, kaj je in zakaj?) in **strokovnjak** (ali se
   možnosti, privzete vrednosti in stolpci ujemajo s kodo?). Preverite, ali nobena stran ne navaja
   pravih nivojev, zemljevidov, igralcev ali posnetkov: primeri so sintetični, trditve o preverjanju
   navajajo le metodo in toleranco.
4. **Odpravite ugotovitve.**
5. **Prevedite.** Vsaka prevedena stran si zabeleži zgoščeno vrednost (hash) angleške strani, iz
   katere je nastala. Ponovno prevedite strani, katerih izvorna zgoščena vrednost se je spremenila,
   in oznake diagramov, ki so se spremenile; nato pregledajte vsak jezik: jasen za tri bralce,
   pravilne oznake diagramov, besede, ki se ujemajo z lokaliziranim vmesnikom pregledovalnika.
6. **Potisnite šele po odobritvi lastnika.** Nato označite izdajo `v<VERSION>`.

Prvič zaganjate te ukaze? [Preden začnete](before-you-start.md) pojasni Python in terminal.

## Prevodi: ukazi {#translations-the-commands}

Spletno mesto je prevedeno v 40 jezikov: angleščina je v `docs/`, vsak drug jezik pa
v `docs/<lang>/` z enakimi imeni datotek. `tools/docs_i18n.py` vodi evidenco:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Prevedite samo, kar izpiše `todo`: Markdown, povezave, kodo, imena datotek in stolpcev pustite
kakršna so, prevedite naslove in opise slik ter uporabljajte lastne besede pregledovalnika 3DHeat za njegove
gumbe in plošče (njegov `src/i18n/locales/<lang>/`). Ustvarjene referenčne strani in slike terminala
ostanejo v angleščini. Na spletnem mestu zastarel prevod to pove in povezuje na angleško stran;
manjkajoč prevod se vrne na angleščino. Jezikovni meni v glavi in preusmeritev domače strani glede
na jezik brskalnika prihajata iz `docs/_includes/`.
