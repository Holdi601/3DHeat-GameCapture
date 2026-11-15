---
title: Održavanje ovih dokumenata
nav_order: 96
lang: "hr"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Održavanje ovih dokumenata {#maintaining-these-docs}

Popis za svako izdanje, da kod, engleske stranice i njihovi prijevodi ostanu usklađeni. Koraci se
izvode redom.

1. **Ponovno stvorite generirane stranice.**
   - `python tools/gen_docs_reference.py` ponovno piše [Referenca naredbi](../cli-reference.md) iz
     `--help` i popisa stupaca u kodu. `--check` izlazi s 1 kad je stranica zastarjela: pokrenite ga
     prije svakog izdanja.
   - `python tools/docs_diagrams.py` ponovno crta dijagrame u `docs/assets/img/`; `--strings` također
     osvježava `docs/assets/i18n/en.json`, oznake za prijevod.
   - `python tools/sync_wiki.py` ponovno stvara kopiju GitHub wikija u `docs/wiki/`.
2. **Popišite što se promijenilo od zadnjeg izdanja.** `git log --oneline v$(cat VERSION)..` (zadnja
   oznaka je `v` + verzija iz `VERSION`). Za svaku novu ili promijenjenu naredbu, opciju, stupac
   izlaza ili ponašanje: ažurirajte njezinu stranicu i dodajte redak u tablicu *Docs* u
   `CHANGELOG.md`.
3. **Neovisni pregled.** Netko tko nije napisao promjenu čita promijenjene stranice i dijagrame kao
   tri čitatelja: **početnik** (nikad nije koristio naredbeni redak: može li instalirati i pokrenuti
   alat?), **osmogodišnjak** (kaže li stranica jednostavnim riječima što je to i zašto?), i **pro**
   (odgovaraju li opcije, zadane vrijednosti i stupci kodu?). Provjerite da nijedna stranica ne
   spominje stvarne razine, karte, igrače ni snimke: primjeri su sintetički, a tvrdnje o provjeri
   daju samo metodu i toleranciju.
4. **Ispravite nalaze.**
5. **Prevedite.** Svaka prevedena stranica bilježi hash engleske stranice iz koje je nastala.
   Ponovno prevedite stranice čiji se izvorni hash promijenio, i oznake dijagrama koje su se
   promijenile; zatim pregledajte svaki jezik: jasno za tri čitatelja, ispravne oznake na dijagramima,
   riječi koje odgovaraju lokaliziranom sučelju pregledniku.
6. **Gurajte tek nakon dopuštenja vlasnika.** Zatim označite izdanje kao `v<VERSION>`.

Novi u pokretanju ovih naredbi? [Prije nego što počnete](before-you-start.md) pokriva Python i
terminal.

## Prijevodi: naredbe {#translations-the-commands}

Stranica je prevedena na 40 jezika preglednika 3DHeat: engleski je u `docs/`, svaki drugi jezik u
`docs/<lang>/` s istim nazivima datoteka. `tools/docs_i18n.py` vodi evidenciju:

```bash
python tools/docs_i18n.py hashes             # nakon svake promjene na engleskom: zabilježi hash svake stranice
python tools/docs_i18n.py svg-strings        # nakon promjene slike: oznake za prijevod
python tools/docs_i18n.py status             # po jeziku: ažurne, zastarjele i nedostajuće stranice
python tools/docs_i18n.py todo --lang de     # njemačke stranice za (ponovni) prijevod
python tools/docs_i18n.py svg-build --lang de    # njemačke slike iz docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # označi njemačke stranice hashom engleske
python tools/docs_i18n.py check              # izlazi s 1 kad su hashevi ili oznake zastarjeli
```

Prevodite samo ono što `todo` navodi: zadržite Markdown, poveznice, kod, nazive datoteka i stupaca, a
prevodite naslove i opise slika, i koristite vlastite riječi preglednika 3DHeat za njegove gumbe i
panele (u `src/i18n/locales/<lang>/`). Generirane stranice s referencama i terminalne slike ostaju na
engleskom. Na stranici se zastarjeli prijevod to kaže i upućuje na englesku stranicu; nedostajući
prijevod se vraća na engleski. Izbornik jezika u zaglavlju i preusmjeravanje početne stranice prema
jeziku pregledniku dolaze iz `docs/_includes/`.
