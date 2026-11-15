---
title: A szabályok
nav_order: 2
lang: "hu"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# A szabályok, amelyek alapján készült {#the-rules-this-is-built-under}

A 3DHeat GameCapture minden részét ugyanazok a megkötések szabályozzák. Ezek tervezési döntések, nem
jogi nyilatkozatok, és több közülük szándékosan pontosságot áldoz fel.

## Semmi nem kerül be, semmire nem kapcsolunk rá {#nothing-is-injected-nothing-is-hooked}

Semmi ebben nem kapcsolódik játékfolyamathoz, nem olvassa a memóriáját, és nem nyúl a grafikus API-hoz.

- **A képkockák** a Windows Graphics Capture-ből jönnek, a nyilvános API-ból, amelyet a képernyőrögzítők
  használnak (a `windows-capture` csomagon keresztül), vagy egy videófájlból. Lásd:
  [Rögzítés, maszkok és képkockaminőség](reconstruction-capture.md).
- **A telemetria** csak azokból a felületekből jön, amelyeket a játékok erre közzétesznek:
  - a Forza Data Out UDP-csatornája, a játék beállításaiban bekapcsolva;
  - a Kunos-játékok által alkalmazásoknak közzétett, megnevezett megosztott memóriaoldalak (`Local\acpmf_physics`
    és társai). Csak olvasásra nyitjuk meg őket `mmap`-pel; ez az alkalmazások dokumentált módja ezek olvasására,
    nem a játékfolyamat memóriájának olvasása;
  - az UDP-telemetria, amelyet az EA SPORTS WRC, a DiRT-játékok és a Richard Burns Rally (az RSF/NGP bővítményen
    keresztül) küld, ha a saját beállítási fájljaikban be van kapcsolva;
  - a BeamNG protokollfelülete, egy kis Lua „protokoll” módosításon keresztül, amelyet a játék saját
    `lua/vehicle/protocols.lua` fájlja tölt be és küld;
  - a Trackmania Openplanet-bővítményének felülete, egy bővítményen keresztül, amely csak azt olvassa, amit az
    Openplanet megmutat, és fájlokat ír;
  - az iRacing saját `.ibt` telemetriafájljai.

## Miért számít {#why-it-matters}

A játék minden pixel mélységét pontosan ismeri, és egy kiolvasott mélységi puffer szinte tökéletessé és
triviálissá tenné a pályarekonstrukciót. Ugyanakkor olyan folyamatokba kellene beavatkozni, amelyeket
csalásvédelem védhet, ami bárki fiókját kockára teheti, aki futtatja. Ezért a mélységet a képből **becsüljük**
([Mélység](reconstruction-depth.md)), a rekonstrukciós folyamat nagy része pedig azért létezik, hogy a pontosság
elvesztett részét olyan forrásokból nyerje vissza, amelyek szabadon használhatók: a telemetriai pozíciókból
ahol a játék közzéteszi őket, a talajsíkos méretarányból ahol nem, és olyan maszkokból, amelyek a HUD-ot és a
pilótafülkét kizárják a megoldásból.

A ReShade mélységi pufferét megvizsgáltuk, de nem használtuk. A ReShade többjátékos munkamenetekben tervezetten
letiltja a mélységhozzáférést, így csak egyjátékos címeknél segítene (lásd
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Dolgok, amelyeket az eszköz a gépén megváltoztat, és csak kérésre {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Művelet | Mikor | Pontosan mi |
|---|---|---|
| Python-csomagokat telepít | a szkennelőablak első futtatásakor, egy párbeszédablak és egy igen után | `pip install` abba az értelmezőbe, amely az eszközt futtatja - a `scan.bat`-tal a mellette lévő privát `.venv`-be. Önmagában sosem rendszerszintesen. |
| Átalakítja a mélységmodellt | a „Mélységmodell beállítása” gomb, egy második párbeszédablak után a PyTorch és társai miatt | a `models/depth-small-518.onnx` fájlt írja |
| Módosítja az EA SPORTS WRC `config.json` fájlját | `telemetry --game wrc --configure <file>` | a `wrc` / `session_update` csomagot 127.0.0.1 felé bekapcsolja; a régi fájl `config.json.bak` néven megmarad |
| Másolja a BeamNG-módosítást | `telemetry --game beamng --install` | a `mods/beamng/heat3d` mappát a `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` helyre (egy régebbi másolatot felülírva) |
| Másolja a Trackmania-bővítményt | `telemetry --game trackmania --install` | a `mods/trackmania/Heat3dRecorder` mappát a `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` helyre (egy régebbi másolatot felülírva) |
| Globális gyorsbillentyűket regisztrál | amíg a szkennelőablak nyitva van (Windows) | Ctrl+Alt+F9 / F10 / F11, az ablak bezárásakor felszabadítva |
| Frissíti az eszközt | miután a frissítési kérdésre igent mond, vagy a `python -m heat3d_update` futtatásakor | lásd: [Frissítések](updates.md) |

A DiRT-játékok `hardware_settings_config.xml` fájlját és a Richard Burns Rally `RichardBurnsRally.ini` fájlját az
eszköz **nem** módosítja; ezeken az UDP-kimenetet önnek kell bekapcsolnia (lásd: [Rally-játékok](telemetry-rally.md)).

## Ami a felhasználó felelőssége {#what-stays-the-users-responsibility}

Hogy mire irányítja a felhasználó az eszközöket, az továbbra is az adott játék licencére és EULA-jára tartozik.
A körfájlok, felvételek, rekonstrukciók és exportált pályák annak a személynek a tulajdonában vannak, aki a játékot
és az adatot birtokolja; a tároló `.gitignore` fájlja a felvételeket, körfájlokat, hálókat, modellsúlyokat és
videókat mappa és fájltípus szerint kizárja a verziókezelésből.
