---
title: "Poloha kamery a měřítko"
nav_order: 4
lang: "cs"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poloha kamery a měřítko {#camera-pose-and-scale}

Mapa hloubky říká, jak daleko jsou věci od *jednoho* pohledu. Aby se z mnoha takových map
stal jeden level, je třeba vědět, kde byl každý pohled, a v jakých jednotkách. Tato
stránka pokrývá živé cesty; offline řešení z dopředného modelu je na
[Offline rekonstrukce](reconstruction-offline.md).

Kód: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamery {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` postaví dírkovou kameru z **horizontálního
zorného pole**, které nastavíte v okně: `fx = (šířka / 2) / tan(fov / 2)`, čtvercové
pixely (`fy = fx`), hlavní bod ve středu snímku. Hra svou projekci nezveřejňuje, takže
je to jediné předpokládané číslo: příliš úzké a scéna vypadá hlubší, než je. Offline
cesta používá 65 stupňů.

`Pose` se ukládá jako **svět-z-kamery**: `rotation` (3 x 3) a `translation` = střed kamery
ve světě, což chtějí trajektorie, mapa pokrytí i překryv.

## Vizuální odometrie (výchozí) {#visual-odometry-the-default}

`VisualOdometry` sleduje každý klíčový snímek vůči předchozímu:

1. **Rysy**: ORB, až 1500 na snímek, detekované jen na masce světa (viz
   [Záběr](reconstruction-capture.md#what-is-not-the-world)).
2. **Shody** s předchozím klíčovým snímkem: hrubou silou, Hammingova vzdálenost,
   křížově ověřené (jen vzájemně nejlepší páry).
3. **Zvednutí do 3D**: hloubka předchozího snímku je už ve světových jednotkách, takže
   jeho sladěné pixely se stanou světovými body.
4. **Umístění kamery**: `solvePnPRansac` mezi těmito body (chyba reprojekce 3 px,
   jistota 0,999, 200 iterací). Posun vyjde ve stejných jednotkách, takže **měřítko
   přechází přes mezeru**.
5. **Ukotvení hloubky tohoto snímku**: jeho vlastní předpovězená inverzní hloubka se
   přizpůsobí (`fit_scale`) hloubkám inlierů PnP a cyklus se opakuje.

**První snímek** je počátek: jednotková poloha, a jeho afinní hloubky je buď kalibrace
země (níže), nebo bez ní jednotka (rekonstrukce je pak sama v sobě konzistentní, ale bez
jednotek).

Poloha potřebuje alespoň **18 RANSAC inlierů** - jasně víc než minimum PnP, šest, protože
řešení z ledva dostatku bodů je přesně to, které si je sebevědomě špatné.

### Jistota {#confidence}

Každý umístěný snímek dostane jistotu v 0..1, která váží jeho sloučení a pokrytí:

| Poloha z | Jistota |
|---|---|
| telemetrie | 1,0 |
| dopředného řešení | 0,85 |
| vizuálního sledování | `inliery / shody x min(1, inliery / 60)` |

### Když sledování selže {#when-tracking-breaks}

Snímek, který nelze umístit, se nahlásí, nikdy se neodhaduje: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Žádná poloha se
nezaznamená a nic se nesloučí. Pokračovat od poslední polohy nebo začít novým počátkem by
dalo další úsek levelu na libovolný posun - šev, který vypadá jako skutečná geometrie.

Po výpadku se každý nový snímek **relokalizuje** proti databázi minulých klíčových snímků
(každý 4. sledovaný snímek se přidá, až 120, nejstarší se zahodí), od nejnovějšího, se
stejným krokem shody a PnP. Dokud se některý nepovede, snímky se zahazují. Obnovený snímek
pokračuje ve stejném souřadném rámci. Obnovy se počítají a ukazují v okně (`N recovered`).

### Uzavření smyčky: vypnuto {#loop-closure-off}

Stejná databáze podporuje uzavření smyčky: porovnání s klíčovými snímky z mnohem dřívější
doby, aby se zjistil návrat na místo a dráha se na něj přichytila. **Je ve výchozím
nastavení vypnuto a skener ho nikdy nezapne** (`Reconstructor(loop_closure=False)`). Na
opakujících se scenériích - etapa rallye, chodba, řada stromů - je každý úsek jako každý
jiný a porovnávání rysů potvrzuje falešné návraty, což připne kameru blízko místa startu,
zatímco jede dál. Dělat to pořádně potřebuje rozpoznávání míst (slovníkový vektor nebo
naučený deskriptor) a geometrické ověření proti mapě, což není postaveno.

Když je zapnuto z kódu, uzavření potřebuje: klíčový snímek alespoň 60 klíčových snímků
starý, do 6 m od současné polohy, shodu s alespoň 90 inliery, a posunuje polohu o více
než 0,02 m a méně než 6 m. I tehdy jen nahradí současnou polohu; není to graf poloh a
nehýbe dřívějšími snímky ani sloučenou geometrií.

## Telemetrické polohy {#telemetry-poses}

S **Racing telemetry (Forza) -> Listen for position data** zapnutým pochází dráha kamery z
Data Out Forzy, ne z obrazů (`ForzaPoseSource`):

- Vlákno poslouchá na `127.0.0.1:<port>` (výchozí 5300) se stejným zjišťováním rozložení
  jako nahrávače ([Forza](telemetry-forza.md)); pakety se používají, zatímco je nastaveno
  `isRaceOn`. Obsazený port se nahlásí, nevyvolá výjimku: telemetrie je vylepšení a sken
  pokračuje vizuálně.
- Každý paket se označí **monotonním časem, kdy dorazil** - stejnými hodinami, kterými
  záběr označuje snímky. Vlastní časové razítko hry počítá od něčeho nesouvisejícího, proto
  se k zarovnání nepoužívá. Jitter smyčky o milisekundu nebo dvě je asi 6 cm při 200 km/h.
- Drží se klouzavý 30sekundový buffer. Póza snímku se **interpoluje** ze vzorků po obou
  stranách jeho času záběru: poloha lineárně, rotace sférickou interpolací (smíchaná
  matice není rotace a zkreslila by každý bod). Přes mezeru delší než **0,35 s**, nebo
  mimo buffer, žádná póza není.
- `pose_from_forza`: kamera je umístěna na auto (offset chase kamery se nezveřejňuje).
  **Polohy se ponechávají přesně tak, jak je hra posílá**: svět Forzy je už s Y nahoru (x a z
  přes mapu, y výška), jak to zapisují soubory kol i trasy, takže povrch dopadne na
  stejné souřadnice jako kola nahraná nad ním. (Dřívější verze prohodila y a z pro svět
  „Z nahoru“ a položila dráhu na bok.)
- Rotace je yaw, pak pitch, pak roll, se smysly odečtenými z nahraných kol: směr jízdy
  `atan2(dx, dz)` se rovná yaw, sklon do kopce se rovná minus pitch (kladné je nos dolů)
  a roll je kladný, když je pravé odpružení stlačené (kladné shodí pravou stranu). Osy auta
  (x vpravo, y nahoru, z dopředu) se pak převedou na osy kamery (x vpravo, y dolů, z
  dopředu) otočením y.
- Svět Forzy je **levotočivý** a rámec kamery ne, takže výsledná matice svět-z-kamery je
  zrcadlení (determinant -1) a sken vyjde levotočivý jako soubory kol. Interpolace na tom
  nezáleží (otočení mezi dvěma takovými pózami je správná rotace).
- Když snímek nemá telemetrickou pózu (mezera), rekonstruktor přejde na **vizuální
  sledování** pro ten snímek, pokračuje od poslední telemetrické pózy a jakmile feed znovu
  odpoví, vrátí se k pózám z feedu. PnP vrací jen rotace, takže v zrcadleném světě se řeší
  se zrcadlením světa přes z a zrcadlení se zase přidá; snímek přistane v souřadnicích hry.
  Jen když selže i vizuální sledování, je snímek nesledovaný.

### Měřítko hloubky z telemetrie {#depth-scale-from-telemetry}

Hra říká, kde je kamera, ne jak daleko je cokoli, takže hloubka každého snímku se pořád
musí ukotvit - ale ne řetězením od nultého snímku, jehož jednotka je libovolná, zatímco
pózy jsou v metrech. Místo toho se rysy sladěné mezi předchozím a současným snímkem (alespoň
8) **triangulují přímo ze dvou známých poloh**, v metrech, a mapa hloubky se přizpůsobí
bodům před kamerou. Každý snímek se tak ukotvuje proti telemetrii, takže není žádný řetěz,
který by driftoval.

Jsou-li dvě polohy od sebe méně než **0,05 m**, paprsky jsou téměř rovnoběžné a
triangulace je šum, takže snímek zůstane neukotven: umístěný přesně, ale nesloučený („positioned,
but its depth has no scale yet“). Proto okno počítá *umístěné* a *sloučené* snímky zvlášť.

## Měřítko {#scale}

Vizuální odometrie správně řetězí relativní měřítko, ale celý level stále plave na jednom
neznámém faktoru. Relativní výstup Depth Anything vychází v libovolných jednotkách, takže
kdybychom nechali první snímek na jednotce, dal by svět do metrů od kamery v libovolné
velikosti.

`GroundCalibrator` tento faktor přibije podle **toho, jak vysoko je kamera nad zemí**,
měřeno na **prvním klíčovém snímku** a, když tam není použitelná země, na následujících:

- Výška kamery: **1,15 m** (linie očí řidiče) - okno to vždy používá; skripty mohou předat
  1,70 m (`WALKING_HEIGHT`, stojící hráč) nebo `None` (bez kalibrace).
- Vzorek země: řádky 62-92 % od horní hrany snímku (pod horizontem, nad kapotou nebo zbraní)
  a sloupce 30-70 % napříč (dál od krajnic).
- Každý pixel tam s použitelnou předpovědí se zvedne s hloubkou `1 / předpověď` v jednotkách
  sítě; body pod optickou osou dají výšku pod kamerou. Jejich medián je výška kamery
  v jednotkách sítě, takže `metrů na jednotku = 1,15 / medián` a afinní hodnota snímku je
  `scale = 1 / metrů_na_jednotku`, posun 0.
- Důvěřuje se jen s alespoň 200 vzorky země a **rozptylem** (medián absolutní odchylky
  dělený mediánem) pod **0,60**.
- Na prvním klíčovém snímku se fit stane jednotkou počátku, takže sken je v metrech od
  začátku. Když první klíčový snímek nemá použitelnou zem, sken začne bez jednotek a
  zkouší se každý další sledovaný klíčový snímek, až do **30 snímků** celkem. První, který
  se zkalibruje, dá *metry na jednotku*: medián přes pásmo země z hloubky, kterou z ní
  plyne, dělený hloubkou, kterou řetěz dal tomu snímku. Vše už sloučené je v jednotce
  prvního snímku, takže faktor se nevrací do řetězu; použije se na celý level (a na
  označená místa) při zápisu a na zobrazenou vzdálenost mezitím. Velikost voxelu je pak v
  jednotkách prvního snímku, takže její velikost v metrech se liší od nastavení o tento
  faktor.
- Po 30 snímcích bez země zůstává sken bez jednotek a řekne to.
- S telemetrií se pozdější klíčové snímky nezkoušejí: hloubka je ukotvena na metry
  telemetrie.

Být do deseti procent skutečné velikosti je lepší než být vzdálený faktor tisíc; telemetrie,
je-li k dispozici, to dělá zbytečným. Poznámka se ukazuje v okně pod řádkem sledování jako
`Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (s `found on frame N, so the level is
scaled by F when it is written`, když to přišlo později), `no usable ground in the first N
frames - sizes are relative, not metres`, nebo `in metres, from the telemetry's positions`.

## Vyrovnání svazku a dlouhé stopy (nezapojeno) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dva kusy existují pro budoucí oknový řešitel a **skener je nepoužívá**:

- **`FeatureTracks`** drží identitu rysů přes stovky snímků sledováním Lucas-Kanade (600
  rysů, znovu zaseté pod 60 %, tolerance dopředu a dozadu 1 px, nové rysy 10 px od
  existujících), což vyrovnání svazku potřebuje - shoda deskriptorů mezi po sobě jdoucími
  snímky dává jen páry.
- **`bundle_adjust`** zpřesňuje okno poloh a bodů najednou pomocí
  `scipy.optimize.least_squares` (oblast důvěry, měkká L1 ztráta s měřítkem 2 px, explicitní
  vzor řídkosti Jakobiánu, pevné kamery vrácené přesně). Otestováno proti známé pravdě v
  `tests/test_bundle.py`.

`WindowedOdometry` je oboje spojuje (okna 12 klíčových snímků, řešení každé 3 klíčové
snímky, první dvě kamery pevné, body s chybou nad 6 px zahozeny, skoky přes 6násobek
nedávného kroku odmítnuty). Jeho docstring zaznamenává, že na skutečných záznamech **zkolabovala
dráha a byla mnohem pomalejší** než sledování od snímku k snímku, s volností měřítka a
zavedením hloubky jako známými příčinami a třetí příčina nezjištěná. Proto zůstává
výchozí odometrie od snímku k snímku; pravděpodobná oprava uvedená v kódu je zavedení
dvou pohledů přes esenciální matici s pevnou základnou z kalibrace roviny země.
