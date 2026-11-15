---
title: Manutenzione di questa documentazione
nav_order: 96
lang: "it"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Manutenzione di questa documentazione {#maintaining-these-docs}

La lista di controllo per ogni rilascio, perché il codice, le pagine in inglese e le loro traduzioni
restino allineati. Esegui i passaggi in ordine.

1. **Rigenera le pagine generate.**
   - `python tools/gen_docs_reference.py` riscrive [Riferimento dei comandi](../cli-reference.md) da
     `--help` e dagli elenchi di colonne nel codice. `--check` esce con 1 quando la pagina è
     superata: eseguilo prima di ogni rilascio.
   - `python tools/docs_diagrams.py` ridisegna i diagrammi in `docs/assets/img/`; `--strings`
     aggiorna anche `docs/assets/i18n/en.json`, le etichette da tradurre.
   - `python tools/sync_wiki.py` rigenera la copia della wiki di GitHub in `docs/wiki/`.
2. **Elenca cosa è cambiato dall'ultimo rilascio.** `git log --oneline v$(cat VERSION)..` (l'ultimo
   tag è `v` + la versione in `VERSION`). Per ogni comando, opzione, colonna di output o
   comportamento nuovo o cambiato: aggiorna la sua pagina e aggiungi una riga alla tabella *Docs* in
   `CHANGELOG.md`.
3. **Revisione indipendente.** Qualcuno che non ha scritto la modifica legge le pagine e i diagrammi
   cambiati come tre lettori: un **principiante** (non ha mai usato una riga di comando: riesce a
   installare ed eseguire il tool?), un **bambino di 8 anni** (la pagina dice con parole semplici
   cos'è e perché serve?), e un **esperto** (opzioni, valori predefiniti e colonne corrispondono al
   codice?). Verifica che nessuna pagina nomini livelli, mappe, giocatori o registrazioni reali: gli
   esempi sono sintetici, e le affermazioni di verifica danno solo il metodo e la tolleranza.
4. **Correggi i problemi trovati.**
5. **Traduci.** Ogni pagina tradotta registra l'hash della pagina inglese da cui è nata.
   Ritraduci le pagine il cui hash della fonte inglese è cambiato, e le etichette dei diagrammi
   cambiate; poi rivedi ogni lingua: chiara per i tre lettori, etichette dei diagrammi giuste, parole
   che corrispondono all'interfaccia localizzata del visualizzatore.
6. **Pubblica solo dopo il via libera del proprietario.** Poi tagga il rilascio `v<VERSION>`.

Non hai mai usato questi comandi? [Prima di iniziare](before-you-start.md) spiega Python e il
terminale.

## Traduzioni: i comandi {#translations-the-commands}

Il sito è tradotto nelle 40 lingue del visualizzatore di 3DHeat: l'inglese in `docs/`, ogni altra lingua in
`docs/<lang>/` con gli stessi nomi di file. `tools/docs_i18n.py` tiene la contabilità:

```bash
python tools/docs_i18n.py hashes             # dopo ogni modifica all'inglese: registra l'hash di ogni pagina
python tools/docs_i18n.py svg-strings        # dopo ogni modifica ai disegni: le etichette da tradurre
python tools/docs_i18n.py status             # per lingua: aggiornate, superate, pagine mancanti
python tools/docs_i18n.py todo --lang de     # le pagine tedesche da (ri)tradurre
python tools/docs_i18n.py svg-build --lang de    # i disegni tedeschi da docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # marca le pagine tedesche con l'hash inglese
python tools/docs_i18n.py check              # esce con 1 quando hash o etichette sono superati
```

Traduci solo ciò che elenca `todo`: lascia invariati Markdown, link, codice, nomi di file e di
colonne, traduci titoli e descrizioni delle immagini, e usa le parole dell'interfaccia del visualizzatore di
3DHeat per i suoi pulsanti e pannelli (la sua `src/i18n/locales/<lang>/`). Le pagine di riferimento
generate e le immagini del terminale restano in inglese. Sul sito, una traduzione superata lo dice e
rimanda alla pagina inglese; una traduzione mancante ricade sull'inglese. Il menu delle lingue
nell'intestazione e il reindirizzamento alla lingua del browser nella home arrivano da
`docs/_includes/`.
