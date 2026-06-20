"""SVG vectorization helpers."""

from __future__ import annotations

import html
from pathlib import Path

import cv2
import numpy as np

from src.processing.preprocess import PreprocessResult, VectorMode


def _contours_to_paths(mask: np.ndarray, fill: str = "#000000") -> list[str]:
    foreground = cv2.bitwise_not(mask) if np.mean(mask) > 127 else mask
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    paths: list[str] = []
    for contour in contours:
        if cv2.contourArea(contour) < 4:
            continue
        epsilon = 0.002 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        points = approx.reshape(-1, 2)
        if len(points) < 3:
            continue
        commands = [f"M {points[0][0]} {points[0][1]}"]
        commands.extend(f"L {x} {y}" for x, y in points[1:])
        commands.append("Z")
        paths.append(f'<path d="{html.escape(" ".join(commands))}" fill="{fill}"/>')
    return paths


def vectorize_to_svg(result: PreprocessResult, title: str | None = None) -> str:
    bitmap = result.bitmap
    height, width = bitmap.shape[:2]
    title_markup = f"<title>{html.escape(title)}</title>" if title else ""

    if result.mode == VectorMode.COLORS and result.color_layers:
        paths: list[str] = []
        for color, mask in result.color_layers:
            paths.extend(_contours_to_paths(mask, fill=color))
    else:
        paths = _contours_to_paths(bitmap, fill="#000000")

    body = "\n  ".join(paths) if paths else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">\n'
        f"  {title_markup}\n"
        f"  {body}\n"
        "</svg>\n"
    )


def save_svg(svg: str, path: str | Path) -> None:
    Path(path).write_text(svg, encoding="utf-8")
