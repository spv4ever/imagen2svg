"""Image preprocessing pipelines for the vectorizer modes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from PIL import Image


class VectorMode(str, Enum):
    SIMPLE = "simple"
    CLEAN = "clean"
    PRINT_3D = "print_3d"
    COLORS = "colors"


@dataclass(frozen=True)
class TraceSettings:
    """Settings equivalent to Inkscape's single-scan brightness cutoff trace."""

    brightness_threshold: float = 0.45
    speckles: int = 2
    smooth_corners: float = 1.0
    optimize_tolerance: float = 0.2
    max_foreground_ratio: float = 0.28


INKSCAPE_SINGLE_SCAN_SETTINGS = TraceSettings()


@dataclass(frozen=True)
class PreprocessResult:
    mode: VectorMode
    bitmap: np.ndarray
    preview: Image.Image
    trace_settings: TraceSettings = INKSCAPE_SINGLE_SCAN_SETTINGS
    color_layers: list[tuple[str, np.ndarray]] | None = None
    background_color: str | None = None


def load_image(path: str) -> np.ndarray:
    image = Image.open(path)
    has_alpha = image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        # Treat transparent canvas pixels as white so they are not traced as
        # black artwork.
        image = image.convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.alpha_composite(image)
        image = background.convert("RGB")
    else:
        image = image.convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _ensure_odd(value: int) -> int:
    return value if value % 2 else value + 1


def _foreground_is_light(gray: np.ndarray, thresholded: np.ndarray) -> bool:
    dark_pixels = gray[thresholded == 0]
    light_pixels = gray[thresholded == 255]
    if dark_pixels.size == 0 or light_pixels.size == 0:
        return False
    border = np.concatenate(
        [thresholded[0, :], thresholded[-1, :], thresholded[:, 0], thresholded[:, -1]]
    )
    background_is_light = np.mean(border) > 127
    return not background_is_light and float(light_pixels.mean()) > float(dark_pixels.mean())


def _remove_colored_annotations(image: np.ndarray) -> np.ndarray:
    """Turn saturated, non-neutral pixels into white before line-art tracing.

    Hand-marked references often contain red/blue guide circles or notes. In
    grayscale those colors become dark enough to be traced as real geometry, so
    remove highly saturated colored pixels for monochrome modes while keeping
    black, white and gray artwork untouched.
    """

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    colored = (saturation > 60) & (value > 45)
    cleaned = image.copy()
    cleaned[colored] = (255, 255, 255)
    return cleaned


def _binary_from_gray(
    gray: np.ndarray,
    *,
    clean: bool = False,
    settings: TraceSettings = INKSCAPE_SINGLE_SCAN_SETTINGS,
) -> np.ndarray:
    """Create a bitmap using the approved Inkscape Trace Bitmap settings.

    The reference configuration is a single scan with brightness cutoff at
    0.450, speckles enabled at 2 px, smooth corners at 1.00 and optimization at
    0.200. A light bilateral denoise plus unsharp mask is applied before the
    cutoff so edges stay crisp instead of being softened into irregular blobs.
    """

    height, width = gray.shape[:2]
    scale = max(height, width)
    blur_size = _ensure_odd(max(3, min(9, scale // 180))) if clean else 3
    denoised = cv2.bilateralFilter(gray, 5, 45, 45)
    blurred = cv2.GaussianBlur(denoised, (blur_size, blur_size), 0)
    sharp = cv2.addWeighted(denoised, 1.35, blurred, -0.35, 0)
    cutoff = int(round(np.clip(settings.brightness_threshold, 0.0, 1.0) * 255))
    thresholded = cv2.threshold(sharp, cutoff, 255, cv2.THRESH_BINARY)[1]

    foreground_is_dark = True
    if _foreground_is_light(gray, thresholded):
        thresholded = cv2.bitwise_not(thresholded)
        foreground_is_dark = False

    # If the fixed 0.450 cutoff floods the trace, keep only the darkest (or
    # lightest, for inverted artwork) pixels so shadows/background texture do
    # not become large black fills.
    foreground_ratio = (
        np.count_nonzero(thresholded == 0)
        if foreground_is_dark
        else np.count_nonzero(thresholded == 255)
    ) / float(thresholded.size)
    max_foreground_ratio = np.clip(settings.max_foreground_ratio, 0.01, 0.95)
    if foreground_ratio > max_foreground_ratio:
        percentile = (
            max_foreground_ratio * 100.0
            if foreground_is_dark
            else (1.0 - max_foreground_ratio) * 100.0
        )
        balanced_cutoff = int(np.percentile(sharp, percentile))
        threshold_type = (
            cv2.THRESH_BINARY if foreground_is_dark else cv2.THRESH_BINARY_INV
        )
        thresholded = cv2.threshold(sharp, balanced_cutoff, 255, threshold_type)[1]

    if settings.speckles > 0:
        minimum_area = float(settings.speckles * settings.speckles)
        foreground = cv2.bitwise_not(thresholded) if foreground_is_dark else thresholded
        components, labels, stats, _ = cv2.connectedComponentsWithStats(foreground, 8)
        cleaned_foreground = np.zeros_like(foreground)
        for label in range(1, components):
            if stats[label, cv2.CC_STAT_AREA] >= minimum_area:
                cleaned_foreground[labels == label] = 255
        thresholded = (
            cv2.bitwise_not(cleaned_foreground)
            if foreground_is_dark
            else cleaned_foreground
        )

    if clean:
        kernel_size = max(2, min(5, scale // 260))
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
        thresholded = cv2.morphologyEx(
            thresholded, cv2.MORPH_CLOSE, kernel, iterations=1
        )
        thresholded = cv2.medianBlur(thresholded, 3)

    return thresholded


def _preview_from_bitmap(bitmap: np.ndarray) -> Image.Image:
    if len(bitmap.shape) == 2:
        return Image.fromarray(bitmap).convert("RGB")
    return Image.fromarray(cv2.cvtColor(bitmap, cv2.COLOR_BGR2RGB))


def _hex_from_bgr(color: np.ndarray) -> str:
    b, g, r = (int(channel) for channel in color)
    return f"#{r:02x}{g:02x}{b:02x}"


def _color_layers(image: np.ndarray) -> tuple[np.ndarray, list[tuple[str, np.ndarray]], str]:
    height, width = image.shape[:2]
    pixel_count = height * width
    k = min(8, max(2, pixel_count // 18_000))
    samples = image.reshape((-1, 3)).astype(np.float32)
    _, labels, centers = cv2.kmeans(
        samples,
        k,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 80, 0.1),
        5,
        cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(centers)
    flat_labels = labels.flatten()
    quantized = centers[flat_labels].reshape(image.shape)

    border_labels = np.concatenate(
        [flat_labels[:width], flat_labels[-width:], flat_labels[::width], flat_labels[width - 1 :: width]]
    )
    background_index = int(np.bincount(border_labels, minlength=k).argmax())
    background_color = _hex_from_bgr(centers[background_index])

    layers: list[tuple[str, np.ndarray]] = []
    for index in np.argsort(np.bincount(flat_labels, minlength=k))[::-1]:
        if int(index) == background_index:
            continue
        mask = np.where(flat_labels.reshape((height, width)) == index, 255, 0).astype(np.uint8)
        if cv2.countNonZero(mask) < 8:
            continue
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        layers.append((_hex_from_bgr(centers[index]), mask))
    return quantized, layers, background_color


def preprocess(path: str, mode: VectorMode) -> PreprocessResult:
    image = load_image(path)
    line_art_image = _remove_colored_annotations(image)
    gray = cv2.cvtColor(line_art_image, cv2.COLOR_BGR2GRAY)

    if mode == VectorMode.SIMPLE:
        bitmap = _binary_from_gray(gray)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.CLEAN:
        bitmap = _binary_from_gray(gray, clean=True)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.PRINT_3D:
        bitmap = cv2.adaptiveThreshold(
            cv2.GaussianBlur(gray, (5, 5), 0),
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            41,
            7,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bitmap = cv2.morphologyEx(bitmap, cv2.MORPH_CLOSE, kernel, iterations=2)
        bitmap = cv2.morphologyEx(bitmap, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.COLORS:
        quantized, layers, background_color = _color_layers(image)
        return PreprocessResult(
            mode=mode,
            bitmap=quantized,
            preview=_preview_from_bitmap(quantized),
            color_layers=layers,
            background_color=background_color,
        )

    raise ValueError(f"Unsupported vector mode: {mode}")
