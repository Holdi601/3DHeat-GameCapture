---
title: Riferimento dei comandi
nav_order: 5
lang: "it"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Riferimento dei comandi {#command-reference}

Tutti i comandi si eseguono dalla cartella del repository, con l'ambiente del progetto:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Comando | Cosa fa |
|---|---|
| [`route`](#route) | Registra solo le posizioni di un giro di Forza, per trovare la mappa nei file del gioco |
| [`telemetry`](#telemetry) | Registra ogni canale, un file di giro per giro, per la scheda Analisi di gara |
| [`laps`](#laps) | Legge una libreria di giri di FH Companion e scrive percorso e campioni di un circuito |
| [`reconstruct`](#reconstruct) | Risolve una registrazione offline e scrive un `.glb` |
| [`hud`](#hud) | Legge dalla registrazione le azioni del giocatore, le morti e il percorso sulla minimappa, e il feed delle uccisioni |
| [`locate`](#locate) | Dove è stato ripreso ogni fotogramma di una registrazione, rispetto ai render del livello |
| [`python -m heat3d_capture.ui`](#the-scan-window) | La finestra di scansione |
| [`python -m heat3d_update`](#updates) | Controlla e applica un aggiornamento |
| [`python tools/export_onnx.py`](#the-model-converter) | Converte il modello di profondità in ONNX |

Se avviato come `python -m heat3d_capture`, lo strumento controlla prima se c'è una release più recente (vedi
[Aggiornamenti](updates.md); `HEAT3D_NO_UPDATE=1` lo disattiva). `--help` dopo un comando elenca le sue opzioni:

![heat3d_capture --help](../assets/img/cli-help.svg)

Codice: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Resta in ascolto dei dati Forza Data Out e tiene solo le posizioni dell'auto, nient'altro: niente modello di
profondità, niente GPU, niente cattura. Codice: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opzione | Default | Significato |
|---|---|---|
| `-o`, `--out` | obbligatoria | Percorso di output; il suo suffisso viene sostituito, quindi `-o lap` scrive `lap.npz` e `lap.json`. |
| `--port` | `5300` | Porta a cui il gioco invia i dati (in ascolto su 127.0.0.1). |
| `--seconds` | `0` | Si ferma dopo questi secondi; `0` continua fino a Ctrl+C. |

Una posizione viene tenuta solo mentre il gioco segnala una gara (`isRaceOn`), l'auto va più veloce di 0,5 m/s,
e dista almeno 0,5 m dall'ultima posizione tenuta. Altrimenti, fermi in un menu a 60 pacchetti al secondo,
il file si riempirebbe della linea di partenza. Il tempo di ogni campione è il tempo di gara del gioco, o
l'orologio di sistema quando quello è 0. La disposizione viene rilevata come per `telemetry` (l'auto deve
prima muoversi; vedi [Forza](telemetry-forza.md)).

Ogni secondo stampa i pacchetti ricevuti, le posizioni tenute e la posizione attuale, oppure
`nothing on port 5300 yet - is Data Out on?` (nessun dato sulla porta 5300 per ora - Data Out è attivo?). Il
percorso viene **salvato mentre si guida**: ogni 2 secondi dopo l'arrivo di una nuova posizione (l'intervallo
cresce fino a venti volte il tempo dell'ultimo salvataggio, così una sessione molto lunga non spende mai più di
un ventesimo del suo tempo a scrivere), e ancora una volta quando il registratore si ferma per qualsiasi motivo -
Ctrl+C, `--seconds` o un'eccezione. Ogni salvataggio scrive `lap.npz.partial` / `lap.json.partial` e poi lo
sposta sul file vero, così i file su disco sono sempre completi; un crash o un processo terminato perde al
massimo gli ultimi secondi. Se non è stato tenuto nulla, stampa come attivare Data Out ed esce con codice 1.

Output:

- `lap.npz` - array NumPy `positions` (n x 3, metri), `times`, `speeds` (m/s);
- `lap.json` - leggibile senza questo progetto:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Le posizioni sono le coordinate mondo del gioco stesso, ed è questo che le rende un punto di riferimento per
trovare lo stesso terreno nei file del gioco: il comando `course` di
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) legge questo JSON ed esporta il circuito
percorso dal giro.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Ogni opzione e ogni gioco sono descritti in [Registratori di telemetria](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Legge la libreria dei giri che FH Companion conserva e scrive due file per un circuito: un percorso che indica
quale pezzo di mappa ritagliare dall'archivio del gioco, e una tabella con ogni campione di ogni giro. Vengono
scritti insieme, così non possono non corrispondere. Codice:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opzione | Default | Significato |
|---|---|---|
| `course` | nessuno | Nome del circuito, cercato in modo approssimativo. Ometterlo per elencare la libreria. |
| `-o`, `--out` | il nome del circuito, in minuscolo, con gli spazi sostituiti da `_` | Percorso di output; `.json` e `.csv` vengono scritti uno accanto all'altro. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Dove si trovano le cartelle dei circuiti. |
| `--margin` | `80` | Metri aggiunti attorno all'estensione del circuito in x e z nei `bounds` del percorso. |

### Elenco {#listing}

Senza circuito stampa il numero di cartelle dei circuiti e, per ciascuna, il numero di file dei giri (`*.json`
in qualunque punto sotto di essa, tranne `course.json`) e il nome del circuito, poi la riga
`Name one to write it out:  -o <file> <course>`.

### Trovare un circuito {#finding-a-course}

Le cartelle dei circuiti si chiamano `<nome> (course_<x>_<z>_to_<x>_<z>)` - partenza e arrivo, arrotondati. Un
circuito viene trovato, in quest'ordine, con: il nome esatto della cartella; la parte del nome della cartella,
senza distinguere maiuscole e minuscole; una cartella unica il cui nome contiene il testo. Più corrispondenze
danno un errore che le elenca.

### Lettura {#reading-it}

- `course.json` nella cartella, quando è leggibile, fornisce il nome e partenza e arrivo non arrotondati
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); altrimenti questi vengono dal nome della cartella. Un
  circuito è indicato come anello quando partenza e arrivo distano meno di 10 m.
- Ogni altro `*.json` sotto la cartella è un giro (i giri stanno più in profondità - per classe, auto,
  taratura, etichetta - e la ricerca è semplicemente ricorsiva). I file vengono letti come UTF-8 con byte order
  mark. Un giro illeggibile viene saltato. I giri sono ordinati per ora di registrazione.
- Per giro: `Lap.samples` (ciascuno con `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`, `LongG`,
  `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), e la classe dell'auto, l'ordinale, l'indice di
  prestazione, i secondi del giro, la lunghezza, l'ora di registrazione e la partenza da fermo.

Stampa un riepilogo (giri, campioni, giro migliore e la sua classe, l'estensione x/y/z).

### Output {#output}

**`<out>.json`** - la stessa forma di percorso scritta da `route`, così l'estrattore della mappa accetta
entrambi: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (allargati di `--margin` in x e z), e
`positions` del giro **più veloce** (una sola linea invece di una macchia di tutti i giri).

**`<out>.csv`** - ogni campione di ogni giro, una riga per campione:

| Colonna | Significato |
|---|---|
| `course` | nome del circuito |
| `lap` | un'etichetta per giro: data e ora di registrazione fino al minuto, e il tempo del giro |
| `car` | ordinale dell'auto |
| `car_class` | lettera della classe di prestazione |
| `pi` | indice di prestazione |
| `lap_seconds` | il tempo del giro |
| `speed_kmh` | velocità in km/h |
| `x`, `y`, `z` | posizione nel mondo, metri, 3 decimali |
| `speed_ms` | velocità, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | così come li registra FH Companion |
| `metres` | distanza lungo il giro, 3 decimali |
| `elapsed` | secondi dall'inizio del giro stesso, 3 decimali |

I valori che non sono posizioni vengono scritti con 4 cifre significative; le posizioni hanno decimali fissi,
perché 4 cifre significative farebbero scattare un circuito su una griglia di un metro. I nomi delle colonne
sono scelti perché il visualizzatore mappi il file senza istruzioni: `lap` diventa la sessione (due giri della
stessa auto non si uniscono mai), `car` la cosa che si muove, `car_class` il gruppo da colorare, `elapsed` l'asse
del tempo (ogni giro si allinea al proprio inizio).

Infine stampa un suggerimento per ritagliare la mappa dal gioco con GameFiles, con il file del percorso o un
riquadro esplicito.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Ricostruisce una registrazione offline, con il percorso della camera risolto tutto insieme da VGGT. Lento:
minuti per finestra su una GPU da desktop. Servono PyTorch, Hugging Face `transformers` e il pacchetto `vggt`,
che lo scanner non richiede: sono elencati in `requirements-offline.txt`, e il comando li controlla dopo aver
stampato la riga della licenza e offre di installare quelli mancanti (codice di uscita 1 se si rifiuta).
Descrizione completa: [Ricostruzione offline](reconstruction-offline.md).

| Opzione | Default | Significato |
|---|---|---|
| `video` | obbligatorio | La registrazione. Codice di uscita 2 se non esiste. |
| `-o`, `--out` | obbligatorio | Il `.glb` da scrivere. |
| `--solve-budget` | `260` | Il massimo di fotogrammi dati al risolutore. Sono distanziati in base a quanto si sposta l'immagine, non in base all'orologio. Di più è più preciso e molto più lento. Oltre 400 fotogrammi pianificati viene rifiutato. |
| `--fuse-interval` | `0.4` | Secondi tra i fotogrammi fusi in geometria. |
| `--model` | `vggt-1b` | Quali pesi VGGT usare per risolvere: `vggt-1b` (`facebook/VGGT-1B`, non commerciale) o `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, con accesso riservato: serve l'accesso concesso da Meta). La riga di licenza stampata per prima è quella di quel modello. |

Stampa per prima la riga di licenza del modello, poi ogni fase (`masking`, `planning`, `solving`, `fusing`,
`exporting`) con i secondi trascorsi e l'avanzamento, e infine un riepilogo: camere risolte, errore di chiusura,
giunzione peggiore, note e il file scritto. Il codice di uscita è 0 solo se un file è stato scritto.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Legge la HUD del gioco dalla registrazione del giocatore, dopo la partita: le azioni del giocatore stesso dal
popup dei punti, le morti e le rianimazioni dalle schermate di caduta e di schieramento, il percorso sulla
minimappa e il feed delle uccisioni. Scrive `<out>.parquet` (percorso ed eventi, una tabella 3DHeat),
`<out>.events.jsonl`, `<out>.summary.json`, e `<out>.map.png` + `.map.json` (il mosaico della minimappa e i suoi
ancoraggi, per l'immagine della mappa del visualizzatore). Battlefield 6 (`bf6`) è per ora l'unico profilo.

Servono **ffmpeg e ffprobe** nel `PATH` (`winget install Gyan.FFmpeg`, poi un nuovo terminale).

| Opzione | Default | Significato |
|---|---|---|
| `video` | obbligatorio | La registrazione. |
| `-o`, `--out` | il nome del video | Percorso di output senza estensione. |
| `--game` | `bf6` | Di quale HUD leggere. |
| `--player` | indovinato | Il nome del giocatore come lo mostra il feed delle uccisioni, cercato in modo approssimativo. |
| `--fps` | `5` | Campioni della minimappa al secondo. |
| `--start`, `--seconds` | tutto il video | La parte della registrazione da leggere. |
| `--metres-per-pixel` | nessuno | La scala della minimappa, se nota; senza, le posizioni sono in pixel della minimappa. |
| `--cpu` | disattivo | Decodifica sulla CPU anche quando c'è una scheda NVIDIA. |

Descrizione completa: [Leggere la HUD da una registrazione](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderizza un livello da ogni punto in cui un giocatore può stare, e indicizza i render; `frames`
colloca ogni fotogramma campionato di una registrazione sul livello, a partire dall'immagine, con il percorso
sulla minimappa del comando `hud` come riserva; `eval` confronta un risultato con pose note della camera;
`train` addestra un modello dei punti per mappa sui render del livello (e sui fotogrammi che una run ha già
localizzato), per `build --head`; `refmap` colloca la mappa del gioco (la sua schermata di schieramento) sul
livello, e `minimap` legge la minimappa di una registrazione rispetto ad essa, fotogramma per fotogramma - ciò
che `frames --minimap` può usare come punto di partenza. Servono PyTorch e `requirements-locate.txt`.
**Sperimentale:** su registrazioni reali, per ora colloca solo una piccola parte dei fotogrammi. Ogni opzione,
gli output e il metodo: [Localizzare i fotogrammi in un livello](locate.md); l'elenco completo delle opzioni:
[Riferimento dei comandi](../cli-reference.md).

## La finestra di scansione {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

oppure fai doppio clic su `scan.bat`. Nessuna opzione. Vedi [La finestra di scansione](reconstruction-scan-ui.md).

## Aggiornamenti {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Vedi [Aggiornamenti](updates.md).

## Il convertitore del modello {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Converte un checkpoint di Depth Anything V2 nel file ONNX che esegue lo scanner. Servono PyTorch,
`transformers` e `onnxscript`. Vedi [Profondità](reconstruction-depth.md#building-the-model).
