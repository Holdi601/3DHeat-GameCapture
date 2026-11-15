---
title: "A szkennelő ablak"
nav_order: 1
lang: "hu"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# A szkennelő ablak {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kód: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Az ablak a `scan/session.py` és a `scan/reconstruct.py` vékony nézete; nincs saját szkennelési vagy geometriai logikája.

## Indulás {#starting-up}

1. **Frissítés-ellenőrzés** - lásd [Frissítések](updates.md).
2. **Függőség-ellenőrzés** - minden csomagot ellenőriz, amelyre a szkennernek szüksége van, mielőtt bármit importálna. A hiányzókat felsorolja azzal, mire kellenek és mekkora a letöltésük, és csak a „Letöltés és telepítés” gombra telepíti őket. A Mégse kilép, és semmit nem változtat. Lásd [Futtatás és függőségek](runtime.md#first-run-preflight).
3. **Ablak** - „3DHeat — Level scanner”, 1420 x 900, Qt Fusion stílussal.
4. **Hardverellenőrzés** - a legjobb következtető-háttér kiválasztása, a mélységmodell betöltése, és a teljesítménye mérése 6 képkockán; a bal felső ítéletdoboz megmondja, milyen lesz a szkennelés (lásd [Futtatás](runtime.md#what-to-expect-from-this-machine)).
5. **Globális billentyűk** - utoljára regisztrálódnak.

### Ha még nincs mélységmodell {#when-there-is-no-depth-model-yet}

Ha a `models/` mappában nincs `depth-*.onnx`, az ítélet ezt írja: **„One more thing to set up.”**, a Start le van tiltva, és megjelenik egy **Mélységmodell beállítása** gomb. Ez:

- ellenőrzi a PyTorch-ot, a `transformers`-t és az `onnxscript`-et (együtt kb. 945 MB), és telepítés előtt kérdez;
- a `tools/export_onnx.py --size small` parancsot külön folyamatként futtatja (így a PyTorch soha nem marad a szkenner memóriájában), 30 perces korláttal. Az ablak nem reagál, amíg fut;
- sikeresen futva újra elvégzi a hardverellenőrzést; sikertelenül az átalakító kimenetének utolsó 600 karakterét mutatja.

Ha több modell van jelen, a választás **licenc szerint, nem fájlnév szerint** történik: a `depth-small-*` (Apache-2.0, kereskedelmi használat engedélyezett), ha van, különben a Base, majd a Large (mindkettő nem kereskedelmi). Az ítéletdoboz és a gombok alatti szürke sor megnevezi a használt fájlt, a licencét, és a jelen lévő, de nem használt modellfájlokat - például: `Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used: depth-base-518.onnx`. A Base-zel való szkenneléshez vidd ki a Small fájlt a `models/` mappából.

## Bal oszlop: beállítások {#left-column-settings}

| Csoport | Vezérlő | Alapérték | Tartomány / értékek | Mit csinál |
|---|---|---|---|---|
| (felül) | Ítéletdoboz | „Checking your graphics card…” | zöld, sárga vagy piros, szint szerint | Címsor, `<device> via <API> — N views per second`, egy megjegyzés és `Depth model: <file> (<licence>)` |
| Mit szkenneljünk | Forrás | Teljes képernyő | Teljes képernyő, Egy ablak, Videófájl | Honnan jönnek a képkockák |
| | Melyik | `1` | monitorszám / ablakcím / videó útvonala | `monitor:<n>`, `window:<title>`, vagy fájlútvonal |
| | Fájl kiválasztása… | videónál látszik | `*.mp4 *.mkv *.avi *.mov` | Kitölti az útvonalat |
| Mennyire alaposan | Előbeállítás | Kiegyensúlyozott | Vázlat, Kiegyensúlyozott, Részletes | A rögzítési felbontás és a kulcskockázás szelektivitása (lent); egysoros összefoglaló látszik alatta |
| | Játék látómezője | 90° | 30-140° | A játék **vízszintes** látómezője. Túl szűk esetén a pálya mélyebbnek rekonstruálódik, mint amilyen; túl szélesnél lapossá válik. A versenyjátékok inkább 65° körül vannak |
| | Felületi részletesség | 0,25 m | 0,05-2,0 m, lépésköz 0,05 | A felület voxelmérete. Kisebb finomabb és nehezebb |
| Állj meg, ha | Idő | nincs korlát | 0-120 perc | Ennyi idő után véget vet a szkennelésnek (0 = nincs korlát) |
| | Megtartott nézetek | 3000 | 0-100 000 | Ennyi kulcskocka után véget vet a szkennelésnek, memóriavédelemként (0 = nincs korlát) |
| Mit hagyjunk figyelmen kívül | HUD és minden a kameránál figyelmen kívül hagyása | be | | Megtanulja és kitakarja a HUD-ot, a célkeresztet, a fegyvert, a motorháztetőt, a vezetőfülkét ([Rögzítés](reconstruction-capture.md#what-is-not-the-world)). Az alatta lévő sor megmondja, mit dönt most a detektor |
| Játék közben | Visszajelzés a játék fölött | be | | A szkennelés közben megnyitja az átkattintható fedvényt. Alatta a tipp: a játékot **szegélyezett ablakos** módban futtasd; a kizárólagos teljes képernyő fölé semmi nem rajzolhat |
| Versenytelemetria (Forza) | Pozíciós adatok figyelése | ki | | A kameraútvonalat a Forza Data Outjából veszi a képből becsült helyett ([Póz](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | A Data Out portja |
| | (állapotsor) | | | `N packets — poses come from the game, not from the picture`, vagy `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Szkennelés indítása** / **Szkennelés leállítása** | | | Elindítja vagy leállítja; megmutatja a gyorsbillentyűt, ha regisztrálódott |
| | **Mélységmodell beállítása** | rejtett | | Lásd fent |
| | **Pálya mentése…** | letiltva | | Egy felületi voxeleket adó szkennelés után engedélyezett; fájlnevet kér (alapértelmezés `scan.glb`) |
| | (szürke sor) | | | `Model: <file> (<licence>) · Available: <backends>`, plusz beállítási megjegyzések, például az `onnxruntime-gpu` telepítése |

### Az előbeállítások {#the-presets}

| Előbeállítás | Rögzítés leghosszabb oldala | Megtartási kvantilis | Kezdeti küszöb | Megjelenített összefoglaló |
|---|---|---|---|---|
| Vázlat | 640 px | 0,85 | 0,020 | Gyors és durva. Jó egy útvonal ellenőrzésére, a valódi szkennelés előtt. |
| Kiegyensúlyozott | 960 px | 0,65 | 0,010 | A szokásos választás. Normál tempóban sétálj. |
| Részletes | 1280 px | 0,40 | 0,004 | Lassú és alapos. Sétálj szándékosan, és fordulj finoman. |

A megtartási kvantilis azt jelenti: „tarts meg egy képkockát, ha az jobban változott, mint az utolsó 240 képkocka változásainak ez a kvantilise” - a Vázlat nagyjából a legzsúfoltabb 15%-ot tartja meg, a Részletes a legzsúfoltabb 60%-ot. Lásd [Kulcskockák](reconstruction-capture.md#keyframes).

### Az ablakban rögzített beállítások {#settings-that-are-fixed-in-the-window}

Az ablak szkenneléskor mindig rekonstruál, a földsík léptékéhez **1,15 m** kamera-magasságot használ (a 1,70 m-es járómagasság nem választható), és a háttér-létrára bízza a GPU kiválasztását. Ezek a `ScanSettings` mezői (`camera_height`, `prefer_backend`), amelyeket csak egy szkript tud megváltoztatni.

## Jobb oszlop: mit csinál a szkennelés {#right-column-what-the-scan-is-doing}

| Elem | Mit mutat |
|---|---|
| **Amit a kamera lát** | az utolsó kulcskocka |
| **Az alak, amelyet olvas** | a jósolt mélysége, a Turbo színtérképpel színezve, az adott képkocka 2. és 98. percentilise között normalizálva (hogy egy égbolt-pixel ne lapítsa el a tartományt) |
| **Lefedettség — ahol jártál, és milyen jól** | egy alaprajz (lent) |
| **Érdemes újra megnézni** | a gyenge pontok, számozva, a térképen lévő gyűrűkkel egyezve, mindegyiknél egy utasítással; a legrosszabb (legnagyobb) elöl, legfeljebb 8; utána a te megjelölt pontjaid (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Séta-sebesség sáv | `walk speed — N% of the way to the next view`: az utolsó képkocka képváltozása osztva a **használt küszöbbel** - az előbeállítás kezdeti értéke az első 30 képkockánál, utána az adaptált ([Kulcskockák](reconstruction-capture.md#keyframes)) |
| Állapotsor | a követés állapota, vagy egy rögzítési figyelmeztetés (lent) |
| Méretsor | `Size: ...`, hogyan lett rögzítve a pálya léptéke, vagy miért nem ([Lépték](reconstruction-pose.md#scale)) |
| Statisztikasor | `views  frames  dropped  depth-per-second  seconds`, és rekonstrukció közben `placed  cells  % well seen  metres`, valamint `recovered` és `loops closed`, ha bármelyik nem nulla |
| Gyorsbillentyű-sor | a regisztrált billentyűk, vagy hogy miért nem lehetett regisztrálni őket |
| Tippsor (sárga) | élő tanács (lent), a szkennelés végső üzenete és a jelölések |

### A lefedettségi térkép {#the-coverage-map}

Minden 900 ms-ban újrarajzolva, háttérszálon (sosem a felületi szálon), 200 x 200 cellában, 420 px-re skálázva:

- a lefedettségi rács minden oszlopa a **legjobb** megfigyelési minőséget veszi benne (így egy jól látott padlót nem fest sárgára egy rosszul látott mennyezet fölötte);
- a skála pirostól (rossz) - sárgán át (vékony) - sárgáig (elfogadható) - zöldig (jó) fut;
- a soha meg nem figyelt cellák egy külön sötétszürke színt kapnak, hogy egy fel nem fedezett sarok ne látszódjon rosszul szkennelt sarokként;
- a bejárt útvonal egy vékony világos vonal, a jelenlegi pozíció egy fehér pont;
- a gyenge pontok fehér gyűrűk a számukkal;
- a megjelölt pontok sárga négyzetek `M1`, `M2`, … felirattal.

Hogyan számolódik a minőség és a gyenge pontok: [Egyesítés, lefedettség és szín](reconstruction-fusion-and-texture.md#coverage).

### A követési állapotsor {#the-health-line}

| Követési állapot (elhelyezett képkockák / képkockák) | Szöveg | Szín |
|---|---|---|
| még nincs képkocka | Waiting for the first frame. | szürke |
| 90% vagy több | Tracking well — N of M frames placed. | zöld |
| 60% vagy több | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | sárga |
| 60% alatt | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | piros |

A lefedettségi rács egy rögzítési figyelmeztetése ezt helyettesíti (piros, ha a szkennelés rekonstruálhatatlannak ítéltetik, egyébként sárga): szinte nincs parallaxis, minden 25 m-nél távolabbról látszik, vagy vékony a parallaxis. Lásd [Lefedettség](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### A tippsor {#the-hint-line}

| Feltétel | Tipp |
|---|---|
| a képkockák több mint fele kimaradt, 6 másodperc után | Lemaradás - N képkocka kimaradt ... Próbáld a Vázlat minőséget, vagy durvább felületi részletességet. |
| 8 másodperc után 0,3 megtartott nézetnél kevesebb másodpercenként | Nagyon keveset tartunk meg - lehet, hogy állsz, vagy valami jellegtelent nézel. Oldalra mozogj, ne helyben fordulj. |
| 8 másodperc után másodpercenként 8 megtartott nézetnél több | Sokat tartunk meg. Lassíts egy kicsit a tisztább geometriáért. |
| a szkennelés véget ért | a munkamenet üzenete: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, vagy `failed: <error>` |

## Gyorsbillentyűk {#hotkeys}

A Windows regisztrálja őket (`RegisterHotKey`), így a játék fókuszában is működnek. A teljes képernyős játékból való kialt-tabulás pontosan az, ami tönkreteszi a rögzítést.

| Billentyűk | Művelet |
|---|---|
| **Ctrl+Alt+F9** | Szkennelés indítása / leállítása |
| **Ctrl+Alt+F10** | Ezt a helyet jelöld meg, hogy visszatérj (szkennelés közben) |
| **Ctrl+Alt+F11** | A fedvény mutatása / elrejtése (átkapcsolja a „Visszajelzés a játék fölött” jelölőnégyzetet) |

- Az ablak megnyitásakor regisztrálódnak, bezáráskor felszabadulnak. Amíg regisztrálva vannak, ezeket a billentyűkombinációkat minden más program elveszi, a játék is. A két módosítós F-billentyűket azért választották, mert a játékok ritkán kötik őket.
- Az automatikus ismétlés el van nyomva (`MOD_NOREPEAT`), így a billentyű nyomva tartása nem kapcsolja a szkennelést tucatszor.
- Egy billentyűt, amelyet már egy másik program tart, jelez (`... unavailable: another program already has this key`), a többi továbbra is működik. Egy gomb csak olyan billentyűt hirdet, amely ténylegesen regisztrálódott.
- A billentyűk a kódban rögzítettek (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); az elemző az F1-F12-t fogadja el a `ctrl`, `alt` és `shift` módosítókkal. Windowson kívül nincsenek globális gyorsbillentyűk, és az ablak ezt megmondja.
- A **Jelölés** rögzíti a jelenlegi kamerapozíciót (az utolsó elhelyezett képkockáét), és azt írja ki: „Marked MN. Marked spots are on the map and saved with the level.” Mielőtt bármelyik képkocka elhelyezésre került volna, azt írja: nincs hova jelölni. A megjelölt pontok sárga négyzetekként `M1`, `M2`, … felirattal jelennek meg az ablak térképén és a fedvényen, a gyenge pontok alatt vannak felsorolva, a fedvény statisztikasorában számolódnak, és a pályával együtt mentődnek (lent).

## A fedvény {#the-overlay}

Egy kis panel, a játék fölé rögzítve, hogy a visszajelzés ott legyen, ahol a szemed már van.

- Keret nélküli, mindig felül, eszközablak (nincs a tálcán vagy az alt-tab-ban), a Qt-ban átlátszó a bemenetre, a Windowsban átkattintható (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), így a játéknak szánt kattintást soha nem nyeli el. Fókusz nélkül jelenik meg.
- Az elsődleges képernyő jobb felső sarkában, 18 px-re a szélektől; 214 x 358 px.
- Akkor nyílik meg, amikor a szkennelés elindul (ha a „Visszajelzés a játék fölött” be van kapcsolva), és amikor leáll, bezárul.
- **Szegélyezett ablakos módot igényel**: semmi nem rajzolhat a kizárólagos teljes képernyő fölé - sem ez, sem a Steam fedvénye, sem a Discordé.

Felülről lefelé ezt mutatja:

| Elem | Tartalom |
|---|---|
| Lefedettségi térkép | 190 px, ugyanaz a térkép, mint az ablakban, 120 x 120-as, durvább felbontásban, az útvonallal, a gyenge pontok gyűrűivel és a megjelölt pontokkal |
| Állapot | ugyanaz a szöveg és szín, mint az ablak állapotsorában |
| Statisztika | `N placed · M to revisit · X m`, és `· K marked`, ha van jelölés |
| **mozgás** sáv | ugyanaz, mint az ablak séta-sebesség sávja: az utolsó képkocka képváltozása a használt küszöbön, teljes, ha a következő képkocka megmarad |
| **élesség** sáv | az élesség a rögzítés saját mediánjához képest: zöld 0,75-tól, sárga 0,45-től, piros alatta |
| Tanács | egy utasítás, zöld / sárga / piros (félkövér, ha nem „ok”) - lásd [a képkockák minősége](reconstruction-capture.md#frame-quality-and-advice) |
| Gyorsbillentyűk | a regisztrált billentyűk |

Ha a fedvény frissítése valaha kivételt dob, egy piros **„Feedback stopped”** panelre vált, amely azt mondja, hogy minden korábban mutatott adat elavult, a szkennelés még fut, és a főablak továbbra is helyes, hibával és számlálóval együtt. Egy zöldnek fagyott panel különben megerősítésként olvasódna.

## Mentés {#saving}

A **Pálya mentése…** a rekonstrukciót `.glb`-ként írja (lásd [A .glb kimenet](glb-output.md)). Ha a térfogat nem ad felületet, a „Nothing to save” megmagyarázza, hogy a követés valószínűleg a szkennelés nagy részében elveszett. Sikerben: „Written to <path> ... Load it in 3DHeat through the Level panel.” - ezt a 3DHeat-ben a **Háttér / pálya** panelen át töltsd be -, és megnevezi a jelölésfájlt is, ha vannak megjelölt pontok.

A megjelölt pontokat a pálya mellé **`<name>.marks.json`** néven írja:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

A `position` a pálya saját koordinátáiban van (a GLB léptéke alkalmazva, így egy jelölés ott ül a hálón, ahol készült), a `metres` méterben; a `number` megfelel az ablakban látható `M1`, `M2`, … számoknak. Ha a léptéket egy későbbi kulcskockán találták meg ([Lépték](reconstruction-pose.md#scale)), mindkettő tartalmazza ezt a tényezőt.

A szkennelés leállítása megtartja, ami összegyűlt; egy új **Indítás** eldobja az előző szkennelést. **Az ablak bezárása nem kérdez mentésről**: leállítja a szkennelést, felszabadítja a gyorsbillentyűket, és bezárja a fedvényt.
