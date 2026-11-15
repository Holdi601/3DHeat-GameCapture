---
title: "Päivitykset"
nav_order: 10
lang: "fi"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Päivitykset {#updates}

3DHeat GameCapture tarkistaa tämän repositorion GitHub-julkaisut käynnistyessään. Kun uudempi versio on ilmestynyt, se kertoo siitä ja tarjoaa päivittämistä. Koodi: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Milloin tarkistus ajetaan {#when-the-check-runs}

- `python -m heat3d_capture <verb>`: ennen komennon ajamista.
- `python -m heat3d_capture.ui` (ja `scan.bat`): ennen ikkunan avautumista.
- `python -m heat3d_update`: pyynnöstä. Se kysyy aina GitHubilta uudelleen.

## Miten tarkistus toimii {#how-the-check-works}

- Asennettu versio on repositorion juuressa oleva tiedosto `VERSION` (esimerkiksi `1.0.1`).
- Uusin julkaisu kysytään osoitteesta `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, **5 sekunnin** aikarajalla. Hidas verkko ei pysäytä työkalua pidemmäksi aikaa.
- Vastaus tallennetaan välimuistiin **6 tunniksi** tiedostoon `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json`. Ilman `LOCALAPPDATA`-muuttujaa se on `~/.cache/3DHeat/...`. Jokaisella 3DHeat-työkalulla on oma välimuistitiedostonsa. "Julkaisua ei vielä ole" (HTTP 404) tallennetaan vastauksena. Muut virheet eivät ole välimuistissa, ja ne tarkoittavat vain, ettei ilmoitusta tule.
- Versiot verrataan numeerisesti (`v1.2.3` tai `1.2.3`). Kaikki `-`:n tai `+`:n jälkeinen jätetään huomiotta.
- Offline-tilassa, nopeusrajoitettuna tai välityspalvelimen takana työkalu jatkaa sillä versiolla, joka sillä on.

## Mitä tapahtuu, kun uudempi julkaisu on ilmestynyt {#what-happens-when-a-newer-release-is-out}

Käynnistyessään se tulostaa virhevirtaan:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Kun päätteeseen on mihin vastata, se kysyy `Update now? [Y/n]`. Enter, `y`, `yes`, `j` ja `ja` tarkoittavat kyllä. Onnistuneen päivityksen jälkeen **sama komento käynnistetään uudelleen** uudella koodilla.
- Ilman päätettä (putki, ajastettu ajo) se tulostaa `Run python -m heat3d_update in <folder> to update.` ja jatkaa muuttumattomana.

## Miten päivitys tehdään {#how-an-update-is-applied}

Riippuu siitä, miten työkalut asennettiin:

- **Git-kloonaus** (`.git`-kansio ja `git` PATH:ssa): `git pull --ff-only`. Päivitys hylätään, kun kopiossa on paikallisia muutoksia seurattuihin tiedostoihin. Ne ovat jonkun työtä, joten tee niistä ensin commit tai talleta ne (stash).
- **Ladattu kopio**: julkaisun lähdearkisto ladataan ja puretaan väliaikaiseen kansioon. Arkiston oman kansion ulkopuoliset merkinnät ohitetaan. Kopio **tarkistetaan**, ja sen täytyy olla versio, jota se väittää olevansa, sen tiedostosta `VERSION`. Sitten sen tiedostot kopioidaan tämän kansion päälle. Julkaisun omissa Python-paketeissa (repositorion yläosan `heat3d_*`-kansiot ja yksi taso alempana vanhemmalle monorepo-rakenteelle) julkaisusta puuttuvat `.py`-moduulit poistetaan. Näin vanhentunut moduuli ei peitä korvaajaansa.

Omia tiedostojasi (tallenteita, kierrostiedostoja, asetuksia, vientejä ja `.venv`-kansiota) ei koskaan kosketa. Kirjoitetaan vain julkaisun osana olevat tiedostot.

## Käsin {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Se tulostaa `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, tai uuden version ja sen, mitä se teki. Poistumiskoodi on 1, jos päivitystä ei voitu tehdä.

## Kytkeminen pois päältä {#switching-it-off}

Aseta **`HEAT3D_NO_UPDATE=1`** (mikä tahansa arvo paitsi tyhjä, `0`, `false` tai `no`). Se kytkee pois käynnistystarkistuksen ja ilmoituksen. `python -m heat3d_update` tarkistaa edelleen, kun sen ajaa käsin.
