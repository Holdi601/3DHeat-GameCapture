---
title: "Skönnunarglugginn"
nav_order: 1
lang: "is"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Skönnunarglugginn {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kóði: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Glugginn er þunn sýn yfir `scan/session.py` og `scan/reconstruct.py`; hann á enga
skönnunar- eða rúmfræðirökfræði.

## Ræsing {#starting-up}

1. **Athugun á uppfærslu** - sjá [Uppfærslur](updates.md).
2. **Athugun á pökkum** - allir pakkar sem skannarinn þarf eru athugaðir áður en nokkuð er
   flutt inn; þeir sem vantar eru taldir upp með tilgangi sínum og niðurhalsstærð, og
   settir upp aðeins eftir „Download and install“. Hætta við lokar án þess að breyta nokkru. Sjá
   [Keyrsluumhverfi og pakkar](runtime.md#first-run-preflight).
3. **Gluggi** - „3DHeat — Level scanner“, 1420 x 900, Fusion stíll Qt.
4. **Athugun á vélbúnaði** - besta ályktunarbakendanum er valið, dýptarlíkanið er hlaðið og
   afköst þess mæld á 6 römmum; úrskurðarreiturinn efst til vinstri segir hvernig skönnunin
   verður (sjá [Keyrsluumhverfi](runtime.md#what-to-expect-from-this-machine)).
5. **Altækir flýtilyklar** eru skráðir síðast.

### Þegar ekkert dýptarlíkan er til enn {#when-there-is-no-depth-model-yet}

Ef `models/` geymir enga `depth-*.onnx` stendur í úrskurðinum **„One more thing to set up.“**, Start
er óvirkur og hnappurinn **Set up the depth model** birtist. Hann:

- athugar PyTorch, `transformers` og `onnxscript` (um 945 MB samtals) og spyr áður en hann
  setur þau upp;
- keyrir `tools/export_onnx.py --size small` sem sérstakt ferli (svo PyTorch verður aldrei eftir í
  minni skannarans), með 30 mínútna tímamörkum. Glugginn svarar ekki meðan það keyrir;
- endurkeyrir athugun vélbúnaðar ef það tekst; ef það mistekst sýnir hann síðustu 600 stafina úr
  úttaki breytisins.

Þegar mörg líkön eru til staðar er valið **eftir leyfi, ekki eftir skráarheiti**: `depth-small-*`
(Apache-2.0, viðskiptaleg notkun leyfð) hvenær sem eitt er til, síðan Base, síðan Large (bæði
óviðskiptaleg). Úrskurðarreiturinn og gráa línan undir hnöppunum nefna skrána sem er notuð, leyfi hennar, og
aðrar líkanaskrár sem eru til staðar en ekki notaðar - til dæmis `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Til að skanna með Base skaltu færa Small skrána úr `models/`.

## Vinstri dálkur: stillingar {#left-column-settings}

| Hópur | Stýring | Sjálfgefið | Svið / gildi | Hvað hún gerir |
|---|---|---|---|---|
| (efst) | Úrskurðarreitur | „Checking your graphics card…“ | litaður grænn, gulbrúnn eða rauður eftir flokki | Fyrirsögn, `<device> via <API> — N views per second`, ein athugasemd og `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Hvaðan rammarnir koma |
| | Which | `1` | númer skjás / gluggaheiti / slóð á myndband | `monitor:<n>`, `window:<title>` eða skráarslóð |
| | Choose file… | sýnt fyrir myndband | `*.mp4 *.mkv *.avi *.mov` | Fyllir inn slóðina |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Upptökuupplausn og hve vandlátt lykilrammaval er (hér á eftir); eins línu samantekt er sýnd undir |
| | Game field of view | 90° | 30-140° | **Lárétt** sjónsvið leiksins. Of þröngt og borðið endurgerist dýpra en það er; of vítt og það flatnar út. Kappakstursleikir eru nær 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, skref 0.05 | Teningastærð yfirborðsins. Minna er fínna og þyngra |
| Stop after | Time | engin takmörk | 0-120 mín | Endar skönnunina eftir þennan tíma (0 = engin takmörk) |
| | Views kept | 3000 | 0-100.000 | Endar skönnunina eftir þennan fjölda lykilramma, sem minnisvörn (0 = engin takmörk) |
| What to ignore | Ignore HUD and anything on the camera | á | | Lærir og grímar HUD, hárkross, vopn, vélarhlíf, stjórnklefa ([Upptaka](reconstruction-capture.md#what-is-not-the-world)). Línan undir segir hvað greinirinn ákveður núna |
| While you play | Show feedback over the game | á | | Opnar yfirlagið sem smellur fara í gegnum meðan skannað er. Ábendingin undir: keyrðu leikinn í **borderless windowed**; ekkert getur teiknað yfir exclusive fullscreen |
| Racing telemetry (Forza) | Listen for position data | slökkt | | Tekur myndavélarferilinn úr Data Out í Forza í stað þess að áætla hann ([Staða](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Data Out gáttin |
| | (stöðulína) | | | `N packets — poses come from the game, not from the picture`, eða `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Ræsir eða stöðvar; sýnir flýtilykilinn þegar hann var skráður |
| | **Set up the depth model** | falið | | Sjá að ofan |
| | **Save level…** | óvirkt | | Virkt eftir skönnun sem skilaði yfirborðsteningum; spyr um skráarheiti (sjálfgefið `scan.glb`) |
| | (grá lína) | | | `Model: <file> (<licence>) · Available: <backends>`, auk uppsetningarathugasemda eins og að setja upp `onnxruntime-gpu` |

### Forstillingarnar {#the-presets}

| Forstilling | Lengsta hlið upptöku | Haldhlutfall (quantile) | Upphafsþröskuldur | Samantekt sem er sýnd |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Fljótt og gróft. Gott til að athuga leið fyrir alvöru skönnun. |
| Balanced | 960 px | 0.65 | 0.010 | Venjulegt val. Gakktu á venjulegum hraða. |
| Detailed | 1280 px | 0.40 | 0.004 | Hægt og vandað. Gakktu yfirvegað og snúðu mjúklega. |

Haldhlutfallið (keep quantile) þýðir „haltu ramma þegar hann breyttist meira en þetta hlutfall breytinga síðustu 240
ramma“ - Draft heldur nokkurn veginn 15% mestu breytinganna, Detailed 60%. Sjá
[Lykilrammar](reconstruction-capture.md#keyframes).

### Stillingar sem eru fastar í glugganum {#settings-that-are-fixed-in-the-window}

Glugginn endurgerir alltaf meðan skannað er, notar myndavélarhæðina **1,15 m** fyrir
kvarða undirlagsins (göngugildið 1,70 m er ekki valanlegt) og lætur bakendastigann
velja skjákortið. Þetta eru `ScanSettings` reitir (`camera_height`, `prefer_backend`) sem aðeins
skripta getur breytt.

## Hægri dálkur: hvað skönnunin er að gera {#right-column-what-the-scan-is-doing}

| Atriði | Sýnir |
|---|---|
| **What the camera sees** | síðasta lykilrammann |
| **Shape it is reading** | spáða dýpt hans, litaða með Turbo litakortinu, stöðlaða milli 2. og 98. hundraðshluta þess ramma (svo einn himinpunktur flati ekki sviðið) |
| **Coverage — where you have been, and how well** | yfirlitsmynd að ofan (sjá hér á eftir) |
| **Worth another look** | veiku blettina, númeraða til samræmis við hringi á kortinu, hvern með leiðbeiningu; versti (stærsti) fyrst, í mesta lagi 8; síðan blettirnir sem þú merktir (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Gönguhraðastika | `walk speed — N% of the way to the next view`: myndbreyting síðasta ramma deilt með **þröskuldinum í notkun** - upphafsgildi forstillingarinnar fyrstu 30 rammana, það aðlagaða eftir það ([Lykilrammar](reconstruction-capture.md#keyframes)) |
| Heilsulína | heilsa rakningar, eða upptökuviðvörun (hér á eftir) |
| Stærðarlína | `Size: ...`, hvernig kvarði borðsins var festur eða hvers vegna ekki ([Kvarði](reconstruction-pose.md#scale)) |
| Tölfræðilína | `views  frames  dropped  depth-per-second  seconds`, og meðan endurgert er `placed  cells  % well seen  metres`, auk `recovered` og `loops closed` þegar annað hvort er ekki núll |
| Flýtilyklalína | skráðu lyklarnir, eða hvers vegna ekki var hægt að skrá þá |
| Ábendingalína (gulbrún) | lifandi ráð (hér á eftir), lokaskilaboð skönnunarinnar og merki |

### Þekjukortið {#the-coverage-map}

Teiknað upp á nýtt á 900 ms fresti í bakgrunnsþræði (aldrei í viðmótsþræðinum), í 200 x 200
reitum skalað í 420 px:

- hver dálkur þekjunetsins tekur **bestu** athugunargæðin í sér (svo vel sést gólf
  er ekki málað gulbrúnt af illa sjáanlegu lofti fyrir ofan það);
- liturinn fer frá rauðu (slæmt) - gulbrúnu (rýrt) - gulu (ásættanlegt) - grænu (gott);
- reitir sem aldrei hafa sést eru sérstakur dökkgrár litur, svo ókannað horn líti ekki út eins og
  illa skannað horn;
- gengna leiðin er teiknuð sem þunn ljós lína, núverandi staða sem hvítur punktur;
- veikir blettir eru hvítir hringir með númeri sínu;
- blettir sem þú merktir eru gulbrúnir ferningar merktir `M1`, `M2`, …

Hvernig gæði og veikir blettir eru reiknuð: [Samruni, þekja og litur](reconstruction-fusion-and-texture.md#coverage).

### Heilsulínan {#the-health-line}

| Heilsa rakningar (rammar staðsettir / rammar) | Texti | Litur |
|---|---|---|
| engir rammar enn | Waiting for the first frame. | grár |
| 90% eða meira | Tracking well — N of M frames placed. | grænn |
| 60% eða meira | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | gulbrúnn |
| undir 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rauður |

Upptökuviðvörun frá þekjunetinu kemur í staðinn (rauð þegar skönnunin er dæmd ekki
endurgerðarhæf, annars gulbrún): nær engin hliðrun (parallax), allt séð úr meira en 25 m fjarlægð,
eða þunn hliðrun. Sjá [Þekja](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Ábendingalínan {#the-hint-line}

| Skilyrði | Ábending |
|---|---|
| fleiri en helmingur ramma felldur, eftir 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| færri en 0,3 rammar geymdir á sekúndu, eftir 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| fleiri en 8 rammar geymdir á sekúndu, eftir 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skönnun lauk | skilaboð lotunnar: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, eða `failed: <error>` |

## Flýtilyklar {#hotkeys}

Skráðir hjá Windows (`RegisterHotKey`), svo þeir virka meðan leikurinn hefur fókus. Að alt-tabba
út úr heilskjásleik er einmitt það sem eyðileggur upptöku.

| Lyklar | Aðgerð |
|---|---|
| **Ctrl+Alt+F9** | Ræsa / stöðva skönnun |
| **Ctrl+Alt+F10** | Merkja þennan stað til að koma aftur á (meðan skannað er) |
| **Ctrl+Alt+F11** | Sýna / fela yfirlagið (víxlar reitnum „Show feedback over the game“) |

- Þeir eru skráðir einu sinni, þegar glugginn opnast, og losaðir þegar hann lokast; meðan
  þeir eru skráðir eru þessar lyklasamsetningar teknar af öllum öðrum forritum, líka
  leiknum. F-lyklar með tveimur breytilyklum voru valdir því leikir binda þá sjaldan.
- Sjálfvirk endurtekning er bæld (`MOD_NOREPEAT`), svo að halda lykli niðri víxli ekki skönnuninni
  tugi sinnum.
- Lykill sem annað forrit heldur nú þegar er tilkynntur (`... unavailable: another program already
  has this key`) og hinir virka áfram. Hnappur auglýsir aðeins lykil sem var í raun
  skráður.
- Lyklarnir eru fastir í kóðanum (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); þáttarinn
  tekur við F1-F12 með `ctrl`, `alt` og `shift`. Utan Windows eru engir altækir flýtilyklar
  og glugginn segir það.
- **Mark** skráir núverandi myndavélarstöðu (stöðu síðasta staðsetta ramma) og sýnir „Marked MN.
  Marked spots are on the map and saved with the level.“ Áður en nokkur rammi hefur verið staðsettur
  segir það að hvergi sé hægt að merkja. Merktir blettir eru teiknaðir á kort gluggans og yfirlagsins sem
  gulbrúnir ferningar merktir `M1`, `M2`, …, taldir upp undir veiku blettunum, taldir í
  tölfræðilínu yfirlagsins og vistaðir með borðinu (hér á eftir).

## Yfirlagið {#the-overlay}

Lítið spjald fest yfir leikinn svo endurgjöfin sé þar sem augun eru nú þegar.

- Rammalaust, alltaf efst, verkfærisgluggi (ekki á verkstikunni né í alt-tab), gegnsætt fyrir
  inntak í Qt og gert þannig að smellir fara í gegnum í Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), svo
  smellur ætlaður leiknum gleypist aldrei. Sýnt án þess að taka fókus.
- Efra hægra horn aðalskjásins, 18 px frá brúnum; 214 x 358 px.
- Opnast þegar skönnun hefst (ef „Show feedback over the game“ er á), lokast þegar hún stöðvast.
- **Þarf borderless windowed ham**: ekkert getur teiknað yfir exclusive fullscreen - ekki þetta,
  ekki yfirlag Steam, ekki yfirlag Discord.

Frá toppi til botns sýnir það:

| Atriði | Innihald |
|---|---|
| Þekjukort | 190 px, sama kort og í glugganum í grófari 120 x 120, með leiðinni, hringjum veikra bletta og merktum blettum |
| Heilsa | sami texti og litur og í heilsulínu gluggans |
| Tölfræði | `N placed · M to revisit · X m`, með `· K marked` þegar einhver eru merkt |
| **movement** stika | sú sama og gönguhraðastika gluggans: myndbreyting síðasta ramma yfir þröskuldinn í notkun, full þegar næsti rammi verður geymdur |
| **sharpness** stika | skerpa miðað við miðgildi þessarar upptöku: græn frá 0,75, gulbrún frá 0,45, rauð undir |
| Ráð | ein leiðbeining, græn / gulbrún / rauð (feitletruð þegar ekki „ok“) - sjá [gæði ramma](reconstruction-capture.md#frame-quality-and-advice) |
| Flýtilyklar | skráðu lyklarnir |

Ef uppfærsla yfirlagsins kastar einhvern tíma villu skiptir það yfir í rautt **„Feedback stopped“** spjald sem segir
að allt sem var sýnt áður sé úrelt, að skönnunin sé enn í gangi og aðalglugginn
enn réttur, með villunni og talningu. Spjald sem frysi grænt myndi annars halda áfram að
lesast sem staðfesting.

## Vistun {#saving}

**Save level…** skrifar endurgerðina sem `.glb` (sjá [`.glb` úttakið](glb-output.md)).
Ef rúmmálið gefur ekkert yfirborð útskýrir „Nothing to save“ að rakning tapaðist líklega
mestalla skönnunina. Þegar það tekst: „Written to <path> ... Load it in 3DHeat through the Level
panel.“, og nefnir merkjaskrána líka þegar merktir blettir eru til.

Merktir blettir eru skrifaðir við hlið borðsins sem **`<name>.marks.json`**:

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

`position` er í eigin hnitum borðsins (kvarði GLB notaður, svo merki situr á netinu sem
það var gert yfir), `metres` í metrum; `number` samsvarar `M1`, `M2`, … í glugganum. Þegar
kvarðinn fannst á síðari lykilramma ([Kvarði](reconstruction-pose.md#scale)) innihalda bæði þann
stuðul.

Að stöðva skönnun heldur því sem var safnað; nýtt **Start** hendir fyrri skönnun.
**Þegar glugganum er lokað er ekki spurt hvort vista eigi**: hann stöðvar skönnunina, losar flýtilyklana og
lokar yfirlaginu.
