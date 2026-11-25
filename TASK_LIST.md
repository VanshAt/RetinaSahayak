# RetinaSahayak: Work Breakdown Structure & Task List

**Problem Statement ID:** SIH26038 | **Project:** RetinaSahayak  
**Current Milestone:** Phase 0 — Planning & Architecture Review  
**Status:** Pending User Approval before starting Phase 1

---

## Phase Overview & Task Distribution

| Phase | Description | Tasks | P0 (Critical) | P1 (High) | P2 (Medium) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Phase 0** | Planning & Architecture Artifacts (10 Documents) | 10 | 10 | 0 | 0 |
| **Phase 1** | Project Scaffold, Auth, Database, Storage Abstraction | 8 | 6 | 2 | 0 |
| **Phase 2** | Image Quality Assessment (IQA), Enhancement & ML Pipeline | 8 | 6 | 2 | 0 |
| **Phase 3** | Explainability (Grad-CAM++) & Candidate Lesion Engine | 6 | 5 | 1 | 0 |
| **Phase 4** | Referral Triage, Tele-Ophthalmology & Audit Trail | 6 | 5 | 1 | 0 |
| **Phase 5** | Bilingual PDF Report Engine (ReportLab) | 5 | 4 | 1 | 0 |
| **Phase 6** | Frontend SPA (React + TypeScript + Tailwind) - 3 Roles | 11 | 8 | 3 | 0 |
| **Phase 7** | Google Cloud Services Integration & District Simulation | 6 | 4 | 2 | 0 |
| **Phase 8** | MathWorks Simulink / Stateflow Model & ONNX Export | 5 | 3 | 2 | 0 |
| **Phase 9** | Demo Dataset, Automated Tests, Pitch & Documentation | 9 | 7 | 2 | 0 |
| **TOTAL** | **Full System Delivery** | **74** | **58** | **16** | **0** |

---

## Phase 0: Planning & Architectural Artifacts (CURRENT)

- [x] **TASK-001 [P0]**: Author `IMPLEMENTATION_PLAN.md` with system architecture, dual-mode GCP strategy, and judging criteria alignment.
- [x] **TASK-002 [P0]**: Author `TASK_LIST.md` with full WBS, priorities, dependencies, and definitions of done.
- [x] **TASK-003 [P0]**: Author `FOLDER_STRUCTURE.md` detailing monorepo directory layout matching `/backend/app/...` structure.
- [x] **TASK-004 [P0]**: Author `API_SPECIFICATION.md` defining OpenAPI 3.1 endpoints, request/response schemas, and provider telemetry.
- [x] **TASK-005 [P0]**: Author `DATABASE_SCHEMA.md` detailing anonymized patient entities, relational models, and provider abstraction.
- [x] **TASK-006 [P0]**: Author `ML_PIPELINE_PLAN.md` with 3-tier IQA (GOOD/BORDERLINE/REJECT), CLAHE enhancement, EfficientNet-B4, and Grad-CAM++.
- [x] **TASK-007 [P0]**: Author `GOOGLE_CLOUD_ARCHITECTURE.md` detailing Cloud Run, GCS, Firestore/Cloud SQL, Vertex AI, Healthcare API, and local fallbacks.
- [x] **TASK-008 [P0]**: Author `UI_SCREEN_PLAN.md` with green/yellow/red color tokens, simplified health-worker wizard, doctor cockpit, and district simulation UI.
- [x] **TASK-009 [P0]**: Author `TEAM_WORKFLOW.md` detailing 4-member Git branching, task division, and daily hackathon timeline.
- [x] **TASK-010 [P0]**: Author `RISKS_AND_ASSUMPTIONS.md` covering clinical safety, offline-first design, and cloud/local dual-mode risks.

---

## Phase 1: Project Scaffold, Backend Setup, Auth & Storage Abstraction

- [x] **TASK-101 [P0]**: Initialize Python FastAPI backend inside `backend/app/` with pinned `requirements.txt` and `.env.example`.
- [x] **TASK-102 [P0]**: Implement Storage Provider Abstraction (`backend/app/services/storage/`):
  - Interface: `StorageProvider` (`save_file`, `get_file`, `get_url`, `delete_file`).
  - Provider 1: `LocalStorageProvider` (saves to `backend/storage/`).
  - Provider 2: `GCSStorageProvider` (Google Cloud Storage bucket with service account / ADC).
  - Factory: Dynamically instantiates provider based on `STORAGE_PROVIDER` environment variable.
- [x] **TASK-103 [P0]**: Implement Database Provider Abstraction (`backend/app/core/database.py`):
  - Local mode: SQLite 3 engine via SQLAlchemy 2.0 with WAL mode.
  - Cloud mode: Cloud SQL PostgreSQL / Firestore connection ready.
- [x] **TASK-104 [P0]**: Implement SQLAlchemy ORM Models:
  - `User`, `HealthCenter`, `Patient` (anonymized), `Screening`, `FundusImage`, `AIAnalysis`, `ExplainabilityMap`, `Referral`, `ClinicalReview`, `AuditLog`.
- [x] **TASK-105 [P0]**: Implement JWT Authentication & RBAC Guard (`backend/app/core/security.py`):
  - Roles: `PHC_WORKER`, `OPHTHALMOLOGIST`, `ADMIN`.
  - Token creation, password hashing with bcrypt, role-verification dependencies.
- [x] **TASK-106 [P0]**: Implement Database Seeder (`backend/app/db/seed.py`) with 5 demo accounts:
  - 1 Admin: `admin@retinasahayak.in`
  - 2 Health Workers: `worker.ramnagar@retinasahayak.in`, `worker.chiraigaon@retinasahayak.in`
  - 2 Ophthalmologists: `dr.verma@retinasahayak.in`, `dr.sharma@retinasahayak.in`
- [x] **TASK-107 [P1]**: Implement Anonymized Patient Management API (`backend/app/api/patients.py`):
  - Zero PII compliance (Patient Code, Age Group, Sex, Diabetes Duration, PHC Location).
- [x] **TASK-108 [P1]**: Implement Offline-Sync Endpoint (`POST /api/v1/screenings/offline-batch-sync`).

---

## Phase 2: Computer Vision, IQA Gate, Enhancement & ML Pipeline

- [x] **TASK-201 [P0]**: Implement Image Quality Assessment Gate (`backend/app/ml/iqa.py`):
  - Laplacian variance focus check ($\sigma^2 \ge 100$).
  - Mean luminance and saturation histogram check ($28 \le \mu_L \le 230$).
  - Green-channel vessel contrast variance check ($\ge 0.35$).
  - Classifies into **`GOOD`**, **`BORDERLINE`**, or **`REJECT`**.
  - Actionable recapture feedback generator for `REJECT` status.
- [x] **TASK-202 [P0]**: Implement Borderline Image Enhancer (`backend/app/ml/enhancer.py`):
  - Contrast Limited Adaptive Histogram Equalization (CLAHE) on Green channel.
  - Ben Graham local contrast normalization ($4I - 4\text{Gauss}(I) + 128$).
  - Denoising filter (Bilateral or Gaussian).
  - Saves both original and enhanced assets.
- [x] **TASK-203 [P0]**: Implement Circular ROI Auto-Cropping (`backend/app/ml/preprocess.py`):
  - Automatic circular mask segmentation, black margin removal, and 512x512 tensor resizing.
- [x] **TASK-204 [P0]**: Implement Deep Learning DR Classifier (`backend/app/ml/classifier.py`):
  - EfficientNet-B4 backbone pre-trained on APTOS 2019 / EyePACS.
  - Outputs 5-class ICDR softmax probabilities (Grade 0 to 4).
  - Returns predicted grade, confidence, and binary referable flag ($\text{Grade} \ge 2$).
- [x] **TASK-205 [P0]**: Implement High-Fidelity `MOCK_INFERENCE` Fallback (`backend/app/ml/mock_inference.py`):
  - Deterministic, clinically realistic predictions for live offline hackathon demos when GPU/weights are absent.
  - Seamless toggle via `USE_MOCK_INFERENCE=true/false`.
- [x] **TASK-206 [P1]**: Implement Uncertainty & Entropy Estimator (`backend/app/ml/uncertainty.py`):
  - Computes predictive entropy and softmax probability margin; flags cases with $\text{Confidence} < 0.65$ as **`UNCERTAIN`**.
- [x] **TASK-207 [P1]**: Implement Macular Edema (DME) Risk Assessor (`backend/app/ml/dme_detector.py`):
  - Identifies hard exudate density within 1 disc diameter of the fovea.
- [x] **TASK-208 [P0]**: Implement End-to-End Inference Orchestration Service (`backend/app/services/inference_service.py`).

---

## Phase 3: Explainability Engine (Grad-CAM++) & Candidate Lesions

- [x] **TASK-301 [P0]**: Implement PyTorch Grad-CAM++ Hook (`backend/app/ml/gradcam.py`):
  - Computes weighted second- and third-order partial derivatives on the final convolutional layer.
  - Produces normalized $512 \times 512$ activation heatmap.
- [x] **TASK-302 [P0]**: Implement Heatmap Overlay Generator (`backend/app/ml/visualizer.py`):
  - Blends Grad-CAM++ heatmap with original and enhanced fundus images (40% alpha).
- [x] **TASK-303 [P0]**: Implement Candidate Lesion Region Extractor (`backend/app/ml/lesions.py`):
  - Detects microaneurysms, blot hemorrhages, and hard exudates; computes quadrant bounding boxes.
- [x] **TASK-304 [P0]**: Implement Plain-Language Clinical Rationale Generator (`backend/app/services/rationale_service.py`):
  - Generates clear explanation strings without claiming autonomous diagnostic certainty.
- [x] **TASK-305 [P1]**: Implement Explainability REST Endpoints (`GET /api/v1/screenings/{id}/explainability`).
- [x] **TASK-306 [P0]**: Unit test Grad-CAM generation and lesion localization on test fundus samples.

---

## Phase 4: Referral Triage, Tele-Ophthalmology & Audit Trail

- [x] **TASK-401 [P0]**: Implement Rule-Based Referral Triage Engine (`backend/app/services/referral_service.py`):
  - Routes Grade 2, 3, 4, or `UNCERTAIN` cases into the doctor queue.
  - Sets clinical priority: `EMERGENCY` (Grade 4 / DME), `URGENT` (Grade 3), `ROUTINE` (Grade 2), `UNCERTAIN_REVIEW` (Low confidence).
- [x] **TASK-402 [P0]**: Implement Doctor Referral Queue API (`GET /api/v1/referrals`):
  - Filtering by priority, status (`PENDING`, `IN_REVIEW`, `VERIFIED`), and PHC location.
- [x] **TASK-403 [P0]**: Implement Doctor Clinical Review & Sign-Off API (`POST /api/v1/reviews`):
  - Options: Agree with AI, Modify grade, Mark non-referable, Mark referable, Request repeat imaging, Mark follow-up required, Close case.
  - Captures clinical notes, recommended action, and cryptographic digital signature hash.
- [x] **TASK-404 [P1]**: Implement Doctor Case Escalation Endpoint (`POST /api/v1/referrals/{id}/escalate`).
- [x] **TASK-405 [P0]**: Implement Tamper-Evident SHA-256 Audit Logger (`backend/app/services/audit_service.py`).
- [x] **TASK-406 [P1]**: Implement Audit Log Inspection Endpoint (`GET /api/v1/admin/audit-logs`).

---

## Phase 5: Bilingual Medical PDF Report Engine (ReportLab)

- [x] **TASK-501 [P0]**: Configure ReportLab PDF Layout Engine (`backend/app/reports/pdf_generator.py`):
  - Standard 2-page A4 clinical format with professional header, patient demographics, and PHC details.
- [x] **TASK-502 [P0]**: Embed High-Resolution Retinal Images & Overlays:
  - Original fundus, enhanced image (if borderline), and Grad-CAM++ heatmap overlay.
- [x] **TASK-503 [P0]**: Format Diagnostic Findings & Quality Status:
  - IQA outcome badge, ICDR grade badge, confidence score, uncertainty status, lesion breakdown.
- [x] **TASK-504 [P0]**: Implement Vernacular Patient Guidance & Tele-Referral QR Code:
  - Bilingual summary (English + Hindi), pictorial indicators, dynamic QR code linking to verification URL, and CDSS legal disclaimer.
- [x] **TASK-505 [P1]**: Implement PDF Download & Streaming Endpoint (`GET /api/v1/screenings/{id}/report/pdf`).

---

## Phase 6: Frontend SPA (React + TypeScript + Tailwind) - 3 Roles

- [x] **TASK-601 [P0]**: Initialize React 18 + TypeScript + Vite project inside `frontend/` with Tailwind CSS and Lucide icons.
- [x] **TASK-602 [P0]**: Implement Global Auth Context & Role Guards (`frontend/src/context/AuthContext.tsx`):
  - Login page with 1-click role demo switcher (Admin, Worker, Doctor).
- [x] **TASK-603 [P0]**: Build PHC Health Worker Workspace (`/worker`):
  - Ultra-simple 3-step wizard with minimal text and large buttons.
  - Step 1: Anonymized patient entry (zero PII friction).
  - Step 2: Fundus image dropzone with instant file validation.
  - Step 3: Interactive IQA feedback alert (`GOOD`, `BORDERLINE`, `REJECT`) with actionable retake guidance.
- [x] **TASK-604 [P0]**: Build Worker Screening Result View:
  - Traffic-light color coding (Green: Normal, Yellow: Borderline/Uncertain, Red: Referable).
  - Interactive Before/After split slider (Original vs Grad-CAM++ overlay).
  - One-click "Download Bilingual PDF" and "Send for Doctor Review" actions.
- [x] **TASK-605 [P0]**: Build Tele-Ophthalmology Cockpit (`/doctor`):
  - Prioritized referral queue sorted by clinical severity.
  - Deep-zoom diagnostic viewer with Pan, Zoom (up to 400%), and Reset.
  - Filter toggles: Natural Color, Red-Free Green, CLAHE Enhanced.
  - Grad-CAM heatmap opacity slider (0% to 100%).
  - Doctor decision form: Agree, Modify, Request retake, Treatment advice, Digital sign-off.
- [x] **TASK-606 [P0]**: Build Public Health Admin Analytics Dashboard (`/admin`):
  - KPI metric cards: Total Screenings, Referable Rate %, Average Turnaround Time.
  - DR Grade distribution charts, IQA pass/rejection breakdown, and PHC volume breakdown.
  - AI-Doctor concordance matrix (Cohen's Kappa).
- [x] **TASK-607 [P1]**: Build Offline-First Upload Queue (`frontend/src/services/offlineQueue.ts`):
  - IndexedDB storage for offline patient screenings with auto-sync indicator.
- [x] **TASK-608 [P1]**: Ensure Responsive Mobile/Tablet Layout and High Contrast Accessibility (WCAG 2.1 AA).
- [x] **TASK-609 [P1]**: Add Loading Skeletons, Empty States, and Toast Alerts.
- [x] **TASK-610 [P0]**: Build and verify frontend production bundle (`npm run build`).

---

## Phase 7: Google Cloud Architecture Integration & District Simulation

- [ ] **TASK-701 [P0]**: Implement Google Cloud Run deployment configuration (`Dockerfile`, `docker-compose.yml`, `cloudrun.yaml`).
- [ ] **TASK-702 [P0]**: Implement GCS Storage Provider (`backend/app/services/storage/gcs_provider.py`) with local disk fallback.
- [ ] **TASK-703 [P1]**: Implement Google Cloud Logging & Secret Manager connectors.
- [ ] **TASK-704 [P1]**: Document Google Cloud Healthcare API (DICOM/FHIR) adapter blueprint.
- [ ] **TASK-705 [P0]**: Build 100,000-Patient District Deployment Simulator (`backend/app/services/simulation_service.py`):
  - Models rural district: PHC count, patients/day, poor quality %, latency, doctor capacity.
  - Calculates daily volume, rejected images, enhanced images, referrals generated, backlog, patient wait times, cloud storage, and bandwidth.
- [ ] **TASK-706 [P0]**: Build District Simulation UI Dashboard in Admin portal with interactive sliders and real-time metric updates.

---

## Phase 8: MathWorks Simulink / Stateflow Model & ONNX Export

- [ ] **TASK-801 [P0]**: Author Simulink Model Specification Document (`simulink/README_SIMULINK.md`).
- [ ] **TASK-802 [P0]**: Author MATLAB Initialization Script (`simulink/init_retinasahayak_sim.m`) with camera, IQA, and triage parameters.
- [ ] **TASK-803 [P0]**: Author Stateflow Edge Triage Controller Specification (`simulink/stateflow_triage_spec.m`).
- [ ] **TASK-804 [P1]**: Implement PyTorch-to-ONNX Exporter (`backend/app/ml/export_onnx.py`).
- [ ] **TASK-805 [P1]**: Author MATLAB Deep Learning Toolbox ONNX Import & Verification Script (`simulink/import_onnx_verify.m`).

---

## Phase 9: Demo Dataset, Automated Tests, Pitch & Documentation

- [ ] **TASK-901 [P0]**: Assemble 12-Image Golden Test Dataset (`demo/sample_images/`):
  - Grade 0 (Normal), Grade 1 (Mild), Grade 2 (Moderate), Grade 3 (Severe), Grade 4 (PDR), Blurry Reject, Dark Borderline, Low-confidence Uncertain.
- [ ] **TASK-902 [P0]**: Create Automated Backend Test Suite (`backend/tests/`):
  - Test IQA gate (Good/Borderline/Reject), CLAHE enhancement, ML grading, Grad-CAM, PDF generation, and doctor sign-off.
- [ ] **TASK-903 [P0]**: Author Master Documentation Suite:
  - `README.md`, `ARCHITECTURE.md`, `MODEL_CARD.md`, `API_DOCUMENTATION.md`, `DEPLOYMENT.md`, `GOOGLE_CLOUD_INTEGRATION.md`.
- [ ] **TASK-904 [P0]**: Author Pitch & Presentation Suite:
  - `PITCH.md` (6-slide executive deck + 12-slide comprehensive deck + slide-by-slide visual plan).
  - `DEMO_SCRIPT.md` (5-minute live demo script + 3-minute 4-speaker pitch script + elevator pitch).
  - `JUDGE_QA.md` (Top 15 judge questions and defensible answers).
- [ ] **TASK-905 [P1]**: Author GitHub Actions CI Pipeline (`.github/workflows/ci.yml`).
- [ ] **TASK-906 [P0]**: End-to-end live testing, screenshot capture, and launch verification.
