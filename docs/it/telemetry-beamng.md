---
title: BeamNG.drive
nav_order: 4
lang: "it"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copia la mod, poi registra
python -m heat3d_capture telemetry --game beamng -o laps      # registra
```

Poi nel gioco: **Opzioni > Altro > Protocolli**, attiva **"others"**.

Codice: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
e la mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Test: `tests/test_beamng.py`, su pacchetti costruiti dalla struct della mod. **La mod non è ancora
stata eseguita nel gioco.**

## Perché una mod {#why-a-mod}

BeamNG invia la telemetria tramite "protocolli": moduli Lua nel veicolo che il file
`lua/vehicle/protocols.lua` del gioco impacchetta e invia via UDP dall'auto guidata dal giocatore.
Quelli di serie non contengono ciò che serve a un'analisi del controllo dell'auto - OutGauge non ha
la posizione, MotionSim non ha le ruote, e OutSim è un segnaposto nelle versioni attuali. Quindi
questo progetto include un proprio protocollo, `heat3d`. Non tocca nulla al di fuori del Lua del
veicolo stesso.

## Installazione {#installing}

`--install` copia `mods/beamng/heat3d` in
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 e successive tengono lì
le mod dell'utente), eliminando prima una copia precedente, e stampa dove l'ha messa. Senza
`LOCALAPPDATA` ricade sulla cartella home. Puoi anche copiare la cartella a mano.

Dopo `--install` si prosegue direttamente con la registrazione.

## La mod {#the-mod}

| Impostazione (in `heat3d.lua`) | Valore |
|---|---|
| Indirizzo | `127.0.0.1` |
| Porta | `4460` - cambiala qui e passa la stessa `--port` al registratore |
| Frequenza massima di aggiornamento | 100 Hz |
| Passo di fisica | usato (`isPhysicsStepUsed` restituisce true) |

Ogni pacchetto è il magic a 4 byte `H3D1` seguito da 39 float little-endian (160 byte in tutto):

| Campo | Quanti | Fonte nel Lua del veicolo |
|---|---|---|
| `time` | 1 | l'orologio della mod: somma dei passi di fisica, azzerato quando il veicolo viene ripristinato |
| posizione | 3 | `obj:getPositionXYZ()` |
| velocità | 3 | `obj:getVelocityXYZ()` (mondo) |
| avanti | 3 | `obj:getDirectionVector()` |
| su | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, e 1/0 da `absActive` e `tcsActive` |
| `wheelSpeed` | 4 | velocità di superficie di ogni ruota (m/s) |
| `wheelAngular` | 4 | velocità angolare per la direzione della ruota (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 quando è in aria |

Le quattro ruote vengono scelte in base a **dove si trovano sull'auto**, non per nome (i nomi variano
da veicolo a veicolo): anteriore o posteriore in base alla posizione del nodo lungo l'auto, sinistra o
destra attraverso di essa (frame del veicolo +X a sinistra, -Y in avanti), prendendo per ogni angolo la
ruota più lontana dal centro. Un angolo mancante viene inviato come zeri con materiale -1.

## Cosa fa il registratore {#what-the-recorder-does-with-it}

Il mondo di BeamNG ha Z verso l'alto; quello del visualizzatore ha Y verso l'alto. Posizioni e vettori vengono
ruotati attorno a X, `(x, y, z) -> (x, z, -y)`, che mantiene il sistema destrorso del mondo. Poi:

| Canale | Derivato come |
|---|---|
| `x`, `y`, `z` | posizione ruotata |
| `speed` | lunghezza della velocità ruotata |
| `longVel`, `latVel`, `vertVel` | velocità proiettata su avanti, su destra = avanti x su, su su |
| `longAcc`, `latAcc`, `vertAcc` | variazione della velocità nel mondo su ±2 campioni, proiettata sugli stessi assi (il sistema di riferimento dei sensori dell'auto non è documentato, quindi non vengono usati) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | come inviati |
| `absActive`, `tcActive` | le spie ABS e TC, dove l'auto le ha |
| `wheelSurfaceSpeed.*` | valore assoluto della velocità di superficie della ruota |
| `wheelSpeed.*` | rotazione |
| `wheelLoad.*` | carico |
| `groundContact.*` | 0 quando il materiale è negativo, altrimenti 1 |

I pacchetti senza il magic o più corti di 160 byte vengono ignorati.

## Giri {#laps}

`LineSplitter`, come per AC EVO: il punto in cui è iniziata la registrazione è la linea; un giro si
chiude dove l'auto ripassa più vicina a essa con la stessa direzione, almeno 300 m dopo. Un giro
conta come completo solo se è iniziato a più di 5 m/s, quindi il primo giro da fermo è parziale. Quando
l'orologio della mod torna indietro di più di mezzo secondo (l'auto è stata ripristinata), la corsa
aperta in quel momento viene chiusa per prima - scritta come corsa parziale se ha coperto almeno 300 m,
come alla fine di una registrazione - e poi il divisore riparte da capo. Vedi
[Suddivisione dei giri e delle tappe](lap-splitting.md).

## Il file del giro {#the-lap-file}

`game` è `beamng`, `meta` è `{"discipline": "circuit"}`, i file si chiamano
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Non viene scritto nessuno slip; il visualizzatore lo ricava
dalle velocità di superficie delle ruote (vedi [Slittamento, deriva e canali derivati](slip-and-drift.md)). Le
posizioni sono nello stesso sistema di riferimento in cui scrive l'export del tracciato BeamNG di
GameFiles, quindi un giro registrato si posiziona su un tracciato esportato.
