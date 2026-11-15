---
title: "Assetto Corsa -pelit"
nav_order: 2
lang: "fi"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO ja AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Koodi: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testit: `tests/test_kunos.py` (synteettiset sivut). Ei vielä ajettu oikeita pelejä vastaan.

## Mistä data tulee {#where-the-data-comes-from}

Kunosin pelit julkaisevat telemetrian sovelluksille **nimettyinä Windowsin jaettuina muistisivuina**, jotka peli
kirjoittaa ja joita kuka tahansa voi lukea. Tallennin avaa ne vain luku -tilassa (`mmap` tunnisteen kanssa), joten sen
täytyy ajaa **sillä koneella, jolla peli on käynnissä**, Windowsissa; muualla se lopettaa viestillä.
Sivut avataan kerran, kun tallennin käynnistyy. Pelin käynnistäminen ja autoon meneminen ensin on turvallinen järjestys;
sitä, toimiiko tallentimen käynnistäminen ennen peliä, ei ole tarkistettu.

| `--game` | Fysiikkasivu | Grafiikkasivu (kierroslaskuri) | Staattinen sivu (nimet) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ei käytössä | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ei käytössä | `Local\acevo_pmf_static` |

Fysiikkasivua luetaan 200 kertaa sekunnissa (`hz=200`); uusi näyte otetaan vain, kun sen `packetId` on muuttunut ja
ei ole nolla. Fysiikkasivun ensimmäiset 800 tavua ovat samassa asettelussa kaikissa neljässä pelissä; ensimmäisen pelin
sivu on taattu vain 580 tavun pituinen, joten jos 800 tavun kartoitusta ei voi avata, tallennin palaa 580 tavuun ja
sitä pidemmät kentät puuttuvat.

## Sijainti {#position}

Mikään sivu ei kanna auton sijaintia suoraan, mutta fysiikkasivu kantaa **kunkin renkaan kosketuspisteen maailmakoordinaateissa**
(offset 420, neljä XYZ-kolmikkoa). Auton sijainti on näiden neljän keskiarvo. Sivu, jolla kaikki kosketuspisteet ovat nollia
(valikko, talli), ei tuota näytettä.

## Kanavat {#channels}

| Kanava | Lähde | Huomautus |
|---|---|---|
| `time` | tallentimen oma kello | sekunteja tallennuksen alusta, siirrettynä kierroksen ensimmäisestä näytteestä |
| `x`, `y`, `z` | renkaiden kosketuspisteiden keskiarvo | maailman metrejä |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | pelin yksiköt, skaalattu kierroskohtaisesti -1..1:een suurimman itseisarvon mukaan, jonka kierros käytti, **vain jos** se arvo ylittää 1,05 (sisääntulo, joka on jo välillä -1..1, jätetään rauhaan) |
| `gear` | `gear - 1` | peli laskee 0 = peruutus, 1 = vapaa, 2 = ensimmäinen; kirjoitetaan -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, kerrottuna 9,80665:llä | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | paikallinen nopeus offsetista 568 | auton kehys; vain kun ei nolla. Mihin puolelle x osoittaa, on dokumentoitu molempiin suuntiin, joten lue sivuliukukulman suuruus, ei sen merkkiä |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | vain 800 tavun sivu |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offsetit 204 ja 252, kirjoitetaan 1:ksi, kun arvo on yli 0; AC: `tcInAction`/`absInAction` 800 tavun sivulta, kun se on läsnä | avustusjärjestelmä toiminnassa |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | johdettu | 0..1 tästä kierroksesta käytetystä matkasta (`suspensionM`:n pienin ja suurin) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offsetit 640, 656 (800 tavun sivu) | jaettuna tyypillisellä huipulla - katso alla |
| `slipRatioRaw.*`, `slipAngleRaw.*` | samat | fyysiset arvot, skaalaamattomina |
| `padLife.*`, `discLife.*` | offsetit 740, 756 | vain 800 tavun sivu |

AC Rally lähettää renkaidensa ja jarrujensa lämpötilat kelvineinä: `--game acrally`-tilassa kaikista näistä arvoista,
jotka ovat yli 200, vähennetään 273,15.

`wheelSlip` (offset 56) dekoodataan, mutta sitä ei kirjoiteta.

## Luiston skaalaus {#slip-scaling}

Forza lähettää luiston normalisoituna niin, että 1 on pidon reuna. Kunos lähettää fyysisen luistosuhteen ja
sivuliukukulman. Siksi tallennin jakaa ne tyypillisellä asfaltin huipulla - **0,12** luistosuhteelle ja
**0,14 rad (noin 8 astetta)** kulmalle - jotta katselimen "yli 1 tarkoittaa liukumista" pitää suunnilleen,
säilyttää raakat arvot niiden rinnalla ja kirjoittaa `"meta": {"slip": "scaled"}`. Missä pito todella päättyy,
katselin mittaa autokohtaisesti kierroksista. Katso [Luisto, sivuliuku ja johdetut kanavat](slip-and-drift.md).

## Kierrokset {#laps}

- **AC ja ACC** laskevat kierrokset grafiikkasivulta (`completedLaps` offsetissa 132, viimeisen kierroksen aika
  millisekunteina offsetissa 144). `CounterSplitter` sulkee kierroksen, kun laskuri muuttuu; se merkitään päätetyksi,
  pelin kierrosajalla, vain jos laskuri nousi täsmälleen yhdellä.
- **AC EVO ja AC Rally** eivät lue kierroksia (EVO:n grafiikkasivu on eri, suurempi asettelu; AC Rally ajaa osuuksia).
  `LineSplitter` käyttää pistettä, josta tallennus alkoi, linjana: kierros sulkeutuu, kun auto seuraavan kerran ohittaa
  linjan lähimpänä samaan suuntaan, ja osuus tai mikä tahansa ajo sulkeutuu, kun auto seisoo paikallaan 8 sekuntia.

Yksityiskohdat ja rajat: [Kierrosten ja osuuksien jakaminen](lap-splitting.md).

## Radan ja auton nimet {#track-and-car-names}

Luetaan kerran staattiselta sivulta, kun ensimmäinen näyte saapuu: AC:lle, ACC:lle ja AC Rallille auto (UTF-16,
offset 68) ja rata (offset 134); AC EVO:lle rata ja sen konfiguraatio (yksitavuinen teksti offseteissa 136 ja 169,
yhdistettynä välilyönnillä) eikä autoa. Ne menevät tiedostoon `track`- ja `car: {"name": ...}`-kenttinä.

## Kierrostiedosto {#the-lap-file}

`game` on `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` tai `assetto-corsa-rally`; `meta` on
`{"slip": "scaled", "discipline": "rally"}` AC Rallille ja `{"slip": "scaled", "discipline": "circuit"}` muille kolmelle.
`surface` ei kirjoiteta.

## Lähteet {#sources}

AC1:n jaetun muistin SDK; ACC:n jaetun muistin dokumentaatio (v1.8); AC EVO:n asettelu mitattuna
`albertowd/live-telemetry-evo`-projektissa; AC Rallin asettelu, jonka lukee `LuizZak/AssettoCorsaRallyTelemetryReader`.
Katso [Pelit](games.md).
