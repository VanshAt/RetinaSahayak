# RetinaSahayak: Team Workflow, Branching Strategy & Hackathon Execution Plan

**Problem Statement ID:** SIH26038 | **Project:** RetinaSahayak  
**Target Event:** Smart India Hackathon 2026 (36-Hour Continuous Sprint)  
**Team Composition:** 4 Members (Cross-functional MedTech / AI / Full-Stack / DevOps)

---

## 1. Team Role Allocation & Ownership Matrix

| Member | Primary Role | Core Ownership & Deliverables | Hackathon Focus |
| :--- | :--- | :--- | :--- |
| **Member 1** | **ML & Computer Vision Lead** | - 3-Tier IQA Gate (`GOOD`/`BORDERLINE`/`REJECT`).<br>- Borderline Enhancement (CLAHE + Ben Graham).<br>- PyTorch EfficientNet-B4 ICDR Model & Mock Fallback.<br>- Grad-CAM++ Hook Engine & Lesion Bounding.<br>- Model Card & ONNX Export for MATLAB. | Ensures high diagnostic sensitivity ($>96\%$) and crisp explainability overlays. |
| **Member 2** | **Full-Stack Backend Lead** | - FastAPI Application Core (`backend/app`).<br>- Provider Abstraction Layer (Local vs GCS/Cloud SQL).<br>- SQLAlchemy 2.0 Models & Zero-PII Patient Schema.<br>- Referral Triage Engine & Doctor Review API.<br>- ReportLab Bilingual A4 Medical PDF Compiler. | Delivers resilient REST APIs and fast local/GCS data pipelines. |
| **Member 3** | **Frontend & UI/UX Lead** | - React 18 + TypeScript + Tailwind CSS Frontend.<br>- Health Worker 3-Step Guided Wizard.<br>- Deep-Zoom Examination Cockpit for Ophthalmologist.<br>- Traffic-Light Color Tokens (Green/Yellow/Red).<br>- Offline-First IndexedDB Upload Queue. | Crafts a zero-friction, touch-friendly UI that wins the 20% UX judging score. |
| **Member 4** | **DevOps, Simulation & Pitch Lead** | - Docker Containerization & Google Cloud Run Setup.<br>- 100k-Patient District Deployment Simulator.<br>- MathWorks Simulink Edge Model (`.slx`) Co-Design.<br>- Pitch Deck (6-Slide & 12-Slide), Demo Script & Judge Q&A.<br>- Automated CI Pipeline & Golden Dataset Curation. | Manages system deployment, presentations, and MathWorks/GCP bonus criteria. |

---

## 2. Git Branching Strategy & Collaboration Rules

We follow a modified **Trunk-Based Development** model with short-lived feature branches:

```
main (Production / Live Jury Demo Ready)
  ↑
develop (Integration & End-to-End Testing)
  ├── feature/backend-auth-storage
  ├── feature/ml-iqa-gradcam
  ├── feature/frontend-wizard-cockpit
  ├── feature/district-simulation-gcp
  └── feature/simulink-edge-specs
```

### Git Rules & Commit Standards
1. **Never commit directly to `main`:** All merges to `main` require a pass of backend tests (`pytest`) and frontend build (`npm run build`).
2. **Conventional Commit Messages:**
   - `feat:` New feature or endpoint.
   - `fix:` Bug fix or clinical logic correction.
   - `refactor:` Code cleanup without feature change.
   - `test:` Unit or integration test addition.
   - `docs:` Documentation or pitch updates.
   - Example: `feat(ml): implement Grad-CAM++ hook on last convolutional layer`
3. **No Secret or Asset Commits:** Never commit `.env`, private keys, GCP service account JSON files, or large raw dataset folders. Use `.env.example` templates only.

---

## 3. 36-Hour Hackathon Execution Timeline

```mermaid
gantt
    title Smart India Hackathon 2026: 36-Hour Milestone Sprint
    dateFormat  X
    axisFormat  Hour %X

    section Architecture & Setup
    Phase 0: Plans, Contracts & Repository Scaffold :0, 4
    Phase 1: Backend Scaffold, Auth & Storage Abstraction :4, 8

    section Core Engines
    Phase 2: IQA Gate, CLAHE & DR Classification :8, 14
    Phase 3: Grad-CAM++ & Lesion Bounding Engine :14, 18
    Phase 6A: Frontend Health Worker 3-Step Wizard :10, 18

    section Downstream Clinical
    Phase 4: Tele-Ophthalmology Cockpit & Sign-off :18, 22
    Phase 5: ReportLab Bilingual PDF Generation :18, 22
    Phase 6B: Frontend Doctor Cockpit & Admin Views :20, 26

    section Innovation & Simulation
    Phase 7: GCP Cloud Run & 100k District Simulator :24, 28
    Phase 8: MathWorks Simulink Edge Co-Design :26, 30

    section Hardening & Demo
    Phase 9: Golden Dataset, End-to-End Tests & CI :30, 33
    Phase 10: Pitch Deck Rehearsal & Live Demo Polish :33, 36
```

### Hour-by-Hour Breakdown

#### Block 1 (Hours 0 – 4): Architecture, Scaffolding & Contract Freezing
- All 10 planning artifacts reviewed and approved.
- Monorepo scaffold initialized (`/backend/app`, `/frontend/src`, `/ml`, `/simulink`).
- Git repository configured with branch protections and `.env.example`.

#### Block 2 (Hours 4 – 12): Foundation & Core Pipeline
- **Backend:** SQLAlchemy models, SQLite WAL database, JWT auth, and storage provider abstraction (Local vs GCS).
- **ML:** IQA gate (Good/Borderline/Reject), CLAHE enhancer, EfficientNet model loader with mock inference fallback.
- **Frontend:** Vite + React + Tailwind setup, routing, authentication state, and basic wizard layout.

#### Block 3 (Hours 12 – 20): Deep Learning, Explainability & Clinical Workflows
- **ML:** Grad-CAM++ mathematical hooks, colormap blending, candidate lesion contour extraction.
- **Backend:** Referral triage logic, tele-ophthalmology endpoints, ReportLab bilingual PDF compiler.
- **Frontend:** Interactive split slider (Fundus vs Grad-CAM), IQA feedback modal with recapture tips.

#### Block 4 (Hours 20 – 28): Tele-Ophthalmology Cockpit, GCP & District Simulator
- **Frontend:** Deep-zoom canvas (Pan, Zoom up to 400%, Red-Free filter, Grad-CAM opacity slider).
- **Backend & DevOps:** 100,000-patient district simulation service, Docker container build, Cloud Run configuration.
- **Simulink:** MathWorks Simulink edge model specification (`RetinaSahayak_Edge.slx`) and ONNX export script.

#### Block 5 (Hours 28 – 33): System Hardening & Golden Dataset Verification
- Load 12 curated demo images into `demo/sample_images/`.
- Run automated pytest suite and verify frontend build (`npm run build`).
- Verify complete offline execution with zero internet connectivity.

#### Block 6 (Hours 33 – 36): Presentation Polish & Jury Rehearsal
- Run live demo rehearsals against the 5-minute pitch script.
- Review judge Q&A responses covering clinical bounds, false negatives, and Google Cloud architecture.
- Final commit to `main`.
