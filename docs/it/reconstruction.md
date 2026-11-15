---
title: Ricostruzione del livello
nav_order: 6
lang: "it"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Ricostruzione del livello dal gioco {#level-reconstruction-from-gameplay}

Cammina lentamente in un livello, o guida su un tracciato, e lo scanner trasforma ciò che lo schermo
ha mostrato in un `.glb` che il visualizzatore di 3DHeat carica come contesto sotto la telemetria - lo stesso
contratto di file che scrive l'esportatore per Unreal. È pensato per il caso in cui nessuno abbia
esportato la mappa e i file del gioco non si possono leggere; un export dal motore o dai file di
gioco è esatto, questo è una stima.

## La pipeline {#the-pipeline}

```text
 fotogrammi          fotogrammi chiave    profondità           posa                 fusione             output
 ----------          -----------------    ----------           ----                 -------             ------
 Windows Graphics -> soglia di        ->  Depth Anything V2 -> odometria visiva -> volume di          -> marching cubes
 Capture, oppure     cambio immagine      (ONNX Runtime,       (ORB + PnP), oppure    occupazione         -> terreno/struttura
 un file video       (adattiva)           letterboxed)         telemetria di Forza,   + griglia di       -> colore per vertice
                                                               oppure una soluzione   copertura           -> .glb
                                                               VGGT                   (mappa in diretta,
                     maschere HUD / abitacolo, consigli sulla                          punti deboli)
                     qualità dei fotogrammi, scala dal piano del terreno
```

| Fase | Scansione dal vivo (`heat3d_capture.ui`) | Offline (`reconstruct`) | Pagina |
|---|---|---|---|
| Fotogrammi | monitor, finestra o video, ridimensionati al lato più lungo del preset | video, campionato due volte (piano di soluzione e intervallo di fusione) | [Cattura](reconstruction-capture.md) |
| Fotogrammi chiave | tenuti in base a quanto è cambiata l'immagine, soglia adattata alla cattura | ogni `--fuse-interval` secondi | [Cattura](reconstruction-capture.md#keyframes) |
| Maschere | `ScreenMask` basata sui cambiamenti, poi `FlowMask` basata sul flusso dopo 40 fotogrammi chiave | `FlowMask` appresa da quattro passate del video; non applicata al solutore | [Cattura](reconstruction-capture.md#what-is-not-the-world) |
| Profondità | modello ONNX sul miglior backend GPU | Depth Anything V2 Small in PyTorch | [Profondità](reconstruction-depth.md) |
| Posa | odometria visiva, oppure telemetria esatta di Forza | finestre VGGT cucite in un unico percorso, interpolato | [Posa](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Scala | altezza della camera dal terreno (1,15 m) una volta, oppure telemetria | le unità del percorso risolto | [Posa](reconstruction-pose.md#scale) |
| Fusione | occupazione pesata, voxel sparsi; griglia di copertura | lo stesso | [Fusione](reconstruction-fusion-and-texture.md) |
| Output | `.glb`, parti terreno/struttura, colore per vertice, centimetri | lo stesso | [L'output .glb](glb-output.md) |

Codice: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - impostazioni e ritmo di una scansione; `reconstruct.py` - fotogrammi chiave in
geometria; `offline.py` - il percorso offline), con le fasi in `capture/`, `depth/`, `pose/`, `fusion/`
e `geometry/`.

## Da dove viene la precisione {#where-accuracy-comes-from}

La profondità monoculare è giusta solo a meno di una scala sconosciuta - una foto di una stanza e di
una casa delle bambole sono la stessa immagine. Quindi alla rete si lascia fare ciò che sa fare bene
(forma relativa, bordi, strutture sottili), e la scala e il percorso della camera arrivano da qualcosa
che li conosce:

| Gioco | Percorso della camera | Scala |
|---|---|---|
| Forza Horizon / Motorsport con telemetria attiva | esatto, da Data Out, interpolato al momento di cattura di ogni fotogramma | esatta: la profondità è ancorata triangolando le feature tra due pose note |
| Qualsiasi altro, dal vivo | odometria visiva, concatenata fotogramma per fotogramma | fissata una volta da un'altezza ipotizzata della camera dal terreno |
| Una registrazione, offline | VGGT, risolto su finestre sovrapposte | le unità della soluzione (non metriche) |

L'unico numero che lo scanner riceve come dato, invece di misurarlo, è il **campo visivo orizzontale**
del gioco (90 gradi per impostazione predefinita nella finestra; i giochi di corse sono più vicini a
65). Se è troppo stretto il livello viene ricostruito più profondo di quanto sia; se è troppo largo
viene appiattito.

## Dire subito all'utente {#telling-the-user-early}

Una scansione è un atto fisico - qualcuno cammina in un livello per diversi minuti - e il fallimento
costoso è finire la passeggiata e scoprire che non andava bene. Quindi la finestra misura la velocità
di profondità di questa macchina prima che si possa partire, e dice com'è probabile che sarà la
scansione ([Runtime](runtime.md#what-to-expect-from-this-machine)); durante la scansione mostra una
mappa di copertura con i punti deboli numerati, la salute del tracking, una barra della velocità di
cammino, una barra della nitidezza e un'istruzione alla volta, nella finestra e in una sovrapposizione
cliccabile sopra il gioco ([La finestra di scansione](reconstruction-scan-ui.md)).

## Misurato su una verità di riferimento sintetica {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` disegna una stanza di 12 x 8 m (4 m di altezza) da un percorso noto della
camera, con profondità analitica (non dalla rete), e la ricostruisce con voxel da 0,2 m. Verifica che
più del 90% dei fotogrammi venga posizionato, che l'errore medio del percorso sia sotto 0,35 m (il
peggiore sotto 1 m), che la distanza percorsa sia entro il 10% del vero, che la stanza esca della
larghezza giusta entro 1,5 m, che oltre il 75% della superficie delle pareti giaccia entro 0,45 m da
una parete reale, che una passeggiata in stile rilievo ottenga una copertura nettamente migliore di
un cammino dritto in avanti, e che una scena senza feature venga rifiutata invece che inventata.
La profondità analitica isola posa, scala e fusione dalla rete; come se la cava la rete nel gioco
reale è una domanda separata a cui nessuna scena sintetica risponde.
`tests/test_track_width.py` verifica che un giro guidato fuori centro su una strada di larghezza nota
ricostruisca la larghezza della strada, non solo la linea percorsa.

## Pagine {#pages}

- [La finestra di scansione](reconstruction-scan-ui.md) - ogni controllo, scorciatoia e elemento della sovrapposizione
- [Cattura, maschere e qualità dei fotogrammi](reconstruction-capture.md)
- [Profondità](reconstruction-depth.md)
- [Posa della camera e scala](reconstruction-pose.md)
- [Fusione, copertura e colore](reconstruction-fusion-and-texture.md)
- [L'output .glb](glb-output.md)
- [Ricostruzione offline](reconstruction-offline.md)
