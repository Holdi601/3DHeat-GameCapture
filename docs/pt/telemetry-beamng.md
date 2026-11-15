---
title: BeamNG.drive
nav_order: 4
lang: "pt"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copy the mod, then record
python -m heat3d_capture telemetry --game beamng -o laps      # record
```

Depois, no jogo, em **Options > Other > Protocols**, ative **"others"**.

Código: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py) e o mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua). Testes: `tests/test_beamng.py`, sobre pacotes construídos a partir da estrutura do mod. **O mod ainda não foi executado no jogo.**

## Porque um mod {#why-a-mod}

O BeamNG envia telemetria através de "protocolos": módulos Lua no veículo que o próprio `lua/vehicle/protocols.lua` do jogo empacota e envia por UDP a partir do carro que o jogador conduz. Os de série não trazem o que uma análise de controlo do carro precisa - o OutGauge não tem posição, o MotionSim não tem rodas, e o OutSim é um esboço sem conteúdo nas versões atuais. Por isso, este projeto traz o seu próprio protocolo, `heat3d`. Não toca em nada fora do Lua do próprio veículo.

## Instalação {#installing}

O `--install` copia `mods/beamng/heat3d` para `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (a partir do BeamNG 0.30 os mods do utilizador ficam lá), apagando primeiro uma cópia mais antiga, e indica para onde foi. Sem `LOCALAPPDATA` recorre à pasta pessoal. Também pode copiar a pasta manualmente.

Depois de `--install`, a gravação começa logo a seguir.

## O mod {#the-mod}

| Definição (em `heat3d.lua`) | Valor |
|---|---|
| Endereço | `127.0.0.1` |
| Porta | `4460` - altere-a aqui e passe o mesmo `--port` ao gravador |
| Taxa máxima de atualização | 100 Hz |
| Passo de física | usado (`isPhysicsStepUsed` devolve verdadeiro) |

Cada pacote é o marcador de 4 bytes `H3D1` seguido de 39 floats em little-endian (160 bytes no total):

| Campo | Quantidade | Origem no Lua do veículo |
|---|---|---|
| `time` | 1 | o relógio do próprio mod: soma dos passos de física, zerado quando o veículo é reposicionado |
| posição | 3 | `obj:getPositionXYZ()` |
| velocidade | 3 | `obj:getVelocityXYZ()` (mundo) |
| frente | 3 | `obj:getDirectionVector()` |
| cima | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, e 1/0 a partir de `absActive` e `tcsActive` |
| `wheelSpeed` | 4 | velocidade de superfície de cada roda (m/s) |
| `wheelAngular` | 4 | velocidade angular vezes a direção da roda (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 quando fora do chão |

As quatro rodas são escolhidas pelo **lugar onde estão no carro**, e não pelo nome (os nomes diferem entre veículos): à frente ou atrás pela posição do nó ao longo do carro, à esquerda ou à direita através dele (referencial do veículo +X à esquerda, -Y para a frente), ficando, para cada canto, com a roda mais afastada do centro. Um canto em falta é enviado com zeros e material -1.

## O que o gravador faz com isto {#what-the-recorder-does-with-it}

O mundo do BeamNG tem Z para cima; o do visualizador tem Y para cima. As posições e os vetores são rodados em torno de X, `(x, y, z) -> (x, z, -y)`, o que mantém a lateralidade do mundo. Depois:

| Canal | Derivado como |
|---|---|
| `x`, `y`, `z` | posição rodada |
| `speed` | comprimento da velocidade rodada |
| `longVel`, `latVel`, `vertVel` | velocidade projetada na frente, na direita = frente x cima, em cima |
| `longAcc`, `latAcc`, `vertAcc` | a variação da velocidade no mundo ao longo de ±2 amostras, projetada nos mesmos eixos (o referencial dos sensores do próprio carro não está documentado, por isso não são usados) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | como enviado |
| `absActive`, `tcActive` | as luzes de ABS e TC, onde o carro as tem |
| `wheelSurfaceSpeed.*` | valor absoluto da velocidade de superfície da roda |
| `wheelSpeed.*` | rotação |
| `wheelLoad.*` | carga |
| `groundContact.*` | 0 quando o material é negativo, senão 1 |

Os pacotes sem o marcador ou com menos de 160 bytes são ignorados.

## Voltas {#laps}

O `LineSplitter`, como para o AC EVO: o ponto onde a gravação começou é a linha; uma volta se fecha onde o carro volta a passar mais perto dela, no mesmo sentido, pelo menos 300 m depois; uma corrida se fecha quando o carro fica parado durante 8 segundos. Uma volta só conta como completa se começou acima de 5 m/s, por isso a primeira volta a partir de parado é parcial. Quando o relógio do mod recua mais de meio segundo (o carro foi reposicionado), a corrida aberta nesse momento é fechada primeiro - escrita como corrida parcial quando cobriu pelo menos 300 m, como no fim de uma gravação - e depois o divisor recomeça. Ver [Divisão de voltas e etapas](lap-splitting.md).

## O ficheiro de volta {#the-lap-file}

`game` é `beamng`, `meta` é `{"discipline": "circuit"}`, os ficheiros têm o nome `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Não é escrito deslizamento; o visualizador o deriva das velocidades de superfície das rodas (ver [Deslizamento, derrapagem e canais derivados](slip-and-drift.md)). As posições estão no mesmo referencial que a exportação de cursos do BeamNG do GameFiles escreve, por isso uma volta gravada assenta num percurso exportado.
