---
title: "Spel: inspelning och banor"
nav_order: 4
lang: "sv"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Spel: inspelning och banor {#games-recording-and-courses}

Så spelas varje spel som stöds in, vad det skickar och vilka av spelens banor som kan exporteras från spelets egna filer.

Reglerna är desamma för varje spel: en bana kommer från filer som användaren äger, eller rekonstrueras från användarens egna spelomgångar. Krypterade arkiv öppnas bara med en nyckel som användaren redan har - här levereras eller återskapas inga nycklar, och ingenting injiceras i ett spels process. Telemetri kommer bara från de gränssnitt som spelen publicerar för det (UDP-utgångar, delat minne, deras egna mod- och plugin-gränssnitt). Vad användaren riktar verktygen mot omfattas fortfarande av spelets licens.

## Telemetri {#telemetry}

Varje spel hamnar till slut som `heat3d-lap`-filer ([`lap-format.md`](lap-format.md)), med kanalnamn i gemensam form och ett `meta`-block som säger vad deras värden betyder - hur slip är skalad, bana, rally eller arkad, underlaget när det är känt - så att en läsare behandlar alla lika. Alla kommandon är `python -m heat3d_capture ...` i det här repot.

| Spel | Så spelar du in | Position | Däck och slip | Driftvinkel | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out över UDP: `heat3d_capture telemetry` (vidarebefordrar till FH Companion) - eller FH Companions egen `.tele.gz` bredvid varje varv, läst tillsammans med varvfilen | världens XYZ | slip ratio, slip angle, kombinerad slip per hjul, normaliserad; ytrumble | hastighet i bilens ram | inspelaren testad; `.tele.gz`-läsaren kontrollerad på riktiga varv |
| Forza Motorsport (inkl. 2023) | samma; särskiljs på paketlängden | världens XYZ | samma | samma | inspelaren testad |
| Assetto Corsa, ACC, AC EVO | delat minne: `telemetry --game ac / acc / acevo` | medelvärdet av däckens kontaktpunkter | slip ratio och vinkel (fysisk, skalad med ett typiskt toppvärde för asfalt); ABS och TC aktiva (ACC, EVO) | hastighet i bilens ram | inspelaren testad på syntetiska sidor |
| Assetto Corsa Rally | `telemetry --game acrally` | samma | samma; hjullaster; temperaturer omräknade från kelvin | hastighet i bilens ram | inspelaren testad på syntetiska sidor |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` slår på standardpaketet `wrc` (filen säkerhetskopieras först) | världens XYZ | kontaktytans hastighet per hjul; slip härleds | från bilens axlar och dess hastighet | inspelaren testad på paket byggda från den dokumenterade layouten |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: sätt `<udp enabled="true" extradata="3" port="20777" delay="1" />` i `hardware_settings_config.xml`, kör sedan `telemetry --game dirtrally2` (eller `dirtrally`, `dirt4`) | världens XYZ | kontaktytans hastighet per hjul; slip härleds. Ingen handbromskanal | från bilens axlar och dess hastighet | samma |
| Richard Burns Rally (RSF/NGP) | NGP:s UDP-telemetri (`udpTelemetry=1`): `telemetry --game rbr` | världen, upp-axeln hittas från etappen | fjäderutslag och kraft per hjul; inga hjulhastigheter | bilens egna hastigheter | samma; axlar och hastighetsenheter är odokumenterade och hanteras utifrån datan |
| BeamNG.drive | `heat3d`-protokollmodden: `telemetry --game beamng --install`, sedan Options > Other > Protocols > "others" | världen, vriden till Y uppåt | hjulets ytfart, rotation, last, markkontakt; slip härleds | från bilens axlar och dess hastighet | inspelaren testad på paket byggda från modens struct; modden är otestad i spelet |
| Trackmania (2020) | Openplanet-pluginet `Heat3dRecorder`: `telemetry --game trackmania --install`, laddat i Openplanets utvecklarläge; en CSV per körning i dess lagringsmapp | världens XYZ | Trackmanias slip-koefficient per hjul; lös mark från hjulens material; i luften | framåt- och sidhastighet | läsaren testad; pluginet otestat i spelet |
| iRacing | dess egna `.ibt`-filer; ingen inspelare behövs | latitud/longitud/höjd, lagd på ett tangentplan | ingen slip (loggas inte); gir-hastighet och sidoacceleration | från gir-hastigheten mot banan | läsaren testad på en syntetisk fil |

Vad ingen av rallyspelen skickar - däckslip - räknar en läsare ut: från varje hjuls kontaktyta eller ytfart mot bilens hastighet där ett spel skickar en sådan (`(hjul - bil) / bil`), och från dess rotation och en rullradie uppmätt på själva varvet där det bara skickar rotation. Driftvinkeln kommer från bilens egen hastighet (Forza, AC-spelen, Trackmania, RBR), från världshastigheten projicerad på bilens axlar (EA WRC, DiRT, BeamNG), eller från riktningen mot banan. Om bilen är i luften avgörs av hjulens kontakt, laster eller fjädring.

Där ett spels värld är vänsterhänt - Forzas är det - kommer banan ut spegelvänd i en högerhänt visare; varvens egen styrning och fjädring avslöjar det. Spel vars orientering (vänster- eller högerhänt) är odokumenterad (RBR, BeamNG, Trackmania) hanteras på samma sätt: uppmätt, inte antaget.

Utöver körkanalerna sparar inspelarna det varje spel lägger till: AC-spelens ABS och spårkontroll i funktion, bromsbalans, DRS, depåbegränsare, boost samt bromsbelägg- och skivlivslängd; iRacings hjälpinställningar, bromsbalans, bränsle-, olje- och vattentemperaturer, och varje annan kanal den loggar under sitt eget namn.

### Källor och det som ännu inte är bekräftat {#sources-and-what-is-not-yet-confirmed}

- **Forza:** Forzas officiella Data Out-dokumentation (Forza Motorsport; Forza Horizon 6) för fälten, deras enheter och bilramen (x höger, y upp, z framåt - vänsterhänt). Vad Forza normaliserar slip mot är inte dokumenterat: mät var varje bils grepp faktiskt upphör i stället för att anta att 1 är gränsen.
- **Kunos:** AC1-SDK:n, dokumentationen för ACC:s delade minne v1.8.12, `albertowd/live-telemetry-evo` (EVO, uppmätt; AC Rally använder ACC:s layout, "bekräftad via byte-för-byte-prov"), `LuizZak/AssettoCorsaRallyTelemetryReader`. Vilken sida en bils x-axel pekar mot är dokumenterat åt båda håll: använd driftvinkelns storlek, inte dess tecken.
- **EA SPORTS WRC:** EA:s UDP Telemetry Guide v1.3 och kanallistan spelet skriver till `readme/channels.json`; offset för standardpaketet `wrc` så som nobonobo/obs-codemasters-telemetry avkodar det. Standardporten är inte dokumenterad; inspelaren slår på paketet på port 20777.
- **DiRT:** Codemasters DiRT 4 UDP-dokument, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Sidvektorns riktning och fjädringspositionens enhet är dokumenterade åt båda håll; ingen av dem avgör något fynd.
- **RBR:** NGP:s `rbr.telemetry.data.TelemetryData.h` (via mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Positionsaxlar, attitydenheter och hastighetsenheten är inte dokumenterade: inspelaren tar upp från etappen och hastigheten från positionerna.
- **BeamNG:** documentation.beamng.com (protocols; refNodes: fordon +X vänster, -Y framåt, Z upp), och spelets egna `lua/vehicle/protocols.lua` och `wheels.lua`. OutSim är en stub i aktuella versioner; OutGauge har ingen position och MotionSim inga hjul, därav modden.
- **Trackmania:** Openplanets `CSceneVehicleVisState` och VehicleState-plugin, `CSmScriptPlayer`-racetiden. Openplanet-plugin kan inte skicka UDP, så pluginet skriver filer. Osignerade plugin laddas bara i utvecklarläge, vilket begränsar onlinespel; pluginet kan signeras på openplanet.dev.

Inget av inspelarna har ännu körts mot de riktiga spelen här; den första riktiga sessionen för varje är testet som spelar roll, och `tests/test_kunos.py`, `test_rally.py` och `test_beamng.py` låser de layouter de byggdes mot. Varje inspelare kontrollerar sina paket när de kommer - hastigheten mot farten, structens storlek - och säger till när en layout inte stämmer.

## Banor: vad som exporteras, per spel {#courses-what-is-exported-per-game}

En bana lägger till kantstenar, väggar och områden utanför banan som förklarar en linje. Banor exporteras av [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), från spelets egna filer, där det har byggts och kontrollerats på en installerad kopia. Detaljer finns i [GameFiles-dokumentationen](https://holdi601.github.io/3DHeat-GameFiles/).

| Spel | Bana från ett varv |
|---|---|
| Forza Horizon | ja |
| BeamNG.drive | ja |
| Assetto Corsa Rally | ja |
| Assetto Corsa EVO | nej: innehållet går inte att läsa som filer |
| iRacing | nej: banmodellerna levereras i ett skyddat format |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | inte än: var och en behöver en installerad kopia för att byggas och kontrolleras mot |

Spelrutten nedan fungerar för alla under tiden.

## Rutten som fungerar för varje spel {#the-route-that-works-for-every-game}

GameCapture rekonstruerar en nivå från spelvideo. Dess svåra del är kamerabanan, och för Forza är den exakt eftersom telemetrin ger bilens pose i varje bildruta. Varje spel ovan har nu samma sak: position och attityd, live, från ett dokumenterat gränssnitt. Om man matar in dem i `pose/telemetry_pose.py` i stället för Forzas är det den enda biten som gör spelrutten exakt för alla - resten av pipelinen (djup, fusion, texturering) bryr sig inte om vilket spel som ritade bildrutorna.
