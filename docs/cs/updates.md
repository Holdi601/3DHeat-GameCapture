---
title: Aktualizace
nav_order: 10
lang: "cs"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Aktualizace {#updates}

3DHeat GameCapture při startu kontroluje GitHub releases tohoto repozitáře, řekne, když je venku novější verze, a nabídne aktualizaci. Kód: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kdy kontrola běží {#when-the-check-runs}

- `python -m heat3d_capture <verb>`: před během příkazu.
- `python -m heat3d_capture.ui` (a `scan.bat`): před otevřením okna.
- `python -m heat3d_update`: na vyžádání, vždy se ptá GitHubu znovu.

## Jak kontrola funguje {#how-the-check-works}

- Nainstalovaná verze je soubor `VERSION` v kořeni repozitáře (například `1.0.1`).
- Nejnovější vydání se žádá z `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, s časovým limitem **5 sekund**. Pomalá síť nikdy nezdrží nástroj déle.
- Odpověď se ukládá do mezipaměti na **6 hodin** do `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` bez `LOCALAPPDATA`). Každý nástroj 3DHeat má svůj soubor mezipaměti. „Zatím žádné vydání“ (HTTP 404) se ukládá jako odpověď. Ostatní selhání se neukládají a znamenají jen, že se nic neoznámí.
- Verze se porovnávají číselně (`v1.2.3` nebo `1.2.3`; cokoli za `-` nebo `+` se ignoruje).
- Offline, při omezení počtu požadavků nebo za proxy nástroj pokračuje s verzí, kterou má.

## Co se stane, když je venku novější vydání {#what-happens-when-a-newer-release-is-out}

Při startu vypíše do chybového proudu:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Když je terminál, kde lze odpovědět, zeptá se `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znamenají ano). Po úspěšné aktualizaci se **spustí znovu stejný příkaz** na novém kódu.
- Bez něj (roura, naplánovaný běh) vypíše `Run python -m heat3d_update in <folder> to update.` a pokračuje beze změny.

## Jak se aktualizace použije {#how-an-update-is-applied}

Závisí na tom, jak byly nástroje nainstalovány:

- **Klon gitu** (složka `.git` a `git` v PATH): `git pull --ff-only`. Odmítne se, dokud má kopie místní změny v sledovaných souborech. To je něčí práce; nejdřív je commitněte nebo odložte (stash).
- **Stažená kopie**: archiv se zdrojovým kódem vydání se stáhne, rozbalí do dočasné složky (položky mimo vlastní složku archivu se přeskočí) a **zkontroluje**, že je to verze, za kterou se vydává, podle jeho souboru `VERSION`. Pak se jeho soubory zkopírují přes tuto složku. V Python balíčcích vydání (složky `heat3d_*` na vrcholu repozitáře a o úroveň níž pro starší monorepo) se smažou `.py` moduly, které vydání už nemá, aby zastaralý modul nezastínil svou náhradu.

Vaše vlastní soubory (záznamy, soubory kol, nastavení, exporty, `.venv`) se nikdy nedotknou. Zapisují se jen soubory, které jsou součástí vydání.

## Ručně {#by-hand}

```bash
python -m heat3d_update            # zkontrolovat a aktualizovat
python -m heat3d_update --check    # jen říct, zda je venku novější vydání
```

Vypíše `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, nebo novou verzi a co udělal. Návratový kód je 1, když aktualizaci nešlo použít.

## Vypnutí {#switching-it-off}

Nastavte **`HEAT3D_NO_UPDATE=1`** (libovolná hodnota kromě prázdné, `0`, `false`, `no`). Tím se vypne kontrola a oznámení při startu. `python -m heat3d_update` spuštěný ručně kontroluje stále.
