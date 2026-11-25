from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ClinicalReviewCreate(BaseModel):
    screening_id: str
    decision_type: str = Field(..., description="AGREE_WITH_AI, MODIFY_GRADE, MARK_NON_REFERABLE, MARK_REFERABLE, REQUEST_REPEAT_IMAGING, MARK_FOLLOW_UP_REQUIRED, CLOSE_CASE")
    confirmed_grade: int = Field(..., ge=0, le=4)
    override_rationale: Optional[str] = None
    clinical_status: str = Field(default="REFERRED_TERTIARY", description="FOLLOW_UP_REQUIRED, REFERRED_TERTIARY, CASE_CLOSED")
    clinical_notes: str
    doctor_digital_signature: Optional[str] = None


class ClinicalReviewResponse(BaseModel):
    id: str
    screening_id: str
    ophthalmologist_id: str
    ophthalmologist_name: str
    decision_type: str
    confirmed_grade: int
    is_concordant: bool
    override_rationale: Optional[str] = None
    clinical_status: str
    clinical_notes: str
    digital_signature_hash: str
    reviewed_at: datetime

    class Config:
        from_attributes = True
