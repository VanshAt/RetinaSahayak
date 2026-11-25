import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.screening import Screening
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.referral import Referral
from backend.app.models.clinical_review import ClinicalReview
from backend.app.schemas.referral import ClinicalReviewSubmission, ReferralDetailResponse
from backend.app.schemas.clinical_review import ClinicalReviewCreate, ClinicalReviewResponse
from backend.app.services.audit_service import create_audit_log
from backend.app.services.referral_service import get_referral_case_detail
from backend.app.core.logging import logger


VALID_DECISIONS = {
    "AGREE_WITH_AI",
    "MODIFY_GRADE",
    "REQUEST_REPEAT_IMAGING",
    "MARK_NON_REFERABLE",
    "MARK_REFERABLE",
    "MARK_FOLLOW_UP_REQUIRED",
    "CLOSE_CASE"
}

NOTES_REQUIRED_DECISIONS = {
    "MODIFY_GRADE",
    "REQUEST_REPEAT_IMAGING",
    "MARK_NON_REFERABLE",
    "MARK_REFERABLE",
    "MARK_FOLLOW_UP_REQUIRED",
    "CLOSE_CASE"
}


def submit_ophthalmologist_referral_review(
    db: Session,
    referral_id: str,
    submission: ClinicalReviewSubmission,
    doctor_user: Any,
    client_ip: str = "127.0.0.1"
) -> ReferralDetailResponse:
    """
    Submits an official ophthalmologist clinical review for a referral.
    Validates decision options, mandatory notes, and mandatory final_grade for MODIFY_GRADE.
    Updates referral status to REVIEWED or CLOSED.
    Enforces that a referral can be reviewed only once unless reopened by admin.
    Logs CLINICAL_REVIEW_SUBMITTED and CLINICAL_REVIEW_SIGNED in audit log.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with ID '{referral_id}' not found."
        )

    # Check if referral already reviewed
    existing_review = db.query(ClinicalReview).filter(
        (ClinicalReview.referral_id == ref.id) | (ClinicalReview.screening_id == ref.screening_id)
    ).first()

    if existing_review and doctor_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A clinical review has already been submitted and signed for this referral."
        )

    decision = submission.clinical_decision.upper()
    if decision not in VALID_DECISIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid clinical decision: '{submission.clinical_decision}'. Must be one of: {', '.join(sorted(VALID_DECISIONS))}"
        )

    # Validation: Notes required for specified decisions
    notes = (submission.clinical_notes or "").strip()
    if decision in NOTES_REQUIRED_DECISIONS and (not notes or len(notes) < 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clinical notes are mandatory when submitting decision '{decision}'."
        )

    # Validation: MODIFY_GRADE requires final_grade
    if decision == "MODIFY_GRADE":
        if submission.final_grade is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Final grade (0-4) is mandatory when modifying AI grade."
            )

    screening = db.query(Screening).filter(Screening.id == ref.screening_id).first()
    ai_ana = db.query(AIAnalysis).filter(AIAnalysis.screening_id == ref.screening_id).first()
    pred_grade = ai_ana.predicted_grade if ai_ana else (ref.predicted_grade if ref.predicted_grade is not None else 0)
    conf = ai_ana.confidence_score if ai_ana else (ref.confidence if ref.confidence is not None else 0.0)

    # Final grade calculation
    if decision == "AGREE_WITH_AI":
        final_grade = pred_grade
        agrees_with_ai = True
    elif decision == "MODIFY_GRADE":
        final_grade = submission.final_grade
        agrees_with_ai = (final_grade == pred_grade)
    else:
        final_grade = submission.final_grade if submission.final_grade is not None else pred_grade
        agrees_with_ai = (final_grade == pred_grade)

    now = datetime.now(timezone.utc)

    # Digital signature hash for verification
    sig_entropy = (
        f"DOCTOR:{doctor_user.id}|REF:{ref.id}|SCR:{ref.screening_id}|GRADE:{final_grade}|"
        f"DECISION:{decision}|NOTES:{notes}|TIME:{now.isoformat()}"
    )
    sig_hash = hashlib.sha256(sig_entropy.encode("utf-8")).hexdigest()

    # Create or update ClinicalReview
    if existing_review:
        review_obj = existing_review
        review_obj.ophthalmologist_id = doctor_user.id
        review_obj.referral_id = ref.id
        review_obj.ai_predicted_grade = pred_grade
        review_obj.ai_confidence = conf
        review_obj.final_grade = final_grade
        review_obj.clinical_decision = decision
        review_obj.clinical_notes = notes or "Clinical review signed."
        review_obj.agrees_with_ai = agrees_with_ai
        review_obj.reviewed_at = now
        review_obj.review_status = "AMENDED" if doctor_user.role == "ADMIN" else "COMPLETED"
        review_obj.digital_signature_hash = sig_hash
        # Backwards compatibility
        review_obj.decision_type = decision
        review_obj.confirmed_grade = final_grade
        review_obj.is_concordant = agrees_with_ai
    else:
        review_obj = ClinicalReview(
            referral_id=ref.id,
            screening_id=ref.screening_id,
            ophthalmologist_id=doctor_user.id,
            ai_predicted_grade=pred_grade,
            ai_confidence=conf,
            final_grade=final_grade,
            clinical_decision=decision,
            clinical_notes=notes or "Clinical review signed.",
            agrees_with_ai=agrees_with_ai,
            review_status="COMPLETED",
            reviewed_at=now,
            digital_signature_hash=sig_hash,
            # Backwards compatibility
            decision_type=decision,
            confirmed_grade=final_grade,
            is_concordant=agrees_with_ai,
            clinical_status="CASE_CLOSED" if decision == "CLOSE_CASE" else "REFERRED_TERTIARY"
        )
        db.add(review_obj)

    # Status updates for referral and screening
    if decision in ["CLOSE_CASE", "MARK_NON_REFERABLE"]:
        ref.status = "CLOSED"
        ref.closed_at = now
        ref.closed_by = doctor_user.id
        ref.close_reason = "CLINICAL_REVIEW_CLOSE"
        ref.close_notes = notes
        if screening:
            screening.status = "CLOSED"
    else:
        ref.status = "REVIEWED"
        if screening:
            screening.status = "VERIFIED_BY_DOCTOR"

    ref.resolved_at = now
    ref.assigned_ophthalmologist_id = doctor_user.id

    db.flush()

    # Audit Logs
    create_audit_log(
        db=db,
        action="CLINICAL_REVIEW_SUBMITTED",
        resource_type="ClinicalReview",
        resource_id=review_obj.id,
        user_id=doctor_user.id,
        user_role=doctor_user.role,
        status="SUCCESS",
        client_ip=client_ip,
        payload_data={
            "referral_id": ref.id,
            "decision": decision,
            "final_grade": final_grade,
            "agrees_with_ai": agrees_with_ai
        }
    )

    create_audit_log(
        db=db,
        action="CLINICAL_REVIEW_SIGNED",
        resource_type="ClinicalReview",
        resource_id=review_obj.id,
        user_id=doctor_user.id,
        user_role=doctor_user.role,
        status="SUCCESS",
        client_ip=client_ip,
        payload_data={
            "referral_id": ref.id,
            "ophthalmologist_id": doctor_user.id,
            "final_decision": decision,
            "final_grade": final_grade,
            "signature_hash": sig_hash,
            "timestamp": now.isoformat()
        }
    )

    db.commit()
    db.refresh(ref)
    db.refresh(review_obj)

    logger.info(
        f"Clinical review signed for referral {ref.id} by {doctor_user.email}: "
        f"decision={decision}, final_grade={final_grade}, agrees_with_ai={agrees_with_ai}"
    )

    return get_referral_case_detail(db, ref.id, current_user=doctor_user)


# Maintain backwards compatibility for legacy POST /api/v1/reviews endpoint
def submit_clinical_review(
    db: Session,
    review_in: ClinicalReviewCreate,
    doctor_user: Any,
    client_ip: str = "127.0.0.1"
) -> ClinicalReviewResponse:
    screening = db.query(Screening).filter(Screening.id == review_in.screening_id).first()
    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening with ID '{review_in.screening_id}' not found."
        )

    referral = db.query(Referral).filter(Referral.screening_id == screening.id).first()
    ref_id = referral.id if referral else "DIRECT"

    submission = ClinicalReviewSubmission(
        clinical_decision=review_in.decision_type,
        final_grade=review_in.confirmed_grade,
        clinical_notes=review_in.clinical_notes
    )

    if referral:
        submit_ophthalmologist_referral_review(
            db=db,
            referral_id=referral.id,
            submission=submission,
            doctor_user=doctor_user,
            client_ip=client_ip
        )
        rev = db.query(ClinicalReview).filter(ClinicalReview.screening_id == screening.id).first()
        if rev and review_in.confirmed_grade is not None:
            rev.confirmed_grade = review_in.confirmed_grade
            db.commit()
            db.refresh(rev)
    else:
        # Screening without referral
        now = datetime.now(timezone.utc)
        sig_entropy = f"DOCTOR:{doctor_user.id}|SCR:{screening.id}|GRADE:{review_in.confirmed_grade}|{now.isoformat()}"
        sig_hash = hashlib.sha256(sig_entropy.encode("utf-8")).hexdigest()
        rev = ClinicalReview(
            screening_id=screening.id,
            ophthalmologist_id=doctor_user.id,
            clinical_decision=review_in.decision_type,
            final_grade=review_in.confirmed_grade,
            clinical_notes=review_in.clinical_notes,
            agrees_with_ai=True,
            digital_signature_hash=sig_hash,
            decision_type=review_in.decision_type,
            confirmed_grade=review_in.confirmed_grade,
            is_concordant=True,
            clinical_status=review_in.clinical_status
        )
        db.add(rev)
        screening.status = "DOCTOR_VERIFIED"
        db.commit()
        db.refresh(rev)

    return ClinicalReviewResponse(
        id=rev.id,
        screening_id=rev.screening_id,
        ophthalmologist_id=doctor_user.id,
        ophthalmologist_name=doctor_user.full_name or doctor_user.email,
        decision_type=rev.clinical_decision or rev.decision_type or "AGREE_WITH_AI",
        confirmed_grade=rev.confirmed_grade if rev.confirmed_grade is not None else rev.final_grade,
        is_concordant=rev.agrees_with_ai,
        override_rationale=rev.override_rationale,
        clinical_status=rev.clinical_status,
        clinical_notes=rev.clinical_notes,
        digital_signature_hash=rev.digital_signature_hash,
        reviewed_at=rev.reviewed_at
    )
