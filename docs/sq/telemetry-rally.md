---
title: "Lojërat e ralit"
nav_order: 3
lang: "sq"
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

Kodi: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testet: `tests/test_rally.py`, në paketa të ndërtuara sipas strukturave të dokumentuara. **Ende të pa ekzekutuara
kundrejt lojërave të vërteta.**

Të gjitha dërgojnë UDP që loja e ndez nga skedarët e vet të cilësimeve. Regjistruesi
dëgjon në të gjitha ndërfaqet (`0.0.0.0`) në portën e paracaktuar të lojës përveç nëse `--port` jep
një tjetër: **20777** për `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** për `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Ndezja {#switching-it-on}

Loja lexon `Documents\My Games\WRC\telemetry\config.json`. Paketa `session_update` e strukturës
standarde `wrc` duhet të aktivizohet drejt kësaj makine:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funksioni `configure_wrc`):

- lexon JSON, gjen `udp.packets` dhe hyrjen me `"structure": "wrc"` dhe
  `"packet": "session_update"`;
- nëse është aktivizuar tashmë drejt `127.0.0.1` ose `localhost` në portën që përdoret, printon
  `already on` dhe nuk ndryshon asgjë;
- përndryshe vendos `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, dhe e mban
  `frequencyHz` të hyrjes (ose `-1` nëse nuk ka); nëse nuk ka një hyrje të tillë, shton një;
- shkruan tekstin origjinal te `config.json.bak` pranë tij, pastaj shkruan skedarin e ri
  (me 4 hapësira zhvendosje).

Rinise lojën pasi ndryshon skedarin nëse nuk e merr ndryshimin (nuk është kontrolluar).

### Çfarë dërgon {#what-it-sends}

Struktura standarde `wrc` është 237 bajte, little-endian, pa kokë: pozicioni botëror,
shpejtësia dhe nxitimi (X majtas, Y lart, Z përpara), vektorët njësi majtas / përpara / lart të makinës,
për çdo rrotë (e pasme-majtë, e pasme-djathtë, e përparme-majtë, e përparme-djathtë) lartësia e qendrës së rrotës dhe
shpejtësia vertikale dhe shpejtësia përpara e njollës së kontaktit, temperaturat e frenave, pedalet pas
ndihmave, drejtimi (-1 majtas, +1 djathtas), frena me dorë, rpm, marshi, dhe ora e etapës, largësia dhe
gjatësia. Një paketë më e shkurtër se 237 bajte shpërfillet dhe raportohet një herë.

| Kanali | Nga |
|---|---|
| `x`, `y`, `z` | pozicioni botëror |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | shpejtësia botërore e projektuar mbi përpara, mbi minus majtas (kështu që pozitive është djathtas), mbi lart |
| `longAcc`, `latAcc`, `vertAcc` | nxitimi botëror i projektuar njësoj |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | siç dërgohen |
| `gear` | `gear_index`; -1 kur është e barabartë me indeksin e mbrapsht, 0 kur është e barabartë me indeksin e neutrales |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | pozicioni i qendrës së rrotës |
| `wheelSurfaceSpeed.*` | shpejtësia përpara e njollës së kontaktit |
| `brakeTemp.*` | temperatura e frenave |

Kontroll: nëse `speed` është mbi 10 dhe gjatësia e shpejtësisë botërore ndryshon prej saj me më shumë se
20%, regjistruesi printon një herë se struktura mund të mos jetë ajo standarde `wrc`.

Një etapë **mbaron** kur gjatësia e etapës është pozitive dhe largësia ka arritur
gjatësinë minus 0.5 m. Ora e përdorur për ndarje dhe për `time` është `stage_time`.

Burimet: UDP Telemetry Guide v1.3 i EA; lista e kanaleve që loja shkruan te
`readme/channels.json`; zhvendosjet siç dekodohen nga nobonobo/obs-codemasters-telemetry dhe
SpaceMonkey. Porta standarde e fabrikës nuk është e dokumentuar; regjistruesi përdor 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Ndezja {#switching-it-on-1}

Ndrysho `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally dhe DiRT 4 përdorin gjithashtu një `hardware_settings_config.xml`; dosja e saktë e tij për ato dy
nuk është kontrolluar këtu) që elementi `udp` të lexohet:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` është ajo që fut pozicionet, rrotat dhe gjatësinë e etapës në paketë. Regjistruesi
nuk e ndryshon këtë skedar.

### Çfarë dërgon {#what-it-sends-1}

66 float-e little-endian (DiRT Rally: 64); paketat më të shkurtra se 64 float-e shpërfillen dhe një
paketë 64-float-she mbushet me zero. Indekset e përdorura:

| Indeksi | Fusha | Kanali |
|---|---|---|
| 1 | koha e xhiros (etapës) | ora e ndarjes dhe `time` |
| 2 | largësia e xhiros | `stageDistance` |
| 4-6 | pozicioni botëror | `x`, `y`, `z` |
| 7 | shpejtësia | `speed` |
| 8-10 | shpejtësia botërore | `longVel` (mbi përpara), `latVel` (mbi vektorin anësor) |
| 11-13 | vektori anësor | |
| 14-16 | vektori përpara | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | pozicioni i pezullimit RL RR FL FR | `suspensionM.*` |
| 25-28 | shpejtësia e njollës së rrotës RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gazi, drejtimi, frena, friksioni, marshi | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ose më shumë do të thotë mbrapsht, shkruhet si -1) |
| 34, 35 | g anësore, gjatësore | `latAcc`, `longAcc` (herë 9.80665) |
| 37 | rpm / 10 | `rpm` (herë 10) |
| 51-54 | temperaturat e frenave | `brakeTemp.*` |
| 59, 60, 61, 62 | xhirot e përfunduara, xhirot gjithsej, gjatësia e pistës, koha e xhiros së fundit | ndarja |

**Nuk ka kanal të frenës me dorë.** Kuptimi i vektorit anësor dokumentohet në të dyja mënyrat, prandaj
shenja e `latVel` nuk duhet mbështetur (shikuesi e lexon madhësinë e këndit të drift-it).

Një etapë **mbaron** kur numri i xhirove të përfunduara ngrihet mbi vlerën e tij në fillim të
etapës (një xhiro rallycross çdo herë që ndodh), ose, për një ngjarje me një xhiro, kur largësia e xhiros
arrin 99.9% të gjatësisë së pistës. Koha e etapës është koha e xhiros së fundit e lojës kur
është pozitive. Kontroll: shpejtësia krahasuar me `speed` si për EA WRC, me mesazhin "is extradata set
to 3?".

Burimet: dokumenti UDP i DiRT 4 nga Codemasters; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Ndezja {#switching-it-on-2}

Te `RichardBurnsRally.ini`, seksioni `[NGP]`: `udpTelemetry=1` dhe pika e fundit (127.0.0.1,
porta 6776 përveç nëse jep një `--port` tjetër). Regjistruesi nuk e ndryshon këtë skedar.

### Çfarë dërgon {#what-it-sends-2}

664 bajte (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): ora e etapës dhe largësia
deri në fund, pedalet, drejtimi, marshi, pozicioni botëror, qëndrimi, shpejtësitë e vetë makinës
(surge përpara, sway anash, heave), nxitimet, rpm, dhe katër blloqe rrotash 128-bajtëshe
(LF, RF, LB, RB) me devijimin e sustës dhe forcën e sustës. Pa shpejtësi rrotash.

| Kanali | Nga |
|---|---|
| `x`, `y`, `z` | pozicioni, akset siç dërgohen, pastaj rirenditur (më poshtë) |
| `longVel`, `latVel`, `vertVel` | surge, sway, heave |
| `longAcc`, `latAcc` | nxitimi x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | siç dërgohen |
| `gear` | `gear - 1` (0 mbrapsht, 1 neutral, 2 e para) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | devijimi i sustës |
| `wheelLoad.*` | forca e sustës |
| `speed` | **llogaritur nga pozicionet** mbi +-2 kampionë, jo marrë nga paketa |

Akset e pozicionit, njësitë e qëndrimit dhe njësia e shpejtësisë së RBR nuk janë të dokumentuara, prandaj kur një etapë
shkruhet: aksi përgjatë të cilit etapa ndryshon më pak merret si lart dhe këmbehet në `y`
(`orient_up`, ka nevojë për të paktën 10 kampionë), dhe shpejtësia rillogaritet nga pozicionet
(`speed_from_positions`). Qëndrimi dekodohet por nuk shkruhet, kështu që skedarët RBR nuk kanë `yaw`.

Një etapë **mbaron** kur ora e garës po vrapon dhe largësia deri në fund ka
arritur zero. Ora është `race_time`.

Burimet: `rbr.telemetry.data.TelemetryData.h` i NGP nëpërmjet mika-n/RBRUDPTelemetryLogger dhe
groybe/rbr-udp-telem.

## Etapat {#stages}

Të pesë përdorin `StageSplitter` mbi orën e etapës të lojës: një etapë hapet kur nis ora,
mbyllet e plotë kur loja thotë se makina mbaroi, dhe një orë që shkon mbrapa (një rinisje,
ose etapa tjetër) braktis etapën e hapur - e mbajtur si skedar `_partial` nëse ka më shumë se 10
kampionë dhe të paktën 300 m. Etapat e përfunduara më të shkurtra se 300 m nuk shkruhen. Detajet:
[Ndarja e xhirove dhe e etapave](lap-splitting.md).

## Skedari i xhiros {#the-lap-file}

`game` është `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ose `richard-burns-rally`.
`meta` është `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"` kur `--surface`
është dhënë. `slip` është null sepse asnjë nga këto lojëra nuk dërgon rrëshqitjen e gomave. Në vend të saj në skedar është shpejtësia e njollës së kontaktit
të çdo rrote (EA WRC, DiRT), dhe shikuesi nxjerr rrëshqitjen dhe këndin e drift-it nga ajo
dhe aksi i makinës; shih [Rrëshqitja, drift-i dhe kanalet e nxjerra](slip-and-drift.md). Kanalet
`suspension.*` (0..1 e udhëtimit të përdorur) shtohen nga `suspensionM.*`.

Kur nuk jepet `--surface` skedari nuk mban fare sipërfaqe, qëllimisht: një vlerë e paracaktuar e shkruar
këtu do ta mbishkruante përfundimin e vetë shikuesit. Shikuesi e merr atëherë sipërfaqen nga emri i
etapës ose i ngjarjes (ralitë në asfalt, ato dimërore, Monte si e përzier), përndryshe nga mënyra si u vozit
makina mbi të (kthesat e forta me kënde të vogla drift-i janë asfalt), dhe të lirshme kur asgjë nuk tregon
- çka është një etapë rali më shpesh. Jep `--surface` kur e di më mirë.
