---
title: "Prozor skeniranja"
nav_order: 1
lang: "hr"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Prozor skeniranja {#the-scan-window}

```bash
python -m heat3d_capture.ui        # ili dvostruki klik na scan.bat
```

Kod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Prozor je tanki prikaz nad `scan/session.py` i `scan/reconstruct.py`; ne posjeduje nikakvu logiku
skeniranja ni geometrije.

## Pokretanje {#starting-up}

1. **Provjera ažuriranja** - vidi [Ažuriranja](updates.md).
2. **Provjera ovisnosti** - svaki paket koji skener treba provjerava se prije bilo kakvog uvoza;
   nedostajući se navode s time čemu služe i veličinom preuzimanja, a instaliraju se tek nakon
   "Download and install". Odustajanje izlazi bez ikakvih promjena. Vidi
   [Izvođenje i ovisnosti](runtime.md#first-run-preflight).
3. **Prozor** - "3DHeat — Level scanner", 1420 x 900, Qt-ov Fusion stil.
4. **Provjera hardvera** - odabire se najbolji backend za zaključivanje, učitava se model dubine i mjeri
   mu se brzina na 6 kadrova; okvir s presudom u gornjem lijevom kutu kaže kakvo će skeniranje biti (vidi
   [Izvođenje](runtime.md#what-to-expect-from-this-machine)).
5. **Globalne tipkovnice** registriraju se na kraju.

### Kad još nema modela dubine {#when-there-is-no-depth-model-yet}

Ako `models/` ne sadrži nijedan `depth-*.onnx`, presuda glasi **"One more thing to set up."**, Start je
onemogućen i pojavljuje se gumb **Set up the depth model**. On:

- provjerava PyTorch, `transformers` i `onnxscript` (ukupno oko 945 MB) i pita prije instalacije;
- pokreće `tools/export_onnx.py --size small` kao zaseban proces (da PyTorch nikad ne ostane u memoriji
  skenera), s ograničenjem od 30 minuta. Prozor se za to vrijeme ne odaziva;
- po uspjehu ponovno pokreće provjeru hardvera; po neuspjehu prikazuje zadnjih 600 znakova ispisa
  pretvarača.

Kad je prisutno više modela, izbor je **prema licenci, a ne prema nazivu datoteke**: `depth-small-*`
(Apache-2.0, komercijalna upotreba dopuštena) kad god postoji, zatim Base, pa Large (oba nekomercijalna).
Okvir s presudom i sivi redak ispod gumba navode datoteku u upotrebi, njezinu licencu i sve druge
prisutne datoteke modela koje se ne koriste - na primjer `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Za skeniranje s Base, premjestite Small datoteku iz `models/`.

## Lijevi stupac: postavke {#left-column-settings}

| Skupina | Kontrola | Zadano | Raspon / vrijednosti | Što radi |
|---|---|---|---|---|
| (vrh) | Okvir s presudom | "Checking your graphics card…" | obojen zeleno, žuto ili crveno prema razredu | Naslov, `<device> via <API> — N views per second`, jedna napomena i `Depth model: <file> (<licence>)` |
| Što skenirati | Izvor | Cijeli ekran | Cijeli ekran, Prozor, Video datoteka | Odakle dolaze kadrovi |
| | Koji | `1` | broj monitora / naslov prozora / putanja do videa | `monitor:<n>`, `window:<title>`, ili putanja datoteke |
| | Choose file… | prikazano za video | `*.mp4 *.mkv *.avi *.mov` | Popunjava putanju |
| Koliko pažljivo | Postavka | Balanced | Draft, Balanced, Detailed | Razlučivost snimanja i koliko je odabir ključnih kadrova selektivan (dolje); pod njom se prikazuje sažetak u jednom retku |
| | Igrino vidno polje | 90° | 30-140° | Igrino **vodoravno** vidno polje. Preusko, i razina se rekonstruira dublje nego što jest; preširoko, i spljošti se. Vozačke igre su bliže 65° |
| | Detalj površine | 0,25 m | 0,05-2,0 m, korak 0,05 | Veličina voksela površine. Manje je finije i teže |
| Zaustavi nakon | Vrijeme | bez ograničenja | 0-120 min | Završava skeniranje nakon toliko vremena (0 = bez ograničenja) |
| | Zadržani pogledi | 3000 | 0-100 000 | Završava skeniranje nakon toliko ključnih kadrova, kao zaštita memorije (0 = bez ograničenja) |
| Što ignorirati | Ignoriraj HUD i sve na kameri | uključeno | | Uči i maskira HUD, nišan, oružje, haubu, kokpit ([Snimanje](reconstruction-capture.md#what-is-not-the-world)). Redak ispod kaže što detektor trenutačno odlučuje |
| Dok igraš | Prikaži povratnu informaciju preko igre | uključeno | | Otvara prozirni prekrivni sloj koji ne hvata klikove tijekom skeniranja. Savjet ispod: pokrenite igru u **bezrubom prozorskom načinu**; izvorni cijeli zaslon ne može prekriti ništa |
| Telemetrija utrke (Forza) | Slušaj podatke o položaju | isključeno | | Uzima putanju kamere iz Forzina Data Out umjesto da je procjenjuje ([Položaj](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Port Data Out |
| | (redak statusa) | | | `N packets — poses come from the game, not from the picture`, ili `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Pokreće ili zaustavlja; prikazuje tipku kad je registrirana |
| | **Set up the depth model** | skriveno | | Vidi gore |
| | **Save level…** | onemogućeno | | Omogućeno nakon skeniranja koje je dalo površinske voksele; traži naziv datoteke (zadano `scan.glb`) |
| | (sivi redak) | | | `Model: <file> (<licence>) · Available: <backends>`, plus napomene o postavljanju, poput instaliranja `onnxruntime-gpu` |

### Postavke {#the-presets}

| Postavka | Dužina najdulje strane snimke | Zadržani kvantil | Početni prag | Prikazani sažetak |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Brzo i grubo. Dobro za provjeru rute prije pravog skeniranja. |
| Balanced | 960 px | 0,65 | 0,010 | Uobičajen izbor. Hodajte normalnim tempom. |
| Detailed | 1280 px | 0,40 | 0,004 | Sporo i temeljito. Hodajte namjerno i okrećite se blago. |

Zadržani kvantil znači "zadrži kadar kad se promijenio više od ovog kvantila promjena zadnjih 240
kadrova" - Draft zadržava otprilike najzauzetijih 15%, Detailed najzauzetijih 60%. Vidi
[Ključni kadrovi](reconstruction-capture.md#keyframes).

### Postavke koje su u prozoru fiksne {#settings-that-are-fixed-in-the-window}

Prozor uvijek rekonstruira dok skenira, koristi visinu kamere od **1,15 m** za mjerilo ravnine tla
(hodačka vrijednost 1,70 m nije izabrana), i prepušta lancu backenda izbor GPU-a. To su `ScanSettings`
polja (`camera_height`, `prefer_backend`) koja samo skripta može promijeniti.

## Desni stupac: što skeniranje radi {#right-column-what-the-scan-is-doing}

| Element | Prikazuje |
|---|---|
| **What the camera sees** | zadnji ključni kadar |
| **Shape it is reading** | njegova predviđena dubina, obojena Turbo mapom boja, normalizirana između 2. i 98. percentila tog kadra (da jedan piksel neba ne sravni raspon) |
| **Coverage — where you have been, and how well** | pogled odozgo (dolje) |
| **Worth another look** | slaba mjesta, numerirana da odgovaraju prstenovima na karti, svako s uputom; najgora (najveća) prva, najviše 8; zatim mjesta koja ste označili (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Traka brzine hoda | `walk speed — N% of the way to the next view`: promjena slike zadnjeg kadra podijeljena s **pragom u upotrebi** - početnom vrijednošću postavke za prvih 30 kadrova, prilagođenom poslije ([Ključni kadrovi](reconstruction-capture.md#keyframes)) |
| Redak zdravlja | zdravlje praćenja, ili upozorenje o snimanju (dolje) |
| Redak veličine | `Size: ...`, kako je mjerilo razine određeno ili zašto nije ([Mjerilo](reconstruction-pose.md#scale)) |
| Redak statistike | `views  frames  dropped  depth-per-second  seconds`, a dok se rekonstruira `placed  cells  % well seen  metres`, plus `recovered` i `loops closed` kad je koji različit od nule |
| Redak tipki | registrirane tipke, ili zašto nisu mogle biti registrirane |
| Redak savjeta (žuto) | savjeti uživo (dolje), završna poruka skeniranja i oznake |

### Karta pokrivenosti {#the-coverage-map}

Iscrtava se svakih 900 ms u pozadinskoj niti (nikad u niti sučelja), na 200 x 200 ćelija,
skalirano na 420 px:

- svaki stupac mreže pokrivenosti uzima **najbolju** kvalitetu opažanja u njemu (tako da dobro
  viđen pod nije obojen žuto zbog loše viđenog stropa iznad njega);
- ljestvica ide od crvene (loše) - žute (tanko) - žućkaste (prihvatljivo) - zelene (dobro);
- nikad opažene ćelije su posebna tamnosiva boja, tako da nepoznati kut ne izgleda kao loše skeniran;
- prijeđeni put crta se tankom svijetlom linijom, trenutačni položaj bijelom točkom;
- slaba mjesta su bijeli prstenovi s brojem;
- mjesta koja ste označili su jantarni kvadrati s oznakom `M1`, `M2`, …

Kako se računaju kvaliteta i slaba mjesta: [Spajanje, pokrivenost i boja](reconstruction-fusion-and-texture.md#coverage).

### Redak zdravlja {#the-health-line}

| Zdravlje praćenja (smješteni kadrovi / kadrovi) | Tekst | Boja |
|---|---|---|
| još nema kadrova | Waiting for the first frame. | siva |
| 90% ili više | Tracking well — N of M frames placed. | zelena |
| 60% ili više | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | žuta |
| ispod 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | crvena |

Upozorenje o snimanju iz mreže pokrivenosti zamjenjuje ga (crveno kad se skeniranje ocijeni kao
nerekonstruktivno, inače žuto): gotovo nikakva paralaksa, sve viđeno s više od 25 m, ili tanak
paralaksa. Vidi [Pokrivenost](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Redak savjeta {#the-hint-line}

| Uvjet | Savjet |
|---|---|
| više od polovice kadrova odbačeno, nakon 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| manje od 0,3 zadržanih pogleda u sekundi, nakon 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| više od 8 zadržanih pogleda u sekundi, nakon 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skeniranje završeno | poruka sesije: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, ili `failed: <error>` |

## Tipkovnice {#hotkeys}

Registrirane kod Windowsa (`RegisterHotKey`), pa rade dok igra ima fokus. Alt-tab iz cijelog zaslona
igre upravo je ono što kvari snimanje.

| Tipke | Radnja |
|---|---|
| **Ctrl+Alt+F9** | Pokreni / zaustavi skeniranje |
| **Ctrl+Alt+F10** | Označi ovo mjesto za ponovni posjet (tijekom skeniranja) |
| **Ctrl+Alt+F11** | Prikaži / sakrij prekrivni sloj (prebacuje okvir "Show feedback over the game") |

- Registriraju se jednom, kad se prozor otvori, i otpuštaju kad se zatvori; dok su registrirane, te
  kombinacije tipki oduzete su svakom drugom programu, uključujući igru. F-tipke s dva modifikatora su
  odabrane jer igre rijetko vežu takve.
- Automatsko ponavljanje je potisnuto (`MOD_NOREPEAT`), pa držanje tipke ne prebacuje skeniranje
  desetak puta.
- Tipku koju je već držao neki drugi program prijavljuje se (`... unavailable: another program already
  has this key`), a ostale i dalje rade. Gumb oglašava tipku samo ako je zaista registrirana.
- Tipke su fiksne u kodu (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); parser prihvaća F1-F12 s
  `ctrl`, `alt` i `shift`. Izvan Windowsa nema globalnih tipkovnica i prozor to kaže.
- **Mark** bilježi trenutačni položaj kamere (zadnjeg smještenog kadra); prikazuje "Marked MN. Marked
  spots are on the map and saved with the level." Prije nego je ijedan kadar smješten kaže da nema gdje
  označiti. Označena mjesta crtaju se na karti prozora i prekrivnog sloja kao jantarni kvadrati s oznakom
  `M1`, `M2`, …, navode se pod slabim mjestima, broje se u retku statistike prekrivnog sloja i spremaju s
  razinom (dolje).

## Prekrivni sloj {#the-overlay}

Mala ploča pričvršćena preko igre, da povratna informacija bude tamo gdje su oči već.

- Bez okvira, uvijek na vrhu, prozor alata (nije na traci zadataka niti u alt-tabu), prozirna za unos
  u Qt-u i učinjena prozirnom za klikove u Windowsu (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), tako da klik
  namijenjen igri nikad nije progutan. Prikazuje se bez preuzimanja fokusa.
- Gornji desni kut primarnog zaslona, 18 px od rubova; 214 x 358 px.
- Otvara se kad skeniranje počne (ako je "Show feedback over the game" uključeno), zatvara se kad stane.
- **Treba bezrubi prozorski način**: ništa ne može crtati preko izvornog cijelog zaslona - ni ovo, ni
  Steamov overlay, ni Discord.

Od vrha prema dnu prikazuje:

| Element | Sadržaj |
|---|---|
| Karta pokrivenosti | 190 px, ista karta kao u prozoru, ali grublje, 120 x 120, s putem, prstenovima slabih mjesta i označenim mjestima |
| Zdravlje | isti tekst i boja kao redak zdravlja u prozoru |
| Statistika | `N placed · M to revisit · X m`, s `· K marked` kad ih ima |
| Traka **pokreta** | ista kao traka brzine hoda u prozoru: promjena slike zadnjeg kadra preko praga u upotrebi, puna kad će se sljedeći kadar zadržati |
| Traka **oštrine** | oštrina u odnosu na vlastitu medijanu snimanja: zelena od 0,75, žuta od 0,45, crvena ispod |
| Savjet | jedna uputa, zelena / žuta / crvena (podebljana kad nije "ok") - vidi [kvaliteta kadra](reconstruction-capture.md#frame-quality-and-advice) |
| Tipke | registrirane tipke |

Ako ažuriranje prekrivnog sloja ikad baci iznimku, prelazi na crvenu ploču **"Feedback stopped"** koja
kaže da je sve prikazano prije zastarjelo, da skeniranje još traje i da je glavni prozor još ispravan, s
greškom i brojem. Ploča koja se smrznula dok je bila zelena inače bi se i dalje čitala kao potvrda.

## Spremanje {#saving}

**Save level…** zapisuje rekonstrukciju kao `.glb` (vidi [`.glb` izlaz](glb-output.md)). Ako volumen ne
daje površinu, "Nothing to save" objašnjava da je praćenje vjerojatno izgubljeno za većinu skeniranja.
Pri uspjehu: "Written to <path> ... Load it in 3DHeat through the Level panel.", uz navođenje datoteke
oznaka ako postoje označena mjesta.

Označena mjesta zapisuju se uz razinu kao **`<name>.marks.json`**:

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

`position` je u vlastitim koordinatama razine (primijenjeno mjerilo GLB-a, pa oznaka sjedi na mreži nad
kojom je napravljena), `metres` u metrima; `number` odgovara `M1`, `M2`, … u prozoru. Kad je mjerilo
nađeno na kasnijem ključnom kadru ([Mjerilo](reconstruction-pose.md#scale)), oba uključuju taj faktor.

Zaustavljanje skeniranja zadržava ono što je prikupljeno; novi **Start** odbacuje prethodno skeniranje.
**Zatvaranje prozora ne pita za spremanje**: zaustavlja skeniranje, otpušta tipkovnice i zatvara
prekrivni sloj.
