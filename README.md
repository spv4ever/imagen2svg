# imagen2svg

Vectorizador local y gratuito para convertir imágenes PNG/JPG en SVG y PNG limpio.

## Flujo inicial

1. Arrastra o selecciona imágenes PNG/JPG.
2. Revisa la vista previa original y procesada.
3. Elige un modo de vectorización.
4. Procesa el lote.
5. Exporta un SVG y un PNG limpio por archivo.
6. Si tienes Inkscape instalado, activa la exportación como SVG plano para reexportar el SVG final con los parámetros estándar de Inkscape.

## Modos incluidos

- **SVG simple**: blanco/negro con contraste local para separar mejor sujeto y fondo.
- **SVG limpio**: reducción de ruido, cierre de huecos pequeños y suavizado antes de vectorizar.
- **SVG impresión 3D**: máximo contraste, líneas más sólidas y cierre de cortes pequeños.
- **SVG por colores**: cuantización adaptativa, color de fondo separado y creación de trazados por color.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Integración opcional con Inkscape

La interfaz detecta el ejecutable `inkscape` en el `PATH`. Si está disponible, marca por defecto **Exportar SVG plano con Inkscape** y, al exportar, primero genera el SVG con el vectorizador interno y después pide a Inkscape que lo reescriba como SVG plano con sus parámetros estándar (`--export-type=svg`, `--export-plain-svg` y `--export-filename`). Así el resultado sigue siendo vectorial y queda normalizado como plain SVG de Inkscape.

Si Inkscape no está disponible o falla la reexportación como SVG plano, la aplicación conserva automáticamente el SVG generado por el vectorizador interno. Si la casilla aparece desactivada, instala Inkscape o añade su ejecutable al `PATH` antes de lanzar la aplicación.

## Uso

```bash
python app.py
```

La aplicación crea y usa las carpetas `input/`, `output/` y `temp/` para organizar imágenes, exportaciones y vistas previas temporales.
