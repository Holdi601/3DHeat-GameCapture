---
title: Slittamento, deriva e canali derivati
nav_order: 8
lang: "it"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Slittamento, deriva e canali derivati {#slip-drift-and-derived-channels}

L'analisi del controllo dell'auto nella scheda Analisi di gara del visualizzatore ha bisogno delle stesse
poche grandezze da ogni gioco: di quanto slitta ogni gomma, di quanto l'auto punta lontano da dove sta
andando (l'angolo di deriva), se è in aria, se è su un fondo sciolto. I giochi le inviano in forme molto
diverse, o non le inviano affatto. I registratori qui scrivono ciò che ogni gioco invia, con nomi canonici,
più una nota `meta.slip` che dice cosa significano i numeri di slittamento; poi il visualizzatore deriva
ciò che manca, una volta, quando carica un giro. **Il valore del gioco vince sempre su quello derivato.**

## Cosa scrivono i registratori {#what-the-recorders-write}

| Gioco | Canali di slittamento | `meta.slip` | Ingressi dell'angolo di deriva |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` per ruota, come inviati | `peak` (lo scrive il registratore; il lettore `.tele.gz` del visualizzatore imposta lo stesso) | `latVel`, `longVel` dalla velocità locale all'auto |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, più `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` dalla velocità nel sistema dell'auto |
| EA SPORTS WRC, giochi DiRT | nessuno; invece `wheelSurfaceSpeed` per ruota | `null` | `latVel`, `longVel` = velocità nel mondo proiettata sugli assi dell'auto |
| Richard Burns Rally | nessuno; nemmeno velocità delle ruote | nessuno | `latVel`, `longVel` = le oscillazioni laterali e longitudinali proprie dell'auto |
| BeamNG.drive | nessuno; `wheelSurfaceSpeed` e `wheelSpeed` per ruota | nessuno | `latVel`, `longVel` = velocità nel mondo proiettata sugli assi dell'auto |
| Trackmania | `slipIndex` per ruota (una misura di scivolamento 0..1) | `index` | `latVel` (velocità laterale), `longVel` (velocità frontale) |
| iRacing | nessuno (non registrato) | nessuno | `yaw` e il percorso, `yawRate` |

I valori di `meta.slip` sono definiti in [Il file heat3d-lap](lap-format.md): `peak` (normalizzato, quindi
oltre 1 la gomma perde aderenza), `scaled` (uno slittamento fisico diviso per un picco d'asfalto tipico),
`physical` (una frazione e radianti), `index` (una misura di scivolamento 0..1).

### Perché lo slittamento Kunos è scalato {#why-kunos-slip-is-scaled}

Lo slittamento di Forza è normalizzato in modo che 1 sia il bordo dell'aderenza; ciò su cui si normalizza
non è documentato. Kunos invia il rapporto di slittamento fisico (una frazione) e l'angolo di slittamento
(radianti). Dividendo per un picco d'asfalto tipico - 0,12 per il rapporto, 0,14 rad (circa 8 gradi) per
l'angolo - "oltre 1 significa che sta slittando" diventa approssimativamente vero per entrambe le famiglie,
il che mantiene una sola lettura per le schermate del visualizzatore. È un'approssimazione: i picchi reali
variano per gomma e superficie, ed è per questo che i valori grezzi vengono conservati accanto a quelli
scalati, e perché il visualizzatore misura dai giri stessi dove la presa di ogni auto cala davvero.

## Cosa deriva il visualizzatore (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Questi girano nel visualizzatore (`src/race/derive.ts` nel visualizzatore 3DHeat), non in questo repository.

### Angolo di deriva, `bodySlip` {#drift-angle-bodyslip}

- **Dalla velocità nel sistema dell'auto** quando sono presenti `latVel` e `longVel`:
  `atan2(latVel, |longVel|)`, e 0 sotto i 3 m/s (un'auto ferma di traverso non sta derivando).
  Il suo segno segue la velocità laterale del gioco, il cui verso è documentato in entrambi i sensi per
  alcuni giochi - leggi la grandezza.
- **Altrimenti dalla direzione rispetto al percorso**: la direzione di marcia viene presa dalle posizioni
  a circa 2 m da ogni lato di ogni campione (`atan2(dx, dz)`); lo `yaw` del gioco viene adattato ad essa
  con un segno e un offset (ogni gioco ha il suo zero e il suo verso di rotazione) usando i campioni sopra
  i 10 m/s, e considerato affidabile solo se poi concorda da vicino (dispersione circolare al massimo 0,05,
  almeno 20 campioni). L'angolo di deriva è la differenza, 0 sotto i 3 m/s.

### Rapporto di slittamento dalle ruote {#slip-ratio-from-the-wheels}

Dove un giro non ha `slipRatio.*` ma ha velocità delle ruote, il rapporto di slittamento è
`(ruota - auto) / auto` per ruota, da:

- `wheelSurfaceSpeed.*` (la velocità del punto di contatto, m/s) direttamente, quando inviata (EA WRC,
  DiRT, BeamNG);
- altrimenti `wheelSpeed.*` (rotazione, rad/s) per un **raggio di rotolamento misurato sul giro**: la
  mediana di `speed / |omega|` sui campioni in cui l'auto rolla in rettilineo (sopra i 10 m/s, non in aria,
  acceleratore sotto 0,3, freno sotto 0,05, accelerazione longitudinale sotto 3 m/s²); con meno di 20 di
  questi campioni, ogni campione sopra i 10 m/s. Un raggio fuori da 0,1-1 m viene rifiutato.

Solo quando si possono derivare tutte e quattro le ruote; il `meta.slip` del giro diventa allora
`physical`. Sotto i 3 m/s lo slittamento è 0.

### In aria {#airborne}

`airborne` vale 1 dove ogni ruota è staccata da terra, giudicato dal primo di questi che il giro ha per
tutte e quattro le ruote:

1. `groundContact.*` (BeamNG): nessuna ruota sopra 0,5;
2. `wheelLoad.*` (giochi AC, RBR, BeamNG): nessuna ruota sopra il 5% del proprio carico mediano;
3. `suspension.*` (0..1 della corsa): nessuna ruota sopra 0,02, cioè tutte completamente estese.

Un singolo campione isolato in aria viene cancellato. Trackmania scrive `airborne` da sé.

### Fondo sciolto {#loose-ground}

Dove un giro ha `surfaceRumble.*` (Forza), `loose` vale 1 dove almeno due ruote segnalano rumble per almeno
un terzo di secondo, con i vuoti più corti di un secondo colmati (un tratto liscio su una strada sterrata
resta la strada sterrata). Trackmania scrive `loose` da sé dai materiali del suolo delle ruote.

### Velocità di imbardata {#yaw-rate}

Dove un giro ha `yaw` ma non `yawRate`, è la variazione di imbardata sui campioni vicini.

## Cosa derivano da sé i registratori {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): ogni registratore tranne Forza (che la invia) la scrive da `suspensionM.*`
  come posizione nel range usato da questo giro (minimo e massimo). Serve alle barre delle sospensioni
  dell'auto e a notare una ruota sospesa in aria; non è una frazione assoluta della corsa.
- **`steer`** per i giochi Kunos, scalato per giro (vedi [Giochi Assetto Corsa](telemetry-assetto-corsa.md)).
- **Accelerazioni** per BeamNG, dalla variazione della velocità nel mondo ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** e l'asse verticale per Richard Burns Rally, dalle posizioni ([Giochi rally](telemetry-rally.md)).

## Lateralità {#handedness}

Dove il mondo di un gioco è sinistrorso - quello di Forza lo è - un tracciato esce specchiato in un
visualizzatore destrorso; lo sterzo e le sospensioni dei giri stessi lo rivelano. I registratori non
cambiano la lateralità: un mondo con Z verso l'alto (BeamNG) viene portato a Y verso l'alto con una
rotazione, che la conserva, e tutto il resto viene scritto come inviato.
