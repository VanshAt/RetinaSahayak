from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.services.report_service import generate_and_save_screening_report

router = APIRouter(prefix="/screenings", tags=["Medical Reports"])


@router.get("/{screening_id}/report")
@router.get("/{screening_id}/report/pdf")
def download_screening_pdf_report(
    screening_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates and streams a professional 2-page A4 medical screening report in PDF format
    with embedded fundus images, Grad-CAM++ heatmaps, IQA metrics, QR code, and CDSS disclaimer.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    pdf_bytes, filename, _ = generate_and_save_screening_report(
        screening_id=screening_id,
        db=db,
        current_user=current_user,
        client_ip=client_ip
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\"",
            "Content-Type": "application/pdf"
        }
    )

