---
title: "Hry Assetto Corsa"
nav_order: 2
lang: "cs"
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
Testy: `tests/test_kunos.py` (syntetické stránky). Zatím nespuštěno proti živým hrám.

## Odkud data přicházejí {#where-the-data-comes-from}

Hry Kunos zveřejňují telemetrii pro aplikace jako **pojmenované stránky sdílené paměti
Windows**, které hra zapisuje a kdokoli je smí číst. Nahrávač je otevírá jen pro čtení
(`mmap` s názvem značky), takže musí běžet **na počítači, kde hra běží**, na Windows; jinde
skončí se zprávou. Stránky se otevřou jednou, když nahrávač startuje. Nejbezpečnější pořadí
je nejdřív spustit hru a sednout do auta; zda nahrávač spuštěný před hrou funguje, nebylo
ověřeno.

| `--game` | Stránka fyziky | Stránka grafiky (počítadlo kol) | Statická stránka (názvy) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nepoužívá se | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nepoužívá se | `Local\acevo_pmf_static` |

Stránka fyziky se čte 200krát za sekundu (`hz=200`); nový vzorek se vezme jen tehdy, když se
její `packetId` změnilo a není nulové. Prvních 800 bajtů stránky fyziky má v těchto čtyřech
hrách stejné rozložení; první hra má stránku zaručenou jen na 580 bajtů, takže když se
800bajtové mapování nedá otevřít, nahrávač přejde na 580 a pole za tím chybí.

## Poloha {#position}

Žádná stránka nenese polohu auta jako takovou, ale stránka fyziky drží **bod styku každé
pneumatiky se světem** (offset 420, čtyři trojice XYZ). Poloha auta je průměr těch čtyř.
Stránka, na které jsou všechny body styku nulové (menu, garáž), žádný vzorek nedá.

## Kanály {#channels}

| Kanál | Z čeho | Poznámky |
|---|---|---|
| `time` | vlastní hodiny nahrávače | sekundy od začátku nahrávání, přepočtené na první vzorek kola |
| `x`, `y`, `z` | průměr bodu styku pneumatik | světové metry |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | jednotky hry, škálované na kolo na -1..1 podle největší absolutní hodnoty, kterou kolo použilo, **jen pokud** ta hodnota přesáhne 1,05 (vstup už v -1..1 se nechá být) |
| `gear` | `gear - 1` | hra počítá 0 zpátečka, 1 neutrál, 2 první; zapisuje se jako -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, krát 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokální rychlost z offsetu 568 | rámec auta; jen když je nenulová. Na kterou stranu ukazuje x, je dokumentováno oběma směry, takže čtěte velikost driftového úhlu, ne jeho znaménko |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | jen stránka 800 bajtů |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offsety 204 a 252, zapsané jako 1, když je nad 0; AC: `tcInAction`/`absInAction` ze stránky 800 bajtů, je-li přítomna | asistence v činnosti |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | odvozeno | 0..1 zdvihu, který kolo použilo (min až max z `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offsety 640, 656 (stránka 800 bajtů) | děleno typickým vrcholem - viz níže |
| `slipRatioRaw.*`, `slipAngleRaw.*` | totéž | fyzikální hodnoty, neškálované |
| `padLife.*`, `discLife.*` | offsety 740, 756 | jen stránka 800 bajtů |

AC Rally posílá teploty pneumatik a brzd v kelvinech: pro `--game acrally` se od každé z
těchto hodnot nad 200 odečte 273,15.

`wheelSlip` (offset 56) se dekóduje, ale nezapisuje.

## Škálování skluzu {#slip-scaling}

Forza posílá skluz normalizovaný tak, že 1 je hrana přilnavosti. Kunos posílá fyzikální
poměr skluzu a úhel skluzu. Nahrávač je proto dělí typickým vrcholem přilnavosti na asfaltu -
**0,12** pro poměr skluzu a **0,14 rad (asi 8 stupňů)** pro úhel skluzu - aby pravidlo
„nad 1 znamená klouzání“ v prohlížeči zhruba platilo, drží surové hodnoty vedle nich a zapisuje
`"meta": {"slip": "scaled"}`. Kde přilnavost skutečně končí, prohlížeč měří pro každé auto
zvlášť z kol. Viz [Skluz, driftový úhel a odvozené kanály](slip-and-drift.md).

## Kola {#laps}

- **AC a ACC** počítají kola na stránce grafiky (`completedLaps` na offsetu 132, čas posledního
  kola v milisekundách na 144). `CounterSplitter` uzavře kolo, když se počítadlo změní; je
  označeno jako dokončené, s časem kola z hry, jen pokud počítadlo vzrostlo přesně o jedna.
- **AC EVO a AC Rally** se kvůli kolům nečtou (grafická stránka EVO má jiné, větší rozložení;
  AC Rally jezdí etapy). `LineSplitter` použije jako čáru místo, kde nahrávání začalo: kolo se
  uzavře, když auto příště projede co nejblíž k ní ve stejném směru, a etapa nebo jakákoli jízda
  se uzavře, když auto stojí 8 sekund.

Podrobnosti a prahy: [Jak se rozdělují kola a etapy](lap-splitting.md).

## Jména tratě a auta {#track-and-car-names}

Čte se jednou, ze statické stránky, když přijde první vzorek: pro AC, ACC a AC Rally auto
(UTF-16, offset 68) a trať (offset 134); pro AC EVO trať a její konfiguraci (jednobajtový text
na offsetech 136 a 169, spojené mezerou) a žádné auto. Zapíšou se do souboru jako `track` a
`car: {"name": ...}`.

## Soubor kola {#the-lap-file}

`game` je `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` nebo
`assetto-corsa-rally`; `meta` je `{"slip": "scaled", "discipline": "rally"}` pro AC Rally a
`{"slip": "scaled", "discipline": "circuit"}` pro ostatní tři. `surface` se nezapisuje.

## Zdroje {#sources}

SDK sdílené paměti AC1; dokumentace sdílené paměti ACC (v1.8); rozložení AC EVO, jak bylo
změřeno v `albertowd/live-telemetry-evo`; rozložení AC Rally, jak je čte
`LuizZak/AssettoCorsaRallyTelemetryReader`. Viz [Hry](games.md).
