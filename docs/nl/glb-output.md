---
title: De .glb-uitvoer
nav_order: 6
lang: "nl"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# De .glb-uitvoer {#the-glb-output}

Een reconstructie wordt geschreven als een binair glTF 2.0-bestand (`.glb`) dat de 3DHeat-viewer via het paneel Achtergrond / level laadt, zonder speciale behandeling - hetzelfde contract als de Unreal-exporter schrijft. Code: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Het wordt met de hand geschreven en niet via een glTF-bibliotheek: de uitvoer is een smalle deelverzameling (één buffer, strak gepakt, geen animatie, geen skinning), en een afhankelijkheid die alle van glTF kan schrijven zou voor een paar honderd regels zijn eigen versieverschil meebrengen.

## Wat er in het bestand van een scan zit {#what-is-in-a-scans-file}

| Deel (naam van node en mesh) | Inhoud |
|---|---|
| `ground:<name>` | driehoeken binnen 35 graden van omhoog gericht |
| `structure:<name>` | al het overige |

`<name>` is de bestandsnaam zonder extensie bij opslaan vanuit het venster, of de naam van de video bij `reconstruct`. Een deel zonder driehoeken wordt weggelaten. Een scan schrijft nooit een `water:`-deel. `asset.generator` is `heat3d-capture-scan`.

## Het contract {#the-contract}

- **Één node per deel**, genoemd naar het label van het deel; de mesh herhaalt de naam. De viewer leest eerst de *node*-naam, dus alleen meshes benoemen zou de indeling verliezen.
- Het label is `<klasse>:<naam>` met klasse `ground`, `structure` of `water` - het voorvoegsel waarop de viewer matcht (`^(ground|structure|water)\s*[:|]`) om de klasse op zijn woord te nemen in plaats van die uit de geometrie te raden. Grond wordt ondoorzichtig getekend, constructies bijna transparant.
- **Coördinaten staan in de viewerruimte**: Y omhoog, rechtshandig, en **geschaald naar centimeters** (meters x 100) zodat ze overeenkomen met de Unreal-exporter; een opname en een engine-export van dezelfde plek laden dan op dezelfde grootte met dezelfde standaardcamera. De bovenste `extras.unit_metres` van het bestand is `0.01` (één eenheid is een centimeter), zodat een lezer die in meters werkt, zoals [`locate`](locate.md), die op ware grootte neemt. Een scan die met Forza-telemetrie is geplaatst is de uitzondering op de handigheid: hij blijft in de eigen wereld van het spel, Y omhoog en linkshandig, net als de rondebestanden, zodat de ronden die erop zijn opgenomen erop landen. Als de schaal van een scan op een latere keyframe is gevonden ([Schaal](reconstruction-pose.md#scale)), wordt die factor in de geschreven schaal verwerkt.
- `COLOR_0` wordt door de viewer gelezen; die kleurt de grond ermee wanneer de schakelaar Vastgelegde kleur in het paneel Achtergrond / level aan staat (standaard uit).
- Een scan met met de hand gemarkeerde plekken krijgt `<name>.marks.json` ernaast; zie [Opslaan](reconstruction-scan-ui.md#saving).
- Per primitive: `POSITION` (float VEC3, met `min` en `max`, waarop de viewer zijn camera richt), `NORMAL` (float VEC3), optioneel `COLOR_0` (float VEC3, 0..1), optioneel `TEXCOORD_0`; indices als 16-bit wanneer elke index kleiner is dan 65.536, anders 32-bit; modus triangles.
- Elke buffer view begint op een 4-byte grens; het JSON-blok wordt met spaties opgevuld en het BIN-blok met nullen tot 4 bytes.

## Controles vóór het schrijven {#checks-before-writing}

Elk deel wordt gecontroleerd en geweigerd met een melding die het noemt wanneer het geen hoekpunten heeft, een aantal indices dat geen hele driehoeken vormt, een index buiten bereik of negatief, niet-eindige posities, of normalen of kleuren die niet bij het aantal hoekpunten passen. Normalen worden berekend wanneer ze ontbreken, **gewogen naar oppervlakte** (marching cubes laat slivers naast grote vlakken achter, en een ongewogen gemiddelde laat kleine driehoeken stemmen tegen het vlak waarop ze liggen); een ontaard hoekpunt krijgt "omhoog". Geen enkel deel schrijven is een fout.

Export levert niets op - en het venster zegt "Nothing to save" - wanneer het volume geen oppervlak oplevert, in plaats van een leeg bestand te schrijven dat als geslaagde scan zou lijken.

## Texturen {#textures}

De schrijver ondersteunt per deel een PNG-basiskleurtextuur (met UV's, een dubbelzijdig, niet-metaal, volledig ruw materiaal). Scans gebruiken die niet; zij dragen kleur per hoekpunt. Zie [kleur](reconstruction-fusion-and-texture.md#colour).

## Het referentielevel {#the-reference-level}

`geometry/reference.py` bouwt via dezelfde schrijver een synthetisch level van precies bekende grootte: een onderverdeelde grond van 400 m, drie gebouwen van 20 x 20 x 12 m en een vijver van 50 m, 1,5 m onder de grond, elke klasse in een eigen vlakke kleur. De eigen tests van de viewer maken het en lezen het met de echte parser van de viewer, zodat het bestandsformaat aan beide kanten getest blijft, zonder game en zonder opnamehardware.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
