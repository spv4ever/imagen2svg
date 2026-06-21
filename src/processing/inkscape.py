"""Inkscape command-line integration for Fusion 360-friendly SVG export."""

from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

TRACE_BITMAP_ACTION = "selection-trace:2,false,true,true,4,1.0,0.20"
STANDARD_EXPORT_ARGS = ("--export-type=svg", "--export-plain-svg")
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

PRESENTATION_ATTRIBUTES = {
    "fill",
    "fill-opacity",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-opacity",
    "opacity",
    "fill-rule",
    "clip-rule",
}
REMOVED_TAGS = {"metadata", "desc", "title"}
UNSUPPORTED_RENDERING_TAGS = {"filter", "mask", "pattern", "clipPath", "image"}
FUSION_GEOMETRY_TAGS = {
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
}
FUSION_ATTRIBUTE_PREFIXES = (
    "{http://www.inkscape.org/namespaces/inkscape}",
    "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}",
)
FUSION_ATTRIBUTES_TO_DROP = {
    "class",
    "filter",
    "mask",
    "clip-path",
    "clip-rule",
    "style",
    "display",
    "visibility",
}
STYLE_SPLIT_RE = re.compile(r"\s*;\s*")
STYLE_PAIR_RE = re.compile(r"\s*([^:]+)\s*:\s*(.*?)\s*$")


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
        "--batch-process",
        f"--actions={_build_trace_actions(destination)}",
        *STANDARD_EXPORT_ARGS,
        f"--export-filename={destination}",
    ]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if tag.startswith("{") else tag


def _style_to_attributes(element: ET.Element) -> None:
    style = element.attrib.get("style")
    if not style:
        return

    for chunk in STYLE_SPLIT_RE.split(style.strip()):
        if not chunk:
            continue
        match = STYLE_PAIR_RE.fullmatch(chunk)
        if not match:
            continue
        key, value = match.groups()
        if key in PRESENTATION_ATTRIBUTES and key not in element.attrib:
            element.set(key, value)


def _remove_unhelpful_children(element: ET.Element) -> None:
    for child in list(element):
        child_name = _local_name(child.tag)
        if child_name in REMOVED_TAGS or child_name in UNSUPPORTED_RENDERING_TAGS:
            element.remove(child)
            continue
        _remove_unhelpful_children(child)


def _strip_fusion_unfriendly_attributes(element: ET.Element) -> None:
    _style_to_attributes(element)
    for attribute in list(element.attrib):
        local_attribute = _local_name(attribute)
        if (
            attribute.startswith(FUSION_ATTRIBUTE_PREFIXES)
            or local_attribute in FUSION_ATTRIBUTES_TO_DROP
        ):
            del element.attrib[attribute]
    for child in element:
        _strip_fusion_unfriendly_attributes(child)


def _contains_fusion_geometry(element: ET.Element) -> bool:
    return any(_local_name(node.tag) in FUSION_GEOMETRY_TAGS for node in element.iter())


def _contains_embedded_image(element: ET.Element) -> bool:
    return any(_local_name(node.tag) == "image" for node in element.iter())


def _build_trace_actions(destination: Path) -> str:
    return ";".join(
        (
            "select-all",
            TRACE_BITMAP_ACTION,
            f"export-filename:{destination}",
            "export-do",
        )
    )


def make_fusion360_compatible(svg_path: str | Path) -> Path:
    """Apply a conservative cleanup pass for Fusion 360 SVG import."""
    path = Path(svg_path)
    tree = ET.parse(path)
    root = tree.getroot()

    if _local_name(root.tag) != "svg":
        raise RuntimeError(f"El archivo no parece ser un SVG válido: {path}")

    _remove_unhelpful_children(root)
    _strip_fusion_unfriendly_attributes(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def export_plain_svg(
    input_path: str | Path,
    svg_path: str | Path,
    *,
    executable: str | None = None,
    fusion360_pass: bool = True,
) -> Path:
    """Trace a PNG/JPEG bitmap in Inkscape, export plain SVG, then clean it."""
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
        raise RuntimeError(
            f"Inkscape no pudo exportar {source.name}: {details}"
        ) from error

    if not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError(f"Inkscape terminó sin crear un SVG válido: {destination}")

    if fusion360_pass:
        root = ET.parse(destination).getroot()
        had_embedded_image = _contains_embedded_image(root)
        make_fusion360_compatible(destination)
        root = ET.parse(destination).getroot()
        if not _contains_fusion_geometry(root):
            if had_embedded_image:
                raise RuntimeError(
                    "Inkscape exportó solo la imagen incrustada y no generó trazado "
                    "vectorial. Revisa que tu versión de Inkscape soporte la acción "
                    "selection-trace o vectoriza manualmente con Mapa de bits > "
                    "Vectorizar mapa de bits y exporta como Plain SVG."
                )
            raise RuntimeError(
                f"El SVG exportado no contiene geometría compatible: {destination}"
            )

    return destination
