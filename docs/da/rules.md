---
title: Reglerne, dette er bygget under
nav_order: 2
lang: "da"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Reglerne, dette er bygget under {#the-rules-this-is-built-under}

Alle dele af 3DHeat GameCapture følger de samme begrænsninger. De er designbeslutninger, ikke
ansvarsfraskrivelser, og flere af dem koster nøjagtighed med vilje.

## Intet injiceres, intet hookes {#nothing-is-injected-nothing-is-hooked}

Ingen del af dette tilknytter sig til en spilproces, læser dens hukommelse eller rører dens grafik-API.

- **Billeder** kommer fra Windows Graphics Capture, den offentlige API, skærmoptagere bruger
  (gennem pakken `windows-capture`), eller fra en videofil. Se
  [Optagelse, masker og billedkvalitet](reconstruction-capture.md).
- **Telemetri** kommer kun fra grænseflader, spillene selv udgiver til det:
  - Forzas Data Out UDP-feed, slået til i spillets indstillinger;
  - de navngivne delte hukommelsessider, Kunos-spil udgiver til apps (`Local\acpmf_physics` og
    venner). De åbnes skrivebeskyttet med `mmap`; det er den dokumenterede måde, apps læser dem på,
    ikke hukommelseslæsning af spilprocessen;
  - den UDP-telemetri, EA SPORTS WRC, DiRT-spillene og Richard Burns Rally (gennem RSF/NGP-plugin'et)
    sender, når den er slået til i deres egne indstillingsfiler;
  - BeamNGs protokolgrænseflade, gennem et lille Lua-"protokol"-mod, som spillets egen
    `lua/vehicle/protocols.lua` indlæser og sender;
  - Trackmanias Openplanet-plugin-grænseflade, gennem et plugin, der kun læser det, Openplanet
    eksponerer, og skriver filer;
  - iRacings egne `.ibt`-telemetrifiler.

## Hvorfor det betyder noget {#why-it-matters}

Spillet kender dybden af hver pixel nøjagtigt, og en hooket dybdebuffer ville gøre banerekonstruktion
næsten perfekt og triviel. Den ville også betyde at injicere i processer, der kan være beskyttet af
anti-cheat, hvilket risikerer kontoen for enhver, der kører det. Så dybde er *estimeret* ud fra billedet i
stedet ([Dybde](reconstruction-depth.md)), og en stor del af rekonstruktionspipelinen findes for at
genvinde så meget af den tabte nøjagtighed som muligt fra kilder, der er frie at bruge: telemetri-positurer,
hvor et spil udgiver dem, en skala fra jordplanet, hvor det ikke gør, og masker, der holder HUD'et og
cockpittet ude af løsningen.

ReShades dybdebuffer blev overvejet og ikke brugt. ReShade slår dybdeadgang fra i multiplayer-sessioner
som et designvalg, så den ville kun hjælpe single-player-titler (se
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Ting værktøjet ændrer på din maskine, og kun når du beder om det {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Handling | Hvornår | Hvad præcist |
|---|---|---|
| Installerer Python-pakker | scanningsvinduets første kørsel, efter en dialog og et ja | `pip install` ind i den fortolker, der kører værktøjet - med `scan.bat`, det private `.venv` ved siden af den. Aldrig systemomfattende af sig selv. |
| Konverterer dybdemodellen | knappen "Set up the depth model", efter en anden dialog for PyTorch og venner | skriver `models/depth-small-518.onnx` |
| Redigerer EA SPORTS WRC's `config.json` | `telemetry --game wrc --configure <file>` | slår pakken `wrc` / `session_update` til på 127.0.0.1; den gamle fil gemmes som `config.json.bak` |
| Kopierer BeamNG-modet | `telemetry --game beamng --install` | `mods/beamng/heat3d` til `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (erstatter en ældre kopi) |
| Kopierer Trackmania-plugin'et | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` til `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (erstatter en ældre kopi) |
| Registrerer globale genveje | mens scanningsvinduet er åbent (Windows) | Ctrl+Alt+F9 / F10 / F11, frigives når vinduet lukkes |
| Opdaterer værktøjet | efter du svarer ja til opdateringsspørgsmålet, eller kører `python -m heat3d_update` | se [Opdateringer](updates.md) |

DiRT-spillenes `hardware_settings_config.xml` og Richard Burns Rallys `RichardBurnsRally.ini` bliver
**ikke** redigeret af værktøjet; du slår selv deres UDP-output til (se [Rally-spil](telemetry-rally.md)).

## Hvad der forbliver brugerens ansvar {#what-stays-the-users-responsibility}

Det, en bruger peger værktøjerne mod, er fortsat underlagt det spils licens og EULA. Lap-filer,
optagelser, rekonstruktioner og eksporterede baner tilhører den, der ejer spillet og dataene; repositoriets
`.gitignore` holder optagelser, lap-filer, mesh'e, modelvægte og video ude af versionsstyring, efter mappe
og efter filtype.
