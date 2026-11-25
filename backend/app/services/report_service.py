from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.screening import Screening
from backend.app.models.user import User
from backend.app.models.report_metadata import ReportMetadata
from backend.app.reports.pdf_generator import generate_screening_pdf
from backend.app.services.storage.factory import get_storage_provider
from backend.app.services.audit_service import create_audit_log


def generate_and_save_screening_report(
    screening_id: str,
    db: Session,
    current_user: User,
    client_ip: str = "127.0.0.1"
) -> Tuple[bytes, str, ReportMetadata]:
    """
    Business logic for screening report generation:
    1. Enforces tenant isolation (worker restricted to their health center, ophthalmologist/admin allowed).
    2. Builds 2-page clinical PDF report.
    3. Persists report file via storage provider abstraction.
    4. Records ReportMetadata entity in database.
    5. Logs REPORT_DOWNLOADED audit event with user attribution and cryptographic hash.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening encounter not found."
        )

    # Multi-tenant Worker Isolation: PHC Worker cannot access screening reports from another health center
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if screening.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to download reports from another health center."
            )

    # Generate PDF bytes using ReportLab
    pdf_bytes = generate_screening_pdf(db=db, screening_id=screening_id)

    # Persist report to storage provider
    storage = get_storage_provider()
    rel_path = f"reports/RetinaSahayak_Report_{screening.id[:8].upper()}.pdf"
    stored_path = storage.save_file(pdf_bytes, rel_path, content_type="application/pdf")

    # Record report metadata in database
    model_ver = (
        screening.ai_analysis.model_version
        if screening.ai_analysis
        else "RetinaSahayak-EfficientNet-v2.1"
    )

    report_meta = ReportMetadata(
        screening_id=screening.id,
        generated_by=current_user.id,
        report_file_path=stored_path,
        report_version="v2.1",
        model_version=model_ver
    )
    db.add(report_meta)
    db.commit()
    db.refresh(report_meta)

    # Record Audit Log Entry
    create_audit_log(
        db=db,
        action="REPORT_DOWNLOADED",
        resource_type="Screening",
        resource_id=screening.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        client_ip=client_ip,
        payload_data={
            "screening_id": screening.id,
            "patient_code": screening.patient.patient_code if screening.patient else None,
            "report_id": report_meta.id,
            "report_file_path": stored_path,
            "format": "PDF"
        }
    )
    db.commit()

    filename = f"RetinaSahayak_Screening_Report_{screening.id[:8].upper()}.pdf"
    return pdf_bytes, filename, report_meta
