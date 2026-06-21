# imagen2svg

Aplicación local mínima para convertir imágenes PNG o JPEG a SVG mediante el trazado de mapa de bits de Inkscape y exportar el resultado como Plain SVG compatible con Fusion 360. La app no genera mallas de píxeles: replica el flujo de Inkscape de vectorizar mapa de bits y guardar como Plain SVG.

## Objetivo

1. Arrastra imágenes `.png`, `.jpg` o `.jpeg` a la ventana, o selecciónalas con el botón **Añadir imágenes**.
2. Pulsa **Vectorizar a Plain SVG**.
3. Elige una carpeta de salida.
4. La aplicación ejecuta Inkscape en modo batch para seleccionar la imagen, aplicar **Vectorizar mapa de bits** y exportar el resultado como Plain SVG:

```bash
inkscape entrada.png --batch-process --actions="select-all;selection-trace:2,false,true,true,4,1.0,0.20;export-filename:salida.svg;export-do" --export-type=svg --export-plain-svg --export-filename=salida.svg
```

5. Después aplica una segunda pasada sobre el SVG generado para conservar la geometría buena y quitar elementos que Fusion 360 suele rechazar: metadatos de Inkscape, estilos CSS, clases, filtros, máscaras, clips e imágenes incrustadas. Los estilos básicos de relleno y trazo se convierten a atributos SVG antes de eliminar el bloque `style`.
6. Si Inkscape no genera trazado vectorial y deja solo la imagen incrustada, la aplicación falla con un mensaje claro en vez de fabricar una malla de rectángulos.

## Requisitos

- Python 3.11 o superior.
- Inkscape instalado y disponible en el `PATH` como `inkscape`.

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

La aplicación crea los SVG en la carpeta de salida que selecciones, reutilizando el nombre base de cada imagen: `foto.png` se exporta como `foto.svg`.
