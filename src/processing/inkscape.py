"""Inkscape command-line integration for plain SVG export."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

STANDARD_EXPORT_ARGS = ("--export-type=svg", "--export-plain-svg")


class InkscapeNotFoundError(RuntimeError):
    """Raised when the Inkscape executable cannot be found."""


def find_inkscape() -> str | None:
    """Return the Inkscape executable path when it is available on PATH."""
    return shutil.which("inkscape")


def build_plain_svg_command(
    source: Path,
    destination: Path,
    *,
    executable: str = "inkscape",
) -> list[str]:
    """Build the standard Inkscape command used by the application."""
    return [
        executable,
        str(source),
        *STANDARD_EXPORT_ARGS,
        f"--export-filename={destination}",
    ]


def export_plain_svg(
    input_path: str | Path,
    svg_path: str | Path,
    *,
    executable: str | None = None,
) -> Path:
    """Convert a PNG/JPEG image to a plain SVG with Inkscape defaults."""
    source = Path(input_path)
    destination = Path(svg_path)

    if not source.exists():
        raise FileNotFoundError(source)

    inkscape = executable or find_inkscape()
    if not inkscape:
        raise InkscapeNotFoundError(
            "No se encontró Inkscape en el PATH. Instala Inkscape o añade "
            "su ejecutable al PATH para poder exportar SVG plain."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = build_plain_svg_command(source, destination, executable=inkscape)
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or error.stdout.strip() or str(error)
        raise RuntimeError(f"Inkscape no pudo exportar {source.name}: {details}") from error

    if not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError(f"Inkscape terminó sin crear un SVG válido: {destination}")

    return destination
