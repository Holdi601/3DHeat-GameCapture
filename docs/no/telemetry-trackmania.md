---
title: Trackmania (2020)
nav_order: 5
lang: "no"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kode: Openplanet-pluginen
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Pluginen er ennå ikke kjørt i spillet.** Visningsprogrammets leser av
CSV-filen er testet.

## Hvorfor en plugin som skriver filer {#why-a-plugin-that-writes-files}

Trackmania har ingen egen telemetriutgang. Openplanet, spillets pluginplattform, gir plugins tilgang til
tilstanden til bilen man ser på. Men Openplanet-plugins kan ikke sende UDP. Derfor skriver pluginen én
CSV-fil per kjøring til sin egen lagringsmappe, og visningsprogrammet leser filene slik de er. Det finnes
ingen opptakerprosess. `telemetry --game trackmania` installerer bare pluginen (med `--install`) og skriver
ut hvor filene kommer.

## Installere og laste {#installing-and-loading}

- `--install` kopierer `mods/trackmania/Heat3dRecorder` til
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, og erstatter en eldre kopi. Uten `--install`
  kopieres ingenting.
- I spillet: **Openplanet > Developer > Load plugin**, og velg `3DHeat recorder`.
- Pluginen avhenger av Openplanets **VehicleState**-plugin (`dependencies = ["VehicleState"]` i
  `info.toml`).
- Usignerte plugins lastes bare i **Openplanets utviklermodus**, som begrenser nettspill. Pluginen kan
  signeres på openplanet.dev. Den er ikke signert her.

Kjøringene skrives til `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Last disse CSV-
filene inn i visningsprogrammets Løpsanalyse-fane. `-o` og `--port` ignoreres for Trackmania.

## Hva pluginen tar opp {#what-the-plugin-records}

Den leser bare det Openplanet viser: tilstanden til bilen man ser på
(`VehicleState::ViewingPlayerState()`), og spillerens løpstid og antall respawn (`CSmScriptPlayer`). Den
sender ingenting noe sted og endrer ingenting i spillet. En rad skrives for hver ramme (`Update`), så
prøvefrekvensen er spillets bildefrekvens.

| Kolonne | Kilde |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunder |
| `x`, `y`, `z` | `Position` (verden, Y opp) |
| `speed` | lengden av `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 eller 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | hvert hjuls `SlipCoef` (et mål for sliring fra 0 til 1) |
| `loose` | 1 når ett av hjulenes underlagsmateriale er Grass, Ice, Sand, Dirt, Green eller RoadIce |
| `airborne` | 1 når bilen ikke har kontakt med underlaget |
| `respawns` | antall respawn siden kjøringen startet |

## Kjøringer {#runs}

- En kjøring **starter** på den første rammen der løpstiden ikke er negativ (nedtellingen tas ikke opp).
- Den **avsluttes** når sekvensen i banens brukergrensesnitt er målsekvensen (verdi 11). Filen skrives
  som fullført, med siste løpstid som `seconds`.
- Den **avbrytes**, og skrives med `_partial` i navnet og `"complete": false`, når løpsklokken går
  bakover med mer enn et halvt sekund (en omstart), eller når spilleren forlater banen.
- En kjøring med færre enn 20 rader skrives ikke.

## Filen {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Navngitt `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Banenavnet har formateringskoder fjernet, og doble
anførselstegn er erstattet med enkle. Verdier skrives med fire desimaler. Formatet beskrives i
[`heat3d-lap`-filen](lap-format.md#the-csv-form).

`meta` i headeren har `"slip": "index"`. `slipIndex.*`-kanalene er Trackmanias egen sliremåling fra 0 til 1,
ikke fysisk sliring. Og `"discipline": "arcade"`.
