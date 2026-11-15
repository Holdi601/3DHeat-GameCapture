---
title: "Mantenimiento de estas páginas"
nav_order: 96
lang: es
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Mantenimiento de estas páginas {#maintaining-these-docs}

La lista de comprobación de cada versión, para que el código, las páginas inglesas y sus traducciones sigan
alineados. Haga los pasos en orden.

1. **Regenerar las páginas generadas.**
   - `python tools/gen_docs_reference.py` reescribe [Referencia de comandos](../cli-reference.md) a partir de
     `--help` y de las listas de columnas del código. `--check` devuelve 1 cuando la página está desactualizada:
     ejecútelo antes de cada versión.
   - `python tools/docs_diagrams.py` redibuja los diagramas en `docs/assets/img/`;
     `--strings` también actualiza `docs/assets/i18n/en.json`, las etiquetas que hay que traducir.
   - `python tools/sync_wiki.py` regenera la copia de la wiki de GitHub en `docs/wiki/`.
2. **Listar lo que ha cambiado desde la última versión.** `git log --oneline v$(cat VERSION)..` (la última
   etiqueta es `v` + la versión de `VERSION`). Para cada comando, opción, columna de salida o
   comportamiento nuevo o modificado: actualice su página y añada una fila a la tabla *Docs* de `CHANGELOG.md`.
3. **Revisión independiente.** Alguien que no haya escrito el cambio lee las páginas y los
   diagramas modificados como tres lectores: un **principiante** (nunca ha usado una línea de comandos: ¿puede instalar y ejecutar
   la herramienta?), un **niño de 8 años** (¿dice la página con palabras sencillas qué es y por qué?) y un **profesional**
   (¿coinciden con el código las opciones, los valores por defecto y las columnas?). Compruebe que ninguna página nombra niveles,
   mapas, jugadores o grabaciones reales: los ejemplos son sintéticos y las afirmaciones de verificación dan solo el método y
   la tolerancia.
4. **Corregir los hallazgos.**
5. **Traducir.** Cada página traducida guarda el hash de la página inglesa de la que procede. Vuelva a traducir
   las páginas cuyo hash de la fuente inglesa ha cambiado, y las etiquetas de diagrama que han cambiado;
   después revise cada lengua: clara para los tres lectores, etiquetas de diagrama correctas, palabras que coincidan con
   la interfaz localizada del visor.
6. **Publicar solo con el visto bueno del propietario.** Después etiquete la versión `v<VERSION>`.

¿Es nuevo con estos comandos? [Antes de empezar](before-you-start.md) cubre Python y la
terminal.

## Traducciones: los comandos {#translations-the-commands}

El sitio está traducido a las 40 lenguas del visor 3DHeat: el inglés en `docs/`, cada otra
lengua en `docs/<lang>/` con los mismos nombres de archivo. `tools/docs_i18n.py` lleva la contabilidad:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Traduzca solo lo que `todo` lista: deje el Markdown, los enlaces, el código y los nombres de archivos y de columnas tal cual,
traduzca los títulos y las descripciones de las imágenes, y use las palabras propias del visor 3DHeat para sus botones
y paneles (su carpeta `src/i18n/locales/<lang>/`). Las páginas de referencia generadas y las imágenes de terminal siguen
en inglés. En el sitio, una traducción desactualizada lo indica y enlaza la página en inglés; una página que falta
recurre al inglés. El menú de idioma de la cabecera y la redirección de la página de inicio según el idioma del navegador
vienen de `docs/_includes/`.
