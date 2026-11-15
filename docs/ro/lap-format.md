---
title: "Fișierul `heat3d-lap`"
nav_order: 9
lang: "ro"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Fișierul `heat3d-lap` {#the-heat3d-lap-file}

Fiecare înregistrator de telemetrie din acest depozit scrie un fișier pentru fiecare tură sau etapă de raliu, în aceeași formă, indiferent de joc. Exportul de traseu din [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) îl citește pentru a afla jocul, nivelul și traiectoria parcursă. Orice program care citește JSON poate citi acest fișier.

![Câmpurile și canalele unui fișier de tură scris dintr-un flux sintetic Forza](../assets/img/lap-file.svg)

## Documentul {#the-document}

Un obiect JSON. Canalele sunt stocate ca și coloane: un tablou pentru fiecare canal, toate de aceeași lungime, cu o intrare pentru fiecare eșantion.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Câmp | Înseamnă |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | din ce joc provine tura; vezi lista de mai jos |
| `track` | numele traseului, etapei sau hărții, când jocul îl trimite |
| `layout` | doar Forza: ce structură de pachet Data Out a fost decodată |
| `car` | tot ce spune jocul despre mașină; liber |
| `lap` | numărul turei, timpul ei așa cum l-a numărat jocul (sau intervalul eșantioanelor), dacă a fost terminată, lungimea ei |
| `meta` | cum se citesc numerele; vezi mai jos |
| `units` | unitatea fiecărui canal prezent, pentru un cititor care nu cunoaște tabelul de mai jos |
| `channels` | eșantioanele |
| `unparsed` | doar Forza, când pachetul are octeți cărora niciun câmp nu le dă nume: `ranges` (decalajele lor `[început, sfârșit)` în octeți din pachet) și `hex` (pentru fiecare eșantion, acei octeți în hexazecimal), astfel încât fișierul singur să conțină tot pachetul |

`game` este unul dintre `forza-horizon`, `forza-motorsport`, `forza` (structura pachetului nedeosebită), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` spune ce înseamnă numerele acolo unde jocurile diferă:

- `slip`: ce conțin canalele de alunecare, acolo unde jocul trimite vreuna - `peak` (normalizată, deci peste 1 anvelopa își pierde aderența: Forza), `scaled` (o alunecare fizică împărțită la un vârf tipic de asfalt: jocurile Assetto Corsa), `physical` (o fracție și radiani), `index` (o măsură de alunecare 0..1: Trackmania);
- `discipline`: `circuit`, `rally` sau `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` sau `mixed`, când este cunoscută (înregistratoarele de raliu o iau din `--surface`).

## Canale {#channels}

Un canal pe care jocul nu îl trimite lipsește, nu este umplut cu zerouri. Canalele pe fiecare roată poartă roata după un punct: `.FL`, `.FR`, `.RL`, `.RR`.

Pozițiile sunt ale lumii jocului, în metri, cu `y` în sus. Un joc a cărui lume are Z în sus este rotit de înregistratorul său la Y în sus; nimic altceva nu se schimbă, deci o lume levogiră (cea a Forza) rămâne levogiră.

| Canal | Unitate | Înțeles |
|---|---|---|
| `time` | s | de la primul eșantion al turei |
| `distance` | m | de-a lungul traseului parcurs de la primul eșantion |
| `x`, `y`, `z` | m | poziție; `y` este înălțimea |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedalele și maneta |
| `steer` | -1..1 | pozitiv la dreapta |
| `gear` | | așa cum o numără jocul |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | cadrul mașinii |
| `yaw`, `pitch`, `roll` | rad | orientarea și atitudinea |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | viteza în cadrul mașinii: dreapta, înainte, sus |
| `bodySlip` | rad | unghiul de derapaj, acolo unde jocul îl trimite |
| `loose` | 0/1 | pe sol afânat (Trackmania) |
| `airborne` | 0/1 | nicio roată pe sol |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | așa cum le trimite jocul |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | asistențele active, sisteme pornite |
| `absLevel`, `tcLevel` | | setările asistențelor |
| `brakeBias` | 0..1 | partea din față |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | pe fiecare roată |
| `tirePressure` | psi | pe fiecare roată |
| `tireWear` | 0..1 | pe fiecare roată |
| `slipRatio`, `slipAngle`, `combinedSlip` | vezi `meta.slip` | pe fiecare roată |
| `slipIndex` | 0..1 | măsura de alunecare pe fiecare roată (Trackmania) |
| `camber` | rad | pe fiecare roată |
| `brakeTemp` | °C | pe fiecare roată |
| `padLife`, `discLife` | | pe fiecare roată |
| `suspensionM` | m | cursa fiecărei roți |
| `suspension` | 0..1 | cursa fiecărei roți, din intervalul folosit de tura aceasta |
| `wheelLoad` | N | pe fiecare roată |
| `wheelSpeed` | rad/s | rotația fiecărei roți |
| `wheelSurfaceSpeed` | m/s | viteza punctului de contact al fiecărei roți |
| `groundContact` | 0/1 | pe fiecare roată |
| `rumble`, `surfaceRumble` | | pe fiecare roată: pe o bandă de zgomot; zgomotul suprafeței |
| `puddle` | | pe fiecare roată, adâncimea apei stătătoare |

Un înregistrator poate adăuga canale proprii, cu alte nume; un cititor le păstrează pe cele pe care nu le cunoaște.

Niciunul dintre jocurile de raliu nu trimite alunecarea anvelopelor. Un cititor o poate calcula din viteza punctului de contact sau a suprafeței fiecărei roți față de viteza mașinii, `(roată - mașină) / mașină`, sau din rotația ei și dintr-o rază de rulare măsurată pe tura însăși, acolo unde se trimite doar rotația. Unghiul de derapaj vine din viteza proprie a mașinii (`latVel`, `longVel`) acolo unde este trimisă, sau din viteza lumii proiectată pe axele mașinii.

## Forma CSV {#the-csv-form}

Pluginul Trackmania scrie în schimb `heat3d-lap-csv`: o primă linie cu `# ` și un obiect JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), o linie cu numele canalelor, apoi câte o linie pentru fiecare eșantion. Numele canalelor sunt aceleași ca mai sus.

## Ce scrie efectiv fiecare înregistrator {#what-each-recorder-actually-writes}

Formatul de mai sus este contractul; înregistratoarele îl completează ușor diferit, iar un cititor trebuie să tolereze toate acestea (verificat în cod):

| Înregistrator | `track` | `layout` | `meta` | `units` | Canale în afara tabelului |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (numărul de traseu al Forza Motorsport 2023 este `lap.trackOrdinal`) | structura pachetului detectată | `slip: peak`, `discipline: circuit` | doar unitățile canalelor prezente | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, ceasul jocului `timestampMs`, `raceTime`, `bestLap`, `lastLap`; viteza în cadrul mașinii este sub numele canonice `latVel`, `vertVel`, `longVel`; `unparsed` lângă canale |
| Jocurile Assetto Corsa (`kunos.py`) | din pagina statică, sau `null` | lipsește | `slip: scaled`, `discipline: circuit` sau `rally` | o listă fixă | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (cum a fost trimis), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Jocurile de raliu (`rally.py` prin `lapfile.py`) | `null` | lipsește | `discipline: rally`, `slip: null`, `surface` doar când s-a dat `--surface` (altfel îl deduce vizualizatorul) | doar unitățile canalelor prezente | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` pentru valorile în virgulă mobilă fără un nume stabilit; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` prin `lapfile.py`) | `null` | lipsește | `discipline: circuit` | doar unitățile canalelor prezente | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Pluginul Trackmania (CSV) | numele hărții | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` este blocul de mașină al Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` pentru jocurile Kunos când pagina statică indică un nume, și `{}` în rest. `lap.metres` este diferența distanței parcurse a jocului pentru Forza și suma distanțelor 3D între eșantioane în rest. Valorile sunt rotunjite la scriere: `time` la 4 zecimale, `distance` la 3, celelalte numere reale la 5. JSON-ul este scris compact (fără spații).

Fiecare pachet sau pagină primită de înregistrator - nu doar cele din ture - este păstrat întreg lângă fișierele de ture, în `<stamp>_<game>.raw.parquet`, cu o autoverificare în `<stamp>_<game>.summary.json` (secțiunea „Completeness" din README).

Un eșantion pentru care un canal nu are valoare - lipsește din cadrul acela, sau nu este un număr finit așa cum l-a trimis jocul - este scris ca `null` de fiecare înregistrator (`lapfile.clean`), iar fracția de suspensie derivată din el este și ea `null`. `NaN` și `Infinity` nu sunt scrise niciodată: nu sunt JSON, iar `JSON.parse` dintr-un browser refuză tot fișierul din cauza unuia dintre ele. Un cititor trebuie să se aștepte la `null` în tabloul unui canal.

Fișierele Forza au `"game": "forza-horizon"`, `"forza-motorsport"` sau `"forza"`, după structura detectată. Cititorul vizualizatorului pentru fișierele `.tele.gz` ale FH Companion produce ture cu `"game": "forza-horizon"` și `meta.slip = "peak"`; acel cititor se află în vizualizator, nu aici. Turele iRacing (citite din `.ibt` în vizualizator) au `"game": "iracing"`, care nu este în lista de valori `game` de mai sus, pentru că niciun înregistrator nu o scrie.

Vezi [Împărțirea în ture și etape](lap-splitting.md) pentru cum se decid `lap.number`, `lap.seconds` și `lap.complete`, și [Alunecare, derapaj și canale derivate](slip-and-drift.md) pentru ce deduce vizualizatorul din aceste canale.
