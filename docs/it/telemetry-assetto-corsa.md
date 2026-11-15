---
title: Giochi Assetto Corsa
nav_order: 2
lang: "it"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO e AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Codice: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Test: `tests/test_kunos.py` (pagine sintetiche). Non ancora eseguito contro i giochi veri.

## Da dove arrivano i dati {#where-the-data-comes-from}

I giochi Kunos pubblicano la telemetria per le app come **pagine di memoria condivisa di Windows con nome**
che il gioco scrive e che chiunque può leggere. Il registratore le apre in sola lettura (`mmap` con un nome
di tag), quindi deve girare **sul PC su cui gira il gioco**, su Windows; altrove esce con un messaggio.
Le pagine vengono aperte una volta sola, all'avvio del registratore. Avviare prima il gioco e salire in
auto è l'ordine sicuro; se avviare il registratore prima del gioco funzioni non è stato verificato.

| `--game` | Pagina fisica | Pagina grafica (contatore di giri) | Pagina statica (nomi) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | non usata | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | non usata | `Local\acevo_pmf_static` |

La pagina fisica viene letta 200 volte al secondo (`hz=200`); un nuovo campione viene preso solo quando il suo
`packetId` è cambiato ed è diverso da zero. I primi 800 byte della pagina fisica hanno lo stesso layout nei
quattro giochi; la pagina del primo gioco è garantita solo per 580 byte, quindi se una mappatura da 800 byte non
può essere aperta il registratore ricade su 580 e i campi oltre sono assenti.

## Posizione {#position}

Nessuna pagina porta una posizione dell'auto come tale, ma la pagina fisica contiene **il punto di contatto di
ogni gomma in coordinate del mondo** (offset 420, quattro terne XYZ). La posizione dell'auto è la media dei
quattro. Una pagina con tutti i punti di contatto a zero (menu, garage) non produce alcun campione.

## Canali {#channels}

| Canale | Da | Note |
|---|---|---|
| `time` | l'orologio del registratore | secondi dall'inizio della registrazione, riportati al primo campione del giro |
| `x`, `y`, `z` | punto di contatto medio delle gomme | metri nel mondo |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | unità del gioco, scalate per giro a -1..1 dal valore assoluto più grande usato nel giro, **solo se** quel valore supera 1,05 (un ingresso già in -1..1 resta invariato) |
| `gear` | `gear - 1` | il gioco conta 0 retromarcia, 1 folle, 2 prima; scritto come -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, per 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | velocità locale all'offset 568 | sistema dell'auto; solo quando diversa da zero. Il lato verso cui punta x è documentato in entrambi i sensi, quindi leggi la grandezza dell'angolo di deriva, non il suo segno |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | solo pagina da 800 byte |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offset 204 e 252, scritti come 1 quando sono sopra 0; AC: `tcInAction`/`absInAction` dalla pagina da 800 byte quando presente | aiuti in funzione |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | derivato | 0..1 della corsa usata in questo giro (min e max di `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offset 640, 656 (pagina da 800 byte) | divisi per un picco tipico - vedi sotto |
| `slipRatioRaw.*`, `slipAngleRaw.*` | gli stessi | i valori fisici, non scalati |
| `padLife.*`, `discLife.*` | offset 740, 756 | solo pagina da 800 byte |

AC Rally invia le temperature delle gomme e dei freni in kelvin: per `--game acrally`, ogni valore di quelle
temperature sopra 200 viene diminuito di 273,15.

`wheelSlip` (offset 56) viene decodificato ma non scritto.

## Scalatura dello slittamento {#slip-scaling}

Forza invia lo slittamento normalizzato in modo che 1 sia il bordo dell'aderenza. Kunos invia il rapporto di
slittamento fisico e l'angolo di slittamento. Quindi il registratore li divide per un picco d'asfalto tipico -
**0,12** per il rapporto di slittamento e **0,14 rad (circa 8 gradi)** per l'angolo di slittamento - così la
lettura "oltre 1 significa che sta slittando" del visualizzatore regge approssimativamente, conserva i valori
grezzi accanto a quelli scalati, e scrive `"meta": {"slip": "scaled"}`. Dove la presa finisce davvero, il
visualizzatore la misura per ogni auto dai giri. Vedi [Slittamento, deriva e canali derivati](slip-and-drift.md).

## Giri {#laps}

- **AC e ACC** contano i giri sulla pagina grafica (`completedLaps` all'offset 132, il tempo dell'ultimo giro in
  millisecondi a 144). `CounterSplitter` chiude un giro quando il contatore cambia; viene marcato come completo,
  con il tempo del gioco, solo se il contatore è salito esattamente di uno.
- **AC EVO e AC Rally** non vengono letti per i giri (la pagina grafica di EVO è un layout diverso e più grande;
  AC Rally corre tappe). `LineSplitter` usa il punto in cui è iniziata la registrazione come linea: un giro si
  chiude quando l'auto passa di nuovo il più vicino possibile alla linea nella stessa direzione, e una tappa o una
  corsa qualunque si chiude quando l'auto sta ferma per 8 secondi.

Dettagli e soglie: [Come vengono divisi i giri e le tappe](lap-splitting.md).

## Nomi di auto e tracciato {#track-and-car-names}

Letti una volta sola, dalla pagina statica, quando arriva il primo campione: per AC, ACC e AC Rally l'auto
(UTF-16, offset 68) e il tracciato (offset 134); per AC EVO il tracciato e la sua configurazione (testo a byte
singolo agli offset 136 e 169, uniti da uno spazio) e nessuna auto. Finiscono nel file come `track` e
`car: {"name": ...}`.

## Il file del giro {#the-lap-file}

`game` è `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` o `assetto-corsa-rally`; `meta` è
`{"slip": "scaled", "discipline": "rally"}` per AC Rally e `{"slip": "scaled", "discipline": "circuit"}` per gli
altri tre. Nessun `surface` viene scritto.

## Fonti {#sources}

L'SDK di memoria condivisa di AC1; la documentazione della memoria condivisa di ACC (v1.8); il layout di AC EVO
come misurato in `albertowd/live-telemetry-evo`; quello di AC Rally come letto da
`LuizZak/AssettoCorsaRallyTelemetryReader`. Vedi [Giochi](games.md).
