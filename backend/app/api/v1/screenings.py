import base64
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_role
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.screening import Screening
from backend.app.models.fundus_image import FundusImage
from backend.app.schemas.common import APIResponse
from backend.app.schemas.screening import (
    ScreeningCreate,
    ScreeningResponse,
    ImageUploadResponse,
    OfflineBatchSyncRequest
)
from backend.app.schemas.ml_result import IQAResult, IQAMetrics
from backend.app.services.storage.factory import get_storage_provider
from backend.app.utils.image_utils import validate_image_file, bytes_to_numpy, numpy_to_jpeg_bytes
from backend.app.ml.iqa import evaluate_image_quality
from backend.app.ml.enhancer import enhance_retinal_image

router = APIRouter(prefix="/screenings", tags=["Screenings & Images"])


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def create_screening(
    request: ScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["PHC_WORKER", "ADMIN"]))
):
    """Initialize a new retinal screening session for an anonymized patient."""
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

    # Isolation: PHC Worker cannot screen another center's patient
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if patient.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot initiate screening for a patient from another health center."
            )

    new_screening = Screening(
        patient_id=patient.id,
        health_center_id=patient.health_center_id,
        worker_id=current_user.id,
        eye_side=request.eye_side.upper(),
        camera_device_model=request.camera_device_model or "Portable Fundus Camera",
        dilation_status=request.dilation_status.upper() or "UNDILATED",
        status="INITIALIZED"
    )

    db.add(new_screening)
    db.commit()
    db.refresh(new_screening)

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="CREATE_SCREENING",
        resource_type="Screening",
        resource_id=new_screening.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        payload_data={
            "patient_id": patient.id,
            "screening_id": new_screening.id,
            "eye_side": new_screening.eye_side,
            "health_center_id": patient.health_center_id
        }
    )
    db.commit()

    return APIResponse(
        success=True,
        data={
            "id": new_screening.id,
            "patient_id": new_screening.patient_id,
            "patient_code": patient.patient_code,
            "eye_side": new_screening.eye_side,
            "status": new_screening.status,
            "created_at": new_screening.created_at.isoformat()
        }
    )


@router.post("/{id}/upload-fundus", response_model=APIResponse)
async def upload_fundus_image(
    id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["PHC_WORKER", "ADMIN"]))
):
    """
    Upload retinal fundus photograph, run instant Image Quality Assessment (IQA),
    apply CLAHE enhancement if borderline, and store via StorageProvider abstraction.
    """
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening encounter not found.")

    # Isolation: PHC Worker can only modify their own health center / screening records
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if screening.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot upload images for a screening from another health center."
            )

    file_bytes = await file.read()
    is_valid, err_msg, width, height = validate_image_file(file_bytes, file.filename or "fundus.jpg")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Decode to RGB numpy array
    img_rgb = bytes_to_numpy(file_bytes)

    # Run deterministic IQA gate
    iqa_eval = evaluate_image_quality(img_rgb)
    storage = get_storage_provider()

    # Save original fundus image
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "jpg"
    base_stem = file.filename.rsplit(".", 1)[0] if file.filename and "." in file.filename else "fundus"
    # Clean stem of any slashes
    clean_stem = "".join(c for c in base_stem if c.isalnum() or c in ("-", "_")).strip() or "fundus"
    orig_rel_path = f"raw_images/{screening.id}_{screening.eye_side}_{clean_stem}.{ext}"
    stored_orig_path = storage.save_file(file_bytes, orig_rel_path, content_type=file.content_type or "image/jpeg")

    # If Borderline, automatically apply CLAHE and Ben Graham enhancement
    stored_enhanced_path = None
    if iqa_eval["iqa_status"] == "BORDERLINE":
        enhanced_np = enhance_retinal_image(img_rgb)
        enhanced_bytes = numpy_to_jpeg_bytes(enhanced_np)
        enhance_rel_path = f"enhanced/{screening.id}_{screening.eye_side}_enhanced.jpg"
        stored_enhanced_path = storage.save_file(enhanced_bytes, enhance_rel_path, content_type="image/jpeg")

    # Upsert FundusImage entity
    existing_img = db.query(FundusImage).filter(FundusImage.screening_id == screening.id).first()
    if existing_img:
        existing_img.original_file_path = stored_orig_path
        existing_img.enhanced_file_path = stored_enhanced_path
        existing_img.storage_provider = storage.get_provider_name()
        existing_img.iqa_status = iqa_eval["iqa_status"]
        existing_img.sharpness_score = iqa_eval["sharpness_score"]
        existing_img.illumination_score = iqa_eval["illumination_score"]
        existing_img.vessel_contrast_score = iqa_eval["vessel_contrast_score"]
        existing_img.actionable_feedback = iqa_eval["actionable_feedback"]
        existing_img.width = width
        existing_img.height = height
        fundus_img = existing_img
    else:
        fundus_img = FundusImage(
            screening_id=screening.id,
            original_file_path=stored_orig_path,
            enhanced_file_path=stored_enhanced_path,
            storage_provider=storage.get_provider_name(),
            iqa_status=iqa_eval["iqa_status"],
            sharpness_score=iqa_eval["sharpness_score"],
            illumination_score=iqa_eval["illumination_score"],
            vessel_contrast_score=iqa_eval["vessel_contrast_score"],
            actionable_feedback=iqa_eval["actionable_feedback"],
            width=width,
            height=height
        )
        db.add(fundus_img)

    # Update screening status
    if iqa_eval["iqa_status"] == "REJECT":
        screening.status = "IQA_REJECTED"
    else:
        screening.status = "IMAGE_UPLOADED"

    db.commit()
    db.refresh(screening)
    db.refresh(fundus_img)

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="UPLOAD_FUNDUS",
        resource_type="FundusImage",
        resource_id=fundus_img.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        payload_data={
            "screening_id": screening.id,
            "patient_id": screening.patient_id,
            "image_id": fundus_img.id,
            "iqa_status": iqa_eval["iqa_status"],
            "eye_side": screening.eye_side
        }
    )
    db.commit()

    iqa_dto = IQAResult(
        iqa_status=iqa_eval["iqa_status"],
        is_acceptable=iqa_eval["is_acceptable"],
        metrics=IQAMetrics(
            sharpness_score=iqa_eval["sharpness_score"],
            illumination_score=iqa_eval["illumination_score"],
            vessel_contrast_score=iqa_eval["vessel_contrast_score"]
        ),
        issues=iqa_eval["issues"],
        actionable_feedback=iqa_eval["actionable_feedback"]
    )

    response_data = ImageUploadResponse(
        image_id=fundus_img.id,
        screening_id=screening.id,
        original_image_url=storage.get_url(stored_orig_path),
        enhanced_image_url=storage.get_url(stored_enhanced_path) if stored_enhanced_path else None,
        storage_provider=storage.get_provider_name(),
        iqa_result=iqa_dto
    )

    return APIResponse(success=True, data=response_data.model_dump())


@router.get("/{id}", response_model=APIResponse)
def get_screening(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve full screening details, image URLs, and diagnostic results."""
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening encounter not found.")

    # Isolation: PHC Worker cannot access screening records from another health center
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if screening.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access screening records from another health center."
            )

    from backend.app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        action="VIEW_SCREENING",
        resource_type="Screening",
        resource_id=screening.id,
        user_id=current_user.id,
        user_role=current_user.role,
        status="SUCCESS",
        payload_data={
            "patient_id": screening.patient_id,
            "screening_id": screening.id,
            "health_center_id": screening.health_center_id
        }
    )
    db.commit()

    storage = get_storage_provider()
    orig_url = storage.get_url(screening.fundus_image.original_file_path) if screening.fundus_image else None
    enh_url = storage.get_url(screening.fundus_image.enhanced_file_path) if screening.fundus_image and screening.fundus_image.enhanced_file_path else None

    screening_dict = {
        "id": screening.id,
        "patient_id": screening.patient_id,
        "patient_code": screening.patient.patient_code if screening.patient else None,
        "age_group": screening.patient.age_group if screening.patient else None,
        "gender": screening.patient.gender if screening.patient else None,
        "health_center_id": screening.health_center_id,
        "health_center_name": screening.health_center.name if screening.health_center else None,
        "worker_name": screening.worker.full_name if screening.worker else None,
        "eye_side": screening.eye_side,
        "camera_device_model": screening.camera_device_model,
        "dilation_status": screening.dilation_status,
        "status": screening.status,
        "created_at": screening.created_at.isoformat(),
        "updated_at": screening.updated_at.isoformat(),
        "original_image_url": orig_url,
        "enhanced_image_url": enh_url,
        "iqa_status": screening.fundus_image.iqa_status if screening.fundus_image else None,
        "actionable_feedback": screening.fundus_image.actionable_feedback if screening.fundus_image else None,
    }

    if screening.ai_analysis:
        ana = screening.ai_analysis
        screening_dict["analysis"] = {
            "predicted_grade": ana.predicted_grade,
            "confidence_score": ana.confidence_score,
            "is_referable": ana.is_referable,
            "is_uncertain": ana.is_uncertain,
            "triage_urgency": ana.triage_urgency,
            "dme_risk_level": ana.dme_risk_level,
            "clinical_explanation": ana.clinical_explanation,
            "heatmap_url": storage.get_url(ana.explainability_map.heatmap_file_path) if ana.explainability_map else None,
            "overlay_url": storage.get_url(ana.explainability_map.overlay_file_path) if ana.explainability_map else None,
        }

    return APIResponse(success=True, data=screening_dict)


@router.post("/offline-batch-sync", response_model=APIResponse)
def offline_batch_sync(
    request: OfflineBatchSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["PHC_WORKER", "ADMIN"]))
):
    """Synchronize offline encounters queued locally in browser IndexedDB."""
    synced_records = []
    storage = get_storage_provider()

    for item in request.items:
        # 1. Find or create patient
        patient = db.query(Patient).filter(Patient.patient_code == item.patient_code).first()
        if not patient:
            patient = Patient(
                patient_code=item.patient_code,
                age_group=item.age_group,
                gender=item.gender,
                diabetes_duration_years=item.diabetes_duration_years,
                health_center_id=current_user.health_center_id or "hc_ramnagar_01"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        # 2. Create screening
        screening = Screening(
            patient_id=patient.id,
            health_center_id=patient.health_center_id,
            worker_id=current_user.id,
            eye_side=item.eye_side,
            status="IMAGE_UPLOADED"
        )
        db.add(screening)
        db.commit()
        db.refresh(screening)

        # 3. Decode base64 image and save
        try:
            b64_clean = item.image_base64.split(",")[-1]
            raw_bytes = base64.b64decode(b64_clean)
            orig_rel_path = f"raw_images/{screening.id}_{screening.eye_side}.jpg"
            stored_path = storage.save_file(raw_bytes, orig_rel_path)

            img_np = bytes_to_numpy(raw_bytes)
            iqa_eval = evaluate_image_quality(img_np)

            fundus_img = FundusImage(
                screening_id=screening.id,
                original_file_path=stored_path,
                storage_provider=storage.get_provider_name(),
                iqa_status=iqa_eval["iqa_status"],
                sharpness_score=iqa_eval["sharpness_score"],
                illumination_score=iqa_eval["illumination_score"],
                vessel_contrast_score=iqa_eval["vessel_contrast_score"],
                actionable_feedback=iqa_eval["actionable_feedback"],
                width=img_np.shape[1],
                height=img_np.shape[0]
            )
            db.add(fundus_img)
            db.commit()

            synced_records.append({
                "patient_code": patient.patient_code,
                "screening_id": screening.id,
                "status": "SYNCED"
            })
        except Exception as e:
            synced_records.append({
                "patient_code": item.patient_code,
                "error": str(e),
                "status": "FAILED"
            })

    return APIResponse(
        success=True,
        data={
            "total_items": len(request.items),
            "synced_count": sum(1 for r in synced_records if r["status"] == "SYNCED"),
            "results": synced_records
        }
    )


@router.post("/{id}/analyze", response_model=APIResponse)
def analyze_screening(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["PHC_WORKER", "OPHTHALMOLOGIST", "ADMIN"]))
):
    """
    Triggers end-to-end deep learning classification, uncertainty estimation,
    Grad-CAM++ explainability, and automated referral triage.
    """
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening encounter not found.")

    # Isolation: PHC Worker cannot run analysis on another center's screening
    if current_user.role == "PHC_WORKER" and current_user.health_center_id:
        if screening.health_center_id != current_user.health_center_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot analyze a screening from another health center."
            )

    from backend.app.services.inference_service import run_screening_analysis_pipeline
    analysis_result = run_screening_analysis_pipeline(screening_id=id, db=db, current_user=current_user)
    return APIResponse(success=True, data=analysis_result.model_dump())

