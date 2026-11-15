---
title: "Běh a závislosti"
nav_order: 8
lang: "cs"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Běh, závislosti a výkon {#runtime-dependencies-and-performance}

Kód: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dvojklik. Sám dělá jen dvě věci:

1. **Najde Python** (`python`, pak `py`). Když žádný není, zeptá se
   `Install it now with winget [Y,N]?`; na Y spustí
   `winget install -e --id Python.Python.3.12`, pak vás požádá zavřít okno a spustit
   `scan.bat` znovu, aby Windows převzal novou PATH. Na N se nic neinstaluje.
2. **Vytvoří soukromé prostředí**, `.venv` vedle `scan.bat`, když žádné není, a aktualizuje
   jeho pip - takže nic se neinstaluje do systémového Pythonu.

Pak spustí `.venv\Scripts\python.exe -m heat3d_capture.ui`. Všechno ostatní - zjištění, co
chybí, vysvětlení, k čemu to je, dotazy - se děje v Pythonu, jako dialog.

## Kontrola při prvním spuštění {#first-run-preflight}

Dřív, než okno naimportuje cokoli těžkého, se zkontroluje každý požadavek (s
`importlib.util.find_spec`, takže napůl odstraněný balíček se počítá jako chybějící).
Pravidla:

- **Všechno se kontroluje nejdřív.** Úplný seznam se shromáždí, než se cokoli řekne, aby
  oprava jednoho balíčku nevedla rovnou k další chybě.
- **Ptát se, nikdy nepředpokládat.** Dialog vypíše každý chybějící balíček, k čemu slouží a
  celkové stažení, a nedělá nic bez **Download and install**. Zrušení skončí: „Nothing was
  installed and nothing was changed.“
- **Mlčení není souhlas.** Bez Qt se kontrola vrátí do konzole a zeptá se
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znamenají ano); bez terminálu, kde
  odpovědět (konec vstupu), se nic neinstaluje.
- **Do vlastního prostředí tohoto nástroje.** Instalace je `<běžící python> -m pip install ...`
  jako podproces - s `scan.bat` soukromé `.venv`. Když selže, dialog ukáže poslední řádek
  výstupu pipu a příkaz k vyzkoušení ručně.

| Balíček | Importuje se jako | Zobrazeno jako, k čemu slouží | Přibližné stažení |
|---|---|---|---|
| numpy | `numpy` | aritmetika, na které stojí všechno ostatní | 20 MB |
| opencv-python | `cv2` | čtení videosouborů a snímků z kamery | 40 MB |
| onnxruntime-directml na Windows, jinde onnxruntime | `onnxruntime` | běh modelu hloubky na vaší grafické kartě | 120 MB |
| PySide6-Essentials | `PySide6` | okno a jeho ovládací prvky | 90 MB |
| scipy | `scipy` | vyhlazení rekonstruovaného povrchu | 45 MB |
| scikit-image | `skimage` | převod měření na 3D povrch | 30 MB |
| windows-capture | `windows_capture` | živé zachycení okna hry (nepovinné: bez něj videosoubory stále fungují) | 5 MB |

Převod modelu hloubky potřebuje tři další, vyžádané zvlášť a jen tehdy, když stisknete
„Set up the depth model“: `torch` (asi 900 MB), `transformers` (30 MB), `onnxscript` (15 MB).
Samotný skener je nikdy neimportuje.

Offline příkaz `reconstruct` má vlastní kontrolu, spuštěnou poté, co vypíše řádek licence,
a jen v terminálu: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow` a `vggt` z GitHub repozitáře Meta (instalovaný s `--no-deps`,
protože jeho metadata připínají numpy pod verzi 2). Stejný seznam je v
`requirements-offline.txt`; viz [Offline rekonstrukce](reconstruction-offline.md#requirements).

Balíček ONNX Runtime, který se nabízí, je ten, který `requirements.txt` vybere pro
platformu: `onnxruntime-directml` na Windows, `onnxruntime` jinde. Když je `onnxruntime`
už naimportovatelný (třeba `onnxruntime-gpu`), nic se neinstaluje: kontrola je podle názvu
modulu.

## Instalace ručně {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` připíná: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(jen Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` na Windows a `onnxruntime>=1.19` jinde.

`requirements-offline.txt` přidává, co potřebuje jen `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` a `Pillow`, s instalačním řádkem `vggt` (`--no-deps`) a
poznámkou o licenci VGGT v záhlaví. PyTorch tam také není, z důvodu níže.

**PyTorch záměrně chybí.** Správný balíček závisí na grafické kartě a verzi CUDA a připnout
jeden by na strojích, které nejvíc potřebují GPU verzi, nainstaloval build pro CPU. Chcete-li
ho (převod modelu, offline cesta `reconstruct`), nainstalujte ho **před** `requirements.txt`:
wheely torche se můžou usadit na numpy 1.x, na kterém scipy odmítne běžet, a selhání se
ukáže jako `module numpy has no attribute long` zevnitř scipy, daleko od své příčiny.

`onnxruntime-directml` a `onnxruntime-gpu` si odporují: nainstalujte jen jeden.

Ověřeno vývojářem: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na NVIDIA RTX
5080, a stejné prostředí bez jakéhokoli balíčku specifického pro NVIDIA.

## Backendy inference {#inference-backends}

ONNX Runtime se ke grafickým kartám dostává přes poskytovatele provedení a to, kteří
existují, závisí na tom, jak byl onnxruntime nainstalován, ne na hardwaru. Dostupnost se
proto zjišťuje, nejlepší první:

| Pořadí | Poskytovatel | Zobrazeno jako | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | libovolná GPU s Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | cokoli |

**DirectML je výchozí instalace**, protože dosáhne na grafiky AMD a Intel stejně jako na
NVIDIA. NVIDIA je s vlastními poskytovateli rychlejší - instalace `onnxruntime-gpu` přidá
CUDA a okno to řekne, když uvidí kartu NVIDIA běžící na DirectML - ale NVIDIA nesmí být
jediná možnost. CPU je vždy poslední, takže stroj bez použitelné GPU dostane pomalý sken
místo žádného, a přidá se jako záložní, když se vytváří relace na GPU.

Název adaptéru se čte z registru, z třídy klíče displejových adaptérů Windows (ne z
vendorského nástroje jako `nvidia-smi`, který je jen na některých strojích), přeskakuje se
Basic Render Driver. Poskytovatelé vázaní na výrobce pojmenují odpovídající adaptér;
DirectML se ukazuje na prvním vyjmenovaném adaptéru, což je výchozí systémový. Název je jen
pro zobrazení.

`ScanSettings.prefer_backend` (jen skripty) může pojmenovat poskytovatele nebo krátké jméno.

## Co čekat na tomto stroji {#what-to-expect-from-this-machine}

Okno při startu změří skutečnou propustnost modelu hloubky na tomto stroji (6 snímků po
zahřátí), místo aby hledalo GPU v tabulce - tepelný stav, profily napájení notebooků a
verze ovladačů hýbou tím příliš - a řekne, jaký bude sken, dřív než cokoli může začít:

| Naměřené pohledy za sekundu | Úroveň | Nadpis | Rada |
|---|---|---|---|
| 25 a více | v reálném čase | Živé skenování v plném detailu. | Jděte normálním tempem; překryv bude stačit. |
| 12 až 25 | použitelné | Živé skenování, s menším počtem zachovaných pohledů než na plnou rychlost. | Jděte pomalu a zatáčejte mírně - rychlé zatáčky nechají mezery. Rychlá předvolba zachová méně pohledů, což pomůže modelu hloubky stačit. |
| 2 až 12 | pomalé | Nejdřív nahrajte, pak rekonstruujte. | Nahrajte video procházky a rekonstruujte ze souboru později. Výsledek je stejný; jen zpětná vazba není živá. |
| pod 2 | nepraktické | Tento stroj je příliš pomalý na užitečné skenování. | Kratší trasa, nebo menší model. **Start je vypnutý.** |

Na CPU poznámka dodá, že instalace `onnxruntime-directml` na Windows to obvykle spraví.
Nic nemění rozlišení záběru samo o sobě: nepomohlo by to, protože model hloubky běží na
svém pevném vstupním rozměru, ať dostane cokoli; to, co udrží pomalejší stroj nahoře, je
zachovat méně pohledů, což dělá Rychlá předvolba.

### Změřeno vývojářem {#measured-by-the-developer}

Stejný soubor ONNX, stejný výstup, RTX 5080:

| Backend | Propustnost hloubky |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Testovací klip prošlý tvarovanou cestou ONNX:

| Předvolba | Zachované pohledy | Propustnost hloubky |
|---|---|---|
| Rychlá | asi 1 z 7 | asi 50 /s |
| Vyvážená | asi 1 ze 4 | asi 50 /s |
| Podrobná | asi 1 ze 2 | asi 40 /s |

Hloubka je pohodlně rychlejší než záznam, takže živé skenování není vázáno hloubkou.
Prostředí aplikace má asi 349 MiB bez PyTorch, proti zhruba 3,5 GB pro torch s CUDA.

Offline cesta `reconstruct` je jiná: minuty na 16snímkové okno na stolním GPU.

## Paměť {#memory}

- Snímky se po sloučení neuchovávají, kromě **160** pro obarvení sítě.
- Sken se defaultně zastaví na **3000** zachovaných pohledech („Views kept“), jako pojistka.
- Fronta živého záznamu drží 4 snímky; buffer telemetrických poloh 30 sekund.
- Obě voxelové mřížky jsou řídké a síť se získává po blocích, takže paměť sleduje to, co
  se naskenovalo, ne ohraničující obdélník.

## Platforma {#platform}

Skener a nahrávače Assetto Corsa jsou v praxi jen pro Windows: živé zachycení používá
Windows Graphics Capture, klávesové zkratky a průhledný překryv používají Win32 API a stránky
Kunos jsou sdílená paměť Windows. Videosoubory se dají skenovat a nahrávače UDP běží i jinde,
ale to nebylo ověřeno.
