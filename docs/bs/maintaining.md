---
title: "Održavanje ove dokumentacije"
nav_order: 96
lang: "bs"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Održavanje ove dokumentacije {#maintaining-these-docs}

Kontrolna lista za svako izdanje, da kod, engleske stranice i njihovi prijevodi ostanu
usklađeni. Radi korake redom.

1. **Iznova generiraj generirane stranice.**
   - `python tools/gen_docs_reference.py` iznova piše [Referencu komandi](../cli-reference.md) iz
     `--help` i popisa kolona u kodu. `--check` izlazi s 1 kad je stranica zastarjela: pokrenite ga
     prije svakog izdanja.
   - `python tools/docs_diagrams.py` iznova crta dijagrame u `docs/assets/img/`;
     `--strings` osvježava i `docs/assets/i18n/en.json`, oznake za prevođenje.
   - `python tools/sync_wiki.py` iznova generira kopiju GitHub wikija u `docs/wiki/`.
2. **Navedite šta se promijenilo od zadnjeg izdanja.** `git log --oneline v$(cat VERSION)..` (zadnja
   oznaka je `v` + verzija iz `VERSION`). Za svaku novu ili izmijenjenu komandu, opciju, izlaznu
   kolonu ili ponašanje: ažurirajte njenu stranicu i dodajte red u tabelu *Docs* u `CHANGELOG.md`.
3. **Nezavisni pregled.** Neko ko nije pisao promjenu čita izmijenjene stranice i
   dijagrame kao tri čitaoca: **početnik** (nikad nije koristio komandnu liniju: može li
   instalirati i pokrenuti?), **osmogodišnjak** (kaže li stranica jednostavnim riječima šta je i zašto?)
   i **profesionalac** (poklapaju li se opcije, zadane vrijednosti i kolone s kodom?). Provjerite da nijedna stranica ne imenuje prave nivoe,
   mape, igrače ili snimke: primjeri su sintetički, tvrdnje o provjeri daju samo metodu
   i toleranciju.
4. **Popravi nalaze.**
5. **Prevedi.** Svaka prevedena stranica bilježi hash engleske stranice iz koje je nastala.
   Ponovo prevedi stranice kojima se promijenio hash engleskog izvora, i oznake dijagrama koje su se promijenile;
   zatim pregledajte svaki jezik: jasno za tri čitaoca, oznake dijagrama tačne, riječi u skladu
   s lokaliziranim sučeljem preglednika.
6. **Šaljite tek uz odobrenje vlasnika.** Zatim označite izdanje sa `v<VERSION>`.

Novo vam je pokretanje ovih komandi? [Prije nego počnete](before-you-start.md) pokriva Python i
terminal.

## Prijevodi: komande {#translations-the-commands}

Stranica je prevedena na 40 jezika preglednika 3DHeat: engleski u `docs/`, svaki drugi
jezik u `docs/<lang>/` s istim imenima datoteka. `tools/docs_i18n.py` vodi evidenciju:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Prevodi samo ono što navede `todo`: Markdown, linkove, kod, imena datoteka i kolona ostavite kakvi jesu,
prevedite naslove i opise slika, i koristite vlastite riječi preglednika 3DHeat za njegova dugmad
i panele (njegov `src/i18n/locales/<lang>/`). Generirane referentne stranice i slike terminala ostaju
na engleskom. Na stranici zastarjeli prijevod to kaže i linka na englesku stranicu; nedostajući
se vraća na engleski. Jezični meni u zaglavlju i preusmjeravanje početne stranice prema jeziku preglednika
dolaze iz `docs/_includes/`.
