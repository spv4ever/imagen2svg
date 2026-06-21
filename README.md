# imagen2svg

Aplicación local mínima para convertir imágenes PNG o JPEG a SVG plain mediante la línea de comandos de Inkscape.

## Objetivo

1. Arrastra imágenes `.png`, `.jpg` o `.jpeg` a la ventana, o selecciónalas con el botón **Añadir imágenes**.
2. Pulsa **Convertir a SVG plain**.
3. Elige una carpeta de salida.
4. La aplicación ejecuta Inkscape con los valores estándar de exportación plain SVG:

```bash
inkscape entrada.png --export-type=svg --export-plain-svg --export-filename=salida.svg
```

No se aplica vectorización propia, filtros OpenCV, limpieza adicional ni modos personalizados. El resultado queda exactamente delegado a Inkscape usando la exportación plain SVG estándar.

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
