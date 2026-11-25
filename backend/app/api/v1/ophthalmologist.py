from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.schemas.referral import (
    ClinicalReviewSubmission,
    CaseEscalationRequest,
    CaseCloseRequest
)
from backend.app.services.referral_service import (
    get_ophthalmologist_referral_queue,
    get_referral_case_detail,
    escalate_referral_case,
    close_referral_case
)
from backend.app.services.review_service import submit_ophthalmologist_referral_review
from backend.app.services.audit_service import create_audit_log


router = APIRouter(prefix="/ophthalmologist/referrals", tags=["Ophthalmologist Cockpit"])


@router.get("", response_model=APIResponse)
def list_referrals(
    status: Optional[str] = Query(None, description="Filter: PENDING, IN_REVIEW, REVIEWED, ESCALATED, CLOSED, ALL"),
    priority: Optional[str] = Query(None, description="Filter: CRITICAL, HIGH, MEDIUM, REVIEW_REQUIRED, ALL"),
    uncertain_only: bool = Query(False, description="Filter for uncertain low-confidence cases"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Returns prioritized referral queue for ophthalmologists and district administrators.
    Rejects PHC worker access with 403 Forbidden.
    """
    items, total = get_ophthalmologist_referral_queue(
        db=db,
        status_filter=status,
        priority_filter=priority,
        uncertain_only=uncertain_only,
        skip=skip,
        limit=limit,
        current_user=current_user
    )

    return APIResponse(
        success=True,
        data={
            "items": [item.model_dump() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{referral_id}", response_model=APIResponse)
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Returns full clinical evidence pack for a referral:
    images, Grad-CAM++ overlays, probabilities, clinical explanations, review history, and audit trail.
    """
    detail = get_referral_case_detail(db, referral_id=referral_id, current_user=current_user)
    return APIResponse(success=True, data=detail.model_dump())


@router.post("/{referral_id}/review", response_model=APIResponse)
def review_referral(
    referral_id: str,
    submission: ClinicalReviewSubmission,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Submits an official ophthalmologist review, validating clinical decisions,
    recording digital signature, updating status to REVIEWED or CLOSED, and audit logging.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    detail = submit_ophthalmologist_referral_review(
        db=db,
        referral_id=referral_id,
        submission=submission,
        doctor_user=current_user,
        client_ip=client_ip
    )
    return APIResponse(success=True, data=detail.model_dump())


@router.post("/{referral_id}/escalate", response_model=APIResponse)
def escalate_referral(
    referral_id: str,
    escalation_in: CaseEscalationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Escalates a referral to a tertiary facility with reason and clinical notes.
    Sets status to ESCALATED and audit logs REFERRAL_ESCALATED.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    detail = escalate_referral_case(
        db=db,
        referral_id=referral_id,
        escalation_reason=escalation_in.escalation_reason,
        clinical_notes=escalation_in.clinical_notes,
        target_hospital_name=escalation_in.target_hospital_name,
        current_user=current_user,
        client_ip=client_ip
    )
    return APIResponse(success=True, data=detail.model_dump())


@router.post("/{referral_id}/close", response_model=APIResponse)
def close_referral(
    referral_id: str,
    close_in: CaseCloseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Closes a referral case with reason and mandatory clinical notes.
    Sets status to CLOSED, stores closed_by and closed_at, and audit logs REFERRAL_CLOSED.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    detail = close_referral_case(
        db=db,
        referral_id=referral_id,
        close_reason=close_in.close_reason,
        clinical_notes=close_in.clinical_notes,
        current_user=current_user,
        client_ip=client_ip
    )
    return APIResponse(success=True, data=detail.model_dump())
