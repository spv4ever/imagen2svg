# imagen2svg

Conversor local para exportar imágenes PNG como SVG plain usando únicamente Inkscape.

## Flujo actual

1. Arrastra o selecciona imágenes PNG.
2. Revisa la vista previa del PNG original.
3. Procesa el lote.
4. Cada PNG se envía directamente a Inkscape y se exporta como SVG plain.

## Requisito obligatorio

La aplicación requiere el ejecutable `inkscape` disponible en el `PATH`. No hay modos alternativos ni vectorizador interno de respaldo: si Inkscape no está disponible o falla, la exportación se detiene para evitar resultados distintos al SVG plain generado por Inkscape.

El comando de exportación usa los parámetros estándar de Inkscape para SVG plain:

```bash
inkscape archivo.png --export-type=svg --export-plain-svg --export-filename=salida.svg
```

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
