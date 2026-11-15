---
title: "Lojërat Assetto Corsa"
nav_order: 2
lang: "sq"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO dhe AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kodi: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testet: `tests/test_kunos.py` (faqe sintetike). Ende të pa ekzekutuara kundrejt lojërave të vërteta.

## Nga vijnë të dhënat {#where-the-data-comes-from}

Lojërat e Kunos publikojnë telemetri për aplikacionet si **faqe të emërtuara të memories së përbashkët të Windows** që
loja i shkruan dhe kushdo mund t'i lexojë. Regjistruesi i hap vetëm për lexim (`mmap` me një emër etikete),
prandaj duhet të ekzekutohet **në PC-në ku punon loja**, në Windows; gjetkë del me një mesazh.
Faqet hapen një herë, kur nis regjistruesi. Nisja e lojës dhe hyrja në makinë më parë
është renditja e sigurt; nëse funksionon nisja e regjistruesit para lojës nuk është kontrolluar.

| `--game` | Faqja e fizikës | Faqja grafike (numëruesi i xhirove) | Faqja statike (emrat) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nuk përdoret | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nuk përdoret | `Local\acevo_pmf_static` |

Faqja e fizikës lexohet 200 herë në sekondë (`hz=200`); një kampion i ri merret vetëm kur `packetId` i saj
ka ndryshuar dhe nuk është zero. 800 bajtet e para të faqes së fizikës ndajnë një strukturë të vetme
në të katër lojërat; faqja e lojës së parë garantohet vetëm 580 bajte, kështu që nëse një
mapim 800-bajtësh nuk hapet regjistruesi kthehet te 580 dhe fushat përtej tij
mungojnë.

## Pozicioni {#position}

Asnjë faqe nuk mbart një pozicion makine si të tillë, por faqja e fizikës mban **pikën e kontaktit të çdo
gome në koordinata botërore** (zhvendosja 420, katër treshe XYZ). Pozicioni i makinës është
mesatarja e të katërve. Një faqe pikat e kontaktit të së cilës janë të gjitha zero (meny, garazh) nuk prodhon
kampion.

## Kanalet {#channels}

| Kanali | Nga | Shënime |
|---|---|---|
| `time` | ora e vetë regjistruesit | sekonda që nga nisja e regjistrimit, e rivendosur te kampioni i parë i xhiros |
| `x`, `y`, `z` | mesatarja e pikave të kontaktit të gomave | metra botërorë |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | njësitë e lojës, shkallëzuar për çdo xhiro në -1..1 me vlerën absolute më të madhe që përdori xhiroja, **vetëm nëse** ajo vlerë tejkalon 1.05 (një hyrje që është tashmë në -1..1 lihet siç është) |
| `gear` | `gear - 1` | loja numëron 0 mbrapa, 1 neutral, 2 e para; shkruhet si -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, herë 9.80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | shpejtësia lokale te zhvendosja 568 | korniza e makinës; vetëm kur nuk është zero. Nga cila anë drejtohet x dokumentohet në të dyja mënyrat, prandaj lexo madhësinë e këndit të drift-it, jo shenjën e tij |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | zhvendosja 564 | vetëm faqja 800-bajtëshe |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: zhvendosjet 204 dhe 252, shkruar si 1 kur mbi 0; AC: `tcInAction`/`absInAction` nga faqja 800-bajtëshe kur është e pranishme | ndihma në veprim |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | e nxjerrë | 0..1 e udhëtimit të përdorur nga kjo xhiro (min deri max i `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | zhvendosjet 640, 656 (faqja 800-bajtëshe) | e pjesëtuar me një maksimum tipik - shih më poshtë |
| `slipRatioRaw.*`, `slipAngleRaw.*` | të njëjtat | vlerat fizike, pa shkallëzim |
| `padLife.*`, `discLife.*` | zhvendosjet 740, 756 | vetëm faqja 800-bajtëshe |

AC Rally i dërgon temperaturat e gomave dhe frenave në kelvin: për `--game acrally`, çdo
vlerë e tyre mbi 200 ka 273.15 të zbritur.

`wheelSlip` (zhvendosja 56) dekodohet por nuk shkruhet.

## Shkallëzimi i rrëshqitjes {#slip-scaling}

Forza dërgon rrëshqitjen e normalizuar që 1 të jetë skaji i kapjes. Kunos dërgon raportin fizik të rrëshqitjes
dhe këndin e rrëshqitjes. Prandaj regjistruesi i pjesëton me një maksimum tipik në asfalt - **0.12** për
raportin e rrëshqitjes dhe **0.14 rad (rreth 8 gradë)** për këndin e rrëshqitjes - që leximi i shikuesit
"pas 1 do të thotë rrëshqet" të qëndrojë përafërsisht, i mban vlerat e papërpunuara pranë tyre, dhe shkruan
`"meta": {"slip": "scaled"}`. Ku përfundon realisht kapja, shikuesi e mat për çdo makinë nga
xhirot. Shih [Rrëshqitja, drift-i dhe kanalet e nxjerra](slip-and-drift.md).

## Xhirot {#laps}

- **AC dhe ACC** i numërojnë xhirot në faqen grafike (`completedLaps` te zhvendosja 132, koha e
  xhiros së fundit në milisekonda te 144). `CounterSplitter` e mbyll një xhiro kur numëruesi
  ndryshon; shënohet e plotë, me kohën e xhiros të lojës, vetëm nëse numëruesi u rrit saktësisht
  me një.
- **AC EVO dhe AC Rally** nuk lexohen për xhiro (faqja grafike e EVO është një strukturë tjetër, më e madhe;
  AC Rally vozit etapa). `LineSplitter` e përdor pikën ku nisi regjistrimi si
  vijë: një xhiro mbyllet kur makina kalon më afër saj herën tjetër duke shkuar në të njëjtin drejtim, dhe një
  etapë ose çdo vozitje mbyllet kur makina qëndron në vend për 8 sekonda.

Detajet dhe pragjet: [Ndarja e xhirove dhe e etapave](lap-splitting.md).

## Emrat e pistës dhe të makinës {#track-and-car-names}

Lexohen një herë, nga faqja statike, kur vjen kampioni i parë: për AC, ACC dhe AC Rally
makina (UTF-16, zhvendosja 68) dhe pista (zhvendosja 134); për AC EVO pista dhe konfigurimi i saj
(tekst njëbajtësh te zhvendosjet 136 dhe 169, i bashkuar me një hapësirë) dhe pa makinë. Hyjnë në
skedar si `track` dhe `car: {"name": ...}`.

## Skedari i xhiros {#the-lap-file}

`game` është `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ose
`assetto-corsa-rally`; `meta` është `{"slip": "scaled", "discipline": "rally"}` për AC Rally dhe
`{"slip": "scaled", "discipline": "circuit"}` për tri të tjerat. Nuk shkruhet `surface`.

## Burimet {#sources}

SDK i memories së përbashkët të AC1; dokumentacioni i memories së përbashkët të ACC (v1.8); struktura e AC EVO siç
është matur te `albertowd/live-telemetry-evo`; ajo e AC Rally siç lexohet nga
`LuizZak/AssettoCorsaRallyTelemetryReader`. Shih [Lojërat](games.md).
