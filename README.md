# imagen2svg

Conversor local para transformar imágenes PNG en SVG vectoriales con trazados reales, pensados para importarse como geometría en herramientas CAD como Fusion 360.

## Flujo actual

1. Arrastra o selecciona imágenes PNG.
2. Revisa la vista previa del PNG original.
3. Procesa el lote.
4. Cada PNG se vectoriza con pasada simple, corte de luminosidad 0.450, motas 2, suavizado 1.00, optimización 0.200 y límite adaptativo de negro al 28%, generando elementos `<path>` dentro de un SVG.

## Compatibilidad con Fusion 360

Fusion 360 no puede crear un boceto útil desde un SVG que solo contiene una imagen PNG incrustada. Ese tipo de archivo se ve correctamente en algunos visores, pero no incluye curvas, líneas ni contornos importables como geometría.

La exportación de esta aplicación evita ese problema generando rutas vectoriales reales (`<path d="...">`) a partir de los contornos de la imagen, usando la configuración validada de Inkscape: pasada simple, modo Corte de luminosidad, umbral 0.450, Motas 2, Suavizar bordes 1.00, Optimizar 0.200 y límite adaptativo de negro al 28%. Inkscape ya no se usa para convertir directamente el PNG a SVG, porque ese flujo puede producir un SVG con mapa de bits incrustado. Si `inkscape` está disponible en el `PATH`, se usa únicamente como postprocesador opcional para normalizar el SVG ya vectorizado a SVG plain.

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
