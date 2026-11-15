---
title: Fusione, copertura e colore
nav_order: 5
lang: "it"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusione, copertura e colore {#fusion-coverage-and-colour}

Codice: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Ogni fotogramma chiave posizionato aggiorna due griglie sparse insieme: il **volume di superficie**,
che diventa la mesh, e la **griglia di copertura**, che dice quanto crederle e dove tornare.
Entrambe vengono aggiornate per ogni fotogramma chiave, non alla fine, perché la mappa di copertura
è ciò con cui il giocatore si orienta.

## Dalla profondità ai punti {#from-depth-to-points}

Per ogni fotogramma chiave la cui posa è nota **e** la cui profondità ha una scala:

1. Viene usato ogni secondo pixel in ogni direzione (`PIXEL_STRIDE = 2`; i pixel vicini di una
   stessa superficie non sono misure indipendenti).
2. La profondità viene convertita in metri con l'affine del fotogramma.
3. Vengono tenuti solo i valori tra **0,35 m** (più vicino è l'arma, l'HUD, il cofano) e **60 m**
   (l'errore monoculare cresce più o meno con il quadrato della distanza, quindi i punti lontani
   sono rumore con la forma della geometria), e solo sui pixel del mondo della maschera.
4. Vengono sollevati attraverso il modello di camera e spostati nel mondo dalla posa.
5. Ogni punto porta il colore del suo pixel.

Un fotogramma posizionato ma senza una scala di profondità viene contato come *posizionato* ma non
*fuso*.

## Il volume di superficie {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - il voxel è il "Surface detail" della finestra.

### Occupazione pesata, non un TSDF {#weighted-occupancy-not-a-tsdf}

Un campo di distanza con segno troncato scava lungo ogni raggio di ogni pixel e azzecca gli oggetti
sottili e lo spazio libero pulito, perché sa che il raggio è passato *attraverso* lo spazio vuoto.
Questo richiede di percorrere il raggio per ognuno di centinaia di milioni di pixel. Questo volume
invece accumula **occupazione pesata** per voxel ed esegue il marching cubes sul risultato
levigato: abbastanza veloce da girare durante la scansione, su una macchina senza una GPU utilizzabile,
e l'output è una superficie chiusa invece che una nuvola di punti. Il costo: gli oggetti sottili e lo
spazio libero sono peggiori di quanto otterrebbe un TSDF.

### Integrare un fotogramma {#integrating-a-frame}

- I punti vengono raggruppati nei voxel (`floor(punto / voxel)`).
- Ogni voxel toccato riceve `peso x sqrt(conteggio / conteggio_massimo)`, dove `conteggio` è quanti
  punti del fotogramma cadono in esso e `peso = max(0.1, confidenza della posa)`. Radice quadrata:
  oltre un certo punto, altri pixel della stessa superficie dallo stesso posto non sono più prova;
  pesare per la confidenza della posa impedisce a una posa dubbia di spingere in giro la superficie.
- Il colore è una media pesata corrente per voxel.

La griglia è **sparsa**: un percorso fatto tocca una piccola frazione del suo bounding box. Le
coordinate dei voxel vengono compresse in una sola chiave a 64 bit (21 bit per asse, fino a
±1.048.575 voxel - a 0,25 m circa ±262 km) e cercate con un array ordinato e una ricerca binaria,
completamente vettorizzate.

### Estrarre la mesh {#extracting-the-mesh}

1. I voxel con peso sotto **0,35** vengono scartati (punti isolati vaganti sui bordi della sagoma
   diventerebbero punte).
2. I pesi vengono scalati dal **75° percentile** dell'intera scansione e limitati a 1.
3. Lo spazio occupato viene tagliato in **blocchi di 64 voxel** per lato, ognuno realizzato con un
   **alone di 3 voxel** dei dati dei vicini (senza di esso, ogni confine tra blocchi si chiuderebbe in
   un muro, e una strada uscirebbe come una fila di scatole).
4. Il campo di ogni blocco viene levigato con una Gaussiana (sigma 0,8 voxel) per rimuovere la
   grinza che lascia il rumore di profondità.
5. **Primo passaggio**: il 99° percentile del campo levigato, campionato su tutti i blocchi (al
   massimo 2 milioni di valori), fissa una sola scala di livello globale. Normalizzare blocco per
   blocco promuoverebbe un valore anomalo isolato a superficie piena nel suo blocco vuoto.
6. **Secondo passaggio**: il campo di ogni blocco diviso per quella scala, marching cubes a **0,5**.
   Un triangolo appartiene al blocco in cui cade il suo **baricentro**, così i triangoli a cavallo di
   una giunzione vengono emessi esattamente una volta.
7. I vertici passano alle unità del mondo nei centri dei voxel; ogni vertice prende il colore del suo
   voxel (grigio medio dove cade fuori da un voxel occupato).

L'estrazione blocco per blocco rende possibile una scansione della dimensione di un circuito: un
array denso su un riquadro di un chilometro quadrato a 0,25 m sarebbe miliardi di celle.
`tests/test_track_scale.py` verifica che funzioni a quella scala con una memoria proporzionale a ciò
che è stato scansionato.

### Suolo e struttura {#ground-and-structure}

`classify` etichetta ogni triangolo in base alla sua normale (orientata dalle normali dei vertici
estratti): entro **35 gradi dritto verso l'alto** è `ground`, tutto il resto `structure`. Il
visualizzatore disegna il suolo pieno e le strutture quasi trasparenti. **L'acqua non viene mai
rivendicata** - non può essere distinta dal suolo piatto dalla forma, e un'etichetta sbagliata
renderebbe un cortile come un lago. Ogni etichetta diventa una parte del `.glb` ([L'output .glb](glb-output.md)).

## Copertura {#coverage}

`CoverageGrid(voxel=0.5)` registra, per cella di mezzo metro, quattro cose che non sono la stessa
cosa:

| Termine | Memorizzato | Punteggio (ognuno limitato a 0..1) | Perché conta separatamente |
|---|---|---|---|
| Quante volte visto | numero di fotogrammi chiave che hanno visto la cella | `conteggio / 3` | una volta è un'ipotesi senza nulla con cui fare la media |
| Da quante direzioni | somma dei vettori di vista unitari | `(1 - dispersione) / (1 - 0,93)`, dove dispersione = lunghezza della somma / conteggio | venti fotogrammi che camminano dritti verso un muro non hanno parallasse tra loro; due viste a trenta gradi di distanza valgono di più |
| Da quanto lontano | distanza di vista minima | `1 - minima / 40 m` | l'errore di profondità cresce più o meno con il quadrato della distanza |
| Quanto bene era posizionata la camera | migliore confidenza della posa | la confidenza | la geometria fusa con una posa dubbia finisce nel posto sbagliato |

I punti di un fotogramma vengono prima raggruppati per cella, così diecimila pixel di un muro contano
come una sola osservazione da una direzione.

**Qualità = il prodotto dei quattro termini**, non la media: sono condizioni che devono valere tutte.
Un posto visto duecento volte da una sola direzione a sessanta metri è osservato male, e una media
lo nasconderebbe dietro un termine eccellente.

Le cifre principali (`summary`): celle occupate, la quota con qualità almeno 0,5 ("% ben visto" nella
finestra), qualità media e volume.

### Punti deboli {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. le celle con qualità sotto 0,35 sono deboli;
2. le celle deboli vengono raggruppate per **connettività** (vicinato 26, union-find solo sulle
   celle occupate - non una raster sul bounding box, che su una guida lunga sono milioni di celle
   vuote);
3. i gruppi di meno di 8 celle vengono ignorati;
4. il motivo di ogni gruppo è il *termine più debole* più comune tra le sue celle, e la sua posizione
   è la media delle sue celle;
5. ordinati dal più grande (poi per qualità peggiore), al massimo 8.

| Motivo | Consiglio mostrato |
|---|---|
| poche viste | Visto solo una o due volte - passaci di nuovo. |
| una direzione | Visto solo da un angolo. Fai un passo di lato e guardalo di nuovo. |
| lontano | Visto solo da lontano. Avvicinati. |
| tracciamento scarso | La camera non era ben localizzata qui. Avvicinati più lentamente. |

La connettività conta: raggruppare per una griglia di blocchi fissa segnalerebbe una stanza laterale
trascurata come tanti anelli separati, e nessuno saprebbe distinguere otto posti da un posto contato
otto volte.

### La vista dall'alto {#the-plan-view}

`top_down(resolution)` proietta le celle su x/z e tiene la **migliore** qualità per colonna (qualcuno in
piedi in una stanza ha una copertura scarsa del soffitto e un'ottima copertura del pavimento; una media
dipingerebbe la stanza di ambra). Le colonne mai osservate sono segnate a parte. La finestra la disegna a
200 x 200, la sovrapposizione a 120 x 120 ([La finestra di scansione](reconstruction-scan-ui.md#the-coverage-map)).

### È ricostruibile? {#is-this-reconstructable}

Ogni 25 fotogrammi fusi, una volta che ci sono almeno 500 celle:

| Risultato | Verdetto | Messaggio (accorciato) |
|---|---|---|
| meno del 2% delle celle ha dispersione di vista sotto 0,93 | non ricostruibile | Quasi nessun parallasse. O la camera non guarda mai di lato, o il tracciamento sta derivando e la stessa superficie non cade mai due volte nello stesso punto. Controlla il numero di fotogrammi posizionati: se è alto, è deriva. |
| distanza minima mediana oltre 25 m | non ricostruibile | Tutto è stato visto da N m o più lontano ... Avvicinati a ciò che vuoi. |
| meno del 6% con buona dispersione | ricostruibile, con avviso | Parallasse scarso - la geometria sarà grezza. Muoversi di lato rispetto a ciò che stai guardando aiuta di più. |

La scarsa parallasse ha due cause che questo non può distinguere, ed è per questo che il messaggio
le nomina entrambe.

## Colore {#colour}

Il colore per voxel della fusione è economico e in diretta, ed è sfocato: ogni pixel di una cella di un
quarto di metro viene mediato, compresi quelli visti di taglio da trenta metri. Quindi all'esportazione
la mesh viene colorata di nuovo, una volta, dai fotogrammi stessi:

- **Fotogrammi tenuti**: fino a **160** fotogrammi chiave (immagine e posa), scelti per campionamento a
  serbatoio così che si distribuiscano su tutta la scansione invece che sulla sua coda.
- **Per vertice** (`project_colours`), ogni fotogramma tenuto contribuisce se il vertice è davanti alla
  camera e dentro l'immagine, la superficie è girata non più di circa 70 gradi rispetto a un'inquadratura
  frontale (`|normale . vista| > 0,34`), è più vicino di **35 m**, e nulla di più vicino gli stava
  davanti (vedi sotto).
- Ogni vista di questo tipo viene valutata `frontalità x (1 - distanza / 35)`, così una vista frontale
  vicina batte una radente lontana. Le **4 viste con punteggio più alto** di ogni vertice vengono tenute -
  qualunque sia l'ordine dei fotogrammi, una vista migliore sostituisce la più debole delle quattro - e
  mescolate, pesate con quello stesso punteggio.
- **Occlusione**: in ogni fotogramma i vertici propri della mesh visibili vengono disegnati in un buffer
  di profondità di celle da 2 pixel, tenendo il più vicino per cella. Un vertice più di `0,3 m + 5%` della
  sua distanza dietro il più vicino della sua cella era nascosto in quel fotogramma - un muro tra la
  camera e la strada oltre - e quella vista non conta nulla. Il test conosce solo la mesh: un ostacolo
  mai fuso (un'auto di passaggio, un montante dell'abitacolo fuori dalla maschera dell'HUD) non viene
  catturato.
- Un vertice che nessun fotogramma ha visto mantiene il colore del voxel; un vertice senza né l'uno né
  l'altro è grigio medio (il nero si leggerebbe come un buco).

Il colore viene scritto come `COLOR_0` per vertice, non come un atlas di texture. L'aspetto predefinito
del visualizzatore è una mappa grigia sotto un calore saturo; il colore serve a trovare la strada su un
circuito scansionato, dove la geometria da sola non la separa dal bordo, e viene mostrato dietro
l'interruttore *Colore acquisito* nel pannello Sfondo / livello del visualizzatore. Un atlas moltiplicherebbe
la dimensione del file e richiederebbe uno svolgitore, per una vista che deliberatamente non è quella
predefinita. Blender e gli altri strumenti glTF leggono `COLOR_0`.
