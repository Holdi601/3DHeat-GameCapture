---
title: "Mirëmbajtja e këtij dokumentacioni"
nav_order: 96
lang: "sq"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Mirëmbajtja e këtij dokumentacioni {#maintaining-these-docs}

Lista e kontrollit për çdo botim, që kodi, faqet angleze dhe përkthimet e tyre të rrinë
në hap. Bëji hapat sipas radhës.

1. **Rigjenero faqet e gjeneruara.**
   - `python tools/gen_docs_reference.py` rishkruan [Referencën e komandave](../cli-reference.md) nga
     `--help` dhe listat e kolonave në kod. `--check` del me kod 1 kur faqja është e vjetruar: ekzekutoje
     para çdo botimi.
   - `python tools/docs_diagrams.py` rivizaton diagramet në `docs/assets/img/`;
     `--strings` rifreskon edhe `docs/assets/i18n/en.json`, etiketat për t'u përkthyer.
   - `python tools/sync_wiki.py` rigjeneron kopjen e wiki-t të GitHub në `docs/wiki/`.
2. **Liston çfarë ndryshoi që nga botimi i fundit.** `git log --oneline v$(cat VERSION)..` (etiketa e fundit
   është `v` + versioni te `VERSION`). Për çdo komandë, opsion, kolonë dalje ose sjellje të re apo të ndryshuar:
   përditëso faqen e saj dhe shto një rresht te tabela *Docs* në `CHANGELOG.md`.
3. **Rishikim i pavarur.** Dikush që nuk e shkroi ndryshimin lexon faqet dhe diagramet e ndryshuara
   si tre lexues: një **fillestar** (nuk ka përdorur kurrë rreshtin e komandave: mund ta instalojë dhe ta nisë?),
   një **8-vjeçar** (a thotë faqja me fjalë të thjeshta çfarë është dhe pse?), dhe një **profesionist**
   (a përputhen opsionet, vlerat e paracaktuara dhe kolonat me kodin?). Kontrollo që asnjë faqe nuk emërton nivele,
   harta, lojtarë ose regjistrime të vërteta: shembujt janë sintetikë, pohimet e verifikimit japin vetëm metodën dhe
   tolerancën.
4. **Rregullo gjetjet.**
5. **Përktheje.** Çdo faqe e përkthyer regjistron hash-in e faqes angleze nga e cila u bë.
   Ripërktheji faqet ku ndryshoi hash-i i burimit anglisht, dhe etiketat e diagrameve që ndryshuan;
   pastaj rishiko çdo gjuhë: e qartë për tre lexuesit, etiketat e diagrameve të sakta, fjalët që përputhen me
   ndërfaqen e lokalizuar të shikuesit.
6. **Shtyje vetëm pasi pronari të japë miratimin.** Pastaj etiketo botimin `v<VERSION>`.

I ri me ekzekutimin e këtyre komandave? [Para se të nisësh](before-you-start.md) mbulon Python-in dhe
Terminalin.

## Përkthimet: komandat {#translations-the-commands}

Faqja përkthehet në 40 gjuhët e shikuesit 3DHeat: anglishtja te `docs/`, çdo gjuhë tjetër
te `docs/<lang>/` me të njëjtat emra skedarësh. `tools/docs_i18n.py` mban llogaritë:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Përkthe vetëm atë që liston `todo`: mbaji Markdown-in, lidhjet, kodin, emrat e skedarëve dhe të kolonave siç janë,
përkthe titujt dhe përshkrimet e fotove, dhe përdor fjalët e vetë shikuesit 3DHeat për butonat
dhe panelet e tij (`src/i18n/locales/<lang>/`). Faqet e gjeneruara të referencës dhe fotot e terminalit mbeten
anglisht. Në faqe, një përkthim i vjetruar e thotë këtë dhe lidh faqen angleze; ai që mungon
kthehet te anglishtja. Menuja e gjuhës në krye dhe ridrejtimi i faqes kryesore sipas gjuhës së shfletuesit
vijnë nga `docs/_includes/`.
