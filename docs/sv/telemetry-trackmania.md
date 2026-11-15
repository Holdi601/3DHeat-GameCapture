---
title: Trackmania (2020)
nav_order: 5
lang: "sv"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kod: Openplanet-insticksprogrammet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Insticksprogrammet har ännu inte körts i spelet**; visarens läsare av dess
CSV testas.

## Varför ett insticksprogram som skriver filer {#why-a-plugin-that-writes-files}

Trackmania har ingen egen telemetriutdata. Openplanet, spelets insticksplattform, exponerar den
visade bilens fordonstillstånd för insticksprogram, men Openplanet-insticksprogram kan inte skicka UDP.
Så insticksprogrammet skriver en CSV-fil per körning i sin egen lagringsmapp, och visaren läser filerna
som de är. Det finns ingen inspelarprocess: `telemetry --game trackmania` installerar bara
insticksprogrammet (med `--install`) och skriver ut var filerna kommer att dyka upp.

## Installera och ladda {#installing-and-loading}

- `--install` kopierar `mods/trackmania/Heat3dRecorder` till
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, och ersätter en äldre kopia. Utan `--install`
  kopieras ingenting.
- I spelet: **Openplanet > Developer > Load plugin**, och välj `3DHeat recorder`.
- Insticksprogrammet beror på Openplanets **VehicleState**-insticksprogram (`dependencies = ["VehicleState"]`
  i `info.toml`).
- Osignerade insticksprogram laddas bara i **Openplanets utvecklarläge**, vilket begränsar onlinespel.
  Insticksprogrammet kan signeras på openplanet.dev; det är inte signerat här.

Körningarna skrivs till `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Läs in de CSV-filerna
på visarens flik Racinganalys. `-o` och `--port` ignoreras för Trackmania.

## Vad insticksprogrammet spelar in {#what-the-plugin-records}

Det läser bara det Openplanet exponerar - den visade bilens fordonstillstånd
(`VehicleState::ViewingPlayerState()`) och spelarens racetid och antal respawns (`CSmScriptPlayer`) -
skickar ingenting någonstans och ändrar ingenting i spelet. En rad skrivs för varje bildruta (`Update`),
så samplingsfrekvensen är spelets bildfrekvens.

| Kolumn | Källa |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunder |
| `x`, `y`, `z` | `Position` (världen, Y uppåt) |
| `speed` | längden av `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 eller 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | varje hjuls `SlipCoef` (ett 0..1-mått på glidning) |
| `loose` | 1 när något hjul har markmaterialet Grass, Ice, Sand, Dirt, Green eller RoadIce |
| `airborne` | 1 när bilen saknar markkontakt |
| `respawns` | respawns sedan körningen började |

## Körningar {#runs}

- En körning **startar** på den första bildrutan där racetiden inte är negativ (nedräkningen spelas inte in).
- Den **slutar** när spelplatsens UI-sekvens är slutsekvensen (värde 11): filen skrivs som komplett, med
  den sista racetiden som `seconds`.
- Den **avbryts** - skrivs med `_partial` i namnet och `"complete": false` - när racetiden går bakåt mer än
  en halv sekund (en omstart), eller när spelaren lämnar spelplatsen.
- En körning med färre än 20 rader skrivs inte.

## Filen {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Namnet är `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Kartnamnet har formateringskoder borttagna och
dubbla citattecken ersatta med enkla. Värden skrivs med fyra decimaler. Formatet beskrivs i
[Heat3D-varvfilen](lap-format.md#the-csv-form).

Headerns `meta` innehåller `"slip": "index"` - kanalerna `slipIndex.*` är Trackmanias egna 0..1-mått på
glidning, inte fysisk slip - och `"discipline": "arcade"`.
