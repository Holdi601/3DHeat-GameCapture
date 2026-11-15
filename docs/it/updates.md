---
title: Aggiornamenti
nav_order: 10
lang: "it"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Aggiornamenti {#updates}

3DHeat GameCapture controlla le release GitHub di questo repository all'avvio, dice quando è uscita una
versione più recente, e propone di aggiornare. Codice:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Quando viene eseguito il controllo {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - prima che il comando venga eseguito.
- `python -m heat3d_capture.ui` (e `scan.bat`) - prima che si apra la finestra.
- `python -m heat3d_update` - su richiesta, chiedendo sempre a GitHub di nuovo.

## Come funziona il controllo {#how-the-check-works}

- La versione installata è il file `VERSION` nella radice del repository (per esempio `1.0.1`).
- La release più recente viene chiesta a `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  con un timeout di **5 secondi**. Una rete lenta non blocca il tool per più di questo.
- La risposta viene memorizzata nella cache per **6 ore** in
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` senza
  `LOCALAPPDATA`). Ogni tool 3DHeat ha il proprio file di cache. "No release yet" (HTTP 404)
  viene memorizzato come una risposta; gli altri errori non vengono memorizzati e significano
  semplicemente nessun avviso.
- Le versioni vengono confrontate numericamente (`v1.2.3` oppure `1.2.3`; tutto ciò che segue `-` o `+`
  viene ignorato).
- Se sei offline, con limite di richieste raggiunto o dietro un proxy, il tool continua con la versione
  che ha.

## Cosa succede quando è uscita una release più recente {#what-happens-when-a-newer-release-is-out}

All'avvio stampa, sul flusso degli errori:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Con un terminale su cui rispondere, chiede `Update now? [Y/n]` (Invio, `y`, `yes`, `j`, `ja` significano
  sì). Dopo un aggiornamento riuscito, **lo stesso comando viene riavviato**, sul nuovo codice.
- Senza un terminale (una pipe, un'esecuzione pianificata), stampa
  `Run python -m heat3d_update in <folder> to update.` e prosegue senza modifiche.

## Come viene applicato un aggiornamento {#how-an-update-is-applied}

Dipende da come sono stati installati i tool:

- **Un clone git** (una cartella `.git` e `git` nel PATH): `git pull --ff-only`. Rifiutato finché la copia
  di lavoro ha modifiche locali a file tracciati - quello è lavoro di qualcuno; committale o mettile da
  parte (stash) prima.
- **Una copia scaricata**: viene scaricato l'archivio sorgente della release, estratto in una cartella
  temporanea (le voci fuori dalla cartella propria dell'archivio vengono saltate), e **verificato che sia
  la versione che dichiara** dal suo file `VERSION`. Poi i suoi file vengono copiati sopra questa cartella.
  Nei pacchetti Python della release (le cartelle `heat3d_*` in cima al repository, e un livello più in
  basso per il vecchio layout monorepo), i moduli `.py` che la release non ha più vengono eliminati, così
  un modulo obsoleto non può fare ombra al suo sostituto.

I tuoi file - registrazioni, file di giro, impostazioni, esportazioni, il `.venv` - non vengono mai toccati:
vengono scritti solo i file che fanno parte della release.

## A mano {#by-hand}

```bash
python -m heat3d_update            # controlla e aggiorna
python -m heat3d_update --check    # dice solo se è uscita una release più recente
```

Stampa `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, oppure la
nuova versione e cosa ha fatto. Codice di uscita 1 se l'aggiornamento non è stato applicato.

## Come disattivarlo {#switching-it-off}

Imposta **`HEAT3D_NO_UPDATE=1`** (qualsiasi valore diverso da vuoto, `0`, `false`, `no`). Questo disattiva il
controllo e l'avviso all'avvio. `python -m heat3d_update` eseguito a mano controlla comunque.
