---
title: Frissítések
nav_order: 10
lang: "hu"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Frissítések {#updates}

A 3DHeat GameCapture indításkor ellenőrzi ennek a tárolónak a GitHub-kiadásait, jelzi, ha újabb verzió van, és
felajánlja a frissítést. Kód: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Mikor fut az ellenőrzés {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - a parancs futása előtt.
- `python -m heat3d_capture.ui` (és a `scan.bat`) - az ablak megnyitása előtt.
- `python -m heat3d_update` - kérésre, mindig újra megkérdezve a GitHubot.

## Hogyan működik az ellenőrzés {#how-the-check-works}

- A telepített verzió a tároló gyökerében lévő `VERSION` fájl (például `1.0.1`).
- A legújabb kiadást a `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest` címről kérdezzük le,
  **5 másodperces** időkorláttal. Egy lassú hálózat sosem tartja vissza az eszközt hosszabban.
- A választ **6 órára** gyorsítótárazzuk a
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` fájlban (`LOCALAPPDATA` nélkül a
  `~/.cache/3DHeat/...` helyen). Minden 3DHeat-eszköznek saját gyorsítótár-fájlja van. A „Még nincs kiadás” (HTTP 404)
  választ úgy tároljuk, mint bármely más választ; a többi hiba nincs gyorsítótárazva, és egyszerűen azt jelenti,
  hogy nincs értesítés.
- A verziókat számszerűen hasonlítjuk össze (`v1.2.3` vagy `1.2.3`; a `-` vagy `+` utáni rész figyelmen kívül marad).
- Offline, sebességkorlátozva vagy proxy mögött az eszköz a meglévő verzióval folytatja.

## Mi történik, ha újabb kiadás van {#what-happens-when-a-newer-release-is-out}

Indításkor a hibafolyamra ír ki:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Ha van terminál, ahol válaszolni lehet, megkérdezi: `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` jelentése igen).
  Sikeres frissítés után **ugyanaz a parancs újraindul**, már az új kóddal.
- Terminál nélkül (csőön keresztül, ütemezett futásnál) kiírja:
  `Run python -m heat3d_update in <folder> to update.` és változatlanul folytatja.

## Hogyan alkalmazódik a frissítés {#how-an-update-is-applied}

A telepítés módjától függ:

- **Git-klón** (van `.git` mappa, és a `git` a PATH-ban): `git pull --ff-only`. Ha a munkapéldányban helyi változtatás van
  a követett fájlokon, megtagadja: ez valakinek a munkája; előbb commitolja vagy tegye félre (stash).
- **Letöltött másolat**: a kiadás forrásarchívumát letöltjük, egy ideiglenes mappába kicsomagoljuk (az archívum saját
  mappáján kívüli bejegyzések kimaradnak), és **ellenőrizzük, hogy valóban az a verzió**, amelyet állít a `VERSION` fájlja.
  Ezután a fájlait átmásoljuk ebbe a mappába. A kiadás saját Python-csomagjaiban (a tároló tetején lévő `heat3d_*`
  mappák, és egy szinttel lejjebb a régi monorepo-elrendezésben) a kiadásban már nem szereplő `.py` modulokat töröljük,
  hogy egy elavult modul ne árnyékolhassa el a helyettesítőjét.

Az Ön saját fájljai - felvételek, körfájlok, beállítások, exportok, a `.venv` - sosem változnak: csak a kiadás részét
képező fájlok íródnak felül.

## Kézzel {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Kiírja: `Up to date: <version>.` (naprakész), `No release found ... offline, or nothing published yet.` (nincs kiadás
vagy offline), vagy az új verziót és a végrehajtott lépéseket. Kilépési kód 1, ha a frissítést nem lehetett alkalmazni.

## Kikapcsolás {#switching-it-off}

Állítsa be a **`HEAT3D_NO_UPDATE=1`** értéket (az üresen, `0`-n, `false`-on és `no`-n kívül bármi). Ez kikapcsolja az
indítási ellenőrzést és értesítést. A `python -m heat3d_update` kézi futtatása továbbra is ellenőriz.
