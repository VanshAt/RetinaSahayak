from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from backend.app.schemas.ml_result import IQAResult, MLAnalysisResponse


class ScreeningCreate(BaseModel):
    patient_id: str
    eye_side: str  # OD, OS
    camera_device_model: Optional[str] = "Forus 3nethra Classic"
    dilation_status: Optional[str] = "UNDILATED"


class ImageUploadResponse(BaseModel):
    image_id: str
    screening_id: str
    original_image_url: str
    enhanced_image_url: Optional[str] = None
    storage_provider: str
    iqa_result: IQAResult


class ScreeningResponse(BaseModel):
    id: str
    patient_id: str
    health_center_id: str
    worker_id: str
    eye_side: str
    camera_device_model: str
    dilation_status: str
    status: str
    created_at: datetime
    updated_at: datetime
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    iqa_status: Optional[str] = None
    analysis: Optional[MLAnalysisResponse] = None

    class Config:
        from_attributes = True


class OfflineSyncItem(BaseModel):
    client_timestamp: str
    patient_code: str
    age_group: str
    gender: str
    diabetes_duration_years: int
    eye_side: str
    image_base64: str
    filename: str


class OfflineBatchSyncRequest(BaseModel):
    items: List[OfflineSyncItem]
