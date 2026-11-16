---
title: Forza
nav_order: 1
lang: "it"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon e Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # gioco -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # e FH Companion continua a funzionare
```

Codice: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(rilevamento del layout),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(ogni canale, file dei giri, inoltro).

## Attivarlo nel gioco {#switching-it-on-in-the-game}

**Impostazioni -> HUD e gioco -> Data Out**: `ON`, IP `127.0.0.1`, porta `5300` (o quella che passi con
`--port`). Forza Motorsport offre anche un formato di pacchetto: deve essere **Dash**, non Sled. Sled non porta
alcuna posizione, e il registratore lo rifiuta.

Il registratore ascolta su `127.0.0.1`, quindi il gioco deve girare sullo stesso PC.

## Cosa invia il gioco, e come si trova il layout {#what-the-game-sends-and-how-the-layout-is-found}

Data Out è un pacchetto UDP per ogni tick della simulazione (circa 60 al secondo), una struct C piatta in
little-endian in queste dimensioni:

| Lunghezza | Variante |
|---|---|
| 232 byte | Motorsport "Sled": senza posizione. Rifiutato con un messaggio che ti dice di passare a Dash. |
| 311 byte | Motorsport "Dash": blocco Sled più il blocco dash di 79 byte |
| 324 byte | Horizon "Dash": lo stesso con imbottitura tra i due blocchi |
| 331 byte | Forza Motorsport (2023): Dash più 20 byte di usura delle gomme e l'id del tracciato |

Il blocco Sled (offset 0-231) è stabile. Dove inizi il blocco dash nella variante Horizon è descritto in modo
incoerente nelle fonti pubblicate, e sbagliare non fa fallire nulla - produce float plausibili dai campi
sbagliati. Quindi l'inizio viene **scoperto**:

1. Gli inizi candidati vengono provati in ordine: `length - 79` (il blocco dash arriva all'ultimo byte in ogni
   variante documentata), 232, 244, e da 232 a 260 a passi di 4.
2. Ogni candidato viene valutato su pacchetti di un'auto in movimento (una componente di velocità sopra 1 m/s):
   il vettore velocità del blocco Sled e lo `Speed` scalare del blocco dash sono la stessa grandezza in due posti,
   quindi `| |velocità| - Speed |` è vicino a zero solo per l'inizio giusto.
3. Vince il candidato con la più piccola discordanza nel caso peggiore, se quella discordanza è al massimo di
   **1 m/s**. Altrimenti il rilevamento continua ad aspettare.

Mentre l'auto è ferma ogni candidato legge zero e concordano, il che non prova nulla, quindi **il rilevamento
aspetta che l'auto si muova**: guida qualche metro prima di aspettarti un output. Fino a 600 pacchetti vengono
trattenuti durante l'attesa (ridotti agli ultimi 300). Una volta noto il layout, anche i pacchetti trattenuti
vengono decodificati, così l'inizio del primo giro non va perso. I pacchetti di una lunghezza diversa dal layout
rilevato, i pacchetti più corti di 311 byte e quelli con una posizione o una velocità non finite vengono ignorati
per i file dei giri.

Quale Forza sia dipende dal layout: un layout Horizon dà `"game": "forza-horizon"`, un layout Motorsport o a 331
byte dà `"forza-motorsport"`, qualunque altra cosa `"forza"`. Il nome del layout rilevato (`Horizon dash`,
`Motorsport dash`, `331-byte dash`) viene scritto come `layout`.

## Canali registrati {#channels-recorded}

Ogni campo del pacchetto viene decodificato (`decode_full`) e convertito:

- i pedali `throttle`, `brake`, `clutch`, `handbrake` da 0..255 a 0..1;
- `steer` da -127..127 a -1..1; `drivingLine` e `aiBrakeDifference` allo stesso modo divisi per 127;
- `tireTemp.FL` ... `.RR` da Fahrenheit a Celsius;
- `latAcc`, `longAcc`, `vertAcc` e `yawRate` sono copie di `accelX`, `accelZ`, `accelY` e `angVelY` sotto i nomi
  canonici (sistema dell'auto: x a destra, y verso l'alto, z in avanti);
- la velocità Sled, che è nel sistema proprio dell'auto (x a destra, y verso l'alto, z in avanti - non quello del
  mondo), viene scritta direttamente sotto i nomi canonici `latVel`, `vertVel` e `longVel`, così il visualizzatore
  legge l'angolo di deriva da essa invece di stimarlo da direzione e percorso.

I canali del file del giro sono tutti questi tranne i campi per giro:

| Gruppo | Canali |
|---|---|
| Tempo e posizione | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Movimento | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motore | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Pilota | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Per ruota (`.FL .FR .RL .RR`) | `suspension` (0 estesa .. 1 compressa), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizzati: oltre 1 la gomma perde aderenza), `wheelSpeed` (rad/s), `rumble` (su una striscia sonora), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Solo Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` è il cronometro del giro corrente del gioco meno il suo valore al primo campione del giro; `distance` è
la distanza percorsa del gioco meno il suo primo valore. Le posizioni sono le coordinate del mondo di Forza in
metri, invariate (y è verso l'alto; il mondo è sinistrorso).

Presi una volta per giro invece che per campione, sotto `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`,
`cylinders`, `rpmMax`, `rpmIdle`. L'id del tracciato di FM2023 va anch'esso una sola volta, come `lap.trackOrdinal`.
Non conservati per campione: `isRaceOn` (1 in ogni fotogramma di un giro). `timestampMs`, `raceTime`, `bestLap` e
`lastLap` sono conservati come canali.

Il resto del documento viene riempito come quello di ogni altro registratore:

- `"track": null` - Forza Horizon non nomina il tracciato, e Forza Motorsport lo numera soltanto;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - i canali di slittamento sono normalizzati in modo che oltre
  1 la gomma perde aderenza;
- `units` elenca solo i canali che il file ha (quelli per ruota con il loro nome di base);
- un valore che non è un numero finito viene scritto come `null`, mai come `NaN`.

Vedi [Il file heat3d-lap](lap-format.md).

## Come vengono divisi i giri {#how-laps-are-split}

`LapSplitter` (vedi [Come vengono divisi i giri e le tappe](lap-splitting.md)): un giro si chiude quando il contatore
di giri del gioco avanza, e il suo tempo è allora il `lastLap` del gioco (quello che mostra il gioco). Una gara da
punto a punto o una sessione che finisce a metà giro si chiude quando il gioco esce dalla gara (`isRaceOn` scende),
quando i pacchetti si fermano per 2 secondi, o quando il timestamp del gioco torna indietro; viene conservata come
`run` se ha coperto almeno 400 m.

## Inoltro a FH Companion {#relaying-to-fh-companion}

Il gioco invia Data Out a un solo indirizzo. Con `--forward host:port`, il registratore passa **ogni pacchetto
ricevuto invariato**, prima di decodificare qualsiasi cosa (anche mentre aspetta ancora di rilevare il layout), così
un'altra app che legge il feed continua a funzionare: imposta il gioco su 5300, l'altra app su 5301, ed esegui con
`--forward 127.0.0.1:5301`.

FH Companion è un'app separata, non parte di 3DHeat. Tiene una libreria di giri in `%LOCALAPPDATA%\FHCompanion\laps`:
una cartella per tracciato, un file di giro per ogni giro campionato circa ogni cinque metri, e accanto a ogni file di
giro `<giro>.json.tele.gz`, l'intero Data Out del giro alla velocità del gioco. 3DHeat legge entrambi:

- **Il visualizzatore legge `.tele.gz` direttamente** quando lo trascini (con o senza il suo file di giro) nella scheda
  Analisi di gara. Mappa i nomi di campo propri di Forza (`PositionX`, `VelocityX`, `TireSlipRatio` + ruota, ...) sui
  canali canonici, trasforma le `VelocityX/Y/Z` locali all'auto in `latVel`, `vertVel`, `longVel`, converte le
  temperature delle gomme da Fahrenheit, elimina le righe che ripetono la precedente tranne per l'orologio del
  registratore, e segna lo slittamento come `peak`. Dato anche il file di giro, il giro prende da lì l'auto e il tempo
  sul giro. Questo lettore sta nel visualizzatore (`src/race/adapters.ts`, `readForzaTelemetry`), non in questo
  repository.
- **Il comando `laps`** legge la libreria dei giri e scrive il percorso di un tracciato e un CSV di ogni campione; vedi
  [Riferimento dei comandi](commands.md#laps).

## Altri usi dello stesso feed {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` registra solo le posizioni, salvate ogni un paio di secondi mentre guidi; vedi
  [Riferimento dei comandi](commands.md#route).
- L'opzione "Racing telemetry (Forza)" della finestra di scansione usa il feed come pose esatte della camera per la
  ricostruzione; vedi [Posa della camera e scala](reconstruction-pose.md#telemetry-poses).

## Note e avvertenze {#notes-and-caveats}

- Non è documentato con cosa Forza normalizza lo slittamento. `1` viene letto come il bordo dell'aderenza, ma il
  visualizzatore misura dove la presa di ogni auto cala davvero.
- La velocità Sled è locale all'auto, come dice la documentazione di Data Out di Forza e come confermano i giri
  registrati (la sua componente in avanti porta la velocità, quella laterale resta vicina a zero). Il rilevamento del
  layout usa solo la sua lunghezza, che è la stessa in ogni fotogramma.
- Le posizioni sono il mondo del gioco, con Y verso l'alto e sinistrorso. I versi di `yaw`, `pitch` e `roll` sono stati
  verificati sui giri registrati: l'imbardata è uguale alla direzione di marcia `atan2(dx, dz)`, un beccheggio positivo è
  muso in giù, e un rollio positivo abbassa il lato destro.
