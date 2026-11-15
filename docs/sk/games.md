---
title: "Hry: nahrávanie a trate"
nav_order: 4
lang: "sk"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Hry: nahrávanie a trate {#games-recording-and-courses}

Ako sa nahráva každá podporovaná hra, čo posiela a ktoré jej trate
sa dajú exportovať zo súborov samotnej hry.

Pravidlá sú pre všetky hry rovnaké: trať vzniká zo súborov, ktoré vlastní
používateľ, alebo sa rekonštruuje z jeho vlastnej hry. Šifrované archívy sa
otvárajú len kľúčom, ktorý používateľ už má – nič tu nedodáva ani neobnovuje
kľúče a nič sa nevkladá do procesu hry. Telemetria pochádza len z rozhraní,
ktoré hry na ňu zverejňujú (UDP výstupy, zdieľaná pamäť, ich vlastné
rozhrania modov a pluginov). Na to, na čo používateľ nasmeruje nástroje,
stále platí licencia danej hry.

## Telemetria {#telemetry}

Každá hra skončí ako súbory `heat3d-lap` ([`lap-format.md`](lap-format.md)),
s kanálmi s kanonickými názvami a blokom `meta`, ktorý hovorí, čo ich čísla
znamenajú – ako sa škáluje ich prešmyk, či ide o okruh, rally alebo arkádu,
a povrch, ak je známy – aby ich čítač spracoval všetky rovnako. Všetky
príkazy sú `python -m heat3d_capture ...` v tomto repozitári.

| Hra | Ako nahrávať | Poloha | Pneumatiky a prešmyk | Driftový uhol | Stav |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out cez UDP: `heat3d_capture telemetry` (preposiela do FH Companion) – alebo `.tele.gz` od FH Companion vedľa každého kola, načítaný spolu so súborom kola | svet XYZ | pomer prešmyku, uhol prešmyku, kombinovaný prešmyk na koleso, normalizovaný; vibrácie povrchu | rýchlosť vo vnútornom súradnicovom systéme auta | nahrávač otestovaný; čítač `.tele.gz` overený na reálnych kolách |
| Forza Motorsport (vrátane 2023) | to isté; rozlíšené podľa dĺžky paketu | svet XYZ | to isté | to isté | nahrávač otestovaný |
| Assetto Corsa, ACC, AC EVO | zdieľaná pamäť: `telemetry --game ac / acc / acevo` | priemer kontaktných bodov pneumatík | pomer a uhol prešmyku (fyzikálne, škálované vrcholom na asfalte); ABS a TC v činnosti (ACC, EVO) | rýchlosť vo vnútornom súradnicovom systéme auta | nahrávač otestovaný na syntetických stránkach |
| Assetto Corsa Rally | `telemetry --game acrally` | to isté | to isté; zaťaženia kolies; teploty prepočítané z kelvinov | rýchlosť vo vnútornom súradnicovom systéme auta | nahrávač otestovaný na syntetických stránkach |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` zapne predvolený paket `wrc` (súbor sa najprv zálohuje) | svet XYZ | rýchlosť kontaktnej plochy na koleso; prešmyk odvodený | z osí auta a jeho rýchlosti | nahrávač otestovaný na paketoch zostavených podľa zdokumentovanej štruktúry |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: nastavte `<udp enabled="true" extradata="3" port="20777" delay="1" />` v `hardware_settings_config.xml`, potom `telemetry --game dirtrally2` (alebo `dirtrally`, `dirt4`) | svet XYZ | rýchlosť kontaktnej plochy na koleso; prešmyk odvodený. Kanál ručnej brzdy chýba | z osí auta a jeho rýchlosti | to isté |
| Richard Burns Rally (RSF/NGP) | UDP telemetria NGP (`udpTelemetry=1`): `telemetry --game rbr` | svet, os hore nájdená z etapy | vychýlenie pružiny a sila na koleso; rýchlosti kolies chýbajú | vlastné rýchlosti auta | to isté; osi a jednotky rýchlosti nie sú zdokumentované a spracúvajú sa z dát |
| BeamNG.drive | mod protokolu `heat3d`: `telemetry --game beamng --install`, potom Options > Other > Protocols > "others" | svet, otočený na os Y hore | rýchlosť povrchu kolesa, otáčanie, zaťaženie, kontakt so zemou; prešmyk odvodený | z osí auta a jeho rýchlosti | nahrávač otestovaný na paketoch zostavených zo štruktúry modu; mod v hre netestovaný |
| Trackmania (2020) | plugin Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, načítaný v režime vývojára Openplanet; jeden CSV súbor na jednu jazdu v jeho priečinku | svet XYZ | koeficient prešmyku Trackmanie na koleso; sypký podklad z materiálov kolies; vo vzduchu | rýchlosť bočná a predná | čítač otestovaný; plugin v hre netestovaný |
| iRacing | jeho vlastné súbory `.ibt`; nahrávač nie je potrebný | zemepisná šírka/dĺžka/nadmorská výška, premietnuté na dotykovú rovinu | prešmyk sa neloguje; rýchlosť zatáčania a bočné zrýchlenie | z rýchlosti zatáčania oproti dráhe | čítač otestovaný na syntetickom súbore |

Čo žiadna rally hra neposiela – prešmyk pneumatík – čítač vypočíta: z rýchlosti
kontaktnej plochy každého kolesa oproti rýchlosti auta, kde hra nejakú posiela
(`(koleso - auto) / auto`), alebo z jeho otáčania a valivého polomeru
zmeraného na samotnom kole, kde posiela len otáčanie. Driftový uhol vychádza
z vlastnej rýchlosti auta (Forza, hry AC, Trackmania, RBR), z rýchlosti sveta
premietnutej na osi auta (EA WRC, DiRT, BeamNG) alebo zo smeru jazdy oproti
trati. To, či je auto vo vzduchu, vyplýva z kontaktu kolies, ich zaťaženia
alebo zavesenia.

Ak má svet hry ľavoruký systém – ako Forza – trať sa v pravoručnom prehliadači
zrkadlí; to prezradia vlastné riadenie a zavesenie kôl. Hry, ktorých
orientácia nie je zdokumentovaná (RBR, BeamNG, Trackmania), sa spracúvajú
rovnako: meria sa, nepredpokladá.

Okrem jazdných kanálov nahrávače ukladajú to, čo každá hra pridáva: činnosť
ABS a trakčnej kontroly v hrách AC, rozdelenie brzdenia, DRS, obmedzovač
pitu, turbo a životnosť brzdových platničiek a kotúčov; v iRacingu nastavenia
asistencií, rozdelenie brzdenia, palivo, teploty oleja a vody a každý ďalší
kanál, ktorý loguje pod vlastným menom.

### Zdroje a čo ešte nie je potvrdené {#sources-and-what-is-not-yet-confirmed}

- **Forza:** oficiálna dokumentácia Data Out (Forza Motorsport; Forza
  Horizon 6) pre polia, ich jednotky a osi auta (x doprava, y hore, z
  dopredu – ľavoruký systém). Voči čomu Forza normalizuje svoj prešmyk, nie je
  zdokumentované: namerajte, kde sa prilipnutie každého auta skutočne stráca,
  a nepredpokladajte, že 1 je hranica.
- **Kunos:** SDK AC1, dokumentácia zdieľanej pamäte ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, nameraná; AC Rally používa rozloženie
  ACC, „potvrdené bajt po bajte“), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Strana, na ktorú smeruje os x auta, je zdokumentovaná v oboch smeroch: použite
  veľkosť driftového uhla, nie jeho znamienko.
- **EA SPORTS WRC:** UDP Telemetry Guide v1.3 od EA a zoznam kanálov, ktorý hra
  zapisuje do `readme/channels.json`; posuny predvoleného paketu `wrc` tak, ako
  ich dekódoval nobonobo/obs-codemasters-telemetry. Predvolený port hry nie je
  zdokumentovaný; nahrávač zapne paket na porte 20777.
- **DiRT:** dokument Codemasters UDP k DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Zmysel vektora strany a jednotka
  polohy zavesenia sú zdokumentované v oboch smeroch; ani jedno nerozhodne
  žiadny nález.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` od NGP (cez
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Osi polohy, jednotky
  uhlov a jednotka rýchlosti nie sú zdokumentované: nahrávač zoberie os hore
  z etapy a rýchlosť z polôh.
- **BeamNG:** documentation.beamng.com (protokoly; refNodes: vehicle +X vľavo,
  -Y dopredu, Z hore) a súbory hry `lua/vehicle/protocols.lua` a
  `wheels.lua`. OutSim je v aktuálnych verziách len zástupca; OutGauge nemá
  polohu a MotionSim nemá kolesá, preto mod.
- **Trackmania:** `CSceneVehicleVisState` od Openplanet a plugin VehicleState,
  čas jazdy `CSmScriptPlayer`. Pluginy Openplanet nedokážu posielať UDP, preto
  plugin zapisuje súbory. Nepodpísané pluginy sa načítajú len v režime
  vývojára, čo obmedzuje hru online; plugin možno podpísať na openplanet.dev.

Ani jeden nahrávač sa zatiaľ nespustil proti živým hrám; prvá skutočná jazda
každého z nich je test, ktorý má význam, a `tests/test_kunos.py`,
`test_rally.py` a `test_beamng.py` zafixujú rozloženia, pre ktoré boli
napísané. Každý nahrávač kontroluje svoje pakety, len čo prídu – rýchlosť
oproti rýchlosti auta, veľkosť štruktúry – a povie, keď sa rozloženie
nezhoduje.

## Trate: čo sa exportuje, pre každú hru {#courses-what-is-exported-per-game}

Trať pridáva obrubníky, steny a výbehové zóny, ktoré vysvetľujú jazdnú líniu.
Trate exportuje [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <kolo>`) zo súborov samotnej hry, tam kde
je to vytvorené a overené na nainštalovanej kópii. Podrobnosti sú v
[dokumentácii GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Hra | Trať z kola |
|---|---|
| Forza Horizon | áno |
| BeamNG.drive | áno |
| Assetto Corsa Rally | áno |
| Assetto Corsa EVO | nie: jej obsah nie je čitateľný ako súbory |
| iRacing | nie: modely tratí sú v chránenom formáte |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | zatiaľ nie: každá potrebuje nainštalovanú kópiu, na ktorej sa to vytvorí a overí |

Trasa z hrania nižšie zatiaľ funguje pre všetky z nich.

## Trasa, ktorá funguje pre každú hru {#the-route-that-works-for-every-game}

GameCapture rekonštruuje level z videa hrania. Jeho ťažká časť je dráha
kamery, a pri Forze je presná, lebo telemetria dáva pozíciu auta v každom
snímku. Teraz to má každá hra vyššie: polohu a orientáciu naživo z
zdokumentovaného rozhrania. Ich vloženie do `pose/telemetry_pose.py` namiesto
Forzy je jediná časť, vďaka ktorej je trasa z hrania presná pre všetky –
zvyšok tejto linky (hĺbka, fúzia, textúrovanie) nezáleží na tom, ktorá hra
kreslila snímky.
