---
title: "Spellen: opnemen en banen"
nav_order: 4
lang: "nl"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Spellen: opnemen en banen {#games-recording-and-courses}

Hoe elk ondersteund spel wordt opgenomen, wat het verstuurt, en welke banen uit de eigen bestanden van het spel kunnen worden geëxporteerd.

De regels zijn voor elk spel hetzelfde: een baan komt uit bestanden die de gebruiker zelf bezit, of wordt gereconstrueerd uit het eigen gameplay van de gebruiker. Versleutelde archieven gaan alleen open met een sleutel die de gebruiker al heeft - hier wordt geen sleutel meegeleverd of teruggehaald, en niets wordt in het proces van een spel geïnjecteerd. Telemetrie komt alleen uit de interfaces die de spellen zelf daarvoor publiceren (UDP-uitvoer, gedeeld geheugen, hun eigen mod- en plugin-interfaces). Wat je de tools op laat richten, valt nog steeds onder de licentie van dat spel.

## Telemetrie {#telemetry}

Elk spel eindigt als `heat3d-lap`-bestanden ([`lap-format.md`](lap-format.md)), met kanaalnamen die overal gelijk zijn en een `meta`-blok dat zegt wat de getallen betekenen - hoe de slip is geschaald, circuit, rally of arcade, het wegdek als dat bekend is - zodat een lezer ze allemaal hetzelfde behandelt. Alle commando's zijn `python -m heat3d_capture ...` in deze repository.

| Spel | Hoe opnemen | Positie | Banden en slip | Drifthoek | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out over UDP: `heat3d_capture telemetry` (stuurt door naar FH Companion) - of de eigen `.tele.gz` van FH Companion naast elke ronde, geladen met het rondenbestand | wereld XYZ | slip-ratio, slip-hoek, gecombineerde slip per wiel, genormaliseerd; rumble van het wegdek | snelheid in het autoframe | opnemer getest; `.tele.gz`-lezer gecontroleerd op echte ronden |
| Forza Motorsport (incl. 2023) | hetzelfde; herkend aan de pakketlengte | wereld XYZ | hetzelfde | hetzelfde | opnemer getest |
| Assetto Corsa, ACC, AC EVO | gedeeld geheugen: `telemetry --game ac / acc / acevo` | gemiddelde van de contactpunten van de banden | slip-ratio en slip-hoek (fysiek, geschaald op een piek voor asfalt); ABS en TC in werking (ACC, EVO) | snelheid in het autoframe | opnemer getest op synthetische pagina's |
| Assetto Corsa Rally | `telemetry --game acrally` | hetzelfde | hetzelfde; wiellasten; temperaturen omgerekend van kelvin | snelheid in het autoframe | opnemer getest op synthetische pagina's |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documenten>/My Games/WRC/telemetry/config.json"` zet het standaardpakket `wrc` aan (eerst wordt er een back-up van het bestand gemaakt) | wereld XYZ | contactvlaksnelheid per wiel; slip afgeleid | uit de assen van de auto en de snelheid van de auto | opnemer getest op pakketten die uit de gedocumenteerde indeling zijn gebouwd |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: zet `<udp enabled="true" extradata="3" port="20777" delay="1" />` in `hardware_settings_config.xml`, dan `telemetry --game dirtrally2` (of `dirtrally`, `dirt4`) | wereld XYZ | contactvlaksnelheid per wiel; slip afgeleid. Geen handremkanaal | uit de assen van de auto en de snelheid van de auto | hetzelfde |
| Richard Burns Rally (RSF/NGP) | UDP-telemetrie van NGP (`udpTelemetry=1`): `telemetry --game rbr` | wereld; verticale as gevonden uit de etappe | veerindrukking en veerkracht per wiel; geen wielsnelheden | de eigen snelheden van de auto | hetzelfde; assen en snelheidseenheden zijn niet gedocumenteerd en worden uit de data afgeleid |
| BeamNG.drive | de `heat3d`-protocolmod: `telemetry --game beamng --install`, dan Options > Other > Protocols > "others" | wereld, omgedraaid naar Y omhoog | oppervlaktesnelheid, rotatie, belasting en grondcontact per wiel; slip afgeleid | uit de assen van de auto en de snelheid van de auto | opnemer getest op pakketten die uit de structuur van de mod zijn gebouwd; de mod is nog niet in het spel getest |
| Trackmania (2020) | de Openplanet-plugin `Heat3dRecorder`: `telemetry --game trackmania --install`, geladen in de ontwikkelaarsmodus van Openplanet; één CSV per run in de opslagmap | wereld XYZ | slipcoëfficiënt van Trackmania per wiel; losse ondergrond uit de materialen van de wielen; in de lucht | zij- en voorsnelheid | lezer getest; de plugin is nog niet in het spel getest |
| iRacing | de eigen `.ibt`-bestanden; geen opnemer nodig | breedtegraad/lengtegraad/hoogte, uitgezet op een raakvlak | geen slip (niet gelogd); gierhoeksnelheid en laterale versnelling | uit de gierhoeksnelheid tegen het pad | lezer getest op een synthetisch bestand |

Wat geen van de rally-spellen verstuurt - bandenslip - rekent een lezer zelf uit: uit de contactvlaksnelheid of oppervlaktesnelheid van elk wiel tegenover de snelheid van de auto waar een spel die stuurt (`(wiel - auto) / auto`), of uit de rotatie en een rolstraal die op de ronde zelf wordt gemeten waar alleen rotatie wordt gestuurd. De drifthoek komt uit de eigen snelheid van de auto (Forza, de AC-spellen, Trackmania, RBR), uit de wereldsnelheid geprojecteerd op de assen van de auto (EA WRC, DiRT, BeamNG), of uit de koers van de auto tegen het pad. Of de auto in de lucht is, volgt uit het grondcontact, de belasting of de vering van de wielen.

Waar de wereld van een spel linkshandig is - die van Forza is dat - komt de baan gespiegeld uit in een rechtshandige viewer; de eigen stuur- en veerdata van de ronden laten dat zien. Spellen waarvan de handigheid niet gedocumenteerd is (RBR, BeamNG, Trackmania) worden op dezelfde manier behandeld: gemeten, niet aangenomen.

Naast de rijkanalen bewaren de opnemers wat elk spel er extra bij levert: de ABS- en tractiecontrole in werking bij de AC-spellen, remverdeling, DRS, pitlimiter, boost en de levensduur van remblokken en remschijven; bij iRacing de hulpinstellingen, remverdeling, brandstof, olie- en watertemperaturen, en elk ander kanaal dat het onder zijn eigen naam logt.

### Bronnen en wat nog niet is bevestigd {#sources-and-what-is-not-yet-confirmed}

- **Forza:** de officiële Data Out-documentatie (Forza Motorsport; Forza Horizon 6) voor de velden, hun eenheden en het autoframe (x naar rechts, y omhoog, z vooruit - linkshandig). Waar Forza de slip op normaliseert, is niet gedocumenteerd: meet waar de grip van elke auto echt wegvalt in plaats van aan te nemen dat 1 de grens is.
- **Kunos:** het AC1-SDK, de documentatie van het gedeelde geheugen van ACC v1.8.12, `albertowd/live-telemetry-evo` (EVO, gemeten; AC Rally gebruikt de indeling van ACC, "bevestigd via byte-voor-byte-onderzoek"), `LuizZak/AssettoCorsaRallyTelemetryReader`. De kant waar de x-as van de auto naartoe wijst, is in beide richtingen gedocumenteerd: gebruik de grootte van de drifthoek, niet het teken.
- **EA SPORTS WRC:** EA's UDP Telemetry Guide v1.3 en de kanalenlijst die het spel naar `readme/channels.json` schrijft; de offsets van het standaardpakket `wrc` zoals gedecodeerd door nobonobo/obs-codemasters-telemetry. De standaardpoort van het spel is niet gedocumenteerd; de opnemer zet het pakket aan op 20777.
- **DiRT:** het UDP-document van Codemasters voor DiRT 4, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Het teken van de zijvector en de eenheid van de veerpositie zijn in beide richtingen gedocumenteerd; geen van beide beslist een bevinding.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` van NGP (via mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). De positieassen, de eenheden van de houding en de snelheidseenheid zijn niet gedocumenteerd: de opnemer neemt omhoog uit de etappe en de snelheid uit de posities.
- **BeamNG:** documentation.beamng.com (protocols; refNodes: voertuig +X links, -Y vooruit, Z omhoog), en de eigen `lua/vehicle/protocols.lua` en `wheels.lua` van het spel. OutSim is een stub in de huidige versies; OutGauge heeft geen positie en MotionSim geen wielen, vandaar de mod.
- **Trackmania:** `CSceneVehicleVisState` van Openplanet en de VehicleState-plugin, de racetijd van `CSmScriptPlayer`. Openplanet-plugins kunnen geen UDP versturen, dus de plugin schrijft bestanden. Niet-ondertekende plugins laden alleen in de ontwikkelaarsmodus, wat online spelen beperkt; de plugin kan op openplanet.dev worden ondertekend.

Geen van de opnemers is tot nu toe tegen de echte spellen hier gedraaid; de eerste echte sessie van elk is de test die telt, en `tests/test_kunos.py`, `test_rally.py` en `test_beamng.py` leggen de indelingen vast waarvoor ze zijn gebouwd. Elke opnemer controleert zijn pakketten zodra ze binnenkomen - de snelheid tegen de snelheid van de auto, de lengte van de struct - en zegt het als een indeling niet klopt.

## Banen: wat per spel wordt geëxporteerd {#courses-what-is-exported-per-game}

Een baan voegt de randstenen, muren en uitloopzones toe die een lijn verklaren. Banen worden geëxporteerd door [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), uit de eigen bestanden van het spel, waar dat is gebouwd en gecontroleerd op een geïnstalleerde kopie. Details staan in de [GameFiles-documentatie](https://holdi601.github.io/3DHeat-GameFiles/).

| Spel | Baan uit een ronde |
|---|---|
| Forza Horizon | ja |
| BeamNG.drive | ja |
| Assetto Corsa Rally | ja |
| Assetto Corsa EVO | nee: de inhoud is niet als bestanden leesbaar |
| iRacing | nee: baanmodellen worden in een beschermd formaat geleverd |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | nog niet: elk heeft een geïnstalleerde kopie nodig om op te bouwen en tegen te controleren |

De route via gameplay hieronder werkt intussen voor al deze spellen.

## De route die voor elk spel werkt {#the-route-that-works-for-every-game}

GameCapture reconstrueert een level uit gameplayvideo. Het moeilijke deel is het cameratraject, en voor Forza is dat exact omdat de telemetrie elk frame de positie van de auto geeft. Elk spel hierboven heeft nu hetzelfde: positie en oriëntatie, live, uit een gedocumenteerde interface. Die in `pose/telemetry_pose.py` invoeren in plaats van die van Forza is het ene onderdeel dat de route via gameplay voor al deze spellen exact maakt - de rest van die pijplijn (diepte, samenvoegen, textuur) maakt niet uit welk spel de beelden tekende.
