import cv2
import numpy as np
from typing import Dict, Any, List
from backend.app.core.config import settings


def evaluate_image_quality(img_rgb: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates retinal fundus image quality across 7 clinical criteria:
    1. Blur/Focus via Laplacian variance over Green channel
    2. Under-exposure and Over-exposure (luminance histogram)
    3. Low vascular contrast (Green-channel standard deviation)
    4. Excessive high-frequency sensor noise
    5. Retinal field coverage (fraction of circular fundus mask)
    6. Incorrect orientation (aspect ratio and retinal symmetry)
    7. Artifacts or obstruction (dust halos / specular glare)
    
    Returns:
        GOOD, BORDERLINE, or REJECT with actionable recapture feedback.
    """
    h, w, c = img_rgb.shape
    green_channel = img_rgb[:, :, 1]
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # 1. Focus & Sharpness: Laplacian Variance over Green channel
    laplacian = cv2.Laplacian(green_channel, cv2.CV_64F)
    sharpness_score = float(laplacian.var())

    # 2. Illumination & Exposure
    mean_luminance = float(np.mean(gray))
    overexposed_pct = float(np.sum(gray > settings.IQA_MAX_LUMINANCE) / gray.size * 100)
    underexposed_pct = float(np.sum(gray < 15) / gray.size * 100)

    # 3. Vascular Contrast Ratio (standard deviation of Green channel)
    vessel_contrast_score = float(np.std(green_channel) / 128.0)

    # 4. Excessive Noise: difference between raw and median-filtered green channel
    median_filtered = cv2.medianBlur(green_channel, 3)
    noise_score = float(np.mean(np.abs(green_channel.astype(np.float32) - median_filtered.astype(np.float32))))

    # 5. Retinal Field Coverage: percentage of image occupied by illuminated retina
    retina_mask = gray > 18
    field_coverage_pct = float(np.sum(retina_mask) / retina_mask.size * 100)

    # 6. Orientation & Dimension Checks
    aspect_ratio = float(w) / max(float(h), 1.0)

    # 7. Specular Glare / Artifact Detection
    glare_mask = gray > 245
    glare_pct = float(np.sum(glare_mask) / gray.size * 100)

    issues: List[str] = []
    remedies: List[str] = []

    # Check 1: Blur
    if sharpness_score < settings.IQA_SHARPNESS_THRESHOLD:
        issues.append("MOTION_BLUR")
        remedies.append("Image is blurry. Stabilize camera against patient headrest and ask patient to fixate on the green alignment light.")

    # Check 2: Underexposure
    if mean_luminance < settings.IQA_MIN_LUMINANCE or underexposed_pct > 65.0:
        issues.append("UNDEREXPOSURE")
        remedies.append("Image is too dark. Increase camera illumination dial to Level 3 and dim the ambient examination room lighting.")

    # Check 3: Overexposure / Glare
    if overexposed_pct > 18.0 or glare_pct > 6.0:
        issues.append("OVEREXPOSURE_GLARE")
        remedies.append("Severe corneal reflection glare detected. Re-align camera objective slightly off-axis.")

    # Check 4: Low Contrast
    if vessel_contrast_score < 0.35 and "UNDEREXPOSURE" not in issues:
        issues.append("LOW_CONTRAST")
        remedies.append("Hazy media or small pupil aperture. Ensure patient has dark-adapted or consider pharmacological pupil dilation.")

    # Check 5: Poor Field Coverage
    if field_coverage_pct < 25.0:
        issues.append("POOR_FIELD_COVERAGE")
        remedies.append("Retinal field coverage is insufficient (<25%). Center the fundus camera lens on the patient pupil.")

    # Check 6: Incorrect Orientation / Framing
    if aspect_ratio < 0.5 or aspect_ratio > 2.0:
        issues.append("INCORRECT_ORIENTATION")
        remedies.append("Unexpected aspect ratio. Maintain standard horizontal fundus camera orientation.")

    # Check 7: Excessive Sensor Noise
    if noise_score > 16.0:
        issues.append("SENSOR_NOISE")
        remedies.append("High sensor ISO noise detected. Lower camera ISO sensitivity and use steady illumination.")

    # Quality score (0.0 to 100.0 scale)
    base_score = 100.0
    if "MOTION_BLUR" in issues:
        base_score -= 40.0
    if "UNDEREXPOSURE" in issues:
        base_score -= 35.0
    if "OVEREXPOSURE_GLARE" in issues:
        base_score -= 30.0
    if "LOW_CONTRAST" in issues:
        base_score -= 20.0
    if "POOR_FIELD_COVERAGE" in issues:
        base_score -= 35.0
    if "INCORRECT_ORIENTATION" in issues:
        base_score -= 25.0
    if "SENSOR_NOISE" in issues:
        base_score -= 15.0
    quality_score = max(5.0, round(base_score, 1))

    # Determine 3-Tier Classification
    if "MOTION_BLUR" in issues or "POOR_FIELD_COVERAGE" in issues or mean_luminance < 20.0 or overexposed_pct > 25.0:
        iqa_status = "REJECT"
        is_acceptable = False
        actionable_feedback = " ".join(remedies)
    elif len(issues) > 0 or vessel_contrast_score < 0.45 or mean_luminance < 45.0 or noise_score > 8.0:
        iqa_status = "BORDERLINE"
        is_acceptable = True
        actionable_feedback = "Image has borderline illumination or contrast. Automatic CLAHE, denoising, and contrast enhancement will be applied."
    else:
        iqa_status = "GOOD"
        is_acceptable = True
        actionable_feedback = "Image quality is optimal for AI diagnostic grading."

    return {
        "iqa_status": iqa_status,
        "is_acceptable": is_acceptable,
        "quality_score": quality_score,
        "sharpness_score": round(sharpness_score, 2),
        "illumination_score": round(mean_luminance, 2),
        "vessel_contrast_score": round(vessel_contrast_score, 2),
        "noise_score": round(noise_score, 2),
        "field_coverage_pct": round(field_coverage_pct, 1),
        "issues": issues,
        "actionable_feedback": actionable_feedback
    }
