---
title: Pravidla
nav_order: 2
lang: "cs"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Pravidla, podle kterých to stojí {#the-rules-this-is-built-under}

Každá část 3DHeat GameCapture se řídí stejnými omezeními. Jsou to návrhová rozhodnutí, ne upozornění, a několik z nich vědomě stojí přesnost.

## Nic se nevkládá a nic se nezachytává háčkem {#nothing-is-injected-nothing-is-hooked}

Žádná část se nepřipojuje k procesu hry, nečte její paměť a nedotýká se jejího grafického API.

- **Snímky** pocházejí z Windows Graphics Capture, veřejného API, které používají nahrávací nástroje obrazovky (přes balíček `windows-capture`), nebo ze souboru videa. Viz [Zachytávání, masky a kvalita snímků](reconstruction-capture.md).
- **Telemetrie** pochází jen z rozhraní, která hry pro ni zveřejňují:
  - UDP feed Data Out ze hry Forza, zapnutý v nastavení hry;
  - pojmenované sdílené paměťové stránky, které hry Kunos zveřejňují pro aplikace (`Local\acpmf_physics` a další). Otevírají se jen pro čtení přes `mmap`. Je to zdokumentovaný způsob, jakým aplikace tyto stránky čtou, ne čtení paměti procesu hry;
  - UDP telemetrii, kterou posílají EA SPORTS WRC, hry DiRT a Richard Burns Rally (přes plugin RSF/NGP), když je zapnete v jejich vlastních nastaveních;
  - protokolové rozhraní BeamNG, přes malý Lua mod „protocol“, který načte a odešle vlastní soubor hry `lua/vehicle/protocols.lua`;
  - rozhraní pluginu Openplanet pro Trackmanii, přes plugin, který čte jen to, co Openplanet vystavuje, a zapisuje soubory;
  - vlastní soubory telemetrie iRacingu `.ibt`.

## Proč na tom záleží {#why-it-matters}

Hra zná hloubku každého pixelu přesně a háčkovaný hloubkový buffer by rekonstrukci úrovně udělal téměř dokonalou a triviální. Znamenalo by to ale také vkládat kód do procesů, které mohou být chráněné proti podvodům (anti-cheat), což ohrožuje účet každého, kdo to spustí. Hloubka se proto **odhaduje** z obrazu ([Hloubka](reconstruction-depth.md)). Velká část pipeline rekonstrukce existuje proto, aby z volně použitelných zdrojů získala co nejvíc ztracené přesnosti: telemetrické pózy tam, kde je hra zveřejňuje, měřítko podle roviny země tam, kde ne, a masky, které drží HUD a kokpit mimo řešení.

Hloubkový buffer ReShade se zvažoval a nepoužil se. ReShade přístup k hloubce ve vícehráčových relacích záměrně vypíná, takže by pomáhal jen hrám pro jednoho hráče (viz [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Věci, které nástroj mění ve vašem počítači, a jen na vyžádání {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Akce | Kdy | Co přesně |
|---|---|---|
| Instaluje balíčky Pythonu | první spuštění okna skeneru, po dialogu a potvrzení | `pip install` do interpretru, který nástroj spouští. S `scan.bat` do soukromého `.venv` vedle něj. Nikdy sám od sebe celosystémově. |
| Převádí model hloubky | tlačítko „Nastavit model hloubky“, po druhém dialogu pro PyTorch a spol. | zapíše `models/depth-small-518.onnx` |
| Upravuje `config.json` hry EA SPORTS WRC | `telemetry --game wrc --configure <file>` | zapne paket `wrc` / `session_update` na 127.0.0.1; starý soubor se ponechá jako `config.json.bak` |
| Kopíruje mod BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` do `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (nahradí starší kopii) |
| Kopíruje plugin Trackmanie | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` do `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (nahradí starší kopii) |
| Registruje globální klávesové zkratky | dokud je otevřené okno skeneru (Windows) | Ctrl+Alt+F9 / F10 / F11, uvolněné při zavření okna |
| Aktualizuje nástroj | po odpovědi ano na výzvu k aktualizaci, nebo při `python -m heat3d_update` | viz [Aktualizace](updates.md) |

Soubory `hardware_settings_config.xml` her DiRT a `RichardBurnsRally.ini` nástroj **neupravuje**. Výstup UDP zapnete sami (viz [Rally hry](telemetry-rally.md)).

## Co se čte a co zůstává ve vašem počítači {#what-is-read-and-what-stays-on-your-machine}

Nástroje čtou to, co hra ukazuje na obrazovce, a telemetrii a soubory, které k tomu hra zveřejňuje, ve vašem vlastním počítači. Nic ze hry se nedodává ani dále nešíří: žádná herní data, žádný kód hry, žádné knihovny DLL. Soubory kol, záznamy, rekonstrukce a exportované tratě zůstávají ve vašem počítači; `.gitignore` repozitáře drží záznamy, soubory kol, sítě, váhy modelů a video mimo správu verzí podle složky a typu souboru.

3DHeat GameCapture není spojen s žádným vydavatelem her ani jím schválen. Názvy her a související ochranné známky patří jejich vlastníkům. Držitelé práv: založte issue na [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - odpovídáme rychle a na požádání cokoli odstraníme.
