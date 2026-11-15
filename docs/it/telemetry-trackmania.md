---
title: Trackmania (2020)
nav_order: 5
lang: "it"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Codice: il plugin per Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Il plugin non è ancora stato eseguito nel gioco**; il lettore del suo CSV nel
visualizzatore è testato.

## Perché un plugin che scrive file {#why-a-plugin-that-writes-files}

Trackmania non ha una propria uscita di telemetria. Openplanet, la piattaforma di plugin del gioco,
espone ai plugin lo stato del veicolo dell'auto osservata, ma i plugin di Openplanet non possono inviare
UDP. Quindi il plugin scrive un file CSV per ogni corsa nella propria cartella di archiviazione, e il
visualizzatore legge quei file così come sono. Non c'è nessun processo registratore:
`telemetry --game trackmania` si limita a installare il plugin (con `--install`) e a stampare dove
compariranno i file.

## Installazione e caricamento {#installing-and-loading}

- `--install` copia `mods/trackmania/Heat3dRecorder` in
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, sostituendo una copia precedente. Senza
  `--install` non viene copiato nulla.
- Nel gioco: **Openplanet > Developer > Load plugin**, e scegli `3DHeat recorder`.
- Il plugin dipende dal plugin **VehicleState** di Openplanet (`dependencies = ["VehicleState"]`
  in `info.toml`).
- I plugin non firmati si caricano solo nella **modalità sviluppatore di Openplanet**, che limita il
  gioco online. Il plugin si può firmare su openplanet.dev; qui non è firmato.

Le corse vengono scritte in `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Carica quei
file CSV nella scheda Analisi di gara del visualizzatore. `-o` e `--port` vengono ignorati per Trackmania.

## Cosa registra il plugin {#what-the-plugin-records}

Legge solo ciò che Openplanet espone - lo stato del veicolo dell'auto osservata
(`VehicleState::ViewingPlayerState()`) e il tempo di gara del giocatore e i respawn
(`CSmScriptPlayer`) - non invia nulla da nessuna parte e non cambia nulla nel gioco. Una riga viene
scritta a ogni fotogramma (`Update`), quindi la frequenza di campionamento è quella dei fotogrammi del
gioco.

| Colonna | Fonte |
|---|---|
| `time` | `CurrentRaceTime` / 1000, secondi |
| `x`, `y`, `z` | `Position` (mondo, Y verso l'alto) |
| `speed` | lunghezza di `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 o 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` di ogni ruota (una misura di slittamento da 0 a 1) |
| `loose` | 1 quando il materiale di contatto di una ruota è Grass, Ice, Sand, Dirt, Green o RoadIce |
| `airborne` | 1 quando l'auto non ha contatto con il suolo |
| `respawns` | respawn dall'inizio della corsa |

## Corse {#runs}

- Una corsa **inizia** sul primo fotogramma in cui il tempo di gara non è negativo (il conto alla
  rovescia non viene registrato).
- **Termina** quando la sequenza UI del playground è la sequenza di arrivo (valore 11): il file viene
  scritto come completo, con l'ultimo tempo di gara come `seconds`.
- Viene **abbandonata** - scritta con `_partial` nel nome e `"complete": false` - quando l'orologio
  di gara torna indietro di più di mezzo secondo (un riavvio), oppure quando il giocatore lascia il
  playground.
- Una corsa con meno di 20 righe non viene scritta.

## Il file {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Chiamato `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Il nome della mappa ha i codici di formattazione
rimossi e le doppie virgolette sostituite da virgolette singole. I valori sono scritti con quattro
decimali. Il formato è descritto in [Il file heat3d-lap](lap-format.md#the-csv-form).

Il `meta` dell'intestazione contiene `"slip": "index"` - i canali `slipIndex.*` sono la misura di
slittamento da 0 a 1 propria di Trackmania, non uno slittamento fisico - e `"discipline": "arcade"`.
