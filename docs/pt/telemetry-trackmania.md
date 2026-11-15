---
title: Trackmania (2020)
nav_order: 5
lang: "pt"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Código: o plugin do Openplanet [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder) (`info.toml`, `main.as`). **O plugin ainda não foi executado no jogo**; o leitor do seu CSV, no visualizador, é testado.

## Porque um plugin que escreve ficheiros {#why-a-plugin-that-writes-files}

O Trackmania não tem saída de telemetria própria. O Openplanet, a plataforma de plugins do jogo, expõe aos plugins o estado do veículo do carro visto, mas os plugins do Openplanet não podem enviar UDP. Por isso, o plugin escreve um ficheiro CSV por corrida na sua própria pasta de armazenamento, e o visualizador lê esses ficheiros tal como estão. Não há processo de gravação: o `telemetry --game trackmania` só instala o plugin (com `--install`) e indica onde os ficheiros vão aparecer.

## Instalação e carregamento {#installing-and-loading}

- O `--install` copia `mods/trackmania/Heat3dRecorder` para `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, substituindo uma cópia mais antiga. Sem `--install` não se copia nada.
- No jogo, em **Openplanet > Developer > Load plugin**, e escolha `3DHeat recorder`.
- O plugin depende do plugin **VehicleState** do Openplanet (`dependencies = ["VehicleState"]` em `info.toml`).
- Os plugins não assinados só carregam no **modo de programador do Openplanet**, o que limita o jogo online. O plugin pode ser assinado no openplanet.dev; aqui não está assinado.

As corridas são escritas em `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Carregue esses ficheiros CSV no separador Análise de corrida do visualizador. `-o` e `--port` são ignorados no Trackmania.

## O que o plugin regista {#what-the-plugin-records}

Lê apenas o que o Openplanet expõe - o estado do veículo do carro visto (`VehicleState::ViewingPlayerState()`) e o tempo de corrida do jogador e o número de reaparecimentos (`CSmScriptPlayer`) - não envia nada para lugar nenhum e não altera nada no jogo. Uma linha é escrita em cada quadro (`Update`), por isso a taxa de amostragem é a taxa de quadros do jogo.

| Coluna | Origem |
|---|---|
| `time` | `CurrentRaceTime` / 1000, em segundos |
| `x`, `y`, `z` | `Position` (mundo, Y para cima) |
| `speed` | comprimento de `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ou 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` de cada roda (uma medida de deslizamento de 0..1) |
| `loose` | 1 quando o material do chão de alguma roda é Grass, Ice, Sand, Dirt, Green ou RoadIce |
| `airborne` | 1 quando o carro não tem contacto com o chão |
| `respawns` | reaparecimentos desde o início da corrida |

## Corridas {#runs}

- Uma corrida **começa** no primeiro quadro em que o tempo de corrida não é negativo (a contagem decrescente não é registada).
- **Termina** quando a sequência de interface do playground é a sequência de chegada (valor 11): o ficheiro é escrito como completo, com o último tempo de corrida como o seu `seconds`.
- É **abandonada** - escrita com `_partial` no nome e `"complete": false` - quando o relógio da corrida recua mais de meio segundo (um reinício), ou quando o jogador sai do playground.
- Uma corrida com menos de 20 linhas não é escrita.

## O ficheiro {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Nomeado `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Ao nome do mapa são retirados os códigos de formatação e as aspas duplas são trocadas por simples. Os valores são escritos com quatro casas decimais. O formato está descrito em [O ficheiro heat3d-lap](lap-format.md#the-csv-form).

O `meta` do cabeçalho traz `"slip": "index"` - os canais `slipIndex.*` são a medida de deslizamento de 0..1 do próprio Trackmania, não um deslizamento físico - e `"discipline": "arcade"`.
