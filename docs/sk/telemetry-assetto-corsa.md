---
title: "Hry Assetto Corsa"
nav_order: 2
lang: "sk"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO a AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kód: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testy: `tests/test_kunos.py` (syntetické stránky). Zatiaľ nespustené proti živým hrám.

## Odkiaľ prichádzajú dáta {#where-the-data-comes-from}

Hry Kunos zverejňujú telemetriu pre aplikácie ako **pomenované stránky zdieľanej
pamäte Windows**, ktoré hra zapisuje a ktoré môže čítať ktokoľvek. Nahrávač ich
otvára len na čítanie (`mmap` s menom značky), takže musí bežať **na PC, kde hra
beží**, vo Windows; inde skončí s hláškou.
Stránky sa otvoria raz, pri štarte nahrávača. Bezpečné poradie je najprv spustiť
hru a sadnúť do auta; či funguje spustenie nahrávača pred hrou, nebolo
overené.

| `--game` | Stránka fyziky | Stránka grafiky (počítadlo kôl) | Statická stránka (názvy) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nepoužíva sa | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nepoužíva sa | `Local\acevo_pmf_static` |

Stránka fyziky sa číta 200-krát za sekundu (`hz=200`); nová vzorka sa zoberie len
vtedy, keď sa jej `packetId` zmení a nie je nulové. Prvých 800 bajtov stránky
fyziky má vo všetkých štyroch hrách rovnaké rozloženie; prvá hra má zaručených
len 580 bajtov, takže ak sa mapovanie 800 bajtov nedá otvoriť, nahrávač sa
vráti na 580 a polia za nimi chýbajú.

## Poloha {#position}

Žiadna zo stránok nenesie polohu auta ako takú, ale stránka fyziky drží **bod
kontaktu každej pneumatiky** vo svetových súradniciach (offset 420, štyri
trojice XYZ). Poloha auta je priemer štyroch. Stránka, na ktorej sú všetky body
kontaktu nulové (menu, garáž), nedá žiadnu vzorku.

## Kanály {#channels}

| Kanál | Zdroj | Poznámky |
|---|---|---|
| `time` | vlastné hodiny nahrávača | sekundy od začiatku nahrávania, prepočítané na prvú vzorku kola |
| `x`, `y`, `z` | priemer bodu kontaktu pneumatík | svetové metre |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | jednotky hry, prepočítané pre každé kolo na -1..1 podľa najväčšej absolútnej hodnoty, ktorú kolo použilo, **len ak** táto hodnota presiahne 1,05 (vstup už v rozsahu -1..1 sa nemení) |
| `gear` | `gear - 1` | hra počíta 0 spiatočka, 1 neutrál, 2 prvý stupeň; zapíše sa ako -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, krát 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokálna rýchlosť na offsete 568 | vnútorný systém auta; len ak nie je nulová. Na ktorú stranu smeruje x, je zdokumentované v oboch smeroch, takže spoľahnite sa na veľkosť driftového uhla, nie na jeho znamienko |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | len stránka 800 bajtov |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offsety 204 a 252, zapísané ako 1, keď je nad 0; AC: `tcInAction`/`absInAction` zo stránky 800 bajtov, ak je prítomná | asistencie v činnosti |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | odvodené | 0..1 zdvihu použitého v tomto kole (min až max z `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offsety 640, 656 (stránka 800 bajtov) | delené typickým vrcholom – pozrite nižšie |
| `slipRatioRaw.*`, `slipAngleRaw.*` | to isté | fyzikálne hodnoty, neškálované |
| `padLife.*`, `discLife.*` | offsety 740, 756 | len stránka 800 bajtov |

AC Rally posiela teploty pneumatík a bŕzd v kelvinoch: pri `--game acrally` sa
od každej z týchto hodnôt nad 200 odčíta 273,15.

`wheelSlip` (offset 56) sa dekóduje, ale nezapisuje sa.

## Škálovanie prešmyku {#slip-scaling}

Forza posiela prešmyk normalizovaný tak, že 1 je hranica prilipnutia. Kunos posiela
fyzikálny pomer prešmyku a uhol prešmyku. Nahrávač ich preto delí typickým
vrcholom na asfalte – **0,12** pre pomer prešmyku a **0,14 rad (asi 8 stupňov)** pre
uhol prešmyku – aby čítanie prehliadača „nad 1 znamená šmyk“ približne platilo,
ponecháva surové hodnoty vedľa nich a zapisuje `"meta": {"slip": "scaled"}`. Kde
prilipnutie naozaj končí, prehliadač meria pre každé auto z kôl. Pozrite [Prešmyk, drift a odvodené kanály](slip-and-drift.md).

## Kolá {#laps}

- **AC a ACC** počítajú kolá na stránke grafiky (`completedLaps` na offsete 132,
  čas posledného kola v milisekundách na 144). `CounterSplitter` uzavrie kolo,
  keď sa počítadlo zmení; je označené ako dokončené s časom hry, len ak počítadlo
  vzrástlo presne o jedno.
- **AC EVO a AC Rally** sa pre kolá nečítajú (grafická stránka EVO má iné,
  väčšie rozloženie; AC Rally jazdí etapy). `LineSplitter` používa bod, kde
  nahrávanie začalo, ako čiaru: kolo sa uzavrie, keď auto ďalší raz prejde
  najbližšie k nej v rovnakom smere, a etapa alebo ľubovoľná jazda sa uzavrie,
  keď auto stojí 8 sekúnd.

Podrobnosti a prahy: [Delenie kôl a etáp](lap-splitting.md).

## Názov auta a trate {#track-and-car-names}

Prečíta sa raz, zo statickej stránky, keď príde prvá vzorka: pre AC, ACC a AC
Rally auto (UTF-16, offset 68) a trať (offset 134); pre AC EVO trať a jej
konfiguráciu (jednobajtový text na offsetoch 136 a 169, spojené medzerou) a
bez auta. Zapíšu sa do súboru ako `track` a `car: {"name": ...}`.

## Súbor kola {#the-lap-file}

`game` je `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` alebo
`assetto-corsa-rally`; `meta` je `{"slip": "scaled", "discipline": "rally"}` pre AC Rally a
`{"slip": "scaled", "discipline": "circuit"}` pre ostatné tri. `surface` sa nezapisuje.

## Zdroje {#sources}

SDK AC1 pre zdieľanú pamäť; dokumentácia zdieľanej pamäte ACC (v1.8); rozloženie
AC EVO tak, ako bolo namerané v `albertowd/live-telemetry-evo`; rozloženie AC
Rally tak, ako ho číta `LuizZak/AssettoCorsaRallyTelemetryReader`. Pozrite [Hry](games.md).
