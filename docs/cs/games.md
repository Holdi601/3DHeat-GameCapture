---
title: "Hry: nahrávání a tratě"
nav_order: 4
lang: "cs"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Hry: nahrávání a tratě {#games-recording-and-courses}

Jak se každá podporovaná hra nahrává, co posílá a které její tratě lze
exportovat ze souborů samotné hry.

Pravidla jsou pro všechny hry stejná: trať pochází ze souborů, které uživatel
vlastní, nebo se rekonstruuje z jeho vlastní hry. Šifrované archivy se otevřou
jen klíčem, který uživatel už má - tento projekt žádné klíče nedodává ani
neobnovuje a nic nevstřikuje do procesu hry. Telemetrie přichází jen z rozhraní,
která hry samy zveřejňují (UDP výstupy, sdílená paměť, jejich vlastní rozhraní
modů a pluginů). K čemu uživatel nástroje použije, dál podléhá licenci dané hry.

## Telemetrie {#telemetry}

Každá hra skončí jako soubory `heat3d-lap` ([`lap-format.md`](lap-format.md)),
s kanály pojmenovanými jednotně a blokem `meta`, který říká, co jejich čísla
znamenají - jak je škálován skluz, zda jde o okruh, rallye nebo arkádu, a povrch,
je-li znám - takže je čtenář zpracuje stejně. Všechny příkazy jsou
`python -m heat3d_capture ...` v tomto repozitáři.

| Hra | Jak nahrávat | Poloha | Pneumatiky a skluz | Driftový úhel | Stav |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out přes UDP: `heat3d_capture telemetry` (přeposílá do FH Companion) - nebo `.tele.gz` z FH Companion vedle každého kola, načtený se souborem kola | světové XYZ | poměr skluzu, úhel skluzu, kombinovaný skluz na kolo, normalizovaný; vibrace povrchu | rychlost v rámu auta | nahrávač otestován; čtečka `.tele.gz` ověřena na skutečných kolech |
| Forza Motorsport (včetně 2023) | totéž; rozlišuje se podle délky paketu | světové XYZ | totéž | totéž | nahrávač otestován |
| Assetto Corsa, ACC, AC EVO | sdílená paměť: `telemetry --game ac / acc / acevo` | průměr bodů styku pneumatik | poměr a úhel skluzu (fyzikální, škálovaný vrcholem přilnavosti na asfaltu); ABS a TC v činnosti (ACC, EVO) | rychlost v rámu auta | nahrávač otestován na syntetických stránkách |
| Assetto Corsa Rally | `telemetry --game acrally` | totéž | totéž; zatížení kol; teploty převedené z kelvinů | rychlost v rámu auta | nahrávač otestován na syntetických stránkách |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Dokumenty>/My Games/WRC/telemetry/config.json"` zapne výchozí paket `wrc` (soubor se předem zálohuje) | světové XYZ | rychlost styku pneumatiky na kolo; skluz odvozen | z os auta a jeho rychlosti | nahrávač otestován na paketech sestavených z dokumentovaného rozložení |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: nastavte `<udp enabled="true" extradata="3" port="20777" delay="1" />` v `hardware_settings_config.xml`, pak `telemetry --game dirtrally2` (nebo `dirtrally`, `dirt4`) | světové XYZ | rychlost styku pneumatiky na kolo; skluz odvozen. Kanál ruční brzdy není | z os auta a jeho rychlosti | totéž |
| Richard Burns Rally (RSF/NGP) | UDP telemetrie NGP (`udpTelemetry=1`): `telemetry --game rbr` | svět, osa nahoru se zjistí z etapy | průhyb pružiny a síla na kolo; rychlosti kol nejsou | vlastní rychlosti auta | totéž; osy a jednotky rychlosti nejsou zdokumentovány a zpracují se z dat |
| BeamNG.drive | mod protokolu `heat3d`: `telemetry --game beamng --install`, pak Options > Other > Protocols > "others" | svět, otočený na osu Y nahoru | povrchová rychlost kola, otáčení, zatížení, kontakt se zemí; skluz odvozen | z os auta a jeho rychlosti | nahrávač otestován na paketech sestavených z struktury modu; mod ve hře netestován |
| Trackmania (2020) | plugin Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, načtený ve vývojářském režimu Openplanetu; jeden CSV soubor na jeden běh ve složce úložiště | světové XYZ | koeficient skluzu Trackmanie na kolo; volný povrch z materiálů kol; ve vzduchu | přední a boční rychlost | čtečka otestována; plugin ve hře netestován |
| iRacing | jeho vlastní soubory `.ibt`; nahrávač není třeba | zeměpisná šířka/délka/výška, promítnuté do tečné roviny | skluz se nezaznamenává; rychlost zatáčení a boční zrychlení | z rychlosti zatáčení vůči dráze | čtečka otestována na syntetickém souboru |

Žádná z rallye her neposílá skluz pneumatik - ten čtečka dopočítá: z rychlosti
styku každého kola nebo povrchu proti rychlosti auta, pokud hra nějakou posílá
(`(kolo - auto) / auto`), nebo z otáčení a poloměru valení změřeného na samotném
kole, pokud posílá jen otáčení. Driftový úhel vychází z vlastní rychlosti auta
(Forza, hry AC, Trackmania, RBR), ze světové rychlosti promítnuté na osy auta
(EA WRC, DiRT, BeamNG), nebo ze směru jízdy vůči dráze. Zda je auto ve
vzduchu, se pozná z kontaktu kol, zatížení nebo odpružení.

Je-li svět hry levotočivý - Forzin ano -, kurz se v pravotočivém prohlížeči
zrcadlí; vlastní řízení a odpružení kol to prozradí. Hry s nedokumentovanou
orientací (RBR, BeamNG, Trackmania) se zpracují stejně: změří se, nepředpokládají.

Kromě jízdních kanálů si nahrávače ponechají, co každá hra přidává: činnost ABS
a trakční kontroly v hrách AC, rozložení brzdné síly, DRS, omezovač v boxech,
turbo a životnost destiček a kotoučů brzd; u iRacingu nastavení asistencí,
rozložení brzd, palivo, teploty oleje a vody a každý další kanál, který zaznamenává
pod svým názvem.

### Zdroje a to, co ještě není potvrzeno {#sources-and-what-is-not-yet-confirmed}

- **Forza:** oficiální dokumentace Data Out (Forza Motorsport; Forza Horizon 6)
  pro pole, jejich jednotky a rám auta (x vpravo, y nahoru, z dopředu -
  levotočivý). Vůči čemu Forza normalizuje skluz, není zdokumentováno: měřte, kde
  přilnavost u každého auta skutečně mizí, a nepředpokládejte, že 1 je mez.
- **Kunos:** SDK AC1, dokumentace sdílené paměti ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, změřeno; AC Rally používá rozložení ACC,
  „ověřeno bajt po bajtu“), `LuizZak/AssettoCorsaRallyTelemetryReader`. Strana,
  na kterou ukazuje osa x auta, je dokumentována oběma směry: použijte velikost
  driftového úhlu, ne jeho znaménko.
- **EA SPORTS WRC:** UDP Telemetry Guide v1.3 od EA a seznam kanálů, který hra
  zapisuje do `readme/channels.json`; posuny výchozího paketu `wrc`, jak je
  dekódoval nobonobo/obs-codemasters-telemetry. Výchozí port hry není
  zdokumentován; nahrávač zapne paket na 20777.
- **DiRT:** dokument Codemasters k UDP pro DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Smysl vektoru strany a jednotka
  polohy odpružení jsou dokumentovány oběma směry; ani jedno nerozhodne žádný
  nález.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` od NGP (přes
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Osy polohy, jednotky
  postojů a jednotka rychlosti nejsou zdokumentovány: nahrávač vezme nahoru
  z etapy a rychlost z pozic.
- **BeamNG:** documentation.beamng.com (protokoly; refNodes: vozidlo +X vlevo,
  -Y dopředu, Z nahoru) a vlastní soubory hry `lua/vehicle/protocols.lua` a
  `wheels.lua`. OutSim je v aktuálních verzích záslepka; OutGauge nemá polohu
  a MotionSim nemá kola, proto mod.
- **Trackmania:** `CSceneVehicleVisState` a VehicleState z Openplanetu, čas
  závodu `CSmScriptPlayer`. Pluginy Openplanetu nemohou posílat UDP, takže plugin
  zapisuje soubory. Nepodepsané pluginy se načtou jen ve vývojářském režimu, což
  omezuje hru online; plugin lze podepsat na openplanet.dev.

Žádný z nahrávačů zatím neběžel proti živým hrám; první skutečné sezení každého
z nich je ten rozhodující test a `tests/test_kunos.py`, `test_rally.py` a
`test_beamng.py` zafixují rozložení, pro která byly napsány. Každý nahrávač
kontroluje své pakety, jak přicházejí - rychlost proti rychlosti, velikost
struktury - a řekne, když rozložení nesedí.

## Tratě: co se exportuje, pro jednotlivé hry {#courses-what-is-exported-per-game}

Trať přidá obrubníky, zdi a odjezdové plochy, které vysvětlují linii. Tratě
exportuje [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <lap>`) ze souborů samotné hry, tam kde je to
sestaveno a ověřeno na nainstalované kopii. Podrobnosti jsou v
[dokumentaci GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Hra | Trať z kola |
|---|---|
| Forza Horizon | ano |
| BeamNG.drive | ano |
| Assetto Corsa Rally | ano |
| Assetto Corsa EVO | ne: její obsah není čitelný jako soubory |
| iRacing | ne: modely tratí jsou v chráněném formátu |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | zatím ne: každá potřebuje nainstalovanou kopii, aby se sestavila a ověřila |

Pro všechny z nich zatím funguje herní postup níže.

## Postup, který funguje pro každou hru {#the-route-that-works-for-every-game}

GameCapture rekonstruuje level z videa hraní. Jeho těžká část je dráha kamery
a u Forzy je přesná, protože telemetrie dává pozici auta v každém snímku. Každá
hra výše má nyní totéž: polohu a postoj živě z dokumentovaného rozhraní.
Jejich přivedení do `pose/telemetry_pose.py` místo Forzina je jediná věc, která
dělá herní postup přesným pro všechny - zbytek tohoto řetězce (hloubka, sloučení,
texturování) na to, která hra snímky nakreslila, nehledí.
