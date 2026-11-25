export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'ADMIN' | 'PHC_WORKER' | 'OPHTHALMOLOGIST';
  health_center_id?: string;
}

export interface Patient {
  id: string;
  patient_code: string;
  age_group: string;
  gender: string;
  diabetes_duration_years: number;
  known_hypertension: boolean;
  health_center_id: string;
  created_at: string;
}

export interface Screening {
  id: string;
  patient_id: string;
  health_center_id: string;
  eye_side: 'OD' | 'OS';
  status: string;
  camera_device_model?: string;
  created_at: string;
}

export interface DMERisk {
  level: string;
  exudates_near_macula: boolean;
}

export interface LesionEvidence {
  microaneurysms_detected: number;
  blot_hemorrhages_detected: number;
  hard_exudates_detected: number;
  neovascularization_detected: boolean;
  suspicious_quadrants: string[];
}

export interface ExplainabilityDetail {
  heatmap_url: string;
  overlay_url: string;
  method: string;
  target_layer: string;
  candidate_lesions: any[];
}

export interface MLAnalysisResponse {
  screening_id: string;
  model_version: string;
  inference_engine: string;
  predicted_grade: number;
  grade_name: string;
  confidence_score: number;
  class_probabilities: Record<string, number>;
  is_referable: boolean;
  is_uncertain: boolean;
  uncertainty_score: number;
  triage_urgency: string;
  dme_risk: DMERisk;
  lesion_evidence: LesionEvidence;
  clinical_explanation: string;
  recommended_action: string;
  explainability: ExplainabilityDetail;
  referral_id?: string;
  referral_status?: string;
}

export interface Referral {
  id: string;
  screening_id: string;
  patient_id: string;
  patient_code: string;
  age_group: string;
  gender: string;
  phc_name: string;
  eye_side: string;
  predicted_grade: number;
  confidence_score: number;
  is_uncertain: boolean;
  clinical_priority: 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'UNCERTAIN_REVIEW';
  status: 'PENDING' | 'IN_REVIEW' | 'VERIFIED' | 'CLOSED' | 'ESCALATED';
  target_hospital_name: string;
  dispatched_at: string;
  resolved_at?: string;
  original_image_url?: string;
  enhanced_image_url?: string;
  heatmap_url?: string;
  overlay_url?: string;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id: string;
  client_ip: string;
  payload_hash: string;
  created_at: string;
}
