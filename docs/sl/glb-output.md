---
title: Izhod .glb
nav_order: 6
lang: "sl"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Izhod .glb {#the-glb-output}

Rekonstrukcija se zapiše kot binarna datoteka glTF 2.0 (`.glb`), ki jo pregledovalnik 3DHeat naloži prek
svoje plošče „Ozadje / nivo“ brez posebne obdelave – enaka pogodba, kot jo zapisuje izvoznik za
Unreal. Koda: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Zapisano je ročno, ne prek knjižnice glTF: izhod je ozek podnabor (en medpomnilnik, tesno
zapakiran, brez animacije, brez skinninga), odvisnost, ki bi znala zapisati ves glTF, pa bi za
nekaj sto vrstic prinesla neusklajenost različic.

## Kaj je v datoteki skeniranja {#what-is-in-a-scans-file}

| Del (ime vozlišča in mreže) | Vsebina |
|---|---|
| `ground:<name>` | trikotniki, obrnjeni največ 35 stopinj navzgor |
| `structure:<name>` | vse drugo |

`<name>` je ime datoteke brez končnice, kadar shranjujete iz okna, ali ime videa za `reconstruct`.
Del brez trikotnikov se izpusti. Skeniranje nikoli ne zapiše dela `water:`. `asset.generator` je
`heat3d-capture-scan`.

## Pogodba {#the-contract}

- **Eno vozlišče na del**, poimenovano z oznako dela; mreža ponovi ime. Pregledovalnik najprej bere ime
  *vozlišča*, zato bi z imenovanjem samo mrež izgubili razvrstitev.
- Oznaka je `<razred>:<ime>`, razred `ground`, `structure` ali `water` – predpona, ki se ujema s
  pregledovalnikom (`^(ground|structure|water)\s*[:|]`), da prevzame razred, kot je zapisan, namesto da ga
  ugiba iz geometrije. Tla se upodobijo polna, konstrukcije skoraj prosojne.
- **Koordinate so v prostoru pregledovalnika**: Y navzgor, desnosučni, **pomnožene na centimetre** (metri x
  100), da se ujemajo z izvoznikom za Unreal; tako se zajem in izvoz iz pogona istega kraja naložita
  v isti velikosti z enakimi privzetimi nastavitvami kamere. Na vrhnjem nivoju datoteke je
  `extras.unit_metres` enak `0.01` (ena enota je centimeter), zato bere v metrih, kot je
  [`locate`](locate.md), vzame velikost v resnični meri. Skeniranje, postavljeno s telemetrijo Forze,
  je izjema pri sučnosti: ostane v lastnem svetu igre, Y navzgor in levosučni, točno kot datoteke
  krogov, zato krogi, posneti nad njim, pristanejo nanj. Kadar je bilo merilo skeniranja najdeno na
  poznejšem ključnem okvirju ([Merilo](reconstruction-pose.md#scale)), se ta faktor vključi v
  zapisano merilo.
- `COLOR_0` bere pregledovalnik, ki z njim senči tla, kadar je stikalo *Zajeta barva* na njegovi plošči
  „Ozadje / nivo“ vklopljeno (privzeto izklopljeno).
- Skeniranje z ročno označenimi mesti dobi ob sebi datoteko `<name>.marks.json`; glejte
  [Shranjevanje](reconstruction-scan-ui.md#saving).
- Za vsak primitiv: `POSITION` (float VEC3, z `min` in `max`, iz katerih pregledovalnik uokvirja kamero),
  `NORMAL` (float VEC3), neobvezen `COLOR_0` (float VEC3, 0..1), neobvezen `TEXCOORD_0`; indeksi
  kot 16-bitni, kadar je vsak indeks manjši od 65.536, sicer 32-bitni; način: trikotniki.
- Vsak pogled na medpomnilnik se začne poravnan na 4 bajte; kos JSON je dopolnjen s presledki, kos
  BIN z ničlami na 4 bajte.

## Preverjanja pred zapisom {#checks-before-writing}

Vsak del se preveri in zavrne s sporočilom, ki ga imenuje, če nima oglišč, če število indeksov ni
celo število trikotnikov, če je indeks zunaj območja ali negativen, če položaji niso končni ali če
normale ali barve ne ustrezajo številu oglišč. Manjkajoče normale se izračunajo **uteženo po
površini** (marching cubes pušča tanke lističe ob velikih ploskvah, neuteženo povprečje pa pusti,
da drobni trikotniki prevladajo nad ploskvijo, na kateri ležijo); degeneriranemu oglišču se dodeli
»navzgor«. Zapis brez delov je napaka.

Izvoz ne vrne ničesar – in okno napiše „Nothing to save“ – kadar prostornina ne da nobene površine,
namesto da bi zapisal prazno datoteko, ki bi jo bralo kot uspešno skeniranje.

## Teksture {#textures}

Pisalnik podpira teksturo osnovne barve PNG za vsak del (z UV koordinatami, dvostransko,
nekovinsko, popolnoma hrapavo snov). Skeniranja je ne uporabljajo; nosijo barvo po ogliščih.
Glejte [barva](reconstruction-fusion-and-texture.md#colour).

## Referenčni nivo {#the-reference-level}

`geometry/reference.py` s tem istim pisalnikom sestavi sintetični nivo natanko znane velikosti:
400 m razdeljena tla, tri stavbe 20 x 20 x 12 m in ribnik 50 m pod tlemi 1,5 m, vsak razred v svoji
nivoja barvi. Lastni testi pregledovalnika ga ustvarijo in razčlenijo z dejanskim razčlenjevalnikom pregledovalnika,
zato format datoteke ostane preizkušen na obeh straneh brez igre in brez strojne opreme za zajem.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
