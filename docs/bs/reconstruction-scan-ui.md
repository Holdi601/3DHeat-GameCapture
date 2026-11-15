---
title: "Prozor za skeniranje"
nav_order: 1
lang: "bs"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Prozor za skeniranje {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Prozor je tanak prikaz nad `scan/session.py` i `scan/reconstruct.py`; ne posjeduje
nikakvu logiku skeniranja ni geometrije.

## Pokretanje {#starting-up}

1. **Provjera ažuriranja** - pogledajte [Ažuriranja](updates.md).
2. **Provjera zavisnosti** - svaki paket koji skener treba provjerava se prije nego što se
   išta uveze; oni koji nedostaju navode se s onim čemu služe i veličinom preuzimanja, i
   instaliraju se tek nakon "Download and install". Cancel izlazi bez ikakve promjene. Pogledajte
   [Runtime i zavisnosti](runtime.md#first-run-preflight).
3. **Prozor** - "3DHeat — Level scanner", 1420 x 900, Qt-ov stil Fusion.
4. **Provjera hardvera** - bira se najbolja inferencijska pozadina, učitava se model dubine i
   mjeri mu se propusnost na 6 kadrova; okvir s presudom gore lijevo kaže kakvo će biti skeniranje
   (pogledajte [Runtime](runtime.md#what-to-expect-from-this-machine)).
5. **Globalne prečice** se registruju posljednje.

### Kad još nema modela dubine {#when-there-is-no-depth-model-yet}

Ako `models/` ne sadrži nijedan `depth-*.onnx`, presuda glasi **"One more thing to set up."**, Start
je onemogućen i pojavljuje se dugme **Set up the depth model**. Ono:

- provjerava PyTorch, `transformers` i `onnxscript` (zajedno oko 945 MB) i pita prije
  instalacije;
- pokreće `tools/export_onnx.py --size small` kao poseban proces (da PyTorch nikad ne ostane u
  memoriji skenera), s ograničenjem od 30 minuta. Prozor ne reaguje dok radi;
- po uspjehu ponovo pokreće provjeru hardvera; po neuspjehu prikazuje posljednjih 600 znakova
  izlaza pretvarača.

Kad je prisutno više modela, izbor je **po licenci, a ne po nazivu datoteke**: `depth-small-*`
(Apache-2.0, komercijalna upotreba dozvoljena) kad god postoji, zatim Base, pa Large (oba
nekomercijalna). Okvir s presudom i siva linija ispod dugmadi navode datoteku koja se koristi, njenu
licencu i sve druge prisutne datoteke modela koje se ne koriste - na primjer `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Da skeniraš s Base, premjesti datoteku Small iz `models/`.

## Lijeva kolona: postavke {#left-column-settings}

| Grupa | Kontrola | Zadano | Raspon / vrijednosti | Šta radi |
|---|---|---|---|---|
| (vrh) | Okvir s presudom | "Checking your graphics card…" | obojen zeleno, žuto ili crveno prema nivou | Naslov, `<device> via <API> — N views per second`, jedna napomena i `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Odakle dolaze kadrovi |
| | Which | `1` | broj monitora / naslov prozora / putanja do videa | `monitor:<n>`, `window:<title>` ili putanja do datoteke |
| | Choose file… | prikazano za video | `*.mp4 *.mkv *.avi *.mov` | Popunjava putanju |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Rezolucija snimanja i koliko je selektivan izbor ključnih kadrova (dolje); jednolinijski sažetak prikazan je ispod |
| | Game field of view | 90° | 30-140° | **Horizontalno** vidno polje igre. Preusko i nivo se rekonstruiše dublji nego što jest; preširoko i spljošti se. Trkaće igre su bliže 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, korak 0.05 | Veličina voksela površine. Manje je finije i teže |
| Stop after | Time | bez ograničenja | 0-120 min | Završava skeniranje nakon ovoliko vremena (0 = bez ograničenja) |
| | Views kept | 3000 | 0-100,000 | Završava skeniranje nakon ovoliko ključnih kadrova, kao zaštita memorije (0 = bez ograničenja) |
| What to ignore | Ignore HUD and anything on the camera | uključeno | | Uči i maskira HUD, nišan, oružje, haubu, kokpit ([Snimanje](reconstruction-capture.md#what-is-not-the-world)). Linija ispod kaže šta detektor trenutno odlučuje |
| While you play | Show feedback over the game | uključeno | | Otvara overlay kroz koji se klika dok traje skeniranje. Savjet ispod: pokrenite igru u **borderless windowed** načinu; ekskluzivni puni ekran ne može se ničim prekriti |
| Racing telemetry (Forza) | Listen for position data | isključeno | | Uzima putanju kamere iz Forza Data Out umjesto da je procjenjuje ([Poza](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Port za Data Out |
| | (linija stanja) | | | `N packets — poses come from the game, not from the picture` ili `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Pokreće ili zaustavlja; prikazuje prečicu kad je registrovana |
| | **Set up the depth model** | skriveno | | Pogledajte gore |
| | **Save level…** | onemogućeno | | Omogućeno nakon skeniranja koje je dalo voksele površine; traži naziv datoteke (zadano `scan.glb`) |
| | (siva linija) | | | `Model: <file> (<licence>) · Available: <backends>`, plus napomene o postavljanju poput instalacije `onnxruntime-gpu` |

### Predpodešenja {#the-presets}

| Predpodešenje | Najduža strana snimanja | Kvantil zadržavanja | Početni prag | Prikazani sažetak |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Brzo i grubo. Dobro za provjeru rute prije pravog skeniranja. |
| Balanced | 960 px | 0.65 | 0.010 | Uobičajen izbor. Hodajte normalnim tempom. |
| Detailed | 1280 px | 0.40 | 0.004 | Sporo i temeljito. Hodajte promišljeno i okrećite se blago. |

Kvantil zadržavanja znači "zadrži kadar kad se promijenio više od ovog kvantila promjena
posljednjih 240 kadrova" - Draft zadržava otprilike najživljih 15%, Detailed najživljih 60%. Pogledajte
[Ključni kadrovi](reconstruction-capture.md#keyframes).

### Postavke koje su u prozoru fiksne {#settings-that-are-fixed-in-the-window}

Prozor uvijek rekonstruiše tokom skeniranja, koristi visinu kamere od **1,15 m** za
razmjeru ravni tla (vrijednost za hodanje 1,70 m ne može se izabrati) i prepušta ljestvici pozadina
izbor GPU-a. To su polja `ScanSettings` (`camera_height`, `prefer_backend`) koja može promijeniti samo
skripta.

## Desna kolona: šta skeniranje radi {#right-column-what-the-scan-is-doing}

| Element | Prikazuje |
|---|---|
| **What the camera sees** | posljednji ključni kadar |
| **Shape it is reading** | njegovu predviđenu dubinu, obojenu mapom boja Turbo, normaliziranu između 2. i 98. percentila tog kadra (da jedan piksel neba ne spljošti raspon) |
| **Coverage — where you have been, and how well** | prikaz plana odozgo (pogledajte dolje) |
| **Worth another look** | slabe tačke, numerisane da odgovaraju prstenovima na mapi, svaka s uputom; najgora (najveća) prva, najviše 8; zatim tačke koje ste označili (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Traka brzine hoda | `walk speed — N% of the way to the next view`: promjena slike posljednjeg kadra podijeljena **pragom u upotrebi** - početnom vrijednošću predpodešenja za prvih 30 kadrova, prilagođenom nakon toga ([Ključni kadrovi](reconstruction-capture.md#keyframes)) |
| Linija zdravlja | zdravlje praćenja ili upozorenje snimanja (dolje) |
| Linija veličine | `Size: ...`, kako je razmjera nivoa utvrđena ili zašto nije ([Razmjera](reconstruction-pose.md#scale)) |
| Linija statistike | `views  frames  dropped  depth-per-second  seconds`, a tokom rekonstrukcije `placed  cells  % well seen  metres`, plus `recovered` i `loops closed` kad je bilo koje različito od nule |
| Linija prečica | registrovani tasteri ili zašto nisu mogli biti registrovani |
| Linija savjeta (žuta) | savjet uživo, završna poruka skeniranja i oznake |

### Mapa pokrivenosti {#the-coverage-map}

Iscrtava se svakih 900 ms u pozadinskoj niti (nikad u niti sučelja), sa 200 x 200
ćelija skaliranih na 420 px:

- svaka kolona mreže pokrivenosti uzima **najbolji** kvalitet posmatranja u njoj (tako
  dobro viđen pod nije obojen žuto lošim viđenjem plafona iznad);
- skala ide od crvene (loše) preko žute (slabo) i žute (prihvatljivo) do zelene (dobro);
- ćelije koje nikad nisu posmatrane su posebna tamno siva, pa neistražen ćošak ne izgleda kao
  loše skeniran;
- pređeni put crta se tankom svijetlom linijom, trenutna pozicija bijelom tačkom;
- slabe tačke su bijeli prstenovi s brojem;
- tačke koje ste označili su žuti kvadrati s oznakama `M1`, `M2`, …

Kako se računaju kvalitet i slabe tačke: [Fuzija, pokrivenost i boja](reconstruction-fusion-and-texture.md#coverage).

### Linija zdravlja {#the-health-line}

| Zdravlje praćenja (smješteni kadrovi / kadrovi) | Tekst | Boja |
|---|---|---|
| još nema kadrova | Waiting for the first frame. | siva |
| 90% ili više | Tracking well — N of M frames placed. | zelena |
| 60% ili više | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | žuta |
| ispod 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | crvena |

Upozorenje snimanja iz mreže pokrivenosti zamjenjuje je (crveno kad se skeniranje ocijeni kao
nerekonstruktibilno, inače žuto): gotovo nikakav paralaks, sve viđeno sa više od 25 m
ili slab paralaks. Pogledajte [Pokrivenost](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Linija savjeta {#the-hint-line}

| Uslov | Savjet |
|---|---|
| više od pola kadrova odbačeno, nakon 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| manje od 0,3 zadržana pogleda u sekundi, nakon 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| više od 8 zadržanih pogleda u sekundi, nakon 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skeniranje završeno | poruka sesije: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` ili `failed: <error>` |

## Prečice {#hotkeys}

Registruju se kod Windowsa (`RegisterHotKey`), pa rade dok igra ima fokus. Alt-tab
iz igre preko punog ekrana je upravo ono što kvari snimanje.

| Tasteri | Radnja |
|---|---|
| **Ctrl+Alt+F9** | Pokrenite / zaustavite skeniranje |
| **Ctrl+Alt+F10** | Označite ovu tačku za ponovni obilazak (tokom skeniranja) |
| **Ctrl+Alt+F11** | Prikažite / sakrijte overlay (prebacuje polje "Show feedback over the game") |

- Registruju se jednom, kad se prozor otvori, a oslobađaju kad se zatvori; dok su
  registrovane, ove kombinacije tastera oduzete su svakom drugom programu, uključujući
  igru. F-tasteri s dva modifikatora izabrani su jer ih igre rijetko koriste.
- Automatsko ponavljanje je potisnuto (`MOD_NOREPEAT`), pa držanje tastera ne prebacuje skeniranje
  desetinama puta.
- Taster koji već drži drugi program se prijavljuje (`... unavailable: another program already
  has this key`), a ostali i dalje rade. Dugme oglašava samo taster koji je zaista
  registrovan.
- Tasteri su fiksirani u kodu (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); parser
  prihvata F1-F12 s `ctrl`, `alt` i `shift`. Izvan Windowsa nema globalnih prečica
  i prozor to kaže.
- **Mark** bilježi trenutnu poziciju kamere (posljednjeg smještenog kadra) i prikazuje "Marked MN.
  Marked spots are on the map and saved with the level." Prije nego što je ijedan kadar smješten,
  kaže da nema gdje označiti. Označene tačke crtaju se na mapi prozora i overlaya kao
  žuti kvadrati s oznakama `M1`, `M2`, …, navedene su ispod slabih tačaka, ubrojane su u liniju
  statistike overlaya i spremaju se s nivoom (dolje).

## Overlay {#the-overlay}

Mali panel prikvačen preko igre da povratna informacija bude tamo gdje su oči već usmjerene.

- Bez okvira, uvijek na vrhu, prozor alata (nije u traci zadataka ni u alt-tabu), proziran za
  unos u Qt-u i s klikom kroz njega u Windowsu (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), pa
  klik namijenjen igri nikad nije progutan. Prikazuje se bez preuzimanja fokusa.
- Gornji desni ugao primarnog ekrana, 18 px od ivica; 214 x 358 px.
- Otvara se kad skeniranje počne (ako je "Show feedback over the game" uključeno), zatvara kad stane.
- **Treba borderless windowed način**: ništa ne može crtati preko ekskluzivnog punog ekrana - ni ovo,
  ni Steamov overlay, ni Discordov.

Odozgo prema dolje prikazuje:

| Element | Sadržaj |
|---|---|
| Mapa pokrivenosti | 190 px, ista mapa kao u prozoru u grubljih 120 x 120, s putanjom, prstenovima slabih tačaka i označenim tačkama |
| Zdravlje | isti tekst i boja kao linija zdravlja u prozoru |
| Statistika | `N placed · M to revisit · X m`, s `· K marked` kad ih ima |
| Traka **movement** | ista kao traka brzine hoda u prozoru: promjena slike posljednjeg kadra nad pragom u upotrebi, puna kad će sljedeći kadar biti zadržan |
| Traka **sharpness** | oštrina u odnosu na medijan ovog snimanja: zelena od 0,75, žuta od 0,45, crvena ispod |
| Savjet | jedna uputa, zelena / žuta / crvena (podebljana kad nije "ok") - pogledajte [kvalitet kadra](reconstruction-capture.md#frame-quality-and-advice) |
| Prečice | registrovani tasteri |

Ako ažuriranje overlaya ikad baci grešku, prelazi na crveni panel **"Feedback stopped"** koji kaže
da je sve prikazano ranije zastarjelo, da skeniranje i dalje radi, a glavni prozor
je i dalje tačan, s greškom i brojačem. Panel koji se zamrzne dok je zelen inače bi
i dalje izgledao kao potvrda.

## Spremanje {#saving}

**Save level…** zapisuje rekonstrukciju kao `.glb` (pogledajte [Izlaz .glb](glb-output.md)).
Ako volumen ne daje površinu, "Nothing to save" objašnjava da je praćenje vjerovatno izgubljeno
veći dio skeniranja. Po uspjehu: "Written to <path> ... Load it in 3DHeat through the Level
panel.", a navodi i datoteku oznaka kad ima označenih tačaka.

Označene tačke zapisuju se pored nivoa kao **`<name>.marks.json`**:

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

`position` je u vlastitim koordinatama nivoa (primijenjena razmjera GLB-a, pa oznaka leži na mreži
nad kojom je napravljena), `metres` u metrima; `number` odgovara `M1`, `M2`, … u prozoru. Kad je
razmjera pronađena na kasnijem ključnom kadru ([Razmjera](reconstruction-pose.md#scale)), oba uključuju taj
faktor.

Zaustavljanje skeniranja zadržava ono što je prikupljeno; novi **Start** odbacuje prethodno skeniranje.
**Zatvaranje prozora ne pita za spremanje**: zaustavlja skeniranje, oslobađa prečice i
zatvara overlay.
