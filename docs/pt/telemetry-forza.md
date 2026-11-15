---
title: "Forza"
nav_order: 1
lang: "pt"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon e Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # jogo -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # e o FH Companion continua a funcionar
```

Código: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(deteção de layout),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(todos os canais, ficheiros de volta, repasse).

## Ligando no jogo {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, porta `5300` (ou o que for passado em `--port`). O Forza Motorsport também oferece um formato de pacote: precisa de ser **Dash**, não Sled. O Sled não traz posição nenhuma, e o gravador o recusa.

O gravador liga-se a `127.0.0.1`, então o jogo precisa de correr no mesmo PC.

## O que o jogo envia, e como o layout é encontrado {#what-the-game-sends-and-how-the-layout-is-found}

O Data Out é um pacote UDP por tick de simulação (cerca de 60 por segundo), uma struct C plana little-endian nestes tamanhos:

| Tamanho | Variante |
|---|---|
| 232 bytes | "Sled" do Motorsport: sem posição. Recusado com uma mensagem a pedir que se troque para Dash. |
| 311 bytes | "Dash" do Motorsport: o bloco Sled mais o bloco dash de 79 bytes |
| 324 bytes | "Dash" do Horizon: o mesmo, com preenchimento entre os dois blocos |
| 331 bytes | Forza Motorsport (2023): Dash mais 20 bytes de desgaste dos pneus e o id da pista |

O bloco Sled (deslocamentos 0-231) é estável. Onde começa o bloco dash na variante do Horizon é descrito de forma inconsistente nas fontes publicadas, e errar o início não falha - produz floats plausíveis dos campos errados. Então o início é **descoberto**:

1. Os inícios candidatos são testados na ordem: `tamanho - 79` (o bloco dash vai até ao último byte em toda variante documentada), 232, 244, e 232 a 260 em passos de 4.
2. Cada candidato é pontuado em pacotes de um carro em movimento (uma componente de velocidade acima de 1 m/s): o vetor de velocidade do bloco Sled e o escalar `Speed` do bloco dash são a mesma grandeza em dois lugares, então `| |velocidade| - Speed |` fica perto de zero só para o início certo.
3. O candidato com a menor discordância no pior caso vence, se essa discordância for de no máximo **1 m/s**. Senão a deteção continua esperando.

Enquanto o carro está parado, todo candidato lê zero e todos concordam, o que não prova nada, então **a deteção espera o carro se mover**: dirija alguns metros antes de esperar pela saída. Até 600 pacotes ficam retidos enquanto se espera (cortados para os últimos 300). Uma vez conhecido o layout, os pacotes retidos também são decodificados, para que o começo da primeira volta não se perca. Pacotes de tamanho diferente do layout detetado, pacotes menores que 311 bytes e pacotes com posição ou velocidade não finitas são ignorados para os ficheiros de volta.

O jogo exato depende do layout: um layout de Horizon dá `"game": "forza-horizon"`, um layout de Motorsport ou de 331 bytes dá `"forza-motorsport"`, qualquer outro `"forza"`. O nome do layout detetado (`Horizon dash`, `Motorsport dash`, `331-byte dash`) é escrito como `layout`.

## Canais gravados {#channels-recorded}

Cada campo do pacote é decodificado (`decode_full`) e convertido:

- os pedais `throttle`, `brake`, `clutch`, `handbrake` de 0..255 para 0..1;
- `steer` de -127..127 para -1..1; `drivingLine` e `aiBrakeDifference` da mesma forma, divididos por 127;
- `tireTemp.FL` ... `.RR` de Fahrenheit para Celsius;
- `latAcc`, `longAcc`, `vertAcc` e `yawRate` são cópias de `accelX`, `accelZ`, `accelY` e `angVelY` sob os nomes canónicos (referencial do carro: x para a direita, y para cima, z para a frente);
- a velocidade do Sled, que está no referencial do próprio carro (x para a direita, y para cima, z para a frente - não o do mundo), é escrita diretamente sob os nomes canónicos `latVel`, `vertVel` e `longVel`, para que o visualizador leia o ângulo de derrapagem dela em vez de estimá-lo a partir do rumo e do trajeto.

Os canais do ficheiro de volta são todos esses, exceto os campos por volta:

| Grupo | Canais |
|---|---|
| Tempo e lugar | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Movimento | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Piloto | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Por roda (`.FL .FR .RL .RR`) | `suspension` (0 estendida .. 1 comprimida), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizados: acima de 1 o pneu perde a aderência), `wheelSpeed` (rad/s), `rumble` (sobre uma zebra), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Só Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` é o cronómetro da volta atual do jogo menos o seu valor na primeira amostra da volta; `distance` é a distância percorrida do jogo menos o seu primeiro valor. As posições são as coordenadas do mundo do Forza em metros, sem alteração (y é para cima; o mundo é canhoto).

Gravados uma vez por volta, e não por amostra, sob `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. O id da pista do FM2023 entra também uma vez, como `lap.trackOrdinal`. Não guardados por amostra: `isRaceOn` (1 em todo quadro de uma volta). `timestampMs`, `raceTime`, `bestLap` e `lastLap` são guardados como canais.

O resto do documento é preenchido como o de todos os outros gravadores:

- `"track": null` - o Forza Horizon não nomeia o percurso, e o Forza Motorsport só o numera;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - os canais de deslizamento são normalizados para que, acima de 1, o pneu perca a aderência;
- `units` lista só os canais que o ficheiro tem (os canais por roda pelo nome base);
- um valor que não é um número finito é escrito como `null`, nunca como `NaN`.

Veja [O ficheiro heat3d-lap](lap-format.md).

## Como as voltas são divididas {#how-laps-are-split}

`LapSplitter` (veja [Divisão de voltas e etapas](lap-splitting.md)): uma volta fecha quando o contador de voltas do jogo avança, e o seu tempo é então o `lastLap` do próprio jogo (o que o jogo mostra). Uma corrida ponto a ponto, ou uma sessão que termina no meio de uma volta, fecha quando o jogo sai da corrida (`isRaceOn` cai), quando os pacotes param por 2 segundos, ou quando o timestamp do jogo volta para trás; é mantida como `run` se cobriu pelo menos 400 m.

## Repassando para o FH Companion {#relaying-to-fh-companion}

O jogo envia o Data Out para um só endereço. Com `--forward host:port`, o gravador repassa **cada pacote que recebe sem alteração**, antes de decodificar qualquer coisa (também enquanto ainda espera a deteção do layout), para que outra aplicação que lê o feed continue a funcionar: configure o jogo para 5300, a outra aplicação para 5301, e execute com `--forward 127.0.0.1:5301`.

O FH Companion é uma aplicação separada, não faz parte do 3DHeat. Ele mantém uma biblioteca de voltas em `%LOCALAPPDATA%\FHCompanion\laps`: uma pasta por percurso, um ficheiro de volta por volta amostrado a cada cinco metros e, ao lado de cada ficheiro de volta, `<volta>.json.tele.gz`, todo o Data Out da volta na taxa do jogo. O 3DHeat lê os dois:

- **O visualizador lê o `.tele.gz` diretamente** quando o solta (com ou sem o ficheiro de volta) no separador Análise de corrida. Ele mapeia os nomes de campo do próprio Forza (`PositionX`, `VelocityX`, `TireSlipRatio` + roda, ...) para os canais canónicos, transforma o `VelocityX/Y/Z` no referencial do carro em `latVel`, `vertVel`, `longVel`, converte as temperaturas dos pneus de Fahrenheit, descarta linhas que repetem a anterior exceto pelo relógio do gravador, e marca o deslizamento como `peak`. Dado também o ficheiro de volta, a volta obtém dele o carro e o tempo. Esse leitor fica no visualizador (`src/race/adapters.ts`, `readForzaTelemetry`), não neste repositório.
- **O comando `laps`** lê a biblioteca de voltas e escreve a rota de um percurso e um CSV de cada amostra; veja [Referência de comandos](commands.md#laps).

## Outros usos do mesmo feed {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` grava só as posições, guardadas a cada dois segundos enquanto conduz; veja [Referência de comandos](commands.md#route).
- A opção "Racing telemetry (Forza)" da janela de digitalização usa o feed como poses exatas da câmara para a reconstrução; veja [Pose da câmara e escala](reconstruction-pose.md#telemetry-poses).

## Notas e ressalvas {#notes-and-caveats}

- Não está documentado em relação a que o Forza normaliza o deslizamento. `1` é lido como a borda da aderência, mas o visualizador mede onde a aderência de cada carro realmente cai.
- A velocidade do Sled está no referencial do carro, como diz a documentação do Data Out do Forza e como confirmam as voltas gravadas (a componente para a frente carrega a velocidade, a lateral fica perto de zero). A deteção de layout usa só o seu tamanho, que é o mesmo em qualquer quadro.
- As posições são o mundo do jogo, Y para cima e canhoto. Os sentidos de `yaw`, `pitch` e `roll` foram conferidos em voltas gravadas: a guinada é igual à direção de movimento `atan2(dx, dz)`, uma arfagem positiva é nariz para baixo, e uma deslocação positiva abaixa o lado direito.
