from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    num_phcs: int = Field(default=50, ge=1, le=200)
    patients_per_phc_per_day: int = Field(default=8, ge=1, le=50)
    poor_quality_percent: float = Field(default=15.0, ge=0.0, le=60.0)
    borderline_quality_percent: float = Field(default=20.0, ge=0.0, le=60.0)
    internet_bandwidth_mbps: float = Field(default=4.0, ge=0.5, le=50.0)
    cloud_inference_latency_ms: int = Field(default=320, ge=50, le=2000)
    local_inference_latency_ms: int = Field(default=110, ge=20, le=1000)
    num_ophthalmologists: int = Field(default=3, ge=1, le=20)
    avg_doctor_review_time_mins: float = Field(default=4.0, ge=1.0, le=15.0)
    referral_rate_percent: float = Field(default=28.0, ge=5.0, le=60.0)


class SimulationResponse(BaseModel):
    simulation_name: str
    daily_image_volume: int
    annual_patient_capacity: int
    images_rejected_daily: int
    images_enhanced_daily: int
    images_graded_daily: int
    referrals_generated_daily: int
    ophthalmologist_daily_capacity: int
    referral_queue_backlog: int
    avg_patient_wait_time_hours: float
    cloud_storage_gb_per_month: float
    daily_bandwidth_mb: float
    system_health: str  # OPTIMAL_SUSTAINABLE, BALANCED, BOTTLENECK_ALERT
    insights: list[str] = []
