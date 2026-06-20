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
class PreprocessResult:
    mode: VectorMode
    bitmap: np.ndarray
    preview: Image.Image
    color_layers: list[tuple[str, np.ndarray]] | None = None


def load_image(path: str) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _binary_from_gray(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def _preview_from_bitmap(bitmap: np.ndarray) -> Image.Image:
    if len(bitmap.shape) == 2:
        return Image.fromarray(bitmap).convert("RGB")
    return Image.fromarray(cv2.cvtColor(bitmap, cv2.COLOR_BGR2RGB))


def preprocess(path: str, mode: VectorMode) -> PreprocessResult:
    image = load_image(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if mode == VectorMode.SIMPLE:
        bitmap = _binary_from_gray(gray)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.CLEAN:
        bitmap = _binary_from_gray(gray)
        kernel = np.ones((3, 3), np.uint8)
        bitmap = cv2.morphologyEx(bitmap, cv2.MORPH_OPEN, kernel, iterations=1)
        bitmap = cv2.medianBlur(bitmap, 3)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.PRINT_3D:
        bitmap = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5
        )
        kernel = np.ones((5, 5), np.uint8)
        bitmap = cv2.morphologyEx(bitmap, cv2.MORPH_CLOSE, kernel, iterations=2)
        bitmap = cv2.erode(bitmap, np.ones((3, 3), np.uint8), iterations=1)
        return PreprocessResult(mode=mode, bitmap=bitmap, preview=_preview_from_bitmap(bitmap))

    if mode == VectorMode.COLORS:
        samples = image.reshape((-1, 3)).astype(np.float32)
        _, labels, centers = cv2.kmeans(
            samples,
            4,
            None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2),
            3,
            cv2.KMEANS_PP_CENTERS,
        )
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()].reshape(image.shape)
        layers: list[tuple[str, np.ndarray]] = []
        for center in centers:
            mask = cv2.inRange(quantized, center, center)
            hex_color = "#{:02x}{:02x}{:02x}".format(center[2], center[1], center[0])
            layers.append((hex_color, mask))
        return PreprocessResult(
            mode=mode,
            bitmap=quantized,
            preview=_preview_from_bitmap(quantized),
            color_layers=layers,
        )

    raise ValueError(f"Unsupported vector mode: {mode}")
