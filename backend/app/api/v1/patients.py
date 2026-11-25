import random
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_role
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.schemas.common import APIResponse
from backend.app.schemas.patient import PatientCreate, PatientResponse

router = APIRouter(prefix="/patients", tags=["Patients"])


def generate_patient_code(db: Session) -> str:
    """Generates a unique anonymized patient code (e.g., PAT-VNS-8841)."""
    while True:
        code = f"PAT-VNS-{random.randint(1000, 9999)}"
        exists = db.query(Patient).filter(Patient.patient_code == code).first()
        if not exists:
            return code


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    request: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["PHC_WORKER", "ADMIN"]))
):
    """Register a new anonymized patient record (Zero Direct PII)."""
    patient_code = request.patient_code or generate_patient_code(db)

    # Check if patient code already exists
    existing = db.query(Patient).filter(Patient.patient_code == patient_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient code '{patient_code}' is already registered."
        )

    health_center_id = current_user.health_center_id
    if not health_center_id:
        from backend.app.models.health_center import HealthCenter
        hc = db.query(HealthCenter).first()
        health_center_id = hc.id if hc else "hc_ramnagar_01"

    new_patient = Patient(
        patient_code=patient_code,
        age_group=request.age_group,
        gender=request.gender.upper(),
        diabetes_duration_years=request.diabetes_duration_years,
        known_hypertension=request.known_hypertension,
        phc_location=request.phc_location or (current_user.health_center.name if current_user.health_center else "Primary Health Centre"),
        health_center_id=health_center_id
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="REGISTER_PATIENT",
        resource_type="Patient",
        resource_id=new_patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        payload_data={
            "patient_code": new_patient.patient_code,
            "health_center_id": new_patient.health_center_id
        }
    )
    db.commit()

    patient_dto = PatientResponse(
        id=new_patient.id,
        patient_code=new_patient.patient_code,
        age_group=new_patient.age_group,
        gender=new_patient.gender,
        diabetes_duration_years=new_patient.diabetes_duration_years,
        known_hypertension=new_patient.known_hypertension,
        phc_location=new_patient.phc_location,
        health_center_id=new_patient.health_center_id,
        registered_at=new_patient.registered_at,
        screenings_count=0
    )

    return APIResponse(success=True, data=patient_dto.model_dump())


@router.get("", response_model=APIResponse)
def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve paginated list of anonymized patients."""
    query = db.query(Patient)

    # If worker, filter by their health center if configured
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        query = query.filter(Patient.health_center_id == current_user.health_center_id)

    if search:
        query = query.filter(Patient.patient_code.ilike(f"%{search}%"))

    total = query.count()
    patients = query.order_by(desc(Patient.registered_at)).offset((page - 1) * limit).limit(limit).all()

    items = []
    for p in patients:
        items.append(PatientResponse(
            id=p.id,
            patient_code=p.patient_code,
            age_group=p.age_group,
            gender=p.gender,
            diabetes_duration_years=p.diabetes_duration_years,
            known_hypertension=p.known_hypertension,
            phc_location=p.phc_location,
            health_center_id=p.health_center_id,
            registered_at=p.registered_at,
            screenings_count=len(p.screenings)
        ).model_dump())

    return APIResponse(
        success=True,
        data={
            "total": total,
            "page": page,
            "limit": limit,
            "items": items
        }
    )


@router.get("/{id}", response_model=APIResponse)
def get_patient(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve single patient demographic profile and prior screenings."""
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

    # Isolation: PHC Worker cannot access patients belonging to other health centers
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if patient.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access patient records from another health center."
            )

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="VIEW_PATIENT",
        resource_type="Patient",
        resource_id=patient.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        payload_data={"patient_code": patient.patient_code, "health_center_id": patient.health_center_id}
    )
    db.commit()

    screenings_data = []
    for s in patient.screenings:
        screenings_data.append({
            "id": s.id,
            "eye_side": s.eye_side,
            "dilation_status": s.dilation_status,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "predicted_grade": s.ai_analysis.predicted_grade if s.ai_analysis else None,
            "is_referable": s.ai_analysis.is_referable if s.ai_analysis else None
        })

    patient_dto = PatientResponse(
        id=patient.id,
        patient_code=patient.patient_code,
        age_group=patient.age_group,
        gender=patient.gender,
        diabetes_duration_years=patient.diabetes_duration_years,
        known_hypertension=patient.known_hypertension,
        phc_location=patient.phc_location,
        health_center_id=patient.health_center_id,
        registered_at=patient.registered_at,
        screenings_count=len(patient.screenings)
    ).model_dump()

    patient_dto["screenings"] = screenings_data

    return APIResponse(success=True, data=patient_dto)
