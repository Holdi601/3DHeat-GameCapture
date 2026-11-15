---
title: De regels
nav_order: 2
lang: "nl"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# De regels waaronder dit is gebouwd {#the-rules-this-is-built-under}

Elk onderdeel van 3DHeat GameCapture volgt dezelfde beperkingen. Het zijn ontwerpkeuzes, geen disclaimers, en een aantal ervan kost bewust nauwkeurigheid.

## Niets wordt geïnjecteerd, niets wordt gehaakt {#nothing-is-injected-nothing-is-hooked}

Geen enkel onderdeel koppelt zich aan een spelproces, leest het geheugen ervan, of raakt de grafische API aan.

- **Frames** komen van Windows Graphics Capture, de openbare API die schermrecorders gebruiken (via het pakket `windows-capture`), of uit een videobestand. Zie [Opname, maskers en beeldkwaliteit](reconstruction-capture.md).
- **Telemetrie** komt alleen uit interfaces die de games daarvoor publiceren:
  - de Data Out UDP-feed van Forza, aan te zetten in de instellingen van het spel;
  - de benoemde gedeelde-geheugenpagina's die Kunos-games voor apps publiceren (`Local\acpmf_physics` en consorten). Ze worden alleen-lezen geopend met `mmap`; dit is de gedocumenteerde manier waarop apps ze lezen, niet het geheugen van het spelproces uitlezen;
  - de UDP-telemetrie die EA SPORTS WRC, de DiRT-games en Richard Burns Rally (via de RSF/NGP-plugin) verstuurt wanneer die in hun eigen instellingenbestanden aan staat;
  - de protocolinterface van BeamNG, via een kleine Lua-"protocol"-mod die het eigen `lua/vehicle/protocols.lua` van het spel laadt en verstuurt;
  - de Openplanet-plugininterface van Trackmania, via een plugin die alleen leest wat Openplanet blootstelt en bestanden schrijft;
  - de eigen `.ibt`-telemetriebestanden van iRacing.

## Waarom het ertoe doet {#why-it-matters}

Het spel kent de diepte van elke pixel precies, en een gehaakte dieptebuffer zou de level-reconstructie bijna perfect en triviaal maken. Het zou ook betekenen dat je in processen injecteert die door anti-cheat beschermd kunnen zijn, wat het account van wie het draait in gevaar brengt. Daarom wordt diepte in plaats daarvan *geschat* uit het beeld ([Diepte](reconstruction-depth.md)), en bestaat een groot deel van de reconstructiepijplijn om zoveel mogelijk van die verloren nauwkeurigheid terug te halen uit bronnen die vrij te gebruiken zijn: telemetriposities waar een spel die publiceert, een schaal op basis van het grondvlak waar dat niet gebeurt, en maskers die de HUD en de cockpit uit de berekening houden.

De dieptebuffer van ReShade is overwogen en niet gebruikt. ReShade schakelt dieptetoegang in multiplayersessies bewust uit, dus het zou alleen singleplayer-titels helpen (zie [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Dingen die de tool op je computer verandert, en alleen op verzoek {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Actie | Wanneer | Wat precies |
|---|---|---|
| Installeert Python-pakketten | de eerste keer dat het scanvenster draait, na een dialoog en een ja | `pip install` in de interpreter die de tool draait - met `scan.bat` de eigen `.venv` ernaast. Nooit systeembreed uit zichzelf. |
| Converteert het dieptemodel | de knop "Set up the depth model", na een tweede dialoog voor PyTorch en consorten | schrijft `models/depth-small-518.onnx` |
| Past het `config.json` van EA SPORTS WRC aan | `telemetry --game wrc --configure <file>` | zet het pakket `wrc` / `session_update` aan naar 127.0.0.1; het oude bestand blijft bewaard als `config.json.bak` |
| Kopieert de BeamNG-mod | `telemetry --game beamng --install` | `mods/beamng/heat3d` naar `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (een oudere kopie wordt vervangen) |
| Kopieert de Trackmania-plugin | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` naar `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (een oudere kopie wordt vervangen) |
| Registreert globale sneltoetsen | zolang het scanvenster open is (Windows) | Ctrl+Alt+F9 / F10 / F11, vrijgegeven wanneer het venster sluit |
| Werkt de tool bij | nadat je ja hebt geantwoord op de updatevraag, of met `python -m heat3d_update` | zie [Updates](updates.md) |

Het `hardware_settings_config.xml` van de DiRT-games en het `RichardBurnsRally.ini` van Richard Burns Rally worden door de tool **niet** bewerkt; je zet hun UDP-uitvoer zelf aan (zie [Rallygames](telemetry-rally.md)).

## Wat de verantwoordelijkheid van de gebruiker blijft {#what-stays-the-users-responsibility}

Waar een gebruiker de tools op richt, blijft onderworpen aan de licentie en EULA van dat spel. Rondebestanden, opnames, reconstructies en geëxporteerde banen horen toe aan wie het spel en de data bezit; de `.gitignore` van de repository houdt opnames, rondebestanden, meshes, modelgewichten en video per map en per bestandstype buiten versiebeheer.
