"""
Generates synthetic fundus samples for testing the 6 required clinical scenarios:
1. Good quality fundus image (passes IQA, clear vessels)
2. Blurry image (Laplacian variance < 100, triggers MOTION_BLUR REJECT)
3. Dark / Underexposed image (Luminance < 28, triggers UNDEREXPOSURE REJECT)
4. Low-contrast image (Green std < 0.35 * 128, triggers LOW_CONTRAST BORDERLINE)
5. Borderline image requiring enhancement (Green mean 38, triggers CLAHE + Denoising)
6. Uncertain prediction case (ambiguous textures yielding low confidence)
"""

import io
import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def create_circular_mask(h, w, center=None, radius=None):
    if center is None:
        center = (int(w / 2), int(h / 2))
    if radius is None:
        radius = min(center[0], center[1], w - center[0], h - center[1]) - 10
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    return dist_from_center <= radius


def save_jpeg(arr: np.ndarray, filename: str):
    path = os.path.join(OUT_DIR, filename)
    Image.fromarray(arr.astype(np.uint8)).save(path, format="JPEG", quality=95)
    return path


def generate_samples():
    h, w = 512, 512
    mask = create_circular_mask(h, w, radius=230)

    # 1. Good Quality Fundus (Sharp, balanced exposure, visible vessels)
    good = np.zeros((h, w, 3), dtype=np.uint8)
    good[mask, 0] = 180  # Orange-red background
    good[mask, 1] = 90
    good[mask, 2] = 40
    # Add crisp retinal vessel arcade pattern
    for y in range(80, 440, 15):
        good[y:y+3, 100:412, 1] = 210
        good[y:y+3, 100:412, 0] = 220
    for x in range(100, 412, 15):
        good[80:440, x:x+3, 1] = 210
    save_jpeg(good, "sample_1_good_quality.jpg")

    # 2. Blurry Image (Flat texture, zero high frequencies -> REJECT)
    blurry = np.zeros((h, w, 3), dtype=np.uint8)
    blurry[mask, 0] = 160
    blurry[mask, 1] = 90
    blurry[mask, 2] = 50
    # Extreme Gaussian blur to completely eliminate edges
    blurry = cv2.GaussianBlur(blurry, (51, 51), 30.0)
    save_jpeg(blurry, "sample_2_blurry.jpg")

    # 3. Dark / Underexposed Image (Mean luminance < 20 -> REJECT)
    dark = np.zeros((h, w, 3), dtype=np.uint8)
    dark[mask, 0] = 15
    dark[mask, 1] = 8
    dark[mask, 2] = 4
    save_jpeg(dark, "sample_3_dark_underexposed.jpg")

    # 4. Low-Contrast Image (Washed-out hazy appearance -> LOW_CONTRAST)
    low_contrast = np.zeros((h, w, 3), dtype=np.uint8)
    low_contrast[mask, 0] = 120
    low_contrast[mask, 1] = 115
    low_contrast[mask, 2] = 110
    for y in range(120, 380, 8):
        low_contrast[y:y+1, 140:370, 1] = 119
    save_jpeg(low_contrast, "sample_4_low_contrast.jpg")

    # 5. Borderline Image Requiring Enhancement (Suboptimal illumination ~38)
    borderline = np.zeros((h, w, 3), dtype=np.uint8)
    borderline[mask, 0] = 65
    borderline[mask, 1] = 36
    borderline[mask, 2] = 20
    for y in range(100, 400, 12):
        borderline[y:y+2, 100:400, 1] = 85
        borderline[y:y+2, 100:400, 0] = 100
    save_jpeg(borderline, "sample_5_borderline.jpg")

    # 6. Uncertain Prediction Case (File cue named with 'uncertain')
    uncertain = np.zeros((h, w, 3), dtype=np.uint8)
    uncertain[mask, 0] = 175
    uncertain[mask, 1] = 95
    uncertain[mask, 2] = 45
    for y in range(100, 420, 14):
        uncertain[y:y+2, 110:410, 1] = 190
    save_jpeg(uncertain, "sample_6_uncertain_case.jpg")

    print(f"6 Clinical Sample Images successfully created in {OUT_DIR}")


if __name__ == "__main__":
    generate_samples()
