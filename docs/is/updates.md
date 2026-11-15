---
title: "Uppfærslur"
nav_order: 10
lang: "is"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Uppfærslur {#updates}

3DHeat GameCapture athugar GitHub útgáfur þessarar geymslu við ræsingu, segir til þegar nýrri
útgáfa er komin og býðst til að uppfæra. Kóði:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Hvenær athugunin keyrir {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - áður en skipunin keyrir.
- `python -m heat3d_capture.ui` (og `scan.bat`) - áður en glugginn opnast.
- `python -m heat3d_update` - samkvæmt beiðni, spyr alltaf GitHub upp á nýtt.

## Hvernig athugunin virkar {#how-the-check-works}

- Uppsetta útgáfan er `VERSION` skráin í rót geymslunnar (til dæmis `1.0.1`).
- Nýjasta útgáfan er sótt frá `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  með **5 sekúndna** tímamörkum. Hægt net tefur verkfærið aldrei lengur.
- Svarið er geymt í **6 klukkustundir** í
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` án
  `LOCALAPPDATA`). Hvert 3DHeat verkfæri hefur sína eigin skyndiminnisskrá. „Engin útgáfa enn“ (HTTP 404) er geymt
  eins og svar; aðrar villur eru ekki geymdar og þýða einfaldlega engin tilkynning.
- Útgáfur eru bornar saman tölulega (`v1.2.3` eða `1.2.3`; allt á eftir `-` eða `+` er hunsað).
- Án nettengingar, með takmörkun á fjölda beiðna eða á bak við milliþjón heldur verkfærið áfram með útgáfuna sem það hefur.

## Hvað gerist þegar nýrri útgáfa er komin {#what-happens-when-a-newer-release-is-out}

Við ræsingu prentar það, í villustrauminn:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Með skipanalínu til að svara í spyr það `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` þýða
  já). Eftir árangursríka uppfærslu **er sama skipun ræst aftur**, á nýja kóðanum.
- Án hennar (pípa, tímasett keyrsla) prentar það
  `Run python -m heat3d_update in <folder> to update.` og heldur áfram óbreytt.

## Hvernig uppfærsla er framkvæmd {#how-an-update-is-applied}

Fer eftir því hvernig verkfærin voru sett upp:

- **Git afrit (clone)** (`.git` mappa og `git` í PATH): `git pull --ff-only`. Hafnað meðan
  afritið hefur staðbundnar breytingar á fylgdum skrám - þær eru vinna einhvers; vistaðu þær eða settu til hliðar
  fyrst.
- **Niðurhalað afrit**: frumkóðasafn útgáfunnar er sótt, dregið út í tímabundna
  möppu (færslur utan eigin möppu safnsins eru hunsaðar) og **athugað að það sé útgáfan
  sem það segist vera** úr `VERSION` skránni. Síðan eru skrár þess afritaðar yfir þessa möppu. Innan
  eigin Python pakka útgáfunnar (`heat3d_*` möppur efst í geymslunni, og einu stigi
  neðar fyrir gamla einrepó-skipulagið) er `.py` einingum sem útgáfan hefur ekki lengur eytt, svo að
  gömul eining skyggi ekki á arftaka sinn.

Þínar eigin skrár - upptökur, hringskrár, stillingar, útflutningur, `.venv` - eru aldrei snertar: aðeins
skrár sem eru hluti af útgáfunni eru skrifaðar.

## Í höndunum {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Það prentar `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, eða
nýju útgáfuna og hvað það gerði. Skilakóði 1 ef ekki tókst að beita uppfærslunni.

## Að slökkva á því {#switching-it-off}

Stilltu **`HEAT3D_NO_UPDATE=1`** (hvaða gildi sem er nema tómt, `0`, `false`, `no`). Það slekkur á
athuguninni við ræsingu og tilkynningunni. `python -m heat3d_update` sjálft athugar samt þegar það er keyrt í höndunum.
