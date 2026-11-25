from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.schemas.clinical_review import ClinicalReviewCreate, ClinicalReviewResponse
from backend.app.schemas.common import APIResponse
from backend.app.services.review_service import submit_clinical_review


router = APIRouter(prefix="/reviews", tags=["Clinical Reviews"])


@router.post("", response_model=APIResponse)
def create_clinical_review(
    review_in: ClinicalReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Submits an official ophthalmologist review with digital cryptographic signature.
    Updates screening status to DOCTOR_VERIFIED and closes/verifies referral.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    review_resp = submit_clinical_review(
        db=db,
        review_in=review_in,
        doctor_user=current_user,
        client_ip=client_ip
    )
    return APIResponse(success=True, data=review_resp.model_dump())
