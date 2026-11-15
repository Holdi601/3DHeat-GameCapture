---
title: "Okno skenování"
nav_order: 1
lang: "cs"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Okno skenování {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kód: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Okno je tenký pohled na `scan/session.py` a `scan/reconstruct.py`; žádnou logiku skenování ani
geometrie nevlastní.

## Spuštění {#starting-up}

1. **Kontrola aktualizací** - viz [Aktualizace](updates.md).
2. **Kontrola závislostí** - každý balíček, který skener potřebuje, se zkontroluje dřív, než se
   cokoli importuje; chybějící se vypíšou s tím, k čemu slouží, a s velikostí ke stažení, a
   nainstalují se až po „Stáhnout a nainstalovat“. Zrušit znamená skončit bez jakékoli změny. Viz
   [Běh a závislosti](runtime.md#first-run-preflight).
3. **Okno** - „3DHeat — Level scanner“, 1420 x 900, styl Fusion od Qt.
4. **Kontrola hardwaru** - vybere se nejlepší backend inference, načte se model hloubky a jeho
   propustnost se změří na 6 snímcích; pole nahoře vlevo říká, jaké skenování bude
   (viz [Běh](runtime.md#what-to-expect-from-this-machine)).
5. **Globální klávesové zkratky** se registrují jako poslední.

### Když ještě není model hloubky {#when-there-is-no-depth-model-yet}

Když `models/` neobsahuje žádný `depth-*.onnx`, pole s verdiktem ukáže **„Ještě je potřeba jeden
krok nastavení.“**, Start je vypnutý a objeví se tlačítko **Nastavit model hloubky**. To:

- zkontroluje PyTorch, `transformers` a `onnxscript` (asi 945 MB dohromady) a před instalací se
  zeptá;
- spustí `tools/export_onnx.py --size small` jako samostatný proces (aby PyTorch nikdy nezůstal v
  paměti skeneru), s limitem 30 minut. Okno během běhu nereaguje;
- po úspěchu znovu spustí kontrolu hardwaru; po neúspěchu ukáže posledních 600 znaků výstupu
  převodníku.

Když je přítomno několik modelů, vybírá se **podle licence, ne podle názvu souboru**: `depth-small-*`
(Apache-2.0, komerční použití povoleno), kdykoli je k dispozici, pak Base, pak Large (obě
nekomerční). Pole s verdiktem a šedý řádek pod tlačítky pojmenují soubor v použití, jeho licenci a
další přítomné soubory modelů, které se nepoužijí - například `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Chcete-li skenovat s Base, přesuňte soubor Small z `models/`.

## Levý sloupec: nastavení {#left-column-settings}

| Skupina | Ovládací prvek | Výchozí | Rozsah / hodnoty | Co dělá |
|---|---|---|---|---|
| (nahoře) | Pole s verdiktem | `Checking your graphics card…` | zbarvené zeleně, žlutě nebo červeně podle úrovně | Hlavní věta, `<device> via <API> — N views per second`, jedna poznámka a `Depth model: <file> (<licence>)` |
| Co skenovat | Zdroj | Celá obrazovka | Celá obrazovka, Okno, Video soubor | Odkud snímky přicházejí |
| | Který | `1` | číslo monitoru / název okna / cesta k videu | `monitor:<n>`, `window:<title>`, nebo cesta k souboru |
| | Vybrat soubor… | zobrazí se u videa | `*.mp4 *.mkv *.avi *.mov` | Vyplní cestu |
| Jak pečlivě | Předvolba | Vyvážené | Náhled, Vyvážené, Podrobné | Rozlišení zachycení a jak výběrově se vybírají klíčové snímky (níže); pod ním se ukáže jednořádkové shrnutí |
| | Zorné pole hry | 90° | 30-140° | **vodorovné** zorné pole hry. Příliš úzké a level se zrekonstruuje hlouběji, než je; příliš široké ho zploští. Závodní hry jsou spíše kolem 65° |
| | Detail povrchu | 0,25 m | 0,05–2,0 m, krok 0,05 | Velikost voxelu povrchu. Menší je jemnější a těžší |
| Zastavit po | Čas | bez limitu | 0-120 min | Ukončí skenování po tolika minutách (0 = bez limitu) |
| | Uchované pohledy | 3000 | 0-100 000 | Ukončí skenování po tolika klíčových snímcích, jako pojistka paměti (0 = bez limitu) |
| Co ignorovat | Ignorovat HUD a vše na kameře | zapnuto | | Učí se a maskuje HUD, zaměřovač, zbraň, kapotu, kokpit ([Zachycení](reconstruction-capture.md#what-is-not-the-world)). Řádek pod ním říká, co detektor právě rozhoduje |
| Když hraješ | Zobrazit zpětnou vazbu přes hru | zapnuto | | Při skenování otevře průhledný překryv, který nereaguje na kliknutí. Nápověda pod ním: spusťte hru v **bezrámečkovém okně**; exkluzivní celá obrazovka nejde ničím překrýt |
| Telemetrie závodu (Forza) | Poslouchat data o pozici | vypnuto | | Vezme dráhu kamery z Forza Data Out místo odhadu z obrazu ([Pozice](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Port Data Out |
| | (stavový řádek) | | | `N packets — poses come from the game, not from the picture`, nebo `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Spustit skenování** / **Zastavit skenování** | | | Spustí nebo zastaví; když byla klávesová zkratka registrována, ukáže ji |
| | **Nastavit model hloubky** | skryto | | Viz výše |
| | **Uložit level…** | vypnuto | | Zapne se po skenování, které vytvořilo povrchové voxely; zeptá se na název souboru (výchozí `scan.glb`) |
| | (šedý řádek) | | | `Model: <file> (<licence>) · Available: <backends>`, plus poznámky k nastavení, například instalace `onnxruntime-gpu` |

### Předvolby {#the-presets}

| Předvolba | Delší strana zachycení | Kvantil ponechání | Počáteční práh | Zobrazené shrnutí |
|---|---|---|---|---|
| Náhled | 640 px | 0,85 | 0,020 | Rychlé a hrubé. Dobré pro kontrolu trasy před skutečným skenováním. |
| Vyvážené | 960 px | 0,65 | 0,010 | Obvyklá volba. Chodit normálním tempem. |
| Podrobné | 1280 px | 0,40 | 0,004 | Pomalé a důkladné. Chodit záměrně a otáčet se mírně. |

Kvantil ponechání znamená „ponechat snímek, když se změnil víc než tento kvantil změn posledních
240 snímků“ - Náhled ponechá zhruba nejrušnějších 15 %, Podrobné nejrušnějších 60 %. Viz
[Klíčové snímky](reconstruction-capture.md#keyframes).

### Nastavení, která jsou v okně pevná {#settings-that-are-fixed-in-the-window}

Okno vždy rekonstruuje při skenování, pro měřítko podle země používá výšku kamery **1,15 m** (chůzová
hodnota 1,70 m nejde vybrat) a nechá žebřík backendů vybrat GPU. To jsou pole `ScanSettings`
(`camera_height`, `prefer_backend`), která může změnit jen skript.

## Pravý sloupec: co skenování právě dělá {#right-column-what-the-scan-is-doing}

| Prvek | Ukazuje |
|---|---|
| **Co kamera vidí** | poslední klíčový snímek |
| **Tvar, který čte** | jeho předpovězená hloubka, obarvená mapou barev Turbo, normalizovaná mezi 2. a 98. percentilem tohoto snímku (aby jeden oblohový pixel nesplácl rozsah) |
| **Pokrytí - kde jsi byl a jak dobře** | pohled shora (viz níže) |
| **Stojí za další pohled** | slabá místa, očíslovaná podle kroužků na mapě, každé s pokynem; nejhorší (největší) první, nejvýš 8; pak místa, která jsi označil (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Lišta rychlosti chůze | `walk speed — N% of the way to the next view`: změna obrazu posledního snímku dělená **prahem v použití** - počáteční hodnota předvolby pro prvních 30 snímků, pak přizpůsobená ([Klíčové snímky](reconstruction-capture.md#keyframes)) |
| Řádek zdraví | zdraví sledování, nebo varování o zachycení (níže) |
| Řádek velikosti | `Size: ...`, jak bylo měřítko levelu určeno, nebo proč určeno nebylo ([Měřítko](reconstruction-pose.md#scale)) |
| Řádek statistik | `views  frames  dropped  depth-per-second  seconds`, a při rekonstrukci `placed  cells  % well seen  metres`, plus `recovered` a `loops closed`, když je některé z nich nenulové |
| Řádek klávesových zkratek | registrované klávesy, nebo proč je nelze registrovat |
| Řádek nápovědy (žlutý) | živé rady (níže), závěrečná zpráva skenování a značky |

### Mapa pokrytí {#the-coverage-map}

Překresluje se každých 900 ms na pozadí (nikdy na vlákně rozhraní), v mřížce 200 x 200 buněk
zmenšené na 420 px:

- každý sloupec mřížky pokrytí bere **nejlepší** kvalitu pozorování v něm (aby dobře viděná podlaha
  nebyla obarvena žlutě špatně viděným stropem nad ní);
- přechod jde od červené (špatné) přes oranžovou (tenké) a žlutou (přijatelné) po zelenou (dobré);
- nikdy nepozorované buňky jsou zřetelně tmavošedé, aby se nezdálo, že neprozkoumaný kout je špatně
  skenovaný;
- projitá cesta se kreslí tenkou světlou čarou, aktuální pozice bílou tečkou;
- slabá místa jsou bílé kroužky s číslem;
- označená místa jsou oranžové čtverce s popiskem `M1`, `M2`, …

Jak se počítá kvalita a slabá místa: [Fúze, pokrytí a barva](reconstruction-fusion-and-texture.md#coverage).

### Řádek zdraví {#the-health-line}

| Zdraví sledování (umístěné snímky / snímky) | Text | Barva |
|---|---|---|
| zatím žádné snímky | `Waiting for the first frame.` | šedá |
| 90 % nebo víc | `Tracking well — N of M frames placed.` | zelená |
| 60 % nebo víc | `Tracking is patchy — N of M frames could not be placed. Turn more slowly.` | žlutá |
| pod 60 % | `Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky.` | červená |

Varování o zachycení z mřížky pokrytí nahrazuje tento řádek (červené, když se skenování posoudí jako
nerekonstruovatelné, jinak žluté): téměř žádná paralaxa, vše viděno z více než 25 m, nebo tenká
paralaxa. Viz [Pokrytí](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Řádek nápovědy {#the-hint-line}

| Podmínka | Nápověda |
|---|---|
| více než polovina snímků zahozena, po 6 s | `Falling behind — N frames dropped.` … |
| méně než 0,3 pohledu ponecháno za sekundu, po 8 s | `Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot.` |
| více než 8 pohledů ponecháno za sekundu, po 8 s | `Keeping a lot. Slow down a little for cleaner geometry.` |
| skenování skončilo | zpráva relace: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, nebo `failed: <error>` |

## Klávesové zkratky {#hotkeys}

Registrované u Windows (`RegisterHotKey`), takže fungují, i když má hra fokus. Přepnutí z celé
obrazovky hry je přesně to, co zkazí zachycení.

| Klávesy | Akce |
|---|---|
| **Ctrl+Alt+F9** | Spustit / zastavit skenování |
| **Ctrl+Alt+F10** | Označit toto místo k opětovné návštěvě (při skenování) |
| **Ctrl+Alt+F11** | Zobrazit / skrýt překryv (přepíná políčko „Zobrazit zpětnou vazbu přes hru“) |

- Registrují se jednou, když se okno otevře, a uvolňují se, když se zavře; zatímco jsou registrované,
  tyto kombinace kláves jsou odebrány každému jinému programu, včetně hry. Kombinace F-kláves se
  dvěma modifikátory byly zvoleny, protože hry je zřídka vážou.
- Automatické opakování je potlačeno (`MOD_NOREPEAT`), takže podržení klávesy nepřepne skenování
  desítkykrát.
- Klávesu, kterou už drží jiný program, se nahlásí (`... unavailable: another program already
  has this key`) a ostatní fungují dál. Tlačítko nabízí jen klávesu, která byla skutečně
  registrována.
- Klávesy jsou pevně zapsané v kódu (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); analyzátor
  přijímá F1-F12 s `ctrl`, `alt` a `shift`. Mimo Windows nejsou žádné globální klávesové zkratky a
  okno to říká.
- **Označit** zaznamená aktuální pozici kamery (poslední umístěného snímku) a ukáže `Marked M{N}. Marked spots are on the map and saved with the level.` Dokud není umístěn žádný snímek, řekne `Nothing placed yet, so there is nowhere to mark.` Označená místa se kreslí na mapě okna a překryvu jako oranžové čtverce s popiskem
  `M1`, `M2`, …, vypisují se pod slabými místy, počítají se v řádku statistik překryvu a ukládají se
  s levelem (níže).

## Překryv {#the-overlay}

Malý panel připnutý přes hru, aby zpětná vazba byla tam, kde už jsou oči.

- Bez rámečku, vždy nahoře, okno nástroje (není na hlavním panelu ani v alt-tabu), průhledný pro
  vstup v Qt a ve Windows nastavený tak, aby nereagoval na kliknutí (`WS_EX_TRANSPARENT | WS_EX_LAYERED`),
  takže kliknutí určené hře nikdy nepohltí. Zobrazí se bez získání fokusu.
- Pravý horní roh hlavní obrazovky, 18 px od okrajů; 214 x 358 px.
- Otevře se, když skenování začne (pokud je zapnuto „Zobrazit zpětnou vazbu přes hru“), zavře se,
  když skenování skončí.
- **Vyžaduje bezrámečkový režim okna**: nic nelze překrýt přes exkluzivní celou obrazovku - ani tohle,
  ani překryv Steamu, ani Discordu.

Shora dolů ukazuje:

| Prvek | Obsah |
|---|---|
| Mapa pokrytí | 190 px, stejná mapa jako v okně v hrubší mřížce 120 x 120, s cestou, kroužky slabých míst a označenými místy |
| Zdraví | stejný text a barva jako řádek zdraví v okně |
| Statistiky | `N placed · M to revisit · X m`, s `· K marked`, když nějaká jsou |
| Lišta **pohybu** | stejná jako lišta rychlosti chůze v okně: změna obrazu posledního snímku nad prahem v použití, plná, když se další snímek ponechá |
| Lišta **ostrosti** | ostrost vzhledem k vlastnímu mediánu tohoto zachycení: zelená od 0,75, žlutá od 0,45, červená pod tím |
| Rada | jedna instrukce, zelená / žlutá / červená (tučně, když není „ok“) - viz [kvalita snímku](reconstruction-capture.md#frame-quality-and-advice) |
| Klávesové zkratky | registrované klávesy |

Když aktualizace překryvu kdykoli vyhodí výjimku, přepne se na červený panel **„Feedback stopped“**, který říká, že cokoli ukázaného dříve je zastaralé, že skenování stále běží a hlavní
okno je stále správné, s chybou a počtem. Panel, který zamrzl při zelené barvě, by jinak dál působil
jako potvrzení.

## Ukládání {#saving}

**Uložit level…** zapíše rekonstrukci jako `.glb` (viz [Výstup .glb](glb-output.md)). Když objem
nevytvoří žádný povrch, „Nothing to save“ vysvětlí, že sledování se pravděpodobně ztratilo na
většině skenování. Při úspěchu: „Written to <path> ... Load it in 3DHeat through the Level
panel.“, a když jsou označená místa, uvede i soubor značek.

Označená místa se zapisují vedle levelu jako **`<name>.marks.json`**:

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

`position` je v souřadnicích levelu (aplikované měřítko GLB, takže značka sedí na síti, nad kterou
byla vytvořena), `metres` v metrech; `number` odpovídá `M1`, `M2`, … v okně. Když se měřítko našlo
na pozdějším klíčovém snímku ([Měřítko](reconstruction-pose.md#scale)), obě hodnoty tento činitel
zahrnují.

Zastavení skenování ponechá, co se nasbíralo; nové **Start** předchozí skenování zahodí.
**Zavření okna se neptá na uložení**: zastaví skenování, uvolní klávesové zkratky a zavře překryv.
