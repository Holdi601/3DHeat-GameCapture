---
title: "Skluz, driftový úhel a odvozené kanály"
nav_order: 8
lang: "cs"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Skluz, driftový úhel a odvozené kanály {#slip-drift-and-derived-channels}

Analýza řízení auta v kartě Analýza závodu prohlížeče potřebuje od každé hry
stejných pár veličin: jak moc každá pneumatika klouže, jak moc auto ukazuje jinam, než kam
jede (driftový úhel), zda je ve vzduchu, zda je na volném povrchu. Hry je posílají ve velmi
různých tvarech, nebo vůbec. Nahrávače tady zapisují, co každá hra posílá, pod kanonickými
názvy, plus poznámku `meta.slip`, která říká, co čísla skluzu znamenají; prohlížeč pak
dopočítá, co chybí, jednou, když načítá kolo. **Vlastní hodnota hry má vždy přednost před
odvozenou.**

## Co nahrávače zapisují {#what-the-recorders-write}

| Hra | Kanály skluzu | `meta.slip` | Vstupy driftového úhlu |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` na kolo, jak byly poslány | `peak` (zapisuje nahrávač; čtečka `.tele.gz` v prohlížeči nastavuje totéž) | `latVel`, `longVel` z rychlosti v lokálním rámu auta |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` z rychlosti v rámu auta |
| EA SPORTS WRC, hry DiRT | žádné; místo toho `wheelSurfaceSpeed` na kolo | `null` | `latVel`, `longVel` = světová rychlost promítnutá na osy auta |
| Richard Burns Rally | žádné; ani rychlosti kol | žádné | `latVel`, `longVel` = vlastní boční a podélný pohyb auta |
| BeamNG.drive | žádné; `wheelSurfaceSpeed` a `wheelSpeed` na kolo | žádné | `latVel`, `longVel` = světová rychlost promítnutá na osy auta |
| Trackmania | `slipIndex` na kolo (měřítko skluzu 0..1) | `index` | `latVel` (boční rychlost), `longVel` (přední rychlost) |
| iRacing | žádné (nezaznamenává se) | žádné | `yaw` a dráha, `yawRate` |

Hodnoty `meta.slip` jsou definované v [Soubor heat3d-lap](lap-format.md): `peak`
(normalizovaný, takže nad 1 pneumatika ztrácí přilnavost), `scaled` (fyzikální skluz
dělený typickým vrcholem přilnavosti na asfaltu), `physical` (zlomek a radiány), `index`
(měřítko skluzu 0..1).

### Proč se skluz Kunos škáluje {#why-kunos-slip-is-scaled}

Skluz Forzy je normalizovaný tak, že 1 je hrana přilnavosti; vůči čemu normalizuje, není
zdokumentováno. Kunos posílá fyzikální poměr skluzu (zlomek) a úhel skluzu (radiány).
Dělení typickým vrcholem přilnavosti na asfaltu - 0,12 pro poměr a 0,14 rad (asi 8 stupňů)
pro úhel - udělá z tvrzení „nad 1 znamená klouzání“ přibližně pravdu pro obě rodiny, což
drží jedno čtení pro zobrazení prohlížeče. Je to přibližné: skutečné vrcholy se liší podle
pneumatiky a povrchu, proto se surové hodnoty drží vedle škálovaných a proto prohlížeč
měří z kol samotných, kde přilnavost každého auta skutečně mizí.

## Co prohlížeč odvozuje (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Tyto běží v prohlížeči (`src/race/derive.ts` v prohlížeči 3DHeat), ne v tomto repozitáři.

### Driftový úhel, `bodySlip` {#drift-angle-bodyslip}

- **Z rychlosti v rámu auta**, když jsou přítomné `latVel` a `longVel`:
  `atan2(latVel, |longVel|)`, a 0 pod 3 m/s (auto stojící bokem nedriftuje).
  Jeho znaménko sleduje boční rychlost hry, jejíž smysl je u některých her dokumentován
  oběma směry - čtěte velikost.
- **Jinak ze směru vůči dráze**: směr jízdy se bere z poloh zhruba 2 m před a za každým
  vzorkem (`atan2(dx, dz)`); `yaw` hry se k němu přizpůsobí se znaménkem a posunem (každá
  hra má svůj nulový bod a smysl otáčení) pomocí vzorků nad 10 m/s, a důvěřuje se mu jen
  tehdy, když pak souhlasí těsně (kruhový rozptyl nejvýš 0,05, alespoň 20 vzorků). Driftový
  úhel je rozdíl, 0 pod 3 m/s.

### Poměr skluzu z kol {#slip-ratio-from-the-wheels}

Tam, kde kolo nemá `slipRatio.*`, ale má rychlosti kol, poměr skluzu je
`(kolo - auto) / auto` na kolo, z:

- `wheelSurfaceSpeed.*` (rychlost styku pneumatiky, m/s) přímo, je-li posílána (EA WRC, DiRT,
  BeamNG);
- jinak `wheelSpeed.*` (otáčení, rad/s) krát **poloměr valení změřený na kole**: medián
  `rychlost / |omega|` přes vzorky, kde auto dojíždí rovně (nad 10 m/s, ne ve vzduchu,
  plyn pod 0,3, brzda pod 0,05, podélné zrychlení pod 3 m/s²); s méně než 20 takovými
  vzorky se použijí všechny vzorky nad 10 m/s. Poloměr mimo 0,1-1 m se odmítne.

Jen když se dá odvodit všechna čtyři kola; `meta.slip` kola pak bude `physical`. Pod 3 m/s
je skluz 0.

### Ve vzduchu {#airborne}

`airborne` je 1 tam, kde jsou všechna kola mimo zem, posuzováno podle prvního z těchto, který
kolo má pro všechna čtyři kola:

1. `groundContact.*` (BeamNG): žádné kolo nad 0,5;
2. `wheelLoad.*` (hry AC, RBR, BeamNG): žádné kolo nad 5 % vlastního mediánu zatížení;
3. `suspension.*` (0..1 zdvihu): žádné kolo nad 0,02, tj. všechna plně prodloužená.

Jediný izolovaný vzorek ve vzduchu se vymaže. Trackmania píše `airborne` sama.

### Volný povrch {#loose-ground}

Tam, kde kolo má `surfaceRumble.*` (Forza), `loose` je 1 tam, kde alespoň dvě kola hlásí
vibrace alespoň třetinu sekundy, s mezerami kratšími než sekunda přemostěnými (hladká
část štěrkové cesty je pořád štěrková cesta). Trackmania píše `loose` sama z materiálů
povrchu kol.

### Rychlost zatáčení {#yaw-rate}

Tam, kde kolo má `yaw`, ale ne `yawRate`, je to změna yaw přes sousední vzorky.

## Co nahrávače odvozují samy {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): každý nahrávač kromě Forzy (která ho posílá) ho zapisuje z
  `suspensionM.*` jako polohu v rozsahu, který kolo použilo (od minima do maxima). Je pro
  tyče odpružení na autě a pro poznání kola visícího ve vzduchu; není to absolutní zlomek
  zdvihu.
- **`steer`** pro hry Kunos, škálované na kolo (viz [Hry Assetto Corsa](telemetry-assetto-corsa.md)).
- **Zrychlení** pro BeamNG, ze změny světové rychlosti ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** a osa nahoru pro Richard Burns Rally, z poloh ([Rallye hry](telemetry-rally.md)).

## Orientace {#handedness}

Je-li svět hry levotočivý - Forzin ano -, kurz se v pravotočivém prohlížeči zrcadlí;
vlastní řízení a odpružení kol to prozradí. Nahrávače nemění orientaci: svět Z nahoru
(BeamNG) se otočí na Y nahoru rotací, která ji zachová, a všechno ostatní se zapisuje tak,
jak přišlo.
