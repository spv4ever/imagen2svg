# imagen2svg

Vectorizador local y gratuito para convertir imágenes PNG/JPG en SVG y PNG limpio.

## Flujo inicial

1. Arrastra o selecciona imágenes PNG/JPG.
2. Revisa la vista previa original y procesada.
3. Elige un modo de vectorización.
4. Procesa el lote.
5. Exporta un SVG y un PNG limpio por archivo.

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

## Uso

```bash
python app.py
```

La aplicación crea y usa las carpetas `input/`, `output/` y `temp/` para organizar imágenes, exportaciones y vistas previas temporales.
