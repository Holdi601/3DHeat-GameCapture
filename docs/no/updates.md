---
title: Oppdateringer
nav_order: 10
lang: "no"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Oppdateringer {#updates}

3DHeat GameCapture sjekker utgivelsene på GitHub for dette repositoriet når den starter. Den sier fra når
en nyere versjon er ute, og tilbyr å oppdatere. Kode:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Når sjekken kjøres {#when-the-check-runs}

- `python -m heat3d_capture <verb>`: før kommandoen kjøres.
- `python -m heat3d_capture.ui` (og `scan.bat`): før vinduet åpnes.
- `python -m heat3d_update`: på forespørsel, og spør alltid GitHub på nytt.

## Hvordan sjekken fungerer {#how-the-check-works}

- Den installerte versjonen er filen `VERSION` i roten av repositoriet (for eksempel `1.0.1`).
- Den nyeste utgivelsen spørres fra `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  med en tidsgrense på **5 sekunder**. Et tregt nettverk stopper aldri verktøyet i mer enn det.
- Svaret mellomlagres i **6 timer** i
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` uten
  `LOCALAPPDATA`). Hvert 3DHeat-verktøy har sin egen mellomlagringsfil. "Ingen utgivelse ennå" (HTTP 404)
  lagres som et svar, på samme måte som andre svar. Andre feil lagres ikke, og betyr bare at det ikke
  vises noe varsel.
- Versjonene sammenlignes tallmessig (`v1.2.3` eller `1.2.3`). Alt etter `-` eller `+` ignoreres.
- Uten nett, ved hastighetsbegrensning eller bak en proxy fortsetter verktøyet med versjonen det har.

## Når en nyere utgivelse er ute {#what-happens-when-a-newer-release-is-out}

Ved oppstart skriver den dette til feilstrømmen:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Med en terminal å svare i spør den `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betyr ja). Etter en
  vellykket oppdatering **startes den samme kommandoen på nytt**, med den nye koden.
- Uten en terminal å svare i (en pipe, en planlagt kjøring) skriver den
  `Run python -m heat3d_update in <folder> to update.` og fortsetter uendret.

## Hvordan en oppdatering brukes {#how-an-update-is-applied}

Det avhenger av hvordan verktøyene ble installert:

- **En git-klone** (en `.git`-mappe og `git` på PATH): `git pull --ff-only`. Avvises mens kopien har lokale
  endringer i sporede filer. Det er noens arbeid. Commit eller stash dem først.
- **En nedlastet kopi**: kildearkivet til utgivelsen lastes ned, pakkes ut i en midlertidig mappe (oppføringer
  utenfor arkivets egen mappe hoppes over), og **kontrolleres** for at det er versjonen det hevder å være, ut
  fra `VERSION`-filen. Deretter kopieres filene over denne mappen. Innenfor utgivelsens egne Python-pakker
  (`heat3d_*`-mapper øverst i repositoriet, og ett nivå ned for det gamle monorepo-oppsettet) slettes `.py`-
  moduler som utgivelsen ikke lenger har. Dermed kan en utdatert modul ikke skygge for erstatningen.

Dine egne filer (opptak, rundefiler, innstillinger, eksporter, `.venv`) røres aldri. Det skrives bare filer
som er en del av utgivelsen.

## For hånd {#by-hand}

```bash
python -m heat3d_update            # sjekk og oppdater
python -m heat3d_update --check    # si bare om en nyere utgivelse er ute
```

Den skriver `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, eller den
nye versjonen og hva den gjorde. Avslutningskoden er 1 hvis oppdateringen ikke kunne brukes.

## Slå den av {#switching-it-off}

Sett **`HEAT3D_NO_UPDATE=1`** (alle verdier unntatt tom, `0`, `false` og `no`). Det slår av sjekken og
varselet ved oppstart. `python -m heat3d_update` selv sjekker fortsatt når den kjøres for hånd.
