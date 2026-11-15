---
title: "Fereastra de scanare"
nav_order: 1
lang: "ro"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Fereastra de scanare {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Cod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Fereastra este o vedere subțire peste `scan/session.py` și `scan/reconstruct.py`; ea nu deține nicio logică de scanare
sau de geometrie.

## Pornirea {#starting-up}

1. **Verificarea actualizărilor** - vezi [Actualizări](updates.md).
2. **Verificarea dependențelor** - fiecare pachet de care are nevoie scanerul este verificat înainte de a fi importat
   nimic; cele lipsă sunt listate cu ce fac și mărimea descărcării, și sunt instalate doar după "Download and install".
   Anulare iese fără să schimbe nimic. Vezi [Rulare și dependențe](runtime.md#first-run-preflight).
3. **Fereastra** - "3DHeat — Level scanner", 1420 x 900, stilul Fusion al Qt.
4. **Verificarea hardware-ului** - se alege cel mai bun backend de inferență, modelul de adâncime este încărcat, iar
   debitul lui este măsurat pe 6 cadre; caseta de verdict din stânga sus spune cum va fi scanarea (vezi
   [Rulare](runtime.md#what-to-expect-from-this-machine)).
5. **Tastele globale** sunt înregistrate ultimele.

### Când nu există încă un model de adâncime {#when-there-is-no-depth-model-yet}

Dacă `models/` nu are niciun `depth-*.onnx`, verdictul spune **"One more thing to set up."** (Mai este un lucru de
pregătit.), Start este dezactivat, iar apare un buton **Set up the depth model** (Pregătește modelul de adâncime). Acesta:

- verifică PyTorch, `transformers` și `onnxscript` (cam 945 MB împreună) și întreabă înainte să le instaleze;
- rulează `tools/export_onnx.py --size small` ca proces separat (ca PyTorch să nu stea niciodată în memoria
  scanerului), cu o limită de 30 de minute. Fereastra nu răspunde cât timp rulează;
- la succes reia verificarea hardware-ului; la eșec arată ultimele 600 de caractere din ieșirea convertorului.

Când sunt mai multe modele prezente, alegerea se face **după licență, nu după numele fișierului**: `depth-small-*`
(Apache-2.0, uz comercial permis) ori de câte ori există unul, apoi Base, apoi Large (ambele necomerciale). Caseta
verdictului și linia gri de sub butoane numesc fișierul folosit, licența lui și orice alte fișiere de model prezente
și nefolosite - de exemplu `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Ca să scanezi cu Base, mută fișierul Small din `models/`.

## Coloana din stânga: setările {#left-column-settings}

| Grup | Control | Implicit | Interval / valori | Ce face |
|---|---|---|---|---|
| (sus) | Caseta verdictului | "Checking your graphics card…" (Se verifică placa grafică…) | colorată verde, chihlimbar sau roșu după nivel | Titlul, `<device> via <API> — N views per second`, o notă și `Depth model: <file> (<licence>)` |
| Ce se scanează | Sursa | Whole screen (Tot ecranul) | Whole screen, A window (O fereastră), A video file (Un fișier video) | De unde vin cadrele |
| | Care | `1` | numărul monitorului / titlul ferestrei / calea unui video | `monitor:<n>`, `window:<title>` sau o cale de fișier |
| | Choose file… (Alege fișierul…) | apare pentru video | `*.mp4 *.mkv *.avi *.mov` | Completează calea |
| Cât de atent | Preset (Presetare) | Balanced (Echilibrat) | Draft (Schiță), Balanced (Echilibrat), Detailed (Detaliat) | Rezoluția capturii și cât de selectivă este cadrarea cheie (mai jos); un rezumat de o linie este arătat sub ea |
| | Game field of view (Câmpul vizual al jocului) | 90° | 30-140° | Câmpul vizual **orizontal** al jocului. Prea îngust și nivelul se reconstruiește mai adânc decât este; prea larg și se aplatizează. Jocurile de curse sunt mai aproape de 65° |
| | Surface detail (Detaliul suprafeței) | 0.25 m | 0.05-2.0 m, pas 0.05 | Mărimea voxelului suprafeței. Mai mic înseamnă mai fin și mai greu |
| Oprește după | Time (Timp) | fără limită | 0-120 min | Încheie scanarea după atâta vreme (0 = fără limită) |
| | Views kept (Vederi păstrate) | 3000 | 0-100,000 | Încheie scanarea după atâtea cadre-cheie, ca gardă de memorie (0 = fără limită) |
| Ce să ignore | Ignore HUD and anything on the camera (Ignoră HUD-ul și orice e pe cameră) | activat | | Învață și mascază HUD-ul, reticulul, arma, capota, cabina ([Captura](reconstruction-capture.md#what-is-not-the-world)). Linia de sub ea spune ce decide acum detectorul |
| În timp ce joci | Show feedback over the game (Arată feedback-ul peste joc) | activat | | Deschide suprapunerea care lasă clicurile să treacă în timpul scanării. Indiciul de sub ea: rulează jocul în **borderless windowed** (fereastră fără margini, pe tot ecranul); exclusive fullscreen (ecran complet exclusiv) nu poate fi desenat peste nimic |
| Telemetria cursei (Forza) | Listen for position data (Ascultă datele de poziție) | oprit | | Ia calea camerei din Data Out al Forza în loc să o estimeze din imagine ([Poziția](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Portul Data Out |
| | (linia de stare) | | | `N packets — poses come from the game, not from the picture`, sau `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** (Pornește scanarea / Oprește scanarea) | | | Pornește sau oprește; arată tasta rapidă când a fost înregistrată |
| | **Set up the depth model** (Pregătește modelul de adâncime) | ascuns | | Vezi mai sus |
| | **Save level…** (Salvează nivelul…) | dezactivat | | Activat după o scanare care a produs voxeli de suprafață; cere un nume de fișier (implicit `scan.glb`) |
| | (linia gri) | | | `Model: <file> (<licence>) · Available: <backends>`, plus note de pregătire, cum ar fi instalarea `onnxruntime-gpu` |

### Presetările {#the-presets}

| Presetare | Latura cea mai lungă a capturii | Cuantila păstrării | Pragul de start | Rezumat afișat |
|---|---|---|---|---|
| Draft (Schiță) | 640 px | 0.85 | 0.020 | Rapidă și grosieră. Bună ca să verifici un traseu înainte de o scanare adevărată. |
| Balanced (Echilibrat) | 960 px | 0.65 | 0.010 | Alegerea obișnuită. Mergi într-un pas normal. |
| Detailed (Detaliat) | 1280 px | 0.40 | 0.004 | Lentă și temeinică. Mergi deliberat și întoarce-te încet. |

Cuantila păstrării înseamnă "păstrează un cadru când s-a schimbat mai mult decât această cuantilă a schimbărilor ultimelor
240 de cadre" - Draft păstrează cam cele mai active 15%, Detailed cele mai active 60%. Vezi
[Cadrele-cheie](reconstruction-capture.md#keyframes).

### Setările fixate în fereastră {#settings-that-are-fixed-in-the-window}

Fereastra reconstruiește mereu în timpul scanării, folosește o înălțime a camerei de **1.15 m** pentru scara planului
solului (valoarea de mers, 1.70 m, nu se poate alege) și lasă scara de backend-uri să aleagă GPU-ul. Acestea sunt câmpurile
`ScanSettings` (`camera_height`, `prefer_backend`) pe care le poate schimba doar un script.

## Coloana din dreapta: ce face scanarea {#right-column-what-the-scan-is-doing}

| Element | Arată |
|---|---|
| **What the camera sees** (Ce vede camera) | ultimul cadru-cheie |
| **Shape it is reading** (Forma pe care o citește) | adâncimea prezisă, colorată cu harta de culori Turbo, normalizată între percentila 2 și 98 a acelui cadru (ca un singur pixel de cer să nu aplatizeze intervalul) |
| **Coverage — where you have been, and how well** (Acoperire - pe unde ai fost și cât de bine) | o vedere în plan (vezi mai jos) |
| **Worth another look** (Merită încă o privire) | punctele slabe, numerotate ca inelele de pe hartă, fiecare cu o instrucțiune; cel mai mare (cel mai mare primul), cel mult 8; apoi punctele pe care le-ai marcat (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Bara vitezei de mers | `walk speed — N% of the way to the next view`: schimbarea imaginii din ultimul cadru împărțită la **pragul folosit** - pragul de start al presetării pentru primele 30 de cadre, cel adaptat după aceea ([Cadrele-cheie](reconstruction-capture.md#keyframes)) |
| Linia de sănătate | sănătatea urmăririi, sau un avertisment de captură (mai jos) |
| Linia de mărime | `Size: ...`, cum a fost fixată scara nivelului sau de ce nu ([Scara](reconstruction-pose.md#scale)) |
| Linia de statistici | `views  frames  dropped  depth-per-second  seconds`, iar în timpul reconstruirii `placed  cells  % well seen  metres`, plus `recovered` și `loops closed` când vreunul nu este zero |
| Linia tastelor rapide | tastele înregistrate, sau de ce nu au putut fi înregistrate |
| Linia de indicii (chihlimbar) | sfaturi live (mai jos), mesajul final al scanării și marcajele |

### Harta de acoperire {#the-coverage-map}

Redesenată la fiecare 900 ms pe un fir de fundal (niciodată pe firul interfeței), la 200 x 200 de celule, scalată la 420 px:

- fiecare coloană a grilei de acoperire ia **cea mai bună** calitate de observare din ea (ca un podea bine văzută să nu
  fie pictată chihlimbar de un tavan slab văzut deasupra ei);
- gama merge de la roșu (rău) - chihlimbar (subțire) - galben (acceptabil) - verde (bun);
- celulele nevăzute niciodată sunt un gri închis distinct, ca un colț neexplorat să nu pară un colț scanat prost;
- traseul parcurs este desenat ca o linie subțire deschisă, poziția curentă ca un punct alb;
- punctele slabe sunt inele albe cu numărul lor;
- punctele pe care le-ai marcat sunt pătrate chihlimbar etichetate `M1`, `M2`, ….

Cum sunt calculate calitatea și punctele slabe: [Fuziunea, acoperirea și culoarea](reconstruction-fusion-and-texture.md#coverage).

### Linia de sănătate {#the-health-line}

| Sănătatea urmăririi (cadre plasate / cadre) | Text | Culoare |
|---|---|---|
| niciun cadru încă | Waiting for the first frame. (Se așteaptă primul cadru.) | gri |
| 90% sau mai mult | Tracking well — N of M frames placed. (Urmărire bună - N din M cadre plasate.) | verde |
| 60% sau mai mult | Tracking is patchy — N of M frames could not be placed. Turn more slowly. (Urmărirea e sacadată - N din M cadre n-au putut fi plasate. Întoarce-te mai încet.) | chihlimbar |
| sub 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. (Pierzi urmărirea - doar N din M cadre plasate. Mișcă-te încet și evită pereții goi și cerul.) | roșu |

Un avertisment de captură din grila de acoperire ține locul acestei linii (roșu când scanarea este judecată ca nereconstruibilă,
chihlimbar altfel): aproape deloc paralaxă, totul văzut de la mai mult de 25 m, sau paralaxă subțire. Vezi
[Acoperirea](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Linia de indicii {#the-hint-line}

| Condiție | Indiciu |
|---|---|
| mai mult de jumătate din cadre pierdute, după 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. (Rămâi în urmă - N cadre pierdute ... Încearcă calitatea Draft sau un detaliu de suprafață mai grosier.) |
| mai puțin de 0,3 vederi păstrate pe secundă, după 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. (Se păstrează foarte puțin - poate stai pe loc, sau te uiți la ceva fără trăsături. Mișcă-te lateral în loc să te întorci pe loc.) |
| mai mult de 8 vederi păstrate pe secundă, după 8 s | Keeping a lot. Slow down a little for cleaner geometry. (Se păstrează multe. Încetinește puțin pentru o geometrie mai curată.) |
| scanarea s-a încheiat | mesajul sesiunii: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` sau `failed: <error>` |

## Tastele rapide {#hotkeys}

Înregistrate la Windows (`RegisterHotKey`), deci funcționează cât timp jocul are focusul. Alt-Tab ieșit dintr-un joc pe
tot ecranul strică exact o captură.

| Taste | Acțiune |
|---|---|
| **Ctrl+Alt+F9** | Pornește / oprește scanarea |
| **Ctrl+Alt+F10** | Marchează acest punct ca să-l revezi (în timpul scanării) |
| **Ctrl+Alt+F11** | Arată / ascunde suprapunerea (comută caseta "Show feedback over the game") |

- Sunt înregistrate o dată, când se deschide fereastra, și eliberate când se închide; cât timp sunt înregistrate, aceste
  combinații de taste sunt luate de la orice alt program, inclusiv jocul. Tastele F cu două modificatoare au fost alese
  pentru că jocurile le leagă rar.
- Repetarea automată este suprimată (`MOD_NOREPEAT`), deci ținerea unei taste nu comută scanarea de zeci de ori.
- O tastă pe care altul program o ține deja este raportată (`... unavailable: another program already has this key`
  - ... indisponibilă: alt program are deja această tastă) iar celelalte funcționează în continuare. Un buton anunță
  doar o tastă care a fost chiar înregistrată.
- Tastele sunt fixate în cod (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); analizorul acceptă F1-F12 cu `ctrl`, `alt`
  și `shift`. În afara Windows nu există taste rapide globale, iar fereastra spune asta.
- **Mark** (Marchează) înregistrează poziția curentă a camerei (a ultimului cadru plasat) și arată "Marked MN.
  Marked spots are on the map and saved with the level." (Marcat MN. Punctele marcate sunt pe hartă și salvate cu
  nivelul.) Înainte ca vreun cadru să fi fost plasat spune că nu există unde să se marcheze. Punctele marcate sunt
  desenate pe harta ferestrei și pe cea a suprapunerii ca pătrate chihlimbar etichetate `M1`, `M2`, …, listate sub
  punctele slabe, numărate în linia de statistici a suprapunerii și salvate cu nivelul (mai jos).

## Suprapunerea {#the-overlay}

Un panou mic fixat peste joc, ca feedback-ul să fie acolo unde se uită deja ochii.

- Fără chenar, mereu deasupra, o fereastră de unelte (nu apare în bara de sarcini sau în alt-tab), transparentă la
  intrare în Qt și făcută să lase clicurile să treacă în Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), ca un clic
  destinat jocului să nu fie înghițit niciodată. Apare fără să ia focusul.
- În colțul din dreapta sus al ecranului principal, la 18 px de margini; 214 x 358 px.
- Se deschide când începe o scanare (dacă "Show feedback over the game" este activat), se închide când se oprește.
- **Are nevoie de modul borderless windowed**: nimic nu poate fi desenat peste ecranul complet exclusiv - nici asta,
  nici suprapunerea Steam, nici cea Discord.

De sus în jos arată:

| Element | Conținut |
|---|---|
| Harta de acoperire | 190 px, aceeași hartă ca fereastra, la 120 x 120 mai grosier, cu traseul, inelele punctelor slabe și punctele marcate |
| Sănătatea | același text și aceeași culoare ca linia de sănătate a ferestrei |
| Statistici | `N placed · M to revisit · X m`, cu `· K marked` când există |
| Bara **movement** (mișcare) | aceeași ca bara vitezei de mers a ferestrei: schimbarea imaginii din ultimul cadru peste pragul folosit, plină când următorul cadru va fi păstrat |
| Bara **sharpness** (claritate) | claritatea față de mediana acestei capturi: verde de la 0,75, chihlimbar de la 0,45, roșu sub atât |
| Sfatul | o instrucțiune, verde / chihlimbar / roșu (îngroșată când nu e "ok") - vezi [calitatea cadrului](reconstruction-capture.md#frame-quality-and-advice) |
| Tastele rapide | tastele înregistrate |

Dacă actualizarea suprapunerii aruncă vreodată o eroare, trece pe un panou roșu **"Feedback stopped"** (Feedback-ul s-a oprit),
care spune că tot ce s-a arătat înainte este depășit, că scanarea rulează în continuare și fereastra principală este încă
corectă, cu eroarea și un contor. Un panou care a înghețat pe verde ar continua altfel să fie citit ca o confirmare.

## Salvarea {#saving}

**Save level…** scrie reconstrucția ca `.glb` (vezi [Rezultatul .glb](glb-output.md)). Dacă volumul nu produce nicio
suprafață, "Nothing to save" (Nimic de salvat) explică faptul că urmărirea s-a pierdut probabil pentru cea mai mare parte
a scanării. La succes: "Written to <path> ... Load it in 3DHeat through the Level panel." (Scris în <path> ... Încarc-o în
3DHeat din panoul Level.), numind și fișierul de marcaje când există puncte marcate.

Punctele marcate sunt scrise lângă nivel ca **`<name>.marks.json`**:

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

`position` este în coordonatele proprii ale nivelului (scara GLB-ului aplicată, deci un punct stă pe plasa peste care a fost
făcut), `metres` în metri; `number` corespunde cu `M1`, `M2`, … din fereastră. Când scara a fost găsită pe un cadru-cheie
ulterior ([Scara](reconstruction-pose.md#scale)), ambele includ acel factor.

Oprirea unei scanări păstrează ce s-a adunat; un nou **Start** șterge scanarea anterioară.
**Închiderea ferestrei nu întreabă dacă vrei să salvezi**: oprește scanarea, eliberează tastele rapide și închide suprapunerea.
