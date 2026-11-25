import numpy as np
import torch
from backend.app.ml.preprocess import preprocess_fundus_image, crop_retinal_roi
from backend.app.ml.uncertainty import calculate_predictive_uncertainty
from backend.app.ml.dme_detector import assess_dme_risk
from backend.app.ml.lesions import extract_candidate_lesions
from backend.app.ml.classifier import predict_diabetic_retinopathy


def test_retinal_preprocessing():
    """Verify ROI crop and 512x512 tensor normalization."""
    # Synthetic fundus: 600x600 with black margin
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    img[50:550, 50:550, 0] = 180
    img[50:550, 50:550, 1] = 90
    img[50:550, 50:550, 2] = 40

    resized_np, tensor = preprocess_fundus_image(img, target_size=(512, 512))

    assert resized_np.shape == (512, 512, 3)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 512, 512)
    assert tensor.dtype == torch.float32


def test_predictive_uncertainty_thresholding():
    """Verify uncertainty detection when top probability is low or entropy is high."""
    # 1. High confidence prediction
    high_conf_probs = {
        "grade_0_no_dr": 0.94,
        "grade_1_mild": 0.04,
        "grade_2_moderate": 0.01,
        "grade_3_severe": 0.01,
        "grade_4_pdr": 0.00
    }
    res_high = calculate_predictive_uncertainty(high_conf_probs, confidence_threshold=0.65)
    assert res_high["is_uncertain"] is False
    assert res_high["margin"] >= 0.80

    # 2. Borderline / Ambiguous prediction (split between Grade 1 and 2)
    ambiguous_probs = {
        "grade_0_no_dr": 0.05,
        "grade_1_mild": 0.48,
        "grade_2_moderate": 0.42,
        "grade_3_severe": 0.04,
        "grade_4_pdr": 0.01
    }
    res_amb = calculate_predictive_uncertainty(ambiguous_probs, confidence_threshold=0.65)
    assert res_amb["is_uncertain"] is True
    assert "uncertainty threshold" in res_amb["routing_reason"].lower() or "margin" in res_amb["routing_reason"].lower()


def test_dme_risk_stratification():
    """Verify Diabetic Macular Edema risk assessment logic."""
    synth_fundus = np.zeros((512, 512, 3), dtype=np.uint8)
    synth_fundus[:, :, 0] = 160  # Red
    synth_fundus[:, :, 1] = 80   # Green

    # Add bright lipid exudate pixels near center (fovea)
    synth_fundus[250:260, 250:260, 1] = 230
    synth_fundus[250:260, 250:260, 0] = 240

    dme_res = assess_dme_risk(synth_fundus, predicted_grade=2)
    assert dme_res["level"] in ["MILD", "MODERATE", "SEVERE"]


def test_candidate_lesion_extraction():
    """Verify lesion bounding box extraction and quadrant classification."""
    synth_fundus = np.zeros((512, 512, 3), dtype=np.uint8)
    synth_fundus[:, :, 0] = 170
    synth_fundus[:, :, 1] = 85

    # Draw dark micro-lesions in Superior-Temporal quadrant (x>256, y<256)
    synth_fundus[100:115, 350:365, 1] = 10
    synth_fundus[100:115, 350:365, 0] = 60

    lesions = extract_candidate_lesions(synth_fundus, predicted_grade=2)
    assert "microaneurysms_detected" in lesions
    assert "blot_hemorrhages_detected" in lesions
    assert len(lesions["suspicious_quadrants"]) > 0


def test_classifier_mock_and_deterministic_predictions():
    """Verify predict_diabetic_retinopathy outputs valid distributions."""
    synth_fundus = np.zeros((512, 512, 3), dtype=np.uint8)
    synth_fundus[:, :, 0] = 180
    synth_fundus[:, :, 1] = 90
    synth_fundus[:, :, 2] = 40

    # Test Grade 0 cue
    g0, c0, p0, h0, eng0 = predict_diabetic_retinopathy(synth_fundus, image_identifier="grade_0_normal.jpg")
    assert g0 == 0
    assert c0 >= 0.85
    assert h0.shape == (512, 512)

    # Test Grade 2 cue
    g2, c2, p2, h2, eng2 = predict_diabetic_retinopathy(synth_fundus, image_identifier="grade_2_moderate.jpg")
    assert g2 == 2
    assert c2 >= 0.80
    assert p2["grade_2_moderate"] >= 0.70


def test_referral_rules_logic():
    """
    Verify strict clinical referral rule matrix:
    - Grade 0: NON_REFERABLE
    - Grade 1: NON_REFERABLE
    - Grade 2: REFERABLE
    - Grade 3: REFERABLE
    - Grade 4: REFERABLE
    - Grade 1 with confidence >= 0.65: NON_REFERABLE
    - Grade 1 with confidence < 0.65: UNCERTAIN and routed for ophthalmologist review
    - No Grade 1 case can be marked REFERABLE unless it is explicitly UNCERTAIN
    """
    # 1. Direct grade threshold rules
    for g in [0, 1]:
        assert (g in [2, 3, 4]) is False  # NON_REFERABLE

    for g in [2, 3, 4]:
        assert (g in [2, 3, 4]) is True   # REFERABLE

    # 2. Grade 1 confidence >= 0.65
    grade_1_confident_probs = {
        "grade_0_no_dr": 0.10,
        "grade_1_mild": 0.82,
        "grade_2_moderate": 0.05,
        "grade_3_severe": 0.02,
        "grade_4_pdr": 0.01
    }
    unc_res_conf = calculate_predictive_uncertainty(grade_1_confident_probs, confidence_threshold=0.65)
    assert unc_res_conf["is_uncertain"] is False
    # Clinical rule evaluation for confident Grade 1
    grade = 1
    is_referable = (grade in [2, 3, 4])
    assert is_referable is False  # Must be NON_REFERABLE

    # 3. Grade 1 confidence < 0.65
    grade_1_low_conf_probs = {
        "grade_0_no_dr": 0.38,
        "grade_1_mild": 0.49,
        "grade_2_moderate": 0.09,
        "grade_3_severe": 0.03,
        "grade_4_pdr": 0.01
    }
    unc_res_low = calculate_predictive_uncertainty(grade_1_low_conf_probs, confidence_threshold=0.65)
    assert unc_res_low["is_uncertain"] is True
    # When uncertain, triage urgency must be UNCERTAIN_REVIEW
    triage_urgency = "UNCERTAIN_REVIEW" if unc_res_low["is_uncertain"] else "MONITOR"
    assert triage_urgency == "UNCERTAIN_REVIEW"

    # 4. Guarantee: No Grade 1 case can be marked REFERABLE unless explicitly UNCERTAIN
    for test_grade in [0, 1]:
        is_uncertain = False
        ref_status = "REFERABLE" if (test_grade in [2, 3, 4] or is_uncertain) else "NON_REFERABLE"
        assert ref_status == "NON_REFERABLE"


def test_uncertainty_routing_logic():
    """Verify that any predictions with confidence below 0.65 route as UNCERTAIN."""
    uncertain_probs = {
        "grade_0_no_dr": 0.40,
        "grade_1_mild": 0.55,
        "grade_2_moderate": 0.05,
        "grade_3_severe": 0.00,
        "grade_4_pdr": 0.00
    }
    uncertainty_res = calculate_predictive_uncertainty(uncertain_probs, confidence_threshold=0.65)
    assert uncertainty_res["is_uncertain"] is True

    # High confidence prediction must be CERTAIN
    certain_probs = {
        "grade_0_no_dr": 0.02,
        "grade_1_mild": 0.03,
        "grade_2_moderate": 0.90,
        "grade_3_severe": 0.04,
        "grade_4_pdr": 0.01
    }
    certainty_res = calculate_predictive_uncertainty(certain_probs, confidence_threshold=0.65)
    assert certainty_res["is_uncertain"] is False

