# imagen2svg

Conversor local para transformar imágenes PNG en SVG vectoriales con trazados reales, pensados para importarse como geometría en herramientas CAD como Fusion 360.

## Flujo actual

1. Arrastra o selecciona imágenes PNG.
2. Revisa la vista previa del PNG original.
3. Procesa el lote.
4. Cada PNG se vectoriza por defecto en modo Mejorado, que aplica limpieza morfológica antes de generar rutas. También puedes elegir Simple, Impresión 3D o Colores desde la interfaz. Todos los modos generan elementos `<path>` dentro de un SVG.

## Compatibilidad con Fusion 360

Fusion 360 no puede crear un boceto útil desde un SVG que solo contiene una imagen PNG incrustada. Ese tipo de archivo se ve correctamente en algunos visores, pero no incluye curvas, líneas ni contornos importables como geometría.

La exportación de esta aplicación evita ese problema generando rutas vectoriales reales (`<path d="...">`) a partir de los contornos de la imagen, usando por defecto el modo Mejorado: corte de luminosidad 0.450, Motas 2, Suavizar bordes 1.00, Optimizar 0.200, límite adaptativo de negro al 28% y una limpieza extra para cerrar pequeños cortes y reducir ruido. El modo Simple conserva la pasada básica cuando se quiere comparar el resultado anterior. Inkscape ya no se usa para convertir directamente el PNG a SVG, porque ese flujo puede producir un SVG con mapa de bits incrustado. Si `inkscape` está disponible en el `PATH`, se usa únicamente como postprocesador opcional para normalizar el SVG ya vectorizado a SVG plain.

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

El selector de modo permite cambiar entre `Mejorado`, `Simple`, `Impresión 3D` y `Colores` antes de procesar el lote.

La aplicación crea y usa las carpetas `input/`, `output/` y `temp/` para organizar imágenes, exportaciones y vistas previas temporales.
