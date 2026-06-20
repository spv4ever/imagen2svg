"""Optional Inkscape CLI integration for SVG post-processing."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def find_inkscape() -> str | None:
    """Return the Inkscape executable path if it is available on PATH."""
    return shutil.which("inkscape")


def is_inkscape_available() -> bool:
    """Return whether Inkscape can be launched from the current environment."""
    return find_inkscape() is not None


def plain_svg_with_inkscape(svg_path: str | Path, *, executable: str | None = None) -> bool:
    """Rewrite an SVG as Inkscape's plain SVG format.

    Returns True when Inkscape completed successfully and the file was replaced;
    returns False when Inkscape is unavailable or the command fails.
    """
    inkscape = executable or find_inkscape()
    if not inkscape:
        return False

    source = Path(svg_path)
    if not source.exists():
        raise FileNotFoundError(source)

    with tempfile.TemporaryDirectory(prefix="imagen2svg-inkscape-") as temp_dir:
        plain_svg = Path(temp_dir) / source.name
        command = [
            inkscape,
            str(source),
            "--export-type=svg",
            "--export-plain-svg",
            f"--export-filename={plain_svg}",
        ]
        try:
            subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        except (OSError, subprocess.CalledProcessError):
            return False

        if not plain_svg.exists() or plain_svg.stat().st_size == 0:
            return False
        source.write_bytes(plain_svg.read_bytes())
        return True
