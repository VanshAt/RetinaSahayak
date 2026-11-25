import cv2
import numpy as np


def enhance_retinal_image(img_rgb: np.ndarray) -> np.ndarray:
    """
    Applies Green-channel CLAHE, median denoising, and Ben Graham local contrast normalization
    to restore borderline or low-contrast retinal fundus photographs.
    """
    # 1. Circular mask detection to protect black periphery
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    # 2. Denoise with fast median filtering
    denoised_rgb = cv2.medianBlur(img_rgb, 3)

    # 3. Extract Green Channel
    r, g, b = cv2.split(denoised_rgb)

    # 4. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to Green
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    g_enhanced = clahe.apply(g)

    # 5. Reconstruct image with enhanced green channel
    enhanced_merged = cv2.merge([r, g_enhanced, b])

    # 6. Ben Graham Contrast Normalization: 4*I - 4*Gaussian(I, sigma=10) + 128
    gaussian_blur = cv2.GaussianBlur(enhanced_merged, (0, 0), sigmaX=10)
    ben_graham = cv2.addWeighted(enhanced_merged, 4, gaussian_blur, -4, 128)

    # 7. Apply circular mask so outside borders remain clean black
    enhanced_final = cv2.bitwise_and(ben_graham, ben_graham, mask=mask)

    return enhanced_final
