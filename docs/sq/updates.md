---
title: "Përditësimet"
nav_order: 10
lang: "sq"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Përditësimet {#updates}

3DHeat GameCapture kontrollon botimet në GitHub të këtij repozitori kur nis, thotë kur ka dalë një version më i ri
dhe ofron ta përditësojë. Kodi:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kur ekzekutohet kontrolli {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - para se të ekzekutohet komanda.
- `python -m heat3d_capture.ui` (dhe `scan.bat`) - para se të hapet dritarja.
- `python -m heat3d_update` - sipas kërkesës, gjithmonë duke pyetur GitHub nga e para.

## Si funksionon kontrolli {#how-the-check-works}

- Versioni i instaluar është skedari `VERSION` në rrënjën e repozitorit (për shembull `1.0.1`).
- Botimi më i ri kërkohet te `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  me kufi kohe **5 sekonda**. Një rrjet i ngadaltë nuk e ngec kurrë mjetin më gjatë.
- Përgjigjja ruhet në cache për **6 orë** te
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` pa
  `LOCALAPPDATA`). Çdo mjet 3DHeat ka skedarin e vet cache. "Ende pa botim" (HTTP 404) ruhet
  si përgjigje; dështimet e tjera nuk ruhen dhe thjesht nënkuptojnë se nuk ka njoftim.
- Versionet krahasohen numerikisht (`v1.2.3` ose `1.2.3`; çdo gjë pas `-` ose `+` shpërfillet).
- Offline, me kufizim shpejtësie ose pas një proxy-je, mjeti vazhdon me versionin që ka.

## Çfarë ndodh kur ka dalë një botim më i ri {#what-happens-when-a-newer-release-is-out}

Në nisje printon, në rrjedhën e gabimeve:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Me një terminal ku mund të përgjigjesh, pyet `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` do të thotë
  po). Pas një përditësimi të suksesshëm **e njëjta komandë niset sërish**, mbi kodin e ri.
- Pa të (një pipe, një ekzekutim i planifikuar), printon
  `Run python -m heat3d_update in <folder> to update.` dhe vazhdon pa ndryshim.

## Si zbatohet një përditësim {#how-an-update-is-applied}

Varet nga mënyra si u instaluan mjetet:

- **Një klon git** (një dosje `.git` dhe `git` te PATH): `git pull --ff-only`. Refuzohet ndërsa
  checkout-i ka ndryshime lokale në skedarë të ndjekur - ato janë puna e dikujt; bëji commit ose stash
  fillimisht.
- **Një kopje e shkarkuar**: arkivi burimor i botimit shkarkohet, nxirret në një dosje të përkohshme
  (hyrjet jashtë dosjes së vetë arkivit anashkalohen), dhe **kontrollohet të jetë versioni që pretendon**
  nga skedari i tij `VERSION`. Pastaj skedarët e tij kopjohen mbi këtë dosje. Brenda paketave Python
  të vetë botimit (dosjet `heat3d_*` në krye të repozitorit, dhe një nivel më poshtë për strukturën e vjetër
  monorepo), modulet `.py` që botimi nuk i ka më fshihen, që një modul i vjetër
  të mos e hijezojë zëvendësuesin e tij.

Skedarët e tu - regjistrimet, skedarët e xhirave, cilësimet, eksportet, `.venv` - nuk preken kurrë: shkruhen vetëm
skedarët që janë pjesë e botimit.

## Me dorë {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Printon `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, ose
versionin e ri dhe çfarë bëri. Kodi i daljes 1 nëse përditësimi nuk mund të zbatohej.

## Fikja e tij {#switching-it-off}

Vendos **`HEAT3D_NO_UPDATE=1`** (çdo vlerë përveç bosh, `0`, `false`, `no`). Kjo fik
kontrollin dhe njoftimin në nisje. `python -m heat3d_update` vetë ende kontrollon kur ekzekutohet me dorë.
