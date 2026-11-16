---
title: Reglene
nav_order: 2
lang: "no"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Reglene dette er bygget etter {#the-rules-this-is-built-under}

Alle deler av 3DHeat GameCapture følger de samme begrensningene. De er designvalg, ikke
ansvarsfraskrivelser. Flere av dem koster nøyaktighet med vilje.

## Ingenting injiseres, ingenting kobles inn {#nothing-is-injected-nothing-is-hooked}

Ingen del av dette kobler seg til en spillprosess, leser minnet dens eller rører grafikk-API-et.

- **Bilder** kommer fra Windows Graphics Capture, det offentlige API-et skjermopptakere bruker
  (gjennom pakken `windows-capture`), eller fra en videofil. Se
  [Opptak, masker og bildekvalitet](reconstruction-capture.md).
- **Telemetri** kommer bare fra grensesnitt spillene publiserer for det:
  - Forzas Data Out UDP-strøm, slått på i spillets innstillinger;
  - de navngitte delte minnesidene Kunos-spillene publiserer for apper (`Local\acpmf_physics` og
    slektninger). De åpnes skrivebeskyttet med `mmap`. Det er den dokumenterte måten apper leser dem
    på, ikke minnelesing fra spillprosessen;
  - UDP-telemetrien som EA SPORTS WRC, DiRT-spillene og Richard Burns Rally (gjennom RSF/NGP-pluginen)
    sender når den er slått på i sine egne innstillingsfiler;
  - BeamNGs protokollgrensesnitt, gjennom en liten Lua-"protokoll"-mod som spillets egen
    `lua/vehicle/protocols.lua` laster og sender;
  - Trackmanias Openplanet-plugin-grensesnitt, gjennom en plugin som bare leser det Openplanet
    viser, og skriver filer;
  - iRacings egne `.ibt`-telemetrifiler.

## Hvorfor det betyr noe {#why-it-matters}

Spillet kjenner dybden til hver piksel nøyaktig. En koblet dybdebuffer ville gjort nivårekonstruksjon
nesten perfekt og enkel. Men da må man injisere i prosesser som kan være beskyttet av anti-juks, og
det risikerer kontoen til den som kjører det. Derfor **anslås** dybden fra bildet i stedet
([Dybde](reconstruction-depth.md)). Mye av rekonstruksjonsløypen finnes for å hente tilbake så mye som
mulig av den tapte nøyaktigheten fra kilder som er fritt brukbare: telemetri-posisjoner der et spill
publiserer dem, en skala fra et bakkeplan der det ikke gjør det, og masker som holder HUD-en og
førerhuset utenfor løsningen.

ReShades dybdebuffer ble vurdert og ikke brukt. ReShade slår av tilgang til dybde i
flerspillerøkter med vilje. Den ville bare hjulpet enspillertitler (se
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Ting verktøyet endrer på maskinen din, og bare når du ber om det {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Handling | Når | Hva nøyaktig |
|---|---|---|
| Installerer Python-pakker | skannevinduets første kjøring, etter en dialog og et ja | `pip install` inn i tolken som kjører verktøyet. Med `scan.bat` er det den private `.venv` ved siden av. Aldri systemomfattende av seg selv. |
| Konverterer dybdemodellen | knappen "Set up the depth model", etter en andre dialog for PyTorch og slektninger | skriver `models/depth-small-518.onnx` |
| Redigerer EA SPORTS WRCs `config.json` | `telemetry --game wrc --configure <file>` | slår på pakken `wrc` / `session_update` til 127.0.0.1; den gamle filen beholdes som `config.json.bak` |
| Kopierer BeamNG-modden | `telemetry --game beamng --install` | `mods/beamng/heat3d` til `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (erstatter en eldre kopi) |
| Kopierer Trackmania-pluginen | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` til `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (erstatter en eldre kopi) |
| Registrerer globale hurtigtaster | mens skannevinduet er åpent (Windows) | Ctrl+Alt+F9 / F10 / F11, frigjort når vinduet lukkes |
| Oppdaterer verktøyet | etter at du svarer ja på oppdateringsspørsmålet, eller kjører `python -m heat3d_update` | se [Oppdateringer](updates.md) |

DiRT-spillenes `hardware_settings_config.xml` og Richard Burns Rallys `RichardBurnsRally.ini` **redigeres
ikke** av verktøyet. Du slår på UDP-utdataene selv (se [Rallyspill](telemetry-rally.md)).

## Hva som leses, og hva som blir på maskinen din {#what-is-read-and-what-stays-on-your-machine}

Verktøyene leser det spillet viser på skjermen, og telemetrien og filene spillet selv publiserer for det, på din egen datamaskin. Ingenting fra et spill leveres med eller videredistribueres: ingen spillressurser, ingen spillkode, ingen DLL-er. Rundefiler, opptak, rekonstruksjoner og eksporterte baner blir på maskinen din; repositoriets `.gitignore` holder opptak, rundefiler, mesher, modellvekter og video utenfor versjonskontrollen etter mappe og filtype.

3DHeat GameCapture er ikke tilknyttet eller godkjent av noen spillutgiver. Spillnavn og tilhørende varemerker tilhører sine eiere. Rettighetshavere: opprett et issue på [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - vi svarer raskt og fjerner hva som helst på forespørsel.
