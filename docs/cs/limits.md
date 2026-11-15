---
title: "Omezení a ověření"
nav_order: 9
lang: "cs"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Omezení a co je ověřeno {#limits-and-what-is-verified}

Upřímný seznam: co nástroje nedělají a co nebylo ověřeno proti běžící hře.

## Telemetrie {#telemetry}

| Záznamník | Stav |
|---|---|
| Forza | Postaveno podle oficiální dokumentace Data Out; rozložení se zjišťuje z paketů samotných. Čtečka `.tele.gz` z FH Companion v prohlížeči byla ověřena na skutečných kolech. |
| AC, ACC, AC EVO, AC Rally | Testováno na syntetických stránkách postavených podle publikovaných rozložení. **Zatím nespuštěno proti živým hrám.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testováno na paketech postavených podle zdokumentovaných rozložení. **Zatím nespuštěno proti živým hrám.** Osy, postoj a jednotky rychlosti RBR nejsou zdokumentované a zpracovávají se podle dat. |
| BeamNG.drive | Záznamník je testován na paketech postavených podle struktury modu. **Mod nebyl spuštěn ve hře.** |
| Trackmania | Čtečka CSV v prohlížeči je testována. **Plugin nebyl spuštěn ve hře.** Načte se jen v režimu vývojáře Openplanet. |
| iRacing | Čtečka `.ibt` v prohlížeči je testována na syntetickém souboru. |

Další omezení telemetrie:

- Normalizace skluzu Forzy není zdokumentovaná; skluz Kunos se škáluje typickým vrcholem na asfaltu,
  což je přibližení.
- Smysl některých bočních os v rámci auta (Kunos, DiRT) je zdokumentován oběma směry; velikost úhlu
  driftu je spolehlivá, jeho znaménko ne.
- Žádná z rally her neposílá skluz pneumatik; odvozuje se v prohlížeči. RBR neposílá rychlosti kol.
- Povrch rally etapy se zapisuje jen tehdy, když je zadán `--surface`; jinak soubor žádný nejmenuje
  a prohlížeč ho odhadne (název etapy nebo akce, pak styl jízdy, při výchozím nastavení volně).
- Detekce kola bez počítadla kol (AC EVO, AC Rally, BeamNG) používá jako čáru bod, kde začal
  záznam, takže začněte nahrávat na startovní čáře.
- Reset vozidla v BeamNG uzavře otevřené kolo v tom okamžiku: zapíše se jako částečný běh, když
  pokryl minimální vzdálenost (300 m), jinak se zahodí.
- `route` ukládá zhruba každé 2 sekundy za jízdy; pád nebo ukončený proces ztratí nejvýš pozice od
  posledního uložení.
- Forza Horizon neposílá název trati, takže soubory kol Forzy mají `"track": null`; Forza Motorsport
  (2023) posílá jen číslo, uložené jako `lap.trackOrdinal`.

## Rekonstrukce {#reconstruction}

- **Hloubka se odhaduje, nečte.** Strop celého přístupu a cena za to, že se nikdy nedotýkáme
  herního procesu.
- **Zorné pole se předpokládá, neměří.** Příliš úzké a level se zrekonstruuje hlouběji, než je.
- **Globální měřítko** pochází z předpokládané výšky kamery (1,15 m v okně), nebo z telemetrie. Měří
  se na prvním klíčovém snímku; když na něm není použitelná zem, zkouší se další klíčové snímky (až
  30 snímků) a měřítko nalezené později se použije na celý level při zápisu. Řádek „Size:“ v okně
  říká, co se stalo; když se nenajde žádná zem, skenování zůstane bez jednotek. Velikost voxelu je
  v jednotkách prvního snímku v tom případě, takže její velikost v metrech se liší od nastavení.
  Offline rekonstrukce jsou v jednotkách řešení.
- **Uzavření smyčky je vypnuté** a není to graf poz, když se zapne v kódu; drift je omezen jen
  kvalitou sledování mezi snímky.
- **Okenní vyrovnání svazků existuje, ale není zapojené**; na skutečném záznamu zkolabovalo.
- **Povrch je vážená obsazenost, ne TSDF**: tenké struktury a volný prostor jsou horší, než by
  dala TSDF.
- **Žádný atlas textur.** Barva je na vrcholech (`COLOR_0`), mísí se ze 4 nejlepších pohledů z 160
  uchovaných snímků. Test zakrytí je hrubý: testuje proti vlastním vrcholům sítě v hloubkovém bufferu
  o velikosti 2 pixely, takže překážku, kterou síť neobsahuje (projíždějící auto), nezachytí.
- **Voda se nikdy neoznačí**; všechno je země nebo stavba.
- **Řešení z předpovědi není živé**: vyžaduje nejdřív záznam. Adaptivní opětovné řešení obtížných
  úseků není postaveno.
- **Pozice z telemetrie** umísťují kameru na auto (offset kamery za autem není znám). Pozice se berou
  tak, jak je Forza posílá (Y nahoru, jako v souborech kol); smysl yaw, pitch a roll se odečetl ze
  zaznamenaných kol (směr jízdy, sklon, která strana odpružení se stlačuje), ne z běžící kamery hry.
- Překryvný prvek nemůže kreslit přes **exkluzivní celou obrazovku**; použijte bezrámečkové okno na
  celou obrazovku.
- Globální klávesové zkratky, průhledný překryv a živé zachytávání fungují jen na **Windows**.
- Zavření okna se nezeptá na uložení.

## Co je měřeno {#what-is-measured}

- `tests/test_accuracy.py`: syntetická místnost se známou cestou a analytickou hloubkou - umístěné
  snímky, chyba cesty, ujetá vzdálenost, velikost místnosti, povrch na stěnách ([Rekonstrukce úrovně](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: silnice o známé šířce, projetá mimo střed, se zrekonstruuje se svou
  šířkou.
- `tests/test_track_scale.py`: extrakce povrchu v měřítku závodní trati, paměť úměrná tomu, co bylo
  naskenováno, bloky spojené do jednoho povrchu.
- `tests/test_glb.py` spolu s vlastními testy prohlížeče: kontrakt `.glb` z obou stran.
- Jak si síť hloubky vede na skutečné hře, syntetická scéna nezodpoví a sada testů to neměří.
