---
title: "EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally"
nav_order: 3
lang: "sv"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # or dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tester: `tests/test_rally.py`, på paket byggda från de dokumenterade layouterna. **Ännu inte körda mot de riktiga spelen.**

Alla skickar UDP som spelet slår på från sina egna inställningsfiler. Inspelaren lyssnar på alla gränssnitt (`0.0.0.0`) på spelets standardport om inte `--port` anger en annan: **20777** för `wrc`, `dirtrally2`, `dirtrally` och `dirt4`; **6776** för `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Slå på den {#switching-it-on}

Spelet läser `Documents\My Games\WRC\telemetry\config.json`. Standardstrukturen `wrc`:s `session_update`-paket måste slås på mot den här datorn:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funktionen `configure_wrc`):

- läser JSON, hittar `udp.packets` och posten med `"structure": "wrc"` och `"packet": "session_update"`;
- om den redan är påslagen mot `127.0.0.1` eller `localhost` på den porten används skriver den `already on` och ändrar ingenting;
- annars sätter den `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, och behåller postens `frequencyHz` (eller `-1` om den saknas). Saknas posten läggs en till;
- skriver den ursprungliga texten till `config.json.bak` bredvid, och skriver sedan den nya filen (indragen med 4 mellanslag).

Starta om spelet efter att du ändrat filen om det inte plockar upp ändringen (inte kontrollerat).

### Vad den skickar {#what-it-sends}

Standardstrukturen `wrc` är 237 byte, little-endian, utan header: världsposition, hastighet och acceleration (X vänster, Y upp, Z framåt), bilens vänster-, framåt- och upp-enhetsvektorer, per hjul (bak-vänster, bak-höger, fram-vänster, fram-höger) navets höjd och vertikala hastighet och kontaktytans framåthastighet, bromstemperaturer, pedaler efter hjälpsystem, styrning (-1 vänster, +1 höger), handbroms, rpm, växel, och etappklockan, distansen och längden. Ett paket kortare än 237 byte ignoreras och rapporteras en gång.

| Kanal | Från |
|---|---|
| `x`, `y`, `z` | världsposition |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | världshastighet projicerad på framåt, på minus vänster (så positivt är höger), på upp |
| `longAcc`, `latAcc`, `vertAcc` | världsacceleration projicerad på samma sätt |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | som skickat |
| `gear` | `gear_index`; -1 när den är lika med backindexet, 0 när den är lika med neutralindexet |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | navposition |
| `wheelSurfaceSpeed.*` | kontaktytans framåthastighet |
| `brakeTemp.*` | bromstemperatur |

Kontroll: om `speed` är över 10 och världshastighetsvektorns längd skiljer sig från den med mer än 20 % skriver inspelaren en gång ut att layouten kanske inte är standardstrukturen `wrc`.

En etapp är **klar** när etappens längd är positiv och distansen har nått längden minus 0,5 m. Klockan som används för delning och för `time` är `stage_time`.

Källor: EA:s UDP Telemetry Guide v1.3; kanallistan spelet skriver till `readme/channels.json`; offset så som nobonobo/obs-codemasters-telemetry och SpaceMonkey avkodar dem. Standardporten är inte dokumenterad; inspelaren använder 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Slå på den {#switching-it-on-1}

Redigera `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally och DiRT 4 använder också en `hardware_settings_config.xml`; deras exakta mapp för de två är inte kontrollerad här) så att `udp`-elementet lyder:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` är det som lägger positioner, hjul och etappens längd i paketet. Inspelaren ändrar inte den här filen.

### Vad den skickar {#what-it-sends-1}

66 little-endian-flyttal (DiRT Rally: 64). Paket kortare än 64 flyttal ignoreras, och ett 64-flyttalspaket fylls ut med nollor. Indexen som används:

| Index | Fält | Kanal |
|---|---|---|
| 1 | varvtid (etapp) | delningsklockan och `time` |
| 2 | varvdistans | `stageDistance` |
| 4-6 | världsposition | `x`, `y`, `z` |
| 7 | hastighet | `speed` |
| 8-10 | världshastighet | `longVel` (på framåt), `latVel` (på sidvektorn) |
| 11-13 | sidvektor | |
| 14-16 | framåtvektor | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | fjädringsposition RL RR FL FR | `suspensionM.*` |
| 25-28 | hjulets kontaktytefart RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gas, styrning, broms, koppling, växel | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 eller mer betyder back, skrivs som -1) |
| 34, 35 | sid- och längdacceleration i g | `latAcc`, `longAcc` (gånger 9,80665) |
| 37 | rpm / 10 | `rpm` (gånger 10) |
| 51-54 | bromstemperaturer | `brakeTemp.*` |
| 59, 60, 61, 62 | antal avklarade varv, totala varv, banlängd, senaste varvtid | delning |

Det finns **ingen handbromskanal**. Sidvektorns riktning är dokumenterad åt båda håll, så tecknet på `latVel` ska inte litas på. Visaren läser driftvinkelns storlek.

En etapp är **klar** när antalet avklarade varv stiger över sitt värde vid etappens start (ett rallycross-varv varje gång det gör det), eller, för ett enkelvarvsevent, när varvdistansen når 99,9 % av banans längd. Etappens tid är spelets senaste varvtid när den är positiv. Kontroll: hastighet mot fart, som för EA WRC, med meddelandet "is extradata set to 3?".

Källor: Codemasters DiRT 4 UDP-dokument; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Slå på den {#switching-it-on-2}

I `RichardBurnsRally.ini`, sektionen `[NGP]`: `udpTelemetry=1` och slutpunkten (127.0.0.1, port 6776 om du inte anger en annan med `--port`). Inspelaren ändrar inte den här filen.

### Vad den skickar {#what-it-sends-2}

664 byte (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): etappklocka och distans till målet, pedaler, styrning, växel, världsposition, attityd, bilens egna hastigheter (längdrörelse framåt, sidrörelse åt sidan, höjdrörelse), accelerationer, rpm, och fyra 128-byte-hjulblock (LF, RF, LB, RB) med fjäderutslag och fjäderkraft. Inga hjulhastigheter.

| Kanal | Från |
|---|---|
| `x`, `y`, `z` | position, axlarna som skickade, sedan omordnade (nedan) |
| `longVel`, `latVel`, `vertVel` | längd-, sid- och höjdrörelse |
| `longAcc`, `latAcc` | acceleration x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | som skickat |
| `gear` | `gear - 1` (0 back, 1 neutral, 2 ettan) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | fjäderutslag |
| `wheelLoad.*` | fjäderkraft |
| `speed` | **beräknad från positionerna** över ±2 sampel, inte tagen från paketet |

RBR:s positionsaxlar, attitydenheter och hastighetsenhet är inte dokumenterade. När en etapp skrivs tas därför axeln etappen varierar minst längs som upp och byts in i `y` (`orient_up`, behöver minst 10 sampel), och hastigheten räknas om från positionerna (`speed_from_positions`). Attityd avkodas men skrivs inte, så RBR-filer har ingen `yaw`.

En etapp är **klar** när loppklockan går och avståndet till målet har nått noll. Klockan är `race_time`.

Källor: NGP:s `rbr.telemetry.data.TelemetryData.h` via mika-n/RBRUDPTelemetryLogger och groybe/rbr-udp-telem.

## Etapper {#stages}

Alla fem använder `StageSplitter` på spelets etappklocka: en etapp öppnas när klockan startar och stängs komplett när spelet säger att bilen är klar. En klocka som går bakåt (en omstart, eller nästa etapp) överger den öppna etappen. Den behålls som en `_partial`-fil om den har fler än 10 sampel och minst 300 m. Avklarade etapper kortare än 300 m skrivs inte. Detaljer: [Hur varv och etapper delas](lap-splitting.md).

## Varvfilen {#the-lap-file}

`game` är `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` eller `richard-burns-rally`. `meta` är `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"` när `--surface` angavs. `slip` är null eftersom inget av dessa spel skickar däckslip. Varje hjuls kontaktytefart (EA WRC, DiRT) ligger i filen i stället, och visaren härleder slip och driftvinkeln från den och bilens axlar; se [Slip, drift och härledda kanaler](slip-and-drift.md). `suspension.*`-kanalerna (0..1 av den använda vägen) läggs till från `suspensionM.*`.

När ingen `--surface` anges har filen ingen yta alls, med flit: ett standardvärde skrivet här skulle åsidosätta visarens egen slutsats. Visaren tar då ytan från etappens eller eventets namn (asfaltsrallyn, vinterrallyn, Monte som blandad). Annars tar den den från hur bilen kördes på den: hård kurvtagning med små driftvinklar är asfalt. Och när inget säger något blir den lös, vilket är vad en rallyetapp oftast är. Ange `--surface` när du vet bättre.
