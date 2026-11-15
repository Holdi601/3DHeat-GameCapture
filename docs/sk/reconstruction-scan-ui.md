---
title: "Okno skenovania"
nav_order: 1
lang: "sk"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Okno skenovania {#the-scan-window}

```bash
python -m heat3d_capture.ui        # alebo dvojklik na scan.bat
```

Kód: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Okno je tenký pohľad na `scan/session.py` a `scan/reconstruct.py`; nevlastní žiadnu logiku skenovania
ani geometrie.

## Spustenie {#starting-up}

1. **Kontrola aktualizácie** – pozrite [Aktualizácie](updates.md).
2. **Kontrola závislostí** – každý balík, ktorý skener potrebuje, sa skontroluje skôr, než sa čokoľvek naimportuje; chýbajúce sa vypíšu s tým, na čo slúžia, a s veľkosťou na stiahnutie, a nainštalujú sa až po **Download and install**. Cancel skončí bez zmeny čohokoľvek. Pozrite [Beh a závislosti](runtime.md#first-run-preflight).
3. **Okno** – „3DHeat — Level scanner“, 1420 x 900, štýl Fusion z Qt.
4. **Kontrola hardvéru** – vyberie sa najlepší backend inferencie, načíta sa model hĺbky a jeho priepustnosť sa zmeria na 6 snímkoch; verdiktové pole vľavo hore hovorí, aký bude sken (pozrite [Beh](runtime.md#what-to-expect-from-this-machine)).
5. **Globálne klávesové skratky** sa zaregistrujú ako posledné.

### Keď ešte nie je model hĺbky {#when-there-is-no-depth-model-yet}

Ak `models/` neobsahuje žiadny `depth-*.onnx`, verdikt hovorí **„One more thing to set up.“**, Start je vypnuté a objaví sa tlačidlo **Set up the depth model**. To:

- skontroluje PyTorch, `transformers` a `onnxscript` (spolu asi 945 MB) a pred inštaláciou sa opýta;
- spustí `tools/export_onnx.py --size small` ako samostatný proces (aby PyTorch nikdy nezostal v pamäti skenera), s limitom 30 minút. Okno počas behu nereaguje;
- pri úspechu znova spustí kontrolu hardvéru; pri zlyhaní zobrazí posledných 600 znakov výstupu konvertora.

Keď je prítomných viac modelov, výber sa robí **podľa licencie, nie podľa názvu súboru**: `depth-small-*` (Apache-2.0, komerčné použitie povolené), kedykoľvek je k dispozícii; potom Base; potom Large (obidva nekomerčné). Verdiktové pole a sivý riadok pod tlačidlami pomenujú používaný súbor, jeho licenciu a ďalšie prítomné modely súborov, ktoré sa nepoužijú – napríklad `Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used: depth-base-518.onnx`. Ak chcete skenovať s Base, presuňte súbor Small mimo `models/`.

## Ľavý stĺpec: nastavenia {#left-column-settings}

| Skupina | Ovládací prvok | Predvolené | Rozsah / hodnoty | Čo robí |
|---|---|---|---|---|
| (hore) | Verdiktové pole | „Checking your graphics card…“ | sfarbené zeleno, žlto alebo červeno podľa stupňa | Nadpis, `<device> via <API> — N views per second`, jedna poznámka a `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Odkiaľ prichádzajú snímky |
| | Which | `1` | číslo monitora / názov okna / cesta k videu | `monitor:<n>`, `window:<title>` alebo cesta k súboru |
| | Choose file… | zobrazí sa pri videu | `*.mp4 *.mkv *.avi *.mov` | Vyplní cestu |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Rozlíšenie zachytávania a to, ako výberovo sa berú kľúčové snímky (nižšie); pod ním je jednoriadkový súhrn |
| | Game field of view | 90° | 30-140° | **Vodorovné** zorné pole hry. Príliš úzke a úroveň sa zrekonštruuje hlbšie, než je; príliš široké ju sploští. Pretekárske hry sú bližšie k 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, krok 0.05 | Veľkosť voxela povrchu. Menšie je jemnejšie a ťažšie |
| Stop after | Time | bez limitu | 0-120 min | Skončí sken po tejto dobe (0 = bez limitu) |
| | Views kept | 3000 | 0-100 000 | Skončí sken po tomto počte kľúčových snímok, ako ochrana pamäte (0 = bez limitu) |
| What to ignore | Ignore HUD and anything on the camera | zapnuté | | Učí sa a maskuje HUD, zameriavač, zbraň, kapotu, kabínu ([Zachytávanie](reconstruction-capture.md#what-is-not-the-world)). Riadok pod ním hovorí, čo detektor práve rozhoduje |
| While you play | Show feedback over the game | zapnuté | | Počas skenovania otvorí prekrytie, ktoré necháva kliky prejsť. Nápoveda pod ním: spustite hru v **borderless windowed**; exkluzívny celoobrazovkový režim nedokáže nič prekryť |
| Racing telemetry (Forza) | Listen for position data | vypnuté | | Berie dráhu kamery z Data Out Forzy namiesto odhadu z obrazu ([Póza](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Port Data Out |
| | (status line) | | | `N packets — poses come from the game, not from the picture`, alebo `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Spustí alebo zastaví; ukáže klávesovú skratku, keď bola zaregistrovaná |
| | **Set up the depth model** | skryté | | Pozrite vyššie |
| | **Save level…** | vypnuté | | Zapne sa po skene, ktorý vytvoril povrchové voxely; pýta sa na názov súboru (predvolene `scan.glb`) |
| | (grey line) | | | `Model: <file> (<licence>) · Available: <backends>`, plus poznámky k nastaveniu, napríklad inštalácia `onnxruntime-gpu` |

### Predvoľby {#the-presets}

| Predvoľba | Dlhšia strana zachytávania | Kvantil ponechania | Začiatočný prah | Zobrazený súhrn |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Rýchle a hrubé. Dobré na kontrolu trasy pred skutočným skenom. |
| Balanced | 960 px | 0.65 | 0.010 | Obvyklá voľba. Choďte normálnym tempom. |
| Detailed | 1280 px | 0.40 | 0.004 | Pomalé a dôkladné. Choďte zámerne a otáčajte sa jemne. |

Kvantil ponechania znamená „ponechať snímok, keď sa zmenil viac než tento kvantil zmien posledných 240 snímok“ – Draft ponechá zhruba najvyťaženejších 15 %, Detailed najvyťaženejších 60 %. Pozrite [Kľúčové snímky](reconstruction-capture.md#keyframes).

### Nastavenia pevne dané v okne {#settings-that-are-fixed-in-the-window}

Okno vždy rekonštruuje počas skenovania, používa výšku kamery **1,15 m** pre mierku roviny zeme (chôdzová hodnota 1,70 m sa nedá vybrať) a nechá rebrík backendov vybrať GPU. Sú to polia `ScanSettings` (`camera_height`, `prefer_backend`), ktoré môže zmeniť len skript.

## Pravý stĺpec: čo sken robí {#right-column-what-the-scan-is-doing}

| Prvok | Zobrazuje |
|---|---|
| **What the camera sees** | posledný kľúčový snímok |
| **Shape it is reading** | jeho predpovedanú hĺbku, sfarbenú mapou farieb Turbo, normalizovanú medzi 2. a 98. percentilom tohto snímku (aby jeden pixel oblohy nezaplatil rozsah) |
| **Coverage — where you have been, and how well** | plán zhora (nižšie) |
| **Worth another look** | slabé miesta, očíslované podľa kruhov na mape, každé s pokynom; najhoršie (najväčšie) prvé, najviac 8; potom miesta, ktoré ste označili (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Lišta rýchlosti chôdze | `walk speed — N% of the way to the next view`: zmena obrazu posledného snímku delená **prahom v použití** – začiatočný prah predvoľby pre prvých 30 snímok, potom prispôsobený ([Kľúčové snímky](reconstruction-capture.md#keyframes)) |
| Riadok stavu sledovania | zdravie sledovania, alebo varovanie zachytávania (nižšie) |
| Riadok veľkosti | `Size: ...`, ako sa pevne určila mierka úrovne, alebo prečo nie ([Mierka](reconstruction-pose.md#scale)) |
| Riadok štatistiky | `views  frames  dropped  depth-per-second  seconds`, a počas rekonštrukcie `placed  cells  % well seen  metres`, plus `recovered` a `loops closed`, keď je niektoré nenulové |
| Riadok klávesových skratok | zaregistrované klávesy, alebo prečo sa nedali zaregistrovať |
| Nápovedný riadok (žltý) | živé rady (nižšie), záverečná správa skenu a označenia |

### Mapa pokrytia {#the-coverage-map}

Prekresľuje sa každých 900 ms na pozadí (nikdy na rozhraní), v mriežke 200 x 200 buniek zmenenej na 420 px:

- každý stĺpec mriežky pokrytia berie **najlepšiu** kvalitu pozorovania v ňom (aby dobre videná podlaha nebola zafarbená žlto kvôli zle videnému stropu nad ňou);
- rampa ide od červenej (zlá) cez oranžovú (tenká) a žltú (prijateľná) po zelenú (dobrá);
- bunky, ktoré nikdy neboli pozorované, sú osobitná tmavosivá, aby sa nepreblikli ako zle skenované;
- prejdená cesta je tenká svetlá čiara, aktuálna pozícia biela bodka;
- slabé miesta sú biele kruhy s číslom;
- označené miesta sú jantárové štvorce s nápisom `M1`, `M2`, …

Ako sa počíta kvalita a slabé miesta: [Fúzia, pokrytie a farba](reconstruction-fusion-and-texture.md#coverage).

### Riadok stavu sledovania {#the-health-line}

| Zdravie sledovania (zaradené snímky / snímky) | Text | Farba |
|---|---|---|
| zatiaľ žiadne snímky | Waiting for the first frame. | sivá |
| 90 % alebo viac | Tracking well — N of M frames placed. | zelená |
| 60 % alebo viac | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | jantárová |
| menej ako 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | červená |

Varovanie zachytávania z mriežky pokrytia nahrádza tento riadok (červené, keď sa sken hodnotí ako nerekonštruovateľný, inak jantárové): takmer žiadna paralaxa, všetko videné z viac než 25 m, alebo tenká paralaxa. Pozrite [Pokrytie](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Nápovedný riadok {#the-hint-line}

| Podmienka | Nápoveda |
|---|---|
| viac než polovica snímok zahodená, po 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| menej ako 0,3 zachovaných pohľadov za sekundu, po 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| viac ako 8 zachovaných pohľadov za sekundu, po 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| sken skončil | správa relácie: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, alebo `failed: <error>` |

## Klávesové skratky {#hotkeys}

Registrované vo Windows (`RegisterHotKey`), takže fungujú, keď má hra zameranie. Prepnutie z celoobrazovkovej hry Alt-Tabom je presne to, čo zničí zachytávanie.

| Klávesy | Akcia |
|---|---|
| **Ctrl+Alt+F9** | Spustiť / zastaviť skenovanie |
| **Ctrl+Alt+F10** | Označiť toto miesto na opätovnú návštevu (počas skenovania) |
| **Ctrl+Alt+F11** | Zobraziť / skryť prekrytie (prepína políčko „Show feedback over the game“) |

- Registrujú sa raz, keď sa okno otvorí, a uvoľnia sa, keď sa zatvorí; kým sú registrované, tieto kombinácie kláves sú odobraté každému inému programu vrátane hry. Klávesy F s dvoma modifikátormi boli zvolené preto, lebo hry ich málokedy viažu.
- Automatické opakovanie je potlačené (`MOD_NOREPEAT`), takže podržanie klávesu neprepne sken desiatky krát.
- Kláves, ktorý už drží iný program, sa nahlási (`... unavailable: another program already has this key`) a ostatné fungujú ďalej. Tlačidlo ponúka len kláves, ktorý sa skutočne zaregistroval.
- Klávesy sú pevne zapísané v kóde (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); parser prijíma F1-F12 s `ctrl`, `alt` a `shift`. Mimo Windows globálne klávesové skratky nie sú a okno to povie.
- **Mark** zaznamená aktuálnu pozíciu kamery (poslednej zaradeného snímku) a ukáže „Marked MN. Marked spots are on the map and saved with the level.“ Keď ešte nebol zaradený žiadny snímok, povie, že nie je kam označiť. Označené miesta sa kreslia na mapu okna a prekrytia ako jantárové štvorce s nápisom `M1`, `M2`, …, sú uvedené pod slabými miestami, počítané v riadku štatistiky prekrytia a uložené spolu s úrovňou (nižšie).

## Prekrytie {#the-overlay}

Malý panel pripnutý nad hru, aby bola spätná väzba tam, kde už sú oči.

- Bez rámu, vždy navrchu, okno nástrojov (nie je na paneli úloh ani v alt-tabe), priehľadné pre vstup v Qt a v systéme Windows prepúšťajúce kliky (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), takže klik určený hre sa nikdy nestratí. Zobrazí sa bez prevzatia zamerania.
- Pravý horný roh hlavnej obrazovky, 18 px od okrajov; 214 x 358 px.
- Otvorí sa, keď sa sken spustí (ak je zapnuté „Show feedback over the game“), zavrie sa, keď sa zastaví.
- **Vyžaduje režim borderless windowed**: nič nemôže prekryť exkluzívny celoobrazovkový režim – ani toto, ani prekrytie Steamu, ani Discordu.

Zhora nadol zobrazuje:

| Prvok | Obsah |
|---|---|
| Mapa pokrytia | 190 px, tá istá mapa ako v okne, v hrubšej mriežke 120 x 120, s cestou, krúžkami slabých miest a označenými miestami |
| Zdravie | ten istý text a farba ako riadok zdravia v okne |
| Štatistika | `N placed · M to revisit · X m`, s `· K marked`, keď nejaké sú |
| Lišta **pohybu** | rovnaká ako lišta rýchlosti chôdze v okne: zmena obrazu posledného snímku nad prahom v použití, plná, keď sa ďalší snímok ponechá |
| Lišta **ostrosti** | ostrosť voči vlastnému mediánu tohto zachytenia: zelená od 0,75, jantárová od 0,45, červená pod tým |
| Rada | jeden pokyn, zelený / jantárový / červený (tučne, keď nie je „ok“) – pozrite [kvalita snímku](reconstruction-capture.md#frame-quality-and-advice) |
| Klávesové skratky | zaregistrované klávesy |

Ak aktualizácia prekrytia niekedy zlyhá, prepne sa na červený panel **„Feedback stopped“**, ktorý hovorí, že všetko zobrazené predtým je zastarané, že sken stále beží a hlavné okno je stále správne, spolu s chybou a počtom. Panel, ktorý zamrzol na zelenej, by inak ďalej pôsobil ako potvrdenie.

## Ukladanie {#saving}

**Save level…** zapíše rekonštrukciu ako `.glb` (pozrite [Výstup .glb](glb-output.md)). Ak objem nevytvorí žiadny povrch, „Nothing to save“ vysvetlí, že sledovanie sa pravdepodobne stratilo na väčšine skenu. Pri úspechu: „Written to <path> ... Load it in 3DHeat through the Level panel.“, s menom súboru označení, keď existujú označené miesta.

Označené miesta sa zapisujú vedľa úrovne ako **`<name>.marks.json`**:

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

`position` je v súradniciach samotnej úrovne (aplikovaná mierka GLB, takže označenie sedí na sieti, nad ktorou vzniklo), `metres` v metroch; `number` zodpovedá `M1`, `M2`, … v okne. Keď sa mierka našla na neskoršom kľúčovom snímku ([Mierka](reconstruction-pose.md#scale)), obidve hodnoty tento faktor obsahujú.

Zastavenie skenu zachová, čo sa nazbieralo; nové **Start** zahodí predchádzajúci sken.
**Zatvorenie okna sa nepýta na uloženie**: zastaví sken, uvoľní klávesové skratky a zavrie prekrytie.
