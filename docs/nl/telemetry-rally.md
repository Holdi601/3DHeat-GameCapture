---
title: "Rallyspellen"
nav_order: 3
lang: "nl"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20-dirt-rally-dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # of dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Code: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py), [`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py). Tests: `tests/test_rally.py`, op pakketten die uit de gedocumenteerde indelingen zijn gebouwd. **Nog niet tegen de echte spellen gedraaid.**

Alle vier sturen UDP dat het spel aanzet via zijn eigen instellingenbestanden. De opnemer luistert op alle interfaces (`0.0.0.0`) op de standaardpoort van het spel, tenzij `--port` een andere geeft: **20777** voor `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** voor `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Het aanzetten {#switching-it-on}

Het spel leest `Documents\My Games\WRC\telemetry\config.json`. Het `session_update`-pakket van de standaardstructuur `wrc` moet naar deze pc aan staan:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<pad naar config.json>"
```

`--configure` (functie `configure_wrc`):

- leest de JSON, zoekt `udp.packets` en de regel met `"structure": "wrc"` en `"packet": "session_update"`;
- als die al naar `127.0.0.1` of `localhost` op de gebruikte poort staat aan, meldt hij `already on` en verandert niets;
- anders zet hij `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, en behoudt hij de `frequencyHz` van de regel (of `-1` als er geen is); als er geen zo'n regel is, voegt hij er een toe;
- schrijft de oorspronkelijke tekst naar `config.json.bak` ernaast, en schrijft daarna het nieuwe bestand (ingesprongen met 4 spaties).

Start het spel opnieuw na het wijzigen van het bestand als het de wijziging niet oppakt (niet gecontroleerd).

### Wat het verstuurt {#what-it-sends}

De standaardstructuur `wrc` is 237 bytes, little-endian, zonder kop: wereldpositie, snelheid en versnelling (X naar links, Y omhoog, Z vooruit), de eenheidsvectoren links / vooruit / omhoog van de auto, per wiel (achterlinks, achterrechts, voorlinks, voorrechts) de hoogte van de naaf en de verticale snelheid en de voorwaartse snelheid van het contactvlak, de remtemperaturen, de pedalen na de hulpsystemen, de sturing (-1 links, +1 rechts), de handrem, het toerental, de versnelling, en de etappeklok, afstand en lengte. Een pakket korter dan 237 bytes wordt genegeerd en één keer gemeld.

| Kanaal | Van |
|---|---|
| `x`, `y`, `z` | wereldpositie |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | wereldsnelheid geprojecteerd op vooruit, op min links (dus positief is rechts), op omhoog |
| `longAcc`, `latAcc`, `vertAcc` | wereldversnelling op dezelfde manier geprojecteerd |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | zoals verstuurd |
| `gear` | `gear_index`; -1 als het gelijk is aan de achteruitindex, 0 als het gelijk is aan de neutraalindex |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | positie van de naaf |
| `wheelSurfaceSpeed.*` | voorwaartse snelheid van het contactvlak |
| `brakeTemp.*` | remtemperatuur |

Controle: als `speed` boven 10 is en de lengte van de wereldsnelheid ervan meer dan 20% verschilt, meldt de opnemer één keer dat de indeling misschien niet de standaard `wrc`-structuur is.

Een etappe is **klaar** wanneer de lengte van de etappe positief is en de afstand de lengte min 0,5 m heeft bereikt. De klok die voor het splitsen en voor `time` wordt gebruikt, is `stage_time`.

Bronnen: de UDP Telemetry Guide v1.3 van EA; de kanalenlijst die het spel naar `readme/channels.json` schrijft; de offsets zoals gedecodeerd door nobonobo/obs-codemasters-telemetry en SpaceMonkey. De standaardpoort van het spel is niet gedocumenteerd; de opnemer gebruikt 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Het aanzetten {#switching-it-on-1}

Bewerk `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally en DiRT 4 gebruiken ook een `hardware_settings_config.xml`; de precieze map daarvoor is hier niet gecontroleerd) zodat het element `udp` er zo uitziet:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` zorgt dat posities, wielen en de etappelengte in het pakket komen. De opnemer past dit bestand niet aan.

### Wat het verstuurt {#what-it-sends-1}

66 little-endian floats (DiRT Rally: 64); pakketten korter dan 64 floats worden genegeerd, en een pakket van 64 floats wordt met nullen aangevuld. De gebruikte indices:

| Index | Veld | Kanaal |
|---|---|---|
| 1 | rondetijd (etappe) | de splitsingsklok en `time` |
| 2 | afstand in de ronde | `stageDistance` |
| 4-6 | wereldpositie | `x`, `y`, `z` |
| 7 | snelheid | `speed` |
| 8-10 | wereldsnelheid | `longVel` (op vooruit), `latVel` (op de zijvector) |
| 11-13 | zijvector | |
| 14-16 | vooruitvector | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | veerpositie RL RR FL FR | `suspensionM.*` |
| 25-28 | snelheid contactvlak van de wielen RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gas, sturing, rem, koppeling, versnelling | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 of hoger betekent achteruit, geschreven als -1) |
| 34, 35 | laterale en longitudinale g | `latAcc`, `longAcc` (maal 9,80665) |
| 37 | toerental / 10 | `rpm` (maal 10) |
| 51-54 | remtemperaturen | `brakeTemp.*` |
| 59, 60, 61, 62 | voltooide ronden, totaal aantal ronden, lengte van de baan, laatste rondetijd | splitsing |

Er is **geen handremkanaal**. De richting van de zijvector is in beide richtingen gedocumenteerd, dus het teken van `latVel` is niet te vertrouwen (de viewer leest de grootte van de drifthoek).

Een etappe is **klaar** wanneer het aantal voltooide ronden hoger is geworden dan de waarde bij het begin van de etappe (elke keer dat het gebeurt een rallycrossronde), of, bij een evenement met één ronde, wanneer de afstand in de ronde 99,9% van de lengte van de baan bereikt. De tijd van de etappe is de laatste rondetijd van het spel als die positief is. Controle: snelheid tegen snelheid zoals bij EA WRC, met de melding "is extradata set to 3?".

Bronnen: het UDP-document van Codemasters voor DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Het aanzetten {#switching-it-on-2}

In `RichardBurnsRally.ini`, sectie `[NGP]`: `udpTelemetry=1` en het eindpunt (127.0.0.1, poort 6776 tenzij je een andere `--port` meegeeft). De opnemer past dit bestand niet aan.

### Wat het verstuurt {#what-it-sends-2}

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): de etappeklok en afstand tot het einde, pedalen, sturing, versnelling, wereldpositie, houding, de eigen snelheden van de auto (voortstuwing vooruit, zijwaartse slinger, opheffing), versnellingen, toerental, en vier wielblokken van 128 bytes (LV, RV, LA, RA) met veerindrukking en veerkracht. Geen wielsnelheden.

| Kanaal | Van |
|---|---|
| `x`, `y`, `z` | positie, assen zoals verstuurd, daarna herordend (hieronder) |
| `longVel`, `latVel`, `vertVel` | voortstuwing, slinger, opheffing |
| `longAcc`, `latAcc` | versnelling x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | zoals verstuurd |
| `gear` | `gear - 1` (0 achteruit, 1 neutraal, 2 eerste) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | veerindrukking |
| `wheelLoad.*` | veerkracht |
| `speed` | **berekend uit de posities** over ±2 metingen, niet uit het pakket overgenomen |

De positieassen, de eenheden van de houding en de snelheidseenheid van RBR zijn niet gedocumenteerd, dus wordt bij het schrijven van een etappe de as waarlangs de etappe het minst varieert, als omhoog genomen en in `y` gezet (`orient_up`, heeft minstens 10 metingen nodig), en wordt de snelheid opnieuw uit de posities berekend (`speed_from_positions`). De houding wordt gedecodeerd maar niet geschreven, dus RBR-bestanden hebben geen `yaw`.

Een etappe is **klaar** wanneer de racetijd loopt en de afstand tot het einde nul heeft bereikt. De klok is `race_time`.

Bronnen: `rbr.telemetry.data.TelemetryData.h` van NGP via mika-n/RBRUDPTelemetryLogger en groybe/rbr-udp-telem.

## Etappes {#stages}

Alle vijf gebruiken `StageSplitter` op de etappeklok van het spel: een etappe opent wanneer de klok start, sluit voltooid wanneer het spel zegt dat de auto klaar is, en een klok die teruggaat (een herstart, of de volgende etappe) geeft de open etappe op - bewaard als een `_partial`-bestand als ze meer dan 10 metingen en minstens 300 m heeft. Voltooide etappes korter dan 300 m worden niet geschreven. Details: [Ronde- en etappesplitsing](lap-splitting.md).

## Het rondenbestand {#the-lap-file}

`game` is `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` of `richard-burns-rally`. `meta` is `{"discipline": "rally", "slip": null}`, plus `"surface": "<waarde>"` als `--surface` was opgegeven. `slip` is null omdat geen van deze spellen bandenslip stuurt. De snelheid van het contactvlak van elk wiel (EA WRC, DiRT) staat in het bestand, en de viewer leidt daar slip en de drifthoek uit af, samen met de assen van de auto; zie [Slip, drifthoek en afgeleide kanalen](slip-and-drift.md). De kanalen `suspension.*` (0..1 van de gebruikte veerweg) worden toegevoegd uit `suspensionM.*`.

Als er geen `--surface` is opgegeven, bevat het bestand met opzet helemaal geen wegdek: een standaardwaarde die hier wordt geschreven, zou het eigen afleiden van de viewer overschrijven. De viewer neemt het wegdek dan uit de naam van de etappe of het evenement (asfaltrally's, winterrally's, de Monte als gemengd), anders uit hoe de auto erop is gereden (hard sturen met kleine drifthoeken is asfalt), en losse ondergrond als niets het verraadt - wat een rallyetappe het vaakst is. Geef `--surface` als je het beter weet.
