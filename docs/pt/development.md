---
title: Desenvolvimento
nav_order: 11
lang: "pt"
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Desenvolvimento {#development}

## Estrutura do repositório {#repository-layout}

| Caminho | Conteúdo |
|---|---|
| `heat3d_capture/__main__.py` | a linha de comandos: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (layout do Data Out), `fulllap.py` (ficheiros de volta do Forza, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (o documento de volta partilhado) |
| `heat3d_capture/capture/` | `sources.py` (captura ao vivo, vídeo), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (o que o digitalizador executa), `estimator.py` (caminho PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (o escritor), `reference.py` (nível de referência sintético) |
| `heat3d_capture/scan/` | `session.py` (uma digitalização), `reconstruct.py` (quadros-chave em geometria), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: o HUD de uma gravação - janela de pontos, ecrãs de morte, minimapa da pista, feed de abates (`profiles.py` por jogo) |
| `heat3d_capture/locate/` | `locate`: as renderizações do nível, a base de dados, a correspondência, o modelo por mapa, o minimapa |
| `heat3d_capture/ui/` | `__main__.py` (entrada e verificação de dependências), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | a verificação de versões e o atualizador |
| `mods/beamng/heat3d/` | o mod de protocolo do BeamNG |
| `mods/trackmania/Heat3dRecorder/` | o plugin do Openplanet |
| `tools/export_onnx.py` | o conversor do modelo de profundidade |
| `tools/gen_docs_reference.py` | escreve `docs/cli-reference.md` a partir de `--help`; `--check` diz se está desatualizado |
| `tools/docs_diagrams.py` | desenha os diagramas em `docs/assets/img/` (por idioma com `--lang`) |
| `tools/sync_wiki.py` | regenera `docs/wiki/` a partir de `docs/` |
| `models/` | ficheiros `.onnx` convertidos (não versionados) |
| `tests/` | a suíte de testes; `scene.py` e `track_scene.py` renderizam cenas sintéticas com geometria conhecida |
| `docs/` | esta documentação; `docs/wiki/` é gerado a partir dela |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

A lógica de digitalização não depende do Qt: `ScanSession` e `Reconstructor` recebem funções simples e podem ser controlados a partir de um script ou de um teste. Exemplo:

```python
from heat3d_capture.depth.onnx_estimator import OnnxDepthEstimator
from heat3d_capture.scan.session import Quality, ScanSession, ScanSettings

settings = ScanSettings(source="walk.mp4", quality=Quality.BALANCED, field_of_view=90.0,
                        camera_height=1.70)
session = ScanSession(settings, estimator=OnnxDepthEstimator("models/depth-small-518.onnx"))
session.start()
session.wait()
print(session.progress.message, session.export("walk.glb"))
```

## O ambiente {#the-environment}

O projeto usa um ambiente virtual em `.venv` (criado por `scan.bat` ou manualmente). Os testes que tocam na interface precisam do **PySide6** nele, que o `requirements.txt` instala como `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Para o conversor de modelos, os testes de profundidade em PyTorch e o caminho offline, instale o PyTorch (adequado à GPU) **antes** do `requirements.txt`; depois o `requirements-offline.txt` e a sua linha `vggt` para o solucionador offline, e o `onnxscript` para o conversor. Ver [Execução e dependências](runtime.md#installing-by-hand).

## Executar os testes {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

O `pytest.ini` define `testpaths = tests` e silencia os `UserWarning` do `huggingface_hub`. A suíte tem várias centenas de verificações; a maioria não precisa de jogo, de GPU nem de equipamento de captura.

O que é ignorado automaticamente, e por quê:

| Testes | São ignorados quando |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, os testes que conduzem a janela em `test_ui_drives_a_scan.py` | não há `models/depth-*.onnx` - execute primeiro `tools/export_onnx.py` |
| os testes do estimador de GPU em `test_depth.py` | o PyTorch não está instalado ou não há dispositivo CUDA; os testes de `fit_scale` e `AffineFit` correm sempre |
| alguns casos de `test_offline.py` e `test_solveprep.py` | o OpenCV não tem codificador de vídeo para escrever o clip sintético |
| `test_hotkeys.py` | os testes de registo precisam do Windows; o teste de recurso corre em outros sistemas |
| `test_course_ground.py` | `HEAT3D_COURSE` não está definido |
| alguns testes de fusão | um caso sintético não fundiu nada |

### O teste de inicialização {#the-launch-test}

`tests/test_launch.py` executa o ponto de entrada real, `python -m heat3d_capture.ui`, como subprocesso (com `QT_QPA_PLATFORM=offscreen`) e verifica que chega ao ciclo de eventos e continua a correr. Existe porque a primeira versão falhou em todas as inicializações enquanto todos os outros testes passavam: todos criam eles próprios um `QApplication` e depois constroem a janela, o que salta a única sequência que um utilizador realiza - a verificação de dependências cria a aplicação primeiro. Um teste de componente que constrói o seu próprio ambiente não consegue ver uma falha na forma como o ambiente é construído.

### Verdade de referência {#ground-truth}

- `tests/test_accuracy.py` - uma sala sintética, de um caminho conhecido, com profundidade analítica; ver [Reconstrução de níveis](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - largura da estrada, extração da escala da pista, a grade de cobertura lida enquanto é escrita, e porque é que o fecho de ciclo fica desligado.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - os layouts de telemetria, sobre pacotes e páginas construídos a partir das estruturas documentadas, e os ficheiros de volta que escrevem (nomes canónicos dos canais, `meta`, sem `NaN` no JSON). `tests/test_trackmania_plugin.py` lê o código-fonte do plugin do Openplanet para ver o que escreve na descrição de cada corrida.
- `tests/test_route_record.py` - o ficheiro `route` está em disco, completo, antes do gravador parar.
- `tests/test_telemetry_pose.py` - poses do Forza nas coordenadas do próprio jogo, os sentidos de yaw, pitch e roll, e uma lacuna de telemetria preenchida visualmente no mundo espelhado.
- `tests/test_glb.py` - o contrato do GLB; os testes do visualizador leem um nível de referência escrito por este escritor, por isso o formato é testado nos dois lados.

### Verificar um percurso exportado contra voltas {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` verifica que um percurso exportado pelo [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) está mesmo por baixo do carro gravado - o carro deve ficar a uma altura ao solo acima da superfície que tem diretamente por baixo. Aponte-o para o nome-base de um percurso exportado (o `.glb` e o seu `.json` ao lado):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Um percurso com saltos grandes pode falhar de propósito: o carro está no ar sobre um terreno que lá está.

## Convenções {#conventions}

- O código em `heat3d_capture/` importa as dependências pesadas (OpenCV, ONNX Runtime, PyTorch, Qt) de forma preguiçosa, dentro das funções; assim, importar um módulo, executar `--help` ou executar os gravadores de telemetria não custa nada.
- As threads de trabalho nunca tocam nos widgets do Qt; os resultados passam para a thread da interface como sinais do Qt.
- As gravações, os ficheiros de volta, as malhas, os pesos dos modelos e o vídeo ficam fora do git pelo `.gitignore`, por pasta e por tipo de ficheiro.
- Commits e versões: a versão é o ficheiro `VERSION`; as versões são lançamentos no GitHub de [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), que o atualizador lê ([Atualizações](updates.md)).
