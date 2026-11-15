---
title: "Zdrs, drift in izpeljani kanali"
nav_order: 8
lang: "sl"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Zdrs, drift in izpeljani kanali {#slip-drift-and-derived-channels}

Analiza vožnje avta v zavihku Analiza dirke pregledovalnika potrebuje od vsake igre iste nekaj količin: koliko vsaka guma zdrsne, koliko je avto obrnjen stran od smeri, v katero se dejansko premika, ali je v zraku in ali je na ohlapni podlagi. Igre to pošiljajo v zelo različnih oblikah ali sploh ne. Snemalniki tukaj zapišejo to, kar igra pošlje, pod kanoničnimi imeni, poleg tega pa `meta.slip`, ki pove, kaj pomenijo številke zdrsa. Pregledovalnik nato izpelje, kar manjka, enkrat, ko naloži krog. **Igrina lastna vrednost vedno zmaga nad izpeljano.**

## Kaj zapišejo snemalniki {#what-the-recorders-write}

| Igra | Kanali zdrsa | `meta.slip` | Vhodi za kot drifta |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` po kolesu, kot poslano | `peak` (zapiše snemalnik; bralnik `.tele.gz` v pregledovalniku nastavi enako) | `latVel`, `longVel` iz lokalne hitrosti avta |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` iz hitrosti v koordinatnem sistemu avta |
| EA SPORTS WRC, igre DiRT | nobenega; namesto njega `wheelSurfaceSpeed` po kolesu | `null` | `latVel`, `longVel` = svetovna hitrost, projicirana na osi avta |
| Richard Burns Rally | nobenega; tudi hitrosti koles ni | ni | `latVel`, `longVel` = lastno zibanje in pospeševanje avta |
| BeamNG.drive | nobenega; `wheelSurfaceSpeed` in `wheelSpeed` po kolesu | ni | `latVel`, `longVel` = svetovna hitrost, projicirana na osi avta |
| Trackmania | `slipIndex` po kolesu (merilo drsenja 0..1) | `index` | `latVel` (hitrost vstran), `longVel` (hitrost naprej) |
| iRacing | nobenega (ne beleži se) | ni | `yaw` in pot, `yawRate` |

Vrednosti `meta.slip` so opisane v [Datoteka `heat3d-lap`](lap-format.md): `peak` (normirano, tako da nad 1 guma popusti), `scaled` (fizikalni zdrs, deljen s tipično vrednostjo vrha na asfaltu), `physical` (delež in radiani), `index` (merilo drsenja 0..1).

### Zakaj je zdrs Kunos skaliran {#why-kunos-slip-is-scaled}

Forzin zdrs je normiran tako, da je 1 rob oprijema; proti čemu se normira, ni dokumentirano. Kunos pošilja fizikalno razmerje zdrsa (delež) in kot zdrsa (radiani). Deljenje s tipično vrednostjo vrha na asfaltu – 0,12 za razmerje in 0,14 rad (približno 8 stopinj) za kot – naredi, da "nad 1 pomeni zdrsavanje" približno velja za obe družini, zato pregledovalnik za oba prikazuje isto. Gre za približek: pravi vrhovi so odvisni od gume in podlage, zato se surove vrednosti ohranijo poleg skaliranih, pregledovalnik pa izmeri, kje se oprijem vsakega avta dejansko izgublja, iz samih krogov.

## Kaj izpelje pregledovalnik (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Te stvari delajo v pregledovalniku (`src/race/derive.ts` v pregledovalniku 3DHeat), ne v tem repozitoriju.

### Kot drifta, `bodySlip` {#drift-angle-bodyslip}

- **Iz hitrosti v koordinatnem sistemu avta**, kadar sta prisotna `latVel` in `longVel`: `atan2(latVel, |longVel|)`, pod 3 m/s pa 0 (avto, ki stoji postrani, ne drifta).
  Njegov predznak sledi igrini stranski hitrosti, katere smer je pri nekaterih igrah dokumentirana na obe strani – preberite velikost.
- **Sicer iz smeri avta glede na pot**: smer vožnje se vzame iz položajev približno 2 m na vsaki strani vzorca (`atan2(dx, dz)`); igrin `yaw` se prilagodi temu s predznakom in odmikom (vsaka igra ima svojo ničlo in smer vrtenja), pri čemer se uporabijo vzorci nad 10 m/s, in zaupa se mu samo, če se nato dobro ujema (krožni razmik največ 0,05, vsaj 20 vzorcev). Kot drifta je razlika, pod 3 m/s pa 0.

### Zdrs razmerja iz koles {#slip-ratio-from-the-wheels}

Kadar krog nima `slipRatio.*`, ima pa hitrosti koles, se zdrs razmerja izračuna kot `(kolo - avto) / avto` za vsako kolo, iz:

- `wheelSurfaceSpeed.*` (hitrost točke stika, m/s) neposredno, kadar je poslana (EA WRC, DiRT, BeamNG);
- sicer `wheelSpeed.*` (vrtenje, rad/s), pomnoženo z **polmerom kotaljenja, izmerjenim na samem krogu**: mediana `speed / |omega|` na vzorcih, kjer avto samo drsi po ravnini (nad 10 m/s, ni v zraku, plin pod 0,3, zavora pod 0,05, vzdolžni pospešek pod 3 m/s²); če je takih vzorcev manj kot 20, vsi vzorci nad 10 m/s. Polmer zunaj 0,1–1 m se zavrže.

Samo kadar se da izračunati vsa štiri kolesa, se `meta.slip` kroga spremeni v `physical`. Pod 3 m/s je zdrs 0.

### V zraku {#airborne}

`airborne` je 1 tam, kjer so vsa kolesa stran od tal; o tem odloča prvi od teh, ki ga krog ima za vsa štiri kolesa:

1. `groundContact.*` (BeamNG): nobeno kolo nad 0,5;
2. `wheelLoad.*` (igre AC, RBR, BeamNG): nobeno kolo nad 5 % lastne mediane obremenitve;
3. `suspension.*` (0..1 poti): nobeno kolo nad 0,02, torej vsa popolnoma iztegnjena.

Posamezen izoliran vzorec v zraku se počisti. Trackmania piše `airborne` sama.

### Ohlapna podlaga {#loose-ground}

Kjer ima krog `surfaceRumble.*` (Forza), je `loose` 1 tam, kjer vsaj dve kolesi javljata robni pas vsaj tretjino sekunde, s prekinitvami krajšimi od ene sekunde, ki se premostijo (gladka lisa na gramoznati cesti je še vedno gramozna cesta). Trackmania piše `loose` sama iz materialov podlage koles.

### Hitrost zasuka {#yaw-rate}

Kjer ima krog `yaw`, nima pa `yawRate`, je to sprememba `yaw` med sosednjimi vzorci.

## Kaj snemalniki izračunajo sami {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): vsak snemalnik razen Forze (ki ga pošilja) ga zapiše iz `suspensionM.*` kot položaj znotraj razpona, ki ga je krog uporabil (najmanj do največ). Namenjen je stolpcem vzmetenja v pregledovalniku in iskanju kolesa, ki visi v zraku; ni absolutni delež poti.
- **`steer`** za igre Kunos, skaliran za vsak krog (glejte [Igre Assetto Corsa](telemetry-assetto-corsa.md)).
- **Pospeški** za BeamNG, iz spremembe svetovne hitrosti ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** in navzgor os za Richard Burns Rally, iz položajev ([Relijske igre](telemetry-rally.md)).

## Levosučnost {#handedness}

Kjer je svet igre levosučen – Forzin je tak – se proga v desnosučnem pregledovalniku zrcalno obrne; to se vidi po krmiljenju in vzmetenju samih krogov. Snemalniki ne spreminjajo levosučnosti: svet Z navzgor (BeamNG) se z vrtenjem obrne na Y navzgor, kar levosučnost ohrani, vse drugo pa se zapiše tako, kot je poslano.
