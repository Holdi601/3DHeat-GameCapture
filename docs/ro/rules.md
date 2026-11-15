---
title: "Regulile"
nav_order: 2
lang: "ro"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Regulile după care este construit {#the-rules-this-is-built-under}

Fiecare parte a 3DHeat GameCapture urmează aceleași constrângeri. Sunt decizii de proiectare, nu
clauze de excludere a răspunderii, iar câteva dintre ele costă precizie în mod intenționat.

## Nimic nu este injectat, nimic nu este agățat {#nothing-is-injected-nothing-is-hooked}

Nicio parte a acestui proiect nu se atașează de un proces de joc, nu citește memoria lui și nu atinge
interfața lui grafică.

- **Cadrele** vin de la Windows Graphics Capture, API-ul public pe care îl folosesc înregistratoarele
  de ecran (prin pachetul `windows-capture`), sau dintr-un fișier video. Vezi
  [Captura, măștile și calitatea cadrului](reconstruction-capture.md).
- **Telemetria** vine doar din interfețele pe care jocurile le publică pentru asta:
  - fluxul UDP Data Out al Forza, pornit din setările jocului;
  - paginile de memorie partajată cu nume pe care jocurile Kunos le publică pentru aplicații
    (`Local\acpmf_physics` și altele). Sunt deschise doar pentru citire, cu `mmap`; aceasta este
    modalitatea documentată prin care aplicațiile le citesc, nu citirea memoriei procesului jocului;
  - telemetria UDP pe care o trimit EA SPORTS WRC, jocurile DiRT și Richard Burns Rally (prin
    modulul RSF/NGP), când este pornită în fișierele lor de setări;
  - interfața de protocol a BeamNG, printr-o mică modificare Lua de „protocol” pe care protocols.lua
    propriu al jocului, din `lua/vehicle/protocols.lua`, o încarcă și o trimite;
  - interfața modulului Openplanet al Trackmania, printr-un modul care citește doar ce expune
    Openplanet și scrie fișiere;
  - fișierele proprii de telemetrie `.ibt` ale iRacing.

## De ce contează {#why-it-matters}

Jocul cunoaște exact adâncimea fiecărui pixel, iar un buffer de adâncime agățat ar face reconstrucția
nivelului aproape perfectă și banală. Ar mai însemna și injectarea în procese care pot fi protejate de
anti-cheat, ceea ce riscă contul oricui o rulează. Așa că adâncimea este *estimată* din imagine
([Adâncimea](reconstruction-depth.md)), iar o mare parte din pipeline-ul de reconstrucție există ca
să recupereze cât mai multă din precizia pierdută din surse libere de folosit: pozele de telemetrie
acolo unde un joc le publică, o scară din planul solului acolo unde nu le publică, și măști care țin
HUD-ul și cabina afară din rezolvare.

Buffer-ul de adâncime din ReShade a fost luat în calcul și nu a fost folosit. ReShade dezactivează
accesul la adâncime în sesiunile multiplayer prin design, deci ar ajuta doar titlurile single-player
(vezi [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Lucruri pe care unealta le schimbă pe calculatorul dumneavoastră, și doar la cerere {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Acțiune | Când | Ce anume |
|---|---|---|
| Instalează pachete Python | prima rulare a ferestrei de scanare, după o casetă de dialog și un da | `pip install` în interpretorul care rulează unealta - cu `scan.bat`, `.venv` privat de lângă el. Niciodată la nivel de sistem de la sine. |
| Convertește modelul de adâncime | butonul „Set up the depth model”, după o a doua casetă de dialog pentru PyTorch și altele | scrie `models/depth-small-518.onnx` |
| Editează `config.json` din EA SPORTS WRC | `telemetry --game wrc --configure <file>` | pornește pachetul `wrc` / `session_update` spre 127.0.0.1; fișierul vechi este păstrat ca `config.json.bak` |
| Copiază modificarea pentru BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` în `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (înlocuind o copie mai veche) |
| Copiază modulul pentru Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` în `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (înlocuind o copie mai veche) |
| Înregistrează taste rapide globale | cât timp fereastra de scanare este deschisă (Windows) | Ctrl+Alt+F9 / F10 / F11, eliberate când fereastra se închide |
| Actualizează unealta | după ce răspundeți da la întrebarea de actualizare, sau rulând `python -m heat3d_update` | vezi [Actualizări](updates.md) |

`hardware_settings_config.xml` al jocurilor DiRT și `RichardBurnsRally.ini` al Richard Burns Rally
**nu** sunt editate de unealtă; pornirea ieșirii UDP trebuie s-o faceți dumneavoastră (vezi
[Jocurile de raliu](telemetry-rally.md)).

## Ce rămâne în responsabilitatea utilizatorului {#what-stays-the-users-responsibility}

Ce indicați uneltelor către rămâne supus licenței și EULA-ei jocului respectiv. Fișierele de tur,
înregistrările, reconstrucțiile și traseele exportate aparțin celui care deține jocul și datele;
`.gitignore` al depozitului ține înregistrările, fișierele de tur, plasele, greutățile modelelor și
video-ul afară din controlul versiunilor, pe foldere și pe tip de fișier.
