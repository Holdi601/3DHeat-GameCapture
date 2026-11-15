---
title: "Regjistruesit e telemetrisë"
nav_order: 3
lang: "sq"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Regjistruesit e telemetrisë {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` regjistron çdo kanal që dërgon një lojë, e ndan rrjedhën në xhiro ose etapa, dhe
shkruan një skedar JSON [`heat3d-lap`](lap-format.md) për çdo xhiro në një dosje. Skeda "Analiza e garës" e shikuesit
i lexon ato skedarë. Regjistrimi vazhdon derisa të shtypësh **Ctrl+C**; çfarëdo xhiroje ose etape
është e hapur në atë moment shkruhet nëse është mjaft e gjatë për t'u mbajtur (shih
[Ndarja e xhirove dhe e etapave](lap-splitting.md)).

Kodi: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
dhe modulet në [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opsionet {#options}

| Opsioni | E paracaktuara | Kuptimi |
|---|---|---|
| `--game` | `forza` | Një nga `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Dosja ku shkruhen skedarët e xhirove. Krijohet nëse mungon. Shpërfillet nga `trackmania`, shtesa e së cilës i shkruan vetë skedarët. |
| `--port` | `5300` | Porta UDP ku dëgjohet. **Për çdo lojë përveç Forza vlera 5300 do të thotë "porta e paracaktuar e vetë lojës"**: 20777 për `wrc` dhe lojërat DiRT, 6776 për `rbr`, 4460 për `beamng`. Jep çdo numër tjetër për ta mbivendosur. Nuk përdoret nga lojërat Assetto Corsa (memorie e përbashkët) ose Trackmania (skedarë). |
| `--forward` | asnjë | Vetëm Forza: `host:port` ku t'i kalohet çdo paketë e marrë, e pandryshuar. `127.0.0.1:5301` për FH Companion. Një `:5301` i zhveshur do të thotë `127.0.0.1:5301`. |
| `--install` | off | `beamng`: kopjo fillimisht modën e protokollit në modet e shpaketuara të BeamNG. `trackmania`: kopjo shtesën Openplanet në dosjen e shtesave të Openplanet. Shpërfillet nga lojërat e tjera. |
| `--configure` | asnjë | Vetëm `wrc`: rruga e `config.json` të telemetrisë së EA SPORTS WRC; ndez paketën standarde `wrc` para regjistrimit (me kopje rezervë më parë). |
| `--surface` | asnjë | Lojërat e ralit (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ose `mixed`, shkruar te `meta.surface` i skedarit të xhiros. Pa të nuk shkruhet sipërfaqe. |

## Lojërat me një shikim {#the-games-at-a-glance}

| `--game` | Loja | Burimi | Porta e paracaktuar | Ndarja | `game` në skedar | Faqja |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (përfshirë 2023) | Data Out UDP | 5300 | numëruesi i xhirove të lojës (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, ose `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | memoria e përbashkët `acpmf_*` | - | numëruesi i xhirove (`CounterSplitter`) | `assetto-corsa` | [Lojërat Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | memoria e përbashkët `acpmf_*` | - | numëruesi i xhirove (`CounterSplitter`) | `assetto-corsa-competizione` | [Lojërat Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | memoria e përbashkët `acevo_pmf_*` | - | vija e startit (`LineSplitter`) | `assetto-corsa-evo` | [Lojërat Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | memoria e përbashkët `acpmf_*` | - | vija e startit / ndalimi (`LineSplitter`) | `assetto-corsa-rally` | [Lojërat Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struktura `wrc` | 20777 | ora e etapës (`StageSplitter`) | `ea-sports-wrc` | [Lojërat e ralit](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | ora e etapës (`StageSplitter`) | `dirt-rally-2` | [Lojërat e ralit](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | ora e etapës (`StageSplitter`) | `dirt-rally` | [Lojërat e ralit](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | ora e etapës (`StageSplitter`) | `dirt-4` | [Lojërat e ralit](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | ora e etapës (`StageSplitter`) | `richard-burns-rally` | [Lojërat e ralit](telemetry-rally.md) |
| `beamng` | BeamNG.drive | moda e protokollit `heat3d`, UDP | 4460 | vija e startit (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | shtesa Openplanet, skedarë CSV | - | për çdo vozitje, në shtesë | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | skedarët e vet `.ibt`, të lexuar nga shikuesi | - | numëruesi i xhirove të simulatorit | `iracing` | [iRacing](telemetry-iracing.md) |

## Gjendja {#status}

Regjistruesi i Forza është ai që është ushtruar më shumë. Regjistruesit Kunos, ralit, BeamNG dhe Trackmania
janë ndërtuar sipas strukturave të publikuara dhe testuar në paketa dhe faqe sintetike
të ndërtuara nga ato struktura (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`); **asnjëri prej tyre nuk është ekzekutuar ende kundrejt lojës së vërtetë**.
Regjistruesit që mund ta kontrollojnë hyrjen e tyre e bëjnë këtë ndërsa vijnë paketat dhe printojnë një `note:` një herë kur
diçka nuk përputhet (EA WRC dhe DiRT e krahasojnë shpejtësinë botërore me shpejtësinë;
EA WRC raporton edhe një paketë më të shkurtër se struktura standarde 237-bajtëshe). [Lojërat](games.md) liston burimet
dhe çfarë nuk është konfirmuar ende për çdo lojë.

## Ndërsa ekzekutohet {#while-it-runs}

- **Forza** printon një rresht gjendjeje një herë në sekondë: paketat e marra, dhe numrin e xhiros së hapur,
  numrin e kampioneve dhe metrat, ose `waiting for a race`. Çdo xhiro e përfunduar printon `wrote <file>`.
- **Lojërat Assetto Corsa** printojnë emrin e çdo skedari xhiroje ndërsa shkruhet.
- **Lojërat e ralit** printojnë `listening for <game> on port <port>`, pastaj `stage written: <file>`;
  me Ctrl+C një etapë e hapur mjaft e gjatë për t'u mbajtur shkruhet si `partial stage written: <file>`.
- **BeamNG** printon `lap written: <file>`, dhe me Ctrl+C `run written: <file>`.
- **Trackmania** nuk printon asgjë për çdo vozitje: shtesa i shkruan vetë skedarët e saj CSV.
- Në fund çdo regjistrues printon sa skedarë shkroi.

Një regjistrim Forza, këtu i ushqyer me paketa sintetike Data Out të një makine që vozit dy xhiro të një
rrethi 150 m (skedarët e xhirove, skedari anësor i papërpunuar dhe përmbledhja e vetëkontrollit që lë):

![telemetry që regjistron dy xhiro të një burimi sintetik Forza](../assets/img/telemetry-run.svg)

## Emrat e skedarëve {#file-names}

| Regjistruesi | Modeli |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Lojërat Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Lojërat e ralit, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, ku `<game>` është emri i gjatë (`ea-sports-wrc`, `beamng`, ...), `stage` për rali dhe `lap` për BeamNG |
| Shtesa Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` kundrejt `run` (Forza, Assetto Corsa) dhe prapashtesa `_partial` (rali, BeamNG) tregojnë
nëse xhiroja ose etapa u përfundua. Vula kohore është kur u shkrua skedari, jo
kur nisi xhiroja.

Pranë skedarëve të xhirove çdo regjistrues shkruan `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - çdo
paketë ose faqe që arriti, e mbajtur e plotë, edhe në meny dhe mes xhirove - dhe
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, vetëkontrollin: për çdo lloj pakete sa erdhën, sa
hynë në skedarët e xhirove, dhe `lost`, që është 0. Shikuesi i anashkalon të dyja kur ngarkohet një dosje.
Shih [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) në README.

## Fëmijët e kësaj faqeje {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Lojërat Assetto Corsa](telemetry-assetto-corsa.md)
- [Lojërat e ralit](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Ndarja e xhirove dhe e etapave](lap-splitting.md)
- [Rrëshqitja, drift-i dhe kanalet e nxjerra](slip-and-drift.md)
- [Skedari heat3d-lap](lap-format.md)
