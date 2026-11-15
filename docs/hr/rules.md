---
title: Pravila na kojima je ovo izgrađeno
nav_order: 2
lang: "hr"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Pravila na kojima je ovo izgrađeno {#the-rules-this-is-built-under}

Svaki dio 3DHeat GameCapture slijedi ista ograničenja. To su projektne odluke, a ne izjave o
odricanju odgovornosti, i nekoliko ih namjerno košta točnosti.

## Ništa se ne ubacuje, ništa se ne kuka {#nothing-is-injected-nothing-is-hooked}

Nijedan dio ovoga se ne veže na proces igre, ne čita njezinu memoriju i ne dira njezin API za grafiku.

- **Kadrovi** dolaze iz Windows Graphics Capture, javnog API-ja koji koriste snimači zaslona (kroz
  paket `windows-capture`), ili iz video datoteke. Vidi
  [Snimanje, maske i kvaliteta kadra](reconstruction-capture.md).
- **Telemetrija** dolazi samo iz sučelja koja igre objavljuju za tu svrhu:
  - Forzin Data Out UDP tok, uključen u postavkama igre;
  - imenovane stranice dijeljene memorije koje Kunos igre objavljuju za aplikacije (`Local\acpmf_physics`
    i srodne). Otvaraju se samo za čitanje pomoću `mmap`; to je dokumentirani način na koji aplikacije
    ih čitaju, a ne čitanje memorije procesa igre;
  - UDP telemetriju koju EA SPORTS WRC, igre DiRT i Richard Burns Rally (kroz RSF/NGP dodatak) šalju kad
    je uključena u njihovim vlastitim postavkama;
  - protokolsko sučelje BeamNG-a, kroz mali Lua "protocol" mod koji ga učitava vlastiti
    `lua/vehicle/protocols.lua` igre i koji ga šalje;
  - sučelje dodatka Trackmanije Openplanet, kroz dodatak koji čita samo ono što Openplanet izlaže i
    piše datoteke;
  - vlastite `.ibt` telemetrijske datoteke iRacinga.

## Zašto je to važno {#why-it-matters}

Igra točno zna dubinu svakog piksela, a zahvaćeni spremnik dubine učinio bi rekonstrukciju razine
gotovo savršenom i trivijalnom. Značilo bi i ubacivanje u procese koji mogu biti zaštićeni protiv
varanja, što ugrožava račun svakoga tko to pokrene. Zato se dubina *procjenjuje* iz slike
([Dubina](reconstruction-depth.md)), a velik dio cjevovoda za rekonstrukciju postoji da povrati što
više izgubljene točnosti iz izvora koji su slobodni za upotrebu: telemetrijskih položaja gdje ih igra
objavljuje, mjerila iz ravnine tla gdje ne objavljuje, i maski koje HUD i kokpit drže izvan rješenja.

ReShadeov spremnik dubine je razmatran i nije korišten. ReShade isključuje pristup dubini u
višekorisničkim sesijama po dizajnu, pa bi pomogao samo jednoigračkim naslovima (vidi
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Što alat mijenja na vašem računalu, i samo kad se to traži {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Radnja | Kada | Što točno |
|---|---|---|
| Instalira Python pakete | prvo pokretanje prozora skeniranja, nakon dijaloga i potvrde | `pip install` u interpreter koji pokreće alat - uz `scan.bat`, privatni `.venv` pored njega. Nikad sustavno sam od sebe. |
| Pretvara model dubine | gumb "Set up the depth model", nakon drugog dijaloga za PyTorch i srodno | piše `models/depth-small-518.onnx` |
| Mijenja `config.json` igre EA SPORTS WRC | `telemetry --game wrc --configure <file>` | uključuje paket `wrc` / `session_update` na 127.0.0.1; stara datoteka se čuva kao `config.json.bak` |
| Kopira BeamNG mod | `telemetry --game beamng --install` | `mods/beamng/heat3d` u `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (zamjenjujući stariju kopiju) |
| Kopira dodatak za Trackmaniju | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` u `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (zamjenjujući stariju kopiju) |
| Registrira globalne prečace | dok je prozor skeniranja otvoren (Windows) | Ctrl+Alt+F9 / F10 / F11, otpuštaju se kad se prozor zatvori |
| Ažurira alat | nakon što potvrdite upit za ažuriranje, ili pokrenete `python -m heat3d_update` | vidi [Ažuriranja](updates.md) |

Datoteke `hardware_settings_config.xml` igara DiRT i `RichardBurnsRally.ini` alat **ne** mijenja;
izlaz UDP-a uključujete sami (vidi [Rally igre](telemetry-rally.md)).

## Što ostaje odgovornost korisnika {#what-stays-the-users-responsibility}

Što korisnik usmjeri prema alatima ostaje podložno licenci i EULA-i te igre. Datoteke krugova,
snimke, rekonstrukcije i izvezene staze pripadaju onome tko posjeduje igru i podatke; `.gitignore`
repozitorija drži snimke, datoteke krugova, mreže, težine modela i video izvan verzioniranja, po mapi i
po vrsti datoteke.
