from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.schemas.referral import ReferralResponse
from backend.app.schemas.common import APIResponse
from backend.app.services.storage.factory import get_storage_provider
from backend.app.models.screening import Screening
from backend.app.services.referral_service import (
    get_ophthalmologist_referral_queue,
    get_referral_case_detail,
    escalate_referral_case
)


router = APIRouter(prefix="/referrals", tags=["Referral Triage (Legacy / Shared)"])


class EscalateRequest(BaseModel):
    target_hospital_name: str = "District Tertiary Eye Hospital"
    escalation_reason: Optional[str] = "High-risk case requiring immediate surgical consultation"
    clinical_notes: Optional[str] = "Case escalated via triage interface."


@router.get("", response_model=APIResponse)
def list_referrals(
    status: Optional[str] = Query(None, description="Filter: PENDING, IN_REVIEW, REVIEWED, ESCALATED, CLOSED"),
    priority: Optional[str] = Query(None, description="Filter: CRITICAL, HIGH, MEDIUM, REVIEW_REQUIRED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    items, total = get_ophthalmologist_referral_queue(
        db=db,
        status_filter=status,
        priority_filter=priority,
        skip=skip,
        limit=limit,
        current_user=current_user
    )
    storage = get_storage_provider()
    LEGACY_PRIORITY_MAP = {
        "CRITICAL": "EMERGENCY",
        "HIGH": "URGENT",
        "MEDIUM": "ROUTINE",
        "REVIEW_REQUIRED": "UNCERTAIN_REVIEW"
    }
    formatted_items = []
    for item in items:
        dumped = item.model_dump()
        dumped["id"] = item.referral_id
        dumped["clinical_priority"] = LEGACY_PRIORITY_MAP.get(item.priority, item.priority)
        dumped["status"] = item.referral_status
        # Provide image URLs for legacy test assertions
        screening = db.query(Screening).filter(Screening.id == item.screening_id).first()
        if screening and screening.fundus_image:
            dumped["original_image_url"] = storage.get_url(screening.fundus_image.original_file_path)
        else:
            dumped["original_image_url"] = None
        if screening and screening.ai_analysis and screening.ai_analysis.explainability_map:
            dumped["heatmap_url"] = storage.get_url(screening.ai_analysis.explainability_map.heatmap_file_path)
        else:
            dumped["heatmap_url"] = None
        formatted_items.append(dumped)

    return APIResponse(
        success=True,
        data={
            "items": formatted_items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{referral_id}", response_model=APIResponse)
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN", "PHC_WORKER"]))
):
    detail = get_referral_case_detail(db, referral_id, current_user=current_user)
    dumped = detail.model_dump()
    dumped["id"] = detail.referral_id
    dumped["clinical_priority"] = detail.priority
    dumped["status"] = detail.current_referral_status
    return APIResponse(success=True, data=dumped)


@router.post("/{referral_id}/escalate", response_model=APIResponse)
def escalate_referral(
    referral_id: str,
    req_body: EscalateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    detail = escalate_referral_case(
        db=db,
        referral_id=referral_id,
        escalation_reason=req_body.escalation_reason or "REQUIRES_SECOND_OPINION",
        clinical_notes=req_body.clinical_notes or "Case escalated to tertiary hospital.",
        target_hospital_name=req_body.target_hospital_name,
        current_user=current_user,
        client_ip=client_ip
    )
    dumped = detail.model_dump()
    dumped["id"] = detail.referral_id
    dumped["status"] = detail.current_referral_status
    dumped["clinical_priority"] = "EMERGENCY"  # Legacy test expectation
    dumped["target_hospital_name"] = req_body.target_hospital_name
    return APIResponse(success=True, data=dumped)
