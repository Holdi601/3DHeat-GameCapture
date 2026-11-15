---
title: "Actualizări"
nav_order: 10
lang: "ro"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Actualizări {#updates}

3DHeat GameCapture verifică versiunile GitHub ale acestui depozit la pornire, spune când a apărut una
nouă și oferă să se actualizeze. Cod:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Când se face verificarea {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - înainte ca comanda să ruleze.
- `python -m heat3d_capture.ui` (și `scan.bat`) - înainte ca fereastra să se deschidă.
- `python -m heat3d_update` - la cerere, întrebând GitHub din nou.

## Cum funcționează verificarea {#how-the-check-works}

- Versiunea instalată este fișierul `VERSION` din rădăcina depozitului (de exemplu `1.0.1`).
- Ultima versiune se cere de la `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  cu un timeout de **5 secunde**. O rețea lentă nu blochează unealta mai mult de atât.
- Răspunsul este reținut în cache **6 ore** în
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` fără
  `LOCALAPPDATA`). Fiecare unealtă 3DHeat are propriul fișier de cache. „Nicio versiune încă” (HTTP 404)
  este reținută ca un răspuns; celelalte eșecuri nu sunt reținute și înseamnă doar că nu apare nicio
  notificare.
- Versiunile se compară numeric (`v1.2.3` sau `1.2.3`; tot ce urmează după `-` sau `+` este ignorat).
- Fără internet, cu limită de cereri sau în spatele unui proxy, unealta merge mai departe cu versiunea
  pe care o are.

## Ce se întâmplă când a apărut o versiune nouă {#what-happens-when-a-newer-release-is-out}

La pornire, afișează pe fluxul de erori:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Dacă există un terminal la care să răspundă, întreabă `Update now? [Y/n]` (Enter, `y`, `yes`, `j`,
  `ja` înseamnă da). După o actualizare reușită, **aceeași comandă este pornită din nou**, pe codul nou.
- Fără terminal (o conductă, o rulare programată), afișează
  `Run python -m heat3d_update in <folder> to update.` și merge mai departe neschimbată.

## Cum se aplică o actualizare {#how-an-update-is-applied}

Depinde de felul în care au fost instalate uneltele:

- **Un clon git** (un folder `.git` și `git` în PATH): `git pull --ff-only`. Refuzat cât timp copia de
  lucru are modificări locale la fișierele urmărite - acelea sunt munca cuiva; înregistrați-le
  (commit) sau puneți-le deoparte (stash) mai întâi.
- **O copie descărcată**: arhiva cu codul sursă al lansării este descărcată, extrasă într-un folder
  temporar (intrările din afara folderului propriu al arhivei sunt sărite) și **verificată să fie
  versiunea pe care o pretinde** din fișierul ei `VERSION`. Apoi fișierele ei sunt copiate peste acest
  folder. În pachetele Python ale lansării (folderele `heat3d_*` din vârful depozitului, și un nivel mai
  jos pentru vechiul aspect monorepo), modulele `.py` pe care lansarea nu le mai are sunt șterse, ca un
  modul vechi să nu umbrească înlocuitorul.

Fișierele dumneavoastră - înregistrările, fișierele de tur, setările, exporturile, `.venv` - nu sunt
atinse niciodată: se scriu doar fișierele care fac parte din lansare.

## Manual {#by-hand}

```bash
python -m heat3d_update            # verifică și actualizează
python -m heat3d_update --check    # spune doar dacă există o lansare nouă
```

Afișează `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, sau
versiunea nouă și ce a făcut. Codul de ieșire 1 dacă actualizarea nu a putut fi aplicată.

## Oprirea ei {#switching-it-off}

Setați **`HEAT3D_NO_UPDATE=1`** (orice valoare în afară de gol, `0`, `false`, `no`). Aceasta oprește
verificarea și notificarea de la pornire. `python -m heat3d_update` în sine tot verifică atunci când
este rulat manual.
