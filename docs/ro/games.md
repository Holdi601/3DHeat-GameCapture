---
title: "Jocuri"
nav_order: 4
lang: "ro"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Jocuri: înregistrare și trasee {#games-recording-and-courses}

Cum este înregistrat fiecare joc acceptat, ce trimite și care dintre traseele lui pot fi exportate din propriile fișiere ale jocului.

Regulile sunt aceleași pentru toate jocurile: un traseu provine dintr-un fișier pe care utilizatorul îl deține sau este reconstruit din propria joacă a utilizatorului. Arhivele criptate se deschid doar cu o cheie pe care utilizatorul o are deja - aici nu se livrează chei și nu se recuperează nimic, iar nimic nu se injectează în procesul unui joc. Telemetria vine doar din interfețele pe care jocurile le publică pentru ea (ieșiri UDP, memorie partajată, propriile lor interfețe de mod și de plugin). Ce indică utilizatorul instrumentelor rămâne supus licenței acelui joc.

## Telemetrie {#telemetry}

Fiecare joc ajunge în fișiere `heat3d-lap` ([`lap-format.md`](lap-format.md)), cu nume canonice de canale și un bloc `meta` care spune ce înseamnă numerele lui - cum este scalată alunecarea, dacă e circuit, raliu sau arcade, suprafața când este cunoscută - astfel încât un cititor le tratează pe toate la fel. Toate comenzile sunt `python -m heat3d_capture ...` în acest depozit.

| Joc | Cum se înregistrează | Poziție | Anvelope și alunecare | Unghi de derapaj | Stare |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out prin UDP: `heat3d_capture telemetry` (retransmite către FH Companion) - sau fișierul `.tele.gz` al FH Companion, de lângă fiecare tură, încărcat împreună cu fișierul turei | XYZ în lumea jocului | raport de alunecare, unghi de alunecare, alunecare combinată pe fiecare roată, normalizate; rugozitatea suprafeței | viteza în cadrul mașinii | înregistratorul e testat; cititorul `.tele.gz` e verificat pe ture reale |
| Forza Motorsport (inclusiv 2023) | la fel; deosebite după lungimea pachetului | XYZ în lume | la fel | la fel | înregistratorul e testat |
| Assetto Corsa, ACC, AC EVO | memorie partajată: `telemetry --game ac / acc / acevo` | media punctelor de contact ale anvelopelor | raport și unghi de alunecare (fizice, scalate printr-un vârf de asfalt); ABS și TC active (ACC, EVO) | viteza în cadrul mașinii | înregistratorul e testat pe pagini sintetice |
| Assetto Corsa Rally | `telemetry --game acrally` | la fel | la fel; sarcini pe roți; temperaturi convertite din kelvin | viteza în cadrul mașinii | înregistratorul e testat pe pagini sintetice |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documente>/My Games/WRC/telemetry/config.json"` pornește pachetul implicit `wrc` (fișierul este salvat întâi) | XYZ în lume | viteza punctului de contact pe fiecare roată; alunecarea derivată | din axele mașinii și din viteza ei | înregistratorul e testat pe pachete construite după structura documentată |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: se setează `<udp enabled="true" extradata="3" port="20777" delay="1" />` în `hardware_settings_config.xml`, apoi `telemetry --game dirtrally2` (sau `dirtrally`, `dirt4`) | XYZ în lume | viteza punctului de contact pe fiecare roată; alunecarea derivată. Fără canal pentru frâna de mână | din axele mașinii și din viteza ei | la fel |
| Richard Burns Rally (RSF/NGP) | telemetria UDP a NGP (`udpTelemetry=1`): `telemetry --game rbr` | lume, axa „sus" se află din etapă | deformarea arcului și forța pe fiecare roată; fără viteze ale roților | vitezele proprii ale mașinii | la fel; axele și unitățile de viteză nu sunt documentate și se tratează din date |
| BeamNG.drive | modul de protocol `heat3d`: `telemetry --game beamng --install`, apoi Options > Other > Protocols > „others" | lume, rotită la Y în sus | viteza suprafeței roții, rotația, sarcina, contactul cu solul; alunecarea derivată | din axele mașinii și din viteza ei | înregistratorul e testat pe pachete construite după structura modului; modul nu e testat în joc |
| Trackmania (2020) | pluginul Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, încărcat în modul dezvoltator Openplanet; un CSV pentru fiecare rulare, în dosarul lui de stocare | XYZ în lume | coeficientul de alunecare al Trackmania pe fiecare roată; pietriș liber din materialele roților; în aer | viteza frontală și laterală | cititorul e testat; pluginul nu e testat în joc |
| iRacing | fișierele lui `.ibt`; nu e nevoie de înregistrator | latitudine/longitudine/altitudine, proiectate pe un plan tangent | fără alunecare (nu este înregistrată); viteza de rotație și accelerația laterală | din viteza de rotație față de traseu | cititorul e testat pe un fișier sintetic |

Ce nu trimite niciun joc de raliu - alunecarea anvelopelor - este calculat de un cititor: din viteza punctului de contact sau a suprafeței fiecărei roți față de viteza mașinii, acolo unde jocul trimite una (`(roată - mașină) / mașină`), sau din rotația ei și dintr-o rază de rulare măsurată pe tura însăși, acolo unde trimite doar rotația. Unghiul de derapaj vine din viteza proprie a mașinii (Forza, jocurile AC, Trackmania, RBR), din viteza lumii proiectată pe axele mașinii (EA WRC, DiRT, BeamNG) sau din orientarea față de traseu. Dacă mașina este în aer se află din contactul, sarcinile sau suspensia roților.

Unde lumea unui joc este levogiră - ca la Forza - traseul iese oglindit într-un vizualizator dreptgiriu; direcția și suspensia proprie ale turelor o arată. Jocurile a căror orientare nu este documentată (RBR, BeamNG, Trackmania) sunt tratate la fel: măsurat, nu presupus.

Pe lângă canalele de conducere, înregistratoarele păstrează ce adaugă fiecare joc: ABS și controlul de tracțiune active în jocurile AC, repartiția frânei, DRS, limitatorul de la boxe, boost și durata de viață a plăcuțelor și discurilor de frână; setările de asistență iRacing, repartiția frânei, temperaturile combustibilului, uleiului și apei și orice alt canal pe care îl înregistrează sub numele lui.

### Surse și ce nu este confirmat încă {#sources-and-what-is-not-yet-confirmed}

- **Forza:** documentația oficială Data Out (Forza Motorsport; Forza Horizon 6) pentru câmpuri, unitățile lor și cadrul mașinii (x dreapta, y sus, z înainte - levogir). Nu este documentat cu ce normalizează Forza alunecarea: măsurați unde începe să scape aderența fiecărei mașini, în loc să presupuneți că 1 este limita.
- **Kunos:** SDK-ul AC1, documentația memoriei partajate ACC v1.8.12, `albertowd/live-telemetry-evo` (EVO, măsurat; AC Rally folosește structura ACC, „confirmată printr-o sondă octet cu octet"), `LuizZak/AssettoCorsaRallyTelemetryReader`. Sensul în care indică axa x a mașinii este documentat în ambele sensuri: folosiți mărimea unghiului de derapaj, nu semnul lui.
- **EA SPORTS WRC:** Ghidul UDP Telemetry v1.3 al EA și lista de canale pe care jocul o scrie în `readme/channels.json`; decalajele pachetului implicit `wrc` așa cum le decodează nobonobo/obs-codemasters-telemetry. Portul implicit din fabrică nu este documentat; înregistratorul pornește pachetul pe 20777.
- **DiRT:** documentul UDP al Codemasters pentru DiRT 4, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Sensul vectorului lateral și unitatea poziției suspensiei sunt documentate în ambele sensuri; niciuna nu decide o constatare.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` al NGP (prin mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Axele poziției, unitățile atitudinii și unitatea de viteză nu sunt documentate: înregistratorul ia „sus" din etapă și viteza din poziții.
- **BeamNG:** documentation.beamng.com (protocoale; refNodes: vehicul +X stânga, -Y înainte, Z sus) și fișierele jocului `lua/vehicle/protocols.lua` și `wheels.lua`. OutSim este un stub în versiunile actuale; OutGauge nu are poziție, iar MotionSim nu are roți - de aceea modul.
- **Trackmania:** `CSceneVehicleVisState` și pluginul VehicleState al Openplanet, timpul de cursă `CSmScriptPlayer`. Pluginurile Openplanet nu pot trimite UDP, așa că pluginul scrie fișiere. Pluginurile nesemnate se încarcă doar în modul dezvoltator, ceea ce limitează jocul online; pluginul poate fi semnat pe openplanet.dev.

Niciun înregistrator nu a fost încă rulat pe jocurile live de aici; prima sesiune reală a fiecăruia este testul care contează, iar `tests/test_kunos.py`, `test_rally.py` și `test_beamng.py` fixează structurile pentru care au fost construite. Fiecare înregistrator își verifică pachetele pe măsură ce sosesc - viteza față de viteza indicată, dimensiunea structurii - și spune când o structură nu se potrivește.

## Trasee: ce se exportă, pe joc {#courses-what-is-exported-per-game}

Un traseu adaugă bordurile, zidurile și zona de siguranță care explică o traiectorie. Traseele sunt exportate de [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <tura>`), din fișierele jocului, acolo unde asta a fost construit și verificat pe o copie instalată. Detaliile sunt în [documentația GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Joc | Traseu dintr-o tură |
|---|---|
| Forza Horizon | da |
| BeamNG.drive | da |
| Assetto Corsa Rally | da |
| Assetto Corsa EVO | nu: conținutul său nu se poate citi ca fișiere |
| iRacing | nu: modelele de circuit vin într-un format protejat |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | încă nu: fiecare are nevoie de o copie instalată ca să fie construit și verificat |

Până atunci, traseul prin joacă funcționează pentru toate.

## Ruta care funcționează pentru fiecare joc {#the-route-that-works-for-every-game}

GameCapture reconstruiește un nivel dintr-un video al jocului. Partea sa grea este traseul camerei, iar pentru Forza este exact, pentru că telemetria dă poziția mașinii la fiecare cadru. Fiecare joc de mai sus are acum același lucru: poziția și atitudinea, în timp real, dintr-o interfață documentată. Dacă acestea sunt introduse în `pose/telemetry_pose.py` în locul celor ale Forza, se obține singura piesă care face ruta prin joacă exactă pentru toate - restul acestui pipeline (adâncime, fuziune, texturare) nu se interesează de jocul care a desenat cadrele.
