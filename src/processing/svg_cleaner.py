"""Small SVG cleanup utilities."""

from __future__ import annotations

import re


def optimize_svg(svg: str) -> str:
    svg = re.sub(r"\s+", " ", svg).replace("> <", "><")
    return svg.strip() + "\n"
