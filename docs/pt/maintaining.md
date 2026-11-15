---
title: Manter estes documentos
nav_order: 96
lang: "pt"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Manter estes documentos {#maintaining-these-docs}

A lista de verificação de cada versão, para que o código, as páginas em inglês e as suas traduções fiquem em sintonia. Faça os passos em ordem.

1. **Gere de novo as páginas geradas.**
   - `python tools/gen_docs_reference.py` reescreve a [Referência de comandos](../cli-reference.md) a partir de `--help` e das listas de colunas do código. `--check` termina com 1 quando a página está desatualizada: execute-o antes de cada versão.
   - `python tools/docs_diagrams.py` redesenha os diagramas em `docs/assets/img/`; `--strings` atualiza também o `docs/assets/i18n/en.json`, os rótulos a traduzir.
   - `python tools/sync_wiki.py` regenera a cópia da wiki do GitHub em `docs/wiki/`.
2. **Liste o que mudou desde a última versão.** `git log --oneline v$(cat VERSION)..` (a etiqueta da última versão é `v` + a versão em `VERSION`). Para cada comando, opção, coluna de saída ou comportamento novo ou alterado: atualize a sua página e acrescente uma linha à tabela *Docs* do `CHANGELOG.md`.
3. **Revisão independente.** Alguém que não escreveu a alteração lê as páginas e os diagramas alterados como três leitores: um **principiante** (nunca usou uma linha de comandos: consegue instalar e executar?), uma criança de **8 anos** (a página diz em palavras simples o que é e porquê?), e um **profissional** (as opções, padrões e colunas coincidem com o código?). Verifique que nenhuma página nomeia níveis, mapas, jogadores ou gravações reais: os exemplos são sintéticos, e as afirmações de verificação dão apenas o método e a tolerância.
4. **Corrija os problemas encontrados.**
5. **Traduza.** Cada página traduzida regista o hash da página em inglês de que foi feita. Traduza de novo as páginas cujo hash de origem em inglês mudou, e os rótulos dos diagramas que mudaram; depois reveja cada idioma: claro para os três leitores, rótulos dos diagramas corretas, palavras a coincidir com a interface localizada do visualizador.
6. **Envie (push) só com a autorização do responsável.** Depois crie o rótulo da versão `v<VERSION>`.

Nunca executou estes comandos? [Antes de começar](before-you-start.md) explica o Python e o terminal.

## Traduções: os comandos {#translations-the-commands}

O site está traduzido para as 40 línguas do visualizador do 3DHeat: o inglês em `docs/`, cada outra língua em `docs/<lang>/`, com os mesmos nomes de ficheiros. O `tools/docs_i18n.py` faz a contabilidade:

```bash
python tools/docs_i18n.py hashes             # depois de qualquer alteração em inglês: regista o hash de cada página
python tools/docs_i18n.py svg-strings        # depois de qualquer alteração de imagem: as etiquetas a traduzir
python tools/docs_i18n.py status             # por idioma: páginas atuais, desatualizadas, em falta
python tools/docs_i18n.py todo --lang de     # as páginas alemãs a (re)traduzir
python tools/docs_i18n.py svg-build --lang de    # imagens alemãs a partir de docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # marca as páginas alemãs com o hash inglês
python tools/docs_i18n.py check              # termina com 1 quando hashes ou etiquetas estão desatualizados
```

Traduza só o que o `todo` lista: mantenha o Markdown, as ligações, o código, os nomes de ficheiros e de colunas como estão, traduza os títulos e as descrições das imagens, e use as palavras do próprio visualizador do 3DHeat para os seus botões e painéis (em `src/i18n/locales/<lang>/`). As páginas de referência geradas e as imagens de terminal ficam em inglês. No site, uma tradução desatualizada diz isso e liga à página em inglês; uma tradução em falta recorre ao inglês. O menu de idiomas do cabeçalho e o redirecionamento por idioma do navegador na página inicial vêm de `docs/_includes/`.
