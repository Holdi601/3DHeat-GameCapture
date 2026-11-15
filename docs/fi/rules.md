---
title: "Säännöt"
nav_order: 2
lang: "fi"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Säännöt, joiden mukaan tämä on rakennettu {#the-rules-this-is-built-under}

Jokainen 3DHeat GameCapturen osa noudattaa samoja rajoituksia. Ne ovat suunnittelupäätöksiä, eivät vastuuvapauslausekkeita, ja useat niistä maksavat tarkkuutta tarkoituksella.

## Mitään ei injektoida, mihinkään ei kiinnitetä {#nothing-is-injected-nothing-is-hooked}

Mikään tämän osa ei kiinnity pelin prosessiin, lue sen muistia eikä koske sen grafiikkarajapintaan.

- **Kehykset** tulevat Windows Graphics Capturesta. Se on julkinen rajapinta, jota ruudunauhurit käyttävät (`windows-capture`-paketin kautta), tai videotiedostosta. Katso [Tallennus, maskit ja kehyksen laatu](reconstruction-capture.md).
- **Telemetria** tulee vain rajapinnoista, jotka pelit julkaisevat sitä varten:
  - Forzan Data Out -UDP-syöte, joka kytketään päälle pelin asetuksista;
  - Kunos-pelien sovelluksille julkaisemat nimetyt jaetun muistin sivut (`Local\acpmf_physics` ja muut). Ne avataan vain lukuun `mmap`-kutsulla. Sovellukset lukevat ne tällä dokumentoidulla tavalla, eikä kyse ole pelin prosessin muistin lukemisesta;
  - UDP-telemetria, jota EA SPORTS WRC, DiRT-pelit ja Richard Burns Rally (RSF/NGP-liitännäisen kautta) lähettävät, kun ne kytketään päälle omissa asetustiedostoissaan;
  - BeamNG:n protokollarajapinta pienen Lua-"protokolla"-modin kautta. Pelin oma `lua/vehicle/protocols.lua` lataa ja lähettää sen;
  - Trackmanian Openplanet-liitännäisen rajapinta. Liitännäinen lukee vain sen, minkä Openplanet paljastaa, ja kirjoittaa tiedostoja;
  - iRacingin oma `.ibt`-telemetriatiedosto.

## Miksi tällä on merkitystä {#why-it-matters}

Peli tuntee jokaisen pikselin syvyyden tarkasti. Kiinnitetty syvyyspuskuri tekisi tason rekonstruoinnista lähes täydellisen ja helpon. Se tarkoittaisi myös injektointia prosesseihin, joita anti-cheat voi suojata, ja se uhkaisi kenen tahansa tilin, joka sitä ajaa. Siksi syvyys *arvioidaan* sen sijaan kuvasta ([Syvyys](reconstruction-depth.md)). Suuri osa rekonstruktioputkesta on olemassa, jotta menetetystä tarkkuudesta saadaan takaisin mahdollisimman paljon lähteistä, joita saa vapaasti käyttää. Näitä ovat telemetria-asennot siellä, missä peli ne julkaisee, maa-tason mittakaava siellä, missä niitä ei ole, ja maskit, jotka pitävät HUDin ja ohjaamon ratkaisusta ulkona.

ReShaden syvyyspuskuria harkittiin, mutta sitä ei käytetty. ReShade poistaa syvyyden käytön moninpeliistunnoissa suunnitelmallisesti, joten se auttaisi vain yksinpelinimikkeitä (katso [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Asiat, joita työkalu muuttaa koneellasi, ja vain pyydettäessä {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Toiminto | Milloin | Tarkalleen mitä |
|---|---|---|
| Asentaa Python-paketteja | skannausikkunan ensimmäinen käynnistys, dialogin ja kyllä-vastauksen jälkeen | `pip install` työkalua ajavaan tulkkiin. `scan.bat`-tiedoston kanssa se on sen vieressä oleva yksityinen `.venv`-kansio. Ei koskaan koko järjestelmään itsestään. |
| Muuntaa syvyysmallin | painike "Set up the depth model", toisen dialogin jälkeen PyTorchille ja muille | kirjoittaa `models/depth-small-518.onnx` |
| Muokkaa EA SPORTS WRC:n `config.json`-tiedostoa | `telemetry --game wrc --configure <file>` | kytkee paketin `wrc` / `session_update` päälle osoitteeseen 127.0.0.1. Vanha tiedosto säilytetään nimellä `config.json.bak` |
| Kopioi BeamNG-modin | `telemetry --game beamng --install` | `mods/beamng/heat3d` kansioon `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (korvaa vanhemman kopion) |
| Kopioi Trackmania-liitännäisen | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` kansioon `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (korvaa vanhemman kopion) |
| Rekisteröi yleiset pikanäppäimet | skannausikkunan ollessa auki (Windows) | Ctrl+Alt+F9 / F10 / F11, vapautetaan, kun ikkuna sulkeutuu |
| Päivittää työkalun | kun vastaat kyllä päivityskehotteeseen tai ajat `python -m heat3d_update` | katso [Päivitykset](updates.md) |

Työkalu **ei** muokkaa DiRT-pelien `hardware_settings_config.xml`-tiedostoa eikä Richard Burns Rallyn `RichardBurnsRally.ini`-tiedostoa. Kytket niiden UDP-ulostulon päälle itse (katso [Rallipelit](telemetry-rally.md)).

## Mistä käyttäjä vastaa {#what-stays-the-users-responsibility}

Mihin käyttäjä työkalut osoittaa, on edelleen kyseisen pelin lisenssin ja EULA:n alainen. Kierrostiedostot, tallenteet, rekonstruktiot ja viedyt radat kuuluvat sille, joka omistaa pelin ja datan. Repositorion `.gitignore` pitää tallenteet, kierrostiedostot, verkot, mallipainot ja videot poissa versionhallinnasta kansioiden ja tiedostotyyppien mukaan.
