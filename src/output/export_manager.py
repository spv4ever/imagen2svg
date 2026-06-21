"""Batch export orchestration for Inkscape plain SVG conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.processing.inkscape import export_plain_svg

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class BatchExportSummary:
    """Results from a batch export that keeps processing after per-file errors."""

    exported: list[Path]
    errors: list[str]

    @property
    def failed_count(self) -> int:
        """Return how many files failed during export."""
        return len(self.errors)


def export_file(input_path: str | Path, output_dir: str | Path) -> Path:
    """Convert a supported image into a plain SVG using Inkscape defaults."""
    source = Path(input_path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Formato no soportado: {suffix}. Usa: {supported}.")

    destination_dir = Path(output_dir)
    svg_path = destination_dir / f"{source.stem}.svg"
    return export_plain_svg(source, svg_path)


def export_batch(files: list[str | Path], output_dir: str | Path) -> list[Path]:
    """Export every supported image in order."""
    return [
        export_file(path, output_dir)
        for path in files
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def export_batch_resilient(
    files: list[str | Path], output_dir: str | Path
) -> BatchExportSummary:
    """Export supported images and collect per-file errors without aborting the batch."""
    exported: list[Path] = []
    errors: list[str] = []

    for path in files:
        source = Path(path)
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            exported.append(export_file(source, output_dir))
        except Exception as error:  # noqa: BLE001
            errors.append(f"{source.name}: {error}")

    return BatchExportSummary(exported=exported, errors=errors)
