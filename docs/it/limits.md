---
title: Limiti e verifiche
nav_order: 9
lang: "it"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Limiti e cosa è verificato {#limits-and-what-is-verified}

Un elenco onesto: cosa non fanno gli strumenti, e cosa non è stato controllato con un gioco in esecuzione.

## Telemetria {#telemetry}

| Registratore | Stato |
|---|---|
| Forza | Costruito sulla documentazione ufficiale di Data Out; la disposizione viene rilevata dai pacchetti stessi. Il lettore `.tele.gz` di FH Companion nel visualizzatore è stato controllato su giri reali. |
| AC, ACC, AC EVO, AC Rally | Provato su pagine sintetiche costruite dalle disposizioni pubblicate. **Non ancora eseguito contro i giochi veri.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Provato su pacchetti costruiti dalle disposizioni documentate. **Non ancora eseguito contro i giochi veri.** Gli assi, l'assetto e le unità di velocità di RBR non sono documentati e vengono gestiti dai dati. |
| BeamNG.drive | Il registratore è provato su pacchetti costruiti dalla struct della mod. **La mod non è stata eseguita nel gioco.** |
| Trackmania | Il lettore del CSV nel visualizzatore è provato. **Il plugin non è stato eseguito nel gioco.** Si carica solo nella modalità sviluppatore di Openplanet. |
| iRacing | Il lettore `.ibt` del visualizzatore è provato su un file sintetico. |

Altri limiti della telemetria:

- La normalizzazione dello slittamento di Forza non è documentata; lo slittamento di Kunos è scalato su un picco
  tipico dell'asfalto, un'approssimazione.
- Il senso di alcuni assi laterali del telaio dell'auto (Kunos, DiRT) è documentato in entrambi i sensi; la grandezza
  dell'angolo di derapata è affidabile, il suo segno no.
- Nessuno dei giochi rally invia lo slittamento delle gomme; viene derivato nel visualizzatore. RBR non invia le
  velocità delle ruote.
- La superficie di una tappa rally viene scritta solo quando è dato `--surface`; altrimenti il file non ne indica
  nessuna e il visualizzatore la deduce (nome della tappa o dell'evento, poi lo stile di guida, sciolto per impostazione predefinita).
- Il rilevamento dei giri senza un contatore di giri (AC EVO, AC Rally, BeamNG) usa il punto in cui è iniziata la
  registrazione come linea, quindi inizia a registrare sulla linea di partenza.
- Un reset del veicolo in BeamNG chiude il giro aperto in quel momento: viene scritto come corsa parziale quando ha
  coperto la distanza minima (300 m), e scartato altrimenti.
- `route` salva circa ogni 2 secondi mentre si guida; un crash o un processo terminato perde al massimo le posizioni
  dall'ultimo salvataggio.
- Forza Horizon non invia il nome della pista, quindi i file dei giri di Forza hanno `"track": null`; Forza Motorsport
  (2023) invia solo un numero, conservato come `lap.trackOrdinal`.

## Ricostruzione {#reconstruction}

- **La profondità è stimata, non letta.** Il limite dell'intero approccio, e il prezzo di non toccare mai il processo
  del gioco.
- **Il campo visivo è presunto, non misurato.** Troppo stretto e il livello si ricostruisce più profondo di quanto sia.
- **La scala globale** viene da un'altezza della camera presunta (1,15 m nella finestra), oppure dalla telemetria. È
  misurata sul primo fotogramma chiave; quando questo non ha terreno utilizzabile, si provano i fotogrammi chiave
  successivi (fino a 30), e una scala trovata più tardi viene applicata a tutto il livello quando viene scritto. La
  riga "Size:" della finestra dice quale caso si è verificato; se non si trova alcun terreno la scansione resta senza
  unità. La dimensione del voxel è allora nelle unità del primo fotogramma, quindi la sua dimensione in metri differisce
  dall'impostazione. Le ricostruzioni offline sono nelle unità della soluzione.
- **La chiusura dell'anello è disattivata**, e non è un grafo di pose quando la si attiva nel codice; la deriva è
  limitata solo dalla qualità del tracciamento fotogramma per fotogramma.
- **L'aggiustamento a fasci in finestra esiste ma non è collegato**; è collassato su filmati reali.
- **La superficie è un'occupazione pesata, non un TSDF**: le strutture sottili e lo spazio libero vengono peggio di
  come li renderebbe un TSDF.
- **Nessun atlante di texture.** Il colore è per vertice (`COLOR_0`), miscelato dalle 4 viste migliori tra 160
  fotogrammi conservati. Il test di occlusione è grossolano: confronta con i vertici della mesh stessa in un buffer di
  profondità a 2 pixel, quindi un ostacolo che la mesh non contiene (un'auto di passaggio) non viene rilevato.
- **L'acqua non viene mai etichettata**; tutto è terreno o struttura.
- **La risoluzione con modello feed-forward non è in tempo reale**: serve prima la registrazione. La risoluzione
  adattiva delle sezioni difficili non è costruita.
- **Le pose dalla telemetria** collocano la camera sull'auto (l'offset di una camera inseguimento è ignoto). Le
  posizioni sono prese come le invia Forza (Y in alto, come nei file dei giri); i sensi di imbardata, beccheggio e
  rollio sono stati letti dai giri registrati (direzione di marcia, pendenza, quale lato delle sospensioni si
  comprime), non dalla camera del gioco in esecuzione.
- La sovrapposizione non può disegnare sopra lo **schermo intero esclusivo**; usa la modalità finestra senza bordi.
- Le scorciatoie globali, la sovrapposizione che lascia passare i clic e la cattura dal vivo sono **solo per Windows**.
- Chiudere la finestra non chiede di salvare.

## Cosa è misurato {#what-is-measured}

- `tests/test_accuracy.py`: una stanza sintetica con un percorso noto e una profondità analitica - fotogrammi
  collocati, errore del percorso, distanza percorsa, dimensione della stanza, superficie sulle pareti
  ([Ricostruzione del livello](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: una strada di larghezza nota percorsa fuori centro viene ricostruita con la sua
  larghezza.
- `tests/test_track_scale.py`: estrazione della superficie alla scala di un circuito di gara, memoria proporzionale a
  quanto è stato scansionato, blocchi che si uniscono in un'unica superficie.
- `tests/test_glb.py` più i test del visualizzatore: il contratto del `.glb` visto dai due lati.
- Come si comporta la rete di profondità su un gameplay reale non è una domanda a cui può rispondere una scena sintetica,
  e non è misurato dalla suite di test.
