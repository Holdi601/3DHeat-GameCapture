---
title: "Ralllíleikir"
nav_order: 3
lang: "is"
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

Kóði: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Prófanir: `tests/test_rally.py`, á pökkum smíðuðum eftir skjalfestum uppsetningum. **Ekki enn keyrt
gegn raunverulegu leikjunum.**

Þeir senda allir UDP sem leikurinn kveikir á úr eigin stillingaskrám. Upptökutækið
hlustar á öllum viðmótum (`0.0.0.0`) á sjálfgefinni gátt leiksins nema `--port` gefi
aðra: **20777** fyrir `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** fyrir `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Að kveikja á því {#switching-it-on}

Leikurinn les `Documents\My Games\WRC\telemetry\config.json`. `session_update` pakka sjálfgefnu `wrc`
byggingarinnar þarf að virkja í átt að þessari vél:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (fallið `configure_wrc`):

- les JSON, finnur `udp.packets` og færsluna með `"structure": "wrc"` og
  `"packet": "session_update"`;
- ef þegar er virkjað til `127.0.0.1` eða `localhost` á gáttinni sem er í notkun, prentar
  `already on` og breytir engu;
- annars setur `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, og heldur
  `frequencyHz` færslunnar (eða `-1` ef ekkert); ef engin slík færsla er til bætir það einni við;
- skrifar upprunalega textann í `config.json.bak` við hlið hennar, skrifar síðan nýju skrána
  (inndregið um 4 bil).

Endurræstu leikinn eftir að skránni er breytt ef hann tekur ekki upp breytinguna (ekki athugað).

### Hvað hann sendir {#what-it-sends}

Sjálfgefna `wrc` byggingin er 237 bæti, little-endian, enginn haus: heimsstaða,
hraði og hröðun (X vinstri, Y upp, Z áfram), vinstri / fram / upp einingavigrar bílsins, fyrir hvert hjól (aftan-vinstri, aftan-hægri,
fram-vinstri, fram-hægri) hæð hubbs og
lóðréttur hraði og framhraði snertiflatarins, bremsuhiti, pedalar eftir
hjálpartæki, stýring (-1 vinstri, +1 hægri), handbremsa, rpm, gír, og leiðarklukka, vegalengd og
lengd. Pakki styttri en 237 bæti er hunsaður og tilkynntur einu sinni.

| Rás | Úr |
|---|---|
| `x`, `y`, `z` | heimsstaða |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | heimshraði varpað á fram, á mínus vinstri (svo jákvætt er hægri), á upp |
| `longAcc`, `latAcc`, `vertAcc` | heimshröðun varpað á sama hátt |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | eins og sent |
| `gear` | `gear_index`; -1 þegar það jafngildir bakkgírsvísinum, 0 þegar það jafngildir hlutlausa vísinum |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | staða hubbs |
| `wheelSurfaceSpeed.*` | framhraði snertiflatar |
| `brakeTemp.*` | bremsuhiti |

Athugun: ef `speed` er yfir 10 og lengd heimshraðans víkur frá því um meira en
20% prentar upptökutækið einu sinni að uppsetningin gæti ekki verið sjálfgefna `wrc` byggingin.

Leið er **kláruð** þegar lengd leiðar er jákvæð og vegalengdin hefur náð
lengdinni mínus 0,5 m. Klukkan sem notuð er til skiptingar og fyrir `time` er `stage_time`.

Heimildir: UDP Telemetry Guide v1.3 frá EA; rásalistinn sem leikurinn skrifar í
`readme/channels.json`; færslur eins og nobonobo/obs-codemasters-telemetry og
SpaceMonkey afkóða þær. Sjálfgefin gátt er ekki skjalfest; upptökutækið notar 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Að kveikja á því {#switching-it-on-1}

Breyttu `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally og DiRT 4 nota líka `hardware_settings_config.xml`; nákvæm mappa þeirra tveggja er
ekki athuguð hér) þannig að `udp` frumefnið segi:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` er það sem setur staðsetningar, hjól og leiðarlengd í pakkann. Upptökutækið
breytir ekki þessari skrá.

### Hvað hann sendir {#what-it-sends-1}

66 little-endian fleytitölur (DiRT Rally: 64); pakkar styttri en 64 fleytitölur eru hunsaðir og
64 fleytitalna pakki er fylltur með núllum. Vísarnir sem eru notaðir:

| Vísir | Reitur | Rás |
|---|---|---|
| 1 | hringtími (leiðar) | skiptiklukkan og `time` |
| 2 | hringvegalengd | `stageDistance` |
| 4-6 | heimsstaða | `x`, `y`, `z` |
| 7 | hraði | `speed` |
| 8-10 | heimshraði | `longVel` (á fram), `latVel` (á hliðarvigur) |
| 11-13 | hliðarvigur | |
| 14-16 | framvigur | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | fjöðrunarstaða RL RR FL FR | `suspensionM.*` |
| 25-28 | hraði hjólsnertiflatar RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | inngjöf, stýring, bremsa, kúpling, gír | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 eða meira þýðir bakk, skrifað sem -1) |
| 34, 35 | hliðar-, lengdar-g | `latAcc`, `longAcc` (sinnum 9.80665) |
| 37 | rpm / 10 | `rpm` (sinnum 10) |
| 51-54 | bremsuhiti | `brakeTemp.*` |
| 59, 60, 61, 62 | kláraðir hringir, hringir alls, lengd brautar, síðasti hringtími | skipting |

**Engin handbremsurás** er til. Stefna hliðarvigursins er skjalfest á báða vegu, svo
ekki má treysta formerki `latVel` (áhorfandinn les stærð rekhornsins).

Leið er **kláruð** þegar fjöldi kláraðra hringja hækkar yfir gildi sitt í upphafi
leiðarinnar (hringur í rallycross í hvert sinn sem það gerist), eða, fyrir viðburð með einum hring, þegar hringvegalengdin
nær 99,9% af lengd brautar. Tími leiðarinnar er síðasti hringtími leiksins þegar hann er
jákvæður. Athugun: hraði gegn hraðamæli eins og fyrir EA WRC, með skilaboðunum „is extradata set
to 3?“.

Heimildir: UDP skjal Codemasters fyrir DiRT 4; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Að kveikja á því {#switching-it-on-2}

Í `RichardBurnsRally.ini`, kafla `[NGP]`: `udpTelemetry=1` og endapunkturinn (127.0.0.1,
gátt 6776 nema þú gefir aðra `--port`). Upptökutækið breytir ekki þessari skrá.

### Hvað hann sendir {#what-it-sends-2}

664 bæti (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): leiðarklukka og vegalengd
að marki, pedalar, stýring, gír, heimsstaða, afstaða, eigin hraðar bílsins
(surge áfram, sway til hliðar, heave), hröðun, rpm, og fjórar 128 bæta hjólablokkir
(LF, RF, LB, RB) með fjöðrunarslagi og fjöðrunarkrafti. Engir hjólahraðar.

| Rás | Úr |
|---|---|
| `x`, `y`, `z` | staða, ásar eins og sent, síðan endurraðað (hér að neðan) |
| `longVel`, `latVel`, `vertVel` | surge, sway, heave |
| `longAcc`, `latAcc` | hröðun x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | eins og sent |
| `gear` | `gear - 1` (0 bakk, 1 hlutlaus, 2 fyrsti) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | fjöðrunarslag |
| `wheelLoad.*` | fjöðrunarkraftur |
| `speed` | **reiknað úr staðsetningunum** yfir +-2 sýni, ekki tekið úr pakkanum |

Staðsetningarásar RBR, afstöðueiningar og hraðaeining eru óskjalfest, svo þegar leið er
skrifuð: ásinn sem leiðin breytist minnst eftir er tekinn sem upp og skipt í `y`
(`orient_up`, þarf að minnsta kosti 10 sýni), og hraðinn er endurreiknaður úr staðsetningunum
(`speed_from_positions`). Afstaða er afkóðuð en ekki skrifuð, svo RBR skrár hafa ekkert `yaw`.

Leið er **kláruð** þegar keppnisklukkan er í gangi og vegalengd að marki hefur
náð núlli. Klukkan er `race_time`.

Heimildir: `rbr.telemetry.data.TelemetryData.h` frá NGP um mika-n/RBRUDPTelemetryLogger og
groybe/rbr-udp-telem.

## Leiðir {#stages}

Allir fimm nota `StageSplitter` á leiðarklukku leiksins: leið opnast þegar klukkan ræsist,
lokast kláruð þegar leikurinn segir að bíllinn sé kominn í mark, og klukka sem fer afturábak (endurræsing,
eða næsta leið) yfirgefur opnu leiðina - geymd sem `_partial` skrá ef hún hefur fleiri en 10
sýni og að minnsta kosti 300 m. Kláraðar leiðir styttri en 300 m eru ekki skrifaðar. Nánar:
[Hring- og leiðaskipting](lap-splitting.md).

## Hringskráin {#the-lap-file}

`game` er `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` eða `richard-burns-rally`.
`meta` er `{"discipline": "rally", "slip": null}`, auk `"surface": "<value>"` þegar `--surface`
var gefið. `slip` er null því enginn þessara leikja sendir dekkjaskrið. Hraði snertiflatar hvers hjóls
(EA WRC, DiRT) er í skránni í staðinn, og áhorfandinn leiðir skrið og rekhorn út frá
honum og ásum bílsins; sjá [Skrið, rek og afleiddar rásir](slip-and-drift.md). Rásirnar
`suspension.*` (0..1 af slaginu sem notað var) eru bættar við úr `suspensionM.*`.

Þegar ekkert `--surface` er gefið ber skráin ekkert undirlag, viljandi: sjálfgefið gildi skrifað
hér myndi yfirskrifa eigin ályktun áhorfandans. Áhorfandinn tekur þá undirlagið úr heiti
leiðarinnar eða viðburðarins (malbiksrallí, vetrarrallí, Monte sem blandað), annars úr því hvernig bílnum
var ekið á því (hörð beygja við lítil rekhorn er malbik), og laust þegar ekkert segir til um það
- sem er það sem rallíleið er oftast. Gefðu `--surface` þegar þú veist betur.
