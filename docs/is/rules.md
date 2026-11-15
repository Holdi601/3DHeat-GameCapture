---
title: "Reglurnar"
nav_order: 2
lang: "is"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Reglurnar sem þetta er smíðað eftir {#the-rules-this-is-built-under}

Allir hlutar 3DHeat GameCapture fylgja sömu takmörkunum. Þær eru hönnunarákvarðanir,
ekki fyrirvarar, og nokkrar þeirra kosta nákvæmni af ásettu ráði.

## Engu er sprautað inn, ekkert er krækt {#nothing-is-injected-nothing-is-hooked}

Enginn hluti hengir sig á leikjaferli, les minni hans eða snertir grafík-API hans.

- **Rammar** koma úr Windows Graphics Capture, opinbera API-inu sem skjáupptökuforrit nota
  (í gegnum `windows-capture` pakkann), eða úr myndbandsskrá. Sjá
  [Upptaka, grímur og gæði ramma](reconstruction-capture.md).
- **Mælingagögn** koma aðeins úr viðmótum sem leikirnir birta til þess:
  - Data Out UDP straumur Forza, kveikt á í stillingum leiksins;
  - nefndu sameiginlegu minnissíðurnar sem Kunos leikir birta fyrir forrit (`Local\acpmf_physics` og
    fleiri). Þær eru opnaðar skrifvarðar með `mmap`; þetta er skjalfesta leiðin sem forrit lesa
    þær, ekki minnislestur leikjaferilsins;
  - UDP mælingagögnin sem EA SPORTS WRC, DiRT leikirnir og Richard Burns Rally (í gegnum
    RSF/NGP viðbótina) senda þegar kveikt er á þeim í eigin stillingaskrám þeirra;
  - samskiptaviðmót BeamNG, í gegnum lítið Lua „protocol“ mod sem `lua/vehicle/protocols.lua`
    leiksins sjálfs hleður og sendir;
  - Openplanet viðbótaviðmót Trackmania, í gegnum viðbót sem les aðeins það sem
    Openplanet birtir og skrifar skrár;
  - eigin `.ibt` mælingaskrár iRacing.

## Hvers vegna það skiptir máli {#why-it-matters}

Leikurinn veit dýpt hvers díls nákvæmlega, og krækt dýptarbiðminni myndi gera endurbyggingu borða
nánast fullkomna og léttvæga. Það myndi líka þýða að sprauta inn í ferli sem
kunna að vera varin af svindlvörn, sem stofnar reikningi hvers sem keyrir það í hættu. Því er dýptin
*áætluð* úr myndinni í staðinn ([Dýpt](reconstruction-depth.md)), og stór hluti
endurbyggingarferlisins er til að endurheimta sem mest af þessari töpuðu nákvæmni úr
heimildum sem eru frjálsar í notkun: stöður úr mælingagögnum þar sem leikur birtir þær, kvarða úr jarðfleti þar sem
hann gerir það ekki, og grímur sem halda HUD og stjórnklefa utan lausnarinnar.

Dýptarbiðminni ReShade var skoðað og ekki notað. ReShade slekkur á aðgangi að dýpt í
fjölspilunarlotum að hönnun, svo það myndi aðeins gagnast einspilunarleikjum (sjá
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Hlutir sem verkfærið breytir á vélinni þinni, og aðeins þegar beðið er um {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Aðgerð | Hvenær | Hvað nákvæmlega |
|---|---|---|
| Setur upp Python pakka | fyrsta keyrsla skönnunargluggans, eftir glugga og já | `pip install` í túlkinn sem keyrir verkfærið - með `scan.bat`, einkarekna `.venv` við hlið þess. Aldrei kerfisbundið af sjálfu sér. |
| Umbreytir dýptarlíkaninu | hnappurinn „Set up the depth model“, eftir annan glugga fyrir PyTorch og fleira | skrifar `models/depth-small-518.onnx` |
| Breytir `config.json` í EA SPORTS WRC | `telemetry --game wrc --configure <file>` | kveikir á `wrc` / `session_update` pakkanum til 127.0.0.1; gamla skráin er geymd sem `config.json.bak` |
| Afritar BeamNG modið | `telemetry --game beamng --install` | `mods/beamng/heat3d` í `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (kemur í stað eldra afrits) |
| Afritar Trackmania viðbótina | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` í `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (kemur í stað eldra afrits) |
| Skráir altæka flýtilykla | meðan skönnunarglugginn er opinn (Windows) | Ctrl+Alt+F9 / F10 / F11, sleppt þegar glugganum er lokað |
| Uppfærir verkfærið | eftir að þú svarar já við uppfærslubeiðninni, eða keyrir `python -m heat3d_update` | sjá [Uppfærslur](updates.md) |

`hardware_settings_config.xml` í DiRT leikjunum og `RichardBurnsRally.ini` í Richard Burns Rally
eru **ekki** breytt af verkfærinu; þú kveikir sjálfur á UDP úttaki þeirra
(sjá [Rallýleikir](telemetry-rally.md)).

## Hvað er áfram á ábyrgð notandans {#what-stays-the-users-responsibility}

Það sem notandi beinir verkfærunum að er áfram háð leyfi og EULA þess leiks. Hringskrár,
upptökur, endurbyggingar og útfluttar brautir tilheyra þeim sem á leikinn og
gögnin; `.gitignore` geymslunnar heldur upptökum, hringskrám, netum (meshes), líkanaþyngdum og
myndbandi utan útgáfustjórnar eftir möppu og skráartegund.
