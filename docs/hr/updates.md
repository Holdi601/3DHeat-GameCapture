---
title: Ažuriranja
nav_order: 10
lang: "hr"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Ažuriranja {#updates}

3DHeat GameCapture pri pokretanju provjerava GitHub izdanja ovog repozitorija, javlja kad je izašla
novija verzija i nudi ažuriranje. Kod:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kad se provjera izvodi {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - prije nego se naredba izvede.
- `python -m heat3d_capture.ui` (i `scan.bat`) - prije nego se prozor otvori.
- `python -m heat3d_update` - na zahtjev, uvijek ponovno pitajući GitHub.

## Kako provjera radi {#how-the-check-works}

- Instalirana verzija je datoteka `VERSION` u korijenu repozitorija (na primjer `1.0.1`).
- Najnovije izdanje se traži s `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  uz **5-sekundni** rok. Spor mrežni put nikad ne zaustavlja alat na dulje od toga.
- Odgovor se čuva **6 sati** u `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json`
  (`~/.cache/3DHeat/...` bez `LOCALAPPDATA`). Svaki alat 3DHeat ima svoju datoteku predmemorije. "Nema
  izdanja" (HTTP 404) se sprema kao odgovor kao i svaki drugi; ostali neuspjesi se ne spremaju i samo
  znače da nema obavijesti.
- Verzije se uspoređuju brojčano (`v1.2.3` ili `1.2.3`; sve iza `-` ili `+` se zanemaruje).
- Bez mreže, s ograničenjem brzine ili iza proxyja, alat nastavlja s verzijom koju ima.

## Što se događa kad je izašlo novije izdanje {#what-happens-when-a-newer-release-is-out}

Pri pokretanju ispisuje na tok grešaka:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- S terminalom na kojem može odgovoriti, pita `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znače
  da). Nakon uspješnog ažuriranja **ista naredba se pokreće ponovno**, na novom kodu.
- Bez terminala (cijev, zakazano pokretanje), ispisuje
  `Run python -m heat3d_update in <folder> to update.` i nastavlja nepromijenjeno.

## Kako se ažuriranje primjenjuje {#how-an-update-is-applied}

Ovisi o tome kako su alati instalirani:

- **Git klon** (mapa `.git` i `git` na PATH-u): `git pull --ff-only`. Odbija se dok checkout ima
  lokalne promjene na praćenim datotekama - to je nečiji rad; prvo ih commitajte ili stashajte.
- **Preuzeta kopija**: arhiva izvornog koda izdanja se preuzme, raspakira u privremenu mapu (unosi izvan
  vlastite mape arhive se preskaču) i **provjeri da je verzija koju tvrdi** iz svoje datoteke `VERSION`.
  Zatim se njezine datoteke kopiraju preko ove mape. Unutar Python paketa izdanja (mape `heat3d_*` na
  vrhu repozitorija, i jednu razinu niže za stariji monorepo raspored) brišu se `.py` moduli koje
  izdanje više nema, pa zastarjeli modul ne može zasjeniti svoju zamjenu.

Vaše vlastite datoteke - snimke, datoteke krugova, postavke, izvozi, `.venv` - se nikad ne diraju: piše
se samo ono što je dio izdanja.

## Ručno {#by-hand}

```bash
python -m heat3d_update            # provjeri i ažuriraj
python -m heat3d_update --check    # samo kaže postoji li novije izdanje
```

Ispisuje `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, ili novu
verziju i što je učinjeno. Izlazni kod 1 ako se ažuriranje nije moglo primijeniti.

## Isključivanje {#switching-it-off}

Postavite **`HEAT3D_NO_UPDATE=1`** (bilo koja vrijednost osim prazne, `0`, `false`, `no`). Time se
isključuje provjera i obavijest pri pokretanju. `python -m heat3d_update` sam i dalje provjerava kad se
pokrene ručno.
