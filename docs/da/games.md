---
title: "Spil: optagelse og baner"
nav_order: 4
lang: "da"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Spil: optagelse og baner {#games-recording-and-courses}

Sådan optages hvert understøttet spil, hvad det sender, og hvilke af dets baner der kan eksporteres fra spillets egne filer.

Reglerne er de samme for alle spil: en bane kommer ud af filer, brugeren ejer, eller den genskabes ud fra brugerens egen spilning. Krypterede arkiver åbnes kun med en nøgle, brugeren allerede har. Her leveres eller findes ingen nøgler, og intet injiceres i et spils proces. Telemetri kommer kun fra de grænseflader, spillene selv udgiver til det (UDP-output, delt hukommelse, deres egne mod- og plugin-grænseflader). Hvad brugeren peger værktøjerne mod, er stadig underlagt det pågældende spils licens.

## Telemetri {#telemetry}

Hvert spil ender som `heat3d-lap`-filer ([`lap-format.md`](lap-format.md)), med kanalnavne i en fast form og en `meta`-blok, der siger, hvad dets tal betyder: hvordan dets slip er skaleret, om det er bane, rally eller arcade, og underlaget når det er kendt. Så en læser behandler dem alle ens. Alle kommandoer er `python -m heat3d_capture ...` i dette repository.

| Spil | Sådan optages det | Position | Dæk og slip | Driftvinkel | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out over UDP: `heat3d_capture telemetry` (videresender til FH Companion) - eller FH Companions egen `.tele.gz` ved siden af hver omgang, indlæst sammen med omgangsfilen | verden XYZ | slip-forhold, slipvinkel og kombineret slip pr. hjul, normaliseret; overfladerumling | bilens hastighed i bilens ramme | optager testet; `.tele.gz`-læseren kontrolleret på rigtige omgange |
| Forza Motorsport (inkl. 2023) | det samme; skelnes på pakkelængden | verden XYZ | det samme | det samme | optager testet |
| Assetto Corsa, ACC, AC EVO | delt hukommelse: `telemetry --game ac / acc / acevo` | gennemsnit af dækkenes kontaktpunkter | slip-forhold og -vinkel (fysisk, skaleret med en asfalttop); ABS og TC i brug (ACC, EVO) | hastighed i bilens ramme | optager testet på syntetiske sider |
| Assetto Corsa Rally | `telemetry --game acrally` | det samme | det samme; hjulbelastninger; temperaturer omregnet fra kelvin | hastighed i bilens ramme | optager testet på syntetiske sider |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Dokumenter>/My Games/WRC/telemetry/config.json"` slår standardpakken `wrc` til (filen sikkerhedskopieres først) | verden XYZ | kontaktfladens hastighed pr. hjul; slip udledt | ud fra bilens akser og dens hastighed | optager testet på pakker bygget efter det dokumenterede layout |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: sæt `<udp enabled="true" extradata="3" port="20777" delay="1" />` i `hardware_settings_config.xml`, derefter `telemetry --game dirtrally2` (eller `dirtrally`, `dirt4`) | verden XYZ | kontaktfladens hastighed pr. hjul; slip udledt. Ingen håndbremsekanal | ud fra bilens akser og dens hastighed | det samme |
| Richard Burns Rally (RSF/NGP) | NGP's UDP-telemetri (`udpTelemetry=1`): `telemetry --game rbr` | verden; opadakse fundet ud fra etapen | fjederudbøjning og fjederkraft pr. hjul; ingen hjulhastigheder | bilens egne hastigheder | det samme; akser og hastighedsenheder er ikke dokumenteret og håndteres ud fra dataene |
| BeamNG.drive | `heat3d`-protokolmodet: `telemetry --game beamng --install`, derefter Options > Other > Protocols > "others" | verden, drejet til Y op | hjulets overfladehastighed, rotation, belastning og jordkontakt; slip udledt | ud fra bilens akser og dens hastighed | optager testet på pakker bygget efter modets struct; modet er ikke testet i spillet |
| Trackmania (2020) | Openplanet-pluginet `Heat3dRecorder`: `telemetry --game trackmania --install`, indlæst i Openplanets udviklertilstand; én CSV pr. kørsel i dets lagermappe | verden XYZ | Trackmanias slipkoefficient pr. hjul; løst underlag ud fra hjulenes materialer; i luften | front- og sidehastighed | læser testet; pluginet er ikke testet i spillet |
| iRacing | dets egne `.ibt`-filer; ingen optager nødvendig | breddegrad, længdegrad og højde, lagt på et tangentplan | intet slip (ikke logget); giringshastighed og lateralacceleration | ud fra giringshastigheden mod stien | læser testet på en syntetisk fil |

Det, ingen af rallyspillene sender - dæk-slip - udregner en læser: ud fra hvert hjuls kontaktflade eller overfladehastighed mod bilens hastighed, hvor et spil sender en (`(hjul - bil) / bil`), og ud fra dets rotation og en rulleradius målt på selve omgangen, hvor spillet kun sender rotation. Driftvinklen kommer fra bilens egen hastighed (Forza, AC-spillene, Trackmania, RBR), fra verdenshastigheden projiceret på bilens akser (EA WRC, DiRT, BeamNG) eller fra retningen mod stien. Om bilen er i luften, afgøres ud fra hjulenes kontakt, belastninger eller affjedring.

Hvor et spils verden er venstrehåndet - Forzas er det - kommer banen spejlvendt ud i en højrehåndet viewer. Omgangenes egen styring og affjedring afslører det. Spil, hvis håndethed ikke er dokumenteret (RBR, BeamNG, Trackmania), håndteres på samme måde: de måles, de antages ikke.

Ud over køredata gemmer optagerne det, hvert spil tilføjer: AC-spillenes ABS og traktionskontrol i brug, bremsefordeling, DRS, pitbegrænser, boost og levetid for brempude og -skive. iRacings hjælpeindstillinger, bremsefordeling, brændstof, olie- og vandtemperaturer og alle andre kanaler, den logger under sit eget navn.

### Kilder og det, der ikke er bekræftet endnu {#sources-and-what-is-not-yet-confirmed}

- **Forza:** Forzas officielle Data Out-dokumentation (Forza Motorsport; Forza Horizon 6) for felterne, deres enheder og bilens ramme (x til højre, y op, z fremad - venstrehåndet). Hvad Forza normaliserer sit slip med, er ikke dokumenteret. Mål i stedet, hvor hver bils greb reelt bliver mindre, i stedet for at antage, at 1 er grænsen.
- **Kunos:** AC1 SDK'en, ACC's delte hukommelse (dokumentation v1.8.12), `albertowd/live-telemetry-evo` (EVO, målt; AC Rally bruger ACC's layout, "bekræftet via byte-for-byte-probe"), `LuizZak/AssettoCorsaRallyTelemetryReader`. Hvilken side bilens x-akse i bilens ramme peger mod, er dokumenteret begge veje. Brug driftvinklens størrelse, ikke dens fortegn.
- **EA SPORTS WRC:** EA's UDP Telemetry Guide v1.3 og kanallisten, spillet skriver til `readme/channels.json`; forskydninger i standardpakken `wrc`, som afkodet af nobonobo/obs-codemasters-telemetry. Standardporten er ikke dokumenteret; optageren slår pakken til på 20777.
- **DiRT:** Codemasters' UDP-dokument for DiRT 4, ErlerPhilipp/dr2_logger og soong-construction/dirt-rally-time-recorder. Retningen på sidevektoren og enheden for affjedringspositionen er dokumenteret begge veje; ingen af dem afgør et resultat.
- **RBR:** NGP's `rbr.telemetry.data.TelemetryData.h` (via mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Positionsakser, enheder for attityde og hastighedsenhed er ikke dokumenteret: optageren tager opadretningen fra etapen og hastigheden fra positionerne.
- **BeamNG:** documentation.beamng.com (protokoller; refNodes: køretøj +X venstre, -Y fremad, Z op) og spillets egne `lua/vehicle/protocols.lua` og `wheels.lua`. OutSim er en stub i nyere versioner; OutGauge har ingen position og MotionSim ingen hjul, derfor modet.
- **Trackmania:** Openplanets `CSceneVehicleVisState` og VehicleState-plugin, `CSmScriptPlayer`-løbstiden. Openplanet-plugins kan ikke sende UDP, så pluginet skriver filer. Usignerede plugins indlæses kun i udviklertilstand, hvilket begrænser onlinespil; pluginet kan signeres på openplanet.dev.

Ingen af optagerne er endnu kørt mod de live spil her. Den første rigtige session med hver af dem er den test, der tæller, og `tests/test_kunos.py`, `test_rally.py` og `test_beamng.py` fastlægger de layouts, de er bygget til. Hver optager kontrollerer sine pakker, efterhånden som de kommer - hastigheden mod farten, structens størrelse - og siger til, når et layout ikke passer.

## Baner: hvad eksporteres, pr. spil {#courses-what-is-exported-per-game}

En bane tilføjer kantsten, vægge og udløbszoner, der forklarer en linje. Baner eksporteres af [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), ud fra spillets egne filer, hvor det er bygget og kontrolleret på en installeret kopi. Detaljerne står i [GameFiles-dokumentationen](https://holdi601.github.io/3DHeat-GameFiles/).

| Spil | Bane fra en omgang |
|---|---|
| Forza Horizon | ja |
| BeamNG.drive | ja |
| Assetto Corsa Rally | ja |
| Assetto Corsa EVO | nej: dets indhold kan ikke læses som filer |
| iRacing | nej: banemodellerne ligger i et beskyttet format |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ikke endnu: hvert kræver en installeret kopi at bygge og kontrollere mod |

Den spilbaserede rute nedenfor virker for dem alle i mellemtiden.

## Den rute, der virker for alle spil {#the-route-that-works-for-every-game}

GameCapture genskaber en bane ud fra spilvideo. Den svære del er kameraets sti, og for Forza er den nøjagtig, fordi telemetrien giver bilens position hver eneste billede. Alle spil ovenfor har nu det samme: position og attityde, live, fra en dokumenteret grænseflade. Når de føres ind i `pose/telemetry_pose.py` i stedet for Forzas, er det ene stykke, der gør den spilbaserede rute nøjagtig for alle dem. Resten af pipelinen (dybde, fusion, teksturering) er ligeglad med, hvilket spil der tegnede billederne.
