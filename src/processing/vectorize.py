"""SVG vectorization helpers."""

from __future__ import annotations

import html
from pathlib import Path

import cv2
import numpy as np

from src.processing.preprocess import PreprocessResult, TraceSettings, VectorMode


def _format_number(value: float) -> str:
    """Format SVG coordinates compactly without losing sub-pixel precision."""

    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_path(points: np.ndarray) -> str:
    commands = [
        f"M {_format_number(float(points[0][0]))} {_format_number(float(points[0][1]))}"
    ]
    commands.extend(
        f"L {_format_number(float(x))} {_format_number(float(y))}" for x, y in points[1:]
    )
    commands.append("Z")
    return " ".join(commands)


def _ellipse_path(contour: np.ndarray) -> str | None:
    """Return an SVG arc path for contours that are well described by an ellipse."""

    if len(contour) < 12:
        return None

    area = abs(cv2.contourArea(contour))
    perimeter = cv2.arcLength(contour, True)
    if area <= 0 or perimeter <= 0:
        return None

    circularity = 4.0 * np.pi * area / (perimeter * perimeter)
    if circularity < 0.72:
        return None

    (center_x, center_y), (diameter_a, diameter_b), angle = cv2.fitEllipse(contour)
    radius_x = diameter_a / 2.0
    radius_y = diameter_b / 2.0
    if radius_x < 2.0 or radius_y < 2.0:
        return None

    ellipse_area = np.pi * radius_x * radius_y
    area_ratio = area / ellipse_area if ellipse_area else 0.0
    if not 0.78 <= area_ratio <= 1.22:
        return None

    radians = np.deg2rad(angle)
    offset_x = radius_x * np.cos(radians)
    offset_y = radius_x * np.sin(radians)
    start_x = center_x + offset_x
    start_y = center_y + offset_y
    end_x = center_x - offset_x
    end_y = center_y - offset_y
    return (
        f"M {_format_number(start_x)} {_format_number(start_y)} "
        f"A {_format_number(radius_x)} {_format_number(radius_y)} "
        f"{_format_number(angle)} 1 0 {_format_number(end_x)} {_format_number(end_y)} "
        f"A {_format_number(radius_x)} {_format_number(radius_y)} "
        f"{_format_number(angle)} 1 0 {_format_number(start_x)} {_format_number(start_y)} Z"
    )


def _is_large_solid_ellipse_artifact(
    contour: np.ndarray,
    *,
    image_area: int,
    has_child: bool,
    foreground_density: float,
) -> bool:
    """Detect filled circular/elliptical blobs caused by failed enclosure tracing.

    Circular badges should normally trace as an outline with one or more white
    child contours. When thresholding loses those children, the SVG becomes a
    solid black disk. Skip only large, very ellipse-like contours that have no
    children so interior artwork and legitimate ring paths are preserved.
    """

    if has_child or len(contour) < 12 or image_area <= 0:
        return False

    # A legitimate filled black circle is dense foreground inside its contour.
    # Failed enclosure recovery leaves only a thin circular outline whose contour
    # still encloses a large area, so its actual foreground density is low.
    if foreground_density >= 0.45:
        return False

    area = abs(cv2.contourArea(contour))
    if area / float(image_area) < 0.18:
        return False

    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return False

    circularity = 4.0 * np.pi * area / (perimeter * perimeter)
    if circularity < 0.82:
        return False

    (_, _), (diameter_a, diameter_b), _ = cv2.fitEllipse(contour)
    longer = max(diameter_a, diameter_b)
    shorter = min(diameter_a, diameter_b)
    if shorter <= 0:
        return False

    return (shorter / longer) >= 0.72


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
        has_child = hierarchy[0][index][2] != -1
        if parent != -1 or cv2.contourArea(contour) < min_area:
            continue
        contour_area = abs(cv2.contourArea(contour))
        contour_mask = np.zeros_like(foreground)
        cv2.drawContours(contour_mask, [contour], -1, 255, -1)
        foreground_pixels = cv2.countNonZero(cv2.bitwise_and(foreground, contour_mask))
        foreground_density = (
            foreground_pixels / contour_area if contour_area > 0 else 0.0
        )
        if _is_large_solid_ellipse_artifact(
            contour,
            image_area=image_area,
            has_child=False,
            foreground_density=foreground_density,
        ):
            ellipse = _ellipse_path(
                (contour - np.array([[[1, 1]]], dtype=contour.dtype)).astype(
                    np.float32
                )
            )
            if ellipse:
                path_data = html.escape(ellipse)
                paths.append(
                    f'<path d="{path_data}" fill="none" stroke="{fill}" '
                    'stroke-width="1" vector-effect="non-scaling-stroke"/>'
                )
            continue

        subpaths: list[str] = []
        stack = [index]
        while stack:
            current = stack.pop()
            current_contour = contours[current] - np.array(
                [[[1, 1]]], dtype=contours[current].dtype
            )
            if cv2.contourArea(current_contour) >= min_area:
                current_contour = current_contour.astype(np.float32)
                current_contour[:, :, 0] = np.clip(
                    current_contour[:, :, 0], 0, mask.shape[1] - 1
                )
                current_contour[:, :, 1] = np.clip(
                    current_contour[:, :, 1], 0, mask.shape[0] - 1
                )
                ellipse = _ellipse_path(current_contour)
                if ellipse:
                    subpaths.append(ellipse)
                    continue

                epsilon = max(0.15, settings.optimize_tolerance)
                approx = cv2.approxPolyDP(current_contour, epsilon, True)
                points = approx.reshape(-1, 2)
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
