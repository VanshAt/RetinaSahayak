from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.services.explainability_service import get_screening_explainability_data

router = APIRouter(prefix="/screenings", tags=["Explainability & Grad-CAM"])


@router.get("/{id}/explainability", response_model=APIResponse)
def get_screening_explainability(
    id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve full explainability visual artifacts:
    Grad-CAM++ heatmap, blended overlay, and transparent mock/real engine attribution.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    data = get_screening_explainability_data(
        screening_id=id,
        db=db,
        current_user=current_user,
        client_ip=client_ip
    )
    return APIResponse(success=True, data=data)

