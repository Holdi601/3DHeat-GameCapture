---
title: Opdateringer
nav_order: 10
lang: "da"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Opdateringer {#updates}

3DHeat GameCapture tjekker dette repositorys GitHub-udgivelser, når det starter, siger til, når en nyere
version er ude, og tilbyder at opdatere. Kode:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Hvornår tjekket kører {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - før kommandoen kører.
- `python -m heat3d_capture.ui` (og `scan.bat`) - før vinduet åbner.
- `python -m heat3d_update` - på forespørgsel, og spørger altid GitHub på ny.

## Hvordan tjekket virker {#how-the-check-works}

- Den installerede version er filen `VERSION` i repositoryets rod (for eksempel `1.0.1`).
- Den nyeste udgivelse spørges fra `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  med en timeout på **5 sekunder**. Et langsomt netværk stopper aldrig værktøjet i længere tid.
- Svaret caches i **6 timer** i `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...`
  uden `LOCALAPPDATA`). Hvert 3DHeat-værktøj har sin egen cachefil. "Ingen udgivelse endnu" (HTTP 404) caches
  ligesom et svar; andre fejl caches ikke og betyder blot ingen besked.
- Versioner sammenlignes talmæssigt (`v1.2.3` eller `1.2.3`; alt efter `-` eller `+` ignoreres).
- Offline, ramt af en hastighedsgrænse eller bag en proxy fortsætter værktøjet med den version, det har.

## Hvad der sker, når en nyere udgivelse er ude {#what-happens-when-a-newer-release-is-out}

Ved opstart skrives følgende til fejlstrømmen:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Med en terminal at svare i spørger den `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betyder ja). Efter en
  vellykket opdatering **startes den samme kommando forfra**, på den nye kode.
- Uden en (en pipe, en planlagt kørsel) skriver den
  `Run python -m heat3d_update in <folder> to update.` og fortsætter uændret.

## Hvordan en opdatering anvendes {#how-an-update-is-applied}

Afhænger af, hvordan værktøjerne blev installeret:

- **En git-klon** (en `.git`-mappe og `git` på PATH): `git pull --ff-only`. Afvist, mens checkout'en har lokale
  ændringer i versionsstyrede filer - det er nogens arbejde; commit eller stash dem først.
- **En downloadet kopi**: udgivelsens kildearkiv downloades, udpakkes til en midlertidig mappe (poster uden for
  arkivets egen mappe springes over), og **kontrolleres for at være den version, det påstår** fra sin `VERSION`-fil.
  Derefter kopieres dens filer over denne mappe. Inden for udgivelsens egne Python-pakker (`heat3d_*`-mapper øverst
  i repositoriet, og et niveau ned for det gamle monorepo-layout) slettes `.py`-moduler, udgivelsen ikke længere
  har, så et forældet modul ikke kan skygge for sin afløser.

Dine egne filer - optagelser, lap-filer, indstillinger, eksporter, `.venv` - røres aldrig: der skrives kun
filer, der er en del af udgivelsen.

## Manuelt {#by-hand}

```bash
python -m heat3d_update            # tjek og opdater
python -m heat3d_update --check    # siger kun, om en nyere udgivelse er ude
```

Den skriver `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, eller den nye
version og hvad den gjorde. Afslutningskode 1, hvis opdateringen ikke kunne anvendes.

## Slå den fra {#switching-it-off}

Sæt **`HEAT3D_NO_UPDATE=1`** (enhver værdi undtagen tom, `0`, `false`, `no`). Det slår opstartstjekket og
meddelelsen fra. `python -m heat3d_update` selv tjekker stadig, når den køres manuelt.
