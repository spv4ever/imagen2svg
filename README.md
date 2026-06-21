# imagen2svg

Aplicación local mínima para convertir imágenes PNG o JPEG a SVG mediante Inkscape y aplicar una segunda pasada conservadora para mejorar la compatibilidad con Fusion 360.

## Objetivo

1. Arrastra imágenes `.png`, `.jpg` o `.jpeg` a la ventana, o selecciónalas con el botón **Añadir imágenes**.
2. Pulsa **Convertir a SVG Fusion 360**.
3. Elige una carpeta de salida.
4. La aplicación ejecuta Inkscape con la exportación plain SVG estándar:

```bash
inkscape entrada.png --export-type=svg --export-plain-svg --export-filename=salida.svg
```

5. Después aplica una segunda pasada sobre el SVG generado para conservar la geometría buena y quitar elementos que Fusion 360 suele rechazar: metadatos de Inkscape, estilos CSS, clases, filtros, máscaras y clips. Los estilos básicos de relleno y trazo se convierten a atributos SVG antes de eliminar el bloque `style`.

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
