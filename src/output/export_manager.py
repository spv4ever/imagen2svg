"""Batch export orchestration."""

from __future__ import annotations

from pathlib import Path

from src.processing.inkscape import export_image_with_inkscape
from src.processing.preprocess import VectorMode, preprocess
from src.processing.svg_cleaner import optimize_svg
from src.processing.vectorize import save_svg, vectorize_to_svg


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def export_file(
    input_path: str | Path,
    output_dir: str | Path,
    mode: VectorMode,
    *,
    use_inkscape: bool = False,
) -> tuple[Path, Path]:
    source = Path(input_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    result = preprocess(str(source), mode)
    stem = f"{source.stem}-{mode.value}"
    svg_path = destination / f"{stem}.svg"
    png_path = destination / f"{stem}-clean.png"

    if use_inkscape and export_image_with_inkscape(source, svg_path):
        pass
    else:
        svg = optimize_svg(vectorize_to_svg(result, title=source.name))
        save_svg(svg, svg_path)
    result.preview.save(png_path)
    return svg_path, png_path


def export_batch(
    files: list[str | Path],
    output_dir: str | Path,
    mode: VectorMode,
    *,
    use_inkscape: bool = False,
) -> list[tuple[Path, Path]]:
    return [
        export_file(path, output_dir, mode, use_inkscape=use_inkscape)
        for path in files
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
    ]
