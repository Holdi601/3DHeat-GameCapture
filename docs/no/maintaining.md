---
title: Vedlikehold av disse dokumentene
nav_order: 96
lang: "no"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Vedlikehold av disse dokumentene {#maintaining-these-docs}

Sjekklisten for hver utgivelse, slik at koden, de engelske sidene og oversettelsene holder følge.
Gjør trinnene i rekkefølge.

1. **Lag de genererte sidene på nytt.**
   - `python tools/gen_docs_reference.py` skriver [Kommandoreferanse](../cli-reference.md) på nytt fra
     `--help` og kolonnelistene i koden. `--check` avslutter med 1 når siden er utdatert. Kjør den
     før hver utgivelse.
   - `python tools/docs_diagrams.py` tegner diagrammene i `docs/assets/img/` på nytt.
     `--strings` oppdaterer også `docs/assets/i18n/en.json`, etikettene som skal oversettes.
   - `python tools/sync_wiki.py` lager GitHub-wikiens kopi i `docs/wiki/` på nytt.
2. **List opp det som er endret siden forrige utgivelse.** `git log --oneline v$(cat VERSION)..`
   (den siste taggen er `v` + versjonen i `VERSION`). For hver nye eller endrede kommando, innstilling,
   utdatakolonne eller oppførsel: oppdater siden, og legg til en rad i tabellen *Docs* i
   `CHANGELOG.md`.
3. **Uavhengig gjennomgang.** Noen som ikke skrev endringen leser de endrede sidene og diagrammene
   som tre lesere: en **nybegynner** (har aldri brukt en kommandolinje: kan de installere og kjøre
   det?), en **8-åring** (sier siden med enkle ord hva det er og hvorfor?), og en **proff** (stemmer
   innstillinger, standardverdier og kolonner med koden?). Sjekk at ingen side nevner ekte nivåer,
   kart, spillere eller opptak. Eksemplene skal være syntetiske, og påstander om verifisering skal
   bare oppgi metoden og toleransen.
4. **Rett det som ble funnet.**
5. **Oversett.** Hver oversatt side registrerer hashen til den engelske siden den ble laget fra.
   Oversett på nytt de sidene der hashen til den engelske kilden har endret seg, og de
   diagrametikettene som har endret seg. Gå deretter gjennom hvert språk: klart for de tre leserne,
   riktige diagramtekster, og ord som stemmer med visningsprogrammets oversatte grensesnitt.
6. **Send først etter eierens klarsignal.** Deretter taggs utgivelsen `v<VERSION>`.

Ny til å kjøre disse kommandoene? [Før du starter](before-you-start.md) forklarer Python og
terminalen.

## Oversettelser: kommandoene {#translations-the-commands}

Nettstedet er oversatt til de 40 språkene i 3DHeat-visningsprogrammet. Engelsk ligger i `docs/`, og
hvert annet språk i `docs/<lang>/` med de samme filnavnene. `tools/docs_i18n.py` sørger for
bokføringen:

```bash
python tools/docs_i18n.py hashes             # etter enhver endring i engelsk: registrer hashen til hver side
python tools/docs_i18n.py svg-strings        # etter enhver endring i bilder: etikettene som skal oversettes
python tools/docs_i18n.py status             # per språk: oppdaterte, utdaterte og manglende sider
python tools/docs_i18n.py todo --lang de     # de tyske sidene som skal (over)oversettes
python tools/docs_i18n.py svg-build --lang de    # tyske bilder fra docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # merk de tyske sidene med hashen til den engelske
python tools/docs_i18n.py check              # avslutter med 1 når hashene eller etikettene er utdaterte
```

Oversett bare det `todo` lister. Behold Markdown, lenker, kode, filnavn og kolonnenavn slik de er.
Oversett titler og bildebeskrivelser, og bruk 3DHeat-visningsprogrammets egne ord for knapper og
paneler (i `src/i18n/locales/<lang>/`). Genererte referansesider og terminalbilder forblir engelske.
På nettstedet sier en utdatert oversettelse fra om det, og lenker til den engelske siden. En manglende
oversettelse faller tilbake til engelsk. Språkmenyen i toppteksten og omdirigeringen på forsiden etter
nettleserens språk kommer fra `docs/_includes/`.
