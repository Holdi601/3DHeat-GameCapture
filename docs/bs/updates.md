---
title: "Ažuriranja"
nav_order: 10
lang: "bs"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Ažuriranja {#updates}

3DHeat GameCapture pri pokretanju provjerava GitHub izdanja ovog repozitorija, javlja kad je izašla novija
verzija i nudi ažuriranje. Kod:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kada se provjera pokreće {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - prije nego što se komanda izvrši.
- `python -m heat3d_capture.ui` (i `scan.bat`) - prije nego što se prozor otvori.
- `python -m heat3d_update` - na zahtjev, uvijek iznova pita GitHub.

## Kako provjera radi {#how-the-check-works}

- Instalirana verzija je datoteka `VERSION` u korijenu repozitorija (na primjer `1.0.1`).
- Najnovije izdanje se traži sa `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  uz vremensko ograničenje od **5 sekundi**. Spora mreža nikad ne zaustavlja alat duže od toga.
- Odgovor se kešira **6 sati** u
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` bez
  `LOCALAPPDATA`). Svaki 3DHeat alat ima svoju keš datoteku. "Još nema izdanja" (HTTP 404) kešira se
  kao odgovor; ostali neuspjesi se ne keširaju i jednostavno znače da nema obavijesti.
- Verzije se porede brojčano (`v1.2.3` ili `1.2.3`; sve nakon `-` ili `+` se ignorira).
- Offline, uz ograničenje broja zahtjeva ili iza proxyja, alat nastavlja s verzijom koju ima.

## Šta se dešava kad je izašlo novije izdanje {#what-happens-when-a-newer-release-is-out}

Pri pokretanju ispisuje, na tok grešaka:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Ako ima terminal za odgovor, pita `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znače
  da). Nakon uspješnog ažuriranja **ista komanda se pokreće ponovo**, na novom kodu.
- Bez njega (cijev, zakazano pokretanje), ispisuje
  `Run python -m heat3d_update in <folder> to update.` i nastavlja nepromijenjeno.

## Kako se ažuriranje primjenjuje {#how-an-update-is-applied}

Zavisi od toga kako su alati instalirani:

- **Git klon** (folder `.git` i `git` na PATH-u): `git pull --ff-only`. Odbija se dok
  checkout ima lokalne promjene praćenih datoteka - to je nečiji rad; prvo ih commitaj ili stash-aj.
- **Preuzeta kopija**: izvorna arhiva izdanja se preuzima, raspakuje u privremeni
  folder (stavke izvan arhivinog vlastitog foldera se preskaču), i **provjerava da je verzija
  za koju se predstavlja** prema njenoj datoteci `VERSION`. Zatim se njene datoteke kopiraju preko ovog foldera. Unutar
  vlastitih Python paketa izdanja (`heat3d_*` folderi na vrhu repozitorija, i jedan nivo
  niže za staru monorepo strukturu), `.py` moduli kojih izdanje više nema se brišu, da
  zastarjeli modul ne zasjeni svoju zamjenu.

Vaše vlastite datoteke - snimci, datoteke krugova, postavke, izvozi, `.venv` - se nikad ne diraju: piše se samo
u datoteke koje su dio izdanja.

## Ručno {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Ispisuje `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, ili
novu verziju i šta je uradio. Izlazni kod 1 ako se ažuriranje nije moglo primijeniti.

## Isključivanje {#switching-it-off}

Postavite **`HEAT3D_NO_UPDATE=1`** (bilo koja vrijednost osim praznog, `0`, `false`, `no`). To isključuje
provjeru i obavijest pri pokretanju. `python -m heat3d_update` i dalje provjerava kad se pokrene ručno.
