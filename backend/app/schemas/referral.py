from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==========================================
# REFERRAL SCHEMAS
# ==========================================

class ReferralQueueItem(BaseModel):
    referral_id: str
    screening_id: str
    patient_anonymized_id: str
    phc_location: str
    screening_date: datetime
    predicted_grade: int
    grade_label: str
    confidence: float
    uncertainty_status: str
    priority: str
    referral_reason: str
    referral_status: str
    assigned_ophthalmologist: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralQueueResponse(BaseModel):
    items: List[ReferralQueueItem]
    total: int
    skip: int
    limit: int


class AuditTrailEntry(BaseModel):
    action: str
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    status: str
    timestamp: datetime
    payload_hash: Optional[str] = None


class ClinicalReviewSummary(BaseModel):
    review_id: str
    ophthalmologist_id: str
    ophthalmologist_name: Optional[str] = None
    clinical_decision: str
    ai_predicted_grade: Optional[int] = None
    final_grade: Optional[int] = None
    clinical_notes: str
    agrees_with_ai: bool
    reviewed_at: datetime
    review_status: str
    digital_signature_hash: Optional[str] = None


class ReferralDetailResponse(BaseModel):
    referral_id: str
    screening_id: str
    patient_anonymized_id: str
    phc_location: str
    screening_date: datetime
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    overlay_url: Optional[str] = None
    predicted_grade: int
    grade_label: str
    class_probabilities: Dict[str, float]
    confidence: float
    uncertainty_status: str
    clinical_explanation: str
    recommended_action: str
    inference_engine: str
    model_version: str
    current_referral_status: str
    priority: str
    existing_clinical_review: Optional[ClinicalReviewSummary] = None
    audit_trail: List[AuditTrailEntry] = []

    class Config:
        from_attributes = True


# Legacy / backwards compatible ReferralResponse
class ReferralResponse(BaseModel):
    id: str
    screening_id: str
    patient_id: str
    patient_code: str
    age_group: str
    gender: str
    phc_name: str
    eye_side: str
    predicted_grade: int
    confidence_score: float
    is_uncertain: bool
    clinical_priority: str
    priority: Optional[str] = None
    status: str
    target_hospital_name: Optional[str] = None
    dispatched_at: datetime
    resolved_at: Optional[datetime] = None
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    overlay_url: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# CLINICAL REVIEW SCHEMAS
# ==========================================

class ClinicalReviewSubmission(BaseModel):
    clinical_decision: str = Field(
        ...,
        description="AGREE_WITH_AI, MODIFY_GRADE, REQUEST_REPEAT_IMAGING, MARK_NON_REFERABLE, MARK_REFERABLE, MARK_FOLLOW_UP_REQUIRED, CLOSE_CASE"
    )
    final_grade: Optional[int] = Field(None, ge=0, le=4, description="Required if clinical_decision is MODIFY_GRADE")
    clinical_notes: Optional[str] = Field(None, description="Clinical justification notes")


class CaseEscalationRequest(BaseModel):
    escalation_reason: str = Field(
        ...,
        description="REQUIRES_SECOND_OPINION, SUSPECTED_PROLIFERATIVE_DR, POSSIBLE_DME_FUTURE_EVALUATION, IMAGE_QUALITY_CONCERN, TECHNICAL_ISSUE, OTHER"
    )
    clinical_notes: str = Field(..., min_length=3, description="Detailed clinical notes for escalation")
    target_hospital_name: Optional[str] = Field("District Tertiary Eye Hospital", description="Target hospital")


class CaseCloseRequest(BaseModel):
    close_reason: str = Field(
        ...,
        description="CLINICALLY_RESOLVED, DUPLICATE_SCREENING, FALSE_POSITIVE_VERIFIED, PATIENT_DECLINED_TREATMENT, OTHER"
    )
    clinical_notes: str = Field(..., min_length=3, description="Clinical justification notes for case closure")


# Admin referral statistics schema
class ReferralStatisticsResponse(BaseModel):
    total_referrals: int
    pending_referrals: int
    in_review_referrals: int
    reviewed_referrals: int
    escalated_referrals: int
    closed_referrals: int
    critical_cases: int
    high_priority_cases: int
    medium_priority_cases: int
    review_required_cases: int
    average_review_time_minutes: float
    ai_doctor_agreement_rate: float
