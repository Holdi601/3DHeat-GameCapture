---
title: "Zachytávanie, masky a kvalita snímok"
nav_order: 2
lang: "sk"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Zachytávanie, masky a kvalita snímok {#capture-masks-and-frame-quality}

Kód: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Odkiaľ prichádzajú snímky {#where-frames-come-from}

Cieľ zdroja je jeden z:

| Cieľ | Zdroj | Poznámky |
|---|---|---|
| `monitor:<n>` | celý monitor, naživo | „Whole screen“ okna s číslom v „Which“ |
| `window:<title>` | jedno okno, naživo | „A window“ okna s jeho názvom |
| cesta k súboru | video súbor | „A video file“ okna; ľubovoľný formát, ktorý dokáže OpenCV čítať |

### Živé zachytávanie: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` používa balík `windows-capture`, ktorý obaľuje **Windows Graphics Capture** –
verejné API, ktoré používajú nahrávače obrazovky. Do hry sa nič nevkladá. Kurzor sa nezachytáva
a nekreslí sa žltý rámik zachytávania.

Knižnica zachytávania doručuje snímky spätnému volaniu na vlákne kompozítora a očakáva, že sa
hneď vráti, takže toto volanie len skopíruje snímku (vyrovnávacia pamäť sa znovu používa), prevedie
BGRA na RGB, zmení veľkosť, označí ju časovou pečiatkou a vloží do frontu **4 snímok**. Keď je
front plný, **najstaršia snímka sa zahodí** a počítadlo stúpne: zaostávanie má stáť snímky, nie
pamäť či správnosť, a živý náhľad má ukazovať, kde je hráč teraz. Zahodené snímky sa ukážu v
riadku štatistík okna a keď ich je viac ako polovica, zobrazí sa tip.

Každá snímka nesie `t` (sekundy od začiatku zachytávania) a `monotonic` (surový `time.monotonic()`
pri zachytení), rovnaké hodiny, s ktorými sa označujú aj telemetrické pakety – vďaka tomu sa dajú
polohy Forzy zarovnať so snímkami.

`windows-capture` je pri kontrole závislostí voliteľný: bez neho sa dá video súbor stále skenovať.

### Video súbory {#video-files}

`VideoSource` číta cez OpenCV, prevádza na RGB a mení veľkosť. Kontajner bez snímkovej frekvencie
sa berie ako 30 fps. Časové pečiatky sú index snímky delený snímkovou frekvenciou; súbor nemá čas
podľa hodín, takže telemetriu nemožno zarovnať s videom.

### Rozlíšenie {#resolution}

Snímky sa menia na veľkosť už pri zdroji tak, aby najdlhšia strana bola stranou zachytenia podľa
predvoľby (Draft 640, Balanced 960, Detailed 1280 px), s interpoláciou podľa plochy. Snímka 4K má
tridsaťkrát viac pixelov, než používa model hĺbky.

## Kľúčové snímky {#keyframes}

Takmer každá snímka zachytenia je nadbytočná: stáť na mieste dá stovky pohľadov na jednu vec.
Rekonštrukcia chce *paralaxu*. Preto sa snímka nedrží podľa časovača, ale podľa **toho, koľko sa
obraz zmenil od poslednej zachovanej snímky**.

`picture_change(a, b)`:

1. obe snímky na sivé a na mriežku 16 x 16 blokových priemerov (blokové priemery reagujú na pohyb
   obrazu, nie na zrno, lístie, blikanie ani HUD);
2. priemerný absolútny rozdiel ako zlomok 255;
3. keď je známa maska sveta, každý blok sa váži podielom, ktorý je svet a nie kokpit, takže blok z
   polovice kokpitom sa počíta polovicou (používa sa, keď maska pokrýva viac ako 5 % váhy mriežky).

Prah sa **prispôsobuje zachyteniu**: prvých 30 snímok má predvolenú začiatočnú hodnotu predvoľby
(0,020 / 0,010 / 0,004), potom je to kvantil predvoľby (0,85 / 0,65 / 0,40) z posledných 240
nameraných zmien, nikdy pod 0,0001. Snímka sa zachová, keď jej zmena dosiahne prah; prvá snímka sa
vždy zachová. Pevný prah nemôže fungovať naprieč scénami – zmena medzi snímkami v tmavom kokpite
kola je zlomok zmeny v svetlej texturovanej izbe –, zatiaľ čo „nechať najrušnejšiu tretinu“ znamená
v oboch to isté. Prah v použití ide von s každou aktualizáciou priebehu (`ScanProgress.threshold`),
a ukazovatele rýchlosti chôdze v okne a v prekrytí merajú poslednú zmenu voči nemu
(`ScanProgress.toward_next_view`).

Len zachované snímky idú cez model hĺbky a rekonštrukciu. Snímky sa neukladajú, pokiaľ si to volajúci
nevyžiada (`keep_frames`); 160 z nich sa drží na sfarbenie siete (pozrite [farba](reconstruction-fusion-and-texture.md#colour)).

Skenovanie končí, keď ho zastavíte, keď video dôjde alebo pri limite času či kľúčových snímok.

## Čo nie je svet {#what-is-not-the-world}

Dve veci v hernej snímke nie sú geometriou úrovne a obe rozbíjajú rekonštrukciu:

- **HUD.** Zameriavač je najopakovateľnejšia črta v akejkoľvek snímke. Porovnávač čŕt ho miluje,
  dokonale sa zhoduje medzi každými dvoma snímkami a každá zhoda je dôkaz, že kamera sa nehla –
  čo stlačí celú rekonštrukciu.
- **Veci pripevnené ku kamere.** Zbraň, kapota, rám kokpitu, palubná doska. Skutočná geometria
  v zlom súradnicovom systéme: pri fúzii sa rozmaže po celej dráhe, ktorou sa prešlo.

Dva detektory ich nájdu. Obidva vytvárajú masku (255 = svet, 0 = nie svet) alebo `None`, kým nie je
dostatok dôkazov; `None` vždy znamená „použi všetko“, nikdy „nepoužívaj nič“.

Maska sa použije:

- pri **detekcii čŕt** vo vizuálnej odometrii (vyradenie zameriavača z výstupu, pričom by ešte hlasoval
  o polohe, by opravilo viditeľný príznak a nechalo škodlivý);
- na **spojené pixely**, takže sa nefúzuje geometria kokpitu;
- na mieru **ostrosti a jasu**, pretože kokpit je vždy dokonale ostrý;
- na **zmenu obrazu**, ktorá rozhoduje o kľúčových snímkach.

**Nepoužije sa** na snímky dané offline riešiteľovi VGGT (pozrite
[Offline rekonštrukcia](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: čo sa nemení {#screenmask-what-does-not-change}

Používa sa od prvej kľúčovej snímky, kým FlowMask nie je pripravený.

- Každá snímka sa prevedie na sivú, zmenší na polovicu a rozmaže (Gaussov filter 3 x 3), aby
  jednopixelové chvenie v statickom prvku HUD nevyzeralo ako pohyb.
- Absolútny rozdiel každého pixelu oproti predchádzajúcej snímke sa zloží do exponenciálneho
  priemeru (rozpad 0,9), takže maska sleduje HUD, ktorý sa objaví alebo zmizne uprostred skenovania.
- Učí sa len zo snímok, kde sa kamera známe hýbe (pri skenovaní: keď je sledovaná aspoň jedna
  snímka) – zaparkovaná kamera robí všetko statické.
- Po **12** učiacich snímkach je pixel statický, keď jeho priemerná zmena je pod **0,22** mediánu
  zmeny snímky – relatívne, takže prah sleduje, ako rýchlo sa hráč hýbe.
- Keď je viac ako **45 %** snímky statických, predpoklad zlyhal (menu, prestrihová scéna) a nič sa
  nemaskuje.
- Maska sa zmenší o jeden pixel (okraje HUD s vyhladením nepatria ani jednej strane) a vráti sa na
  plnú veľkosť.

Jej poznámka v okne: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, alebo `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: čo sa nikdy nehýbe {#flowmask-what-never-travels}

Kokpit nie je statický: ihly sa pohybujú, otáčkomer cukne, mapa sa otáča, takže detektor zmeny
označí tieto pixely ako svet – a sú to najhoršie črty na dodanie riešiteľovi polohy. FlowMask kladie
lepšiu otázku: **ktoré črty pretrvávajú bez toho, aby sa hýbali?**

- Pri živom skenovaní sa učí raz, z prvých **40 kľúčových snímok** (sivé); potom nahradí ScreenMask
  pre zvyšok skenovania.
- Snímky sa rozdelia na okná po **30** snímkach, prekrývajúce sa o polovicu. V každom okne sa zasiahne
  až 800 rohov (`goodFeaturesToTrack`, kvalita 0,01, 8 px od seba) a sledujú sa pyramídovým
  Lucasom-Kanadeom (21 x 21, 4 úrovne) s **kontrolou dopredu a dozadu**: stopa, ktorej tok dozadu
  nedopadne do 1 px od miesta začiatku, sa zahodí, lebo sledovač, ktorý zablúdi na susedný vzor, by
  vyrobil presne ten podpis „pretrváva, ale nehýbe sa“, ktorý sa hľadá. Okná kratšie ako 20 snímok sa
  preskakujú. Krátke okná sú dôležité: pri dlhom behu takmer každá svetová črta opustí snímku a dôkaz
  sa stenčí na nič.
- Čistý pohyb každej zachovanej črty sa porovnáva s **2 % šírky snímky**: pod touto hodnotou je
  „zaseknutá“, nad ňou „v pohybe“. Počty sa zbierajú v mriežke **24 x 24** buniek obrazovky podľa
  toho, kde črta začala.
- Bunka je blokovaná, keď obsahuje aspoň 2 zaseknuté črty a viac zaseknutých než pohybujúcich sa,
  **a** aspoň 3 z jej 8 susedov sú tiež blokované (samotná bunka je šum; tmavý záznam ich vytvára
  veľa).
- Zachovajú sa len blokované oblasti **spojené s okrajom snímky**. Všetko pripevnené ku kamere
  dosahuje okraj obrazovky; čo sedí v strede a nehýbe sa, je bod úniku – pri jazde dopredu je cesta
  priamo pred vami bez toku a je to geometria, ktorú najviac chceme.
- Zostávajúca oblasť sa zväčší o jednu bunku (okraj prístrojovej dosky je gradient).
- Keď by sa maskovalo viac ako **60 %** snímky, nemaskuje sa nič: v nočnom zázname väčšina buniek
  neobsahuje sledovateľnú črtu, čo vyzerá rovnako ako ciferník.

Jej poznámka: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, alebo po 60 % správa, že nič nemaskuje.

Offline cesta sa učí ten istý FlowMask zo 4 behov po 90 po sebe idúcich snímkach rozložených
po videu, pri 960 x 540 ([Offline](reconstruction-offline.md)).

## Kvalita snímok a rady {#frame-quality-and-advice}

`QualityWatcher` posudzuje každú kľúčovú snímku a vyberie **jednu** inštrukciu, aby prekrytie mohlo
povedať „spomaľte“, kým je na to ešte čas.

Na každej snímke meria, len na pixeloch sveta (všetky pixely, ak maska zostane pod 5 %):

- **ostrosť**: rozptyl Laplaciánu – štandardná jednoprechodová miera a reaguje presne na to, čo
  rozmazanie od pohybu ničí;
- **svetlosť**: priemerná úroveň sivej, 0–255.

Ostrosť nemá absolútnu mierku (nočná etapa a svetlá ulica sa líšia o rád, obidve sú v ostrom
zaostrení), preto sa posudzuje voči **bežiacemu mediánu tohto zachytenia**: posledných 90 snímok,
pričom na akýkoľvek úsudok treba 20. Každá snímka sa porovnáva s históriou *pred* sebou, takže dlhý
rozmazaný úsek nemôže stiahnuť medián tak, aby sa k nemu sám prispôsobil.

| Podmienka | Test |
|---|---|
| plochá | ostrosť najviac 1,0 (načítavacia obrazovka, stena, obloha) |
| tmavá | svetlosť pod 26 |
| rozmazaná | ostrosť pod 0,55 mediánu a nie plochá |

Rada, prvá zhoda vyhráva (zoradené podľa toho, čo skenovanie najviac blokuje):

| Situácia | Rada | Stupeň |
|---|---|---|
| menej ako 20 snímok | Zisťujem, aký je obraz… | ok |
| plochá | Nie je čo merať – nasmerujte kameru na level, nie na oblohu. | stop |
| tmavá | Príliš tmavé na rekonštrukciu. Zapnite svetlá alebo jazdite tento úsek za denného svetla. | stop |
| rozmazaná | Rozmazané – spomaľte. | warn |
| sledovaných menej ako polovica snímok | Strácam sledovanie – spomaľte a nechajte v zábere viac levelu. | warn |
| spojených menej ako 40 % sledovaných snímok | Polohy sú dobré, ale hĺbka sa nedrží. Jazdite bližšie k scenérii. | warn |
| existujú slabé miesta | N slabých miest – mapa ich označuje. | ok |
| inak | Dobré – pokračujte. | ok |

Prekrytie farbí rady podľa stupňa (zelená / oranžová / červená). Lišta **ostrosti** v prekrytí je
ostrosť snímky voči mediánu. (Kód má tiež „Blurred, and the camera is not moving. Check the
capture.“ pre nehybnú kameru; skenovanie vždy hlási kameru ako pohybujúcu sa, takže sa to nezobrazuje.)
