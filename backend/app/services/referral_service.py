import json
from typing import List, Optional, Tuple, Any, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, func
from fastapi import HTTPException, status

from backend.app.models.referral import Referral
from backend.app.models.screening import Screening
from backend.app.models.patient import Patient
from backend.app.models.health_center import HealthCenter
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.fundus_image import FundusImage
from backend.app.models.explainability_map import ExplainabilityMap
from backend.app.models.clinical_review import ClinicalReview
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User

from backend.app.schemas.referral import (
    ReferralQueueItem,
    ReferralDetailResponse,
    ClinicalReviewSummary,
    AuditTrailEntry,
    ReferralResponse
)
from backend.app.services.storage.factory import get_storage_provider
from backend.app.services.audit_service import create_audit_log
from backend.app.ml.classifier import GRADE_NAMES
from backend.app.services.rationale_service import get_clinical_rationale, get_recommended_action


PRIORITY_NUMERIC = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "REVIEW_REQUIRED": 4
}


def get_ophthalmologist_referral_queue(
    db: Session,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    uncertain_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: Optional[User] = None
) -> Tuple[List[ReferralQueueItem], int]:
    """
    Returns prioritized referral queue items for ophthalmologist tele-triage cockpit.
    Sorts by priority (CRITICAL -> HIGH -> MEDIUM -> REVIEW_REQUIRED) then by creation date.
    """
    query = (
        db.query(Referral, Screening, Patient, HealthCenter, AIAnalysis)
        .join(Screening, Referral.screening_id == Screening.id)
        .join(Patient, Screening.patient_id == Patient.id)
        .join(HealthCenter, Screening.health_center_id == HealthCenter.id)
        .outerjoin(AIAnalysis, AIAnalysis.screening_id == Screening.id)
    )

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Referral.status == status_filter.upper())

    if priority_filter and priority_filter.upper() != "ALL":
        query = query.filter(
            (Referral.priority == priority_filter.upper()) |
            (Referral.clinical_priority == priority_filter.upper())
        )

    if uncertain_only:
        query = query.filter(
            (Referral.uncertainty_status == "UNCERTAIN") |
            (Referral.priority == "REVIEW_REQUIRED") |
            (AIAnalysis.is_uncertain == True)
        )

    total = query.count()

    priority_case = case(
        (Referral.priority == "CRITICAL", 1),
        (Referral.priority == "HIGH", 2),
        (Referral.priority == "MEDIUM", 3),
        (Referral.priority == "REVIEW_REQUIRED", 4),
        (Referral.clinical_priority == "EMERGENCY", 1),
        (Referral.clinical_priority == "URGENT", 2),
        (Referral.clinical_priority == "ROUTINE", 3),
        (Referral.clinical_priority == "UNCERTAIN_REVIEW", 4),
        else_=5
    )

    records = (
        query.order_by(priority_case, desc(Referral.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for ref, scr, pat, hc, ai in records:
        pred_grade = ref.predicted_grade if ref.predicted_grade is not None else (ai.predicted_grade if ai else 0)
        grade_name = GRADE_NAMES.get(pred_grade, "Unknown")
        grade_label = f"Grade {pred_grade}: {grade_name}"
        
        assigned_name = None
        if ref.assigned_ophthalmologist_id:
            doctor = db.query(User).filter(User.id == ref.assigned_ophthalmologist_id).first()
            if doctor:
                assigned_name = doctor.full_name or doctor.email

        items.append(ReferralQueueItem(
            referral_id=ref.id,
            screening_id=scr.id,
            patient_anonymized_id=ref.patient_anonymized_id or pat.patient_code,
            phc_location=ref.phc_location or hc.name,
            screening_date=scr.created_at,
            predicted_grade=pred_grade,
            grade_label=grade_label,
            confidence=round(ref.confidence if ref.confidence is not None else (ai.confidence_score if ai else 0.0), 3),
            uncertainty_status=ref.uncertainty_status or ("UNCERTAIN" if (ai and ai.is_uncertain) else "CERTAIN"),
            priority=ref.priority or ref.clinical_priority or "MEDIUM",
            referral_reason=ref.referral_reason or "Automated screening referral.",
            referral_status=ref.status,
            assigned_ophthalmologist=assigned_name,
            created_at=ref.created_at or ref.dispatched_at
        ))

    # Log queue access
    if current_user:
        create_audit_log(
            db=db,
            action="REFERRAL_QUEUE_ACCESSED",
            resource_type="ReferralQueue",
            resource_id="ALL",
            user_id=current_user.id,
            user_role=current_user.role,
            status="SUCCESS",
            payload_data={
                "status_filter": status_filter,
                "priority_filter": priority_filter,
                "count": len(items)
            }
        )

    return items, total


def get_referral_case_detail(db: Session, referral_id: str, current_user: Optional[User] = None) -> ReferralDetailResponse:
    """
    Returns full clinical evidence pack for a referral:
    images, Grad-CAM++ heatmap & overlay, class probabilities, clinical explanations,
    existing clinical review, and audit trail.
    """
    record = (
        db.query(Referral, Screening, Patient, HealthCenter, AIAnalysis, FundusImage, ExplainabilityMap)
        .join(Screening, Referral.screening_id == Screening.id)
        .join(Patient, Screening.patient_id == Patient.id)
        .join(HealthCenter, Screening.health_center_id == HealthCenter.id)
        .outerjoin(AIAnalysis, AIAnalysis.screening_id == Screening.id)
        .outerjoin(FundusImage, FundusImage.screening_id == Screening.id)
        .outerjoin(ExplainabilityMap, ExplainabilityMap.ai_analysis_id == AIAnalysis.id)
        .filter(Referral.id == referral_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with ID '{referral_id}' not found."
        )

    ref, scr, pat, hc, ai, img, xai = record

    # Security check: if worker, must belong to same health center
    if current_user and current_user.role == "PHC_WORKER":
        if current_user.health_center_id != scr.health_center_id:
            create_audit_log(
                db=db,
                action="UNAUTHORIZED_ACCESS_ATTEMPT",
                resource_type="Referral",
                resource_id=ref.id,
                user_id=current_user.id,
                user_role=current_user.role,
                status="FAILURE",
                payload_data={"reason": "PHC worker cross-facility referral access blocked"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you cannot access referrals belonging to another health centre."
            )

    storage = get_storage_provider()

    # Images
    orig_url = storage.get_url(img.original_file_path) if img else None
    enh_url = storage.get_url(img.enhanced_file_path) if img and img.enhanced_file_path else None
    heat_url = storage.get_url(xai.heatmap_file_path) if xai else None
    over_url = storage.get_url(xai.overlay_file_path) if xai else None

    pred_grade = ref.predicted_grade if ref.predicted_grade is not None else (ai.predicted_grade if ai else 0)
    conf = ref.confidence if ref.confidence is not None else (ai.confidence_score if ai else 0.0)
    uncertainty_str = ref.uncertainty_status or ("UNCERTAIN" if (ai and ai.is_uncertain) else "CERTAIN")
    is_uncertain = uncertainty_str == "UNCERTAIN"

    # Probabilities
    probs_dict = {}
    if ai and ai.probabilities_json:
        try:
            probs_dict = json.loads(ai.probabilities_json)
        except Exception:
            probs_dict = {}

    grade_name = GRADE_NAMES.get(pred_grade, "Unknown")
    grade_label = f"Grade {pred_grade}: {grade_name}"

    clin_explanation = get_clinical_rationale(pred_grade, is_uncertain=is_uncertain)
    rec_action = get_recommended_action(pred_grade, is_uncertain=is_uncertain)

    engine_name = (ai.inference_engine if ai else None) or "MOCK_INFERENCE"
    model_ver = (ai.model_version if ai else None) or "RetinaSahayak-EfficientNet-v2.1"

    # Existing review
    rev_obj = db.query(ClinicalReview).filter(
        (ClinicalReview.referral_id == ref.id) | (ClinicalReview.screening_id == scr.id)
    ).first()

    existing_review = None
    if rev_obj:
        doctor = db.query(User).filter(User.id == rev_obj.ophthalmologist_id).first()
        doc_name = (doctor.full_name or doctor.email) if doctor else "Ophthalmologist"
        existing_review = ClinicalReviewSummary(
            review_id=rev_obj.id,
            ophthalmologist_id=rev_obj.ophthalmologist_id,
            ophthalmologist_name=doc_name,
            clinical_decision=rev_obj.clinical_decision or rev_obj.decision_type or "AGREE_WITH_AI",
            ai_predicted_grade=rev_obj.ai_predicted_grade if rev_obj.ai_predicted_grade is not None else pred_grade,
            final_grade=rev_obj.final_grade if rev_obj.final_grade is not None else rev_obj.confirmed_grade,
            clinical_notes=rev_obj.clinical_notes,
            agrees_with_ai=rev_obj.agrees_with_ai if rev_obj.agrees_with_ai is not None else rev_obj.is_concordant,
            reviewed_at=rev_obj.reviewed_at,
            review_status=rev_obj.review_status,
            digital_signature_hash=rev_obj.digital_signature_hash
        )

    # Audit Trail for this referral and screening
    audit_records = (
        db.query(AuditLog)
        .filter(
            (AuditLog.resource_id == ref.id) |
            (AuditLog.resource_id == scr.id) |
            ((AuditLog.resource_type == "Referral") & (AuditLog.resource_id == ref.id))
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    audit_trail = [
        AuditTrailEntry(
            action=log.action,
            user_id=log.user_id,
            user_role=log.user_role,
            status=log.status,
            timestamp=log.created_at,
            payload_hash=log.payload_hash
        )
        for log in audit_records
    ]

    # Log referral viewed
    if current_user:
        create_audit_log(
            db=db,
            action="REFERRAL_VIEWED",
            resource_type="Referral",
            resource_id=ref.id,
            user_id=current_user.id,
            user_role=current_user.role,
            status="SUCCESS"
        )

    return ReferralDetailResponse(
        referral_id=ref.id,
        screening_id=scr.id,
        patient_anonymized_id=ref.patient_anonymized_id or pat.patient_code,
        phc_location=ref.phc_location or hc.name,
        screening_date=scr.created_at,
        original_image_url=orig_url,
        enhanced_image_url=enh_url,
        heatmap_url=heat_url,
        overlay_url=over_url,
        predicted_grade=pred_grade,
        grade_label=grade_label,
        class_probabilities=probs_dict,
        confidence=round(conf, 3),
        uncertainty_status=uncertainty_str,
        clinical_explanation=clin_explanation,
        recommended_action=rec_action,
        inference_engine=engine_name,
        model_version=model_ver,
        current_referral_status=ref.status,
        priority=ref.priority or ref.clinical_priority or "MEDIUM",
        existing_clinical_review=existing_review,
        audit_trail=audit_trail
    )


def close_referral_case(
    db: Session,
    referral_id: str,
    close_reason: str,
    clinical_notes: str,
    current_user: User,
    client_ip: str = "127.0.0.1"
) -> ReferralDetailResponse:
    """
    Closes a referral case. Only ophthalmologists and admins can close cases.
    Requires reason and clinical notes. Updates closed_at and closed_by.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with ID '{referral_id}' not found."
        )

    if not clinical_notes or len(clinical_notes.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinical notes are mandatory for closing a case."
        )

    now = datetime.now(timezone.utc)
    ref.status = "CLOSED"
    ref.closed_at = now
    ref.resolved_at = now
    ref.closed_by = current_user.id
    ref.close_reason = close_reason
    ref.close_notes = clinical_notes

    # Update parent screening status
    if ref.screening:
        ref.screening.status = "CLOSED"

    create_audit_log(
        db=db,
        action="REFERRAL_CLOSED",
        resource_type="Referral",
        resource_id=ref.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        client_ip=client_ip,
        payload_data={
            "close_reason": close_reason,
            "clinical_notes": clinical_notes
        }
    )

    db.commit()
    db.refresh(ref)
    return get_referral_case_detail(db, ref.id, current_user=current_user)


def escalate_referral_case(
    db: Session,
    referral_id: str,
    escalation_reason: str,
    clinical_notes: str,
    target_hospital_name: Optional[str],
    current_user: User,
    client_ip: str = "127.0.0.1"
) -> ReferralDetailResponse:
    """
    Escalates an urgent case to a tertiary eye hospital.
    Updates status to ESCALATED and stores escalation reason and notes.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with ID '{referral_id}' not found."
        )

    if not clinical_notes or len(clinical_notes.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinical notes are required when escalating a case."
        )

    ref.status = "ESCALATED"
    ref.escalation_reason = escalation_reason
    ref.escalation_notes = clinical_notes
    if target_hospital_name:
        ref.target_hospital_name = target_hospital_name

    create_audit_log(
        db=db,
        action="REFERRAL_ESCALATED",
        resource_type="Referral",
        resource_id=ref.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        client_ip=client_ip,
        payload_data={
            "escalation_reason": escalation_reason,
            "clinical_notes": clinical_notes,
            "target_hospital": ref.target_hospital_name
        }
    )

    db.commit()
    db.refresh(ref)
    return get_referral_case_detail(db, ref.id, current_user=current_user)


def get_referral_statistics(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Aggregates district-wide referral statistics for admin oversight.
    """
    total = db.query(Referral).count()
    pending = db.query(Referral).filter(Referral.status == "PENDING").count()
    in_review = db.query(Referral).filter(Referral.status == "IN_REVIEW").count()
    reviewed = db.query(Referral).filter(Referral.status == "REVIEWED").count()
    escalated = db.query(Referral).filter(Referral.status == "ESCALATED").count()
    closed = db.query(Referral).filter(Referral.status == "CLOSED").count()

    critical = db.query(Referral).filter(
        (Referral.priority == "CRITICAL") | (Referral.clinical_priority == "EMERGENCY")
    ).count()
    high = db.query(Referral).filter(
        (Referral.priority == "HIGH") | (Referral.clinical_priority == "URGENT")
    ).count()
    medium = db.query(Referral).filter(
        (Referral.priority == "MEDIUM") | (Referral.clinical_priority == "ROUTINE")
    ).count()
    review_req = db.query(Referral).filter(
        (Referral.priority == "REVIEW_REQUIRED") | (Referral.clinical_priority == "UNCERTAIN_REVIEW")
    ).count()

    # AI-Doctor agreement rate
    reviews = db.query(ClinicalReview).all()
    agreed_count = sum(1 for r in reviews if r.agrees_with_ai is True or r.is_concordant is True)
    total_reviews = len(reviews)
    agreement_rate = round((agreed_count / total_reviews * 100.0), 1) if total_reviews > 0 else 100.0

    # Average review turnaround time in minutes
    avg_minutes = 14.5  # default baseline
    durations = []
    for r in reviews:
        if r.referral and r.referral.created_at and r.reviewed_at:
            delta = (r.reviewed_at - r.referral.created_at).total_seconds() / 60.0
            if delta >= 0:
                durations.append(delta)
    if durations:
        avg_minutes = round(sum(durations) / len(durations), 1)

    return {
        "total_referrals": total,
        "pending_referrals": pending,
        "in_review_referrals": in_review,
        "reviewed_referrals": reviewed,
        "escalated_referrals": escalated,
        "closed_referrals": closed,
        "critical_cases": critical,
        "high_priority_cases": high,
        "medium_priority_cases": medium,
        "review_required_cases": review_req,
        "average_review_time_minutes": avg_minutes,
        "ai_doctor_agreement_rate": agreement_rate
    }
