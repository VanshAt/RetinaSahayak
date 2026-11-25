from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class GradeDistribution(BaseModel):
    grade_0_normal: int = 0
    grade_1_mild: int = 0
    grade_2_moderate: int = 0
    grade_3_severe: int = 0
    grade_4_pdr: int = 0


class AnalyticsOverviewResponse(BaseModel):
    total_screenings: int
    unique_patients: int
    good_quality_count: int
    borderline_quality_count: int
    rejected_quality_count: int
    referable_count: int
    non_referable_count: int
    uncertain_count: int
    pending_referrals: int
    reviewed_referrals: int
    referable_percentage: float
    grade_distribution: GradeDistribution
    concordance_rate: float
    avg_inference_latency_ms: float


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    status: str = "SUCCESS"
    client_ip: str
    payload_hash: str
    created_at: Any

    class Config:
        from_attributes = True

