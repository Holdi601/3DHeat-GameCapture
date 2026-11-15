---
title: Trackmania (2020)
nav_order: 5
lang: "nl"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Code: de Openplanet-plugin [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder) (`info.toml`, `main.as`). **De plugin is nog niet in het spel gedraaid**; de lezer van de viewer voor zijn CSV wordt getest.

## Waarom een plugin die bestanden schrijft {#why-a-plugin-that-writes-files}

Trackmania heeft geen eigen telemetrie-uitvoer. Openplanet, het pluginplatform van het spel, geeft de voertuigtoestand van de bekeken auto aan plugins, maar Openplanet-plugins kunnen geen UDP versturen. Daarom schrijft de plugin per run één CSV-bestand naar de eigen opslagmap, en de viewer leest die bestanden zoals ze zijn. Er is geen recorderproces: `telemetry --game trackmania` installeert alleen de plugin (met `--install`) en drukt af waar de bestanden verschijnen.

## Installeren en laden {#installing-and-loading}

- `--install` kopieert `mods/trackmania/Heat3dRecorder` naar `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, een oudere kopie wordt vervangen. Zonder `--install` wordt niets gekopieerd.
- In het spel: kies **Openplanet > Developer > Load plugin** en selecteer `3DHeat recorder`.
- De plugin heeft de **VehicleState**-plugin van Openplanet nodig (`dependencies = ["VehicleState"]` in `info.toml`).
- Niet-ondertekende plugins laden alleen in de **ontwikkelaarsmodus** van Openplanet, die online spelen beperkt. De plugin kan op openplanet.dev worden ondertekend; hier is hij niet ondertekend.

Runs worden geschreven naar `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Laad die CSV-bestanden in het tabblad Race-analyse van de viewer. `-o` en `--port` worden voor Trackmania genegeerd.

## Wat de plugin opneemt {#what-the-plugin-records}

Hij leest alleen wat Openplanet blootstelt - de voertuigtoestand van de bekeken auto (`VehicleState::ViewingPlayerState()`) en de racetijd en het aantal respawns van de speler (`CSmScriptPlayer`) - verstuurt niets en verandert niets in het spel. Er wordt op elk frame (`Update`) een rij geschreven, dus de samplefrequentie is de framesnelheid van het spel.

| Kolom | Bron |
|---|---|
| `time` | `CurrentRaceTime` / 1000, seconden |
| `x`, `y`, `z` | `Position` (wereld, Y omhoog) |
| `speed` | lengte van `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 of 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | de `SlipCoef` van elk wiel (een schuifmaat van 0..1) |
| `loose` | 1 wanneer het grondmateriaal van een wiel Grass, Ice, Sand, Dirt, Green of RoadIce is |
| `airborne` | 1 wanneer de auto geen grondcontact heeft |
| `respawns` | respawns sinds het begin van de run |

## Runs {#runs}

- Een run **begint** op het eerste frame waarop de racetijd niet negatief is (het aftellen wordt niet opgenomen).
- Hij **eindigt** wanneer de UI-reeks van de playground de finishreeks is (waarde 11): het bestand wordt als compleet geschreven, met de laatste racetijd als `seconds`.
- Hij wordt **opgegeven** - geschreven met `_partial` in de naam en `"complete": false` - wanneer de race-klok meer dan een halve seconde teruggaat (een herstart), of wanneer de speler de playground verlaat.
- Een run met minder dan 20 rijen wordt niet geschreven.

## Het bestand {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Genoemd `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. De mapnaam heeft opmaakcodes verwijderd en dubbele aanhalingstekens vervangen door enkele. Waarden worden met vier decimalen geschreven. Het formaat staat beschreven in [Het heat3d-lapbestand](lap-format.md#the-csv-form).

De `meta` van de kop bevat `"slip": "index"` - de `slipIndex.*`-kanalen zijn de eigen schuifmaat van Trackmania op 0..1, geen fysieke slip - en `"discipline": "arcade"`.
