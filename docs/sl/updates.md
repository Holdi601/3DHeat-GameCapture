---
title: Posodobitve
nav_order: 10
lang: "sl"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Posodobitve {#updates}

3DHeat GameCapture ob zagonu preveri izdaje tega repozitorija na GitHubu, pove, kdaj je na voljo
novejša različica, in ponudi posodobitev. Koda: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kdaj poteka preverjanje {#when-the-check-runs}

- `python -m heat3d_capture <verb>` – preden se ukaz zažene.
- `python -m heat3d_capture.ui` (in `scan.bat`) – preden se odpre okno.
- `python -m heat3d_update` – na zahtevo; GitHub se vedno vpraša znova.

## Kako preverjanje deluje {#how-the-check-works}

- Nameščena različica je datoteka `VERSION` v korenu repozitorija (na primer `1.0.1`).
- Najnovejša izdaja se zahteva pri
  `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, s **5-sekundno**
  časovno omejitvijo. Počasno omrežje orodja nikoli ne zadrži dlje.
- Odgovor se shrani v predpomnilnik za **6 ur** v
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...`, kadar
  `LOCALAPPDATA` ni). Vsako orodje 3DHeat ima svojo datoteko predpomnilnika. „Še ni izdaje“ (HTTP 404)
  se shrani kot odgovor; druge napake se ne shranijo in pomenijo samo, da ni obvestila.
- Različice se primerjajo numerično (`v1.2.3` ali `1.2.3`; vse za `-` ali `+` se prezre).
- Brez povezave, pri omejitvi hitrosti ali za posrednikom orodje nadaljuje z različico, ki jo ima.

## Kaj se zgodi, ko je na voljo novejša izdaja {#what-happens-when-a-newer-release-is-out}

Ob zagonu izpiše v tok napak:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Če je na voljo terminal za odgovor, vpraša `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja`
  pomenijo da). Po uspešni posodobitvi se **isti ukaz zažene znova** na novi kodi.
- Brez njega (cev, načrtovan zagon) izpiše `Run python -m heat3d_update in <folder> to update.` in
  nadaljuje nespremenjeno.

## Kako se posodobitev uporabi {#how-an-update-is-applied}

Odvisno od tega, kako so bila orodja nameščena:

- **Klon git** (mapa `.git` in `git` v PATH): `git pull --ff-only`. Zavrne se, dokler ima kopija
  lokalne spremembe v sledenih datotekah – to je nečije delo; najprej jih predajte (commit) ali
  shranite v skladišče (stash).
- **Prenesena kopija**: izvorni arhiv izdaje se prenese, razpakira v začasno mapo (vnosi zunaj lastne
  mape arhiva se preskočijo) in **preveri, da je to različica, ki jo trdi**, iz svoje datoteke
  `VERSION`. Nato se njene datoteke prekopirajo čez to mapo. Znotraj lastnih paketov Python izdaje
  (mape `heat3d_*` na vrhu repozitorija in ena stopnja nižje za stari monorepo) se izbrišejo moduli
  `.py`, ki jih izdaja nima več, tako da zastareli modul ne more zakriti svoje zamenjave.

Vaše lastne datoteke – posnetki, datoteke krogov, nastavitve, izvozi, `.venv` – se nikoli ne
spremenijo: zapišejo se samo datoteke, ki so del izdaje.

## Ročno {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Izpiše `Up to date: <version>.`, `No release found ... offline, or nothing published yet.` ali novo
različico in kaj je naredil. Izhodna koda 1, če posodobitve ni bilo mogoče uporabiti.

## Izklop {#switching-it-off}

Nastavite **`HEAT3D_NO_UPDATE=1`** (katerakoli vrednost razen prazne, `0`, `false`, `no`). S tem se
izklopita preverjanje ob zagonu in obvestilo. `python -m heat3d_update` sam še vedno preveri, kadar ga
zaženete ročno.
