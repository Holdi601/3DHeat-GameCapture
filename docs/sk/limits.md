---
title: "Obmedzenia a overenie"
nav_order: 9
lang: "sk"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Obmedzenia a čo je overené {#limits-and-what-is-verified}

Úprimný zoznam: čo nástroje nerobia a čo sa neoverilo voči bežiacej hre.

## Telemetria {#telemetry}

| Rekordér | Stav |
|---|---|
| Forza | Postavený na oficiálnej dokumentácii Data Out; rozloženie sa zisťuje z samotných paketov. Čítačka `.tele.gz` z FH Companion vo prehliadači bola overená na skutočných kolách. |
| AC, ACC, AC EVO, AC Rally | Testované na syntetických stránkach postavených z publikovaných rozložení. **Zatiaľ nespustené proti živým hrám.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testované na paketoch postavených z zdokumentovaných rozložení. **Zatiaľ nespustené proti živým hrám.** Osi, postoj a jednotky rýchlosti RBR nie sú zdokumentované a spracúvajú sa podľa dát. |
| BeamNG.drive | Rekordér je testovaný na paketoch postavených zo štruktúry modu. **Mod sa v hre nespustil.** |
| Trackmania | Čítačka CSV vo prehliadači je testovaná. **Plugin sa v hre nespustil.** Načítava sa len v režime vývojára Openplanet. |
| iRacing | Čítačka `.ibt` vo prehliadači je testovaná na syntetickom súbore. |

Ďalšie obmedzenia telemetrie:

- Normalizácia šmyku Forzy nie je zdokumentovaná; šmyk Kunos je škálovaný typickým vrcholom asfaltu, čo je aproximácia.
- Zmysel niektorých bočných osí karosérie (Kunos, DiRT) je zdokumentovaný oboma smermi; veľkosť uhla driftu je spoľahlivá, jej znamienko nie.
- Žiadna z rally hier neposiela šmyk kolies; odvodzuje sa vo prehliadači. RBR neposiela rýchlosti kolies.
- Povrch rally etapy sa zapisuje len vtedy, keď je zadané `--surface`; inak súbor nič nepomenuje a prehliadač ho odhadne (názov etapy alebo udalosti, potom štýl jazdy, predvolene voľne).
- Detekcia kola bez počítadla kôl (AC EVO, AC Rally, BeamNG) používa ako čiaru bod, kde sa začalo nahrávať, preto spustite nahrávanie na štartovej čiare.
- Reset vozidla v BeamNG uzavrie kolo otvorené v tom okamihu: zapíše sa ako čiastočná jazda, ak prešlo minimálnu vzdialenosť (300 m), inak sa zahodí.
- `route` ukladá asi každé 2 sekundy počas jazdy; pád alebo zabitý proces stratí najviac pozície od posledného uloženia.
- Forza Horizon neposiela názov trate, takže súbory kôl Forzy majú `"track": null`; Forza Motorsport (2023) posiela len číslo, uložené ako `lap.trackOrdinal`.

## Rekonštrukcia {#reconstruction}

- **Hĺbka sa odhaduje, nečíta sa.** Strop celého prístupu a cena za to, že sa nikdy nedotýka procesu hry.
- **Zorné pole sa predpokladá, nemeria sa.** Príliš úzke a úroveň sa zrekonštruuje hlbšie, než je.
- **Globálna mierka** pochádza z predpokladanej výšky kamery (1,15 m v okne) alebo z telemetrie. Meria sa na prvom kľúčovom snímku; keď tam nie je použiteľná zem, skúsia sa ďalšie kľúčové snímky (až 30 snímok) a mierka nájdená neskôr sa použije na celú úroveň pri zápise. Riadok „Size:“ v okne hovorí, čo sa stalo; keď sa nenašla žiadna zem, skenovanie zostane bez jednotiek. Veľkosť voxela je v jednotkách prvého snímku v tom prípade, takže jeho veľkosť v metroch sa líši od nastavenia. Offline rekonštrukcie sú v jednotkách riešenia.
- **Uzavretie slučky je vypnuté** a nie je to graf pózy, keď sa zapne v kóde; drift je ohraničený len kvalitou sledovania medzi susednými snímkami.
- **Okenná bundle adjustment existuje, ale nie je zapojená**; na skutočnom zábere sa zrútila.
- **Povrch je vážená obsadenosť, nie TSDF**: tenké štruktúry a voľný priestor sú horšie, než by ich TSDF zachytil.
- **Bez atlasu textúr.** Farba je na vrchole (`COLOR_0`), zmiešaná z 4 najlepších pohľadov spomedzi 160 zachovaných snímok. Test zakrytia je hrubý: porovnáva sa s vlastnými vrcholmi siete v hĺbkovom buffri 2 pixle, takže zakrývajúci objekt, ktorý sieť neobsahuje (prechádzajúce auto), sa nezachytí.
- **Voda sa nikdy neoznačuje**; všetko je zem alebo stavba.
- **Riešenie podľa predikcie nie je živé**: potrebuje najprv nahrávku. Adaptívne preriešenie náročných úsekov nie je postavené.
- **Telemetrické pózy** umiestňujú kameru na auto (posun kamery pri chase nie je známy). Pozície sa berú tak, ako ich posiela Forza (Y nahor, ako v súboroch kôl); zmysel yaw, pitch a roll sa odčítal zo zaznamenaných kôl (smer jazdy, sklon, ktorá strana odpruženia sa stláča), nie z kamery bežiacej hry.
- Prekrytie sa nedá kresliť nad **exkluzívnym celoobrazovkovým režimom**; použite okno bez okrajov (borderless windowed).
- Globálne klávesové skratky, prekrytie prepúšťajúce kliknutia a živé snímanie sú **len na Windows**.
- Zatvorenie okna sa neopýta na uloženie.

## Čo je merané {#what-is-measured}

- `tests/test_accuracy.py`: syntetická izba so známou trasou a analytickou hĺbkou – umiestnené snímky, chyba trasy, prejdená vzdialenosť, veľkosť izby, povrch na stenách ([Rekonštrukcia úrovne](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: cesta známej šírky, prejdená mimo stredu, sa zrekonštruuje so svojou šírkou.
- `tests/test_track_scale.py`: extrakcia povrchu v mierke okruhu, pamäť úmerná tomu, čo bolo naskenované, bloky, ktoré sa spájajú do jedného povrchu.
- `tests/test_glb.py` spolu s vlastnými testami prehliadača: kontrakt `.glb` z oboch strán.
- Ako hĺbková sieť funguje na skutočnej hre, syntetická scéna nezodpovie a testovacia sada to nemeria.
