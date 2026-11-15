---
title: Registratori di telemetria
nav_order: 3
lang: "it"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Registratori di telemetria {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GIOCO] [-o CARTELLA] [--port PORTA]
                                   [--forward HOST:PORTA] [--install]
                                   [--configure CONFIG_JSON] [--surface SUPERFICIE]
```

`telemetry` registra ogni canale che un gioco invia, divide il flusso in giri o tappe e scrive un file JSON
[`heat3d-lap`](lap-format.md) per ogni giro in una cartella. La scheda Analisi di gara del visualizzatore legge questi
file. La registrazione prosegue finché premi **Ctrl+C**; il giro o la tappa aperti in quel momento vengono
scritti se sono abbastanza lunghi da essere conservati (vedi [Come vengono divisi i giri e le tappe](lap-splitting.md)).

Codice: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
e i moduli in [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opzioni {#options}

| Opzione | Predefinito | Significato |
|---|---|---|
| `--game` | `forza` | Uno tra `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Cartella in cui vengono scritti i file dei giri. Viene creata se manca. Ignorata da `trackmania`, il cui plugin scrive i file da sé. |
| `--port` | `5300` | Porta UDP su cui ascoltare. **Per ogni gioco tranne Forza il valore 5300 significa "la porta predefinita del gioco"**: 20777 per `wrc` e i giochi DiRT, 6776 per `rbr`, 4460 per `beamng`. Indica un altro numero per sovrascrivere. Non usata dai giochi Assetto Corsa (memoria condivisa) né da Trackmania (file). |
| `--forward` | nessuno | Solo Forza: `host:porta` a cui inoltrare ogni pacchetto ricevuto, invariato. `127.0.0.1:5301` per FH Companion. Un semplice `:5301` significa `127.0.0.1:5301`. |
| `--install` | disattivato | `beamng`: copia prima la mod del protocollo nelle mod decompresse di BeamNG. `trackmania`: copia il plugin Openplanet nella cartella dei plugin di Openplanet. Ignorata dagli altri giochi. |
| `--configure` | nessuno | Solo `wrc`: percorso del `config.json` della telemetria di EA SPORTS WRC; attiva il pacchetto `wrc` predefinito prima di registrare (prima viene fatto un backup). |
| `--surface` | nessuno | Giochi rally (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` o `mixed`, scritto in `meta.surface` del file del giro. Senza di esso non viene scritta alcuna superficie. |

## I giochi in breve {#the-games-at-a-glance}

| `--game` | Gioco | Sorgente | Porta predefinita | Divisione | `game` nel file | Pagina |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (incl. 2023) | Data Out UDP | 5300 | il contatore di giri del gioco (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, oppure `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | memoria condivisa `acpmf_*` | - | contatore di giri (`CounterSplitter`) | `assetto-corsa` | [Giochi Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | memoria condivisa `acpmf_*` | - | contatore di giri (`CounterSplitter`) | `assetto-corsa-competizione` | [Giochi Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | memoria condivisa `acevo_pmf_*` | - | linea di partenza (`LineSplitter`) | `assetto-corsa-evo` | [Giochi Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | memoria condivisa `acpmf_*` | - | linea di partenza / arresto (`LineSplitter`) | `assetto-corsa-rally` | [Giochi Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struttura `wrc` | 20777 | orologio di tappa (`StageSplitter`) | `ea-sports-wrc` | [Giochi rally](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | orologio di tappa (`StageSplitter`) | `dirt-rally-2` | [Giochi rally](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | orologio di tappa (`StageSplitter`) | `dirt-rally` | [Giochi rally](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | orologio di tappa (`StageSplitter`) | `dirt-4` | [Giochi rally](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | UDP NGP | 6776 | orologio di tappa (`StageSplitter`) | `richard-burns-rally` | [Giochi rally](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod del protocollo `heat3d`, UDP | 4460 | linea di partenza (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanet, file CSV | - | per corsa, nel plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | i suoi file `.ibt`, letti dal visualizzatore | - | il contatore di giri del simulatore | `iracing` | [iRacing](telemetry-iracing.md) |

## Stato {#status}

Il registratore di Forza è quello più usato. I registratori Kunos, rally, BeamNG e Trackmania sono costruiti
sui layout pubblicati e testati su pacchetti sintetici e pagine costruite da quei layout (`tests/test_kunos.py`,
`tests/test_rally.py`, `tests/test_beamng.py`); **nessuno di essi è stato ancora eseguito contro il gioco vero**.
I registratori che possono controllare il proprio input lo fanno man mano che arrivano i pacchetti, e stampano una
`note:` una volta quando qualcosa non corrisponde (EA WRC e DiRT confrontano la velocità nel mondo con la velocità;
EA WRC segnala anche un pacchetto più corto della struttura predefinita di 237 byte). [Giochi](games.md) elenca le
fonti e cosa non è confermato per ogni gioco.

## Durante l'esecuzione {#while-it-runs}

- **Forza** stampa una riga di stato ogni secondo: pacchetti ricevuti, e il numero del giro aperto, il numero di
  campioni e i metri, oppure `waiting for a race`. Ogni giro completato stampa `wrote <file>`.
- **I giochi Assetto Corsa** stampano il nome di ogni file di giro man mano che viene scritto.
- **I giochi rally** stampano `listening for <game> on port <port>`, poi `stage written: <file>`; con Ctrl+C una tappa
  aperta abbastanza lunga da essere conservata viene scritta come `partial stage written: <file>`.
- **BeamNG** stampa `lap written: <file>`, e con Ctrl+C `run written: <file>`.
- **Trackmania** non stampa nulla per corsa: il plugin scrive da sé i suoi file CSV.
- Alla fine ogni registratore stampa quanti file ha scritto.

Una registrazione di Forza, qui alimentata con pacchetti Data Out sintetici di un'auto che guida due giri di un
cerchio di 150 m (i file dei giri, il file grezzo accessorio e il riepilogo di controllo che lascia):

![registrazione di telemetria di due giri da un feed Forza sintetico](../assets/img/telemetry-run.svg)

## Nomi dei file {#file-names}

| Registratore | Schema |
|---|---|
| Forza | `<AAAA-MM-GG_HH-MM-SS>_car<ordinal>_<lap|run><numero>_<secondi>s.lap.json` |
| Giochi Assetto Corsa | `<AAAA-MM-GG_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><numero>_<secondi>s.lap.json` |
| Giochi rally, BeamNG | `<gioco>_<AAAA-MM-GG_HH-MM-SS>_<stage|lap><numero>_<secondi>s[_partial].json`, dove `<gioco>` è il nome lungo (`ea-sports-wrc`, `beamng`, ...), `stage` per il rally e `lap` per BeamNG |
| Plugin Trackmania | `run_<AAAA-MM-GG_HH-MM-SS>[_partial].csv` |

`lap` contro `run` (Forza, Assetto Corsa) e il suffisso `_partial` (rally, BeamNG) indicano se il giro o la tappa
sono stati completati. L'ora nel nome è quando il file è stato scritto, non quando è iniziato il giro.

Accanto ai file dei giri ogni registratore scrive `<AAAA-MM-GG_HH-MM-SS>_<gioco>.raw.parquet` - ogni pacchetto o
pagina arrivato, conservato intero, anche nei menu e tra un giro e l'altro - e
`<AAAA-MM-GG_HH-MM-SS>_<gioco>.summary.json`, il riepilogo di controllo: per tipo di pacchetto quanti ne sono arrivati,
quanti sono entrati nei file dei giri, e `lost`, che è 0. Il visualizzatore li salta quando viene caricata una
cartella. Vedi [Completezza](https://github.com/Holdi601/3DHeat-GameCapture#completeness) nel README.

## Pagine figlie di questa {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Giochi Assetto Corsa](telemetry-assetto-corsa.md)
- [Giochi rally](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Come vengono divisi i giri e le tappe](lap-splitting.md)
- [Slittamento, deriva e canali derivati](slip-and-drift.md)
- [Il file heat3d-lap](lap-format.md)
