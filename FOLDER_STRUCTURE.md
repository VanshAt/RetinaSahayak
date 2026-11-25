# RetinaSahayak: Project Folder Structure & Monorepo Architecture

**Problem Statement ID:** SIH26038 | **Project:** RetinaSahayak  
**Architecture Style:** Modular Monorepo with Clean Layered Backend (`/backend/app`), Modern React Frontend (`/frontend/src`), ML Training & Evaluation (`/ml`), Simulink Hardware Co-Design (`/simulink`), and Deployment Manifests (`/deployment`).

---

## 1. Directory Tree Map

```
d:/RBU/RetinaSahayak/
│
├── .gitignore                          # Git exclusions (venv, node_modules, weights, storage)
├── .env.example                        # Environment variables template with local/GCP modes
├── README.md                           # Master setup, quickstart, and SIH pitch overview
├── ARCHITECTURE.md                     # System architecture & data flow diagrams
├── IMPLEMENTATION_PLAN.md              # Master technical implementation roadmap
├── TASK_LIST.md                        # Work breakdown structure and task tracking
├── FOLDER_STRUCTURE.md                 # Monorepo directory map (This file)
├── API_SPECIFICATION.md                # OpenAPI 3.1 REST API contract
├── DATABASE_SCHEMA.md                  # Relational schema, SQLAlchemy models, ER diagram
├── ML_PIPELINE_PLAN.md                 # Deep learning, IQA, and Grad-CAM++ algorithms
├── GOOGLE_CLOUD_ARCHITECTURE.md        # Google Cloud services & local fallback design
├── UI_SCREEN_PLAN.md                   # UI screens, wireframes, and design system tokens
├── TEAM_WORKFLOW.md                    # Git branching, task division, and daily timeline
├── RISKS_AND_ASSUMPTIONS.md            # Clinical, hardware, and operational risk matrix
├── MODEL_CARD.md                       # Intended use, limitations, datasets, and ethical metrics
├── PITCH.md                            # 6-slide & 12-slide SIH presentation deck outlines
├── DEMO_SCRIPT.md                      # 5-minute judge demo & 3-minute pitch scripts
├── JUDGE_QA.md                         # Likely judge technical & clinical Q&A cheat sheet
├── DEPLOYMENT.md                       # Local, Docker, and Google Cloud Run deployment guide
├── GOOGLE_CLOUD_INTEGRATION.md         # Detailed GCP integration & fallback instructions
├── docker-compose.yml                  # Multi-container orchestration (Backend + Frontend)
├── Dockerfile                          # Production container build for Google Cloud Run
│
├── backend/                            # Python FastAPI Backend Service
│   ├── requirements.txt                # Pinned dependencies (FastAPI, PyTorch, ReportLab, etc.)
│   ├── main.py                         # ASGI entry point and route mounter
│   │
│   ├── app/                            # Core application package
│   │   ├── __init__.py
│   │   │
│   │   ├── core/                       # Global application configuration & security
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic Settings (Local vs GCP provider flags)
│   │   │   ├── security.py             # JWT token creation, bcrypt hashing, RBAC guards
│   │   │   ├── logging.py              # Structured logging & Google Cloud Logging connector
│   │   │   └── database.py             # SQLAlchemy engine & session factory (SQLite / Cloud SQL)
│   │   │
│   │   ├── models/                     # SQLAlchemy 2.0 ORM database entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # Users (Health Worker, Doctor, Admin)
│   │   │   ├── health_center.py        # Rural PHC facilities
│   │   │   ├── patient.py              # Anonymized patient demographics (No direct PII)
│   │   │   ├── screening.py            # Screening sessions & status tracking
│   │   │   ├── fundus_image.py         # Original & enhanced image metadata + IQA scores
│   │   │   ├── ai_analysis.py          # 5-grade ICDR predictions, confidence, uncertainty
│   │   │   ├── explainability_map.py   # Grad-CAM heatmap paths & candidate lesion data
│   │   │   ├── referral.py             # Tele-triage tickets & clinical priority
│   │   │   ├── clinical_review.py      # Ophthalmologist review, override & digital sign
│   │   │   └── audit_log.py            # Immutable tamper-evident security audit trail
│   │   │
│   │   ├── schemas/                    # Pydantic v2 Request & Response DTO schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py               # Standard API response envelope
│   │   │   ├── auth.py                 # Token & credential schemas
│   │   │   ├── patient.py              # Anonymized patient DTOs
│   │   │   ├── screening.py            # Screening session DTOs
│   │   │   ├── ml_result.py            # IQA, DR grading, and Grad-CAM result DTOs
│   │   │   ├── referral.py             # Referral ticket DTOs
│   │   │   ├── clinical_review.py      # Doctor review & endorsement schemas
│   │   │   ├── simulation.py           # District-scale deployment simulation DTOs
│   │   │   └── analytics.py            # Admin epidemiological telemetry DTOs
│   │   │
│   │   ├── services/                   # Business Logic & Provider Abstractions
│   │   │   ├── __init__.py
│   │   │   ├── storage/                # Storage Provider Abstraction Layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py             # StorageProvider interface
│   │   │   │   ├── local_provider.py   # Local disk storage implementation
│   │   │   │   ├── gcs_provider.py     # Google Cloud Storage bucket implementation
│   │   │   │   └── factory.py          # Storage provider factory (LOCAL vs GCS)
│   │   │   ├── patient_service.py      # Anonymized patient business rules
│   │   │   ├── screening_service.py    # Screening lifecycle orchestrator
│   │   │   ├── inference_service.py    # IQA -> Enhancement -> ML -> Grad-CAM pipeline
│   │   │   ├── referral_service.py     # Rule-based clinical triage engine
│   │   │   ├── review_service.py       # Doctor endorsement & concordance logic
│   │   │   ├── simulation_service.py   # 100k-patient district deployment simulator
│   │   │   ├── audit_service.py        # Cryptographic audit logging
│   │   │   └── analytics_service.py    # Public health telemetry aggregator
│   │   │
│   │   ├── ml/                         # Computer Vision & Deep Learning Algorithms
│   │   │   ├── __init__.py
│   │   │   ├── iqa.py                  # IQA Gate (GOOD / BORDERLINE / REJECT)
│   │   │   ├── enhancer.py             # Borderline image enhancement (CLAHE + Ben Graham)
│   │   │   ├── preprocess.py           # Circular ROI crop & tensor normalization
│   │   │   ├── classifier.py           # PyTorch EfficientNet-B4 ICDR classifier
│   │   │   ├── mock_inference.py       # High-fidelity deterministic mock fallback
│   │   │   ├── uncertainty.py          # Predictive entropy & confidence thresholding
│   │   │   ├── gradcam.py              # Grad-CAM++ gradient hooks
│   │   │   ├── visualizer.py           # Heatmap colormap & overlay blending
│   │   │   ├── lesions.py              # Candidate lesion region extractor & quadrant mapper
│   │   │   └── export_onnx.py          # Model exporter for MATLAB / Simulink
│   │   │
│   │   ├── api/                        # REST API Route Controllers
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                 # FastAPI dependency injection (DB, Current User, Role)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py           # Aggregated V1 API router
│   │   │       ├── auth.py             # Login, refresh, profile endpoints
│   │   │       ├── patients.py         # Anonymized patient CRUD
│   │   │       ├── screenings.py       # Image upload, IQA, and grading trigger
│   │   │       ├── explainability.py   # Grad-CAM maps & lesion coordinates
│   │   │       ├── referrals.py        # Doctor prioritized triage queue
│   │   │       ├── reviews.py          # Doctor clinical sign-off & override
│   │   │       ├── reports.py          # Bilingual PDF streaming
│   │   │       ├── simulation.py       # District deployment simulation endpoints
│   │   │       └── admin.py            # Analytics & audit logs
│   │   │
│   │   └── utils/                      # Helper utilities
│   │       ├── __init__.py
│   │       ├── image_utils.py          # Image format conversions & EXIF stripping
│   │       ├── validators.py           # File size & MIME type checkers
│   │       └── qr_generator.py         # QR code generator for PDF reports
│   │
│   ├── reports/                        # ReportLab PDF Generation Package
│   │   ├── __init__.py
│   │   ├── pdf_generator.py            # 2-Page bilingual medical report compiler
│   │   └── templates/                  # Report styling assets & clinical branding
│   │
│   ├── storage/                        # Local file storage (Git ignored)
│   │   ├── raw_images/                 # Uploaded fundus photographs
│   │   ├── enhanced/                   # Borderline enhanced fundus photos
│   │   ├── heatmaps/                   # Grad-CAM activation maps
│   │   ├── overlays/                   # Blended fundus + heatmap overlays
│   │   └── reports/                    # Compiled PDF reports
│   │
│   └── tests/                          # Automated backend test suite
│       ├── __init__.py
│       ├── conftest.py                 # Pytest fixtures and mock client
│       ├── test_auth.py                # Test JWT auth & RBAC guards
│       ├── test_iqa.py                 # Test Good/Borderline/Reject gate
│       ├── test_enhancement.py         # Test CLAHE & Ben Graham enhancement
│       ├── test_ml_pipeline.py         # Test DR classification & mock inference
│       ├── test_gradcam.py             # Test Grad-CAM++ hooks & overlay rendering
│       ├── test_referral_triage.py     # Test priority classification rules
│       ├── test_pdf_report.py          # Test ReportLab PDF byte generation
│       ├── test_simulation.py          # Test 100k-patient district simulation
│       └── test_storage_provider.py    # Test local vs GCS provider abstraction
│
├── frontend/                           # React 18 + TypeScript + Tailwind CSS Frontend
│   ├── package.json                    # Dependencies (React, Lucide, Tailwind, Axios)
│   ├── tsconfig.json                   # Strict TypeScript compiler options
│   ├── vite.config.ts                  # Vite build configuration & API proxy
│   ├── tailwind.config.js              # Clinical design tokens (Green/Yellow/Red spectrum)
│   ├── postcss.config.js               # PostCSS plugins
│   ├── index.html                      # HTML5 root with Inter font
│   │
│   └── src/                            # React application source code
│       ├── main.tsx                    # React root render
│       ├── App.tsx                     # Router and layout shell
│       ├── index.css                   # Tailwind imports & custom clinical styles
│       │
│       ├── api/                        # Axios API Client & Endpoints
│       │   ├── client.ts               # Axios instance with JWT interceptors
│       │   ├── authApi.ts              # Auth endpoints
│       │   ├── patientApi.ts           # Anonymized patient endpoints
│       │   ├── screeningApi.ts         # Screening & image endpoints
│       │   ├── reviewApi.ts            # Doctor review endpoints
│       │   ├── simulationApi.ts        # District simulation endpoints
│       │   └── adminApi.ts             # Analytics endpoints
│       │
│       ├── context/                    # React Context State
│       │   ├── AuthContext.tsx         # User authentication & active role state
│       │   └── ToastContext.tsx        # Toast alert notifications
│       │
│       ├── hooks/                      # Custom React Hooks
│       │   ├── useAuth.ts              # Authentication state hook
│       │   ├── useOfflineQueue.ts      # Offline-first upload queue manager
│       │   └── useImageZoom.ts         # Canvas pan and zoom controller
│       │
│       ├── services/                   # Client-side Services
│       │   └── offlineStorage.ts       # IndexedDB offline cache
│       │
│       ├── types/                      # TypeScript Interface Definitions
│       │   ├── auth.ts                 # User & Token types
│       │   ├── patient.ts              # Anonymized patient types
│       │   ├── screening.ts            # Screening, IQA, and ML types
│       │   ├── review.ts               # Referral & doctor decision types
│       │   ├── simulation.ts           # District simulation types
│       │   └── analytics.ts            # Admin telemetry types
│       │
│       ├── components/                 # Reusable UI Components
│       │   ├── common/                 # Core atomic components
│       │   │   ├── Navbar.tsx          # Top navigation with role badge & offline pill
│       │   │   ├── Sidebar.tsx         # Role-based navigation links
│       │   │   ├── Button.tsx          # Accessible clinical button
│       │   │   ├── Badge.tsx           # Status badge (Green/Yellow/Red)
│       │   │   ├── Modal.tsx           # Accessible dialog
│       │   │   ├── DisclaimerBanner.tsx# Mandatory CDSS medical disclaimer
│       │   │   ├── LoadingSkeleton.tsx # Content loading skeleton
│       │   │   └── EmptyState.tsx      # Clean empty data placeholders
│       │   │
│       │   ├── worker/                 # Health Worker Components
│       │   │   ├── AnonymizedPatientForm.tsx # 30-second intake form (Zero PII)
│       │   │   ├── ImageDropzone.tsx   # Drag-and-drop fundus file selector
│       │   │   ├── IQAResultModal.tsx  # Good/Borderline/Reject alert with recapture tips
│       │   │   ├── EnhancementViewer.tsx # Side-by-side original vs CLAHE enhanced
│       │   │   ├── PipelineProgress.tsx# Animated step-by-step inference indicator
│       │   │   ├── SplitCompareSlider.tsx # Interactive Fundus vs Grad-CAM slider
│       │   │   └── ResultCard.tsx      # Summary card with 1-click PDF download
│       │   │
│       │   ├── doctor/                 # Tele-Ophthalmology Cockpit Components
│       │   │   ├── ReferralTable.tsx   # Prioritized triage worklist
│       │   │   ├── DeepZoomCanvas.tsx  # Canvas pan, zoom (up to 400%), and reset
│       │   │   ├── FilterToolbar.tsx   # Natural, Red-Free Green, and CLAHE toggles
│       │   │   ├── HeatmapSlider.tsx   # Grad-CAM opacity slider (0% to 100%)
│       │   │   ├── LesionPins.tsx      # Quadrant markers & candidate lesions
│       │   │   └── ClinicalDecisionForm.tsx # Agree/Modify/Reject form & digital sign
│       │   │
│       │   └── admin/                  # Public Health & Admin Components
│       │       ├── MetricCard.tsx      # KPI cards (Total Screened, Referrals, etc.)
│       │       ├── GradeDistributionChart.tsx # Severity bar and pie charts
│       │       ├── ConcordanceHeatmap.tsx # AI-Doctor agreement confusion matrix
│       │       ├── SimulationControls.tsx # Interactive sliders for 100k-patient model
│       │       ├── SimulationResults.tsx # Backlog, bandwidth, and workload graphs
│       │       └── AuditTable.tsx      # Immutable audit trail inspector
│       │
│       └── pages/                      # Role-Specific Page Views
│           ├── LoginPage.tsx           # 1-Click demo role switcher (Admin/Worker/Doctor)
│           ├── worker/
│           │   ├── WorkerDashboard.tsx # Patient registry & queue
│           │   ├── NewScreeningPage.tsx# Intake, upload & IQA gate
│           │   └── ScreeningResultPage.tsx # XAI findings & PDF download
│           ├── doctor/
│           │   ├── DoctorDashboard.tsx # Prioritized referral queue
│           │   └── ExaminationCockpit.tsx # Deep-zoom diagnostic viewer & review form
│           └── admin/
│               ├── AdminDashboard.tsx  # Epidemiological surveillance & KPIs
│               ├── DistrictSimulatorPage.tsx # 100k rural patient simulation
│               └── AuditLogsPage.tsx   # Security & DISHA compliance logs
│
├── ml/                                 # ML Model Engineering & Research Assets
│   ├── data/                           # Dataset preparation guides (APTOS 2019, EyePACS)
│   ├── notebooks/                      # Exploratory data analysis & Grad-CAM prototyping
│   ├── training/                       # EfficientNet-B4 fine-tuning scripts
│   ├── evaluation/                     # Quadratic Weighted Kappa & confusion matrix scripts
│   └── inference/                      # Standalone CLI inference harness
│
├── simulink/                           # MathWorks Simulink & MATLAB Ecosystem
│   ├── README_SIMULINK.md              # Model specification & architecture document
│   ├── RetinaSahayak_Edge.slx          # Simulink system simulation model
│   ├── init_retinasahayak_sim.m        # MATLAB parameter initialization script
│   ├── stateflow_triage_spec.m         # Stateflow triage state chart specification
│   ├── import_onnx_verify.m            # Deep Learning Toolbox ONNX import script
│   └── run_edge_benchmark.m            # Latency, memory & power profiling harness
│
├── matlab/                             # Standalone MATLAB Algorithms (Sponsor Complement)
│   ├── iqa_laplacian_filter.m          # Laplacian blur variance in pure MATLAB
│   ├── clahe_enhancement.m             # Contrast Limited Adaptive Histogram Equalization
│   └── ben_graham_normalization.m      # Retinal color normalization function
│
├── deployment/                         # DevOps & Cloud Deployment Manifests
│   ├── cloudrun.yaml                   # Google Cloud Run service definition
│   ├── gcs_bucket_setup.sh             # Cloud Storage bucket creation script
│   ├── nginx.conf                      # Production frontend Nginx config
│   └── github-actions.yml              # CI/CD automated test & build workflow
│
├── demo/                               # Hackathon Demo Dataset & Assets
│   └── sample_images/                  # 12 Curated Fundus Images
│       ├── 01_grade0_normal.jpg        # Normal healthy retina
│       ├── 02_grade1_mild.jpg          # Mild NPDR (Microaneurysms only)
│       ├── 03_grade2_moderate.jpg      # Moderate NPDR (Hemorrhages & exudates)
│       ├── 04_grade3_severe.jpg        # Severe NPDR (4-quadrant hemorrhages)
│       ├── 05_grade4_pdr.jpg           # Proliferative DR (Neovascularization)
│       ├── 06_reject_blurry.jpg        # Motion-blurred image for IQA rejection
│       ├── 07_borderline_dark.jpg      # Underexposed image for CLAHE enhancement
│       ├── 08_uncertain_lowconf.jpg    # Ambiguous case for uncertainty routing
│       ├── 09_grade2_dme_risk.jpg      # Moderate NPDR with macular exudates
│       ├── 10_grade0_healthy_alt.jpg   # Normal retina variant
│       ├── 11_reject_glare.jpg         # Corneal reflection glare reject
│       └── 12_grade3_irma.jpg          # Severe NPDR with IRMA
│
└── docs/                               # Presentation Materials & Slide Blueprints
    ├── ARCHITECTURE_DIAGRAMS.md        # Mermaid diagrams of full system & GCP stack
    └── CLINICAL_RATIONALE_GUIDE.md     # CDSS screening guidelines & medical backing
```

---

## 2. Key Architectural Boundaries

1. **`backend/app/` Internal Separation:**
   - `core/`: Immutable application settings, JWT logic, and database connectivity.
   - `models/` vs `schemas/`: Absolute decoupling between persistent ORM entities and network DTOs.
   - `services/storage/`: Clean provider abstraction interface allowing seamless switching between local disk storage (`LocalStorageProvider`) and Google Cloud Storage (`GCSStorageProvider`) with zero downstream code changes.
   - `ml/`: Pure algorithmic computer vision and deep learning modules, runnable independently of the web framework.
2. **Offline-First Resilience:**
   - The frontend leverages `IndexedDB` (`frontend/src/services/offlineStorage.ts`) to queue patient records and images during rural cellular outages, synchronizing via `/api/v1/screenings/offline-batch-sync` upon reconnection.
3. **Pluggable Mock Inference:**
   - If trained PyTorch weights are absent on the demo host, `backend/app/ml/mock_inference.py` provides realistic, deterministic predictions and Grad-CAM maps without crashing or emitting generic random data.
