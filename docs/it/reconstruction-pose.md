---
title: Posa della camera e scala
nav_order: 4
lang: "it"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Posa della camera e scala {#camera-pose-and-scale}

Una mappa di profondità dice quanto sono lontane le cose da *un* punto di vista. Per trasformarne molte
in un solo livello bisogna sapere dove si trovava ogni punto di vista, e in quali unità. Questa pagina
copre i percorsi in diretta; la risoluzione offline feed-forward è nella pagina [Ricostruzione
offline](reconstruction-offline.md).

Codice: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Il modello di camera {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` costruisce una camera stenopeica dal **campo visivo orizzontale**
che imposti nella finestra: `fx = (width / 2) / tan(fov / 2)`, pixel quadrati (`fy = fx`), il punto
principale al centro del fotogramma. Un gioco non pubblica la sua proiezione, quindi questo è l'unico numero
supposto: troppo stretto e la scena sembra più profonda di quanto sia. Il percorso offline usa 65 gradi.

Una `Pose` è memorizzata **mondo-da-camera**: `rotation` (3 x 3) e `translation` = il centro della camera nel
mondo, che è ciò che vogliono la traiettoria, la mappa di copertura e la sovrapposizione.

## Odometria visiva (predefinita) {#visual-odometry-the-default}

`VisualOdometry` segue ogni fotogramma chiave rispetto al precedente:

1. **Caratteristiche**: ORB, fino a 1500 per fotogramma, rilevate solo sulla maschera del mondo (vedi
   [Cattura](reconstruction-capture.md#what-is-not-the-world)).
2. **Corrispondenze** con il fotogramma chiave precedente: forza bruta, distanza di Hamming, controllo
   incrociato (solo coppie reciprocamente migliori).
3. **Sollevamento in 3D**: la profondità del fotogramma precedente è già in unità del mondo, quindi i suoi
   pixel corrispondenti diventano punti del mondo.
4. **Posizionare la camera**: `solvePnPRansac` tra quei punti (errore di riproiezione 3 px, confidenza
   0,999, 200 iterazioni). La traslazione esce nelle stesse unità, quindi **la scala attraversa
   l'intervallo**.
5. **Ancorare la profondità di questo fotogramma**: la sua profondità inversa prevista viene adattata
   (`fit_scale`) contro le profondità degli inlier del PnP, e il ciclo si ripete.

Il **primo fotogramma** è l'origine: posa identità, e la sua affine di profondità è o la calibrazione a
terra qui sotto o, senza di essa, l'identità (la ricostruzione è allora coerente con sé stessa ma senza
unità).

Una posa richiede almeno **18 inlier RANSAC** - chiaramente più del minimo del PnP, che è sei, perché una
soluzione da punti appena sufficienti è esattamente quella che sbaglia con sicurezza.

### Confidenza {#confidence}

Ogni fotogramma posizionato riceve una confidenza in 0..1 che pesa la sua fusione e la sua copertura:

| Posa da | Confidenza |
|---|---|
| telemetria | 1,0 |
| una risoluzione feed-forward | 0,85 |
| tracciamento visivo | `inlier / corrispondenze x min(1, inlier / 60)` |

### Quando il tracciamento si rompe {#when-tracking-breaks}

Un fotogramma che non può essere posizionato viene segnalato, mai indovinato: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Non viene registrata alcuna posa e
nulla viene fuso. Proseguire dall'ultima posa, o iniziare una nuova origine, metterebbe il tratto
successivo di livello a un offset arbitrario - una giuntura che sembra geometria reale.

Dopo una rottura, ogni nuovo fotogramma viene **rilocalizzato** rispetto a un database di fotogrammi chiave
passati (ogni 4° fotogramma tracciato viene aggiunto, fino a 120, eliminando i più vecchi), a partire dal più
recente, con lo stesso passo di corrispondenza e PnP. Finché uno non riesce, i fotogrammi vengono scartati.
Un fotogramma recuperato continua nello stesso sistema di coordinate. Le rilocalizzazioni vengono contate e
mostrate nella finestra (`N recovered`).

### Chiusura del ciclo: disattivata {#loop-closure-off}

Lo stesso database supporta la chiusura del ciclo: confrontare con fotogrammi chiave molto più vecchi per
riconoscere un ritorno e far scattare il tracciato su di esso. **È disattivata per impostazione predefinita, e
lo scanner non la attiva mai** (`Reconstructor(loop_closure=False)`). Su paesaggi ripetitivi - una tappa rally,
un corridoio, una fila di alberi - ogni tratto assomiglia a ogni altro, e la corrispondenza delle caratteristiche
conferma ritorni falsi, che bloccano la camera vicino al punto di partenza mentre continua a guidare. Farla bene
richiede il riconoscimento dei luoghi (un vocabolario a sacchetto di parole o un descrittore appreso) e una
verifica geometrica contro una mappa, che non è stata costruita.

Quando viene attivata dal codice, una chiusura richiede: un fotogramma chiave almeno 60 fotogrammi più vecchio,
entro 6 m dalla posa corrente, abbinato con almeno 90 inlier, che sposti la posa di più di 0,02 m e meno di 6 m.
Anche così sostituisce solo la posa corrente; non è un grafo di pose e non sposta i fotogrammi precedenti né la
geometria già fusa.

## Pose dalla telemetria {#telemetry-poses}

Con **Racing telemetry (Forza) -> Listen for position data** attivo, il percorso della camera arriva dal Data
Out di Forza invece che dalle immagini (`ForzaPoseSource`):

- Un thread ascolta su `127.0.0.1:<porta>` (5300 per impostazione predefinita) con la stessa rilevazione del
  layout dei registratori ([Forza](telemetry-forza.md)); i pacchetti vengono usati mentre `isRaceOn` è attivo.
  Una porta occupata viene segnalata, non sollevata: la telemetria è un miglioramento e la scansione prosegue
  visivamente.
- Ogni pacchetto viene marcato con il **tempo monotono in cui è arrivato** - lo stesso orologio con cui la
  cattura marca i fotogrammi. Il timestamp del gioco conta da qualcosa di non correlato, quindi non viene usato
  per l'allineamento. Un jitter di loopback di uno o due millisecondi equivale a circa 6 cm a 200 km/h.
- Viene mantenuto un buffer mobile di 30 secondi. La posa di un fotogramma è **interpolata** dai campioni ai due
  lati del suo tempo di cattura: la posizione linearmente, la rotazione per interpolazione sferica (una matrice
  mescolata non è una rotazione e distorcerebbe ogni punto). Attraverso un vuoto più lungo di **0,35 s**, o fuori
  dal buffer, non c'è posa.
- `pose_from_forza`: la camera viene posta sull'auto (l'offset di una camera di inseguimento non è pubblicato).
  **Le posizioni vengono mantenute esattamente come le invia il gioco**: il mondo di Forza è già con Y verso
  l'alto (x e z sulla mappa, y l'altezza), che è il modo in cui i file dei giri e dei percorsi li scrivono, quindi
  la superficie cade sulle stesse coordinate dei giri registrati sopra di essa. (Una versione precedente scambiava
  y e z per un mondo "Z verso l'alto" e metteva il tracciato di lato.)
- La rotazione è imbardata, poi beccheggio, poi rollio, con i versi letti dai giri registrati: la direzione di
  marcia `atan2(dx, dz)` è uguale all'imbardata, la salita percorsa è uguale al beccheggio negativo (positivo è
  muso in giù), e il rollio è positivo quando la sospensione destra è compressa (positivo abbassa il lato destro).
  Gli assi dell'auto (x a destra, y verso l'alto, z in avanti) vengono poi convertiti in quelli della camera (x a
  destra, y verso il basso, z in avanti) invertendo y.
- Il mondo di Forza è **sinistrorso** e il sistema della camera non lo è, quindi la matrice mondo-da-camera
  risultante è una riflessione (determinante -1), e la scansione esce sinistrorsa come i file dei giri.
  L'interpolazione non ne risente (la rotazione tra due di queste pose è una rotazione propria).
- Quando un fotogramma non ha una posa dalla telemetria (un vuoto), il ricostruttore ricorre al **tracciamento
  visivo** per quel fotogramma, proseguendo dall'ultima posa della telemetria, e torna alle pose del feed non appena
  questo risponde. Il PnP restituisce solo rotazioni, quindi in un mondo specchiato viene risolto con il mondo
  specchiato attraverso z e lo specchio riportato indietro; il fotogramma atterra nelle coordinate del gioco. Solo se
  anche il tracciamento visivo fallisce il fotogramma è non tracciato.

### Scala della profondità dalla telemetria {#depth-scale-from-telemetry}

Il gioco dice dove si trova la camera, non quanto sono lontane le cose, quindi la profondità di ogni fotogramma va
ancora ancorata - ma non concatenando dal fotogramma zero, la cui unità è arbitraria mentre le pose sono in metri.
Invece, le caratteristiche abbinate tra il fotogramma precedente e quello corrente (almeno 8) vengono **triangolate
direttamente dalle due pose note**, in metri, e la mappa di profondità viene adattata ai punti davanti alla camera.
Ogni fotogramma viene ancorato contro la telemetria, quindi non c'è alcuna catena che possa derivare.

Se le due pose distano meno di **0,05 m** i raggi sono quasi paralleli e la triangolazione è rumore, quindi il
fotogramma resta non ancorato: posizionato esattamente, ma non fuso ("positioned, but its depth has no scale yet").
Per questo la finestra conta separatamente i fotogrammi *posizionati* e quelli *fusi*.

## Scala {#scale}

L'odometria visiva concatena correttamente la scala relativa, ma l'intero livello galleggia ancora su un fattore
sconosciuto. L'output relativo di Depth Anything esce in unità arbitrarie, quindi lasciare il primo fotogramma
all'identità mette il mondo a pochi metri dalla camera a una dimensione arbitraria.

`GroundCalibrator` fissa quel fattore dall'**altezza della camera sopra il suolo**, misurata sul **primo fotogramma
chiave** e, quando questo non ha un suolo utilizzabile, su quelli successivi:

- Altezza della camera: **1,15 m** (la linea degli occhi di un pilota) - la finestra usa sempre questo valore; gli
  script possono passare 1,70 m (`WALKING_HEIGHT`, un giocatore in piedi) oppure `None` (nessuna calibrazione).
- Campione di suolo: righe dal 62% al 92% dall'alto del fotogramma (sotto l'orizzonte, sopra il cofano o l'arma) e
  colonne dal 30% al 70% in larghezza (lontano dai bordi).
- Ogni pixel lì con una previsione utilizzabile viene sollevato con profondità `1 / predicted` nelle unità della rete;
  i punti sotto l'asse ottico danno un'altezza sotto la camera. La loro mediana è l'altezza della camera in unità di
  rete, quindi `metri per unità = 1,15 / mediana`, e l'affine del fotogramma è `scale = 1 / metri_per_unità`, shift 0.
- Considerato affidabile solo con almeno 200 campioni di suolo e una **dispersione** (deviazione assoluta mediana
  diviso la mediana) sotto **0,60**.
- Sul primo fotogramma chiave l'adattamento diventa l'unità dell'origine, quindi la scansione è in metri dall'inizio.
  Quando il primo fotogramma chiave non ha un suolo utilizzabile, la scansione parte senza unità e ogni fotogramma
  chiave successivo tracciato viene provato, fino a **30 fotogrammi** in tutto. Il primo che si calibra dà i *metri per
  unità*: la mediana, sulla fascia del suolo, della profondità che il suo suolo implica divisa per la profondità che la
  catena aveva dato a quel fotogramma. Tutto ciò che è già fuso è nell'unità del primo fotogramma, quindi il fattore non
  viene riportato nella catena; viene applicato a tutto il livello (e ai punti segnati) quando viene scritto, e alla
  distanza mostrata nel frattempo. La dimensione del voxel è quindi nelle unità del primo fotogramma, quindi la sua
  dimensione in metri differisce dall'impostazione per quel fattore.
- Dopo 30 fotogrammi senza suolo la scansione resta senza unità, e lo dichiara.
- Con la telemetria, i fotogrammi chiave successivi non vengono provati: la profondità è ancorata ai metri della
  telemetria.

Stare entro il dieci per cento della dimensione reale è meglio che sbagliare di un fattore mille; la telemetria, dove
disponibile, lo rende superfluo. La nota viene mostrata nella finestra sotto la riga del tracciamento, come `Size: ...`:
`measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera
height, ...` (con `found on frame N, so the level is scaled by F when it is written` quando è arrivato più tardi),
`no usable ground in the first N frames - sizes are relative, not metres`, oppure `in metres, from the telemetry's
positions`.

## Bundle adjustment e tracce lunghe (non collegati) {#bundle-adjustment-and-long-tracks-not-wired-in}

Due componenti esistono per un futuro solutore a finestre e **non sono usati dallo scanner**:

- **`FeatureTracks`** mantiene l'identità delle caratteristiche su centinaia di fotogrammi con il tracciamento
  Lucas-Kanade (600 caratteristiche, riseminate sotto il 60%, tolleranza avanti-indietro di 1 px, nuove caratteristiche
  a 10 px da quelle esistenti), che è ciò di cui ha bisogno il bundle adjustment - la corrispondenza dei descrittori tra
  fotogrammi consecutivi dà solo coppie.
- **`bundle_adjust`** affina una finestra di pose e punti insieme con `scipy.optimize.least_squares` (regione di fiducia,
  perdita soft-L1 con scala di 2 px, un pattern di sparsità esplicito dello Jacobiano, camere fisse ripristinate
  esattamente). Testato contro una verità nota in `tests/test_bundle.py`.

`WindowedOdometry` li combina (finestre di 12 fotogrammi chiave, una soluzione ogni 3 fotogrammi chiave, le prime due
camere fisse, punti con più di 6 px di errore scartati, salti oltre 6 volte il passo recente rifiutati). Il suo docstring
registra che su filmati reali ha **fatto collassare il percorso ed era molto più lento** del tracciamento fotogramma per
fotogramma, con la libertà di gauge (la scala) e un bootstrap basato sulla profondità come cause note e una terza causa
non identificata. Quindi l'odometria fotogramma per fotogramma resta il predefinito; la correzione probabile annotata nel
codice è un bootstrap a due viste con matrice essenziale e la base fissata dalla calibrazione del piano del suolo.
