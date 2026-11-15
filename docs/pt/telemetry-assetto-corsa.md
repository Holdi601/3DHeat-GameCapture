---
title: "Jogos Assetto Corsa"
nav_order: 2
lang: "pt"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO e AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Código: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testes: `tests/test_kunos.py` (páginas sintéticas). Ainda não executado contra os jogos ao vivo.

## De onde vêm os dados {#where-the-data-comes-from}

Os jogos da Kunos publicam telemetria para aplicações como **páginas de memória partilhada do Windows com nome** que o jogo escreve e que qualquer um pode ler. O gravador as abre somente leitura (`mmap` com um nome de tag), então ele precisa de correr **no PC em que o jogo corre**, no Windows; em outro lugar, ele encerra com uma mensagem. As páginas são abertas uma única vez, quando o gravador inicia. Iniciar o jogo e entrar no carro primeiro é a ordem segura; se começar pelo gravador antes do jogo funciona não foi verificado.

| `--game` | Página de física | Página de gráficos (contador de voltas) | Página estática (nomes) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | não usada | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | não usada | `Local\acevo_pmf_static` |

A página de física é lida 200 vezes por segundo (`hz=200`); uma nova amostra é tomada apenas quando o seu `packetId` mudou e não é zero. Os primeiros 800 bytes da página de física têm o mesmo layout nos quatro jogos; a página do primeiro jogo só tem garantidos 580 bytes, então, se um mapeamento de 800 bytes não puder ser aberto, o gravador recorre a 580, e os campos além disso ficam ausentes.

## Posição {#position}

Nenhuma das páginas traz uma posição do carro como tal, mas a página de física guarda **o ponto de contacto de cada pneu em coordenadas do mundo** (deslocamento 420, quatro tríades XYZ). A posição do carro é a média dos quatro. Uma página cujos pontos de contacto são todos zero (menu, garagem) não produz amostra.

## Canais {#channels}

| Canal | De | Observações |
|---|---|---|
| `time` | o relógio do próprio gravador | segundos desde o início da gravação, recalculados para a primeira amostra da volta |
| `x`, `y`, `z` | média do ponto de contacto dos pneus | metros do mundo |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | as unidades do jogo, escaladas por volta para -1..1 pelo maior valor absoluto que a volta usou, **somente se** esse valor for maior que 1,05 (uma entrada já em -1..1 fica intacta) |
| `gear` | `gear - 1` | o jogo conta 0 marcha a ré, 1 ponto morto, 2 primeira; escrito como -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, vezes 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | velocidade local no deslocamento 568 | referencial do carro; só quando não é zero. Para qual lado aponta o x é documentado nos dois sentidos, então leia o tamanho do ângulo de derrapagem, não o sinal |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | deslocamento 564 | só na página de 800 bytes |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: deslocamentos 204 e 252, escritos como 1 quando acima de 0; AC: `tcInAction`/`absInAction` da página de 800 bytes, quando presente | auxílios atuando |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | derivado | 0..1 do curso que essa volta usou (mínimo a máximo de `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | deslocamentos 640, 656 (página de 800 bytes) | divididos por um pico típico - veja abaixo |
| `slipRatioRaw.*`, `slipAngleRaw.*` | o mesmo | os valores físicos, sem escala |
| `padLife.*`, `discLife.*` | deslocamentos 740, 756 | só na página de 800 bytes |

O AC Rally envia as suas temperaturas de pneu e travão em kelvin: para `--game acrally`, qualquer um desses valores acima de 200 tem 273,15 subtraído.

`wheelSlip` (deslocamento 56) é decodificado, mas não escrito.

## Escala do deslizamento {#slip-scaling}

O Forza envia o deslizamento normalizado para que 1 seja a borda da aderência. A Kunos envia a razão de deslizamento física e o ângulo de deslizamento. Então o gravador os divide por um pico típico de asfalto - **0,12** para a razão de deslizamento e **0,14 rad (cerca de 8 graus)** para o ângulo de deslizamento - para que a leitura "acima de 1 significa a deslizar" do visualizador valha aproximadamente, mantém os valores brutos ao lado, e escreve `"meta": {"slip": "scaled"}`. Onde a aderência realmente termina, o visualizador mede por carro, a partir das voltas. Veja [Deslizamento, derrapagem e canais derivados](slip-and-drift.md).

## Voltas {#laps}

- **AC e ACC** contam voltas na página de gráficos (`completedLaps` no deslocamento 132, o tempo da última volta em milissegundos no 144). O `CounterSplitter` fecha uma volta quando o contador muda; ela é marcada como completa, com o tempo de volta do jogo, somente se o contador subiu exatamente um.
- **AC EVO e AC Rally** não são lidos para voltas (a página de gráficos do EVO é um layout diferente e maior; o AC Rally corre etapas). O `LineSplitter` usa o ponto onde a gravação começou como a linha: uma volta fecha quando o carro passa de novo o mais perto dessa linha, no mesmo sentido, e uma etapa ou qualquer corrida fecha quando o carro fica parado por 8 segundos.

Detalhes e limites: [Divisão de voltas e etapas](lap-splitting.md).

## Nomes de pista e de carro {#track-and-car-names}

Lidos uma vez, da página estática, quando a primeira amostra chega: para AC, ACC e AC Rally, o carro (UTF-16, deslocamento 68) e a pista (deslocamento 134); para o AC EVO, a pista e a sua definição (texto de um byte nos deslocamentos 136 e 169, unidos por um espaço) e nenhum carro. Eles vão para o ficheiro como `track` e `car: {"name": ...}`.

## O ficheiro de volta {#the-lap-file}

`game` é `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ou `assetto-corsa-rally`; `meta` é `{"slip": "scaled", "discipline": "rally"}` para o AC Rally e `{"slip": "scaled", "discipline": "circuit"}` para os outros três. Nenhum `surface` é escrito.

## Fontes {#sources}

O SDK de memória partilhada do AC1; a documentação de memória partilhada do ACC (v1.8); o layout do AC EVO como medido em `albertowd/live-telemetry-evo`; o do AC Rally como lido por `LuizZak/AssettoCorsaRallyTelemetryReader`. Veja [Jogos](games.md).
