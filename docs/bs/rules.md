---
title: "Pravila"
nav_order: 2
lang: "bs"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Pravila pod kojima je ovo građeno {#the-rules-this-is-built-under}

Svaki dio 3DHeat GameCapture slijedi ista ograničenja. To su projektantske odluke,
a ne odricanja, i nekoliko ih namjerno košta tačnost.

## Ništa se ne ubacuje, ništa se ne kači {#nothing-is-injected-nothing-is-hooked}

Nijedan dio se ne veže na proces igre, ne čita njenu memoriju niti dira njen grafički API.

- **Kadrovi** dolaze iz Windows Graphics Capture, javnog API-ja koji koriste snimači ekrana
  (kroz paket `windows-capture`), ili iz video datoteke. Pogledajte
  [Snimanje, maske i kvalitet kadra](reconstruction-capture.md).
- **Telemetrija** dolazi samo iz sučelja koja igre za to objavljuju:
  - Forzin Data Out UDP tok, uključen u postavkama igre;
  - imenovane stranice dijeljene memorije koje Kunos igre objavljuju za aplikacije (`Local\acpmf_physics` i
    slične). Otvaraju se samo za čitanje pomoću `mmap`; to je dokumentiran način na koji aplikacije čitaju
    te stranice, a ne čitanje memorije procesa igre;
  - UDP telemetrija koju šalju EA SPORTS WRC, DiRT igre i Richard Burns Rally (kroz
    RSF/NGP dodatak) kad se uključi u njihovim vlastitim datotekama postavki;
  - BeamNG protokolno sučelje, kroz mali Lua "protokolni" mod koji igra učitava iz svog
    `lua/vehicle/protocols.lua` i šalje;
  - Trackmania Openplanet sučelje za dodatke, kroz dodatak koji samo čita ono što
    Openplanet izlaže i piše datoteke;
  - iRacingove vlastite `.ibt` telemetrijske datoteke.

## Zašto je to važno {#why-it-matters}

Igra tačno zna dubinu svakog piksela, a zakačen bafer dubine učinio bi rekonstrukciju
nivoa gotovo savršenom i trivijalnom. To bi značilo i ubacivanje u procese koji
mogu biti zaštićeni anti-cheatom, što dovodi u opasnost nalog svakoga ko to pokrene. Zato se dubina
umjesto toga *procjenjuje* iz slike ([Dubina](reconstruction-depth.md)), a veliki dio
cjevovoda rekonstrukcije postoji da povrati što više tako izgubljene tačnosti iz
izvora koji su slobodni za upotrebu: telemetrijskih poza gdje ih igra objavljuje, razmjera
ravni tla gdje ne objavljuje, i maski koje drže HUD i kokpit van rješavanja.

ReShade bafer dubine je razmatran i nije korišten. ReShade po dizajnu onemogućava pristup dubini u
multiplayer sesijama, pa bi pomogao samo igrama za jednog igrača (pogledajte
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Šta alat mijenja na tvom računaru, i to samo kad se traži {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Radnja | Kada | Šta tačno |
|---|---|---|
| Instalira Python pakete | prvo pokretanje prozora skeniranja, nakon dijaloga i potvrde | `pip install` u interpreter koji pokreće alat - uz `scan.bat`, privatni `.venv` pored njega. Nikad sam od sebe za cijeli sistem. |
| Pretvara model dubine | dugme "Set up the depth model", nakon drugog dijaloga za PyTorch i prateće pakete | piše `models/depth-small-518.onnx` |
| Uređuje `config.json` igre EA SPORTS WRC | `telemetry --game wrc --configure <file>` | uključuje paket `wrc` / `session_update` prema 127.0.0.1; stara datoteka se čuva kao `config.json.bak` |
| Kopira BeamNG mod | `telemetry --game beamng --install` | `mods/beamng/heat3d` u `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (zamjenjuje stariju kopiju) |
| Kopira Trackmania dodatak | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` u `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (zamjenjuje stariju kopiju) |
| Registrira globalne prečice | dok je prozor skeniranja otvoren (Windows) | Ctrl+Alt+F9 / F10 / F11, oslobađaju se kad se prozor zatvori |
| Ažurira alat | nakon što odgovorite s da na pitanje o ažuriranju, ili pokrenete `python -m heat3d_update` | pogledajte [Ažuriranja](updates.md) |

Datoteke `hardware_settings_config.xml` igara DiRT i `RichardBurnsRally.ini` igre Richard Burns Rally
alat **ne** uređuje; njihov UDP izlaz uključujete sami
(pogledajte [Rally igre](telemetry-rally.md)).

## Šta se čita i šta ostaje na tvom računaru {#what-is-read-and-what-stays-on-your-machine}

Alati čitaju ono što igra prikazuje na ekranu te telemetriju i datoteke koje igra za to objavljuje, na tvom vlastitom računaru. Ništa iz igre se ne isporučuje niti dalje distribuira: nikakvi resursi igre, nikakav kod igre, nikakvi DLL-ovi. Datoteke krugova, snimci, rekonstrukcije i izvezene staze ostaju na tvom računaru; `.gitignore` repozitorija drži snimke, datoteke krugova, mreže, težine modela i video van kontrole verzija po folderu i po tipu datoteke.

3DHeat GameCapture nije povezan ni sa jednim izdavačem igara niti ga on podržava. Nazivi igara i povezani zaštitni znakovi pripadaju njihovim vlasnicima. Nosioci prava: otvorite issue na [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - brzo odgovaramo i uklanjamo sve na zahtjev.
