---
title: "Modelos y licencias"
nav_order: 7
lang: es
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modelos y licencias {#models-and-licences}

Todo lo escrito para este repositorio está bajo la **licencia MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Lo que la MIT no puede cubrir es con lo que trabajan las herramientas: los paquetes que importan, los modelos que usa la reconstrucción y los juegos que leen. El registro completo, con fuentes, está en [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); sus licencias se leyeron de los metadatos de los paquetes y de las fichas de los modelos en septiembre de 2026. Si las condiciones de un componente han cambiado desde entonces, cuenta la fuente, no esta página. Nada de lo que hay aquí es asesoramiento jurídico.

## El modelo de profundidad: el que decide el uso comercial {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **no tiene la misma licencia en todos sus tamaños**, y una reconstrucción hereda la licencia del modelo que la hizo:

| Modelo | Licencia | Uso comercial | Lo usa |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **permitido** | el valor predeterminado: el modelo convertido del escáner (`tools/export_onnx.py` lo toma por defecto, y «Set up the depth model» de la ventana siempre lo construye), y la profundidad de la ruta sin conexión (fusión); VGGT aporta sus poses |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | solo no comercial | solo si lo conviertes tú (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | solo no comercial | solo si lo conviertes tú (`--size large`) |

Base y Large dan mejor profundidad. Convertirlos está permitido; eso hace que ese archivo de modelo, y cada reconstrucción hecha con él, sea no comercial. Es una decisión de quien lo ejecuta, no un valor por defecto que se herede. El escáner elige entre los archivos `models/depth-*.onnx` **por licencia, no por nombre**: `depth-small-*` siempre que exista, luego Base, luego Large (`choose_model` en [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). La ventana indica el archivo que tomó, su licencia y cualquier otro archivo de modelo que encontró y no usó; para escanear con Base, saca el archivo Small de `models/`.

## VGGT: solo reconstrucción sin conexión {#vggt---offline-reconstruction-only}

| Modelo | Licencia | Disponibilidad |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - solo no comercial**; las reconstrucciones hechas con él heredan esa condición | público; el predeterminado |
| `facebook/VGGT-1B-Commercial` | licencia aparte; revisa las condiciones que te hayan concedido | restringido: el acceso se pide a Meta y se concede por cuenta; sin él, la descarga falla. Se elige con `reconstruct --model vggt-1b-commercial` |

VGGT solo lo usa `python -m heat3d_capture reconstruct`; el escáner en vivo nunca lo carga. El comando imprime la línea de licencia antes de empezar. La reconstrucción a partir de vídeo es la parte de este proyecto que haría un jugador, y las condiciones no comerciales le encajan; para trabajo comercial, la ruta es una exportación del motor o el exportador de archivos del juego, y ambas son exactas de todos modos.

## Localizar fotogramas: `locate` {#locating-frames---locate}

| Modelo | Licencia | Función |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | encuentra los renderizados que muestran el mismo lugar |
| ALIKED `aliked-n16` | BSD-3-Clause | puntos clave y descriptores |
| LightGlue (variante ALIKED) | Apache-2.0 | los empareja |

Los tres permiten el uso comercial y se descargan en el primer uso. SuperPoint, la pareja habitual de LightGlue, no se usa: sus pesos son no comerciales. Véase [Localizar fotogramas en un nivel](locate.md).

## Paquetes de Python {#python-packages}

| Paquete | Licencia | Función |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmética, suavizado, marching cubes |
| opencv-python | Apache-2.0 | vídeo, características, flujo óptico |
| onnxruntime, onnxruntime-directml | MIT | inferencia de profundidad |
| windows-capture | MIT | captura en vivo mediante Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | la ventana |
| pytest | MIT | solo desarrollo |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | conversión de modelos única; la ruta sin conexión |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | la ruta sin conexión (`requirements-offline.txt`) |
| vggt | «VGGT License» de Meta (acuerdo de materiales de investigación con una política de uso aceptable) | la ruta sin conexión; se instala desde GitHub con `--no-deps` |
| moderngl, glcontext | MIT | `locate`: renderizado del nivel fuera de pantalla (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: puntos clave y emparejamiento |

**PySide6 tiene condiciones.** LGPL-3.0 permite el uso propietario y comercial siempre que Qt siga siendo una biblioteca *reemplazable*. Aquí se usa como una importación normal enlazada dinámicamente, lo que lo cumple, y su aviso de licencia debe acompañar a cualquier distribución. Empaquetar la herramienta en un único ejecutable obligaría a mantener Qt reemplazable.

La licencia del paquete `vggt` se leyó de su `LICENSE.txt` y está registrada en `LICENSES.md`; cubre el código, aparte de los pesos, que son CC-BY-NC-4.0.

## Los juegos {#the-games}

La telemetría solo llega desde las interfaces que publican los juegos; los fotogramas vienen de la pantalla. Véase [Las reglas](rules.md). Lo que el usuario apunte con las herramientas sigue sujeto a la licencia y al EULA de ese juego, y esa obligación recae en quien ejecute la herramienta.
