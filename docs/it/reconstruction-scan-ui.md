---
title: La finestra di scansione
nav_order: 1
lang: "it"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# La finestra di scansione {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Codice: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
La finestra è una vista sottile su `scan/session.py` e `scan/reconstruct.py`; non possiede alcuna logica di scansione
o di geometria.

Nota: la finestra di scansione mostra le sue etichette in inglese (non ha una traduzione), quindi le etichette di
controlli, pulsanti e sezioni restano come appaiono nel programma.

## All'avvio {#starting-up}

1. **Controllo degli aggiornamenti** - vedi [Aggiornamenti](updates.md).
2. **Controllo delle dipendenze** - ogni pacchetto che lo scanner richiede viene controllato prima di importare qualunque
   cosa; quelli mancanti vengono elencati con a cosa servono e la dimensione del download, e installati solo dopo
   "Download and install". Cancel esce senza cambiare nulla. Vedi [Esecuzione e dipendenze](runtime.md#first-run-preflight).
3. **Finestra** - "3DHeat — Level scanner", 1420 x 900, stile Fusion di Qt.
4. **Controllo dell'hardware** - viene scelto il backend di inferenza migliore, il modello di profondità viene caricato e la
   sua velocità viene misurata su 6 fotogrammi; il riquadro del verdetto in alto a sinistra dice com'è probabile che sia la
   scansione (vedi [Esecuzione](runtime.md#what-to-expect-from-this-machine)).
5. **Le scorciatoie globali** vengono registrate per ultime.

### Quando non c'è ancora un modello di profondità {#when-there-is-no-depth-model-yet}

Se `models/` non contiene alcun `depth-*.onnx`, il verdetto dice **"One more thing to set up."**, Start è disattivato e
compare un pulsante **Set up the depth model**. Esso:

- controlla PyTorch, `transformers` e `onnxscript` (circa 945 MB in tutto), e chiede prima di installarli;
- esegue `tools/export_onnx.py --size small` come processo separato (così PyTorch non resta mai nella memoria dello
  scanner), con un limite di 30 minuti. La finestra non risponde mentre gira;
- in caso di successo ripete il controllo dell'hardware; in caso di errore mostra gli ultimi 600 caratteri dell'output del
  convertitore.

Quando sono presenti più modelli, la scelta avviene **per licenza, non per nome del file**: `depth-small-*` (Apache-2.0, uso
commerciale permesso) ogni volta che ce n'è uno, poi Base, poi Large (entrambi non commerciali). Il riquadro del verdetto e la
riga grigia sotto i pulsanti indicano il file in uso, la sua licenza e gli altri file di modello presenti e non usati - per
esempio `Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Per scansionare con Base, sposta il file Small fuori da `models/`.

## Colonna sinistra: impostazioni {#left-column-settings}

| Gruppo | Controllo | Predefinito | Intervallo / valori | Cosa fa |
|---|---|---|---|---|
| (in alto) | Verdict box | "Checking your graphics card…" | colorato verde, ambra o rosso secondo il livello | Titolo, `<device> via <API> — N views per second`, una nota, e `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Da dove vengono i fotogrammi |
| | Which | `1` | numero del monitor / titolo della finestra / percorso di un video | `monitor:<n>`, `window:<title>`, oppure un percorso di file |
| | Choose file… | visibile per il video | `*.mp4 *.mkv *.avi *.mov` | Riempie il percorso |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Risoluzione di cattura e quanto è selettiva la scelta dei fotogrammi chiave (sotto); un riepilogo di una riga è mostrato sotto |
| | Game field of view | 90° | 30-140° | Il campo visivo **orizzontale** del gioco. Troppo stretto e il livello si ricostruisce più profondo di quanto sia; troppo largo e lo appiattisce. I giochi di corsa sono più vicini a 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, passo 0.05 | Dimensione del voxel della superficie. Più piccolo è più fine e più pesante |
| Stop after | Time | no limit | 0-120 min | Termina la scansione dopo questo tempo (0 = nessun limite) |
| | Views kept | 3000 | 0-100.000 | Termina la scansione dopo questo numero di fotogrammi chiave, come protezione della memoria (0 = nessun limite) |
| What to ignore | Ignore HUD and anything on the camera | on | | Impara e maschera la HUD, il mirino, l'arma, il cofano, l'abitacolo ([Cattura](reconstruction-capture.md#what-is-not-the-world)). La riga sotto dice cosa decide attualmente il rilevatore |
| While you play | Show feedback over the game | on | | Apre la sovrapposizione che lascia passare i clic durante la scansione. Il suggerimento sotto: esegui il gioco in **finestra senza bordi**; lo schermo intero esclusivo non può essere disegnato sopra da nulla |
| Racing telemetry (Forza) | Listen for position data | off | | Prende il percorso della camera da Data Out di Forza invece di stimarlo ([Posa](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | La porta di Data Out |
| | (status line) | | | `N packets — poses come from the game, not from the picture`, oppure `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Avvia o ferma; mostra la scorciatoia quando è stata registrata |
| | **Set up the depth model** | hidden | | Vedi sopra |
| | **Save level…** | disabled | | Attivo dopo una scansione che ha prodotto voxel di superficie; chiede un nome di file (predefinito `scan.glb`) |
| | (grey line) | | | `Model: <file> (<licence>) · Available: <backends>`, più note di configurazione come l'installazione di `onnxruntime-gpu` |

### I preset {#the-presets}

| Preset | Lato più lungo della cattura | Quantile di conservazione | Soglia iniziale | Riepilogo mostrato |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Veloce e grossolano. Utile per controllare un percorso prima di una scansione vera. |
| Balanced | 960 px | 0.65 | 0.010 | La scelta abituale. Cammina a passo normale. |
| Detailed | 1280 px | 0.40 | 0.004 | Lento e accurato. Cammina con decisione e gira con dolcezza. |

Il quantile di conservazione significa "conserva un fotogramma quando è cambiato più di questo quantile delle variazioni
degli ultimi 240 fotogrammi" - Draft conserva circa il 15% più movimentato, Detailed il 60% più movimentato. Vedi
[Fotogrammi chiave](reconstruction-capture.md#keyframes).

### Impostazioni fisse nella finestra {#settings-that-are-fixed-in-the-window}

La finestra ricostruisce sempre durante la scansione, usa un'altezza della camera di **1,15 m** per la scala del piano del
terreno (il valore a piedi, 1,70 m, non è selezionabile), e lascia che la scala dei backend scelga la GPU. Sono campi di
`ScanSettings` (`camera_height`, `prefer_backend`) che solo uno script può cambiare.

## Colonna destra: cosa sta facendo la scansione {#right-column-what-the-scan-is-doing}

| Elemento | Mostra |
|---|---|
| **What the camera sees** | l'ultimo fotogramma chiave |
| **Shape it is reading** | la sua profondità prevista, colorata con la mappa di colori Turbo, normalizzata tra il 2° e il 98° percentile di quel fotogramma (così un solo pixel di cielo non appiattisce l'intervallo) |
| **Coverage — where you have been, and how well** | una vista in pianta (vedi sotto) |
| **Worth another look** | i punti deboli, numerati in corrispondenza dei cerchi sulla mappa, ciascuno con un'istruzione; il peggiore (il più grande) per primo, al massimo 8; poi i punti che hai segnato (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Walk-speed bar | `walk speed — N% of the way to the next view`: la variazione dell'immagine dell'ultimo fotogramma divisa per la **soglia in uso** - il valore iniziale del preset per i primi 30 fotogrammi, quello adattato dopo ([Fotogrammi chiave](reconstruction-capture.md#keyframes)) |
| Health line | stato del tracciamento, o un avviso di cattura (sotto) |
| Size line | `Size: ...`, come è stata fissata la scala del livello o perché non lo è stata ([Scala](reconstruction-pose.md#scale)) |
| Statistics line | `views  frames  dropped  depth-per-second  seconds`, e durante la ricostruzione `placed  cells  % well seen  metres`, più `recovered` e `loops closed` quando uno dei due non è zero |
| Hotkey line | le scorciatoie registrate, o perché non è stato possibile registrarle |
| Hint line (ambra) | consigli in tempo reale (sotto), il messaggio finale della scansione, e i segni |

### La mappa di copertura {#the-coverage-map}

Ridisegnata ogni 900 ms su un thread di sfondo (mai sul thread dell'interfaccia), su 200 x 200 celle scalate a 420 px:

- ogni colonna della griglia di copertura prende la **migliore** qualità di osservazione al suo interno (così un pavimento
  ben visto non viene dipinto di ambra da un soffitto visto male sopra di esso);
- la scala va dal rosso (cattivo) all'ambra (sottile) al giallo (accettabile) al verde (buono);
- le celle mai osservate sono di un grigio scuro distinto, così un angolo inesplorato non sembra un angolo scansionato male;
- il percorso fatto è disegnato come una linea chiara sottile, la posizione attuale come un punto bianco;
- i punti deboli sono cerchi bianchi con il loro numero;
- i punti che hai segnato sono quadrati ambra etichettati `M1`, `M2`, ….

Come sono calcolati qualità e punti deboli: [Fusione, copertura e colore](reconstruction-fusion-and-texture.md#coverage).

### La riga di stato del tracciamento {#the-health-line}

| Salute del tracciamento (fotogrammi collocati / fotogrammi) | Testo | Colore |
|---|---|---|
| nessun fotogramma ancora | Waiting for the first frame. | grigio |
| 90% o più | Tracking well — N of M frames placed. (Tracciamento buono.) | verde |
| 60% o più | Tracking is patchy — N of M frames could not be placed. Turn more slowly. (Tracciamento a tratti: gira più lentamente.) | ambra |
| sotto il 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. (Stai perdendo il tracciamento: muoviti lentamente ed evita muri vuoti e cielo.) | rosso |

Un avviso di cattura dalla griglia di copertura sostituisce questa riga (rosso quando la scansione è giudicata non
ricostruibile, ambra altrimenti): quasi nessuna parallasse, tutto visto da più di 25 m, oppure parallasse sottile. Vedi
[Copertura](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### La riga dei suggerimenti {#the-hint-line}

| Condizione | Suggerimento |
|---|---|
| più della metà dei fotogrammi scartati, dopo 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. (Sei indietro: prova la qualità Draft, o un dettaglio di superficie più grossolano.) |
| meno di 0,3 viste conservate al secondo, dopo 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. (Si conserva pochissimo: muoviti di lato invece di girare sul posto.) |
| più di 8 viste conservate al secondo, dopo 8 s | Keeping a lot. Slow down a little for cleaner geometry. (Ne conservi molte: rallenta un po' per una geometria più pulita.) |
| scansione terminata | il messaggio della sessione: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, oppure `failed: <error>` |

## Scorciatoie {#hotkeys}

Registrate con Windows (`RegisterHotKey`), quindi funzionano mentre il gioco ha il focus. Uscire con Alt-Tab da un gioco a
schermo intero è esattamente ciò che rovina una cattura.

| Tasti | Azione |
|---|---|
| **Ctrl+Alt+F9** | Avvia / ferma la scansione |
| **Ctrl+Alt+F10** | Segna questo punto da rivedere (durante la scansione) |
| **Ctrl+Alt+F11** | Mostra / nascondi la sovrapposizione (commuta la casella "Show feedback over the game") |

- Sono registrate una volta, all'apertura della finestra, e rilasciate alla chiusura; finché sono registrate, queste
  combinazioni di tasti sono sottratte a ogni altro programma, compreso il gioco. I tasti F con due modificatori sono stati
  scelti perché i giochi raramente li associano.
- La ripetizione automatica è soppressa (`MOD_NOREPEAT`), così tenere premuto un tasto non attiva o disattiva la scansione
  decine di volte.
- Un tasto che un altro programma tiene già viene segnalato (`... unavailable: another program already has this key`) e gli
  altri continuano a funzionare. Un pulsante annuncia una scorciatoia solo se è stata davvero registrata.
- I tasti sono fissi nel codice (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); il parser accetta F1-F12 con `ctrl`, `alt`
  e `shift`. Fuori da Windows non ci sono scorciatoie globali e la finestra lo dice.
- **Mark** registra la posizione attuale della camera (quella dell'ultimo fotogramma collocato) e mostra "Marked MN. Marked
  spots are on the map and saved with the level." Prima che un fotogramma sia stato collocato dice che non c'è nessun posto
  dove segnare. I punti segnati sono disegnati sulla mappa della finestra e su quella della sovrapposizione come quadrati
  ambra etichettati `M1`, `M2`, …, elencati sotto i punti deboli, contati nella riga statistiche della sovrapposizione, e
  salvati con il livello (sotto).

## La sovrapposizione {#the-overlay}

Un piccolo pannello fissato sopra il gioco, così il feedback è dove gli occhi sono già.

- Senza bordi, sempre in primo piano, una finestra di strumenti (non nella barra delle applicazioni né in Alt-Tab), trasparente
  agli input in Qt e resa attraversabile dai clic in Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), così un clic destinato al
  gioco non viene mai inghiottito. Mostrata senza prendere il focus.
- Angolo in alto a destra dello schermo principale, a 18 px dai bordi; 214 x 358 px.
- Si apre quando una scansione inizia (se "Show feedback over the game" è attivo), si chiude quando si ferma.
- **Richiede la modalità finestra senza bordi**: nulla può essere disegnato sopra lo schermo intero esclusivo - né questo, né
  l'overlay di Steam, né quello di Discord.

Dall'alto in basso mostra:

| Elemento | Contenuto |
|---|---|
| Coverage map | 190 px, la stessa mappa della finestra a 120 x 120 più grossolana, con il percorso, gli anelli dei punti deboli e i punti segnati |
| Health | lo stesso testo e colore della riga della finestra |
| Stats | `N placed · M to revisit · X m`, con `· K marked` quando ce ne sono |
| **movement** bar | la stessa della Walk-speed bar della finestra: la variazione dell'ultimo fotogramma sulla soglia in uso, piena quando il prossimo fotogramma sarà conservato |
| **sharpness** bar | nitidezza relativa alla mediana di questa stessa cattura: verde da 0,75, ambra da 0,45, rosso sotto |
| Advice | un'istruzione, verde / ambra / rosso (in grassetto quando non è "ok") - vedi [qualità del fotogramma](reconstruction-capture.md#frame-quality-and-advice) |
| Hotkeys | i tasti registrati |

Se l'aggiornamento della sovrapposizione genera mai un errore, passa a un pannello rosso **"Feedback stopped"** che dice che
tutto ciò che era mostrato prima è superato, che la scansione è ancora in corso e la finestra principale è ancora corretta,
con l'errore e un conteggio. Un pannello congelato mentre era verde verrebbe altrimenti letto come una conferma.

## Salvataggio {#saving}

**Save level…** scrive la ricostruzione come `.glb` (vedi [L'output .glb](glb-output.md)). Se il volume non produce alcuna
superficie, "Nothing to save" spiega che il tracciamento è probabilmente andato perso per gran parte della scansione. In caso
di successo: "Written to <path> ... Load it in 3DHeat through the Level panel.", indicando anche il file dei segni quando ci
sono punti segnati.

I punti segnati sono scritti accanto al livello come **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` è nelle coordinate proprie del livello (con la scala del GLB applicata, così un segno sta sulla mesh sulla quale è
stato fatto), `metres` in metri; `number` corrisponde a `M1`, `M2`, … nella finestra. Quando la scala è stata trovata su un
fotogramma chiave successivo ([Scala](reconstruction-pose.md#scale)), entrambi includono quel fattore.

Fermare una scansione conserva ciò che è stato raccolto; un nuovo **Start** scarta la scansione precedente.
**Chiudere la finestra non chiede di salvare**: ferma la scansione, rilascia le scorciatoie e chiude la sovrapposizione.
