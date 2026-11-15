---
title: Atualizações
nav_order: 10
lang: "pt"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Atualizações {#updates}

O 3DHeat GameCapture verifica as versões publicadas no GitHub deste repositório quando inicia, diz quando há uma versão mais recente e se oferece para atualizar. Código: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Quando corre a verificação {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - antes do comando correr.
- `python -m heat3d_capture.ui` (e `scan.bat`) - antes da janela abrir.
- `python -m heat3d_update` - a pedido, perguntando sempre ao GitHub de novo.

## Como funciona a verificação {#how-the-check-works}

- A versão instalada é o ficheiro `VERSION` na raiz do repositório (por exemplo `1.0.1`).
- A versão mais recente é pedida a `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, com um tempo limite de **5 segundos**. Uma rede lenta nunca bloqueia a ferramenta por mais tempo.
- A resposta fica em cache durante **6 horas** em `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` sem `LOCALAPPDATA`). Cada ferramenta do 3DHeat tem o seu próprio ficheiro de cache. "Ainda sem versão" (HTTP 404) fica em cache como uma resposta; as outras falhas não ficam em cache e significam simplesmente que não há aviso.
- As versões são comparadas numericamente (`v1.2.3` ou `1.2.3`; tudo o que vem depois de `-` ou `+` é ignorado).
- Sem conexão, com limite de pedidos atingido ou atrás de um proxy, a ferramenta continua com a versão que tem.

## O que acontece quando há uma versão mais recente {#what-happens-when-a-newer-release-is-out}

Ao iniciar, imprime, no fluxo de erros:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Com um terminal onde responder, pergunta `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` significam sim). Depois de uma atualização bem-sucedida, **o mesmo comando volta a iniciar**, com o código novo.
- Sem terminal (um pipe, uma execução agendada), imprime `Run python -m heat3d_update in <folder> to update.` e continua sem alterações.

## Como é aplicada uma atualização {#how-an-update-is-applied}

Depende de como as ferramentas foram instaladas:

- **Um clone do git** (uma pasta `.git` e o `git` no PATH): `git pull --ff-only`. Recusado enquanto a cópia de trabalho tiver alterações locais em ficheiros controlados - esse trabalho é de alguém; faça commit ou guarde-o com stash primeiro.
- **Uma cópia transferida**: o ficheiro de código-fonte da versão é transferido, extraído para uma pasta temporária (as entradas fora da pasta do próprio ficheiro são ignoradas), e **verificado para ser a versão que diz ser** no seu ficheiro `VERSION`. Depois, os seus ficheiros são copiados por cima desta pasta. Dentro dos pacotes Python da própria versão (pastas `heat3d_*` no topo do repositório, e um nível abaixo no antigo layout de monorepo), os módulos `.py` que a versão já não tem são apagados, para que um módulo antigo não tampe o seu substituto.

Os seus próprios ficheiros - gravações, ficheiros de volta, definições, exportações, o `.venv` - nunca são tocados: só são escritos os ficheiros que fazem parte da versão.

## Manualmente {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Imprime `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, ou a nova versão e o que fez. Código de saída 1 se a atualização não pôde ser aplicada.

## Desligar {#switching-it-off}

Defina **`HEAT3D_NO_UPDATE=1`** (qualquer valor exceto vazio, `0`, `false`, `no`). Isso desliga a verificação e o aviso ao iniciar. O próprio `python -m heat3d_update` continua a verificar quando é executado manualmente.
