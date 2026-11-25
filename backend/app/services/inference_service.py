import json
import time
from typing import Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.screening import Screening
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.explainability_map import ExplainabilityMap
from backend.app.models.referral import Referral
from backend.app.services.storage.factory import get_storage_provider
from backend.app.utils.image_utils import bytes_to_numpy
from backend.app.ml.classifier import predict_diabetic_retinopathy
from backend.app.ml.uncertainty import calculate_predictive_uncertainty
from backend.app.ml.dme_detector import assess_dme_risk
from backend.app.ml.lesions import extract_candidate_lesions
from backend.app.ml.visualizer import render_heatmap_and_overlay
from backend.app.services.rationale_service import generate_clinical_rationale
from backend.app.schemas.ml_result import (
    MLAnalysisResponse,
    DMERisk,
    LesionEvidence,
    ExplainabilityDetail
)


GRADE_NAMES = {
    0: "No Apparent Diabetic Retinopathy (Normal)",
    1: "Mild Non-Proliferative Diabetic Retinopathy (NPDR)",
    2: "Moderate Non-Proliferative Diabetic Retinopathy (NPDR)",
    3: "Severe Non-Proliferative Diabetic Retinopathy (NPDR)",
    4: "Proliferative Diabetic Retinopathy (PDR)",
}


def run_screening_analysis_pipeline(
    screening_id: str,
    db: Session,
    current_user: Any = None
) -> MLAnalysisResponse:
    """
    Executes end-to-end ML classification, uncertainty quantification,
    Grad-CAM++ explainability, candidate lesion extraction, and referral dispatch.
    """
    start_time = time.time()
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening encounter not found.")

    if not screening.fundus_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fundus image uploaded for this screening encounter."
        )

    if screening.fundus_image.iqa_status == "REJECT":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot analyze image rejected by quality gate. Recapture required."
        )

    storage = get_storage_provider()

    # Prefer enhanced image if image was borderline, otherwise use original
    active_img_path = (
        screening.fundus_image.enhanced_file_path
        if screening.fundus_image.enhanced_file_path
        else screening.fundus_image.original_file_path
    )

    image_bytes = storage.get_file(active_img_path)
    img_rgb = bytes_to_numpy(image_bytes)

    # 1. Deep Learning Classifier (with calibrated mock fallback)
    identifier = screening.fundus_image.original_file_path
    grade, confidence, probs_dict, heatmap_2d, engine_name = predict_diabetic_retinopathy(
        img_rgb, image_identifier=identifier
    )

    # 2. Predictive Uncertainty Calculation
    uncertainty_res = calculate_predictive_uncertainty(probs_dict)
    is_uncertain = uncertainty_res["is_uncertain"]

    # 3. Macular Edema (DME) Risk Assessment
    dme_res = assess_dme_risk(img_rgb, predicted_grade=grade)

    # 4. Candidate Lesion Extraction & Quadrant Localization
    lesion_res = extract_candidate_lesions(img_rgb, predicted_grade=grade, heatmap_2d=heatmap_2d)

    # 5. Clinical Rationale Generation
    explanation, recommendation = generate_clinical_rationale(
        grade=grade,
        lesion_evidence=lesion_res,
        dme_risk=dme_res,
        is_uncertain=is_uncertain
    )

    # 6. Render Grad-CAM++ Colormap & Blended Overlay
    heatmap_bytes, overlay_bytes = render_heatmap_and_overlay(
        img_rgb=img_rgb,
        heatmap_2d=heatmap_2d,
        alpha=0.42,
        bounding_boxes=lesion_res["bounding_boxes"]
    )

    heatmap_rel_path = f"heatmaps/{screening.id}_gradcam.jpg"
    overlay_rel_path = f"overlays/{screening.id}_overlay.jpg"
    stored_heatmap_path = storage.save_file(heatmap_bytes, heatmap_rel_path, content_type="image/jpeg")
    stored_overlay_path = storage.save_file(overlay_bytes, overlay_rel_path, content_type="image/jpeg")

    # 7. Strict Clinical Referral Rules & Triage Determination:
    # Rule 1: Grade 0 and Grade 1 are strictly NON_REFERABLE
    # Rule 2: Grade 2, Grade 3, and Grade 4 are strictly REFERABLE
    # Rule 3: Any confidence below 0.65 or high entropy is designated UNCERTAIN
    # Rule 4: UNCERTAIN cases route for ophthalmologist review regardless of DR grade
    # (DME risk removed from current referral logic; documented as future clinical work)
    is_referable = grade in [2, 3, 4]

    if is_uncertain:
        triage_urgency = "UNCERTAIN_REVIEW"
    elif grade == 4:
        triage_urgency = "EMERGENCY"
    elif grade == 3:
        triage_urgency = "URGENT"
    elif grade == 2:
        triage_urgency = "ROUTINE"
    elif grade == 1:
        triage_urgency = "MONITOR"
    else:
        triage_urgency = "HEALTHY"

    # Explicit guarantee: Grade 0 and Grade 1 can NEVER be marked REFERABLE unless explicitly UNCERTAIN
    if grade in [0, 1] and not is_uncertain:
        is_referable = False

    latency_ms = int((time.time() - start_time) * 1000)

    # 8. Upsert AIAnalysis Entity
    existing_ana = db.query(AIAnalysis).filter(AIAnalysis.screening_id == screening.id).first()
    if existing_ana:
        existing_ana.predicted_grade = grade
        existing_ana.confidence_score = confidence
        existing_ana.probabilities_json = json.dumps(probs_dict)
        existing_ana.is_referable = is_referable
        existing_ana.is_uncertain = is_uncertain
        existing_ana.uncertainty_score = uncertainty_res["uncertainty_score"]
        existing_ana.triage_urgency = triage_urgency
        existing_ana.dme_risk_level = dme_res["level"]
        existing_ana.lesion_evidence_json = json.dumps(lesion_res)
        existing_ana.clinical_explanation = explanation
        existing_ana.inference_engine = engine_name
        existing_ana.inference_latency_ms = latency_ms
        ai_ana = existing_ana
    else:
        ai_ana = AIAnalysis(
            screening_id=screening.id,
            model_version="RetinaSahayak-EfficientNet-v2.1",
            inference_engine=engine_name,
            predicted_grade=grade,
            confidence_score=confidence,
            probabilities_json=json.dumps(probs_dict),
            is_referable=is_referable,
            is_uncertain=is_uncertain,
            uncertainty_score=uncertainty_res["uncertainty_score"],
            triage_urgency=triage_urgency,
            dme_risk_level=dme_res["level"],
            lesion_evidence_json=json.dumps(lesion_res),
            clinical_explanation=explanation,
            inference_latency_ms=latency_ms
        )
        db.add(ai_ana)

    db.flush()

    # 9. Upsert ExplainabilityMap Entity
    existing_xai = db.query(ExplainabilityMap).filter(ExplainabilityMap.ai_analysis_id == ai_ana.id).first()
    if existing_xai:
        existing_xai.heatmap_file_path = stored_heatmap_path
        existing_xai.overlay_file_path = stored_overlay_path
        existing_xai.candidate_lesions_json = json.dumps(lesion_res["bounding_boxes"])
        xai_map = existing_xai
    else:
        xai_map = ExplainabilityMap(
            ai_analysis_id=ai_ana.id,
            heatmap_file_path=stored_heatmap_path,
            overlay_file_path=stored_overlay_path,
            method="Grad-CAM++",
            target_layer="model.features.7",
            candidate_lesions_json=json.dumps(lesion_res["bounding_boxes"])
        )
        db.add(xai_map)

    # 10. Automated Referral Dispatch for Referable or Uncertain Cases
    referral_id = None
    referral_status = None

    if is_referable or is_uncertain:
        # Phase 4 Referral Priority Rules:
        # Grade 4 -> CRITICAL
        # Grade 3 -> HIGH
        # Grade 2 -> MEDIUM
        # Any uncertain case -> REVIEW_REQUIRED
        if is_uncertain:
            ref_priority = "REVIEW_REQUIRED"
            ref_reason = "Model confidence below safety threshold (or high entropy); mandatory review."
        elif grade == 4:
            ref_priority = "CRITICAL"
            ref_reason = "Proliferative Diabetic Retinopathy identified. Urgent ophthalmologist review is required."
        elif grade == 3:
            ref_priority = "HIGH"
            ref_reason = "Severe Non-Proliferative Diabetic Retinopathy identified. Urgent ophthalmologist review recommended."
        elif grade == 2:
            ref_priority = "MEDIUM"
            ref_reason = "Moderate Non-Proliferative Diabetic Retinopathy identified. Referable for ophthalmologist review."
        else:
            ref_priority = "MEDIUM"
            ref_reason = "Automated screening referral."

        patient_code = screening.patient.patient_code if screening.patient else "UNKNOWN"
        phc_name = screening.health_center.name if screening.health_center else "Primary Health Centre"

        existing_ref = db.query(Referral).filter(Referral.screening_id == screening.id).first()
        if existing_ref:
            existing_ref.priority = ref_priority
            existing_ref.clinical_priority = ref_priority
            existing_ref.status = "PENDING"
            existing_ref.patient_anonymized_id = patient_code
            existing_ref.phc_location = phc_name
            existing_ref.health_worker_id = screening.worker_id
            existing_ref.predicted_grade = grade
            existing_ref.confidence = confidence
            existing_ref.uncertainty_status = "UNCERTAIN" if is_uncertain else "CERTAIN"
            existing_ref.referable_status = "REFERABLE" if is_referable else "NON_REFERABLE"
            existing_ref.referral_reason = ref_reason
            referral = existing_ref
        else:
            referral = Referral(
                screening_id=screening.id,
                patient_anonymized_id=patient_code,
                phc_location=phc_name,
                health_worker_id=screening.worker_id,
                predicted_grade=grade,
                confidence=confidence,
                uncertainty_status="UNCERTAIN" if is_uncertain else "CERTAIN",
                referable_status="REFERABLE" if is_referable else "NON_REFERABLE",
                priority=ref_priority,
                clinical_priority=ref_priority,
                referral_reason=ref_reason,
                status="PENDING",
                target_hospital_name="District Tertiary Eye Hospital"
            )
            db.add(referral)
        db.flush()
        referral_id = referral.id
        referral_status = referral.status
        screening.status = "REFERRAL_DISPATCHED"

        # Log referral creation in audit trail
        from backend.app.services.audit_service import create_audit_log
        create_audit_log(
            db=db,
            action="REFERRAL_CREATED",
            resource_type="Referral",
            resource_id=referral.id,
            user_id=screening.worker_id,
            user_role="PHC_WORKER",
            status="SUCCESS",
            payload_data={
                "screening_id": screening.id,
                "priority": ref_priority,
                "predicted_grade": grade,
                "confidence": confidence,
                "is_uncertain": is_uncertain
            }
        )
    else:
        screening.status = "AI_ANALYZED"

    db.commit()
    db.refresh(screening)
    db.refresh(ai_ana)

    user_id = current_user.id if current_user else screening.worker_id
    user_role = current_user.role if current_user else "PHC_WORKER"

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="RUN_AI_DIAGNOSIS",
        resource_type="AIAnalysis",
        resource_id=ai_ana.id,
        user_id=user_id,
        user_role=user_role,
        status="SUCCESS",
        payload_data={
            "screening_id": screening.id,
            "patient_id": screening.patient_id,
            "image_id": screening.fundus_image.id if screening.fundus_image else None,
            "predicted_grade": grade,
            "confidence": confidence,
            "is_referable": is_referable,
            "is_uncertain": is_uncertain
        }
    )
    db.commit()

    # Construct Response DTO
    grade_label = f"Grade {grade}: {GRADE_NAMES[grade]}"
    referable_status = "REFERABLE" if is_referable else "NON_REFERABLE"
    uncertainty_status = "UNCERTAIN" if is_uncertain else "CERTAIN"
    inference_time_sec = round(latency_ms / 1000.0, 3)

    # Differentiate explainability transparency based on inference engine
    if "MOCK" in engine_name.upper():
        explanation_label = "Simulated explanation generated by mock inference."
        explanation_disclaimer = "Simulated visual explanation generated by deterministic mock inference. Does not reflect trained model activations."
    else:
        explanation_label = "AI-generated visual explanation; requires ophthalmologist verification."
        explanation_disclaimer = "Grad-CAM++ activation map generated from trained EfficientNet convolutional feature maps. Requires ophthalmologist clinical verification."

    return MLAnalysisResponse(
        screening_id=screening.id,
        model_version=ai_ana.model_version,
        inference_engine=ai_ana.inference_engine,
        inference_time=inference_time_sec,
        quality_status=screening.fundus_image.iqa_status,
        quality_score=getattr(screening.fundus_image, "quality_score", 85.0) or 85.0,
        quality_issues=[screening.fundus_image.actionable_feedback] if screening.fundus_image.iqa_status != "GOOD" and screening.fundus_image.actionable_feedback else [],
        recapture_guidance=screening.fundus_image.actionable_feedback if screening.fundus_image.iqa_status != "GOOD" else None,
        enhanced_image_url=storage.get_url(screening.fundus_image.enhanced_file_path) if screening.fundus_image.enhanced_file_path else None,
        predicted_grade=grade,
        grade_label=grade_label,
        grade_name=GRADE_NAMES[grade],
        class_probabilities=probs_dict,
        confidence=round(confidence, 3),
        confidence_score=round(confidence, 3),
        uncertainty_status=uncertainty_status,
        uncertainty_score=ai_ana.uncertainty_score,
        referable_status=referable_status,
        is_referable=is_referable,
        is_uncertain=is_uncertain,
        triage_urgency=triage_urgency,
        dme_risk=DMERisk(
            level=dme_res["level"],
            exudates_near_macula=dme_res["exudates_near_macula"]
        ),
        lesion_evidence=LesionEvidence(
            microaneurysms_detected=lesion_res["microaneurysms_detected"],
            blot_hemorrhages_detected=lesion_res["blot_hemorrhages_detected"],
            hard_exudates_detected=lesion_res["hard_exudates_detected"],
            neovascularization_detected=lesion_res["neovascularization_detected"],
            suspicious_quadrants=lesion_res["suspicious_quadrants"]
        ),
        clinical_explanation=explanation,
        recommended_action=recommendation,
        explainability=ExplainabilityDetail(
            heatmap_url=storage.get_url(stored_heatmap_path),
            overlay_url=storage.get_url(stored_overlay_path),
            method="Grad-CAM++",
            target_layer="model.features.7",
            candidate_lesions=lesion_res["bounding_boxes"],
            explanation_label=explanation_label,
            explanation_disclaimer=explanation_disclaimer
        ),
        referral_id=referral_id,
        referral_status=referral_status,
        disclaimer=(
            "Presumptive AI Screening Observation. Not an autonomous medical diagnosis. "
            "Must be reviewed and verified by a licensed ophthalmologist before any clinical treatment."
        )
    )
