---
title: "Întreținerea acestor documente"
nav_order: 96
lang: "ro"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Întreținerea acestor documente {#maintaining-these-docs}

Lista de verificări pentru fiecare lansare, ca codul, paginile în engleză și traducerile lor să
rămână sincronizate. Faceți pașii în ordine.

1. **Regenerați paginile generate.**
   - `python tools/gen_docs_reference.py` rescrie [Referința comenzilor](../cli-reference.md) din
     `--help` și din listele de coloane din cod. `--check` iese cu codul 1 când pagina este
     învechită: rulați-l înainte de fiecare lansare.
   - `python tools/docs_diagrams.py` redesenează diagramele din `docs/assets/img/`;
     `--strings` reîmprospătează și `docs/assets/i18n/en.json`, etichetele de tradus.
   - `python tools/sync_wiki.py` regenerează copia wiki-ului GitHub din `docs/wiki/`.
2. **Enumerați ce s-a schimbat de la ultima lansare.** `git log --oneline v$(cat VERSION)..` (ultimul
   tag este `v` + versiunea din `VERSION`). Pentru fiecare comandă, opțiune, coloană de rezultat sau
   comportament nou ori schimbat: actualizați pagina lui și adăugați un rând în tabelul *Docs* din
   `CHANGELOG.md`.
3. **Revizuire independentă.** Cineva care nu a scris schimbarea citește paginile și diagramele
   schimbate ca trei cititori: un **începător** (nu a folosit niciodată linia de comandă: poate el
   instala și rula aplicația?), un **copil de 8 ani** (spune pagina, în cuvinte simple, ce este și de
   ce?), și un **profesionist** (opțiunile, valorile implicite și coloanele se potrivesc cu codul?).
   Verificați că nicio pagină nu numește nivele, hărți, jucători sau înregistrări reale: exemplele
   sunt sintetice, iar afirmațiile de verificare dau doar metoda și toleranța.
4. **Remediați constatările.**
5. **Traduceți.** Fiecare pagină tradusă reține hash-ul paginii engleze din care a fost făcută.
   Retraduceți paginile al căror hash sursă în engleză s-a schimbat, și etichetele diagramelor care
   s-au schimbat; apoi verificați fiecare limbă: clar pentru cei trei cititori, etichetele
   diagramelor corecte, cuvintele potrivite cu interfața localizată a vizualizatorului.
6. **Trimiteți doar cu acordul proprietarului.** Apoi etichetați lansarea `v<VERSION>`.

Nu ați mai rulat aceste comenzi? [Înainte de a începe](before-you-start.md) explică Python și
terminalul.

## Traducerile: comenzile {#translations-the-commands}

Site-ul este tradus în cele 40 de limbi ale vizualizatorului 3DHeat: engleza în `docs/`, fiecare
altă limbă în `docs/<lang>/`, cu aceleași nume de fișiere. `tools/docs_i18n.py` ține evidența:

```bash
python tools/docs_i18n.py hashes             # după orice schimbare în engleză: notează hash-ul fiecărei pagini
python tools/docs_i18n.py svg-strings        # după orice schimbare a unei imagini: etichetele de tradus
python tools/docs_i18n.py status             # pe limbă: actuale, învechite, pagini lipsă
python tools/docs_i18n.py todo --lang de     # paginile în germană de (re)tradus
python tools/docs_i18n.py svg-build --lang de    # imaginile în germană din docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # marchează paginile în germană cu hash-ul din engleză
python tools/docs_i18n.py check              # iese cu codul 1 când hash-urile sau etichetele sunt vechi
```

Traduceți doar ce listează `todo`: păstrați Markdown-ul, linkurile, codul, numele fișierelor și al
coloanelor așa cum sunt, traduceți titlurile și descrierile imaginilor, și folosiți cuvintele proprii
ale vizualizatorului 3DHeat pentru butoanele și panourile sale (`src/i18n/locales/<lang>/`). Paginile
de referință generate și imaginile cu terminalul rămân în engleză. Pe site, o traducere învechită o
spune și trimite la pagina engleză; una lipsă revine la engleză. Meniul de limbă din antet și
redirecționarea de pe pagina principală după limba browserului vin din `docs/_includes/`.
