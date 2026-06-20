"""Batch export orchestration using Inkscape only."""

from __future__ import annotations

from pathlib import Path

from src.processing.inkscape import export_image_with_inkscape

SUPPORTED_EXTENSIONS = {".png"}


def export_file(input_path: str | Path, output_dir: str | Path) -> Path:
    """Export a PNG directly to an Inkscape plain SVG."""
    source = Path(input_path)
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported input format: {source.suffix}. Only PNG is supported."
        )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    svg_path = destination / f"{source.stem}.svg"
    if not export_image_with_inkscape(source, svg_path):
        raise RuntimeError(
            "Inkscape is required to export PNG files as plain SVG. "
            "Install Inkscape or add its executable to PATH."
        )
    return svg_path


def export_batch(files: list[str | Path], output_dir: str | Path) -> list[Path]:
    return [
        export_file(path, output_dir)
        for path in files
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
    ]
