---
title: "Gravadores de telemetria"
nav_order: 3
lang: "pt"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Gravadores de telemetria {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` grava cada canal que um jogo envia, divide o fluxo em voltas ou etapas e escreve um ficheiro JSON [`heat3d-lap`](lap-format.md) por volta numa pasta. O separador Análise de corrida do visualizador lê esses ficheiros. A gravação continua até premir **Ctrl+C**; a volta ou etapa que estiver aberta naquele momento é escrita se for longa o bastante para ser guardada (veja [Divisão de voltas e etapas](lap-splitting.md)).

Código: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
e os módulos em [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opções {#options}

| Opção | Padrão | Significado |
|---|---|---|
| `--game` | `forza` | Um destes: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Pasta onde os ficheiros de volta são escritos. Criada se não existir. Ignorada pelo `trackmania`, cujo plugin escreve os ficheiros por conta própria. |
| `--port` | `5300` | Porta UDP onde escutar. **Para todos os jogos exceto o Forza, o valor 5300 significa "a porta padrão do jogo"**: 20777 para o `wrc` e os jogos DiRT, 6776 para o `rbr`, 4460 para o `beamng`. Dê outro número para substituir. Não usada pelos jogos Assetto Corsa (memória partilhada) nem pelo Trackmania (ficheiros). |
| `--forward` | nenhum | Só Forza: `host:porta` para repassar cada pacote recebido, sem alteração. `127.0.0.1:5301` para o FH Companion. Um `:5301` sozinho significa `127.0.0.1:5301`. |
| `--install` | desligado | `beamng`: copia o mod de protocolo para os mods descompactados do BeamNG antes. `trackmania`: copia o plugin do Openplanet para a pasta de plugins do Openplanet. Ignorada pelos outros jogos. |
| `--configure` | nenhum | Só `wrc`: caminho para o `config.json` de telemetria do EA SPORTS WRC; liga o pacote `wrc` padrão antes de gravar (copiado antes como backup). |
| `--surface` | nenhum | Jogos de rali (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ou `mixed`, escrito em `meta.surface` do ficheiro de volta. Sem ele, nenhuma superfície é escrita. |

## Os jogos em resumo {#the-games-at-a-glance}

| `--game` | Jogo | Fonte | Porta padrão | Divisão | `game` no ficheiro | Página |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (incl. 2023) | Data Out UDP | 5300 | o contador de voltas do jogo (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, ou `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | memória partilhada `acpmf_*` | - | contador de voltas (`CounterSplitter`) | `assetto-corsa` | [Jogos Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | memória partilhada `acpmf_*` | - | contador de voltas (`CounterSplitter`) | `assetto-corsa-competizione` | [Jogos Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | memória partilhada `acevo_pmf_*` | - | linha de largada (`LineSplitter`) | `assetto-corsa-evo` | [Jogos Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | memória partilhada `acpmf_*` | - | linha de largada / parada (`LineSplitter`) | `assetto-corsa-rally` | [Jogos Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, estrutura `wrc` | 20777 | relógio de etapa (`StageSplitter`) | `ea-sports-wrc` | [Jogos de rali](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | relógio de etapa (`StageSplitter`) | `dirt-rally-2` | [Jogos de rali](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | relógio de etapa (`StageSplitter`) | `dirt-rally` | [Jogos de rali](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | relógio de etapa (`StageSplitter`) | `dirt-4` | [Jogos de rali](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | UDP do NGP | 6776 | relógio de etapa (`StageSplitter`) | `richard-burns-rally` | [Jogos de rali](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod de protocolo `heat3d`, UDP | 4460 | linha de largada (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin do Openplanet, ficheiros CSV | - | por corrida, no plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | seus próprios ficheiros `.ibt`, lidos pelo visualizador | - | o contador de voltas do simulador | `iracing` | [iRacing](telemetry-iracing.md) |

## Situação {#status}

O gravador do Forza é o mais testado. Os gravadores Kunos, de rali, BeamNG e Trackmania são construídos sobre os layouts publicados e testados com pacotes e páginas sintéticos montados a partir desses layouts (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **nenhum deles foi ainda executado contra o jogo ao vivo**. Os gravadores que conseguem verificar a própria entrada fazem isso conforme os pacotes chegam e imprimem uma `note:` uma vez quando algo não bate (o EA WRC e o DiRT comparam a velocidade do mundo com a velocidade; o EA WRC também reporta um pacote menor que a estrutura padrão de 237 bytes). [Jogos](games.md) lista as fontes e o que não está confirmado para cada jogo.

## Enquanto roda {#while-it-runs}

- **Forza** imprime uma linha de status a cada segundo: pacotes recebidos, e o número da volta aberta, a quantidade de amostras e os metros, ou `waiting for a race`. Cada volta terminada imprime `wrote <ficheiro>`.
- **Jogos Assetto Corsa** imprimem o nome de cada ficheiro de volta à medida que ele é escrito.
- **Jogos de rali** imprimem `listening for <jogo> on port <porta>`, depois `stage written: <ficheiro>`; com Ctrl+C, uma etapa aberta longa o bastante para ser guarda é escrita como `partial stage written: <ficheiro>`.
- **BeamNG** imprime `lap written: <ficheiro>`, e com Ctrl+C `run written: <ficheiro>`.
- **Trackmania** não imprime nada por corrida: o plugin escreve os seus ficheiros CSV por conta própria.
- No fim, cada gravador imprime quantos ficheiros escreveu.

Uma gravação do Forza, aqui alimentada com pacotes sintéticos do Data Out de um carro a dar duas voltas num círculo de 150 m (os ficheiros de volta, o sidecar bruto e o resumo de autoverificação que ela deixa):

![gravação de telemetria de duas voltas de um feed sintético do Forza](../assets/img/telemetry-run.svg)

## Nomes de ficheiro {#file-names}

| Gravador | Padrão |
|---|---|
| Forza | `<AAAA-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><número>_<segundos>s.lap.json` |
| Jogos Assetto Corsa | `<AAAA-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><número>_<segundos>s.lap.json` |
| Jogos de rali, BeamNG | `<jogo>_<AAAA-MM-DD_HH-MM-SS>_<stage|lap><número>_<segundos>s[_partial].json`, onde `<jogo>` é o nome longo (`ea-sports-wrc`, `beamng`, ...), `stage` para rali e `lap` para o BeamNG |
| Plugin do Trackmania | `run_<AAAA-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` contra `run` (Forza, Assetto Corsa) e o sufixo `_partial` (rali, BeamNG) marcam se a volta ou a etapa foi terminada. O carimbo de tempo é o momento em que o ficheiro foi escrito, não quando a volta começou.

Ao lado dos ficheiros de volta, todo gravador escreve `<AAAA-MM-DD_HH-MM-SS>_<jogo>.raw.parquet` - cada pacote ou página que chegou, guardado inteiro, nos menus e entre as voltas também - e `<AAAA-MM-DD_HH-MM-SS>_<jogo>.summary.json`, a autoverificação: por tipo de pacote, quantos chegaram, quantos foram para ficheiros de volta, e `lost`, que é 0. O visualizador ignora os dois quando uma pasta é carregada. Veja [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) no README.

## Páginas desta seção {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Jogos Assetto Corsa](telemetry-assetto-corsa.md)
- [Jogos de rali](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Divisão de voltas e etapas](lap-splitting.md)
- [Deslizamento, derrapagem e canais derivados](slip-and-drift.md)
- [O ficheiro heat3d-lap](lap-format.md)
