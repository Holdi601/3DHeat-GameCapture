---
title: Referência de comandos
nav_order: 5
lang: "pt"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Referência de comandos {#command-reference}

Todos os comandos são executados a partir da pasta do repositório, com o ambiente do projeto:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Comando | Faz |
|---|---|
| [`route`](#route) | Regista só as posições de uma volta do Forza, para encontrar o mapa nos ficheiros do jogo |
| [`telemetry`](#telemetry) | Regista todos os canais, um ficheiro de volta por volta, para o separador Análise de corrida |
| [`laps`](#laps) | Lê uma biblioteca de voltas do FH Companion e escreve o percurso e as amostras de um circuito |
| [`reconstruct`](#reconstruct) | Resolve uma gravação offline e escreve um `.glb` |
| [`hud`](#hud) | Lê as ações do próprio jogador, as mortes e o trajeto no minimapa, e o feed de abates, a partir de uma gravação |
| [`locate`](#locate) | Onde foi tirado cada quadro de uma gravação, comparado com renderizações do nível |
| [`python -m heat3d_capture.ui`](#the-scan-window) | A janela de digitalização |
| [`python -m heat3d_update`](#updates) | Verifica e aplica uma atualização |
| [`python tools/export_onnx.py`](#the-model-converter) | Converte o modelo de profundidade para ONNX |

Quando é iniciado como `python -m heat3d_capture`, a ferramenta verifica primeiro se há uma versão
mais recente (ver [Atualizações](updates.md); `HEAT3D_NO_UPDATE=1` desliga isto). `--help` depois de
qualquer verbo lista as suas opções:

![heat3d_capture --help](../assets/img/cli-help.svg)

Código: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Escuta o Forza Data Out e guarda só as posições do carro, mais nada: sem modelo de profundidade, sem
GPU, sem captura. Código: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opção | Padrão | Significado |
|---|---|---|
| `-o`, `--out` | obrigatório | Caminho de saída; o sufixo é substituído, por isso `-o lap` escreve `lap.npz` e `lap.json`. |
| `--port` | `5300` | Porta para a qual o jogo envia (ligada a 127.0.0.1). |
| `--seconds` | `0` | Para depois deste número de segundos; `0` corre até ao Ctrl+C. |

Uma posição só é guardada enquanto o jogo indica uma corrida (`isRaceOn`), o carro se move a mais de
0,5 m/s e está a pelo menos 0,5 m da última posição guarda - caso contrário, estar parado num menu a
60 pacotes por segundo encheria o ficheiro com a linha de largada. O tempo de cada amostra é o tempo de
corrida do jogo, ou o relógio de parede quando esse é 0. O layout é detetado exatamente como em
`telemetry` (o carro precisa se mover primeiro; ver [Forza](telemetry-forza.md)).

Uma vez por segundo imprime os pacotes recebidos, as posições guardadas e a posição atual, ou
`nothing on port 5300 yet - is Data Out on?` (ainda nada na porta 5300 - o Data Out está ligado?). O
percurso é **guardado enquanto é conduzido**: a cada 2 segundos, assim que chegou uma nova posição (o
intervalo cresce até vinte vezes o tempo que a última gravação levou, para que uma sessão muito longa
nunca gaste mais de um vigésimo do seu tempo a escrever), e mais uma vez quando o gravador para por
qualquer motivo - Ctrl+C, `--seconds` ou uma exceção. Cada gravação escreve `lap.npz.partial` /
`lap.json.partial` e depois substitui o ficheiro real, por isso os ficheiros em disco estão sempre
completos; uma falha ou um processo morto perde no máximo os últimos segundos. Se nada foi guardado,
indica como ligar o Data Out e termina com o código 1.

Saída:

- `lap.npz` - matrizes NumPy `positions` (n x 3, metros), `times`, `speeds` (m/s);
- `lap.json` - legível sem este projeto:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

As posições são as próprias coordenadas do mundo do jogo, e é isso que as torna uma forma de encontrar o
mesmo terreno nos ficheiros do jogo: o comando `course` do
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) recebe este JSON e exporta o percurso
que a volta cobriu.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Todas as opções e jogos estão descritos em [Gravadores de telemetria](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Lê a biblioteca de voltas que o FH Companion guarda e escreve dois ficheiros para um circuito: um
percurso que indica qual trecho do mapa recortar do ficheiro do jogo, e uma tabela de cada amostra de cada
volta. São escritos juntos para que não possam ficar dessincronizados. Código:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opção | Padrão | Significado |
|---|---|---|
| `course` | nenhum | Nome do circuito, com correspondência aproximada. Omita para listar a biblioteca. |
| `-o`, `--out` | o nome do circuito, em minúsculas, espaços como `_` | Caminho de saída; `.json` e `.csv` são escritos lado a lado. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Onde estão as pastas dos circuitos. |
| `--margin` | `80` | Metros acrescentados em volta da extensão do circuito em x e z, no `bounds` do percurso. |

### Listagem {#listing}

Sem um circuito, imprime o número de pastas de circuitos e, para cada uma, o número de ficheiros de
voltas (`*.json` em qualquer nível abaixo dela, exceto `course.json`) e o nome do circuito, depois
`Name one to write it out:  -o <file> <course>` (indique um nome para escrevê-lo: `-o <ficheiro> <circuito>`).

### Encontrar um circuito {#finding-a-course}

As pastas dos circuitos têm o nome `<name> (course_<x>_<z>_to_<x>_<z>)` - o início e o fim, arredondados.
Um circuito é encontrado, por esta ordem, por: o nome exato da pasta; a parte do nome da pasta, sem
distinguir maiúsculas; uma pasta única cujo nome contém o texto. Vários resultados geram um erro que os
lista.

### Leitura {#reading-it}

- `course.json` na pasta, quando é legível, dá o nome e o início e fim não arredondados (`Name`,
  `StartX`, `StartZ`, `FinishX`, `FinishZ`); caso contrário, estes vêm do nome da pasta. Um circuito é
  indicado como circuito fechado quando o início e o fim estão a menos de 10 m um do outro.
- Cada outro `*.json` abaixo da pasta é uma volta (as voltas ficam várias pastas abaixo - por classe,
  carro, afinação, rótulo - e a pesquisa é simplesmente recursiva). Os ficheiros são lidos como UTF-8
  com marca de ordem de bytes. Uma volta ilegível é ignorada. As voltas são ordenadas pelo seu tempo de
  gravação.
- Por volta: `Lap.samples` (cada uma com `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), e a classe do carro,
  o ordinal, o índice de desempenho, os segundos da volta, o comprimento, o tempo de gravação e a largada
  parada.

Imprime um resumo (voltas, amostras, a melhor volta e a sua classe, a extensão x/y/z).

### Saída {#output}

**`<out>.json`** - a mesma forma de percurso que `route` escreve, para que o extrator de mapas aceite
qualquer um: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (alargado por `--margin` em x e
z) e `positions` da volta **mais rápida** (uma linha, em vez de um borrão com todas as voltas).

**`<out>.csv`** - cada amostra de cada volta, uma linha por amostra:

| Coluna | Significado |
|---|---|
| `course` | nome do circuito |
| `lap` | um rótulo por volta: data e hora da gravação, até ao minuto, e o tempo da volta |
| `car` | ordinal do carro |
| `car_class` | letra da classe de desempenho |
| `pi` | índice de desempenho |
| `lap_seconds` | o tempo da volta |
| `speed_kmh` | velocidade em km/h |
| `x`, `y`, `z` | posição no mundo, em metros, 3 decimais |
| `speed_ms` | velocidade, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | como o FH Companion os regista |
| `metres` | distância ao longo da volta, 3 decimais |
| `elapsed` | segundos desde o início da própria volta, 3 decimais |

Os valores que não são posições são escritos com 4 algarismos significativos; as posições têm casas
decimais fixas, porque 4 algarismos significativos encaixariam um circuito numa grade de um metro. Os
nomes das colunas são escolhidos para que o visualizador mapeie o ficheiro sem lhe dizerem nada: `lap`
torna-se a sessão (duas voltas feitas pelo mesmo carro nunca são juntas), `car` a coisa que se move,
`car_class` o grupo pelo qual colorir, `elapsed` o eixo do tempo (cada volta alinha no seu próprio
início).

No fim imprime uma dica para recortar o mapa do jogo com o GameFiles, com o ficheiro do percurso ou uma
caixa explícita.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Reconstrói uma gravação offline, com o caminho da câmara resolvido de uma só vez pelo VGGT. Lento:
minutos por janela numa GPU de desktop. Precisa de PyTorch, do `transformers` do Hugging Face e do pacote
`vggt`, que o digitalizador não precisa: estão listados em `requirements-offline.txt`, e o comando os verifica
depois de imprimir a linha da licença e se oferece para instalar o que falta (código de saída 1 se
recusar). Descrição completa: [Reconstrução offline](reconstruction-offline.md).

| Opção | Padrão | Significado |
|---|---|---|
| `video` | obrigatório | A gravação. Código de saída 2 se não existir. |
| `-o`, `--out` | obrigatório | O `.glb` a escrever. |
| `--solve-budget` | `260` | Máximo de quadros entregues ao solucionador. São espaçados pelo quanto a imagem se move, não pelo relógio. Mais é mais preciso e muito mais lento. Mais de 400 quadros planeados são recusados. |
| `--fuse-interval` | `0.4` | Segundos entre os quadros fundidos em geometria. |
| `--model` | `vggt-1b` | Com que pesos VGGT resolver: `vggt-1b` (`facebook/VGGT-1B`, não comercial) ou `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, com acesso restrito; precisa de autorização da Meta). A linha de licença impressa primeiro é a desse modelo. |

Imprime primeiro a linha de licença do modelo, depois cada etapa (`masking`, `planning`, `solving`,
`fusing`, `exporting`) com os segundos decorridos e o progresso, e por fim um resumo: câmaras resolvidas,
erro de fecho, pior junção, notas e o ficheiro escrito. O código de saída é 0 só se um ficheiro foi escrito.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Lê o HUD do jogo a partir da gravação do próprio jogador, depois da partida: as ações do próprio jogador
do popup de pontos, as mortes e as reanimações dos ecrãs de abatido e de implantação, o trajeto no
minimapa e o feed de abates. Escreve `<out>.parquet` (trajeto e eventos, uma tabela do 3DHeat),
`<out>.events.jsonl`, `<out>.summary.json`, e `<out>.map.png` + `.map.json` (o mosaico do minimapa e as
suas âncoras para a imagem de mapa do visualizador). Battlefield 6 (`bf6`) é, por agora, o único perfil.

Precisa de **ffmpeg e ffprobe** no PATH (`winget install Gyan.FFmpeg`, e depois um terminal novo).

| Opção | Padrão | Significado |
|---|---|---|
| `video` | obrigatório | A gravação. |
| `-o`, `--out` | o nome do vídeo | Caminho de saída sem extensão. |
| `--game` | `bf6` | Qual HUD será lido. |
| `--player` | adivinhado | O nome do jogador como o feed de abates o mostra, com correspondência aproximada. |
| `--fps` | `5` | Amostras do minimapa por segundo. |
| `--start`, `--seconds` | vídeo inteiro | A parte da gravação a ler. |
| `--metres-per-pixel` | nenhum | A escala do minimapa, quando se conhece; sem ela as posições ficam em pixels do minimapa. |
| `--cpu` | desligado | Decodifica na CPU mesmo quando há uma placa NVIDIA. |

Descrição completa: [Ler o HUD de uma gravação](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderiza um nível a partir de cada lugar onde um jogador pode estar e indexa as renderizações;
`frames` situa cada quadro amostrado de uma gravação contra ele, pela imagem, com o trajeto no
minimapa do comando `hud` como alternativa; `eval` compara um resultado com poses de câmara conhecidas;
`train` treina um modelo de lugares por mapa a partir de renderizações do nível (e de quadros que uma
execução já localizou), para `build --head`; `refmap` situa o mapa do próprio jogo (a sua ecrã de
implantação) sobre o nível, e `minimap` lê o minimapa de uma gravação contra ele, quadro a quadro -
o que `frames --minimap` pode receber antes. Precisa de PyTorch e de `requirements-locate.txt`.
**Experimental:** em gravações reais, até agora só localiza uma pequena parte dos quadros. Todas as
opções, as saídas e o método: [Localizar quadros num nível](locate.md); a lista completa de opções:
[Referência de comandos](../cli-reference.md).

## A janela de digitalização {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ou faça duplo clique em `scan.bat`. Sem opções. Ver [A janela de digitalização](reconstruction-scan-ui.md).

## Atualizações {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Ver [Atualizações](updates.md).

## O conversor de modelos {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Converte um ponto de controlo do Depth Anything V2 para o ficheiro ONNX que o digitalizador executa.
Precisa de PyTorch, `transformers` e `onnxscript`. Ver [Profundidade](reconstruction-depth.md#building-the-model).
