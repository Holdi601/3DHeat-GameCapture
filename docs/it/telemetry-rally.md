---
title: Giochi rally
nav_order: 3
lang: "it"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # oppure dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Codice: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Test: `tests/test_rally.py`, su pacchetti costruiti dai layout documentati. **Non ancora eseguito contro i
giochi veri.**

Tutti inviano UDP che il gioco attiva dai propri file di impostazioni. Il registratore ascolta su tutte le
interfacce (`0.0.0.0`) sulla porta predefinita del gioco, a meno che `--port` ne indichi un'altra: **20777** per
`wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** per `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Attivarlo {#switching-it-on}

Il gioco legge `Documents\My Games\WRC\telemetry\config.json`. Il pacchetto `session_update` della struttura
predefinita `wrc` deve essere attivato verso questo PC:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<percorso di config.json>"
```

`--configure` (funzione `configure_wrc`):

- legge il JSON, trova `udp.packets` e la voce con `"structure": "wrc"` e `"packet": "session_update"`;
- se è già attivata verso `127.0.0.1` o `localhost` sulla porta in uso, stampa `already on` e non cambia nulla;
- altrimenti imposta `"ip": "127.0.0.1"`, `"port": <porta>`, `"bEnabled": true`, e mantiene il `frequencyHz`
  della voce (o `-1` se non ce n'è); se non esiste una voce del genere, ne aggiunge una;
- scrive il testo originale in `config.json.bak` accanto a esso, poi scrive il nuovo file (indentato di 4 spazi).

Riavvia il gioco dopo aver cambiato il file se non lo riprende (non verificato).

### Cosa invia {#what-it-sends}

La struttura predefinita `wrc` è di 237 byte, little-endian, senza intestazione: posizione nel mondo, velocità e
accelerazione (X a sinistra, Y verso l'alto, Z in avanti), i vettori unitari sinistra / avanti / alto dell'auto,
per ruota (posteriore sinistra, posteriore destra, anteriore sinistra, anteriore destra) l'altezza del mozzo e la
sua velocità verticale e la velocità in avanti del punto di contatto, le temperature dei freni, i pedali dopo gli
aiuti, lo sterzo (-1 sinistra, +1 destra), il freno a mano, i giri, la marcia, e l'orologio di tappa, la distanza e
la lunghezza. Un pacchetto più corto di 237 byte viene ignorato e segnalato una volta.

| Canale | Da |
|---|---|
| `x`, `y`, `z` | posizione nel mondo |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | velocità nel mondo proiettata su avanti, su meno sinistra (quindi positiva a destra), su alto |
| `longAcc`, `latAcc`, `vertAcc` | accelerazione nel mondo proiettata allo stesso modo |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | come inviati |
| `gear` | `gear_index`; -1 quando è uguale all'indice della retromarcia, 0 quando è uguale a quello del folle |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | posizione del mozzo |
| `wheelSurfaceSpeed.*` | velocità in avanti del punto di contatto |
| `brakeTemp.*` | temperatura del freno |

Controllo: se `speed` è sopra 10 e la lunghezza della velocità nel mondo differisce da essa per più del 20%, il
registratore stampa una volta che il layout potrebbe non essere la struttura `wrc` predefinita.

Una tappa è **finita** quando la lunghezza della tappa è positiva e la distanza ha raggiunto la lunghezza meno
0,5 m. L'orologio usato per la divisione e per `time` è `stage_time`.

Fonti: la Guida UDP Telemetry v1.3 di EA; l'elenco dei canali che il gioco scrive in `readme/channels.json`;
gli offset come decodificati da nobonobo/obs-codemasters-telemetry e SpaceMonkey. La porta predefinita di
fabbrica non è documentata; il registratore usa la 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Attivarlo {#switching-it-on-1}

Modifica `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally e DiRT 4
usano anch'essi un `hardware_settings_config.xml`; la loro cartella esatta per questi due non è verificata qui)
in modo che l'elemento `udp` riporti:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` è ciò che mette posizioni, ruote e lunghezza della tappa nel pacchetto. Il registratore non
modifica questo file.

### Cosa invia {#what-it-sends-1}

66 float little-endian (DiRT Rally: 64); i pacchetti più corti di 64 float vengono ignorati, e un pacchetto di 64
float viene riempito con zeri. Gli indici usati:

| Indice | Campo | Canale |
|---|---|---|
| 1 | tempo del giro (tappa) | l'orologio di divisione e `time` |
| 2 | distanza nel giro | `stageDistance` |
| 4-6 | posizione nel mondo | `x`, `y`, `z` |
| 7 | velocità | `speed` |
| 8-10 | velocità nel mondo | `longVel` (in avanti), `latVel` (sul vettore laterale) |
| 11-13 | vettore laterale | |
| 14-16 | vettore in avanti | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | posizione delle sospensioni RL RR FL FR | `suspensionM.*` |
| 25-28 | velocità del punto di contatto delle ruote RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | acceleratore, sterzo, freno, frizione, marcia | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 o più significa retromarcia, scritta come -1) |
| 34, 35 | g laterali, longitudinali | `latAcc`, `longAcc` (per 9,80665) |
| 37 | giri / 10 | `rpm` (per 10) |
| 51-54 | temperature dei freni | `brakeTemp.*` |
| 59, 60, 61, 62 | giri completati, giri totali, lunghezza del tracciato, tempo dell'ultimo giro | divisione |

**Non c'è nessun canale del freno a mano**. Il verso del vettore laterale è documentato in entrambi i sensi, quindi
il segno di `latVel` non è affidabile (il visualizzatore legge la grandezza dell'angolo di deriva).

Una tappa è **finita** quando il conteggio dei giri completati sale sopra il suo valore all'inizio della tappa (un
giro di rallycross ogni volta che succede), oppure, per un evento a giro singolo, quando la distanza nel giro
raggiunge il 99,9% della lunghezza del tracciato. Il tempo della tappa è il tempo dell'ultimo giro del gioco quando
è positivo. Controllo: velocità contro velocità dell'auto come per EA WRC, con il messaggio "is extradata set to 3?".

Fonti: il documento UDP di DiRT 4 di Codemasters; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Attivarlo {#switching-it-on-2}

In `RichardBurnsRally.ini`, sezione `[NGP]`: `udpTelemetry=1` e l'endpoint (127.0.0.1, porta 6776 salvo che tu
passi un altro `--port`). Il registratore non modifica questo file.

### Cosa invia {#what-it-sends-2}

664 byte (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): orologio di tappa e distanza dalla fine, pedali,
sterzo, marcia, posizione nel mondo, assetto, le velocità proprie dell'auto (avanzamento in avanti, oscillazione
laterale, sussulto verticale), accelerazioni, giri, e quattro blocchi di ruota da 128 byte (AS, AD, PS, PD) con
deflessione e forza della molla. Nessuna velocità delle ruote.

| Canale | Da |
|---|---|
| `x`, `y`, `z` | posizione, assi come inviati, poi riordinati (sotto) |
| `longVel`, `latVel`, `vertVel` | avanzamento, oscillazione, sussulto |
| `longAcc`, `latAcc` | accelerazione x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | come inviati |
| `gear` | `gear - 1` (0 retromarcia, 1 folle, 2 prima) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | deflessione della molla |
| `wheelLoad.*` | forza della molla |
| `speed` | **calcolata dalle posizioni** su ±2 campioni, non presa dal pacchetto |

Gli assi di posizione, le unità dell'assetto e l'unità di velocità di RBR non sono documentati, quindi quando una
tappa viene scritta: l'asse lungo cui la tappa varia meno viene preso come verticale e scambiato in `y`
(`orient_up`, servono almeno 10 campioni), e la velocità viene ricalcolata dalle posizioni (`speed_from_positions`).
L'assetto viene decodificato ma non scritto, quindi i file RBR non hanno `yaw`.

Una tappa è **finita** quando l'orologio di gara è in marcia e la distanza dalla fine ha raggiunto zero. L'orologio
è `race_time`.

Fonti: `rbr.telemetry.data.TelemetryData.h` di NGP tramite mika-n/RBRUDPTelemetryLogger e groybe/rbr-udp-telem.

## Tappe {#stages}

Tutti e cinque usano `StageSplitter` sull'orologio di tappa del gioco: una tappa si apre quando parte l'orologio, si
chiude completa quando il gioco dice che l'auto ha finito, e un orologio che torna indietro (un riavvio, o la tappa
successiva) abbandona la tappa aperta - conservata come file `_partial` se ha più di 10 campioni e almeno 300 m.
Le tappe finite più corte di 300 m non vengono scritte. Dettagli: [Come vengono divisi i giri e le tappe](lap-splitting.md).

## Il file del giro {#the-lap-file}

`game` è `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` o `richard-burns-rally`. `meta` è
`{"discipline": "rally", "slip": null}`, più `"surface": "<valore>"` quando è stato dato `--surface`. `slip` è null
perché nessuno di questi giochi invia lo slittamento delle gomme. Al suo posto, la velocità del punto di contatto di
ogni ruota (EA WRC, DiRT) è nel file, e il visualizzatore ne deriva lo slittamento e l'angolo di deriva insieme agli
assi dell'auto; vedi [Slittamento, deriva e canali derivati](slip-and-drift.md). I canali `suspension.*` (0..1 della
corsa usata) vengono aggiunti da `suspensionM.*`.

Quando non viene dato alcun `--surface`, il file non porta alcuna superficie, di proposito: un valore predefinito
scritto qui sovrascriverebbe la deduzione del visualizzatore. Il visualizzatore prende allora la superficie dal nome
della tappa o dell'evento (rally su asfalto, invernali, il Monte come misto), altrimenti da come è stata guidata l'auto
sopra (curve decise con piccoli angoli di deriva indicano asfalto), e sterrato quando nulla lo indica - che è ciò che
più spesso è una tappa rally. Indica `--surface` quando ne sai di più.
