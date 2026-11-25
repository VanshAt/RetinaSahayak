# PHASE 1 VERIFICATION & QUICKSTART GUIDE
RetinaSahayak — Community-Level AI Diabetic Retinopathy Screening System

## 1. How to Run Tests
Activate the Python virtual environment and run the complete automated test suite:

```powershell
# In PowerShell (Windows):
.\.venv\Scripts\pytest -v

# Or using python -m pytest:
.\.venv\Scripts\python -m pytest -v
```

All 34 test cases will execute and validate:
- Authentication & JWT token refresh
- RBAC and PHC worker health center isolation
- Patient registration (zero direct PII)
- Retinal image upload and validation (format & <= 15MB limit)
- Deterministic 7-factor IQA gating (rejection & borderline handling)
- CLAHE and Ben Graham retinal enhancement
- EfficientNet model & calibrated deterministic mock inference
- Predictive uncertainty routing (< 0.65 threshold & high entropy)
- Clinical referral classification (Grade 0-1 non-referable, Grade 2-4 referable)
- Grad-CAM++ activation maps & candidate lesion bounding boxes
- Tele-ophthalmology triage queues, review sign-offs & escalations
- Tamper-evident cryptographic audit logs with SHA-256 signatures
- Bilingual medical report PDF streaming with QR codes
- Local and cloud storage provider fallbacks

---

## 2. How to Start the Server

### Local Development (Direct)
```powershell
# Set environment variables (or rely on .env defaults)
$env:ENVIRONMENT="local"
$env:USE_MOCK_INFERENCE="True"
$env:STORAGE_PROVIDER="LOCAL"

# Start Uvicorn development server
.\.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI Swagger UI is available at:
`http://127.0.0.1:8000/docs`

### Starting via Docker Compose (Zero Cloud Credentials Required)
RetinaSahayak is fully containerized to run in standalone/offline mode with zero GCP credentials required:

```powershell
docker compose up --build
```

Health check verifies `http://localhost:8000/api/v1/health`.

---

## 3. Demo Credentials

The database automatically seeds with default test credentials for all primary personas:

| Role | Email | Password | Facility / Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@retinasahayak.in` | `AdminDemo123!` | District Health Authority, Varanasi |
| **PHC Worker** | `worker.ramnagar@retinasahayak.in` | `WorkerDemo123!` | Ramnagar Primary Health Centre (PHC-UP-VNS-01) |
| **PHC Worker** | `worker.chiraigaon@retinasahayak.in` | `WorkerDemo123!` | Chiraigaon Community Health Centre (CHC-UP-VNS-02) |
| **Ophthalmologist** | `dr.verma@retinasahayak.in` | `DoctorDemo123!` | Reg: MCI-UP-48821 (Tertiary Eye Hospital) |
| **Ophthalmologist** | `dr.sharma@retinasahayak.in` | `DoctorDemo123!` | Reg: MCI-UP-52190 (Vitreo-Retina Specialist) |

---

## 4. Sample curl Commands & Expected Responses

### Step 1: Health Worker Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "worker.ramnagar@retinasahayak.in", "password": "WorkerDemo123!"}'
```

**Expected Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "4a5335f9-bfd5-4aac-8d10-adcf3ab19f73",
      "email": "worker.ramnagar@retinasahayak.in",
      "full_name": "Smt. Sunita Devi (ANM)",
      "role": "PHC_WORKER",
      "health_center_id": "hc_ramnagar_01",
      "health_center_name": "Ramnagar Primary Health Centre"
    }
  }
}
```

---

### Step 2: Register Anonymized Patient (Zero Direct PII)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/patients \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "age_group": "51-65",
    "gender": "FEMALE",
    "diabetes_duration_years": 9,
    "known_hypertension": true
  }'
```

**Expected Response (`201 Created`):**
```json
{
  "success": true,
  "data": {
    "id": "3be2931a-8e2b-45f8-8ef9-8d1aa20ec871",
    "patient_code": "PAT-VNS-7521",
    "age_group": "51-65",
    "gender": "FEMALE",
    "diabetes_duration_years": 9,
    "known_hypertension": true,
    "phc_location": "Ramnagar Primary Health Centre",
    "health_center_id": "hc_ramnagar_01",
    "registered_at": "2026-10-14T17:30:00Z"
  }
}
```

---

### Step 3: Initiate Screening Encounter
```bash
curl -X POST http://127.0.0.1:8000/api/v1/screenings \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "3be2931a-8e2b-45f8-8ef9-8d1aa20ec871",
    "eye_side": "OD",
    "camera_device_model": "Forus 3nethra Classic",
    "dilation_status": "UNDILATED"
  }'
```

**Expected Response (`201 Created`):**
```json
{
  "success": true,
  "data": {
    "id": "78201a08-251c-4395-8854-325dbb277d33",
    "patient_id": "3be2931a-8e2b-45f8-8ef9-8d1aa20ec871",
    "patient_code": "PAT-VNS-7521",
    "eye_side": "OD",
    "status": "INITIALIZED"
  }
}
```

---

### Step 4: Upload Fundus Photograph (Triggering IQA Gate)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/screenings/78201a08-251c-4395-8854-325dbb277d33/upload-fundus \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@sample_fundus.jpg"
```

**Expected Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "image_id": "f5e921d7-210f-4886-9a25-e514f7623910",
    "screening_id": "78201a08-251c-4395-8854-325dbb277d33",
    "original_image_url": "/api/v1/storage/raw_images/78201a08-251c-4395-8854-325dbb277d33_OD.jpg",
    "enhanced_image_url": null,
    "storage_provider": "LOCAL_STORAGE_PROVIDER",
    "iqa_result": {
      "iqa_status": "GOOD",
      "is_acceptable": true,
      "metrics": {
        "sharpness_score": 142.3,
        "illumination_score": 88.5,
        "vessel_contrast_score": 0.52
      },
      "issues": [],
      "actionable_feedback": "Image quality is optimal for AI diagnostic grading."
    }
  }
}
```

---

### Step 5: Execute AI Diagnosis & Referral Triage
```bash
curl -X POST http://127.0.0.1:8000/api/v1/screenings/78201a08-251c-4395-8854-325dbb277d33/analyze \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "screening_id": "78201a08-251c-4395-8854-325dbb277d33",
    "model_version": "RetinaSahayak-EfficientNet-v2.1",
    "inference_engine": "MOCK_INFERENCE_SERVICE",
    "inference_time": 0.082,
    "quality_status": "GOOD",
    "quality_score": 95.0,
    "predicted_grade": 2,
    "grade_label": "Grade 2: Moderate Non-Proliferative Diabetic Retinopathy (NPDR)",
    "class_probabilities": {
      "grade_0_no_dr": 0.012,
      "grade_1_mild": 0.082,
      "grade_2_moderate": 0.874,
      "grade_3_severe": 0.028,
      "grade_4_pdr": 0.004
    },
    "confidence": 0.874,
    "uncertainty_status": "CERTAIN",
    "referable_status": "REFERABLE",
    "is_referable": true,
    "is_uncertain": false,
    "triage_urgency": "ROUTINE",
    "disclaimer": "Presumptive AI Screening Observation. Not an autonomous medical diagnosis. Must be reviewed and verified by a licensed ophthalmologist before any clinical treatment."
  }
}
```

---

## 5. Security & Multi-Tenant Isolation Verification
- **Cross-Worker / Cross-PHC Access Rejection**:
  A worker assigned to Ramnagar PHC receives `HTTP 403 Forbidden` if attempting to view or screen patients or screenings created by Chiraigaon PHC.
- **File Validation**:
  - Unsupported file types (`.txt`, `.sh`, `.exe`, `.pdf`) return `HTTP 400 Bad Request` with `Unsupported file format`.
  - Files over 15 MB return `HTTP 400 Bad Request` with `File size exceeds 15MB maximum limit.`.
- **Audit Logs**:
  All transactions log the `user_id`, `user_role`, `action`, `resource_id`, `timestamp`, and `status`, protected with a SHA-256 tamper-evident payload hash.
