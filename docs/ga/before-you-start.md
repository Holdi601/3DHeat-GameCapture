---
title: Sula dtosaíonn tú
nav_order: 1.5
lang: ga
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Sula dtosaíonn tú {#before-you-start}

An bhfuil tú nua leis an líne ordaithe? Tugann an leathanach seo thú ó rud ar bith go dtí do chéad ordú oibre. Tógann sé
thart ar dheich nóiméad, uair amháin.

## 1. Suiteáil Python {#install-python}

Is clár Python é GameCapture. Teastaíonn **Python 3.10 nó níos nuaí** uait.

1. Téigh go [python.org/downloads](https://www.python.org/downloads/) agus íoslódáil an
   Python is nuaí do Windows.
2. Rith an suiteálaí. Ar an gcéad scáileán, **cuir tic i "Add python.exe to PATH"**. Gan an tic,
   ní aimseoidh an teirminéal Python.
3. Cliceáil *Install Now*.

Nó, i dteirminéal: `winget install Python.Python.3.12`.

## 2. Suiteáil Git {#install-git}

Íoslódálann Git an uirlis. Faigh é ó [git-scm.com](https://git-scm.com/download/win), nó rith
`winget install Git.Git`. Mura bhfuil Git uait, úsáid *Code > Download ZIP* ar an
[leathanach GitHub](https://github.com/Holdi601/3DHeat-GameCapture) agus dízipeáil é.

## 3. Oscail teirminéal i bhfillteán {#open-a-terminal-in-a-folder}

Is fuinneog é teirminéal inar clóscríobhann tú orduithe. Úsáideann na leathanaigh seo **PowerShell**, atá ag gach
ríomhaire Windows.

- Oscail an fillteán in File Explorer, cliceáil an barra seoltaí, clóscríobh `powershell` agus brúigh Enter.
  Osclaíonn PowerShell **sa fhillteán sin**.
- Nó oscail PowerShell ón roghchlár Start agus téigh go fillteán le `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Léigh na horduithe ar na leathanaigh seo {#read-the-commands-on-these-pages}

- Clóscríobh gach líne ordaithe agus brúigh Enter.
- Is **ionadchoinneálaí** é téacs idir lúibíní uilleacha: cuir do luach féin ansin, gan na lúibíní.
  Ciallaíonn `<recording>.mp4` ainm comhaid ar nós `match1.mp4`.
- Tá téacs idir lúibíní cearnacha, ar nós `[--fps 5]`, **roghnach**.
- Teastaíonn comharthaí athfhriotail ó chosán a bhfuil spásanna ann: `"C:\My Videos\match1.mp4"`.
- Is nótaí iad línte a thosaíonn le `#`. Ní chlóscríobhann tú iad.

## 5. Faigh an uirlis agus a pacáistí {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Déanann `python -m venv .venv` fillteán príobháideach do phacáistí na huirlise, ionas nach measctar iad le
haon rud eile ar do ríomhaire. Tosaíonn gach ordú ansin le `.venv\Scripts\python`.

**Ba chóir duit** an líne dheireanach a fheiceáil ag rá `Successfully installed ...`. Seiceáil go n-oibríonn an uirlis:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Ba chóir duit** liosta orduithe a fheiceáil, ag tosú le `usage: heat3d_capture`.

![An liosta orduithe a phriontálann --help](../assets/img/cli-help.svg)

Is féidir leat an fillteán a *ghníomhachtú* uair amháin freisin, agus ansin `python` amháin a chlóscríobh:

| Teirminéal | Gníomhachtaigh | Ansin |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Má deir PowerShell *running scripts is disabled*, rith
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` uair amháin, nó scipeáil an ghníomhachtú.

## 6. Cláir bhreise a theastaíonn ó roinnt orduithe {#extra-programs-some-commands-need}

| Ordú | Teastaíonn | Suiteáil |
|---|---|---|
| `hud` | **ffmpeg** agus **ffprobe** (léann comhaid físe) | `winget install Gyan.FFmpeg`, ansin oscail teirminéal nua. Seiceáil le `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, suiteáilte roimh na pacáistí eile | an t-ordú ó [pytorch.org](https://pytorch.org/get-started/locally/) do do GPU |

## Nuair a théann rud éigin cearr {#when-something-goes-wrong}

| Feiceann tú | Ciallaíonn sé | Déan seo |
|---|---|---|
| `'python' is not recognized` | Níl Python ar PATH | Athshuiteáil Python leis an tic PATH, ansin oscail teirminéal nua. |
| `No module named heat3d_capture` | níl an teirminéal i bhfillteán na huirlise | Úsáid `cd` chun dul isteach san fhillteán `3DHeat-GameCapture`. |
| `No module named numpy` (nó pacáiste eile) | níl na pacáistí suiteáilte, nó d'úsáid tú Python eile | Rith an líne `pip install -r requirements.txt` arís, le `.venv\Scripts\python`. |
| `'.venv' is not recognized` | chlóscríobh tú `/` i cmd | Úsáid cúlslaiseanna: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | tá ffmpeg ar iarraidh | Féach céim 6, ansin oscail teirminéal nua. |

Ar aghaidh: tá chéad sampla do gach jab ar an [Leathanach baile](index.md).
