---
title: iRacing
nav_order: 6
lang: "fi"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing ei tarvitse **tallenninta**. Simulaattori kirjoittaa omat telemetriatiedostonsa, `.ibt`-tiedostot, kun telemetrian tallennus on päällä (Alt+L autossa). Tiedostoon tulee koko sessio 60 Hz:llä, jokainen kanava, jonka simulaattori tarjoaa, ja session YAML-kuvaus vieressä. Pudota `.ibt`-tiedosto katselimen **Kisa-analyysi**-välilehdelle.

Lukija on katselimessa, ei tässä repositoriossa (`src/race/ibt.ts` 3DHeat-katselimessa). Sitä testataan synteettisellä tiedostolla. Se on dokumentoitu tässä, koska se on iRacingin puoli samasta kierrostallennustarinasta.

## Mitä tiedosto sisältää ja miten se luetaan {#what-the-file-holds-and-how-it-is-read}

Tiedosto on simulaattorin dokumentoitu muistirakenne kirjoitettuna levylle:

| Osa | Koko | Sisältää |
|---|---|---|
| Otsikko | 112 tavua | versio, tikkitaajuus, missä YAML ja muuttujataulukko ovat, yhden näytteen rivin pituus, mistä rivit alkavat |
| Levyn alaotsikko | 32 tavua | aloituspäivä ja -aika, kierrosmäärä, rivimäärä |
| Muuttujataulukko | 144 tavua per kanava | tyyppi, siirtymä rivissä, määrä, nimi, kuvaus, yksikkö |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rivit | yksi per tikki | |

Tiedosto hylätään, jos se on lyhyempi kuin 144 tavua. Se hylätään myös, jos sen otsikko ei ole järkevä: muuttujia ei ole, muuttujataulukko on tiedoston ulkopuolella tai rivin pituus on nolla. Lisäksi se hylätään, jos siitä puuttuu jokin kentistä `SessionTime`, `Lap`, `Lat` tai `Lon`, tai jos yhdelläkään näytteellä ei ole sijaintikiinnitystä.

## Sijainti {#position}

iRacing raportoi leveysasteen, pituusasteen ja korkeuden. Se ei raportoi sijaintia radan omassa koordinaatistossa. Sijainnit asetetaan metreinä tasoon, joka sivuaa ensimmäistä näytettä, jolla on sijaintikiinnitys (Maan säde 6,371,008.8 m): `x` itään, `z` etelään, `y` korkeus. Näin ylhäältä katsottuna, katselimen kameran oletussuunnalla, pohjoinen on ruudun ylhäällä.

## Kierrokset {#laps}

Sessio jaetaan simulaattorin `Lap`-laskurin mukaan. Kierros säilytetään vain, jos siinä on yli 60 näytettä, se alkaa alle 5 %:sta kierrosmatkasta (`LapDistPct`) ja päättyy yli 95 %:iin. Eli kierrokset, jotka on ajettu linjalta linjalle. Jos mikään kierros ei täytä ehtoja, tiedosto hylätään viestillä, joka nimeää radan pituuden YAML:sta. `distance` on `LapDist` siirrettynä kierroksen alkuun. Jos `LapDist` puuttuu, se on ajettu matka sijainneista. `time` on `SessionTime` kierroksen alusta.

## Kanavat {#channels}

| iRacing | Kanava | Muunnos |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | ei muunnosta |
| `Clutch` | `clutch` | `1 - value` (iRacing pitää kytkintä kytkettynä; kanava on polkimen asento) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radiaaneina, vastapäivään positiivinen, muutettuna väliltä -1..1 niin, että oikealle on positiivinen; pi, kun maksimi puuttuu) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | ei muunnosta |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | ei muunnosta |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | avustinasetukset |
| `dcBrakeBias` | `brakeBias` | jaetaan 100:lla, kun arvo on yli 1.5 (joissakin autoissa prosentteina) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | ei muunnosta |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | renkaan rungon lämpötila keskeltä |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa kerrottuna 0.145038:lla, psi-yksiköksi |
| `..wearM` | `tireWear.*` | `1 - value` |

Jokainen muu kanava, jossa on yksi arvo näytettä kohden (eikä yksi tavu), kulkee läpi omalla nimellään. Pyöräetuliite (`LF`, `RF`, `LR`, `RR`) muuttuu päätteeksi (`.FL`, `.FR`, `.RL`, `.RR`). Siksi katselimen kuvaajat tarjoavat sen ilman, että kukaan kuvailee sitä.

Auto tulee kohdasta `DriverInfo`. Merkintä, jonka `CarIdx` vastaa `DriverCarIdx`-arvoa, antaa `CarScreenName`, `CarID` ja `CarClassShortName`. Rata on `TrackDisplayName` (tai `TrackName`).

## Mitä iRacing ei anna {#what-iracing-does-not-give}

Renkaiden luistoa ei kirjata, joten luistokanavia ei ole. Ajautumiskulma johdetaan kääntymisnopeudesta suhteessa polkuun (katso [Luisto, ajautuminen ja johdetut kanavat](slip-and-drift.md)). Ratamallit toimitetaan suojatussa muodossa, eikä niitä haeta purkamalla tiedostoista (katso [Pelit](games.md)).
