---
title: "`.glb`-utdata"
nav_order: 6
lang: "no"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# `.glb`-utdata {#the-glb-output}

En rekonstruksjon skrives som en binær glTF 2.0-fil (`.glb`). 3DHeat-visningsprogrammet laster den
via panelet Bakgrunn / nivå uten noen spesialbehandling. Det er samme kontrakt som Unreal-eksportøren
skriver. Koden: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Den er skrevet for hånd i stedet for med et glTF-bibliotek. Utdataene er en smal delmengde (én
buffer, tett pakket, ingen animasjon, ingen skinning). Et bibliotek som kan skrive alt av glTF
ville gi versjonsproblemer for noen hundre linjer.

## Hva som står i en skannings fil {#what-is-in-a-scans-file}

| Del (navn på node og mesh) | Innhold |
|---|---|
| `ground:<navn>` | trekanter som vender opp innen 35 grader |
| `structure:<navn>` | alt annet |

`<navn>` er filnavnet uten filendelse når man lagrer fra vinduet, eller videoens navn for
`reconstruct`. En del uten trekanter utelates. En skanning skriver aldri en `water:`-del.
`asset.generator` er `heat3d-capture-scan`.

## Kontrakten {#the-contract}

- **Én node per del**, med navnet til delen. Meshen gjentar navnet. Visningsprogrammet leser
  *node*-navnet først, så hvis bare meshene ble navngitt, ville klassifiseringen gå tapt.
- Etiketten er `<klasse>:<navn>`, med klassen `ground`, `structure` eller `water`. Det er
  prefikset visningsprogrammet matcher (`^(ground|structure|water)\s*[:|]`). Det tar klassen som den
  står, og gjetter ikke ut fra geometrien. Bakken tegnes massiv, konstruksjoner nesten
  gjennomsiktige.
- **Koordinatene er i visningsrommet**: Y opp, høyrehåndet, og **skalert til centimeter**
  (meter x 100) for å passe Unreal-eksportøren. Da laster en opptak og en motoreksport av samme sted
  i samme størrelse med de samme kameraverdiene. Filens øverste `extras.unit_metres` er `0.01`
  (en enhet er en centimeter). En leser som jobber i meter, som [`locate`](locate.md), tar den i sin
  rette størrelse. En skanning som er plassert av Forza-telemetri er et unntak i høyrehåndsregelen.
  Den blir i spillets egen verden, Y opp og venstrehåndet, akkurat som rundefilene. Slik
  havner rundene som er kjørt over den på riktig sted. Når skalaen til en skanning ble funnet på et
  senere nøkkelbilde ([Skala](reconstruction-pose.md#scale)), tas den faktoren med i skalaen som
  skrives.
- `COLOR_0` leses av visningsprogrammet, som bruker den til å skygge bakken når bryteren
  *Registrert farge* i panelet Bakgrunn / nivå er på (av som standard).
- En skanning med steder merket for hånd får `<navn>.marks.json` ved siden av seg. Se
  [Lagring](reconstruction-scan-ui.md#saving).
- Per primitiv: `POSITION` (float VEC3, med `min` og `max`, som visningsprogrammet rammer kameraet
  inn fra), `NORMAL` (float VEC3), valgfri `COLOR_0` (float VEC3, 0..1), valgfri `TEXCOORD_0`.
  Indekser er 16-bit når alle er under 65 536, ellers 32-bit. Modus er trekanter.
- Hver buffervisning starter på en 4-byte-grense. JSON-delen fylles med mellomrom og BIN-delen med
  nuller til 4 byte.

## Sjekker før skriving {#checks-before-writing}

Hver del valideres. Den avvises med en melding som nevner delen, hvis den mangler hjørnepunkter,
hvis antall indekser ikke er hele trekanter, hvis en indeks er utenfor rekkevidde eller negativ, hvis
posisjoner ikke er endelige tall, eller hvis normaler eller farger ikke stemmer med antall
hjørnepunkter. Manglende normaler regnes ut, **vektet etter areal**. Marching cubes lar tynne
biter ligge ved siden av store flater, og et uvektet gjennomsnitt lar små trekanter overstemme flaten
de ligger på. Et hjørnepunkt uten retning får "opp". Det er en feil å ikke skrive noen deler.

Eksporten gir ingenting tilbake, og vinduet sier "Ingenting å lagre", når volumet ikke gir noen
flate. Da skrives heller ingen tom fil som ser ut som en vellykket skanning.

## Teksturer {#textures}

Skriveren støtter en PNG-basisfarge-tekstur per del (med UV-er, dobbeltsidig, ikke-metallisk og helt
ru materiale). Skanninger bruker den ikke. De har farge per hjørnepunkt. Se
[farge](reconstruction-fusion-and-texture.md#colour).

## Referansenivået {#the-reference-level}

`geometry/reference.py` bygger et syntetisk nivå av nøyaktig kjent størrelse gjennom den samme
skriveren: en 400 m underdelt bakke, tre bygninger på 20 x 20 x 12 m og en dam på 50 m, 1,5 m under
bakken. Hver klasse har sin egen flate farge. Visningsprogrammets egne tester lager det og leser det
med visningsprogrammets ekte leser. Formatet testes dermed på begge sider, uten spill og uten
opptaksutstyr.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
