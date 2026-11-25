import cv2
import numpy as np
from typing import Dict, Any, List


def extract_candidate_lesions(
    img_rgb: np.ndarray,
    predicted_grade: int,
    heatmap_2d: np.ndarray = None
) -> Dict[str, Any]:
    """
    Extracts candidate microvascular lesions (microaneurysms, hemorrhages, exudates)
    and maps high-activation regions to retinal quadrants.
    """
    h, w, _ = img_rgb.shape
    center_x, center_y = w // 2, h // 2
    green = img_rgb[:, :, 1]

    # 1. Detect dark lesions (microaneurysms and hemorrhages) using Top-Hat morphological filtering
    # Bottom-hat / Black-hat transform extracts small dark elements on lighter background
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    blackhat_small = cv2.morphologyEx(green, cv2.MORPH_BLACKHAT, kernel_small)
    _, ma_mask = cv2.threshold(blackhat_small, 22, 255, cv2.THRESH_BINARY)

    # Larger kernel for blot hemorrhages
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    blackhat_large = cv2.morphologyEx(green, cv2.MORPH_BLACKHAT, kernel_large)
    _, he_mask = cv2.threshold(blackhat_large, 28, 255, cv2.THRESH_BINARY)

    # Exudates (bright in green)
    tophat_ex = cv2.morphologyEx(green, cv2.MORPH_TOPHAT, kernel_large)
    _, ex_mask = cv2.threshold(tophat_ex, 30, 255, cv2.THRESH_BINARY)

    # Combine with Grad-CAM heatmap if provided
    combined_focus = np.zeros((h, w), dtype=np.uint8)
    if heatmap_2d is not None:
        heat_uint8 = (cv2.resize(heatmap_2d, (w, h)) * 255).astype(np.uint8)
        _, heat_thresh = cv2.threshold(heat_uint8, 160, 255, cv2.THRESH_BINARY)
        combined_focus = cv2.bitwise_or(combined_focus, heat_thresh)

    # Extract bounding boxes from peak activations and lesion clusters
    merged_mask = cv2.bitwise_or(ma_mask, he_mask)
    if heatmap_2d is not None:
        merged_mask = cv2.bitwise_and(merged_mask, combined_focus)
        # Fallback if intersection is sparse: use heatmap contours directly
        if cv2.countNonZero(merged_mask) < 20:
            merged_mask = combined_focus

    contours, _ = cv2.findContours(merged_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes: List[Dict[str, Any]] = []
    suspicious_quadrants = set()

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 25 < area < (h * w * 0.15):  # Filter micro-noise and whole-image blobs
            x, y, bw, bh = cv2.boundingRect(cnt)
            bx_center = x + bw // 2
            by_center = y + bh // 2

            # Determine Quadrant (Assuming Right Eye OD: Temporal is Right x > center_x)
            is_superior = by_center < center_y
            is_temporal = bx_center > center_x

            if is_superior and is_temporal:
                quad = "SUPERIOR_TEMPORAL"
            elif not is_superior and is_temporal:
                quad = "INFERIOR_TEMPORAL"
            elif is_superior and not is_temporal:
                quad = "SUPERIOR_NASAL"
            else:
                quad = "INFERIOR_NASAL"

            suspicious_quadrants.add(quad)

            # Classify candidate lesion tag based on size & intensity
            lesion_type = "HEMORRHAGE" if area > 120 else "MICROANEURYSM"
            if np.mean(green[y:y+bh, x:x+bw]) > 140:
                lesion_type = "HARD_EXUDATE"

            bounding_boxes.append({
                "x": int(x),
                "y": int(y),
                "width": int(bw),
                "height": int(bh),
                "area": float(area),
                "quadrant": quad,
                "lesion_type": lesion_type
            })

    # Limit to top 15 most prominent lesion bounding boxes
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b["area"], reverse=True)[:15]

    # Clinical lesion presence flags aligned with ICDR grade
    has_ma = predicted_grade >= 1 or len(bounding_boxes) > 0
    has_he = predicted_grade >= 2
    has_ex = predicted_grade >= 2 and any(b["lesion_type"] == "HARD_EXUDATE" for b in bounding_boxes)
    has_nv = predicted_grade >= 4

    return {
        "microaneurysms_detected": has_ma,
        "blot_hemorrhages_detected": has_he,
        "hard_exudates_detected": has_ex,
        "cotton_wool_spots_detected": predicted_grade >= 3,
        "neovascularization_detected": has_nv,
        "suspicious_quadrants": list(suspicious_quadrants) if suspicious_quadrants else ["POSTERIOR_POLE"],
        "bounding_boxes": bounding_boxes
    }
