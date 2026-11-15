---
title: "O ficheiro heat3d-lap"
nav_order: 9
lang: "pt"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# O ficheiro `heat3d-lap` {#the-heat3d-lap-file}

Cada gravador de telemetria deste repositório escreve um ficheiro por volta ou etapa de rali, no mesmo formato, seja qual for o jogo. A exportação de percursos do [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) lê esse ficheiro para descobrir o jogo, o nível e a linha percorrida. Qualquer coisa que leia JSON consegue ler.

![Os campos e canais de um ficheiro de volta escrito a partir de um feed sintético do Forza](../assets/img/lap-file.svg)

## O documento {#the-document}

Um objeto JSON. Os canais são guardados como colunas: um array por canal, todos com o mesmo tamanho, uma entrada por amostra.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Campo | Significado |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | de qual jogo é a volta; veja a lista abaixo |
| `track` | o nome da pista, do trecho ou do mapa, quando o jogo o envia |
| `layout` | só no Forza: qual layout de pacote do Data Out foi decodificado |
| `car` | o que o jogo diz sobre o carro; livre |
| `lap` | o número da volta, o tempo dela como o jogo contou (ou o intervalo das amostras), se foi terminada e o seu comprimento |
| `meta` | como ler os números; veja abaixo |
| `units` | a unidade de cada canal presente, para um leitor que não conhece a tabela abaixo |
| `channels` | as amostras |
| `unparsed` | só no Forza, quando o pacote tem bytes que nenhum campo nomeia: `ranges` (os deslocamentos de byte `[início, fim)` no pacote) e `hex` (por amostra, esses bytes em hexadecimal), para que só o ficheiro contenha o pacote inteiro |

`game` é um destes: `forza-horizon`, `forza-motorsport`, `forza` (layout do pacote não diferenciado), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` diz o que os números significam onde os jogos diferem:

- `slip`: o que os canais de deslizamento contêm, quando o jogo envia algum - `peak` (normalizado, então acima de 1 o pneu perde a aderência: Forza), `scaled` (um deslizamento físico dividido por um pico típico de asfalto: os jogos Assetto Corsa), `physical` (uma fração e radianos), `index` (uma medida de deslizamento de 0 a 1: Trackmania);
- `discipline`: `circuit`, `rally` ou `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` ou `mixed`, quando conhecida (os gravadores de rali a tiram de `--surface`).

## Canais {#channels}

Um canal que o jogo não envia fica ausente, nunca preenchido com zeros. Canais por roda levam o nome da roda depois de um ponto: `.FL`, `.FR`, `.RL`, `.RR`.

As posições são o mundo do jogo, em metros, com `y` para cima. Um jogo cujo mundo é Z para cima é girado para Y para cima pelo seu gravador; nada mais é alterado, então um mundo canhoto (o do Forza) continua canhoto.

| Canal | Unidade | Significado |
|---|---|---|
| `time` | s | desde a primeira amostra da volta |
| `distance` | m | ao longo do trajeto percorrido desde a primeira amostra |
| `x`, `y`, `z` | m | posição; `y` é a altura |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedais e alavanca |
| `steer` | -1..1 | positivo para a direita |
| `gear` | | como o jogo conta |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | referencial do carro |
| `yaw`, `pitch`, `roll` | rad | rumo e atitude |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | velocidade no referencial do carro: direita, frente, cima |
| `bodySlip` | rad | ângulo de derrapagem, quando o jogo o envia |
| `loose` | 0/1 | em chão solto (Trackmania) |
| `airborne` | 0/1 | nenhuma roda no chão |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | como o jogo os envia |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | auxílios atuando, sistemas ligados |
| `absLevel`, `tcLevel` | | definições de auxílio |
| `brakeBias` | 0..1 | parcela da dianteira |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | por roda |
| `tirePressure` | psi | por roda |
| `tireWear` | 0..1 | por roda |
| `slipRatio`, `slipAngle`, `combinedSlip` | veja `meta.slip` | por roda |
| `slipIndex` | 0..1 | medida de deslizamento por roda (Trackmania) |
| `camber` | rad | por roda |
| `brakeTemp` | °C | por roda |
| `padLife`, `discLife` | | por roda |
| `suspensionM` | m | curso da roda |
| `suspension` | 0..1 | curso da roda, da faixa que esta volta usou |
| `wheelLoad` | N | por roda |
| `wheelSpeed` | rad/s | rotação por roda |
| `wheelSurfaceSpeed` | m/s | velocidade do ponto de contacto por roda |
| `groundContact` | 0/1 | por roda |
| `rumble`, `surfaceRumble` | | por roda: sobre uma zebra; a rugosidade da superfície |
| `puddle` | | por roda, profundidade de água parada |

Um gravador pode acrescentar canais próprios com outros nomes; um leitor mantém o que não conhece.

Nenhum dos jogos de rali envia o deslizamento dos pneus. Um leitor pode calculá-lo a partir da velocidade do ponto de contacto ou da superfície de cada roda em relação à velocidade do carro, `(roda - carro) / carro`, ou a partir da rotação e de um raio de deslocação medido na própria volta, quando só a rotação é enviada. O ângulo de derrapagem vem da velocidade do próprio carro (`latVel`, `longVel`), quando ela é enviada, ou da velocidade do mundo projetada nos eixos do carro.

## A forma CSV {#the-csv-form}

O plugin do Trackmania escreve `heat3d-lap-csv` no lugar: uma primeira linha com `# ` e um objeto JSON (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), uma linha com os nomes dos canais e, depois, uma linha por amostra. Os nomes dos canais são os mesmos de cima.

## O que cada gravador escreve de facto {#what-each-recorder-actually-writes}

O formato acima é o contrato; os gravadores o preenchem de forma um pouco diferente, e um leitor deve tolerar todas estas variações (verificado contra o código):

| Gravador | `track` | `layout` | `meta` | `units` | Canais além da tabela |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (o número de pista do Forza Motorsport 2023 é `lap.trackOrdinal`) | o layout de pacote detetado | `slip: peak`, `discipline: circuit` | só as unidades dos canais presentes | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, o relógio do jogo `timestampMs`, `raceTime`, `bestLap`, `lastLap`; a velocidade no referencial do carro fica sob os nomes canónicos `latVel`, `vertVel`, `longVel`; `unparsed` ao lado dos canais |
| Jogos Assetto Corsa (`kunos.py`) | da página estática, ou `null` | ausente | `slip: scaled`, `discipline: circuit` ou `rally` | uma lista fixa | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (como enviado), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Jogos de rali (`rally.py` via `lapfile.py`) | `null` | ausente | `discipline: rally`, `slip: null`, `surface` só quando `--surface` foi dado (senão o visualizador infere) | só as unidades dos canais presentes | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` para os floats sem nome definido; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` via `lapfile.py`) | `null` | ausente | `discipline: circuit` | só as unidades dos canais presentes | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Plugin do Trackmania (CSV) | o nome do mapa | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` é o bloco de carro do Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` para os jogos Kunos quando a página estática traz um nome, e `{}` nos demais casos. `lap.metres` é a diferença da distância percorrida do contador do jogo no Forza, e a soma das distâncias 3D entre amostras nos demais. Os valores são arredondados ao gravar: `time` com 4 casas decimais, `distance` com 3, os outros floats com 5. O JSON é gravado compacto (sem espaços).

Todo pacote ou página que o gravador recebeu - não só os das voltas - é guardado inteiro ao lado dos ficheiros de volta em `<carimbo>_<jogo>.raw.parquet`, com uma autoverificação em `<carimbo>_<jogo>.summary.json` (a seção "Completeness" do README).

Uma amostra para a qual um canal não tem valor - ausente naquele quadro, ou não um número finito como o jogo o enviou - é escrita como `null` por todos os gravadores (`lapfile.clean`), e a fração de suspensão derivada dela também é `null`. `NaN` e `Infinity` nunca são escritos: não são JSON, e o `JSON.parse` do navegador recusa o ficheiro inteiro por causa de um deles. Um leitor deve esperar `null` dentro do array de um canal.

Os ficheiros do Forza trazem `"game": "forza-horizon"`, `"forza-motorsport"` ou `"forza"`, conforme o layout detetado. O leitor do visualizador para os ficheiros `.tele.gz` do FH Companion produz voltas com `"game": "forza-horizon"` e `meta.slip = "peak"`; esse leitor está no visualizador, não aqui. As voltas do iRacing (lidas de `.ibt` no visualizador) trazem `"game": "iracing"`, que não está na lista de valores `game` dos gravadores acima, porque nenhum gravador o escreve.

Veja [Divisão de voltas e etapas](lap-splitting.md) para saber como `lap.number`, `lap.seconds` e `lap.complete` são decididos, e [Deslizamento, derrapagem e canais derivados](slip-and-drift.md) para o que o visualizador deriva a partir destes canais.
