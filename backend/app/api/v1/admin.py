from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.services.referral_service import get_referral_statistics


router = APIRouter(prefix="/admin", tags=["Admin Oversight"])


@router.get("/referral-stats", response_model=APIResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Returns aggregated district referral metrics, triage breakdown,
    average turnaround times, and AI-doctor concordance rates.
    """
    stats = get_referral_statistics(db, current_user=current_user)
    return APIResponse(success=True, data=stats)
