
# RetinaSahayak: REST API Specification (OpenAPI 3.1)

**Problem Statement ID:** SIH26038 | **Base URL:** `http://localhost:8000/api/v1`
**Protocol:** HTTPS / HTTP 1.1 | **Content-Type:** `application/json` (unless `multipart/form-data` or `application/pdf`)
**Security:** Bearer Token (JWT in `Authorization: Bearer <token>`)
**Architecture:** Provider-Agnostic (Local vs Google Cloud Platform)

---

## 1. Authentication & Security Architecture

All protected endpoints require a Bearer token issued via `/auth/login`. Tokens encode user identity, role, and assigned facility.

### Pre-Configured Demo Credentials (One-Click Login)
| Role | Email | Password | Assigned Health Centre / Hospital |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@retinasahayak.in` | `AdminDemo123!` | Varanasi District Health Office |
| **PHC Health Worker** | `worker.ramnagar@retinasahayak.in` | `WorkerDemo123!` | Ramnagar Primary Health Centre |
| **PHC Health Worker (Alt)** | `worker.chiraigaon@retinasahayak.in`| `WorkerDemo123!` | Chiraigaon Community Health Centre |
| **Ophthalmologist** | `dr.verma@retinasahayak.in` | `DoctorDemo123!` | Banaras Hindu University (BHU) Eye Hospital |
| **Ophthalmologist (Alt)** | `dr.sharma@retinasahayak.in` | `DoctorDemo123!` | District Hospital Eye Department |

---

### Standard Response Envelope
All non-binary JSON responses adhere to the standard envelope:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-10-13T10:30:00Z"
}
```

Standard Error Envelope:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "IQA_REJECTED",
    "message": "Image failed diagnostic quality threshold.",
    "details": {
      "status": "REJECT",
      "issues": ["MOTION_BLUR"],
      "actionable_feedback": "Motion blur detected. Stabilize camera against patient headrest and instruct patient to fixate on the green alignment light."
    }
  },
  "timestamp": "2026-10-13T10:30:00Z"
}
```

---

## 2. Authentication Endpoints

### 2.1 User Login
- **Endpoint:** `POST /auth/login`
- **Access:** Public
- **Request Body:**
```json
{
  "email": "worker.ramnagar@retinasahayak.in",
  "password": "WorkerDemo123!"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_9b1deb4d",
      "full_name": "Smt. Sunita Devi (ANM)",
      "email": "worker.ramnagar@retinasahayak.in",
      "role": "PHC_WORKER",
      "health_center_id": "hc_ramnagar_01",
      "health_center_name": "Ramnagar Primary Health Centre"
    }
  },
  "error": null,
  "timestamp": "2026-10-13T10:30:00Z"
}
```

### 2.2 Token Refresh
- **Endpoint:** `POST /auth/refresh`
- **Access:** Public (Requires valid Refresh Token)

### 2.3 Current User Profile
- **Endpoint:** `GET /auth/me`
- **Access:** Authenticated (Any Role)

---

## 3. Anonymized Patient Management (Zero Direct PII)

To respect patient privacy, no real names, phone numbers, or Aadhaar numbers are collected in the demo or clinical screening flow.

### 3.1 Register Anonymized Patient
- **Endpoint:** `POST /patients`
- **Access:** `PHC_WORKER`, `ADMIN`
- **Request Body:**
```json
{
  "patient_code": "PAT-VNS-8841",
  "age_group": "51-65",
  "gender": "MALE",
  "diabetes_duration_years": 12,
  "known_hypertension": true,
  "phc_location": "Ramnagar PHC"
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "data": {
    "id": "pat_8841c9",
    "patient_code": "PAT-VNS-8841",
    "age_group": "51-65",
    "gender": "MALE",
    "diabetes_duration_years": 12,
    "known_hypertension": true,
    "phc_location": "Ramnagar PHC",
    "registered_at": "2026-10-13T10:31:00Z"
  },
  "error": null,
  "timestamp": "2026-10-13T10:31:00Z"
}
```

### 3.2 List Anonymized Patients
- **Endpoint:** `GET /patients?page=1&limit=20&search=PAT-VNS`
- **Access:** Authenticated

---

## 4. Screening, IQA & ML Inference Endpoints

### 4.1 Initialize Screening Encounter
- **Endpoint:** `POST /screenings`
- **Access:** `PHC_WORKER`
- **Request Body:**
```json
{
  "patient_id": "pat_8841c9",
  "eye_side": "OD",
  "camera_device_model": "Forus 3nethra Classic",
  "dilation_status": "DILATED"
}
```
- **Response `201 Created`:** Returns screening session ID `scr_22a7f8`.

### 4.2 Upload Fundus Image & Run IQA Gate
- **Endpoint:** `POST /screenings/{id}/upload-fundus`
- **Access:** `PHC_WORKER`
- **Content-Type:** `multipart/form-data`
- **Form Data:** `file: Binary image (JPEG/PNG/TIFF)`
- **Execution:** Evaluates sharpness ($\sigma^2$), illumination histogram, and vessel contrast.
- **Response `200 OK` (Quality: GOOD):**
```json
{
  "success": true,
  "data": {
    "image_id": "img_aa7109",
    "screening_id": "scr_22a7f8",
    "original_image_url": "/api/v1/storage/raw_images/scr_22a7f8_OD.jpg",
    "enhanced_image_url": null,
    "storage_provider": "LOCAL_STORAGE_PROVIDER",
    "iqa_status": "GOOD",
    "metrics": {
      "sharpness_score": 182.4,
      "illumination_score": 115.2,
      "vessel_contrast_score": 0.81
    },
    "actionable_feedback": "Image quality is optimal for AI diagnostic grading."
  },
  "error": null,
  "timestamp": "2026-10-13T10:32:00Z"
}
```

- **Response `200 OK` (Quality: BORDERLINE — Automatically Enhanced):**
```json
{
  "success": true,
  "data": {
    "image_id": "img_aa7109",
    "screening_id": "scr_22a7f8",
    "original_image_url": "/api/v1/storage/raw_images/scr_22a7f8_OD.jpg",
    "enhanced_image_url": "/api/v1/storage/enhanced/scr_22a7f8_OD_enhanced.jpg",
    "storage_provider": "LOCAL_STORAGE_PROVIDER",
    "iqa_status": "BORDERLINE",
    "metrics": {
      "sharpness_score": 105.1,
      "illumination_score": 45.3,
      "vessel_contrast_score": 0.42
    },
    "actionable_feedback": "Image has sub-optimal illumination. Automatic CLAHE and Ben Graham contrast enhancement applied. Proceeding with enhanced image."
  },
  "error": null,
  "timestamp": "2026-10-13T10:32:00Z"
}
```

- **Response `422 Unprocessable Entity` (Quality: REJECT):**
```json
{
  "success": false,
  "data": {
    "iqa_status": "REJECT",
    "metrics": {
      "sharpness_score": 38.6,
      "illumination_score": 19.4,
      "vessel_contrast_score": 0.18
    },
    "issues": ["MOTION_BLUR", "UNDEREXPOSURE"],
    "actionable_feedback": "Image too dark and blurry: increase camera illumination dial to Level 3, hold camera steady, and recapture."
  },
  "error": {
    "code": "IQA_REJECTED",
    "message": "Image quality below diagnostic threshold. Recapture required."
  },
  "timestamp": "2026-10-13T10:32:00Z"
}
```

### 4.3 Trigger DR Grading & Explainability
- **Endpoint:** `POST /screenings/{id}/analyze`
- **Access:** `PHC_WORKER`
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "screening_id": "scr_22a7f8",
    "model_version": "RetinaSahayak-EfficientNet-v2.1",
    "inference_engine": "MOCK_INFERENCE_SERVICE",
    "predicted_grade": 2,
    "grade_name": "Moderate Non-Proliferative Diabetic Retinopathy (NPDR)",
    "confidence_score": 0.874,
    "class_probabilities": {
      "grade_0_no_dr": 0.012,
      "grade_1_mild": 0.082,
      "grade_2_moderate": 0.874,
      "grade_3_severe": 0.028,
      "grade_4_pdr": 0.004
    },
    "is_referable": true,
    "is_uncertain": false,
    "triage_urgency": "ROUTINE",
    "dme_risk": {
      "level": "MILD",
      "exudates_near_macula": false
    },
    "lesion_evidence": {
      "microaneurysms_detected": true,
      "blot_hemorrhages_detected": true,
      "hard_exudates_detected": false,
      "neovascularization_detected": false,
      "suspicious_quadrants": ["SUPERIOR_TEMPORAL", "INFERIOR_TEMPORAL"]
    },
    "clinical_explanation": "The model highlights suspicious microaneurysm-like and hemorrhage-like regions in the posterior retina, consistent with Moderate NPDR.",
    "recommended_action": "Refer to ophthalmologist for confirmatory tele-examination within 30 days.",
    "explainability": {
      "heatmap_url": "/api/v1/storage/heatmaps/scr_22a7f8_gradcam.png",
      "overlay_url": "/api/v1/storage/overlays/scr_22a7f8_overlay.png",
      "method": "Grad-CAM++"
    },
    "referral_id": "ref_91b402",
    "referral_status": "PENDING_DOCTOR_REVIEW"
  },
  "error": null,
  "timestamp": "2026-10-13T10:32:45Z"
}
```

### 4.4 Offline Batch Sync Endpoint
- **Endpoint:** `POST /screenings/offline-batch-sync`
- **Access:** `PHC_WORKER`
- **Request Body:** Array of offline screening encounters and base64 encoded images cached in `IndexedDB`.
- **Response `200 OK`:** Batch sync status with array of created screening IDs.

---

## 5. Tele-Ophthalmology Cockpit & Doctor Review Endpoints

### 5.1 Prioritized Referral Queue
- **Endpoint:** `GET /referrals?priority=ALL&status=PENDING&page=1&limit=20`
- **Access:** `OPHTHALMOLOGIST`, `ADMIN`
- **Response `200 OK`:** Sorted list of referrals with emergency/urgent cases prioritized at the top.

### 5.2 Submit Doctor Decision (Human-in-the-Loop)
- **Endpoint:** `POST /reviews`
- **Access:** `OPHTHALMOLOGIST`
- **Request Body:**
```json
{
  "screening_id": "scr_22a7f8",
  "decision_type": "AGREE_WITH_AI",
  "confirmed_grade": 2,
  "override_rationale": null,
  "clinical_status": "REFERRED_TERTIARY",
  "clinical_notes": "Confirmed Moderate NPDR. Scattered blot hemorrhages visible in temporal arcade. Patient referred to district eye center for dilated indirect ophthalmoscopy. Recommend glycemic control.",
  "doctor_digital_signature": "SHA256:d892ef...Dr.RajeshVerma"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "review_id": "rev_7718e2",
    "screening_id": "scr_22a7f8",
    "status": "VERIFIED_BY_DOCTOR",
    "reviewed_at": "2026-10-13T10:35:00Z",
    "reviewer_name": "Dr. Rajesh Verma, MD",
    "concordance": true
  },
  "error": null,
  "timestamp": "2026-10-13T10:35:00Z"
}
```

---

## 6. Report Generation Endpoints

### 6.1 Download Bilingual PDF Medical Report
- **Endpoint:** `GET /screenings/{id}/report/pdf`
- **Access:** Authenticated
- **Response `200 OK`:** Streams binary `application/pdf` containing:
  - Anonymized Patient ID, PHC location, date.
  - Original and enhanced fundus images + Grad-CAM++ overlay.
  - Quality score, predicted grade, confidence, uncertainty status.
  - Vernacular summary (Hindi + English) with pictorial guidance.
  - Tele-consultation verification QR code and CDSS disclaimer.

---

## 7. Public Health Analytics & 100k District Simulation

### 7.1 Analytics Overview
- **Endpoint:** `GET /admin/analytics/overview`
- **Access:** `ADMIN`
- **Response `200 OK`:** KPI metrics: Total screenings, Good/Borderline/Reject counts, DR grade distribution, Referable vs Non-referable counts, Uncertain cases, Pending vs Reviewed referrals.

### 7.2 Run District Deployment Simulation
- **Endpoint:** `POST /simulation/district-run`
- **Access:** `ADMIN`
- **Request Body:**
```json
{
  "num_phcs": 50,
  "patients_per_phc_per_day": 8,
  "poor_quality_percent": 15.0,
  "borderline_quality_percent": 20.0,
  "internet_bandwidth_mbps": 4.0,
  "cloud_inference_latency_ms": 320,
  "local_inference_latency_ms": 110,
  "num_ophthalmologists": 3,
  "avg_doctor_review_time_mins": 4.0,
  "referral_rate_percent": 28.0
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "simulation_name": "Varanasi District 100k Screening Model",
    "daily_image_volume": 400,
    "annual_patient_capacity": 104000,
    "images_rejected_daily": 60,
    "images_enhanced_daily": 80,
    "images_graded_daily": 340,
    "referrals_generated_daily": 95,
    "ophthalmologist_daily_capacity": 135,
    "referral_queue_backlog": 0,
    "avg_patient_wait_time_hours": 3.2,
    "cloud_storage_gb_per_month": 42.5,
    "daily_bandwidth_mb": 1820.0,
    "system_health": "OPTIMAL_SUSTAINABLE"
  },
  "error": null,
  "timestamp": "2026-10-13T10:36:00Z"
}
```

---

## 8. Provider Status & System Health Endpoint

### 8.1 Provider Telemetry
- **Endpoint:** `GET /system/provider-status`
- **Access:** Public
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "app_name": "RetinaSahayak",
    "version": "1.0.0-SIH2026",
    "environment": "LOCAL_OFFLINE_READY",
    "storage_provider": "LOCAL_STORAGE_PROVIDER",
    "database_provider": "SQLITE_LOCAL",
    "inference_engine": "MOCK_INFERENCE_SERVICE",
    "gcp_connected": false,
    "uptime_seconds": 1840
  },
  "error": null,
  "timestamp": "2026-10-13T10:36:30Z"
}
```
