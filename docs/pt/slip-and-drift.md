---
title: "Deslizamento, derrapagem e canais derivados"
nav_order: 8
lang: "pt"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Deslizamento, derrapagem e canais derivados {#slip-drift-and-derived-channels}

A análise de controlo do carro no separador Análise de corrida do visualizador precisa das mesmas poucas grandezas de todos os jogos: o quanto cada pneu desliza, o quanto o carro aponta para longe de onde está a ir (o ângulo de derrapagem), se ele está no ar, se está em chão solto. Os jogos enviam essas coisas de formas muito diferentes, ou não enviam. Os gravadores daqui escrevem o que cada jogo envia, com nomes canónicos, mais uma nota `meta.slip` dizendo o que os números de deslizamento significam; depois o visualizador deriva o que falta, uma vez, quando carrega uma volta. **O valor nativo de um jogo sempre vence um valor derivado.**

## O que os gravadores escrevem {#what-the-recorders-write}

| Jogo | Canais de deslizamento | `meta.slip` | Entradas do ângulo de derrapagem |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` por roda, como enviados | `peak` (escrito pelo gravador; o leitor `.tele.gz` do visualizador define o mesmo) | `latVel`, `longVel` a partir da velocidade no referencial do carro |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, além de `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` a partir da velocidade no referencial do carro |
| EA SPORTS WRC, jogos DiRT | nenhum; `wheelSurfaceSpeed` por roda no lugar | `null` | `latVel`, `longVel` = velocidade do mundo projetada nos eixos do carro |
| Richard Burns Rally | nenhum; também sem velocidades de roda | nenhum | `latVel`, `longVel` = a deriva lateral e o avanço do próprio carro |
| BeamNG.drive | nenhum; `wheelSurfaceSpeed` e `wheelSpeed` por roda | nenhum | `latVel`, `longVel` = velocidade do mundo projetada nos eixos do carro |
| Trackmania | `slipIndex` por roda (uma medida de deslizamento de 0 a 1) | `index` | `latVel` (velocidade lateral), `longVel` (velocidade frontal) |
| iRacing | nenhum (não registado) | nenhum | `yaw` e o trajeto, `yawRate` |

Os valores de `meta.slip` são definidos em [O ficheiro heat3d-lap](lap-format.md): `peak` (normalizado, então acima de 1 o pneu perde a aderência), `scaled` (um deslizamento físico dividido por um pico típico de asfalto), `physical` (uma fração e radianos), `index` (uma medida de deslizamento de 0 a 1).

### Por que o deslizamento dos jogos Kunos é escalado {#why-kunos-slip-is-scaled}

O deslizamento do Forza é normalizado para que 1 seja a borda da aderência; o que ele normaliza não está documentado. A Kunos envia a razão de deslizamento física (uma fração) e o ângulo de deslizamento (radianos). Dividir por um pico típico de asfalto - 0,12 para a razão e 0,14 rad (cerca de 8 graus) para o ângulo - faz com que "acima de 1 significa a deslizar" seja aproximadamente verdade para as duas famílias, o que mantém uma só leitura para os ecrãs do visualizador. É uma aproximação: os picos reais variam por pneu e superfície, e é por isso que os valores brutos são guardados ao lado dos escalados, e por que o visualizador mede, a partir das próprias voltas, onde a aderência de cada carro realmente cai.

## O que o visualizador deriva (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Estes correm no visualizador (`src/race/derive.ts` no visualizador do 3DHeat), não neste repositório.

### Ângulo de derrapagem, `bodySlip` {#drift-angle-bodyslip}

- **A partir da velocidade no referencial do carro** quando `latVel` e `longVel` estão presentes: `atan2(latVel, |longVel|)`, e 0 abaixo de 3 m/s (um carro parado de lado não está a derrapar).
  O seu sinal segue a velocidade lateral do jogo, cujo sentido é documentado nos dois sentidos para alguns jogos - leia o tamanho.
- **Caso contrário, a partir do rumo em relação ao trajeto**: a direção de movimento é tirada de posições a cerca de 2 m de cada lado de cada amostra (`atan2(dx, dz)`); a `yaw` do jogo é ajustada a ela com um sinal e um deslocamento (cada jogo tem o seu próprio zero e sentido de rotação), a usar amostras acima de 10 m/s, e só é confiável se depois concordar de perto (dispersão circular de no máximo 0,05, com pelo menos 20 amostras). O ângulo de derrapagem é a diferença, 0 abaixo de 3 m/s.

### Razão de deslizamento a partir das rodas {#slip-ratio-from-the-wheels}

Quando uma volta não tem `slipRatio.*` mas tem velocidades de roda, a razão de deslizamento é `(roda - carro) / carro` por roda, a partir de:

- `wheelSurfaceSpeed.*` (a velocidade do ponto de contacto, m/s) diretamente, quando enviada (EA WRC, DiRT, BeamNG);
- senão `wheelSpeed.*` (rotação, rad/s) vezes um **raio de deslocação medido na volta**: a mediana de `velocidade / |ômega|` nas amostras em que o carro está em roda livre numa reta (acima de 10 m/s, não no ar, aceleração abaixo de 0,3 de acelerador, travão abaixo de 0,05, aceleração longitudinal abaixo de 3 m/s²); com menos de 20 dessas amostras, todas as amostras acima de 10 m/s. Um raio fora de 0,1-1 m é rejeitado.

Só quando as quatro rodas podem ser derivadas; o `meta.slip` da volta então vira `physical`. Abaixo de 3 m/s o deslizamento é 0.

### No ar {#airborne}

`airborne` é 1 onde todas as rodas estão fora do chão, julgado pelo primeiro destes que a volta tem para as quatro rodas:

1. `groundContact.*` (BeamNG): nenhuma roda acima de 0,5;
2. `wheelLoad.*` (jogos AC, RBR, BeamNG): nenhuma roda acima de 5% da sua própria carga mediana;
3. `suspension.*` (0..1 do curso): nenhuma roda acima de 0,02, ou seja, todas totalmente estendidas.

Uma única amostra isolada no ar é apagada. O Trackmania escreve `airborne` por conta própria.

### Chão solto {#loose-ground}

Onde uma volta tem `surfaceRumble.*` (Forza), `loose` é 1 onde pelo menos duas rodas reportam rugosidade por pelo menos um terço de segundo, com lacunas menores que um segundo preenchidas (um trecho liso numa estrada de cascalho ainda é a estrada de cascalho). O Trackmania escreve `loose` por conta própria, a partir dos materiais de chão das rodas.

### Taxa de guinada {#yaw-rate}

Onde uma volta tem `yaw` mas não `yawRate`, ela é a variação da guinada nas amostras vizinhas.

## O que os gravadores derivam por conta própria {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): todos os gravadores, exceto o do Forza (que a envia), a escreve a partir de `suspensionM.*` como a posição dentro da faixa que a volta usou (mínimo a máximo). Serve para as barras de suspensão do carro e para perceber uma roda pendurada no ar; não é uma fração absoluta de curso.
- **`steer`** para os jogos Kunos, escalado por volta (veja [Jogos Assetto Corsa](telemetry-assetto-corsa.md)).
- **Acelerações** para o BeamNG, a partir da variação da velocidade do mundo ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** e o eixo vertical do Richard Burns Rally, a partir das posições ([Jogos de rali](telemetry-rally.md)).

## Lateralidade {#handedness}

Quando o mundo de um jogo é canhoto - o do Forza é -, um percurso sai espelhado num visualizador destrorso; a direção e a suspensão das próprias voltas denunciam isso. Os gravadores não mudam a lateralidade: um mundo Z para cima (BeamNG) é girado para Y para cima por uma rotação, o que o mantém, e todo o resto é escrito como enviado.
