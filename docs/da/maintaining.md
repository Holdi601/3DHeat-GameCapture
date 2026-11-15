---
title: Vedligeholdelse af dokumentationen
nav_order: 96
lang: "da"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Vedligeholdelse af dokumentationen {#maintaining-these-docs}

Tjeklisten for hver udgivelse, så koden, de engelske sider og deres oversættelser holder trit. Gør
trinene i rækkefølge.

1. **Generer de genererede sider igen.**
   - `python tools/gen_docs_reference.py` omskriver [Kommandoreference](../cli-reference.md) ud fra
     `--help` og kolonnelisterne i koden. `--check` afslutter med 1, når siden er forældet: kør den
     før hver udgivelse.
   - `python tools/docs_diagrams.py` tegner diagrammerne i `docs/assets/img/` igen;
     `--strings` opdaterer også `docs/assets/i18n/en.json`, etiketterne der skal oversættes.
   - `python tools/sync_wiki.py` genskaber wikiens kopi i `docs/wiki/` på GitHub.
2. **List, hvad der er ændret siden sidste udgivelse.** `git log --oneline v$(cat VERSION)..` (det
   sidste tag er `v` + versionen i `VERSION`). For hver nye eller ændrede kommando, indstilling,
   outputkolonne eller adfærd: opdater dens side, og tilføj en række i tabellen *Docs* i
   `CHANGELOG.md`.
3. **Uafhængig gennemgang.** En, der ikke skrev ændringen, læser de ændrede sider og diagrammer ud
   fra tre læsere: en **begynder** (har aldrig brugt en kommandolinje: kan de installere og køre det?),
   en **8-årig** (siger siden med almindelige ord, hvad det er og hvorfor?), og en **professionel**
   (stemmer indstillingerne, standarderne og kolonnerne med koden?). Kontrollér, at ingen side navngiver
   rigtige baner, kort, spillere eller optagelser: eksempler er syntetiske, og verifikationspåstande
   giver kun metoden og tolerancen.
4. **Ret fundene.**
5. **Oversæt.** Hver oversat side registrerer hashen af den engelske side, den blev lavet ud fra.
   Oversæt de sider igen, hvis engelske kildehash er ændret, samt de diagrametiketter, der er ændret;
   gennemgå derefter hvert sprog: klart for de tre læsere, diagrametiketterne rigtige, ordene passer
   til viewerens lokaliserede grænseflade.
6. **Skub kun efter ejerens grønne lys.** Mærk derefter udgivelsen `v<VERSION>`.

Ny i at køre disse kommandoer? [Før du begynder](before-you-start.md) forklarer Python og terminalen.

## Oversættelser: kommandoerne {#translations-the-commands}

Webstedet er oversat til 3DHeat-viewerens 40 sprog: engelsk i `docs/`, hvert andet sprog i
`docs/<lang>/` med de samme filnavne. `tools/docs_i18n.py` står for bogholderiet:

```bash
python tools/docs_i18n.py hashes             # efter enhver engelsk ændring: registrer hver sides hash
python tools/docs_i18n.py svg-strings        # efter enhver billedændring: etiketterne der skal oversættes
python tools/docs_i18n.py status             # pr. sprog: aktuelle, forældede og manglende sider
python tools/docs_i18n.py todo --lang de     # de tyske sider der skal (over)oversættes
python tools/docs_i18n.py svg-build --lang de    # tyske billeder ud fra docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stempel de tyske sider med deres engelske hash
python tools/docs_i18n.py check              # afslutter med 1, når hashes eller etiketter er forældede
```

Oversæt kun det, `todo` lister: behold Markdown, links, kode, fil- og kolonnenavne som de er, oversæt
titler og billedbeskrivelser, og brug 3DHeat-viewerens egne ord for dens knapper og paneler (dens
`src/i18n/locales/<lang>/`). Genererede referencesider og terminalbilleder forbliver engelske. På
webstedet siger en forældet oversættelse det og linker til den engelske side; en manglende falder
tilbage til engelsk. Sprogmenuen i sidehovedet og browsersprog-omdirigeringen på startsiden kommer
fra `docs/_includes/`.
