---
title: "Assetto Corsa, ACC, AC EVO och AC Rally"
nav_order: 2
lang: "sv"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO och AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kod: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tester: `tests/test_kunos.py` (syntetiska sidor). Ännu inte körda mot de riktiga spelen.

## Varifrån datan kommer {#where-the-data-comes-from}

Kunos spel publicerar telemetri för appar som **namngivna delade minnessidor i Windows**, som spelet skriver och vem som helst får läsa. Inspelaren öppnar dem skrivskyddat (`mmap` med ett taggnamn), så den måste köras **på datorn spelet körs på**, i Windows. Annars avslutas den med ett meddelande. Sidorna öppnas en gång, när inspelaren startar. Att starta spelet och komma in i bilen först är den säkra ordningen. Om det fungerar att starta inspelaren före spelet är inte kontrollerat.

| `--game` | Fysiksida | Grafiksida (varvräknare) | Statisk sida (namn) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | används inte | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | används inte | `Local\acevo_pmf_static` |

Fysiksidan läses 200 gånger per sekund (`hz=200`). Ett nytt sampel tas bara när dess `packetId` har ändrats och inte är noll. De första 800 byte av fysiksidan har samma layout i alla fyra spel. Det första spelets sida garanteras bara 580 byte, så om en 800-byte-mappning inte kan öppnas faller inspelaren tillbaka till 580, och fälten bortom det saknas.

## Position {#position}

Ingen av sidorna bär en bils position som sådan, men fysiksidan innehåller **varje däcks kontaktpunkt i världskoordinater** (offset 420, fyra XYZ-trippel). Bilens position är medelvärdet av de fyra. En sida där alla kontaktpunkter är noll (meny, garage) ger inget sampel.

## Kanaler {#channels}

| Kanal | Från | Anmärkningar |
|---|---|---|
| `time` | inspelarens egen klocka | sekunder sedan inspelningen började, omräknade till varvets första sampel |
| `x`, `y`, `z` | medelvärdet av däckens kontaktpunkter | världsmeter |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | spelets enheter, skalade per varv till -1..1 med det största absolutvärdet varvet använde, **bara om** det värdet överstiger 1,05 (en insignal redan i -1..1 lämnas orörd) |
| `gear` | `gear - 1` | spelet räknar 0 back, 1 neutral, 2 ettan; skrivs som -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, gånger 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokal hastighet vid offset 568 | bilens ram; bara när den inte är noll. Vilken sida x pekar mot är dokumenterat åt båda håll, så läs driftvinkelns storlek, inte dess tecken |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | bara 800-byte-sidan |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offset 204 och 252, skrivs som 1 när värdet är över 0. AC: `tcInAction`/`absInAction` från 800-byte-sidan när den finns | hjälpsystem aktiva |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | härleds | 0..1 av den väg varvet använde (min till max av `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offset 640, 656 (800-byte-sidan) | delat med ett typiskt toppvärde, se nedan |
| `slipRatioRaw.*`, `slipAngleRaw.*` | samma | de fysiska värdena, oskalade |
| `padLife.*`, `discLife.*` | offset 740, 756 | bara 800-byte-sidan |

AC Rally skickar sina däck- och bromstemperaturer i kelvin: för `--game acrally` dras 273,15 från alla värden över 200.

`wheelSlip` (offset 56) avkodas men skrivs inte.

## Slip-skalning {#slip-scaling}

Forza skickar slip normaliserad så att 1 är gränsen för grepp. Kunos skickar den fysiska slip-kvoten och slip-vinkeln. Så inspelaren delar dem med ett typiskt toppvärde för asfalt: **0,12** för slip-kvoten och **0,14 rad (ungefär 8 grader)** för slip-vinkeln. Därmed håller visarens läsning "över 1 betyder glidning" ungefär, de råa värdena behålls bredvid, och filen skriver `"meta": {"slip": "scaled"}`. Var grepp faktiskt upphör mäter visaren per bil från varven. Se [Slip, drift och härledda kanaler](slip-and-drift.md).

## Varv {#laps}

- **AC och ACC** räknar varv på grafiksidan (`completedLaps` vid offset 132, senaste varvets tid i millisekunder vid 144). `CounterSplitter` stänger ett varv när räknaren ändras. Det markeras komplett, med spelets varvtid, bara om räknaren gick upp med exakt ett.
- **AC EVO och AC Rally** läses inte för varv. EVO:s grafiksida är en annan, större layout, och AC Rally kör etapper. `LineSplitter` använder punkten där inspelningen började som linje: ett varv stängs när bilen nästa gång passerar närmast den i samma riktning, och en etapp eller valfri körning stängs när bilen står still i 8 sekunder.

Detaljer och tröskelvärden: [Hur varv och etapper delas](lap-splitting.md).

## Bane- och bilnamn {#track-and-car-names}

Läses en gång, från den statiska sidan, när det första samplet kommer. För AC, ACC och AC Rally läses bilen (UTF-16, offset 68) och banan (offset 134). För AC EVO läses banan och dess konfiguration (enkelbyte-text vid offset 136 och 169, sammanfogade med ett mellanslag) och ingen bil. De läggs i filen som `track` och `car: {"name": ...}`.

## Varvfilen {#the-lap-file}

`game` är `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` eller `assetto-corsa-rally`. `meta` är `{"slip": "scaled", "discipline": "rally"}` för AC Rally och `{"slip": "scaled", "discipline": "circuit"}` för de andra tre. Ingen `surface` skrivs.

## Källor {#sources}

AC1:s SDK för delat minne; ACC:s dokumentation för delat minne (v1.8); AC EVO:s layout så som den mätts i `albertowd/live-telemetry-evo`; AC Rallys så som den läses av `LuizZak/AssettoCorsaRallyTelemetryReader`. Se [Spel](games.md).
