"""Batch export orchestration for Fusion-compatible vector SVG files."""

from __future__ import annotations

from pathlib import Path

from src.processing.inkscape import plain_svg_with_inkscape
from src.processing.preprocess import VectorMode, preprocess
from src.processing.svg_cleaner import optimize_svg
from src.processing.vectorize import save_svg, vectorize_to_svg

SUPPORTED_EXTENSIONS = {".png"}


def export_file(input_path: str | Path, output_dir: str | Path) -> Path:
    """Trace a PNG to real SVG paths that CAD tools can import as geometry."""
    source = Path(input_path)
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported input format: {source.suffix}. Only PNG is supported."
        )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    svg_path = destination / f"{source.stem}.svg"
    result = preprocess(str(source), VectorMode.CLEAN)
    svg = optimize_svg(vectorize_to_svg(result, title=source.stem))
    save_svg(svg, svg_path)

    # Inkscape is useful for normalizing the file as plain SVG, but exporting a
    # PNG directly with Inkscape produces an embedded bitmap. Fusion 360 rejects
    # that kind of SVG because it does not contain sketch geometry. Keep the
    # traced paths as the source of truth and only run Inkscape as an optional
    # post-processor when it is installed.
    plain_svg_with_inkscape(svg_path)
    return svg_path


def export_batch(files: list[str | Path], output_dir: str | Path) -> list[Path]:
    return [
        export_file(path, output_dir)
        for path in files
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
    ]
