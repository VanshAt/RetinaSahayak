import cv2
import numpy as np
from typing import Tuple, List, Dict, Any
from backend.app.utils.image_utils import numpy_to_jpeg_bytes


def render_heatmap_and_overlay(
    img_rgb: np.ndarray,
    heatmap_2d: np.ndarray,
    alpha: float = 0.42,
    bounding_boxes: List[Dict[str, Any]] = None
) -> Tuple[bytes, bytes]:
    """
    Renders:
    1. Standalone colorized Grad-CAM++ heatmap JPEG bytes.
    2. Blended perceptual overlay (Fundus + Heatmap + optional lesion markers) JPEG bytes.
    """
    h, w, _ = img_rgb.shape

    # Ensure heatmap matches image spatial resolution
    if heatmap_2d.shape[:2] != (h, w):
        heatmap_resized = cv2.resize(heatmap_2d, (w, h), interpolation=cv2.INTER_LINEAR)
    else:
        heatmap_resized = heatmap_2d

    # Convert normalized [0, 1] float to [0, 255] uint8
    heatmap_uint8 = np.uint8(255 * np.clip(heatmap_resized, 0.0, 1.0))

    # Apply JET / TURBO colormap (OpenCV uses BGR, so convert to RGB)
    colormap_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    colormap_rgb = cv2.cvtColor(colormap_bgr, cv2.COLOR_BGR2RGB)

    # 1. Standalone Heatmap Bytes
    heatmap_bytes = numpy_to_jpeg_bytes(colormap_rgb, quality=90)

    # 2. Blended Perceptual Overlay
    overlay_rgb = cv2.addWeighted(img_rgb, 1.0 - alpha, colormap_rgb, alpha, 0)

    # Optional: Draw delicate lesion bounding boxes on the overlay
    if bounding_boxes:
        for box in bounding_boxes[:6]:  # Draw top 6 prominent boxes
            bx, by, bw, bh = box["x"], box["y"], box["width"], box["height"]
            color = (255, 255, 0) if box.get("lesion_type") == "MICROANEURYSM" else (255, 60, 60)
            cv2.rectangle(overlay_rgb, (bx, by), (bx + bw, by + bh), color, 2)

    overlay_bytes = numpy_to_jpeg_bytes(overlay_rgb, quality=92)

    return heatmap_bytes, overlay_bytes
