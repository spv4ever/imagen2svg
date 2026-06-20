# imagen2svg

Vectorizador local y gratuito para convertir imágenes PNG/JPG en SVG y PNG limpio.

## Flujo inicial

1. Arrastra o selecciona imágenes PNG/JPG.
2. Revisa la vista previa original y procesada.
3. Elige un modo de vectorización.
4. Procesa el lote.
5. Exporta un SVG y un PNG limpio por archivo.
6. Si tienes Inkscape instalado, activa la optimización opcional para reescribir el SVG como “plain SVG”.

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

La interfaz detecta el ejecutable `inkscape` en el `PATH`. Si está disponible, marca por defecto **Optimizar SVG con Inkscape** y, al exportar, pasa cada SVG generado por Inkscape con `--export-plain-svg`. Esto normaliza el SVG final y suele mejorar la compatibilidad con otros programas sin obligarte a instalar dependencias adicionales de Python.

Si la casilla aparece desactivada, instala Inkscape o añade su ejecutable al `PATH` antes de lanzar la aplicación.

## Uso

```bash
python app.py
```

La aplicación crea y usa las carpetas `input/`, `output/` y `temp/` para organizar imágenes, exportaciones y vistas previas temporales.
