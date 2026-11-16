---
title: "Pravidlá"
nav_order: 2
lang: "sk"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Pravidlá, podľa ktorých to vzniklo {#the-rules-this-is-built-under}

Každá časť 3DHeat GameCapture sa riadi rovnakými obmedzeniami. Sú to konštrukčné rozhodnutia, nie
výhrady, a niekoľko z nich úmyselne stojí presnosť.

## Nič sa neinjektuje, nič sa neháčkuje {#nothing-is-injected-nothing-is-hooked}

Nič z toho sa nepripája k procesu hry, nečíta jej pamäť a nedotýka sa jej grafického API.

- **Snímky** prichádzajú z Windows Graphics Capture, verejného API, ktoré používajú nahrávače
  obrazovky (cez balík `windows-capture`), alebo zo súboru videa. Pozrite
  [Snímanie, masky a kvalita snímok](reconstruction-capture.md).
- **Telemetria** prichádza len z rozhraní, ktoré hry na tento účel zverejňujú:
  - UDP telemetria Forza Data Out, zapnutá v nastaveniach hry;
  - pomenované zdieľané stránky pamäte, ktoré hry Kunos zverejňujú pre aplikácie (`Local\acpmf_physics`
    a ďalšie). Otvárajú sa len na čítanie cez `mmap`; je to zdokumentovaný spôsob, akým aplikácie
    tieto údaje čítajú, nie čítanie pamäte procesu hry;
  - UDP telemetria, ktorú posielajú EA SPORTS WRC, hry DiRT a Richard Burns Rally (cez plugin
    RSF/NGP), keď sú zapnuté vo ich vlastných nastaveniach;
  - protokolové rozhranie BeamNG cez malý Lua "protokolový" mod, ktorý načíta vlastný
    `lua/vehicle/protocols.lua` hry a ktorý ho posiela;
  - rozhranie zásuvného modulu Openplanet pre Trackmania, cez plugin, ktorý číta len to, čo
    Openplanet sprístupní, a zapisuje súbory;
  - vlastné telemetrické súbory iRacing `.ibt`.

## Prečo na tom záleží {#why-it-matters}

Hra pozná hĺbku každého pixelu presne, a háčkovaný hĺbkový buffer by spravil rekonštrukciu levelu
takmer dokonalou a triviálnou. Znamenal by aj injektovanie do procesov, ktoré môžu byť chránené
proti podvádzaniu, čo ohrozuje účet každého, kto to spustí. Hĺbka sa preto *odhaduje* z obrazu
([Hĺbka](reconstruction-depth.md)), a veľká časť rekonštrukčnej linky existuje na to, aby z
zdrojov, ktoré sú voľne použiteľné, získala čo najviac z tejto stratenej presnosti: telemetrické
pózy tam, kde ich hra zverejňuje, mierku z roviny terénu tam, kde nie, a masky, ktoré držia HUD
a kokpit mimo riešenia.

ReShade hĺbkový buffer bol zvažovaný a nepoužitý. ReShade v multiplayerových reláciách prístup
k hĺbke vypína úmyselne, takže by pomohol len hrám pre jedného hráča (pozrite
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Veci, ktoré nástroj mení na vašom počítači, a len keď sa to žiada {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Akcia | Kedy | Čo presne |
|---|---|---|
| Inštaluje balíky Python | prvé spustenie okna skenovania, po dialógu a súhlase | `pip install` do interpretera, ktorý nástroj spúšťa - pri `scan.bat` do súkromného `.venv` vedľa neho. Nikdy nie systémovo sama od seba. |
| Prevádza model hĺbky | tlačidlo "Set up the depth model", po druhom dialógu pre PyTorch a ďalšie | zapíše `models/depth-small-518.onnx` |
| Upraví `config.json` EA SPORTS WRC | `telemetry --game wrc --configure <file>` | zapne paket `wrc` / `session_update` na 127.0.0.1; pôvodný súbor sa uloží ako `config.json.bak` |
| Skopíruje mod BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` do `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (nahradí staršiu kópiu) |
| Skopíruje plugin Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` do `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (nahradí staršiu kópiu) |
| Registruje globálne klávesové skratky | kým je otvorené okno skenovania (Windows) | Ctrl+Alt+F9 / F10 / F11, uvoľnené pri zatvorení okna |
| Aktualizuje nástroj | po potvrdení v dialógu aktualizácie, alebo spustením `python -m heat3d_update` | pozrite [Aktualizácie](updates.md) |

Súbory `hardware_settings_config.xml` hier DiRT a `RichardBurnsRally.ini` hry Richard Burns Rally
nástroj **neupravuje**; výstup UDP si zapnete sami (pozrite [Hry rally](telemetry-rally.md)).

## Čo sa číta a čo zostáva na vašom počítači {#what-is-read-and-what-stays-on-your-machine}

Nástroje čítajú to, čo hra ukazuje na obrazovke, a telemetriu a súbory, ktoré na to hra zverejňuje, na vašom vlastnom počítači. Nič z hry sa nedodáva ani ďalej nešíri: žiadne herné dáta, žiadny kód hry, žiadne knižnice DLL. Súbory kôl, záznamy, rekonštrukcie a exportované trate zostávajú na vašom počítači; `.gitignore` repozitára drží záznamy, súbory kôl, siete, váhy modelov a video mimo správy verzií podľa priečinka a typu súboru.

3DHeat GameCapture nie je spojený so žiadnym vydavateľom hier ani ním schválený. Názvy hier a súvisiace ochranné známky patria ich vlastníkom. Držitelia práv: založte issue na [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - odpovedáme rýchlo a na požiadanie čokoľvek odstránime.
