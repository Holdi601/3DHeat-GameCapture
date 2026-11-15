---
title: "Prešmyk, driftový uhol a odvodené kanály"
nav_order: 8
lang: "sk"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Prešmyk, driftový uhol a odvodené kanály {#slip-drift-and-derived-channels}

Analýza jazdy na karte Analýza pretekov v prehliadači potrebuje z každej hry tie isté
veličiny: o koľko každá pneumatika prešmykuje, o koľko auto smeruje mimo smeru jazdy
(driftový uhol), či je vo vzduchu, či je na sypkom podklade. Hry ich posielajú
vo veľmi rôznych tvaroch, alebo vôbec. Nahrávače tu zapisujú to, čo každá hra posiela,
pod kanonickými menami, plus poznámku `meta.slip`, ktorá hovorí, čo znamenajú čísla
prešmyku; prehliadač potom odvodí, čo chýba, raz, keď načíta kolo. **Hodnota samotnej
hry má vždy prednosť pred odvodenou.**

## Čo zapisujú nahrávače {#what-the-recorders-write}

| Hra | Kanály prešmyku | `meta.slip` | Vstupy driftového uhla |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` pre každé koleso, ako sa posielajú | `peak` (zapíše nahrávač; čítač `.tele.gz` v prehliadači nastavuje to isté) | `latVel`, `longVel` z rýchlosti auta vo vnútornom systéme |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` z rýchlosti vo vnútornom systéme auta |
| EA SPORTS WRC, hry DiRT | žiadne; namiesto nich `wheelSurfaceSpeed` pre každé koleso | `null` | `latVel`, `longVel` = svetová rýchlosť premietnutá na osi auta |
| Richard Burns Rally | žiadne; ani rýchlosti kolies | žiadne | `latVel`, `longVel` = vlastné bočné a pozdĺžne pohyby auta |
| BeamNG.drive | žiadne; `wheelSurfaceSpeed` a `wheelSpeed` pre každé koleso | žiadne | `latVel`, `longVel` = svetová rýchlosť premietnutá na osi auta |
| Trackmania | `slipIndex` pre každé koleso (0..1 kĺzavá miera) | `index` | `latVel` (bočná rýchlosť), `longVel` (predná rýchlosť) |
| iRacing | žiadne (neloguje sa) | žiadne | `yaw` a dráha, `yawRate` |

Hodnoty `meta.slip` sú definované v [Súbor heat3d-lap](lap-format.md): `peak`
(normalizované tak, že nad 1 pneumatika stráca prilipnutie), `scaled` (fyzikálny prešmyk
delený typickým vrcholom na asfalte), `physical` (zlomok a radiány), `index` (0..1 kĺzavá miera).

### Prečo sa prešmyk Kunos škáluje {#why-kunos-slip-is-scaled}

Prešmyk Forzy je normalizovaný tak, že 1 je hrana prilipnutia; voči čomu sa normalizuje, nie je
zdokumentované. Kunos posiela fyzikálny pomer prešmyku (zlomok) a uhol prešmyku (radiány). Delením
typickým vrcholom na asfalte – 0,12 pre pomer a 0,14 rad (asi 8 stupňov) pre uhol – sa „nad 1
znamená šmyk“ približne splní pre obe rodiny, takže jedno čítanie platí pre zobrazenia prehliadača.
Je to približné: skutočné vrcholy sa líšia podľa pneumatiky a povrchu, preto sa surové hodnoty
ponechávajú vedľa škálovaných a prehliadač meria z kôl, kde prilipnutie každého auta naozaj končí.

## Čo odvodzuje prehliadač (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Tieto kroky bežia v prehliadači (`src/race/derive.ts` v prehliadači 3DHeat), nie v tomto repozitári.

### Driftový uhol, `bodySlip` {#drift-angle-bodyslip}

- **Z rýchlosti vo vnútornom systéme auta**, keď sú prítomné `latVel` a `longVel`:
  `atan2(latVel, |longVel|)`, a 0 pod 3 m/s (auto stojace bokom nedriftuje).
  Jeho znamienko nasleduje bočnú rýchlosť hry, ktorej zmysel je pri niektorých hrách
  zdokumentovaný v oboch smeroch – spoľahnite sa na veľkosť.
- **Inak zo smeru oproti dráhe**: smer jazdy sa berie z polôh zhruba 2 m pred a za každou
  vzorkou (`atan2(dx, dz)`); `yaw` hry sa prifituje k nemu so znamienkom a posunom (každá hra
  má vlastný nulový bod a zmysel otáčania) pomocou vzoriek nad 10 m/s a dôveruje sa mu len vtedy,
  ak potom výborne súhlasí (kruhový rozptyl najviac 0,05, aspoň 20 vzoriek). Driftový uhol je
  rozdiel, 0 pod 3 m/s.

### Pomer prešmyku z kolies {#slip-ratio-from-the-wheels}

Ak kolo nemá `slipRatio.*`, ale má rýchlosti kolies, pomer prešmyku je
`(koleso - auto) / auto` pre každé koleso, z:

- `wheelSurfaceSpeed.*` (rýchlosť kontaktnej plochy, m/s) priamo, ak sa posiela (EA WRC, DiRT,
  BeamNG);
- inak `wheelSpeed.*` (otáčanie, rad/s) krát **valivý polomer nameraný na samotnom kole**: medián
  z `speed / |omega|` na vzorkách, kde auto dobieha rovno (nad 10 m/s, nie vo vzduchu, plyn pod 0,3,
  brzda pod 0,05, pozdĺžne zrýchlenie pod 3 m/s²); pri menej ako 20 takých vzorkách každá vzorka nad
  10 m/s. Polomer mimo 0,1–1 m sa zamietne.

Len keď sa dajú odvodiť všetky štyri kolesá; `meta.slip` kola sa potom zmení na `physical`. Pod
3 m/s je prešmyk 0.

### Vo vzduchu {#airborne}

`airborne` je 1 tam, kde sú všetky kolesá mimo zeme, posudzované podľa prvého z týchto, ktoré
kolo má pre všetky štyri kolesá:

1. `groundContact.*` (BeamNG): žiadne koleso nad 0,5;
2. `wheelLoad.*` (hry AC, RBR, BeamNG): žiadne koleso nad 5 % svojho mediánu zaťaženia;
3. `suspension.*` (0..1 zdvihu): žiadne koleso nad 0,02, t. j. všetky úplne vysunuté.

Jediná izolovaná vzorka vo vzduchu sa vymaže. Trackmania zapisuje `airborne` sama.

### Sypký podklad {#loose-ground}

Ak kolo má `surfaceRumble.*` (Forza), `loose` je 1 tam, kde aspoň dve kolesá hlásia vibrácie
aspoň tri desatiny sekundy, s medzerami kratšími ako jedna sekunda premostenými (hladká časť na
štrkovej ceste je stále štrková cesta). Trackmania zapisuje `loose` sama z materiálov povrchu
kolies.

### Rýchlosť zatáčania {#yaw-rate}

Ak kolo má `yaw`, ale nie `yawRate`, je to zmena yaw medzi susednými vzorkami.

## Čo nahrávače odvodzujú samy {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): každý nahrávač okrem Forzy (ktorá ho posiela) ho zapíše z
  `suspensionM.*` ako polohu v rozsahu, ktorý toto kolo použilo (minimum až maximum). Slúži na
  stĺpiky zavesenia auta a na odhalenie kolesa visiaceho vo vzduchu; nie je to absolútny zlomok zdvihu.
- **`steer`** pre hry Kunos, škálované pre každé kolo (pozrite [Hry Assetto Corsa](telemetry-assetto-corsa.md)).
- **Zrýchlenia** pre BeamNG, zo zmeny svetovej rýchlosti ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** a os hore pre Richard Burns Rally, z polôh ([Rallye hry](telemetry-rally.md)).

## Orientácia {#handedness}

Ak má svet hry ľavoruký systém – ako Forza – trať sa v pravoručnom prehliadači zrkadlí; to
prezradia vlastné riadenie a zavesenie kôl. Nahrávače nemenia orientáciu: svet s osou Z hore
(BeamNG) sa otočí na os Y hore, čo orientáciu zachová, a všetko ostatné sa zapisuje tak, ako
je poslané.
