---
title: Underhålla dokumenten
nav_order: 96
lang: "sv"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Underhålla dokumenten {#maintaining-these-docs}

Checklistan för varje släpp, så att koden, de engelska sidorna och översättningarna
hänger ihop. Gör stegen i ordning.

1. **Skapa om de genererade sidorna.**
   - `python tools/gen_docs_reference.py` skriver om [Kommandoreferens](../cli-reference.md) från
     `--help` och kolumnlistorna i koden. `--check` avslutar med 1 när sidan är gammal: kör den
     före varje släpp.
   - `python tools/docs_diagrams.py` ritar om diagrammen i `docs/assets/img/`;
     `--strings` uppdaterar också `docs/assets/i18n/en.json`, etiketterna att översätta.
   - `python tools/sync_wiki.py` skapar om GitHub-wikins kopia i `docs/wiki/`.
2. **Lista vad som ändrats sedan det senaste släppet.** `git log --oneline v$(cat VERSION)..` (den
   senaste taggen är `v` + versionen i `VERSION`). För varje nytt eller ändrat kommando, alternativ,
   utdatakolumn eller beteende: uppdatera dess sida, och lägg till en rad i tabellen *Docs* i
   `CHANGELOG.md`.
3. **Oberoende granskning.** Någon som inte skrev ändringen läser de ändrade sidorna och
   diagrammen som tre läsare: en **nybörjare** (har aldrig använt en kommandorad: kan de installera
   och köra den?), en **åttaåring** (säger sidan med enkla ord vad det är och varför?), och en
   **proffs** (stämmer alternativen, standardvärdena och kolumnerna med koden?). Kontrollera att
   ingen sida nämner riktiga nivåer, kartor, spelare eller inspelningar: exempel är syntetiska, och
   verifieringspåståenden anger bara metoden och toleransen.
4. **Åtgärda fynden.**
5. **Översätt.** Varje översatt sida registrerar hashen för den engelska sida den gjordes från.
   Översätt om de sidor vars engelska källhash ändrats, och de diagrametiketter som ändrats;
   granska sedan varje språk: tydligt för de tre läsarna, diagrametiketterna rätt, orden stämmer
   med visarens lokaliserade gränssnitt.
6. **Skicka bara efter ägarens klartecken.** Tagga sedan släppet `v<VERSION>`.

Nytt med att köra de här kommandona? [Innan du börjar](before-you-start.md) förklarar Python och
terminalen.

## Översättningarna: kommandona {#translations-the-commands}

Webbplatsen är översatt till de 40 språk som 3DHeat-visaren har: engelska i `docs/`, varje annat
språk i `docs/<lang>/` med samma filnamn. `tools/docs_i18n.py` sköter bokföringen:

```bash
python tools/docs_i18n.py hashes             # efter varje engelsk ändring: registrera varje sidas hash
python tools/docs_i18n.py svg-strings        # efter varje bildändring: etiketterna att översätta
python tools/docs_i18n.py status             # per språk: aktuella, gamla och saknade sidor
python tools/docs_i18n.py todo --lang de     # de tyska sidorna att (över)översätta
python tools/docs_i18n.py svg-build --lang de    # tyska bilder från docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # märk de tyska sidorna med deras engelska hash
python tools/docs_i18n.py check              # avslutar med 1 när hashar eller etiketter är gamla
```

Översätt bara det `todo` listar: behåll Markdown, länkar, kod, fil- och kolumnnamn som de är, och
översätt titlar och bildbeskrivningar. Använd 3DHeat-visarens egna ord för dess knappar och paneler
(dess `src/i18n/locales/<lang>/`). Genererade referenssidor och terminalbilder förblir på engelska.
På webbplatsen säger en gammal översättning det och länkar den engelska sidan; en saknad faller
tillbaka till engelska. Språkmenyn i sidhuvudet och webbläsarspråkets omdirigering på startsidan
kommer från `docs/_includes/`.
