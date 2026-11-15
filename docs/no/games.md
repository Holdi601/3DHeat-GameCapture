---
title: "Spill: opptak og baner"
nav_order: 4
lang: "no"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Spill: opptak og baner {#games-recording-and-courses}

Hvordan hvert støttet spill tas opp, hva det sender, og hvilke av banene
deres som kan eksporteres fra spillets egne filer.

Reglene er de samme for alle spill: en bane kommer enten fra filer brukeren
eier, eller den rekonstrueres fra brukerens egen spilling. Arkiver som er
kryptert åpnes bare med en nøkkel brukeren allerede har - her leveres eller
hentes ingen nøkler, og ingenting injiseres i et spills prosess. Telemetri
kommer bare fra grensesnittene spillene selv publiserer for det (UDP-utdata,
delt minne, egne mod- og plugin-grensesnitt). Hva brukeren peker verktøyene
mot, er fortsatt underlagt spillets lisens.

## Telemetri {#telemetry}

Alle spill ender opp som `heat3d-lap`-filer ([`lap-format.md`](lap-format.md)),
med kanalnavn etter felles standard og en `meta`-blokk som forteller hva
tallene betyr - hvordan sklien er skalert, om det er bane, rally eller arkade,
og underlaget når det er kjent - slik at en leser behandler dem likt. Alle
kommandoer er `python -m heat3d_capture ...` i dette depotet.

| Spill | Slik tas det opp | Posisjon | Dekk og sklí | Driftvinkel | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out over UDP: `heat3d_capture telemetry` (videresender til FH Companion) - eller FH Companions egen `.tele.gz` ved siden av hver runde, lastet sammen med rundefilen | verdens-XYZ | sklíforhold, sklívinkel, kombinert sklí per hjul, normalisert; underlagsrumling | bilens rammeverdi for fart | opptaker testet; `.tele.gz`-leser kontrollert på ekte runder |
| Forza Motorsport (inkl. 2023) | det samme; skilles ved pakkelengde | verdens-XYZ | det samme | det samme | opptaker testet |
| Assetto Corsa, ACC, AC EVO | delt minne: `telemetry --game ac / acc / acevo` | gjennomsnitt av dekkenes kontaktpunkter | sklíforhold og sklívinkel (fysiske, skalert med en asfalttopp); ABS og TC i bruk (ACC, EVO) | bilens rammeverdi for fart | opptaker testet på syntetiske sider |
| Assetto Corsa Rally | `telemetry --game acrally` | det samme | det samme; hjullaster; temperaturer omregnet fra kelvin | bilens rammeverdi for fart | opptaker testet på syntetiske sider |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Dokumenter>/My Games/WRC/telemetry/config.json"` slår på standardpakken `wrc` (filen sikkerhetskopieres først) | verdens-XYZ | kontaktflatens fart per hjul; sklí utledet | fra bilens akser og fart | opptaker testet på pakker bygget etter dokumentert oppsett |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: sett `<udp enabled="true" extradata="3" port="20777" delay="1" />` i `hardware_settings_config.xml`, og kjør deretter `telemetry --game dirtrally2` (eller `dirtrally`, `dirt4`) | verdens-XYZ | kontaktflatens fart per hjul; sklí utledet. Ingen kanal for håndbrems | fra bilens akser og fart | det samme |
| Richard Burns Rally (RSF/NGP) | NGPs UDP-telemetri (`udpTelemetry=1`): `telemetry --game rbr` | verden, opp-akse funnet fra etappen | fjæringsutslag og kraft per hjul; ingen hjulfart | bilens egne hastigheter | det samme; akser og fartsenheter er ikke dokumentert og håndteres ut fra dataene |
| BeamNG.drive | `heat3d`-protokollmodden: `telemetry --game beamng --install`, deretter Alternativer > Annet > Protokoller > "others" | verden, vridd til Y opp | hjulets overflatefart, rotasjon, last, bakkekontakt; sklí utledet | fra bilens akser og fart | opptaker testet på pakker bygget etter modens struktur; modden er ikke testet i spillet |
| Trackmania (2020) | Openplanet-pluginen `Heat3dRecorder`: `telemetry --game trackmania --install`, lastet i Openplanets utviklermodus; én CSV-fil per kjøring i lagringsmappen | verdens-XYZ | Trackmanias sklikoeffisient per hjul; løst underlag fra hjulenes materialer; i luften | fremover- og sidefart | leser testet; pluginen er ikke testet i spillet |
| iRacing | egne `.ibt`-filer; ingen opptaker nødvendig | breddegrad/lengdegrad/høyde, lagt på et tangentplan | ingen sklí (ikke logget); gir-rate og sideakselerasjon | fra gir-raten mot banen | leser testet på en syntetisk fil |

Det ingen av rallyspillene sender - sklí i dekkene - regner en leser ut: fra
hvert hjuls kontaktflate eller overflatefart mot bilens fart der et spill
sender en, (`(hjul - bil) / bil`), eller fra rotasjonen og en rulleradius målt
på selve runden der det bare sendes rotasjon. Driftvinkelen kommer fra bilens
egen hastighet (Forza, AC-spillene, Trackmania, RBR), fra verdenshastigheten
projisert på bilens akser (EA WRC, DiRT, BeamNG), eller fra retningen mot
banen. Om bilen er i luften kommer fra hjulenes kontakt, last eller fjæring.

Der et spills verden er venstrehåndet - Forzas er det - blir banen speilvendt
i en høyrehåndet visning; rundenes egen styring og fjæring viser det. Spill der
håndsystemet ikke er dokumentert (RBR, BeamNG, Trackmania) behandles likt:
målt, ikke antatt.

Utover kjørekanalene tar opptakerne vare på det hvert spill legger til: AC-spillenes
ABS- og sporstabilitetsbruk, bremsefordeling, DRS, pitbegrensning, turbo og
levetid for bremseklosser og -skiver; iRacings hjelpeinnstillinger, bremsefordeling,
drivstoff, olje- og vanntemperaturer, og alle andre kanaler den logger under sitt eget navn.

### Kilder og det som ikke er bekreftet ennå {#sources-and-what-is-not-yet-confirmed}

- **Forza:** den offisielle Data Out-dokumentasjonen (Forza Motorsport; Forza
  Horizon 6) for feltene, enhetene og bilens rammeverk (x høyre, y opp,
  z fremover - venstrehåndet). Det Forza normaliserer sklíen mot, er ikke
  dokumentert: mål heller hvor hver bils grep faktisk avtar enn å anta at 1 er grensen.
- **Kunos:** AC1 SDK-en, dokumentasjonen for ACCs delte minne v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, målt; AC Rally bruker ACCs oppsett,
  "bekreftet med byte-for-byte-probe"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Hvilken side bilens x-akse peker mot, er dokumentert begge veier: bruk driftvinkelens
  størrelse, ikke fortegnet.
- **EA SPORTS WRC:** EAs UDP Telemetry Guide v1.3 og kanallisten spillet skriver til
  `readme/channels.json`; forskyvninger i standardpakken `wrc` slik nobonobo/obs-codemasters-telemetry
  har tolket dem. Standardporten i spillet er ikke dokumentert; opptakeren slår pakken på på 20777.
- **DiRT:** Codemasters' DiRT 4 UDP-dokument, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Retningen på sidevektoren og enheten for
  fjæringsposisjonen er dokumentert begge veier; ingen av dem avgjør et funn.
- **RBR:** NGPs `rbr.telemetry.data.TelemetryData.h` (via
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Posisjonsaksene, enhetene for
  holdning og fartsenheten er ikke dokumentert: opptakeren finner opp fra etappen og fart fra posisjonene.
- **BeamNG:** documentation.beamng.com (protokoller; refNodes: kjøretøy +X venstre,
  -Y fremover, Z opp), og spillets egne `lua/vehicle/protocols.lua` og
  `wheels.lua`. OutSim er en stub i nyere versjoner; OutGauge har ingen posisjon
  og MotionSim ingen hjul, derav modden.
- **Trackmania:** Openplanets `CSceneVehicleVisState` og VehicleState-plugin,
  `CSmScriptPlayer`-løptiden. Openplanet-plugins kan ikke sende UDP, så pluginen skriver filer.
  Usignerte plugins lastes bare i utviklermodus, som begrenser nettspill; pluginen kan
  signeres på openplanet.dev.

Ingen av opptakerne er kjørt mot de levende spillene her ennå; den første ekte
økten med hvert er testen som teller, og `tests/test_kunos.py`, `test_rally.py`
og `test_beamng.py` låser oppsettene de ble bygget mot. Hver opptaker kontrollerer
pakkene sine etter hvert som de kommer - fart mot hastigheten, størrelsen på structen - og
sier fra når et oppsett ikke stemmer.

## Baner: hva som eksporteres, per spill {#courses-what-is-exported-per-game}

En bane legger til kantsteiner, vegger og utløpssoner som forklarer en linje. Baner eksporteres av
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), fra spillets egne filer,
der det er bygget og kontrollert på en installert kopi. Detaljene finnes i
[GameFiles-dokumentasjonen](https://holdi601.github.io/3DHeat-GameFiles/).

| Spill | Bane fra en runde |
|---|---|
| Forza Horizon | ja |
| BeamNG.drive | ja |
| Assetto Corsa Rally | ja |
| Assetto Corsa EVO | nei: innholdet kan ikke leses som filer |
| iRacing | nei: banemodeller leveres i et beskyttet format |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ikke ennå: hver trenger en installert kopi for å bygges og kontrolleres mot |

Spillrouten nedenfor fungerer for alle av dem i mellomtiden.

## Ruten som fungerer for alle spill {#the-route-that-works-for-every-game}

GameCapture rekonstruerer et nivå fra spillvideo. Den vanskelige delen er
kamerabanen, og for Forza er den eksakt fordi telemetrien gir bilens posisjon
hver ramme. Alle spillene over har nå det samme: posisjon og holdning, live,
fra et dokumentert grensesnitt. Å mate disse inn i `pose/telemetry_pose.py` i stedet
for Forzas er det ene som gjør spillruten eksakt for alle - resten av pipeline
(dybde, sammensmelting, tekstur) bryr seg ikke om hvilket spill som tegnet bildene.
