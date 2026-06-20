"""Optional Inkscape CLI integration for SVG export/post-processing."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


STANDARD_EXPORT_ARGS = ("--export-type=svg", "--export-plain-svg")


def find_inkscape() -> str | None:
    """Return the Inkscape executable path if it is available on PATH."""
    return shutil.which("inkscape")


def is_inkscape_available() -> bool:
    """Return whether Inkscape can be launched from the current environment."""
    return find_inkscape() is not None


def _run_standard_svg_export(
    source: Path, destination: Path, *, executable: str | None = None
) -> bool:
    """Run Inkscape's standard plain-SVG export command."""
    inkscape = executable or find_inkscape()
    if not inkscape:
        return False
    if not source.exists():
        raise FileNotFoundError(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        inkscape,
        str(source),
        *STANDARD_EXPORT_ARGS,
        f"--export-filename={destination}",
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except (OSError, subprocess.CalledProcessError):
        return False
    return destination.exists() and destination.stat().st_size > 0


def export_image_with_inkscape(
    input_path: str | Path, svg_path: str | Path, *, executable: str | None = None
) -> bool:
    """Export an input image directly with Inkscape's standard SVG parameters.

    This lets Inkscape create the SVG from the original bitmap instead of first
    tracing it with OpenCV. The result preserves the source visually and avoids
    adding differences introduced by the internal vectorizer.
    """
    return _run_standard_svg_export(Path(input_path), Path(svg_path), executable=executable)


def plain_svg_with_inkscape(svg_path: str | Path, *, executable: str | None = None) -> bool:
    """Rewrite an SVG as Inkscape's plain SVG format.

    Returns True when Inkscape completed successfully and the file was replaced;
    returns False when Inkscape is unavailable or the command fails.
    """
    source = Path(svg_path)
    if not source.exists():
        raise FileNotFoundError(source)

    with tempfile.TemporaryDirectory(prefix="imagen2svg-inkscape-") as temp_dir:
        plain_svg = Path(temp_dir) / source.name
        if not _run_standard_svg_export(source, plain_svg, executable=executable):
            return False
        source.write_bytes(plain_svg.read_bytes())
        return True
