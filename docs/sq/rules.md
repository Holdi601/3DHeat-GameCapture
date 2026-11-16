---
title: "Rregullat"
nav_order: 2
lang: "sq"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Rregullat nën të cilat është ndërtuar kjo {#the-rules-this-is-built-under}

Çdo pjesë e 3DHeat GameCapture ndjek të njëjtat kufizime. Janë vendime dizajni,
jo shfajësime, dhe disa prej tyre kushtojnë saktësi me qëllim.

## Asgjë nuk injektohet, asgjë nuk kapet me hook {#nothing-is-injected-nothing-is-hooked}

Asnjë pjesë e kësaj nuk lidhet me procesin e një loje, nuk lexon memorien e saj dhe nuk prek API-n e saj grafik.

- **Kuadrot** vijnë nga Windows Graphics Capture, API publike që përdorin regjistruesit e ekranit
  (përmes paketës `windows-capture`), ose nga një skedar videoje. Shih
  [Kapja, maskat dhe cilësia e kuadrove](reconstruction-capture.md).
- **Telemetria** vjen vetëm nga ndërfaqet që lojërat i publikojnë për të:
  - furnizimi UDP Data Out i Forzës, i ndezur te cilësimet e lojës;
  - faqet e emërtuara të memories së përbashkët që lojërat Kunos i publikojnë për aplikacionet (`Local\acpmf_physics` dhe
    të tjerat). Hapen vetëm për lexim me `mmap`; ky është mënyra e dokumentuar si i lexojnë
    aplikacionet, jo lexim memorieje i procesit të lojës;
  - telemetria UDP që dërgojnë EA SPORTS WRC, lojërat DiRT dhe Richard Burns Rally (përmes shtojcës
    RSF/NGP) kur ndizet te skedarët e tyre të cilësimeve;
  - ndërfaqja e protokollit të BeamNG, përmes një moduli të vogël Lua "protocol" që `lua/vehicle/protocols.lua`
    e vetë lojës e ngarkon dhe e dërgon;
  - ndërfaqja e shtojcave Openplanet të Trackmania, përmes një shtojce që lexon vetëm ç'ekspozon
    Openplanet dhe shkruan skedarë;
  - skedarët e telemetrisë `.ibt` të vetë iRacing.

## Pse ka rëndësi {#why-it-matters}

Loja e di saktësisht thellësinë e çdo piksel, dhe një buffer thellësie i kapur me hook do ta bënte rindërtimin e nivelit
pothuajse të përsosur dhe të parëndësishëm. Do të thoshte edhe injektim në procese që
mund të mbrohen nga anti-cheat, gjë që rrezikon llogarinë e kujtdo që e ekzekuton. Ndaj thellësia
*vlerësohet* nga fotoja ([Thellësia](reconstruction-depth.md)), dhe një pjesë e madhe e rrjedhës së
rindërtimit ekziston për të rikuperuar sa më shumë nga ajo saktësi e humbur nga burime që janë të lira për t'u përdorur:
pozat e telemetrisë ku një lojë i publikon, një shkallë e planit të tokës ku nuk i publikon, dhe maska që e mbajnë HUD-in dhe
kabinën jashtë zgjidhjes.

Buffer-i i thellësisë i ReShade u shqyrtua dhe nuk u përdor. ReShade e çaktivizon qasjen në thellësi në
seanca me shumë lojtarë me dizajn, ndaj do të ndihmonte vetëm lojërat me një lojtar (shih
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Gjërat që mjeti ndryshon në makinën tënde, dhe vetëm kur kërkohet {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Veprimi | Kur | Çfarë saktësisht |
|---|---|---|
| Instalon paketa Python | nisja e parë e dritares së skanimit, pas një dialogu dhe një po-je | `pip install` në interpretuesin që ekzekuton mjetin - me `scan.bat`, `.venv` privat pranë tij. Kurrë në gjithë sistemin vetvetiu. |
| Konverton modelin e thellësisë | butoni "Set up the depth model", pas një dialogu të dytë për PyTorch e të tjerat | shkruan `models/depth-small-518.onnx` |
| Ndryshon `config.json` të EA SPORTS WRC | `telemetry --game wrc --configure <file>` | ndez paketën `wrc` / `session_update` drejt 127.0.0.1; skedari i vjetër ruhet si `config.json.bak` |
| Kopjon modulin e BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` te `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (duke zëvendësuar një kopje më të vjetër) |
| Kopjon shtojcën e Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` te `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (duke zëvendësuar një kopje më të vjetër) |
| Regjistron hotkey globalë | gjersa dritarja e skanimit është e hapur (Windows) | Ctrl+Alt+F9 / F10 / F11, lirohen kur dritarja mbyllet |
| Përditëson mjetin | pasi i përgjigjesh po kërkesës për përditësim, ose ekzekuton `python -m heat3d_update` | shih [Përditësimet](updates.md) |

Skedari `hardware_settings_config.xml` i lojërave DiRT dhe `RichardBurnsRally.ini` i Richard Burns Rally
**nuk** ndryshohen nga mjeti; ti e ndez vetë daljen e tyre UDP
(shih [Lojërat e rally-t](telemetry-rally.md)).

## Çfarë lexohet dhe çfarë mbetet në makinën tënde {#what-is-read-and-what-stays-on-your-machine}

Mjetet lexojnë atë që loja shfaq në ekran, si dhe telemetrinë dhe skedarët që loja publikon për këtë, në kompjuterin tënd. Asgjë nga një lojë nuk dorëzohet as rishpërndahet: asnjë burim i lojës, asnjë kod i lojës, asnjë DLL. Skedarët e xhirove, regjistrimet, rindërtimet dhe pistat e eksportuara mbeten në makinën tënde; `.gitignore` i depos i mban regjistrimet, skedarët e xhirove, rrjetat, peshat e modeleve dhe videon jashtë kontrollit të versioneve sipas dosjes dhe llojit të skedarit.

3DHeat GameCapture nuk është i lidhur me asnjë botues lojërash dhe nuk është miratuar nga asnjë prej tyre. Emrat e lojërave dhe markat tregtare përkatëse u përkasin pronarëve të tyre. Mbajtësit e të drejtave: hapni një issue në [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - përgjigjemi shpejt dhe heqim çdo gjë me kërkesë.
