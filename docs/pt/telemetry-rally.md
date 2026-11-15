---
title: "EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally"
nav_order: 3
lang: "pt"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # ou dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Código: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testes: `tests/test_rally.py`, com pacotes montados a partir dos layouts documentados. **Ainda não executado contra os jogos ao vivo.**

Todos eles enviam UDP que o jogo liga a partir dos próprios ficheiros de definição. O gravador escuta em todas as interfaces (`0.0.0.0`) na porta padrão do jogo, a menos que `--port` dê outra: **20777** para `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** para `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Ligando {#switching-it-on}

O jogo lê `Documents\My Games\WRC\telemetry\config.json`. O pacote `session_update` da estrutura `wrc` padrão precisa estar ativado para esta máquina:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<caminho para config.json>"
```

`--configure` (função `configure_wrc`):

- lê o JSON, encontra `udp.packets` e a entrada com `"structure": "wrc"` e `"packet": "session_update"`;
- se ela já está ativada para `127.0.0.1` ou `localhost` na porta usada, imprime `already on` e não muda nada;
- senão define `"ip": "127.0.0.1"`, `"port": <porta>`, `"bEnabled": true`, e mantém o `frequencyHz` da entrada (ou `-1` se não houver); se não existir essa entrada, acrescenta uma;
- grava o texto original em `config.json.bak` ao lado dele, e depois grava o novo ficheiro (indentado com 4 espaços).

Reinicie o jogo depois de mudar o ficheiro, se ele não aplicar a alteração (não verificado).

### O que ele envia {#what-it-sends}

A estrutura `wrc` padrão tem 237 bytes, little-endian, sem cabeçalho: posição, velocidade e aceleração do mundo (X para a esquerda, Y para cima, Z para a frente), os vetores unitários esquerda / frente / cima do carro, por roda (traseira esquerda, traseira direita, dianteira esquerda, dianteira direita) a altura do cubo e a velocidade vertical dele e a velocidade para a frente do ponto de contacto, as temperaturas de travão, os pedais depois das assistências, a direção (-1 esquerda, +1 direita), o travão de mão, rpm, marcha, e o relógio da etapa, a distância e o comprimento. Um pacote menor que 237 bytes é ignorado e reportado uma vez.

| Canal | De |
|---|---|
| `x`, `y`, `z` | posição do mundo |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | velocidade do mundo projetada para a frente, com a esquerda negativa (então positivo é para a direita), em cima |
| `longAcc`, `latAcc`, `vertAcc` | aceleração do mundo projetada da mesma forma |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | como enviados |
| `gear` | `gear_index`; -1 quando é igual ao índice de marcha a ré, 0 quando é igual ao índice de ponto morto |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | posição do cubo |
| `wheelSurfaceSpeed.*` | velocidade para a frente do ponto de contacto |
| `brakeTemp.*` | temperatura do travão |

Verificação: se `speed` está acima de 10 e o comprimento da velocidade do mundo difere dela em mais de 20%, o gravador imprime uma vez que o layout pode não ser a estrutura `wrc` padrão.

Uma etapa está **terminada** quando o comprimento da etapa é positivo e a distância alcançou o comprimento menos 0,5 m. O relógio usado para dividir e para `time` é `stage_time`.

Fontes: Guia de Telemetria UDP v1.3 da EA; a lista de canais que o jogo grava em `readme/channels.json`; deslocamentos como decodificados por nobonobo/obs-codemasters-telemetry e SpaceMonkey. A porta padrão de fábrica não está documentada; o gravador usa 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Ligando {#switching-it-on-1}

Edite `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (o DiRT Rally e o DiRT 4 também usam um `hardware_settings_config.xml`; a pasta exata deles não foi verificada aqui) para que o elemento `udp` fique assim:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` é o que põe posições, rodas e o comprimento da etapa no pacote. O gravador não edita esse ficheiro.

### O que ele envia {#what-it-sends-1}

66 floats little-endian (DiRT Rally: 64); pacotes com menos de 64 floats são ignorados, e um pacote de 64 floats recebe zeros de preenchimento. Os índices usados:

| Índice | Campo | Canal |
|---|---|---|
| 1 | tempo da volta (etapa) | o relógio de divisão e `time` |
| 2 | distância da volta | `stageDistance` |
| 4-6 | posição do mundo | `x`, `y`, `z` |
| 7 | velocidade | `speed` |
| 8-10 | velocidade do mundo | `longVel` (na frente), `latVel` (no vetor lateral) |
| 11-13 | vetor lateral | |
| 14-16 | vetor frente | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | posição da suspensão TE TD DE DD | `suspensionM.*` |
| 25-28 | velocidade do ponto de contacto das rodas TE TD DE DD | `wheelSurfaceSpeed.*` |
| 29-33 | acelerador, direção, travão, embreagem, marcha | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ou mais significa ré, escrito como -1) |
| 34, 35 | g lateral e longitudinal | `latAcc`, `longAcc` (vezes 9,80665) |
| 37 | rpm / 10 | `rpm` (vezes 10) |
| 51-54 | temperaturas de travão | `brakeTemp.*` |
| 59, 60, 61, 62 | voltas completadas, total de voltas, comprimento da pista, tempo da última volta | divisão |

**Não há canal de travão de mão.** O sentido do vetor lateral é documentado nos dois sentidos, então o sinal de `latVel` não deve ser usado como garantia (o visualizador lê o tamanho do ângulo de derrapagem).

Uma etapa está **terminada** quando a contagem de voltas completadas sobe acima do seu valor no início da etapa (uma volta de rallycross cada vez que isso acontece), ou, para um evento de uma volta só, quando a distância da volta alcança 99,9% do comprimento da pista. O tempo da etapa é o tempo da última volta do jogo quando é positivo. Verificação: velocidade contra velocidade, como no EA WRC, com a mensagem "is extradata set to 3?".

Fontes: documento UDP do DiRT 4 da Codemasters; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Ligando {#switching-it-on-2}

Em `RichardBurnsRally.ini`, seção `[NGP]`: `udpTelemetry=1` e o endereço de destino (127.0.0.1, porta 6776 a menos que se passe outra em `--port`). O gravador não edita esse ficheiro.

### O que ele envia {#what-it-sends-2}

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): relógio e distância até ao fim da etapa, pedais, direção, marcha, posição do mundo, atitude, as próprias velocidades do carro (avanço para a frente, deriva lateral, arfagem vertical), acelerações, rpm, e quatro blocos de roda de 128 bytes (DE, DD, TE, TD) com deflexão e força da mola. Nenhuma velocidade de roda.

| Canal | De |
|---|---|
| `x`, `y`, `z` | posição, eixos como enviados, depois reordenados (abaixo) |
| `longVel`, `latVel`, `vertVel` | avanço, deriva lateral, arfagem vertical |
| `longAcc`, `latAcc` | aceleração x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | como enviados |
| `gear` | `gear - 1` (0 ré, 1 ponto morto, 2 primeira) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | deflexão da mola |
| `wheelLoad.*` | força da mola |
| `speed` | **calculado a partir das posições** em ±2 amostras, não tirado do pacote |

Os eixos de posição, as unidades de atitude e a unidade de velocidade do RBR não são documentados, então, quando uma etapa é escrita: o eixo ao longo do qual a etapa varia menos é tomado como vertical e trocado para `y` (`orient_up`, precisa de pelo menos 10 amostras), e a velocidade é recalculada a partir das posições (`speed_from_positions`). A atitude é decodificada, mas não escrita, então os ficheiros do RBR não têm `yaw`.

Uma etapa está **terminada** quando o relógio de corrida está a correr e a distância até ao fim chegou a zero. O relógio é `race_time`.

Fontes: `rbr.telemetry.data.TelemetryData.h` do NGP, via mika-n/RBRUDPTelemetryLogger e groybe/rbr-udp-telem.

## Etapas {#stages}

Os cinco usam `StageSplitter` no relógio de etapa do jogo: uma etapa abre quando o relógio começa, fecha completa quando o jogo diz que o carro terminou, e um relógio que volta para trás (um reinício, ou a etapa seguinte) abandona a etapa aberta - mantida como ficheiro `_partial` se tiver mais de 10 amostras e pelo menos 300 m. Etapas terminadas com menos de 300 m não são escritas. Detalhes: [Divisão de voltas e etapas](lap-splitting.md).

## O ficheiro de volta {#the-lap-file}

`game` é `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ou `richard-burns-rally`. `meta` é `{"discipline": "rally", "slip": null}`, mais `"surface": "<valor>"` quando `--surface` foi dado. `slip` é null porque nenhum desses jogos envia deslizamento dos pneus. O deslizamento da área de contacto de cada roda (EA WRC, DiRT) fica no ficheiro, no lugar; o visualizador deriva o deslizamento e o ângulo de derrapagem a partir dele e dos eixos do carro; veja [Deslizamento, derrapagem e canais derivados](slip-and-drift.md). Os canais `suspension.*` (0..1 do curso usado) são acrescentados a partir de `suspensionM.*`.

Quando nenhum `--surface` é dado, o ficheiro não traz superfície nenhuma, de propósito: um valor padrão escrito aqui sobrescreveria a inferência do próprio visualizador. O visualizador então tira a superfície do nome da etapa ou do evento (rali de asfalto, de inverno, o Monte como misto), senão de como o carro foi dirigido ali (curvas fortes com pequeno ângulo de derrapagem são asfalto), e cascalho quando nada indica - o que uma etapa de rali mais costuma ser. Indique `--surface` quando souber melhor.
