---
title: "Poloha kamery a mierka"
nav_order: 4
lang: "sk"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poloha kamery a mierka {#camera-pose-and-scale}

Mapa hĺbky hovorí, aká ďaleko sú veci od *jedného* bodu pohľadu. Aby sa z mnohých z nich dala
zostaviť jedna úroveň, treba vedieť, kde každý bod pohľadu bol a v akých jednotkách. Táto stránka
pokrýva živé cesty; offline riešenie feed-forward je na [Offline rekonštrukcii](reconstruction-offline.md).

Kód: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamery {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` vytvorí dierkovú kameru z **horizontálneho zorného poľa**,
ktoré nastavíte v okne: `fx = (width / 2) / tan(fov / 2)`, štvorcové pixely (`fy = fx`), hlavný bod v
strede snímky. Hra nezverejňuje svoju projekciu, takže toto je jediné predpokladané číslo: príliš
úzke a scéna vyzerá hlbšie, než je. Offline cesta používa 65 stupňov.

`Pose` sa ukladá **svet-z-kamery**: `rotation` (3 x 3) a `translation` = stred kamery vo svete, čo chcú
trajektória, mapa pokrytia aj prekrytie.

## Vizuálna odometria (predvolená) {#visual-odometry-the-default}

`VisualOdometry` sleduje každú kľúčovú snímku oproti predchádzajúcej:

1. **Črty**: ORB, až 1500 na snímku, detegované len na maske sveta (pozrite
   [Zachytávanie](reconstruction-capture.md#what-is-not-the-world)).
2. **Zhody** s predchádzajúcou kľúčovou snímkou: hrubou silou, Hammingova vzdialenosť, krížová kontrola
   (len vzájomne najlepšie dvojice).
3. **Zdvihnutie do 3D**: hĺbka predchádzajúcej snímky je už vo svetových jednotkách, takže jej zhodné
   pixely sa stanú svetovými bodmi.
4. **Umiestnenie kamery**: `solvePnPRansac` medzi týmito bodmi (chyba premietnutia 3 px, istota 0,999,
   200 iterácií). Posun vyjde v rovnakých jednotkách, takže **mierka prechádza cez medzeru**.
5. **Zakotvenie hĺbky tejto snímky**: jej vlastná predpovedaná inverzná hĺbka sa prifituje
   (`fit_scale`) k hĺbkam vnútorných bodov PnP, a cyklus sa opakuje.

**Prvá snímka** je počiatok: jednotková poloha a jej afinné ladenie hĺbky je buď kalibrácia zeme nižšie,
alebo bez nej jednotková (rekonštrukcia je potom sama so sebou konzistentná, ale bez jednotiek).

Poloha potrebuje aspoň **18 vnútorných bodov RANSAC** – jasne viac než minimum PnP, šesť, lebo riešenie
z takmer dostatočného počtu bodov je presne to, ktoré sa sebavedome mýli.

### Istota {#confidence}

Každá umiestnená snímka dostane istotu v 0..1, ktorá váži jej fúziu a pokrytie:

| Poloha z | Istota |
|---|---|
| telemetrie | 1,0 |
| riešenia feed-forward | 0,85 |
| vizuálneho sledovania | `inliers / matches x min(1, inliers / 60)` |

### Keď sledovanie zlyhá {#when-tracking-breaks}

Snímka, ktorá sa nedá umiestniť, sa nahlási, nikdy sa neodhaduje: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Žiadna poloha sa nezapíše
a nič sa nefúzuje. Pokračovanie od poslednej polohy alebo začatie nového počiatku by umiestnilo
ďalší úsek levelu na ľubovoľný posun – zlom, ktorý vyzerá ako skutočná geometria.

Po prerušení sa každá nová snímka **relokalizuje** voči databáze minulých kľúčových snímok (každá 4.
sledovaná snímka sa pridá, až 120, najstaršie sa zahodia), od najnovšej, s rovnakým krokom zhody a
PnP. Kým jedna neuspeje, snímky sa zahadzujú. Obnovená snímka pokračuje v tom istom súradnicovom
rámci. Obnovy sa počítajú a zobrazujú v okne (`N recovered`).

### Uzavretie slučky: vypnuté {#loop-closure-off}

Tá istá databáza podporuje uzavretie slučky: porovnanie s kľúčovými snímkami z oveľa skoršieho obdobia,
aby sa zistil návrat na miesto a dráha sa k nemu pripnula. **Je vypnuté v predvolenom nastavení a skener
ho nikdy nezapne** (`Reconstructor(loop_closure=False)`). Na opakujúcom sa prostredí – rally etapa,
chodba, rad stromov – každý úsek vyzerá ako každý iný a porovnávanie čŕt potvrdí falošné návraty, čo
pripne kameru blízko miesta, kde začala, kým ide ďalej. Robiť to poriadne potrebuje rozpoznávanie miest
(slovník bag-of-words alebo naučený deskriptor) a geometrické overenie voči mape, a to nie je
postavené.

Keď sa zapne z kódu, uzavretie potrebuje: kľúčovú snímku aspoň 60 snímok starú, do 6 m od aktuálnej
polohy, zhodu s aspoň 90 vnútornými bodmi, pričom poloha sa posunie o viac ako 0,02 m a menej ako
6 m. Aj vtedy len nahradí aktuálnu polohu; nie je to graf polôh a nepohne skoršími snímkami ani
spojenou geometriou.

## Polohy z telemetrie {#telemetry-poses}

Keď je zapnuté **Racing telemetry (Forza) -> Listen for position data**, cesta kamery pochádza z
Data Out Forzy namiesto obrazov (`ForzaPoseSource`):

- Vlákno počúva na `127.0.0.1:<port>` (predvolene 5300) s rovnakým zisťovaním rozloženia ako nahrávače
  ([Forza](telemetry-forza.md)); pakety sa používajú, kým je nastavené `isRaceOn`. Obsadený port sa
  nahlási, nevyvolá výnimku: telemetria je vylepšenie a skenovanie pokračuje vizuálne.
- Každý paket dostane pečiatku **monotónneho času, kedy prišiel** – rovnaké hodiny, akými zachytávanie
  označuje snímky. Časový údaj hry sa počíta od niečoho nesúvisiaceho, takže sa na zarovnanie nepoužíva.
  Jitter na slučke o milisekundu alebo dve je pri 200 km/h asi 6 cm.
- Drží sa posuvný 30-sekundový buffer. Poloha snímky sa **interpoluje** zo vzoriek po oboch stranách jej
  časa zachytenia: poloha lineárne, rotácia sférickou interpoláciou (zmiešaná matica nie je rotácia a
  skreslila by každý bod). Cez medzeru dlhšiu ako **0,35 s**, alebo mimo bufferu, nie je poloha.
- `pose_from_forza`: kamera je umiestnená pri aute (odsadenie kamery za autom nie je zverejnené).
  **Polohy sa ponechávajú presne tak, ako ich hra posiela**: svet Forzy je už s osou Y hore (x a z po
  mape, y výška), tak ako ho zapisujú súbory kôl a trás, takže povrch dopadne na tie isté súradnice ako
  kolá nahraté nad ním. (Staršia verzia vymenila y a z pre svet „Z hore“ a položila trať na bok.)
- Rotácia je yaw, potom pitch, potom roll, so zmyslami odčítanými z nahratých kôl: smer jazdy
  `atan2(dx, dz)` sa rovná yaw, sklon do kopca sa rovná mínus pitch (kladné je nos dole) a roll je
  kladný, keď je pravé zavesenie stlačené (kladné spúšťa pravú stranu). Osi auta (x doprava, y hore,
  z dopredu) sa potom prevedú na osi kamery (x doprava, y dole, z dopredu) otočením y.
- Svet Forzy je **ľavoruký** a rámec kamery nie je, takže výsledná matica svet-z-kamery je zrkadlenie
  (determinant -1), a sken vyjde ľavoruký ako súbory kôl. Interpolácia sa tým nemení (otočenie medzi
  dvoma takýmito polohami je správna rotácia).
- Keď snímka nemá polohu z telemetrie (medzera), rekonštruktor sa pre túto snímku vráti k **vizuálnemu
  sledovaniu**, pokračuje od poslednej polohy z telemetrie a vráti sa k polohám zdroja, akonáhle odpovie.
  PnP vracia len rotácie, takže v zrkadlenom svete sa rieši so zrkadleným svetom cez z a zrkadlenie sa
  vráti späť; snímka tak pristane v súradniciach hry. Len keď zlyhá aj vizuálne sledovanie, je snímka
  nesledovaná.

### Mierka hĺbky z telemetrie {#depth-scale-from-telemetry}

Hra hovorí, kde je kamera, nie aká ďaleko je čokoľvek, takže hĺbka každej snímky sa stále musí zakotviť –
ale nie reťazením od nultej snímky, ktorej jednotka je ľubovoľná, kým polohy sú v metroch. Namiesto toho
sa črty spárované medzi predchádzajúcou a aktuálnou snímkou (aspoň 8) **triangulujú priamo z oboch
známych polôh**, v metroch, a mapa hĺbky sa prifituje k bodom pred kamerou. Každá snímka sa zakotví
voči telemetrii, takže nie je žiadna reťaz, ktorá by driftovala.

Ak sú obe polohy bližšie než **0,05 m**, lúče sú takmer rovnobežné a triangulácia je šum, takže snímka
ostane nezakotvená: presne umiestnená, ale nespojená („positioned, but its depth has no scale yet“).
Preto okno počíta *umiestnené* a *spojené* snímky osobitne.

## Mierka {#scale}

Vizuálna odometria správne reťazí relatívnu mierku, ale celá úroveň stále pláva na jednom neznámom
faktore. Relatívny výstup Depth Anything prichádza v ľubovoľných jednotkách, takže ak necháte prvú
snímku ako identitu, svet je v metroch od kamery v ľubovoľnej veľkosti.

`GroundCalibrator` pripne tento faktor z **toho, aké vysoko je kamera nad zemou**, meraného na **prvej
kľúčovej snímke** a, keď tam nie je použiteľná zem, na nasledujúcich:

- Výška kamery: **1,15 m** (línia očí vodiča) – okno to vždy používa; skripty môžu dať 1,70 m
  (`WALKING_HEIGHT`, stojaci hráč) alebo `None` (bez kalibrácie).
- Vzorka zeme: riadky 62–92 % zhora nadol (pod horizontom, nad kapotou alebo zbraňou) a stĺpce 30–70 %
  naprieč (ďaleko od krajníc).
- Každý pixel tam s použiteľnou predikciou sa zdvihne s hĺbkou `1 / predicted` v jednotkách siete;
  body pod optickou osou dajú výšku pod kamerou. Ich medián je výška kamery v jednotkách siete, takže
  `metres per unit = 1.15 / median` a afinné ladenie snímky je `scale = 1 / metres_per_unit`, posun 0.
- Dôveruje sa len pri aspoň 200 vzorkách zeme a **rozptyle** (medián absolútnej odchýlky delený mediánom)
  pod **0,60**.
- Na prvej kľúčovej snímke sa fit stane jednotkou počiatku, takže sken je od začiatku v metroch. Keď
  prvá kľúčová snímka nemá použiteľnú zem, sken začne bez jednotiek a každá neskoršia sledovaná
  kľúčová snímka sa skúsi, až do **30 snímok** celkom. Prvá, ktorá kalibruje, dá *metre na jednotku*:
  medián, cez pásmo zeme, z hĺbky, ktorú jej zem implikuje, delenej hĺbkou, ktorú reťaz dala tej snímke.
  Všetko už spojené je v jednotke prvej snímky, takže faktor sa nevracia do reťaze; aplikuje sa na celú
  úroveň (a na označené miesta), keď sa zapisuje, a na zobrazenú vzdialenosť medzitým. Veľkosť voxelu je
  potom v jednotke prvej snímky, takže jej veľkosť v metroch sa líši od nastavenia o tento faktor.
- Po 30 snímkach bez zeme zostane sken bez jednotiek a hovorí to.
- S telemetriou sa neskoršie kľúčové snímky neskúšajú: hĺbka sa zakotví v metroch telemetrie.

Byť v rámci desať percent skutočnej veľkosti je lepšie než byť mimo faktor tisíc; telemetria, kde je
k dispozícii, to robí zbytočným. Poznámka sa zobrazuje v okne pod riadkom sledovania ako `Size: ...`:
`measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`,
`scaled from a 1.15 m camera height, ...` (s `found on frame N, so the level is scaled by F when it is
written`, keď to prišlo neskôr), `no usable ground in the first N frames - sizes are relative, not
metres`, alebo `in metres, from the telemetry's positions`.

## Vyrovnanie zväzku a dlhé stopy (nezapojené) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dva kusy existujú pre budúci okenný riešiteľ a **skener ich nepoužíva**:

- **`FeatureTracks`** drží identitu čŕt naprieč stovkami snímok sledovaním Lucasom-Kanadeom (600 čŕt,
  doplnených pod 60 %, tolerancia dopredu a dozadu 1 px, nové črty 10 px od existujúcich), čo potrebuje
  vyrovnanie zväzku – zhoda deskriptorov medzi po sebe idúcimi snímkami dá len dvojice.
- **`bundle_adjust`** spresní okno polôh a bodov naraz pomocou `scipy.optimize.least_squares`
  (oblasť dôvery, strata soft-L1 so škálou 2 px, explicitný vzor rozrieďovania Jacobiánu, pevné kamery
  obnovené presne). Testované voči známej pravde v `tests/test_bundle.py`.

`WindowedOdometry` ich spája (okná po 12 kľúčových snímkach, riešenie každé 3 kľúčové snímky, prvé dve
kamery pevné, body s chybou nad 6 px zahodené, skoky nad 6-násobok nedávneho kroku odmietnuté). Jeho
docstring zaznamenáva, že na reálnom zábere **zrútil dráhu a bol oveľa pomalší** než sledovanie
snímka-po-snímke, s voľnosťou kalibrácie (mierkou) a bootstrapom založeným na hĺbke ako známymi
príčinami a treťou príčinou neidentifikovanou. Preto zostáva predvolenou odometria snímka-po-snímke;
pravdepodobná oprava uvedená v kóde je bootstrap dvoch pohľadov cez esenciálnu maticu so základňou pevnou z kalibrácie roviny zeme.
