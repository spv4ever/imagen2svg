from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.output.export_manager import SUPPORTED_EXTENSIONS, export_batch, export_file
from src.processing.inkscape import (
    InkscapeNotFoundError,
    build_plain_svg_command,
    export_plain_svg,
)


def test_supported_extensions_include_png_and_jpeg():
    assert SUPPORTED_EXTENSIONS == {".png", ".jpg", ".jpeg"}


def test_build_plain_svg_command_uses_standard_inkscape_args(tmp_path):
    source = tmp_path / "input.png"
    destination = tmp_path / "output.svg"

    command = build_plain_svg_command(source, destination, executable="inkscape")

    assert command == [
        "inkscape",
        str(source),
        "--export-type=svg",
        "--export-plain-svg",
        f"--export-filename={destination}",
    ]


def test_export_plain_svg_runs_inkscape_and_returns_destination(tmp_path):
    source = tmp_path / "photo.jpeg"
    source.write_bytes(b"jpeg")
    destination = tmp_path / "out" / "photo.svg"

    def fake_run(command, check, stdout, stderr, text):
        destination.write_text("<svg />", encoding="utf-8")
        return Mock(returncode=0)

    with patch("src.processing.inkscape.find_inkscape", return_value="inkscape"), patch(
        "src.processing.inkscape.subprocess.run", side_effect=fake_run
    ) as run:
        assert export_plain_svg(source, destination) == destination

    run.assert_called_once()
    assert run.call_args.args[0] == [
        "inkscape",
        str(source),
        "--export-type=svg",
        "--export-plain-svg",
        f"--export-filename={destination}",
    ]


def test_export_plain_svg_requires_inkscape(tmp_path):
    source = tmp_path / "image.png"
    source.write_bytes(b"png")

    with patch("src.processing.inkscape.find_inkscape", return_value=None):
        with pytest.raises(InkscapeNotFoundError):
            export_plain_svg(source, tmp_path / "image.svg")


def test_export_file_rejects_unsupported_formats(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("nope", encoding="utf-8")

    with pytest.raises(ValueError):
        export_file(source, tmp_path)


def test_export_batch_skips_unsupported_files(tmp_path):
    png = tmp_path / "one.png"
    jpg = tmp_path / "two.jpg"
    txt = tmp_path / "skip.txt"
    for path in (png, jpg, txt):
        path.write_bytes(b"data")

    with patch("src.output.export_manager.export_plain_svg") as export_plain_svg_mock:
        export_plain_svg_mock.side_effect = lambda source, destination: Path(destination)
        results = export_batch([png, jpg, txt], tmp_path / "out")

    assert results == [tmp_path / "out" / "one.svg", tmp_path / "out" / "two.svg"]
