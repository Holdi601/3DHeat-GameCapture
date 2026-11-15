---
title: Skannevinduet
nav_order: 1
lang: "no"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Skannevinduet {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kode: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Vinduet er en tynn visning over `scan/session.py` og `scan/reconstruct.py`. Det eier ingen skanne-
eller geometrilogikk.

## Oppstart {#starting-up}

1. **Oppdateringssjekk** - se [Oppdateringer](updates.md).
2. **Avhengighetssjekk** - hver pakke skanneren trenger, sjekkes før noe importeres. Manglende
   pakker listes med hva de brukes til og nedlastingsstørrelsen, og installeres bare etter
   «Download and install». Avbryt avslutter uten å endre noe. Se
   [Kjøring og avhengigheter](runtime.md#first-run-preflight).
3. **Vindu** - «3DHeat — Level scanner», 1420 x 900, Qt-ens Fusion-stil.
4. **Maskinvaresjekk** - den beste inferensbackenden velges, dybdemodellen lastes, og gjennomstrømningen
   måles på 6 rammer. Vurderingsboksen øverst til venstre sier hvordan skanningen blir (se
   [Kjøring](runtime.md#what-to-expect-from-this-machine)).
5. **Globale hurtigtaster** registreres sist.

### Når det ikke finnes en dybdemodell ennå {#when-there-is-no-depth-model-yet}

Hvis `models/` ikke har noen `depth-*.onnx`, står vurderingen på **«One more thing to set up.»**,
Start er deaktivert, og en knapp **Set up the depth model** vises. Den:

- sjekker etter PyTorch, `transformers` og `onnxscript` (ca. 945 MB til sammen), og spør før den
  installerer dem;
- kjører `tools/export_onnx.py --size small` som en egen prosess (slik at PyTorch aldri ligger i
  skannerens minne), med en grense på 30 minutter. Vinduet svarer ikke mens den kjører;
- ved suksess kjører maskinvaresjekken på nytt; ved feil vises de siste 600 tegnene fra konverterens utdata.

Når flere modeller finnes, velges de **etter lisens, ikke etter filnavn**: `depth-small-*`
(Apache-2.0, kommersiell bruk tillatt) når en finnes, deretter Base, og så Large (begge
ikke-kommersielle). Vurderingsboksen og den grå linjen under knappene sier hvilken fil som brukes,
dens lisens, og eventuelle andre modellfiler som finnes men ikke brukes, for eksempel `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. For å skanne med Base, flytt Small-filen ut av `models/`.

## Venstre kolonne: innstillinger {#left-column-settings}

| Gruppe | Kontroll | Standard | Område / verdier | Hva den gjør |
|---|---|---|---|---|
| (øverst) | Vurderingsboks | «Checking your graphics card…» | farget grønn, gul eller rød etter nivå | Overskriften, `<device> via <API> — N views per second`, én merknad og `Depth model: <file> (<licence>)` |
| Hva skal skannes | Kilde | Hele skjermen | Hele skjermen, Et vindu, En videofil | Hvor rammene kommer fra |
| | Hvilken | `1` | skjermnummer / vindustittel / sti til en video | `monitor:<n>`, `window:<title>`, eller en filsti |
| | Velg fil… | vises for video | `*.mp4 *.mkv *.avi *.mov` | Fyller inn stien |
| Hvor nøye | Forhåndsinnstilling | Balanced | Draft, Balanced, Detailed | Oppløsning på opptaket og hvor selektivt nøkkelrammer velges (under); en enlinjesoppsummering vises under den |
| | Spillets synsfelt | 90° | 30-140° | Spillets **horisontale** synsfelt. For smalt, og nivået rekonstrueres dypere enn det er; for bredt, og det flater ut. Kjørespill ligger nærmere 65° |
| | Overflatedetalj | 0,25 m | 0,05-2,0 m, steg 0,05 | Voxel-størrelse på overflaten. Mindre er finere og tyngre |
| Stopp etter | Tid | ingen grense | 0-120 min | Avslutter skanningen etter så lang tid (0 = ingen grense) |
| | Beholdte synsvinkler | 3000 | 0-100 000 | Avslutter skanningen etter så mange nøkkelrammer, som et minnevern (0 = ingen grense) |
| Hva skal ignoreres | Ignorer HUD og alt på kameraet | på | | Lærer og maskerer HUD, siktekorset, våpenet, panseret og cockpiten ([Opptak](reconstruction-capture.md#what-is-not-the-world)). Linjen under sier hva detektoren avgjør akkurat nå |
| Mens du spiller | Vis tilbakemelding over spillet | på | | Åpner det gjennomsiktige overlegget under skanningen. Hintet under sier: kjør spillet i **kantløs fullskjerm**; eksklusiv fullskjerm kan ikke tegnes over av noe |
| Kjøretelemetri (Forza) | Lytt etter posisjonsdata | av | | Tar kamerabanen fra Forzas Data Out i stedet for å estimere den fra bildet ([Posisjon](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Porten for Data Out |
| | (statuslinje) | | | `N packets — poses come from the game, not from the picture`, eller `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Starter eller stopper; viser hurtigtasten når den ble registrert |
| | **Set up the depth model** | skjult | | Se over |
| | **Save level…** | deaktivert | | Aktiveres etter en skanning som ga overflatevoksler; spør etter et filnavn (standard `scan.glb`) |
| | (grå linje) | | | `Model: <file> (<licence>) · Available: <backends>`, pluss oppsettsmerknader som å installere `onnxruntime-gpu` |

### Forhåndsinnstillingene {#the-presets}

| Forhåndsinnstilling | Lengste side på opptaket | Beholdt kvantil | Startterskel | Oppsummering som vises |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Rask og grov. God for å sjekke en rute før en ekte skanning. |
| Balanced | 960 px | 0,65 | 0,010 | Det vanlige valget. Gå i normalt tempo. |
| Detailed | 1280 px | 0,40 | 0,004 | Treg og grundig. Gå bevisst og sving forsiktig. |

Den beholdte kvantilen betyr «behold en ramme når den endret seg mer enn denne kvantilen av endringene
i de siste 240 rammene». Draft beholder omtrent de travleste 15 %, Detailed de travleste 60 %. Se
[Nøkkelrammer](reconstruction-capture.md#keyframes).

### Innstillinger som er låst i vinduet {#settings-that-are-fixed-in-the-window}

Vinduet rekonstruerer alltid under skanning, bruker en kamerahøyde på **1,15 m** for skalaen i
bakkeplanet (gangverdien 1,70 m kan ikke velges), og lar backend-stigen velge GPU. Dette er
`ScanSettings`-felt (`camera_height`, `prefer_backend`) som bare et skript kan endre.

## Høyre kolonne: hva skanningen gjør {#right-column-what-the-scan-is-doing}

| Element | Viser |
|---|---|
| **What the camera sees** | den siste nøkkelrammen |
| **Shape it is reading** | den predikerte dybden, farget med Turbo-fargekartet, normalisert mellom 2. og 98. persentil for den rammen (så én himmelpiksel ikke flater ut området) |
| **Coverage — where you have been, and how well** | et planoppriss (se under) |
| **Worth another look** | de svake punktene, nummerert til samsvarende ringer på kartet, hver med en instruks; verst (størst) først, høyst 8; deretter punktene du har markert (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Gangfartsbar | `walk speed — N% of the way to the next view`: den siste rammens bildeendring delt på **terskelen i bruk**. Det er forhåndsinnstillingens startverdi for de første 30 rammene, og den justerte verdien etter det ([Nøkkelrammer](reconstruction-capture.md#keyframes)) |
| Helselinje | sporingshelse, eller en opptaksadvarsel (se under) |
| Størrelseslinje | `Size: ...`, hvordan nivåets skala ble fastsatt, eller hvorfor den ikke ble det ([Skala](reconstruction-pose.md#scale)) |
| Statistikklinje | `views  frames  dropped  depth-per-second  seconds`, og mens den rekonstruerer `placed  cells  % well seen  metres`, pluss `recovered` og `loops closed` når noen av dem er ikke-null |
| Hurtigtastlinje | de registrerte tastene, eller hvorfor de ikke kunne registreres |
| Hintlinje (gul) | levende råd (se under), skanningens siste melding, og merker |

### Dekningskartet {#the-coverage-map}

Tegnes på nytt hvert 900. ms i en bakgrunnstråd (aldri i grensesnitttråden), i 200 x 200 celler skalert
til 420 px:

- hver kolonne i dekningsgitteret tar den **beste** observasjonskvaliteten i den (så et godt sett gulv
  ikke males gult av et dårlig sett tak over det);
- fargeskalaen går fra rødt (dårlig) via gult (tynt) og gult (akseptabelt) til grønt (godt);
- aldri observerte celler er en egen mørk grå, så et uutforsket hjørne ikke ser ut som et dårlig skannet;
- banen som er gått, tegnes som en tynn lys linje, gjeldende posisjon som en hvit prikk;
- svake punkter er hvite ringer med nummer;
- punkter du har markert, er gule firkanter merket `M1`, `M2`, ….

Hvordan kvalitet og svake punkter beregnes: [Fusjon, dekning og farge](reconstruction-fusion-and-texture.md#coverage).

### Helselinjen {#the-health-line}

| Sporingshelse (plasserte rammer / rammer) | Tekst | Farge |
|---|---|---|
| ingen rammer ennå | Waiting for the first frame. | grå |
| 90 % eller mer | Tracking well — N of M frames placed. | grønn |
| 60 % eller mer | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | gul |
| under 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rød |

En opptaksadvarsel fra dekningsgitteret erstatter den (rød når skanningen vurderes som ikke
rekonstruerbar, gul ellers): nesten ingen parallakse, alt sett fra over 25 m, eller tynn parallakse.
Se [Dekning](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Hintlinjen {#the-hint-line}

| Vilkår | Hint |
|---|---|
| mer enn halvparten av rammene droppet, etter 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| færre enn 0,3 synsvinkler beholdt per sekund, etter 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| mer enn 8 synsvinkler beholdt per sekund, etter 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skanningen er avsluttet | sesjonens melding: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, eller `failed: <error>` |

## Hurtigtaster {#hotkeys}

Registrert hos Windows (`RegisterHotKey`), så de virker mens spillet har fokus. Å alt-tabbe ut av et
fullskjermspill er akkurat det som ødelegger en opptak.

| Taster | Handling |
|---|---|
| **Ctrl+Alt+F9** | Start / stopp skanning |
| **Ctrl+Alt+F10** | Merk dette stedet for å besøke igjen (under skanning) |
| **Ctrl+Alt+F11** | Vis / skjul overlegget (slår av og på boksen «Show feedback over the game») |

- De registreres én gang, når vinduet åpnes, og frigjøres når det lukkes. Så lenge de er registrert,
  tas disse tastekombinasjonene fra alle andre programmer, også spillet. F-taster med to modifikatorer
  ble valgt fordi spill sjelden binder dem.
- Autorepetering undertrykkes (`MOD_NOREPEAT`), så et holdt nede tastetrykk ikke slår skanningen av
  og på dusinvis av ganger.
- En tast som et annet program allerede holder, rapporteres (`... unavailable: another program already
  has this key`), og de andre virker fortsatt. En knapp viser bare en tast som faktisk ble registrert.
- Tastene er faste i koden (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`). Parseren tar F1-F12 med
  `ctrl`, `alt` og `shift`. Utenfor Windows finnes det ingen globale hurtigtaster, og vinduet sier det.
- **Mark** lagrer gjeldende kameraposisjon (den siste plasserte rammens) og viser «Marked MN. Marked
  spots are on the map and saved with the level.». Før noen ramme er plassert, sier den at det ikke
  finnes noe sted å merke. Merkede punkter tegnes på vinduets kart og overleggets som gule firkanter
  merket `M1`, `M2`, …, listes under de svake punktene, telles i overleggets statistikklinje, og lagres
  sammen med nivået (se under).

## Overlegget {#the-overlay}

Et lite panel festet over spillet, slik at tilbakemeldingen er der øynene allerede er.

- Rammeløst, alltid øverst, et verktøyvindu (ikke i oppgavelinjen eller alt-tab), gjennomsiktig for
  input i Qt og klikk-gjennom i Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), så et klikk beregnet på
  spillet aldri blir spist. Vises uten å ta fokus.
- Øverst til høyre på hovedskjermen, 18 px fra kantene; 214 x 358 px.
- Åpnes når en skanning starter (hvis «Show feedback over the game» er på), og lukkes når den stopper.
- **Krever kantløs fullskjerm**: ingenting kan tegnes over eksklusiv fullskjerm, verken dette, Steams
  overlegg eller Discords.

Fra topp til bunn viser det:

| Element | Innhold |
|---|---|
| Dekningskart | 190 px, samme kart som vinduet, men grovere 120 x 120, med banen, ringene for svake punkter og merkede punkter |
| Helse | samme tekst og farge som helselinjen i vinduet |
| Statistikk | `N placed · M to revisit · X m`, med `· K marked` når noen er merket |
| **bevegelses**-bar | samme som gangfartsbaren i vinduet: den siste rammens bildeendring delt på terskelen i bruk, full når neste ramme vil bli beholdt |
| **skarphets**-bar | skarphet relativt til denne opptakets egen median: grønn fra 0,75, gul fra 0,45, rød under |
| Råd | én instruks, grønn / gul / rød (fet når den ikke er «ok») – se [bilderkvalitet og råd](reconstruction-capture.md#frame-quality-and-advice) |
| Hurtigtaster | de registrerte tastene |

Hvis oppdateringen av overlegget noen gang kaster en feil, bytter det til et rødt panel
**«Feedback stopped»**. Det sier at alt som vises fra før er utdatert, at skanningen fortsatt kjører,
at hovedvinduet fortsatt er riktig, og viser feilen og en teller. Et panel som frøs mens det var grønt,
ville ellers fortsatt blitt lest som en bekreftelse.

## Lagring {#saving}

**Save level…** skriver rekonstruksjonen som en `.glb` (se [`.glb`-utdata](glb-output.md)).
Hvis opptaket ikke gir noen overflate, forklarer «Nothing to save» at sporingen sannsynligvis gikk
tapt for det meste av skanningen. Ved suksess: «Written to <path> ... Load it in 3DHeat through the
Level panel.», og nevner også merkefilen når det finnes merkede punkter.

Merkede punkter skrives ved siden av nivået som **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` er i nivåets egne koordinater (GLB-ens skala brukt, slik at et merke sitter på meshet det ble
laget over), `metres` er i meter; `number` samsvarer med `M1`, `M2`, … i vinduet. Når skalaen ble
funnet på en senere nøkkelramme ([Skala](reconstruction-pose.md#scale)), inkluderer begge denne faktoren.

Å stoppe en skanning beholder det som er samlet inn; en ny **Start** kaster den forrige skanningen.
**Å lukke vinduet spør ikke om lagring**: det stopper skanningen, frigjør hurtigtastene og lukker overlegget.
