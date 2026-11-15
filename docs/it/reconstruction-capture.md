---
title: Cattura, maschere e qualità dei fotogrammi
nav_order: 2
lang: "it"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Cattura, maschere e qualità dei fotogrammi {#capture-masks-and-frame-quality}

Codice: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Da dove vengono i fotogrammi {#where-frames-come-from}

Un bersaglio di sorgente è uno dei seguenti:

| Bersaglio | Sorgente | Note |
|---|---|---|
| `monitor:<n>` | un intero monitor, in diretta | la voce "Whole screen" della finestra, con il numero in "Which" |
| `window:<titolo>` | una sola finestra, in diretta | la voce "A window" della finestra, con il suo titolo |
| un percorso di file | un file video | la voce "A video file" della finestra; qualunque formato che OpenCV sappia leggere |

### Cattura in diretta: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` usa il pacchetto `windows-capture`, che avvolge **Windows Graphics Capture** -
l'API pubblica che usano i registratori di schermo. Non viene iniettato nulla nel gioco. Il
cursore non viene catturato e non viene disegnato nessun bordo giallo di cattura.

La libreria di cattura consegna i fotogrammi a una funzione di richiamata sul thread del
compositore e si aspetta che ritorni subito, quindi la richiamata si limita a copiare il
fotogramma (il buffer viene riutilizzato), a convertire da BGRA a RGB, a ridimensionarlo, a
marcarlo con l'ora e a metterlo in una coda da **4 fotogrammi**. Quando la coda è piena,
viene scartato il **fotogramma più vecchio** e un contatore sale: restare indietro deve
costare fotogrammi, non memoria o correttezza, e la vista in diretta deve mostrare dove si
trova il giocatore adesso. I fotogrammi scartati vengono mostrati nella riga delle statistiche
della finestra, e se più della metà viene scartata compare un suggerimento.

Ogni fotogramma porta `t` (secondi dall'inizio della cattura) e `monotonic` (il valore grezzo
di `time.monotonic()` al momento della cattura), lo stesso orologio con cui sono marcati i
pacchetti di telemetria - ed è ciò che permette di allineare le pose di Forza ai fotogrammi.

`windows-capture` è facoltativo nel controllo delle dipendenze: senza di esso un file video
può comunque essere analizzato.

### File video {#video-files}

`VideoSource` legge con OpenCV, converte in RGB e ridimensiona. Un contenitore senza frequenza
di fotogrammi viene trattato come 30 fps. I tempi sono l'indice del fotogramma diviso per la
frequenza; un file non ha un orario reale, quindi la telemetria non può essere allineata a un
video.

### Risoluzione {#resolution}

I fotogrammi vengono ridimensionati alla sorgente in modo che il lato più lungo sia la
dimensione di cattura del preset (Draft 640, Balanced 960, Detailed 1280 px), con
interpolazione per area. Un fotogramma 4K ha trenta volte i pixel che usa il modello di
profondità.

## Fotogrammi chiave {#keyframes}

Quasi ogni fotogramma di una cattura è ridondante: stare fermi produce centinaia di viste di
una stessa cosa. La ricostruzione vuole il *parallasse*. Quindi un fotogramma viene tenuto in
base a **quanto è cambiata l'immagine dall'ultimo fotogramma tenuto**, non a un timer.

`picture_change(a, b)`:

1. entrambi i fotogrammi vengono portati in scala di grigi e ridotti a una griglia 16 x 16 di
   medie di blocco (le medie di blocco reagiscono al movimento dell'immagine, non alla grana,
   al fogliame, allo sfarfallio o all'HUD);
2. la differenza assoluta media, come frazione di 255;
3. quando una maschera del mondo è nota, ogni blocco viene pesato in base alla quota di esso
   che è mondo e non abitacolo, così un blocco mezzo cruscotto conta per metà (usato quando la
   maschera copre più del 5% del peso della griglia).

La soglia **si adatta alla cattura**: per i primi 30 fotogrammi è il valore iniziale del preset
(0,020 / 0,010 / 0,004), poi è il quantile del preset (0,85 / 0,65 / 0,40) degli ultimi 240
cambiamenti misurati, mai sotto 0,0001. Un fotogramma viene tenuto quando il suo cambiamento
raggiunge la soglia; il primo fotogramma è sempre tenuto. Una soglia fissa non può funzionare
tra scene diverse - il cambiamento da un fotogramma all'altro di un giro in un abitacolo buio è
una piccola frazione di quello di una stanza luminosa e piena di texture - mentre "tieni il
terzo più movimentato" significa la stessa cosa in entrambi i casi. La soglia in uso esce con
ogni aggiornamento di avanzamento (`ScanProgress.threshold`), e le barre della velocità di
camminata nella finestra e nella sovrapposizione misurano l'ultimo cambiamento rispetto ad essa
(`ScanProgress.toward_next_view`).

Solo i fotogrammi tenuti passano dal modello di profondità e dalla ricostruzione. I fotogrammi
non vengono conservati a meno che un chiamante non lo chieda (`keep_frames`); 160 di essi
vengono conservati per colorare la mesh (vedi [colore](reconstruction-fusion-and-texture.md#colour)).

Una scansione finisce quando viene fermata, quando un video finisce, o al limite di tempo o di
fotogrammi chiave.

## Cosa non è il mondo {#what-is-not-the-world}

Due cose in un fotogramma di gioco non sono geometria del livello, e rovinano entrambe una
ricostruzione:

- **L'HUD.** Un mirino è la caratteristica più ripetibile di qualsiasi fotogramma. Un
  corrispondente di caratteristiche lo adora: combacia perfettamente tra ogni coppia di
  fotogrammi, e ogni corrispondenza è una prova che la camera non si è mossa - il che comprime
  l'intera ricostruzione.
- **Le cose fissate alla camera.** Un'arma, un cofano, la struttura dell'abitacolo, un
  cruscotto. Vera geometria nel sistema di coordinate sbagliato: fusa, si sfuma lungo tutto il
  percorso fatto.

Due rilevatori le trovano. Entrambi producono una maschera (255 = mondo, 0 = non mondo) oppure
`None` finché non c'è prova sufficiente; `None` significa sempre "usa tutto", mai "non usare
niente".

La maschera viene applicata:

- al **rilevamento delle caratteristiche** nell'odometria visiva (mascherare un mirino
  nell'output lasciandolo però votare sulla posa risolverebbe il sintomo visibile e lascerebbe
  il danno vero);
- ai **pixel fusi**, così nessuna geometria dell'abitacolo viene fusa;
- alla misura di **nitidezza e luminosità**, perché un abitacolo è sempre perfettamente nitido;
- al **cambiamento dell'immagine** che decide i fotogrammi chiave.

**Non** viene applicata ai fotogrammi dati al solutore VGGT offline (vedi
[Ricostruzione offline](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: ciò che non cambia {#screenmask-what-does-not-change}

Usato dal primo fotogramma chiave finché FlowMask non è pronto.

- Ogni fotogramma viene convertito in grigio, dimezzato e sfocato (Gaussiana 3 x 3) così uno
  spostamento di un pixel di un elemento fisso dell'HUD non sembra movimento.
- La differenza assoluta per pixel rispetto al fotogramma precedente viene integrata in una media
  esponenziale (decadimento 0,9), così la maschera segue un HUD che compare o scompare a metà
  scansione.
- Impara solo dai fotogrammi in cui si sa che la camera si muove (nella scansione: una volta che
  almeno un fotogramma è stato tracciato) - una camera ferma renderebbe tutto statico.
- Dopo **12** fotogrammi di apprendimento un pixel è statico quando la sua variazione media è
  sotto **0,22** della variazione mediana del fotogramma - in modo relativo, così la soglia segue
  la velocità con cui si muove il giocatore.
- Se più del **45%** del fotogramma risulta statico, la premessa è fallita (un menu, una
  sequenza), e non viene mascherato nulla.
- La maschera viene erosa di un pixel (i bordi antialiasati dell'HUD non appartengono a nessuno
  dei due lati) e riportata a piena dimensione.

La sua nota nella finestra: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, oppure `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: ciò che non si sposta mai {#flowmask-what-never-travels}

Un abitacolo non è statico: le lancette si muovono, il contagiri sussulta, la minimappa ruota,
quindi un rilevatore di cambiamenti chiama mondo quei pixel - ed è proprio lì che sono le
caratteristiche peggiori da dare a un solutore di posa. FlowMask pone la domanda migliore: **quali
caratteristiche persistono senza spostarsi?**

- Nella scansione in diretta impara una volta sola, dai primi **40 fotogrammi chiave** (in scala
  di grigi); poi sostituisce ScreenMask per il resto della scansione.
- I fotogrammi vengono tagliati in finestre di **30** fotogrammi, sovrapposte per metà. In ogni
  finestra vengono seminati fino a 800 angoli (`goodFeaturesToTrack`, qualità 0,01, a 8 px di
  distanza) e seguiti con Lucas-Kanade piramidale (21 x 21, 4 livelli) con un **controllo
  avanti-indietro**: una traccia il cui flusso all'indietro non riporta entro 1 px dal punto di
  partenza viene scartata, perché un tracciatore che scivola su uno schema vicino creerebbe
  proprio la firma "persistente ma fermo" che si cerca. Le finestre più corte di 20 fotogrammi
  vengono saltate. Le finestre corte contano: su un percorso lungo quasi ogni caratteristica del
  mondo esce dall'inquadratura e le prove si assottigliano fino a sparire.
- Lo spostamento netto di ogni caratteristica sopravvissuta viene confrontato con **2% della
  larghezza del fotogramma**: sotto, è "ferma"; sopra, "in movimento". I conteggi vengono
  accumulati su una griglia di celle di schermo **24 x 24** a seconda di dove la caratteristica
  è partita.
- Una cella è bloccata quando contiene almeno 2 caratteristiche ferme e più ferme che in
  movimento, **e** almeno 3 delle sue 8 vicine sono bloccate anch'esse (una cella isolata è
  rumore; i filmati scuri ne producono parecchie).
- Vengono tenute solo le regioni bloccate **collegate al bordo del fotogramma**. Tutto ciò che è
  fissato alla camera raggiunge un bordo dello schermo; ciò che sta al centro e non si sposta è
  il punto di fuga - guidando in avanti, la strada dritta davanti non ha flusso ed è la geometria
  più preziosa.
- La regione sopravvissuta viene allargata di una cella (il bordo di un pannello strumenti è un
  gradiente).
- Se più del **60%** del fotogramma verrebbe mascherato, non viene mascherato nulla: di notte la
  maggior parte delle celle non contiene caratteristiche tracciabili, il che si legge come un
  quadrante.

La sua nota: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, oppure, oltre il 60%, un messaggio che spiega che non maschera nulla.

Il percorso offline impara lo stesso FlowMask da 4 serie di 90 fotogrammi consecutivi distribuite
sul video, a 960 x 540 ([Offline](reconstruction-offline.md)).

## Qualità dei fotogrammi e consigli {#frame-quality-and-advice}

`QualityWatcher` giudica ogni fotogramma chiave e sceglie **una** istruzione, così la
sovrapposizione può dire "rallenta" finché si è ancora in tempo.

Per ogni fotogramma misura, solo sui pixel del mondo (tutti i pixel se la maschera lascia meno del
5%):

- **nitidezza**: varianza del Laplaciano - la misura standard in un passaggio, e reagisce
  esattamente a ciò che il movimento sfocato distrugge;
- **luminanza**: livello di grigio medio, 0-255.

La nitidezza non ha una scala assoluta (una tappa notturna e una strada luminosa differiscono di
un ordine di grandezza, entrambe a fuoco), quindi viene giudicata rispetto alla **mediana corrente
di questa cattura**: gli ultimi 90 fotogrammi, con almeno 20 necessari prima di qualunque giudizio.
Ogni fotogramma viene confrontato con la storia *prima* di essere aggiunto, così un lungo tratto
sfocato non può trascinare la mediana fino a raggiungere se stesso.

| Condizione | Test |
|---|---|
| piatto | nitidezza al massimo 1,0 (una schermata di caricamento, un muro, il cielo) |
| buio | luminanza sotto 26 |
| sfocato | nitidezza sotto 0,55 della mediana, e non piatto |

Il consiglio, vince la prima corrispondenza (ordinate da ciò che blocca di più la scansione):

| Situazione | Consiglio | Livello |
|---|---|---|
| meno di 20 fotogrammi | Ci stiamo facendo un'idea dell'immagine… | ok |
| piatto | Niente da misurare - punta la camera sul livello, non sul cielo. | stop |
| buio | Troppo buio per ricostruire. Accendi i fari, o percorri questo tratto di giorno. | stop |
| sfocato | Sfocato - rallenta. | warn |
| meno della metà dei fotogrammi tracciati | Si perde il tracciamento - rallenta e tieni più livello nell'inquadratura. | warn |
| meno del 40% dei fotogrammi tracciati fusi | Le posizioni sono buone ma la profondità non tiene. Guida più vicino al paesaggio. | warn |
| ci sono punti deboli | N punti deboli - la mappa li segna. | ok |
| altrimenti | Buono - continua così. | ok |

Il livello colora il consiglio della sovrapposizione (verde / ambra / rosso). La barra di
**nitidezza** della sovrapposizione è la nitidezza del fotogramma rispetto alla mediana. (Il
codice contiene anche "Blurred, and the camera is not moving. Check the capture." per una camera
ferma; la scansione segnala sempre la camera come in movimento, quindi questo non viene mostrato.)
