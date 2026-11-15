---
title: Updates
nav_order: 10
lang: "nl"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Updates {#updates}

3DHeat GameCapture controleert bij het starten de GitHub-releases van deze repository, meldt wanneer er een nieuwere versie uit is, en biedt aan bij te werken. Code: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Wanneer de controle draait {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - vóór de opdracht draait.
- `python -m heat3d_capture.ui` (en `scan.bat`) - voordat het venster opent.
- `python -m heat3d_update` - op verzoek; vraagt GitHub altijd opnieuw.

## Hoe de controle werkt {#how-the-check-works}

- De geïnstalleerde versie is het bestand `VERSION` in de hoofdmap van de repository (bijvoorbeeld `1.0.1`).
- De nieuwste release wordt opgevraagd bij `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, met een time-out van **5 seconden**. Een trage netwerkverbinding houdt de tool nooit langer tegen.
- Het antwoord wordt **6 uur** bewaard in `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` zonder `LOCALAPPDATA`). Elke 3DHeat-tool heeft zijn eigen cachebestand. "Nog geen release" (HTTP 404) wordt net als een antwoord bewaard; andere fouten worden niet bewaard en betekenen gewoon geen melding.
- Versies worden numeriek vergeleken (`v1.2.3` of `1.2.3`; alles na `-` of `+` wordt genegeerd).
- Offline, bij een limiet op het aantal verzoeken of achter een proxy, gaat de tool door met de versie die hij heeft.

## Wat er gebeurt wanneer een nieuwere release uit is {#what-happens-when-a-newer-release-is-out}

Bij het opstarten drukt hij af, naar de foutstroom:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Met een terminal om op te antwoorden vraagt hij `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betekenen ja). Na een geslaagde update **wordt dezelfde opdracht opnieuw gestart**, met de nieuwe code.
- Zonder terminal (een pipe, een geplande run) drukt hij `Run python -m heat3d_update in <folder> to update.` af en gaat ongewijzigd door.

## Hoe een update wordt toegepast {#how-an-update-is-applied}

Hangt af van hoe de tools zijn geïnstalleerd:

- **Een git-kloon** (een map `.git` en `git` in het PATH): `git pull --ff-only`. Wordt geweigerd zolang de checkout lokale wijzigingen in bijgehouden bestanden heeft - dat is iemands werk; commit of stash die eerst.
- **Een gedownloade kopie**: het bronarchief van de release wordt gedownload, uitgepakt naar een tijdelijke map (items buiten de eigen map van het archief worden overgeslagen), en **gecontroleerd of het de versie is die het zegt te zijn** via het bestand `VERSION`. Daarna worden de bestanden over deze map gekopieerd. Binnen de eigen Python-pakketten van de release (mappen `heat3d_*` bovenaan de repository, en één niveau lager voor de oude monorepo-indeling) worden `.py`-modules die de release niet meer heeft verwijderd, zodat een verouderde module zijn vervanger niet kan overschaduwen.

Je eigen bestanden - opnames, rondebestanden, instellingen, exports, de `.venv` - worden nooit aangeraakt: alleen bestanden die bij de release horen worden geschreven.

## Met de hand {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Het drukt `Up to date: <version>.`, `No release found ... offline, or nothing published yet.` af, of de nieuwe versie en wat het deed. Exitcode 1 als de update niet kon worden toegepast.

## Uitschakelen {#switching-it-off}

Zet **`HEAT3D_NO_UPDATE=1`** (elke waarde behalve leeg, `0`, `false`, `no`). Dat schakelt de controle en melding bij het opstarten uit. `python -m heat3d_update` zelf controleert nog wel wanneer je het met de hand draait.
