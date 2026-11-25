from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    patient_code: Optional[str] = None  # Auto-generated if not provided
    age_group: str = Field(..., description="18-35, 36-50, 51-65, 65+")
    gender: str = Field(..., description="MALE, FEMALE, OTHER")
    diabetes_duration_years: int = Field(default=0, ge=0, le=70)
    known_hypertension: bool = False
    phc_location: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    patient_code: str
    age_group: str
    gender: str
    diabetes_duration_years: int
    known_hypertension: bool
    phc_location: Optional[str] = None
    health_center_id: str
    registered_at: datetime
    screenings_count: Optional[int] = 0

    class Config:
        from_attributes = True
