"""SVG vectorization helpers."""

from __future__ import annotations

import html
from pathlib import Path

import cv2
import numpy as np

from src.processing.preprocess import PreprocessResult, TraceSettings, VectorMode


def _format_path(points: np.ndarray) -> str:
    commands = [f"M {int(points[0][0])} {int(points[0][1])}"]
    commands.extend(f"L {int(x)} {int(y)}" for x, y in points[1:])
    commands.append("Z")
    return " ".join(commands)


def _contours_to_paths(
    mask: np.ndarray,
    fill: str = "#000000",
    *,
    settings: TraceSettings,
) -> list[str]:
    foreground = cv2.bitwise_not(mask) if np.mean(mask) > 127 else mask
    foreground = cv2.copyMakeBorder(
        foreground, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0
    )
    contours, hierarchy = cv2.findContours(
        foreground, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS
    )
    if hierarchy is None:
        return []

    paths: list[str] = []
    image_area = mask.shape[0] * mask.shape[1]
    min_area = max(3.0, image_area * 0.00001)
    for index, contour in enumerate(contours):
        parent = hierarchy[0][index][3]
        if parent != -1 or cv2.contourArea(contour) < min_area:
            continue

        subpaths: list[str] = []
        stack = [index]
        while stack:
            current = stack.pop()
            current_contour = contours[current] - np.array(
                [[[1, 1]]], dtype=contours[current].dtype
            )
            if cv2.contourArea(current_contour) >= min_area:
                epsilon = max(0.35, settings.optimize_tolerance)
                approx = cv2.approxPolyDP(current_contour, epsilon, True)
                points = approx.reshape(-1, 2)
                points[:, 0] = np.clip(points[:, 0], 0, mask.shape[1] - 1)
                points[:, 1] = np.clip(points[:, 1], 0, mask.shape[0] - 1)
                if len(points) >= 3:
                    subpaths.append(_format_path(points))

            child = hierarchy[0][current][2]
            while child != -1:
                stack.append(child)
                child = hierarchy[0][child][0]

        if subpaths:
            path_data = html.escape(" ".join(subpaths))
            paths.append(f'<path d="{path_data}" fill="{fill}" fill-rule="evenodd"/>')
    return paths


def vectorize_to_svg(result: PreprocessResult, title: str | None = None) -> str:
    bitmap = result.bitmap
    height, width = bitmap.shape[:2]
    title_markup = f"<title>{html.escape(title)}</title>" if title else ""

    extra_markup = ""
    if result.mode == VectorMode.COLORS and result.color_layers:
        paths: list[str] = []
        if result.background_color:
            extra_markup = f'  <rect width="100%" height="100%" fill="{result.background_color}"/>\n'
        for color, mask in result.color_layers:
            paths.extend(
                _contours_to_paths(mask, fill=color, settings=result.trace_settings)
            )
    else:
        paths = _contours_to_paths(
            bitmap, fill="#000000", settings=result.trace_settings
        )

    body = "\n  ".join(paths) if paths else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">\n'
        f"  {title_markup}\n"
        f"{extra_markup}"
        f"  {body}\n"
        "</svg>\n"
    )


def save_svg(svg: str, path: str | Path) -> None:
    Path(path).write_text(svg, encoding="utf-8")
