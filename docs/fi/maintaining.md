---
title: "Dokumentaation ylläpito"
nav_order: 96
lang: "fi"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Dokumentaation ylläpito {#maintaining-these-docs}

Julkaisukohtainen tarkistuslista, jotta koodi, englanninkieliset sivut ja niiden käännökset pysyvät samassa tahdissa. Tee vaiheet järjestyksessä.

1. **Luo generoidut sivut uudelleen.**
   - `python tools/gen_docs_reference.py` kirjoittaa uudelleen [Komentoviite](../cli-reference.md)-sivun kohdasta `--help` ja koodin sarakeluetteloista. `--check` päättyy koodiin 1, kun sivu on vanhentunut. Aja se ennen jokaista julkaisua.
   - `python tools/docs_diagrams.py` piirtää kaaviot uudelleen kansioon `docs/assets/img/`. `--strings` päivittää lisäksi `docs/assets/i18n/en.json`-tiedoston, eli käännettävät tunnisteet.
   - `python tools/sync_wiki.py` luo GitHub-wikin kopion uudelleen kansioon `docs/wiki/`.
2. **Listaa, mikä on muuttunut edellisen julkaisun jälkeen.** `git log --oneline v$(cat VERSION)..` (viimeinen tagi on `v` ja tiedoston `VERSION` versio). Jokaiselle uudelle tai muuttuneelle komennolle, valinnalle, tulostesarakkeelle tai toiminnalle: päivitä sen sivu ja lisää rivi tiedoston `CHANGELOG.md` *Docs*-taulukkoon.
3. **Riippumaton tarkistus.** Joku, joka ei kirjoittanut muutosta, lukee muuttuneet sivut ja kaaviot kolmena lukijana: **aloittelija** (ei ole koskaan käyttänyt komentoriviä: osaako hän asentaa ja ajaa työkalun?), **8-vuotias** (kertooko sivu selkein sanoin, mitä se on ja miksi?) ja **ammattilainen** (vastaavatko valinnat, oletusarvot ja sarakkeet koodia?). Tarkista, ettei mikään sivu nimeä oikeita tasoja, karttoja, pelaajia tai tallenteita. Esimerkit ovat synteettisiä, ja todentamisväitteet kertovat vain menetelmän ja toleranssin.
4. **Korjaa havainnot.**
5. **Käännä.** Jokainen käännetty sivu tallentaa englanninkielisen lähdesivun tiivisteen, josta se tehtiin. Käännä uudelleen sivut, joiden englanninkielisen lähteen tiiviste muuttui, sekä muuttuneet kaaviotunnisteet. Tarkista sen jälkeen jokainen kieli: se on selkeä kolmelle lukijalle, kaaviotunnisteet ovat oikein, ja sanat vastaavat katselimen lokalisoitua käyttöliittymää.
6. **Työnnä vasta omistajan luvalla.** Merkitse sen jälkeen julkaisu tagilla `v<VERSION>`.

Uusi komentojen ajamisessa? [Ennen aloittamista](before-you-start.md) kertoo Pythonista ja päätteestä.

## Käännökset: komennot {#translations-the-commands}

Sivusto on käännetty 3DHeat-katselimen 40 kielelle. Englanti on kansiossa `docs/`, ja muut kielet ovat kansiossa `docs/<lang>/` samoilla tiedostonimillä. `tools/docs_i18n.py` hoitaa kirjanpidon:

```bash
python tools/docs_i18n.py hashes             # englanninkielisen muutoksen jälkeen: tallenna jokaisen sivun tiiviste
python tools/docs_i18n.py svg-strings        # kuvamuutoksen jälkeen: käännettävät tunnisteet
python tools/docs_i18n.py status             # kielittäin: ajantasaiset, vanhentuneet ja puuttuvat sivut
python tools/docs_i18n.py todo --lang de     # saksankieliset sivut, jotka käännetään (uudelleen)
python tools/docs_i18n.py svg-build --lang de    # saksankieliset kuvat tiedostosta docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # merkitse saksankieliset sivut englanninkielisen tiivisteen mukaan
python tools/docs_i18n.py check              # päättyy koodiin 1, kun tiivisteet tai tunnisteet ovat vanhentuneet
```

Käännä vain se, mitä `todo` listaa. Säilytä Markdown, linkit, koodi sekä tiedosto- ja sarakenimet sellaisinaan. Käännä otsikot ja kuvien kuvaukset. Käytä 3DHeat-katselimen omia sanoja sen painikkeille ja paneeleille (sen `src/i18n/locales/<lang>/`). Generoidut viitesivut ja terminaalikuvat pysyvät englanniksi. Sivustolla vanhentunut käännös kertoo sen ja linkittää englanninkieliseen sivuun. Puuttuva käännös palaa englanniksi. Ylätunnisteen kielivalikko ja etusivun selaimen kielen mukainen uudelleenohjaus tulevat kansiosta `docs/_includes/`.
