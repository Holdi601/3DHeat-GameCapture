---
title: "Okno za pregled"
nav_order: 1
lang: "sl"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Okno za pregled {#the-scan-window}

```bash
python -m heat3d_capture.ui        # ali dvokliknite scan.bat
```

Koda: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Okno je tanek pogled na `scan/session.py` in `scan/reconstruct.py`; nima lastne logike skeniranja ali
geometrije.

## Zagon {#starting-up}

1. **Preverjanje posodobitev** - glejte [Posodobitve](updates.md).
2. **Preverjanje odvisnosti** - preveri se vsak paket, ki ga skener potrebuje, preden se kaj uvozi;
   manjkajoči se izpišejo z opisom, čemu služijo, in velikostjo prenosa, namestijo pa se šele po
   kliku na "Download and install". Cancel izstopi, ne da bi kaj spremenil. Glejte
   [Izvajanje in odvisnosti](runtime.md#first-run-preflight).
3. **Okno** - "3DHeat — Level scanner", 1420 x 900, Qt-jev slog Fusion.
4. **Preverjanje strojne opreme** - izbere se najboljši pogonski sistem za sklepanje, globinski model se
   naloži, njegova hitrost se izmeri na 6 okvirjih; okvirček z oceno v zgornjem levem kotu pove, kakšno
   bo skeniranje (glejte [Izvajanje](runtime.md#what-to-expect-from-this-machine)).
5. **Globalne bližnjice** se registrirajo zadnje.

### Ko globinskega modela še ni {#when-there-is-no-depth-model-yet}

Če `models/` nima nobene datoteke `depth-*.onnx`, okvirček piše **"One more thing to set up."**, gumb
Start je onemogočen, pojavi pa se gumb **Set up the depth model**. Ta:

- preveri PyTorch, `transformers` in `onnxscript` (skupaj približno 945 MB) in pred namestitvijo vpraša;
- zažene `tools/export_onnx.py --size small` kot ločen proces (da PyTorch nikoli ne ostane v pomnilniku
  skenerja), z omejitvijo 30 minut. Okno med delovanjem ne odgovarja;
- ob uspehu ponovno zažene preverjanje strojne opreme; ob neuspehu pokaže zadnjih 600 znakov izpisa
  pretvornika.

Če je prisotnih več modelov, se izbira po **licenci, ne po imenu datoteke**: `depth-small-*`
(Apache-2.0, komercialna uporaba dovoljena) kadarkoli obstaja, nato Base, nato Large (oba nekomercialna).
Okvirček in siva vrstica pod gumbi imenujeta uporabljeno datoteko, njeno licenco in vse druge prisotne,
a neuporabljene datoteke modelov - na primer `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Za skeniranje z Base premaknite datoteko Small iz `models/`.

## Levi stolpec: nastavitve {#left-column-settings}

| Skupina | Kontrola | Privzeto | Razpon / vrednosti | Kaj naredi |
|---|---|---|---|---|
| (zgoraj) | Okvirček z oceno | "Checking your graphics card…" | obarvan zeleno, rumeno ali rdeče glede na stopnjo | Naslov, `<device> via <API> — N views per second`, ena opomba in `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Od kod prihajajo okvirji |
| | Which | `1` | številka monitorja / naslov okna / pot do videa | `monitor:<n>`, `window:<title>` ali pot do datoteke |
| | Choose file… | prikazano za video | `*.mp4 *.mkv *.avi *.mov` | Vpiše pot |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Ločljivost zajema in kako strogo se izbirajo ključni okvirji (spodaj); pod njim je prikazan povzetek v eni vrstici |
| | Game field of view | 90° | 30-140° | **Vodoravno** vidno polje igre. Preozko in nivo se rekonstruira globlje, kot je; preširoko jo sploti. Dirkalne igre so bližje 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, korak 0.05 | Velikost voksla površine. Manjše je natančneje in težje |
| Stop after | Time | brez omejitve | 0-120 min | Konča skeniranje po tolikšnem času (0 = brez omejitve) |
| | Views kept | 3000 | 0-100,000 | Konča skeniranje po tolikšnem številu ključnih okvirjev, kot varovalo pomnilnika (0 = brez omejitve) |
| What to ignore | Ignore HUD and anything on the camera | vklopljeno | | Nauči se in prekrije HUD, tarčo, orožje, pokrov motorja, kabino ([Zajem](reconstruction-capture.md#what-is-not-the-world)). Vrstica pod tem pove, kaj zaznavanje trenutno odloča |
| While you play | Show feedback over the game | vklopljeno | | Med skeniranjem odpre prosojno prekrivanje, ki ne prestreže klikov. Namig pod njim: zaženite igro v **borderless windowed** načinu; ekskluzivni celozaslonski način ne more biti prekrit z ničemer |
| Racing telemetry (Forza) | Listen for position data | izključeno | | Vzame pot kamere iz Forza Data Out namesto ocene iz slike ([Poza](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Vrata Data Out |
| | (status line) | | | `N packets — poses come from the game, not from the picture` ali `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Začne ali ustavi; ob registraciji prikaže bližnjico |
| | **Set up the depth model** | skrito | | Glejte zgoraj |
| | **Save level…** | onemogočeno | | Omogočeno po skeniranju, ki je dalo površinske voksle; vpraša za ime datoteke (privzeto `scan.glb`) |
| | (siva vrstica) | | | `Model: <file> (<licence>) · Available: <backends>`, ter opombe o namestitvi, na primer `onnxruntime-gpu` |

### Prednastavitve {#the-presets}

| Prednastavitev | Daljša stranica zajema | Ohranjeni kvantil | Začetni prag | Prikazan povzetek |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Hitro in grobo. Dobro za preverjanje poti pred pravim skeniranjem. |
| Balanced | 960 px | 0.65 | 0.010 | Običajna izbira. Hodite z normalno hitrostjo. |
| Detailed | 1280 px | 0.40 | 0.004 | Počasno in temeljito. Hodite namerno in se obračajte nežno. |

Ohranjeni kvantil pomeni "ohrani okvir, ko se je spremenil bolj od tega kvantila sprememb zadnjih 240
okvirjev" - Draft ohrani približno najbolj zaposlenih 15 %, Detailed najbolj zaposlenih 60 %. Glejte
[Ključni okvirji](reconstruction-capture.md#keyframes).

### Nastavitve, ki so v oknu fiksne {#settings-that-are-fixed-in-the-window}

Okno med skeniranjem vedno rekonstruira, za merilo nivoja na tleh uporablja višino kamere **1,15 m** (hoja
s 1,70 m ni izbirna) in pusti, da lestev pogonskih sistemov izbere GPU. To so polja `ScanSettings`
(`camera_height`, `prefer_backend`), ki jih lahko spremeni samo skripta.

## Desni stolpec: kaj skeniranje počne {#right-column-what-the-scan-is-doing}

| Element | Prikazuje |
|---|---|
| **What the camera sees** | zadnji ključni okvir |
| **Shape it is reading** | njegovo napovedano globino, obarvano z zemljevidom barv Turbo, normirano med 2. in 98. percentilom tega okvirja (tako da en nebesni piksel ne splošči razpona) |
| **Coverage — where you have been, and how well** | pogled z vrha (glejte spodaj) |
| **Worth another look** | šibka mesta, oštevilčena, da se ujemajo s kolobarji na zemljevidu, vsako z navodilom; najslabše (največje) najprej, največ 8; nato mesta, ki ste jih označili (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Vrstica hitrosti hoje | `walk speed — N% of the way to the next view`: sprememba slike zadnjega okvirja, deljena z **uporabljenim pragom** - začetna vrednost prednastavitve za prvih 30 okvirjev, nato prilagojena ([Ključni okvirji](reconstruction-capture.md#keyframes)) |
| Vrstica zdravja | zdravje sledenja ali opozorilo o zajemu (spodaj) |
| Vrstica velikosti | `Size: ...`, kako je bilo merilo nivoja določeno ali zakaj ni bilo ([Merilo](reconstruction-pose.md#scale)) |
| Statistična vrstica | `views  frames  dropped  depth-per-second  seconds`, med rekonstrukcijo pa `placed  cells  % well seen  metres`, ter `recovered` in `loops closed`, kadar sta kateri koli neničelni |
| Vrstica bližnjic | registrirane tipke ali zakaj jih ni bilo mogoče registrirati |
| Namigovna vrstica (oranžna) | sprotni nasveti (spodaj), končno sporočilo skeniranja in oznake |

### Pokritost {#the-coverage-map}

Prerisuje se na vsakih 900 ms v ozadnji niti (nikoli v vmesniški niti), na 200 x 200 celic, skaliranih na 420 px:

- vsak stolpec mreže pokritosti vzame **najboljšo** kakovost opazovanja v njem (tako dobro vidnega tal
  ne prebarva v oranžno slabo vidni strop nad njim);
- lestvica teče od rdeče (slabo) - oranžne (tanko) - rumene (sprejemljivo) - zelene (dobro);
- nikoli opažene celice so jasno temno sive, da nepreiskan kot ne izgleda kot slabo skeniran;
- pot, po kateri ste hodili, je narisana s tanko svetlo črto, trenutni položaj pa z belo piko;
- šibka mesta so bela kolobarja s številko;
- mesta, ki ste jih označili, so jantarna kvadrata z oznako `M1`, `M2`, …

Kako se izračunajo kakovost in šibka mesta: [Zlivanje, pokritost in barva](reconstruction-fusion-and-texture.md#coverage).

### Vrstica zdravja {#the-health-line}

| Zdravje sledenja (postavljeni okvirji / okvirji) | Besedilo | Barva |
|---|---|---|
| še ni okvirjev | Waiting for the first frame. | siva |
| 90% ali več | Tracking well — N of M frames placed. | zelena |
| 60% ali več | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | oranžna |
| pod 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rdeča |

Opozorilo o zajemu iz mreže pokritosti nadomesti vrstico (rdeče, ko skeniranje ni ocenjeno kot
rekonstruktibilno, sicer oranžno): skoraj nič paralakse, vse vidno z več kot 25 m ali tanka paralaksa.
Glejte [Pokritost](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Namigovna vrstica {#the-hint-line}

| Pogoj | Namig |
|---|---|
| več kot polovica okvirjev izpuščena, po 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| manj kot 0,3 ohranjenih pogledov na sekundo, po 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| več kot 8 ohranjenih pogledov na sekundo, po 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skeniranje se je končalo | sporočilo seje: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` ali `failed: <error>` |

## Bližnjice {#hotkeys}

Registrirane pri Windows (`RegisterHotKey`), zato delujejo, medtem ko ima igra fokus. Preklop z Alt-tab iz
celozaslonske igre je prav to, kar uniči zajem.

| Tipke | Dejanje |
|---|---|
| **Ctrl+Alt+F9** | Začne / ustavi skeniranje |
| **Ctrl+Alt+F10** | Označi to mesto za ponovni obisk (med skeniranjem) |
| **Ctrl+Alt+F11** | Pokaži / skrij prekrivanje (preklopi polje "Show feedback over the game") |

- Registrirane so enkrat, ko se okno odpre, in sprostijo se, ko se zapre; dokler so registrirane, so te
  kombinacije tipk vzete vsakemu drugemu programu, vključno z igro. Tipke F z dvema modifikatorjema so bile
  izbrane, ker igre redko vežejo nanje.
- Samodejno ponavljanje je zatrto (`MOD_NOREPEAT`), zato držanje tipke ne preklopi skeniranja
  desetkrat.
- Tipka, ki jo že drži drug program, je prijavljena (`... unavailable: another program already
  has this key`), ostale pa delujejo. Gumb oglaša tipko samo, če je bila dejansko registrirana.
- Tipke so v kodi fiksne (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); razčlenjevalnik sprejme F1-F12
  s `ctrl`, `alt` in `shift`. Zunaj Windows globalnih bližnjic ni in okno to pove.
- **Mark** zapiše trenutni položaj kamere (zadnjega postavljenega okvirja) in pokaže "Marked MN.
  Marked spots are on the map and saved with the level." Preden je postavljen kakršen koli okvir, pove, da
  ni kam označiti. Označena mesta so narisana na zemljevidu okna in prekrivanja kot jantarni kvadrati z
  oznako `M1`, `M2`, …, naštejejo se pod šibkimi mesti, štejejo se v statistični vrstici prekrivanja in
  shranijo z nivojem (spodaj).

## Prekrivanje {#the-overlay}

Majhna plošča, pripeta čez igro, da je povratna informacija tam, kjer so že oči.

- Brez okvirja, vedno na vrhu, orodno okno (ni v opravilni vrstici ali alt-tab), v vnosu prosojno v Qt in
  naredi se prosojno za klike v Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), tako da klik, namenjen igri,
  nikoli ni pogoltnjen. Pokaže se brez prevzema fokusa.
- Zgornji desni kot primarnega zaslona, 18 px od robov; 214 x 358 px.
- Odpre se, ko se skeniranje začne (če je "Show feedback over the game" vklopljeno), zapre se, ko se ustavi.
- **Potrebuje način borderless windowed**: nič ne more biti narisano čez ekskluzivni celozaslonski način - ne to,
  ne Steamov prekrivni sloj, ne Discord.

Od vrha navzdol prikazuje:

| Element | Vsebina |
|---|---|
| Zemljevid pokritosti | 190 px, isti zemljevid kot v oknu, pri grobljih 120 x 120, s potjo, kolobarji šibkih mest in označenimi mesti |
| Zdravje | isto besedilo in barva kakor vrstica zdravja v oknu |
| Statistika | `N placed · M to revisit · X m`, z `· K marked`, kadar kaj je označeno |
| Vrstica **gibanja** | enaka kakor vrstica hitrosti hoje v oknu: sprememba slike zadnjega okvirja, deljena z uporabljenim pragom, polna, ko bo naslednji okvir ohranjen |
| Vrstica **ostrine** | ostrina glede na lastno mediano tega zajema: zelena od 0,75, oranžna od 0,45, rdeča pod tem |
| Nasvet | ena navodila, zelena / oranžna / rdeča (krepko, kadar ni "ok") - glejte [kakovost okvirja](reconstruction-capture.md#frame-quality-and-advice) |
| Bližnjice | registrirane tipke |

Če posodabljanje prekrivanja kdaj sproži napako, preklopi v rdečo ploščo **"Feedback stopped"**, ki pove, da je
vse, kar je bilo prikazano prej, zastarelo, da skeniranje še teče in da je glavno okno še pravilno, z napako in
številom. Plošča, ki je zamrznila, medtem ko je zelena, bi sicer še naprej brala kot potrditev.

## Shranjevanje {#saving}

**Save level…** zapiše rekonstrukcijo kot `.glb` (glejte [Izhodna datoteka .glb](glb-output.md)).
Če skeniranje ne ustvari površine, "Nothing to save" pojasni, da je bilo sledenje verjetno izgubljeno za večji
del skeniranja. Ob uspehu: "Written to <path> ... Load it in 3DHeat through the Level
panel.", pri čemer se navede tudi datoteka oznak, kadar so označena mesta.

Označena mesta se zapišejo ob nivoju kot **`<name>.marks.json`**:

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

`position` je v lastnih koordinatah nivoja (merilo GLB je uporabljeno, zato oznaka sedi na mreži, nad katero
je bila narejena), `metres` v metrih; `number` ustreza `M1`, `M2`, … v oknu. Kadar je bilo merilo najdeno na
kasnejšem ključnem okvirju ([Merilo](reconstruction-pose.md#scale)), oba vsebujeta ta faktor.

Ustavitev skeniranja ohrani, kar je bilo zbrano; nov **Start** zavrže prejšnje skeniranje.
**Zapiranje okna ne vpraša za shranjevanje**: ustavi skeniranje, sprosti bližnjice in zapre prekrivanje.
