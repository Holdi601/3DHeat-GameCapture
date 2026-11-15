---
title: Trackmania
nav_order: 5
lang: "da"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kode: Openplanet-plugin'et
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Plugin'et er endnu ikke blevet kørt i spillet**; viewerens læser af dets CSV er testet.

## Hvorfor et plugin, der skriver filer {#why-a-plugin-that-writes-files}

Trackmania har ingen telemetriudgang af sin egen. Openplanet, spillets pluginplatform, eksponerer den
viste bils køretøjstilstand til plugins, men Openplanet-plugins kan ikke sende UDP. Så plugin'et skriver
én CSV-fil pr. kørsel til sin egen lagermappe, og vieweren læser filerne, som de er. Der er ingen
optagerproces: `telemetry --game trackmania` installerer kun plugin'et (med `--install`) og skriver,
hvor filerne dukker op.

## Installation og indlæsning {#installing-and-loading}

- `--install` kopierer `mods/trackmania/Heat3dRecorder` til
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, og erstatter en ældre kopi. Uden `--install`
  kopieres intet.
- I spillet: **Openplanet > Developer > Load plugin**, og vælg `3DHeat recorder`.
- Plugin'et afhænger af Openplanets **VehicleState**-plugin (`dependencies = ["VehicleState"]`
  i `info.toml`).
- Usignerede plugins indlæses kun i **Openplanets udviklertilstand**, som begrænser onlinespil.
  Plugin'et kan signeres på openplanet.dev; det er ikke signeret her.

Kørsler skrives til `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Indlæs de CSV-filer på
viewerens fane Løbsanalyse. `-o` og `--port` ignoreres for Trackmania.

## Hvad plugin'et optager {#what-the-plugin-records}

Det læser kun det, Openplanet eksponerer - den viste bils køretøjstilstand
(`VehicleState::ViewingPlayerState()`) og spillerens racetid og respawn-antal (`CSmScriptPlayer`) - sender
intet nogen steder og ændrer intet i spillet. En række skrives på hvert billede (`Update`), så prøvehastigheden
er spillets billedhastighed.

| Kolonne | Kilde |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunder |
| `x`, `y`, `z` | `Position` (verden, Y op) |
| `speed` | længden af `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 eller 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | hvert hjuls `SlipCoef` (et 0..1 mål for glidning) |
| `loose` | 1 når ethvert hjuls jordmateriale er Grass, Ice, Sand, Dirt, Green eller RoadIce |
| `airborne` | 1 når bilen ingen jordkontakt har |
| `respawns` | respawns siden kørslen begyndte |

## Kørsler {#runs}

- En kørsel **starter** på det første billede, hvor racetiden ikke er negativ (nedtællingen optages ikke).
- Den **afsluttes**, når playgroundens UI-sekvens er målsekvensen (værdi 11): filen skrives som komplet,
  med den sidste racetid som sin `seconds`.
- Den **opgives** - skrevet med `_partial` i navnet og `"complete": false` - når løbsuret går tilbage med
  mere end et halvt sekund (en genstart), eller når spilleren forlader playgroundet.
- En kørsel med færre end 20 rækker skrives ikke.

## Filen {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Navngivet `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Banens navn har formateringskoder fjernet, og
dobbelte anførselstegn erstattet med enkelte. Værdier skrives med fire decimaler. Formatet er beskrevet i
[Heat3d-lap-filen](lap-format.md#the-csv-form).

Headerens `meta` har `"slip": "index"` - `slipIndex.*`-kanalerne er Trackmanias egen 0..1-glidningsmåling,
ikke et fysisk slip - og `"discipline": "arcade"`.
