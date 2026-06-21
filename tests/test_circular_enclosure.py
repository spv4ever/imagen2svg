import cv2
import numpy as np

from src.processing.preprocess import PreprocessResult, VectorMode, _binary_from_gray
from src.processing.vectorize import vectorize_to_svg


def test_flooded_circle_keeps_inner_artwork_visible():
    image = np.full((220, 220), 255, np.uint8)
    cv2.circle(image, (110, 110), 82, 95, -1)
    cv2.circle(image, (110, 110), 82, 0, 3)
    cv2.line(image, (80, 110), (140, 110), 0, 4)
    cv2.line(image, (110, 80), (110, 140), 0, 4)

    bitmap = _binary_from_gray(image)
    svg = vectorize_to_svg(
        PreprocessResult(mode=VectorMode.SIMPLE, bitmap=bitmap, preview=None),
        title="flooded-circle",
    )

    assert bitmap.mean() > 220
    assert 'fill="none"' in svg
    assert svg.count("<path") >= 2


def test_solid_black_circle_stays_filled():
    image = np.full((200, 200), 255, np.uint8)
    cv2.circle(image, (100, 100), 70, 0, -1)

    bitmap = _binary_from_gray(image)
    svg = vectorize_to_svg(
        PreprocessResult(mode=VectorMode.SIMPLE, bitmap=bitmap, preview=None),
        title="solid-black-circle",
    )

    assert bitmap[100, 100] == 0
    assert 'fill="#000000"' in svg
    assert 'fill="none"' not in svg
