---
title: Il file heat3d-lap
nav_order: 9
lang: "it"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Il file `heat3d-lap` {#the-heat3d-lap-file}

Ogni registratore di telemetria di questo repository scrive un file per giro o
tappa rally, con la stessa forma qualunque sia il gioco. L'esportazione dei tracciati
in [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) lo legge per
trovare il gioco, il livello e la linea percorsa. Qualunque cosa legga JSON può leggerlo.

![I campi e i canali di un file di giro scritto da un feed Forza sintetico](../assets/img/lap-file.svg)

## Il documento {#the-document}

Un oggetto JSON. I canali sono memorizzati come colonne: un array per canale, tutti
della stessa lunghezza, un elemento per campione.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Campo | Significato |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | da quale gioco viene il giro; vedi l'elenco sotto |
| `track` | il nome del tracciato, della tappa o della mappa, quando il gioco lo invia |
| `layout` | solo Forza: quale layout di pacchetto Data Out è stato decodificato |
| `car` | tutto ciò che il gioco dice dell'auto; a formato libero |
| `lap` | il numero del giro, il suo tempo come lo ha contato il gioco (o la durata dei campioni), se è stato completato, la sua lunghezza |
| `meta` | come leggere i numeri; vedi sotto |
| `units` | l'unità di ogni canale presente, per un lettore che non conosce la tabella sotto |
| `channels` | i campioni |
| `unparsed` | solo Forza, quando il pacchetto ha byte che nessun campo nomina: `ranges` (i loro offset in byte `[inizio, fine)` nel pacchetto) e `hex` (per campione, quei byte in esadecimale), così il file da solo contiene l'intero pacchetto |

`game` è uno di `forza-horizon`, `forza-motorsport`, `forza` (layout del pacchetto
non distinto), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` dice cosa significano i numeri dove i giochi differiscono:

- `slip`: cosa contengono i canali di slittamento, dove il gioco ne invia - `peak`
  (normalizzato, quindi oltre 1 la gomma perde aderenza: Forza), `scaled` (uno
  slittamento fisico diviso per un picco d'asfalto tipico: i giochi Assetto Corsa),
  `physical` (una frazione e radianti), `index` (una misura di scivolamento 0..1:
  Trackmania);
- `discipline`: `circuit`, `rally` o `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` o `mixed`, quando è noto (i registratori
  rally lo prendono da `--surface`).

## Canali {#channels}

Un canale che il gioco non invia è assente, mai riempito di zeri. I canali per ruota
portano la ruota dopo un punto: `.FL`, `.FR`, `.RL`, `.RR`.

Le posizioni sono nel mondo del gioco, in metri, con `y` verso l'alto. Un gioco il cui
mondo ha Z verso l'alto viene ruotato a Y verso l'alto dal suo registratore; non si
cambia altro, quindi un mondo sinistrorso (quello di Forza) resta sinistrorso.

| Canale | Unità | Significato |
|---|---|---|
| `time` | s | dal primo campione del giro |
| `distance` | m | lungo il percorso fatto dal primo campione |
| `x`, `y`, `z` | m | posizione; `y` è l'altezza |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedali e leva |
| `steer` | -1..1 | positivo a destra |
| `gear` | | come lo conta il gioco |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | sistema dell'auto |
| `yaw`, `pitch`, `roll` | rad | direzione e assetto |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | velocità nel sistema dell'auto: destra, avanti, alto |
| `bodySlip` | rad | angolo di deriva, dove il gioco lo invia |
| `loose` | 0/1 | su fondo sciolto (Trackmania) |
| `airborne` | 0/1 | nessuna ruota a terra |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | come li invia il gioco |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | aiuti in funzione, sistemi attivi |
| `absLevel`, `tcLevel` | | impostazioni degli aiuti |
| `brakeBias` | 0..1 | quota anteriore |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | per ruota |
| `tirePressure` | psi | per ruota |
| `tireWear` | 0..1 | per ruota |
| `slipRatio`, `slipAngle`, `combinedSlip` | vedi `meta.slip` | per ruota |
| `slipIndex` | 0..1 | per ruota, misura di scivolamento (Trackmania) |
| `camber` | rad | per ruota |
| `brakeTemp` | °C | per ruota |
| `padLife`, `discLife` | | per ruota |
| `suspensionM` | m | per ruota, corsa della sospensione |
| `suspension` | 0..1 | per ruota, corsa nel range usato in questo giro |
| `wheelLoad` | N | per ruota |
| `wheelSpeed` | rad/s | per ruota, rotazione |
| `wheelSurfaceSpeed` | m/s | per ruota, velocità del punto di contatto |
| `groundContact` | 0/1 | per ruota |
| `rumble`, `surfaceRumble` | | per ruota: su una striscia sonora; il rumble della superficie |
| `puddle` | | per ruota, profondità dell'acqua stagnante |

Un registratore può aggiungere canali propri con altri nomi; un lettore conserva quelli
che non conosce.

Nessun gioco rally invia lo slittamento delle gomme. Un lettore può calcolarlo dalla
velocità del punto di contatto o di superficie di ogni ruota rispetto alla velocità
dell'auto, `(ruota - auto) / auto`, oppure dalla sua rotazione e da un raggio di
rotolamento misurato sul giro stesso dove viene inviata solo la rotazione. L'angolo di
deriva viene dalla velocità propria dell'auto (`latVel`, `longVel`) dove è inviata, o
dalla velocità nel mondo proiettata sugli assi dell'auto.

## Il formato CSV {#the-csv-form}

Il plugin di Trackmania scrive invece `heat3d-lap-csv`: una prima riga con `# ` e un
oggetto JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), una
riga con i nomi dei canali, poi una riga per campione. I nomi dei canali sono gli stessi
di sopra.

## Cosa scrive davvero ogni registratore {#what-each-recorder-actually-writes}

Il formato sopra è il contratto; i registratori lo riempiono in modo leggermente diverso,
e un lettore deve tollerarli tutti (verificato sul codice):

| Registratore | `track` | `layout` | `meta` | `units` | Canali oltre la tabella |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (il numero di tracciato di Forza Motorsport 2023 è `lap.trackOrdinal`) | il layout di pacchetto rilevato | `slip: peak`, `discipline: circuit` | solo le unità dei canali presenti | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, l'orologio del gioco `timestampMs`, `raceTime`, `bestLap`, `lastLap`; la velocità locale all'auto è sotto i canonici `latVel`, `vertVel`, `longVel`; `unparsed` accanto ai canali |
| Giochi Assetto Corsa (`kunos.py`) | dalla pagina statica, oppure `null` | assente | `slip: scaled`, `discipline: circuit` o `rally` | un elenco fisso | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (come inviato), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Giochi rally (`rally.py` tramite `lapfile.py`) | `null` | assente | `discipline: rally`, `slip: null`, `surface` solo quando è stato dato `--surface` (altrimenti lo deduce il visualizzatore) | solo le unità dei canali presenti | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` per i float senza un nome definito; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` tramite `lapfile.py`) | `null` | assente | `discipline: circuit` | solo le unità dei canali presenti | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Plugin Trackmania (CSV) | il nome della mappa | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` è il blocco auto di Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`,
`cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` per i giochi Kunos quando la pagina
statica ne indica uno, e `{}` altrimenti. `lap.metres` è la differenza di distanza
percorsa del gioco per Forza, e altrove la somma delle distanze 3D tra campioni. I
valori vengono arrotondati in scrittura: `time` a 4 decimali, `distance` a 3, gli altri
float a 5. Il JSON viene scritto compatto (senza spazi).

Ogni pacchetto o pagina ricevuto dal registratore - non solo quelli dei giri - viene
conservato intero accanto ai file dei giri in `<data>_<gioco>.raw.parquet`, con un
controllo di completezza in `<data>_<gioco>.summary.json` (la sezione "Completeness"
del README).

Un campione per cui un canale non ha valore - mancante in quel fotogramma, o non un
numero finito come lo ha inviato il gioco - viene scritto come `null` da ogni
registratore (`lapfile.clean`), e la frazione di sospensione derivata da esso è anch'essa
`null`. `NaN` e `Infinity` non vengono mai scritti: non sono JSON, e il `JSON.parse` di
un browser rifiuta l'intero file per uno solo di essi. Un lettore deve aspettarsi `null`
dentro l'array di un canale.

I file di Forza portano `"game": "forza-horizon"`, `"forza-motorsport"` o `"forza"`
secondo il layout rilevato. Il lettore del visualizzatore per i file `.tele.gz` di FH
Companion produce giri con `"game": "forza-horizon"` e `meta.slip = "peak"`; quel lettore
si trova nel visualizzatore, non qui. I giri di iRacing (letti dai file `.ibt` nel
visualizzatore) portano `"game": "iracing"`, che non è nell'elenco dei valori `game`
dei registratori sopra perché nessun registratore lo scrive.

Vedi [Divisione in giri e tappe](lap-splitting.md) per come vengono decisi
`lap.number`, `lap.seconds` e `lap.complete`, e [Slittamento, deriva e canali
derivati](slip-and-drift.md) per ciò che il visualizzatore deriva da questi canali.
