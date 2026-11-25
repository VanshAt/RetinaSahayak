import cv2
import numpy as np
from typing import Dict, Any


def assess_dme_risk(img_rgb: np.ndarray, predicted_grade: int) -> Dict[str, Any]:
    """
    Evaluates risk of Diabetic Macular Edema (DME) by detecting lipid hard exudates
    and estimating proximity to the foveal center (ETDRS guidelines).
    """
    h, w, _ = img_rgb.shape
    green = img_rgb[:, :, 1]
    red = img_rgb[:, :, 0]

    # 1. Candidate hard exudates appear bright in Green channel and yellow (high Red+Green)
    # Threshold upper percentile intensities in green channel while excluding the optic disc
    green_blur = cv2.GaussianBlur(green, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g_clahe = clahe.apply(green_blur)

    # High intensity mask for potential exudates
    _, exudate_cand = cv2.threshold(g_clahe, 210, 255, cv2.THRESH_BINARY)

    # 2. Approximate Optic Disc Location (brightest circular zone)
    # Erode to eliminate small exudates and find large disc contour
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    disc_cand = cv2.morphologyEx(red, cv2.MORPH_CLOSE, kernel)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(disc_cand)
    disc_center = max_loc  # (x, y)

    # Disc diameter approximation (typically ~ 1/6th of image width)
    disc_diameter = max(int(w / 6.5), 40)

    # Mask out the optic disc itself from exudate detection (within 1.2 disc diameters of disc center)
    cv2.circle(exudate_cand, disc_center, int(disc_diameter * 0.7), 0, -1)

    # 3. Fovea is anatomical center / temporally offset from disc
    # For fundus images, the macula/fovea is typically near center of image (w/2, h/2)
    fovea_center = (int(w / 2), int(h / 2))

    # Calculate distance of detected exudate pixels to foveal center
    exudate_coords = np.argwhere(exudate_cand > 0)
    has_exudates_near_macula = False
    min_dist_to_fovea = float("inf")
    exudates_count = len(exudate_coords)

    if exudates_count > 10:
        for y, x in exudate_coords[::5]:  # subsample for speed
            dist = np.sqrt((x - fovea_center[0])**2 + (y - fovea_center[1])**2)
            if dist < min_dist_to_fovea:
                min_dist_to_fovea = dist

        # Exudate within 1 disc diameter of fovea
        if min_dist_to_fovea <= disc_diameter:
            has_exudates_near_macula = True

    # 4. Stratify DME risk level based on clinical criteria and predicted DR grade
    if has_exudates_near_macula and predicted_grade >= 2:
        level = "SEVERE"
    elif has_exudates_near_macula or (exudates_count > 30 and predicted_grade >= 2):
        level = "MODERATE"
    elif predicted_grade >= 2 or exudates_count > 15:
        level = "MILD"
    else:
        level = "NONE"

    return {
        "level": level,
        "exudates_near_macula": has_exudates_near_macula,
        "fovea_proximity_disc_diameters": round(min_dist_to_fovea / disc_diameter, 2) if min_dist_to_fovea != float("inf") else 3.5,
        "candidate_exudate_count": exudates_count
    }
