---
title: iRacing
nav_order: 6
lang: "pt"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

O iRacing **não precisa de gravador**. O simulador escreve os seus próprios ficheiros de telemetria, `.ibt`, quando o registo de telemetria está ligado (Alt+L no carro): a sessão inteira a 60 Hz, todos os canais que o simulador expõe, com a descrição YAML da sessão ao lado. Solte o ficheiro `.ibt` no separador Análise de corrida do visualizador.

O leitor está no visualizador, e não neste repositório (`src/race/ibt.ts` no visualizador do 3DHeat). É testado com um ficheiro sintético; está documentado aqui porque é a metade do iRacing da mesma história de gravação de voltas.

## O que o ficheiro contém, e como é lido {#what-the-file-holds-and-how-it-is-read}

O ficheiro é o layout de memória documentado do simulador escrito em disco:

| Parte | Tamanho | Contém |
|---|---|---|
| Cabeçalho | 112 bytes | versão, taxa de ticks, onde estão o YAML e a tabela de variáveis, o comprimento de uma linha de amostra, onde começam as linhas |
| Subcabeçalho do disco | 32 bytes | data e hora de início, número de voltas, número de linhas |
| Tabela de variáveis | 144 bytes por canal | tipo, deslocamento na linha, quantidade, nome, descrição, unidade |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Linhas | uma por tick | |

Um ficheiro é recusado quando tem menos de 144 bytes, quando o cabeçalho não faz sentido (sem variáveis, uma tabela de variáveis fora do ficheiro, um comprimento de linha zero), quando lhe falta algum de `SessionTime`, `Lap`, `Lat`, `Lon`, ou quando nenhuma amostra tem uma posição fixa.

## Posição {#position}

O iRacing indica latitude, longitude e altitude, não uma posição no referencial da própria pista. As posições são dispostas em metros num plano tangente à primeira amostra com fixo (raio da Terra 6.371.008,8 m): `x` para leste, `z` para sul, `y` a altitude - assim, vista de cima, com o rumo padrão da câmara do visualizador, o norte fica para cima no ecrã.

## Voltas {#laps}

A sessão é dividida pelo contador `Lap` do simulador. Uma volta só é guardada se tiver mais de 60 amostras, começar abaixo de 5% da distância da volta (`LapDistPct`) e terminar acima de 95% - ou seja, voltas feitas de linha a linha. Se nenhuma volta cumprir, o ficheiro é recusado com uma mensagem que indica o comprimento da pista, a partir do YAML. A `distance` é o `LapDist` recalculado a partir do início da volta, ou a distância percorrida a partir das posições quando falta o `LapDist`; o `time` é o `SessionTime` a partir do início da volta.

## Canais {#channels}

| iRacing | Canal | Conversão |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | nenhuma |
| `Clutch` | `clutch` | `1 - value` (o iRacing conta a embraiagem como engatada; o canal é o pedal) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radianos, positivo no sentido anti-horário, passando para -1..1 com a direita positiva; pi quando falta o máximo) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | nenhuma |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | nenhuma |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | definições de ajuda |
| `dcBrakeBias` | `brakeBias` | dividido por 100 quando acima de 1,5 (uma percentagem em alguns carros) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura da carcaça no meio |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa vezes 0,145038, para psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Todos os outros canais com um valor por amostra (e não um único byte) passam com o seu próprio nome, com um prefixo de roda (`LF`, `RF`, `LR`, `RR`) transformado num sufixo (`.FL`, `.FR`, `.RL`, `.RR`), para que os gráficos do visualizador o ofereçam sem que ninguém o descreva.

O carro vem de `DriverInfo`: a entrada cujo `CarIdx` coincide com `DriverCarIdx` dá `CarScreenName`, `CarID` e `CarClassShortName`. A pista é `TrackDisplayName` (ou `TrackName`).

## O que o iRacing não dá {#what-iracing-does-not-give}

Não é registado o deslizamento dos pneus, por isso não há canais de deslizamento. O ângulo de derrapagem é derivado da taxa de guinada contra o caminho (ver [Deslizamento, derrapagem e canais derivados](slip-and-drift.md)). Os modelos de pista vêm num formato protegido e não são alvo de extração de ficheiros (ver [Jogos](games.md)).
