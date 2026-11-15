---
title: "Aktualizácie"
nav_order: 10
lang: "sk"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Aktualizácie {#updates}

3DHeat GameCapture pri štarte kontroluje vydania GitHub tohto repozitára, povie, keď je vonku
novšia verzia, a ponúkne aktualizáciu. Kód:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kedy kontrola prebehne {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - pred spustením príkazu.
- `python -m heat3d_capture.ui` (a `scan.bat`) - pred otvorením okna.
- `python -m heat3d_update` - na požiadanie, vždy sa pýta GitHub nanovo.

## Ako kontrola funguje {#how-the-check-works}

- Nainštalovaná verzia je súbor `VERSION` v koreni repozitára (napríklad `1.0.1`).
- Najnovšie vydanie sa pýta z `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`
  s **5-sekundovým** časovým limitom. Pomalá sieť nikdy nezastaví nástroj na dlhšie.
- Odpoveď sa ukladá do vyrovnávacej pamäte na **6 hodín** do
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` bez
  `LOCALAPPDATA`). Každý nástroj 3DHeat má vlastný súbor vyrovnávacej pamäte. "Zatiaľ žiadne vydanie"
  (HTTP 404) sa ukladá ako odpoveď; iné chyby sa neukladajú a znamenajú len, že sa nezobrazí žiadne
  upozornenie.
- Verzie sa porovnávajú číselne (`v1.2.3` alebo `1.2.3`; všetko za `-` alebo `+` sa ignoruje).
- Bez pripojenia, pri obmedzení počtu požiadaviek alebo za proxy nástroj pokračuje s verziou, ktorú
  má.

## Čo sa stane, keď je vonku novšie vydanie {#what-happens-when-a-newer-release-is-out}

Pri štarte vypíše do chybového výstupu:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Ak je k dispozícii terminál, na ktorý sa dá odpovedať, opýta sa `Update now? [Y/n]` (Enter, `y`,
  `yes`, `j`, `ja` znamenajú áno). Po úspešnej aktualizácii sa **rovnaký príkaz spustí znovu**, už
  na novom kóde.
- Bez neho (rúra, naplánovaný beh) vypíše `Run python -m heat3d_update in <folder> to update.` a
  pokračuje nezmenený.

## Ako sa aktualizácia uplatní {#how-an-update-is-applied}

Závisí od toho, ako boli nástroje nainštalované:

- **Klon gitu** (priečinok `.git` a `git` v PATH): `git pull --ff-only`. Odmietne sa, kým má
  pracovná kópia lokálne zmeny sledovaných súborov - to je cudzia práca; najprv ich commitnite alebo
  odložte (stash).
- **Stiahnutá kópia**: zdrojový archív vydania sa stiahne, rozbalí do dočasného priečinka (položky
  mimo vlastného priečinka archívu sa preskočia) a **skontroluje sa, že je to verzia, za ktorú sa
  vydáva** podľa svojho súboru `VERSION`. Potom sa jeho súbory skopírujú cez tento priečinok. V rámci
  Python balíkov vydania (priečinky `heat3d_*` na vrchnej úrovni repozitára a o úroveň nižšie pre
  starý monorepo layout) sa zmažú moduly `.py`, ktoré vydanie už nemá, aby zastaraný modul nemohol
  zakryť svoju náhradu.

Vaše vlastné súbory - nahrávky, súbory kôl, nastavenia, exporty, `.venv` - sa nikdy nedotknú: zapisujú
sa len súbory, ktoré sú súčasťou vydania.

## Ručne {#by-hand}

```bash
python -m heat3d_update            # skontrolovať a aktualizovať
python -m heat3d_update --check    # len zistiť, či je vonku novšie vydanie
```

Vypíše `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, alebo
novú verziu a čo urobil. Návratový kód 1, ak sa aktualizácia nedala uplatniť.

## Vypnutie {#switching-it-off}

Nastavte **`HEAT3D_NO_UPDATE=1`** (ľubovoľná hodnota okrem prázdnej, `0`, `false`, `no`). Tým sa
vypne kontrola pri štarte a upozornenie. `python -m heat3d_update` sa pri ručnom spustení kontroluje
aj tak.
