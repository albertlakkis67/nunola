---
name: litofania-stl
description: Convierte una foto o imagen en un archivo STL imprimible en 3D, como litofanía (se ve al trasluz) o como relieve (la imagen sobresale). Usar cuando el usuario pida un STL, una litofanía, un relieve o una pieza para impresora 3D a partir de una foto.
---

# Litofanía o relieve STL a partir de una foto

Todo se genera en local con Python (numpy y Pillow), sin servicios externos.

## Pasos

1. Pregunta solo lo que falte (si no, usa los valores por defecto):
   - **Tipo:** `litofania` (retratos, fotos) o `relieve` (dibujos, logotipos).
   - **Ancho** en mm (por defecto 100).
   - **Encuadre:** proporción (`3:4`, `1:1`, `original`…) y qué centrar.
   - **Marco** y **agujero para colgar** (por defecto, los dos).
2. Comprueba que hay numpy y Pillow (`python3 -c "import numpy, PIL"`); si faltan, `pip install numpy pillow`.
3. Ejecuta el script del skill:

   ```
   python3 scripts/foto_a_stl.py FOTO SALIDA.stl --tipo litofania --ancho 100 --proporcion 3:4 --centro-y 0.55
   ```

   Opciones: `--tipo litofania|relieve`, `--ancho MM`, `--proporcion A:B|original`,
   `--centro-x` y `--centro-y` (0–1, punto de la foto que queda centrado al recortar),
   `--min MM` y `--max MM` (grosores), `--marco MM` (0 = sin marco), `--agujero MM`
   (diámetro, 0 = sin agujero), `--invertir` (en relieve, lo claro sube), `--res MM`
   (tamaño de píxel, por defecto 0,25).
4. El script comprueba que la malla es cerrada, guarda una vista previa
   `SALIDA_vista.png` (relieve sombreado + simulación al trasluz) y muestra medidas y volumen.
5. **Mira la vista previa** antes de entregar. Si el sujeto queda cortado o con poco contraste,
   ajusta `--centro-y`, `--proporcion` o los grosores y repite.
6. Entrega el STL y la vista previa, con las medidas y estos consejos de impresión:
   - Litofanía: filamento **blanco**, relleno **100 %**, capas de **0,12 mm** o menos,
     mejor impresa **de pie**, y mirarla con luz detrás.
   - Relieve: cualquier color; capas de 0,12–0,16 mm para más detalle.
