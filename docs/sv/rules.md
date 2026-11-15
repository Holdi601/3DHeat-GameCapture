---
title: Reglerna
nav_order: 2
lang: "sv"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Reglerna som verktyget bygger på {#the-rules-this-is-built-under}

Alla delar av 3DHeat GameCapture följer samma begränsningar. De är konstruktionsbeslut, inte
ansvarsfriskrivningar, och flera av dem kostar noggrannhet med avsikt.

## Ingenting injiceras, ingenting hakas i {#nothing-is-injected-nothing-is-hooked}

Ingen del av det här kopplar sig till en spelprocess, läser dess minne eller rör dess grafik-API.

- **Bildrutor** kommer från Windows Graphics Capture, det publika API som skärminspelare använder
  (via paketet `windows-capture`), eller från en videofil. Se
  [Inspelning, masker och bildrutekvalitet](reconstruction-capture.md).
- **Telemetri** kommer bara från gränssnitt som spelen publicerar för det:
  - Forzas Data Out-UDP-flöde, påslaget i spelets inställningar;
  - de namngivna delade minnessidorna som Kunos-spelen publicerar för appar (`Local\acpmf_physics`
    och liknande). De öppnas skrivskyddat med `mmap`; det är det dokumenterade sättet appar läser
    dem på, inte minnesläsning av spelprocessen;
  - UDP-telemetrin som EA SPORTS WRC, DiRT-spelen och Richard Burns Rally (via RSF/NGP-insticksprogrammet)
    skickar när den är påslagen i deras egna inställningsfiler;
  - BeamNGs protokollgränssnitt, via en liten Lua-"protokoll"-mod som spelets egen
    `lua/vehicle/protocols.lua` laddar och skickar;
  - Trackmanias Openplanet-insticksgränssnitt, via ett insticksprogram som bara läser det Openplanet
    exponerar och skriver filer;
  - iRacings egna `.ibt`-telemetrifiler.

## Varför det spelar roll {#why-it-matters}

Spelet känner djupet för varje pixel exakt, och en kapad djupbuffer skulle göra nivårekonstruktionen
nästan perfekt och trivial. Det skulle också innebära att man injicerar i processer som kan vara
skyddade av anti-cheat, vilket riskerar kontot för var och en som kör det. Så djupet *uppskattas* från
bilden i stället ([Djup](reconstruction-depth.md)), och mycket av rekonstruktionspipelinen finns för att
återfå så mycket som möjligt av den förlorade noggrannheten från källor som är fritt användbara:
telemetriposer där ett spel publicerar dem, en markplansskala där det inte gör det, och masker som
håller HUD:en och cockpiten utanför lösningen.

ReShades djupbuffer övervägdes och användes inte. ReShade stänger av djupåtkomst i
flerspelarsessioner med avsikt, så den skulle bara hjälpa enspelarstitlar (se
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Saker verktyget ändrar på din dator, och bara när du ber om det {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Åtgärd | När | Exakt vad |
|---|---|---|
| Installerar Python-paket | skanningsfönstrets första körning, efter en dialog och ett ja | `pip install` i tolken som kör verktyget - med `scan.bat` den privata `.venv` bredvid. Aldrig systemomfattande av sig själv. |
| Konverterar djupmodellen | knappen "Set up the depth model", efter en andra dialog för PyTorch och liknande | skriver `models/depth-small-518.onnx` |
| Redigerar EA SPORTS WRC:s `config.json` | `telemetry --game wrc --configure <file>` | slår på paketet `wrc` / `session_update` till 127.0.0.1; den gamla filen behålls som `config.json.bak` |
| Kopierar BeamNG-modden | `telemetry --game beamng --install` | `mods/beamng/heat3d` till `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (ersätter en äldre kopia) |
| Kopierar Trackmania-insticksprogrammet | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` till `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (ersätter en äldre kopia) |
| Registrerar globala snabbtangenter | medan skanningsfönstret är öppet (Windows) | Ctrl+Alt+F9 / F10 / F11, släpps när fönstret stängs |
| Uppdaterar verktyget | efter att du svarat ja på uppdateringsfrågan, eller kör `python -m heat3d_update` | se [Uppdateringar](updates.md) |

DiRT-spelens `hardware_settings_config.xml` och Richard Burns Rallys `RichardBurnsRally.ini` redigeras
**inte** av verktyget; du slår på deras UDP-utdata själv (se [Rallyspel](telemetry-rally.md)).

## Vad som förblir användarens ansvar {#what-stays-the-users-responsibility}

Vad en användare riktar verktygen mot lyder fortfarande under det spelets licens och
slutanvändarlicensavtal. Varvfiler, inspelningar, rekonstruktioner och exporterade banor tillhör den
som äger spelet och datan; förrådets `.gitignore` håller inspelningar, varvfiler, nät, modellvikter och
video utanför versionshanteringen, per mapp och per filtyp.
