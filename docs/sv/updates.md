---
title: Uppdateringar
nav_order: 10
lang: "sv"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Uppdateringar {#updates}

3DHeat GameCapture kontrollerar det här förrådets GitHub-releaser när det startar, säger till när en
nyare version finns, och erbjuder att uppdatera. Kod:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## När kontrollen körs {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - innan kommandot körs.
- `python -m heat3d_capture.ui` (och `scan.bat`) - innan fönstret öppnas.
- `python -m heat3d_update` - på begäran, och frågar alltid GitHub på nytt.

## Hur kontrollen fungerar {#how-the-check-works}

- Den installerade versionen är filen `VERSION` i förrådets rot (till exempel `1.0.1`).
- Den senaste releasen frågas från `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  med en **5-sekunders** timeout. Ett långsamt nätverk stoppar aldrig verktyget längre än så.
- Svaret cachas i **6 timmar** i `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json`
  (`~/.cache/3DHeat/...` utan `LOCALAPPDATA`). Varje 3DHeat-verktyg har sin egen cachefil. "Ingen
  release ännu" (HTTP 404) cachas precis som ett svar; andra fel cachas inte och betyder bara att ingen
  notis visas.
- Versioner jämförs numeriskt (`v1.2.3` eller `1.2.3`; allt efter `-` eller `+` ignoreras).
- Offline, begränsad av hastighetsgräns eller bakom en proxy fortsätter verktyget med den version det har.

## Vad som händer när en nyare release finns {#what-happens-when-a-newer-release-is-out}

Vid start skriver det till felströmmen:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Med en terminal att svara i frågar det `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betyder ja).
  Efter en lyckad uppdatering **startas samma kommando om**, på den nya koden.
- Utan en (en pipe, en schemalagd körning) skriver det
  `Run python -m heat3d_update in <folder> to update.` och fortsätter oförändrat.

## Så tillämpas en uppdatering {#how-an-update-is-applied}

Beror på hur verktygen installerades:

- **En git-klon** (en `.git`-mapp och `git` på PATH): `git pull --ff-only`. Vägras medan utcheckningen
  har lokala ändringar i spårade filer - det är någons arbete; committa eller stasha dem först.
- **En nedladdad kopia**: releasens källarkiv laddas ned, packas upp i en tillfällig mapp (poster utanför
  arkivets egen mapp hoppas över), och **kontrolleras att det är den version det påstår** utifrån dess
  `VERSION`-fil. Sedan kopieras dess filer över den här mappen. Inom releasens egna Python-paket
  (`heat3d_*`-mappar överst i förrådet, och en nivå ned för den gamla monorepo-layouten) tas `.py`-moduler
  som releasen inte längre har bort, så att en föråldrad modul inte kan skugga sin ersättning.

Dina egna filer - inspelningar, varvfiler, inställningar, exporter, `.venv` - rörs aldrig: bara filer som
ingår i releasen skrivs.

## För hand {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Det skriver `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, eller den
nya versionen och vad den gjorde. Avslutningskod 1 om uppdateringen inte kunde tillämpas.

## Stänga av den {#switching-it-off}

Sätt **`HEAT3D_NO_UPDATE=1`** (vilket värde som helst utom tomt, `0`, `false`, `no`). Det stänger av
kontrollen och notisen vid start. `python -m heat3d_update` själv kontrollerar fortfarande när den körs
för hand.
