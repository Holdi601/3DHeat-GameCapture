---
title: "Záběr, masky a kvalita snímků"
nav_order: 2
lang: "cs"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Záběr, masky a kvalita snímků {#capture-masks-and-frame-quality}

Kód: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Odkud přicházejí snímky {#where-frames-come-from}

Cíl zdroje je jedno z následujícího:

| Cíl | Zdroj | Poznámky |
|---|---|---|
| `monitor:<n>` | celý monitor, živě | v okně „Celá obrazovka“ s číslem v „Který“ |
| `window:<title>` | jedno okno, živě | v okně „Jedno okno“ s jeho názvem |
| cesta k souboru | videosoubor | v okně „Videosoubor“; libovolný formát, který umí OpenCV číst |

### Živý záznam: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` používá balíček `windows-capture`, který obaluje **Windows Graphics
Capture** - veřejné API, které používají nahrávače obrazovky. Do hry se nic
nevstřikuje. Kurzor se nezachytává a nekreslí se žádný žlutý rámeček zachycení.

Knihovna zachycení doručuje snímky zpětným voláním na vlákně kompozitoru a očekává,
že se volání hned vrátí. Proto zpětné volání jen zkopíruje snímek (vyrovnávací paměť
se znovu používá), převede BGRA na RGB, změní velikost, označí časem a vloží do
fronty na **4 snímky**. Když je fronta plná, **nejstarší snímek se zahodí** a
zvýší se počítadlo: když nestíhání stojí snímky, má to stát snímky, ne paměť nebo
správnost, a živý náhled má ukazovat, kde hráč je právě teď. Zahozené snímky se
ukazují v řádku statistik okna a když jich zahodí více než polovina, objeví se
nápověda.

Každý snímek nese `t` (sekundy od začátku zachycení) a `monotonic` (surový
`time.monotonic()` v okamžiku zachycení), tedy stejné hodiny, jakými se označují
telemetrické pakety - díky tomu lze pozice Forzy srovnat se snímky.

`windows-capture` je v kontrole závislostí nepovinný: bez něj lze stále skenovat
videosoubor.

### Videosoubory {#video-files}

`VideoSource` čte pomocí OpenCV, převádí na RGB a mění velikost. Kontejner bez
snímkové frekvence se bere jako 30 fps. Časy jsou index snímku dělený snímkovou
frekvencí; soubor nemá čas nástěnných hodin, takže telemetrii nelze zarovnat
s videem.

### Rozlišení {#resolution}

Snímky se při čtení zmenší tak, aby delší strana byla velikost záznamu z předvolby
(Rychlá 640, Vyvážená 960, Podrobná 1280 px), s plošnou interpolací. Snímek 4K má
třicetkrát více pixelů než model hloubky používá.

## Klíčové snímky {#keyframes}

Téměř každý snímek záznamu je nadbytečný: stání na místě dá stovky pohledů na
jednu věc. Rekonstrukce potřebuje *paralaxu*. Snímek se proto nenechá podle
časovače, ale podle toho, **jak moc se obraz změnil od posledního zachovaného
snímku**.

`picture_change(a, b)`:

1. oba snímky se převedou na šedou a zmenší na mřížku 16 x 16 průměrů bloků (průměry
   bloků reagují na pohyb obrazu, ne na zrno, listí, blikání nebo HUD);
2. střední absolutní rozdíl jako zlomek 255;
3. je-li známa maska světa, každý blok se váží podílem, který je svět a ne kokpit,
   takže blok napůl zakrytý palubní deskou se počítá poloviční (používá se, jakmile
   maska pokrývá více než 5 % váhy mřížky).

Práh se **přizpůsobuje záznamu**: prvních 30 snímků používá výchozí hodnotu
předvolby (0,020 / 0,010 / 0,004), potom kvantil předvolby (0,85 / 0,65 / 0,40)
posledních 240 změřených změn, nikdy méně než 0,0001. Snímek se zachová, když jeho
změna dosáhne prahu; první snímek se vždy zachová. Pevný práh nemůže fungovat napříč
scénami - změna mezi snímky v temném kokpitu za jízdy je zlomek změny v jasné
texturované místnosti -, zatímco „nechej nejrušnější třetinu“ znamená totéž v obou.
Práh v užití se posílá s každou aktualizací průběhu (`ScanProgress.threshold`) a
lišty rychlosti chůze v okně a v překryvu měří poslední změnu proti němu
(`ScanProgress.toward_next_view`).

Jen zachované snímky jdou přes model hloubky a rekonstrukci. Snímky se neukládají,
pokud o to volající nepožádá (`keep_frames`); 160 z nich se drží pro obarvení sítě
(viz [barva](reconstruction-fusion-and-texture.md#colour)).

Skenování skončí, když se zastaví, když video dojde, nebo při limitu času nebo klíčových
snímků.

## Co není svět {#what-is-not-the-world}

Dvě věci v herním snímku nejsou geometrií levelu a obě rekonstrukci zničí:

- **HUD.** Zaměřovač je nejopakovatelnější prvek v jakémkoli snímku. Porovnávač
  rysů ho miluje, dokonale se shoduje mezi každými dvěma snímky, a každá shoda je
  důkaz, že kamera se nehnula - což celou rekonstrukci stlačí.
- **Věci připevněné ke kameře.** Zbraň, kapota, rám kokpitu, palubní deska. Skutečná
  geometrie ve špatné souřadné soustavě: sloučena se rozmaže podél celé dráhy.

Dva detektory je najdou. Oba vytvoří masku (255 = svět, 0 = ne svět), nebo `None`,
dokud není důkazů dost; `None` vždy znamená „použij vše“, nikdy „nepoužij nic“.

Maska se použije:

- při **detekci rysů** ve vizuální odometrii (maskování zaměřovače z výstupu, zatímco
  ho nechá hlasovat o poloze, by opravilo viditelný příznak a ponechalo škodlivý);
- na **sloučené pixely**, aby se nesloučila žádná geometrie kokpitu;
- na měření **ostrosti a jasu**, protože kokpit je vždy dokonale ostrý;
- na **změnu obrazu**, která rozhoduje o klíčových snímcích.

Nepoužije se na snímky předávané offline řešiteli VGGT (viz
[Offline rekonstrukce](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: co se nemění {#screenmask-what-does-not-change}

Používá se od prvního klíčového snímku, dokud FlowMask není připraven.

- Každý snímek se převede na šedou, zmenší na polovinu a rozmaže (Gaussovo 3 x 3),
  aby jednopixelové chvění statického prvku HUD nevypadalo jako pohyb.
- Absolutní rozdíl každého pixelu od předchozího snímku se složí do exponenciálního
  průměru (rozpad 0,9), takže maska sleduje HUD, který se objeví nebo zmizí uprostřed
  skenování.
- Učí se jen z snímků, kde je známo, že se kamera hýbe (ve skenování: jakmile je
  sledován aspoň jeden snímek) - stojící kamera všechno dělá statickým.
- Po **12** snímcích učení je pixel statický, když jeho průměrná změna je pod
  **0,22** mediánu změny snímku - relativně, takže práh sleduje, jak rychle se hráč
  hýbe.
- Když je více než **45 %** snímku čteno jako statické, předpoklad selhal (menu,
  scénka) a nic se nemaskuje.
- Maska se zmenší o jeden pixel (zubaté hrany HUD nepatří ani jedné straně) a
  zvětší zpět na plnou velikost.

Jeho poznámka v okně (v originále anglicky, tak jak ji okno ukazuje): `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected`, nebo `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: co se nikdy nehýbe {#flowmask-what-never-travels}

Kokpit není statický: ručičky se pohybují, otáčkoměr cuká, mapka se otáčí, takže
detektor změny považuje ty pixely za svět - a jsou to nejhorší rysy, které lze dát
řešiteli polohy. FlowMask klade lepší otázku: **které rysy přetrvají, aniž by se
pohnuly?**

- Při živém skenování se učí jednou, z prvních **40 klíčových snímků** (ve stupních
  šedi); pak nahradí ScreenMask na zbytek skenování.
- Snímky se rozdělí do oken po **30** snímcích, překrývajících se napůl. V každém
  okně se zasévá až 800 rohů (`goodFeaturesToTrack`, kvalita 0,01, 8 px od sebe) a
  sledují se pyramidovým Lucas-Kanade (21 x 21, 4 úrovně) s **kontrolou dopředu a
  dozadu**: stopa, jejíž zpětný tok nepřistane do 1 px od místa startu, se zahodí,
  protože sledovač, který zabloudí na sousední vzor, by vyrobil přesně ten podpis
  „přetrvává, ale stojí“, který se hledá. Okna kratší než 20 snímků se přeskočí.
  Krátká okna mají význam: během dlouhého běhu téměř každý svět prvek opustí snímek
  a důkazy se ztenčí na nic.
- Čistý pohyb každého zachovaného rysu se srovná s **2 % šířky snímku**: pod ním je
  „zaseklý“, nad ním „pohybující se“. Počty se sčítají na mřížce **24 x 24**
  obrazovkových buněk podle místa, kde rys začal.
- Buňka je blokována, když obsahuje alespoň 2 zaseklé rysy a zaseklých je víc než
  pohybujících se, **a** alespoň 3 z jejích 8 sousedů jsou také blokované (osamělá
  buňka je šum; tmavý záznam jich dělá spoustu).
- Zachovají se jen blokované oblasti **spojené s okrajem snímku**. Všechno připevněné
  ke kameře sahá k okraji obrazovky; co leží uprostřed a nehýbe se, je úběžník -
  při jízdě vpřed je silnice přímo před vámi bez proudu a je to geometrie, kterou
  nejvíc potřebujeme.
- Zachovaná oblast se rozroste o jednu buňku (hrana přístrojového panelu je
  přechod).
- Když by bylo maskováno více než **60 %** snímku, nemaskuje se nic: v noci většina
  buněk neobsahuje sledovatelný rys, což vypadá stejně jako ciferník.

Jeho poznámka (anglicky, jak ji okno ukazuje): `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, nebo při více než 60 % hláška, že se nemaskuje nic.

Offline cesta se učí stejný FlowMask ze 4 běhů po 90 po sobě jdoucích snímcích
rozložených po videu, při 960 x 540 ve stupních šedi ([Offline](reconstruction-offline.md)).

## Kvalita snímků a rady {#frame-quality-and-advice}

`QualityWatcher` posoudí každý klíčový snímek a vybere **jednu** instrukci, aby
překryv mohl říct „zpomal“, dokud je na to čas.

Na snímek měří, jen na pixelech světa (všechny pixely, když maska zůstane pod 5 %):

- **ostrost**: rozptyl Laplaceova operátoru - standardní jednoprůchodová míra, která
  reaguje přesně na to, co pohybové rozmazání ničí;
- **jas**: průměrná úroveň šedi, 0-255.

Ostrost nemá absolutní měřítko (noční etapa a jasná ulice se liší o řád, obě jsou
ostré), proto se posuzuje proti **běžícímu mediánu tohoto záznamu**: posledních 90
snímků, přičemž 20 je potřeba, než se cokoli posoudí. Každý snímek se srovnává s
historií *před* jeho přidáním, takže dlouhý rozmazaný úsek nemůže median stáhnout
dolů, aby se s ním vyrovnal.

| Podmínka | Test |
|---|---|
| plochý | ostrost nejvýše 1,0 (načítací obrazovka, zeď, obloha) |
| tmavý | jas pod 26 |
| rozmazaný | ostrost pod 0,55 mediánu a není plochý |

Rada, první shoda vyhrává (seřazeno podle toho, co skenování nejvíc blokuje):

| Situace | Rada | Úroveň |
|---|---|---|
| méně než 20 snímků | `Getting a feel for the picture…` | ok |
| plochý | `Nothing to measure — point the camera at the level, not at the sky.` | stop |
| tmavý | `Too dark to reconstruct. Headlights on, or drive this stretch in daylight.` | stop |
| rozmazaný | `Blurred — slow down.` (a `Blurred, and the camera is not moving. Check the capture.` pro stojící kameru) | warn |
| méně než polovina snímků sledována | `Losing track — slow down and keep more of the level in view.` | warn |
| méně než 40 % sledovaných snímků sloučeno | `Positions are good but depth is not sticking. Drive nearer the scenery.` | warn |
| existují slabá místa | `N thin spots — the map marks them.` | ok |
| jinak | `Good — keep going.` | ok |

Úroveň obarvuje radu překryvu (zelená / jantarová / červená). Ukazatel **ostrosti**
v překryvu je ostrost snímku vůči mediánu. (Kód má také „Blurred, and the camera is
not moving. Check the capture.“ pro stojící kameru; skenování hlásí kameru vždy jako
pohybující se, takže se nezobrazuje.)
