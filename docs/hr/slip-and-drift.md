---
title: "Klizanje, drift i izvedeni kanali"
nav_order: 8
lang: "hr"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Klizanje, drift i izvedeni kanali {#slip-drift-and-derived-channels}

Analiza upravljanja automobilom u kartici Analiza utrke preglednika treba iste nekoliko
veličina iz svake igre: koliko svaka guma klizi, koliko automobil pokazuje dalje od smjera
kojim ide (kut drifta), je li u zraku, je li na rastresitom tlu. Igre to šalju u vrlo
različitim oblicima ili uopće ne šalju. Snimači ovdje zapisuju ono što pojedina igra šalje,
pod kanonskim nazivima, plus napomenu `meta.slip` koja kaže što znače brojevi klizanja;
preglednik zatim izvodi ono što nedostaje, jednom, kad učita krug. **Vrijednost same igre
uvijek pobjeđuje izvedenu.**

## Što snimači zapisuju {#what-the-recorders-write}

| Igra | Kanali klizanja | `meta.slip` | Ulazi za kut drifta |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` po kotaču, kako je poslano | `peak` (zapisuje snimač; čitač `.tele.gz` u pregledniku postavlja isto) | `latVel`, `longVel` iz brzine vozila u okviru automobila |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` iz brzine u okviru automobila |
| EA SPORTS WRC, igre DiRT | nema; umjesto toga `wheelSurfaceSpeed` po kotaču | `null` | `latVel`, `longVel` = brzina svijeta projicirana na osi automobila |
| Richard Burns Rally | nema; nema ni brzina kotača | nema | `latVel`, `longVel` = vlastito njihanje i uzdužna brzina automobila |
| BeamNG.drive | nema; `wheelSurfaceSpeed` i `wheelSpeed` po kotaču | nema | `latVel`, `longVel` = brzina svijeta projicirana na osi automobila |
| Trackmania | `slipIndex` po kotaču (mjera klizanja od 0 do 1) | `index` | `latVel` (bočna brzina), `longVel` (brzina naprijed) |
| iRacing | nema (nije zabilježeno) | nema | `yaw` i putanja, `yawRate` |

Vrijednosti `meta.slip` definirane su u [Datoteka `heat3d-lap`](lap-format.md): `peak`
(normalizirano, pa iznad 1 guma popušta), `scaled` (fizičko klizanje podijeljeno s tipičnim
vrhom na asfaltu), `physical` (udio i radijani), `index` (mjera klizanja od 0 do 1).

### Zašto se klizanje Kunosovih igara skalira {#why-kunos-slip-is-scaled}

Forzino klizanje normalizirano je tako da je 1 rub prianjanja; prema čemu normalizira nije
dokumentirano. Kunos šalje fizički omjer klizanja (udio) i kut klizanja (radijani). Dijeljenje
s tipičnim vrhom na asfaltu - 0,12 za omjer, 0,14 rad (oko 8 stupnjeva) za kut - čini da
„iznad 1 znači klizanje” približno vrijedi za obje obitelji, pa jedno čitanje ostaje za
prikaze u preglednicima. To je aproksimacija: pravi vrhovi variraju po gumi i podlozi, zato
se sirove vrijednosti čuvaju uz skalirane, a preglednik mjeri iz samih krugova gdje se
prianjanje svakog automobila stvarno gubi.

## Što preglednik izvodi (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Ovo se izvršava u pregledniku (`src/race/derive.ts` u 3DHeat pregledniku), ne u ovom repozitoriju.

### Kut drifta, `bodySlip` {#drift-angle-bodyslip}

- **Iz brzine u okviru automobila** kad su prisutni `latVel` i `longVel`:
  `atan2(latVel, |longVel|)`, a 0 ispod 3 m/s (automobil koji stoji postrance ne driftira).
  Predznak prati bočnu brzinu igre, čiji je smjer za neke igre dokumentiran u oba smjera -
  čitajte veličinu.
- **Inače iz smjera naspram putanje**: smjer vožnje uzima se iz položaja otprilike 2 m s obje
  strane svakog uzorka (`atan2(dx, dz)`); `yaw` igre prilagođava mu se s predznakom i
  pomakom (svaka igra ima vlastitu nulu i smjer rotacije) koristeći uzorke iznad 10 m/s, i
  vjeruje mu se samo ako se tada dobro slaže (kružno odstupanje najviše 0,05, najmanje 20
  uzoraka). Kut drifta je razlika, 0 ispod 3 m/s.

### Omjer klizanja iz kotača {#slip-ratio-from-the-wheels}

Ako krug nema `slipRatio.*`, ali ima brzine kotača, omjer klizanja je
`(wheel - car) / car` po kotaču, iz:

- `wheelSurfaceSpeed.*` (brzina dodirne površine, m/s) izravno, kad je poslana (EA WRC,
  DiRT, BeamNG);
- inače `wheelSpeed.*` (okretanje, rad/s) puta **polumjer kotrljanja izmjeren na samom krugu**:
  medijan `speed / |omega|` na uzorcima gdje automobil ide bez gasa u ravnoj liniji (iznad 10
  m/s, nije u zraku, gas ispod 0,3, kočnica ispod 0,05, uzdužno ubrzanje ispod 3 m/s²); s manje
  od 20 takvih uzoraka, svaki uzorak iznad 10 m/s. Polumjer izvan 0,1-1 m se odbacuje.

Samo kad se sva četiri kotača mogu izvesti; `meta.slip` kruga tada postaje `physical`. Ispod
3 m/s klizanje je 0.

### U zraku {#airborne}

`airborne` je 1 kad je svaki kotač bez dodira s tlom, a procjenjuje se prvim od ovih koje
krug ima za sva četiri kotača:

1. `groundContact.*` (BeamNG): nijedan kotač iznad 0,5;
2. `wheelLoad.*` (igre AC, RBR, BeamNG): nijedan kotač iznad 5 % vlastitog medijanskog
   opterećenja;
3. `suspension.*` (0..1 puta): nijedan kotač iznad 0,02, tj. svi potpuno ispruženi.

Jedan izolirani uzorak u zraku se briše. Trackmania sama piše `airborne`.

### Rastresito tlo {#loose-ground}

Ako krug ima `surfaceRumble.*` (Forza), `loose` je 1 tamo gdje najmanje dva kotača javljaju
vibriranje najmanje trećinu sekunde, s prekidima kraćim od jedne sekunde premoštenim (glatka
dionica na šljunčanoj cesti i dalje je šljunčana cesta). Trackmania sama piše `loose` iz
materijala podloge kotača.

### Brzina skretanja {#yaw-rate}

Ako krug ima `yaw`, ali nema `yawRate`, to je promjena `yaw` na susjednim uzorcima.

## Što snimači sami izvode {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): svaki snimač osim Forze (koja ga šalje) piše ga iz
  `suspensionM.*` kao položaj unutar raspona koji je krug koristio (najmanji do najveći).
  Služi za trake ovjesa u automobilu i za otkrivanje kotača koji visi u zraku; nije apsolutni
  udio puta.
- **`steer`** za Kunosove igre, skaliran po krugu (vidi
  [Assetto Corsa igre](telemetry-assetto-corsa.md)).
- **Ubrzanja** za BeamNG, iz promjene brzine svijeta ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** i os gore za Richard Burns Rally, iz položaja ([Vozačke igre](telemetry-rally.md)).

## Orijentacija {#handedness}

Tamo gdje je svijet igre lijevo orijentiran - Forzin jest - staza se u desno orijentiranom
pregledniku ispisuje zrcaljeno; vlastito upravljanje i ovjes krugova to odaju. Snimači ne
mijenjaju orijentaciju: svijet okrenut prema Z gore (BeamNG) pretvara se u Y gore rotacijom,
što orijentaciju čuva, a sve ostalo se zapisuje kako je poslano.
