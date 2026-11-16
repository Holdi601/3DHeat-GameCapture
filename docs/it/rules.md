---
title: Le regole
nav_order: 2
lang: "it"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Le regole su cui è costruito questo progetto {#the-rules-this-is-built-under}

Ogni parte di 3DHeat GameCapture segue gli stessi vincoli. Sono decisioni di progetto, non
avvertenze, e diversi di essi costano precisione di proposito.

## Niente viene iniettato, niente viene agganciato {#nothing-is-injected-nothing-is-hooked}

Nessuna parte di questo progetto si collega a un processo di gioco, legge la sua memoria o tocca la
sua API grafica.

- I **fotogrammi** arrivano da Windows Graphics Capture, l'API pubblica che usano i registratori
  dello schermo (tramite il pacchetto `windows-capture`), oppure da un file video. Vedi
  [Cattura, maschere e qualità dei fotogrammi](reconstruction-capture.md).
- La **telemetria** arriva solo dalle interfacce che i giochi pubblicano per questo scopo:
  - il feed UDP Data Out di Forza, attivato nelle impostazioni del gioco;
  - le pagine di memoria condivisa con nome che i giochi Kunos pubblicano per le app
    (`Local\acpmf_physics` e simili). Vengono aperte in sola lettura con `mmap`; è il modo
    documentato in cui le app le leggono, non la lettura della memoria del processo di gioco;
  - la telemetria UDP che EA SPORTS WRC, i giochi DiRT e Richard Burns Rally (tramite il plugin
    RSF/NGP) inviano quando è attivata nei propri file di impostazioni;
  - l'interfaccia di protocollo di BeamNG, tramite una piccola mod Lua "protocol" che il file
    `lua/vehicle/protocols.lua` del gioco carica e invia;
  - l'interfaccia del plugin Openplanet di Trackmania, tramite un plugin che legge solo ciò che
    Openplanet espone e scrive file;
  - i file di telemetria `.ibt` del proprio iRacing.

## Perché conta {#why-it-matters}

Il gioco conosce la profondità di ogni pixel esattamente, e un depth buffer agganciato renderebbe la
ricostruzione del livello quasi perfetta e banale. Significherebbe però iniettare codice in processi
che potrebbero essere protetti da anti-cheat, rischiando l'account di chiunque lo esegua. Quindi la
profondità viene *stimata* dall'immagine, e buona parte della pipeline di ricostruzione esiste per
recuperare il più possibile di quella precisione perduta da fonti liberamente utilizzabili: pose dalla
telemetria dove un gioco le pubblica, una scala dal piano del terreno dove non le pubblica, e maschere
che tengono HUD e abitacolo fuori dalla soluzione.

Il depth buffer di ReShade è stato considerato e non usato. ReShade disabilita per progetto l'accesso
alla profondità nelle sessioni multigiocatore, quindi aiuterebbe solo i titoli per giocatore singolo
(vedi [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Cose che il tool modifica sul tuo computer, e solo se richiesto {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Azione | Quando | Cosa esattamente |
|---|---|---|
| Installa pacchetti Python | la prima esecuzione della finestra di scansione, dopo una finestra di dialogo e un sì | `pip install` nell'interprete che esegue il tool - con `scan.bat`, il `.venv` privato accanto ad esso. Mai a livello di sistema di propria iniziativa. |
| Converte il modello di profondità | pulsante "Set up the depth model", dopo una seconda finestra di dialogo per PyTorch e simili | scrive `models/depth-small-518.onnx` |
| Modifica il `config.json` di EA SPORTS WRC | `telemetry --game wrc --configure <file>` | attiva il pacchetto `wrc` / `session_update` verso 127.0.0.1; il file precedente viene conservato come `config.json.bak` |
| Copia la mod di BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` in `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (sostituendo una copia precedente) |
| Copia il plugin di Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` in `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (sostituendo una copia precedente) |
| Registra scorciatoie globali | mentre la finestra di scansione è aperta (Windows) | Ctrl+Alt+F9 / F10 / F11, rilasciate alla chiusura della finestra |
| Aggiorna il tool | dopo aver risposto sì alla richiesta di aggiornamento, oppure eseguendo `python -m heat3d_update` | vedi [Aggiornamenti](updates.md) |

Il file `hardware_settings_config.xml` dei giochi DiRT e il file `RichardBurnsRally.ini` di Richard
Burns Rally **non** vengono modificati dal tool; l'output UDP lo attivi tu a mano (vedi
[Giochi rally](telemetry-rally.md)).

## Cosa viene letto e cosa resta sul tuo computer {#what-is-read-and-what-stays-on-your-machine}

Gli strumenti leggono ciò che il gioco mostra sullo schermo e la telemetria e i file che pubblica a tale scopo, sul tuo computer. Nulla di un gioco viene fornito o ridistribuito: nessuna risorsa del gioco, nessun codice del gioco, nessuna DLL. I file dei giri, le registrazioni, le ricostruzioni e i tracciati esportati restano sul tuo computer; il `.gitignore` del repository tiene registrazioni, file dei giri, mesh, pesi dei modelli e video fuori dal controllo di versione per cartella e per tipo di file.

3DHeat GameCapture non è affiliato ad alcun editore di giochi né approvato da alcuno di essi. I nomi dei giochi e i relativi marchi appartengono ai rispettivi proprietari. Titolari dei diritti: aprite una issue su [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - rispondiamo in fretta e rimuoviamo qualsiasi cosa su richiesta.
