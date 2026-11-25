# RetinaSahayak

An AI-assisted diabetic retinopathy (DR) screening, image quality assessment (IQA), and clinical referral workflow platform built for primary health centers and ophthalmology review.

> **Disclaimer:** This project does **not** include any real patient data, medical records, or clinical fundus images. All sample data and inference outputs in this repository are synthetic or mocked for demonstration and testing purposes.

---

## Features

- **Image Quality Assessment (IQA)**: Automated sharpness, luminance, and contrast checks before inference.
- **Diabetic Retinopathy Screening**: Multi-class DR grading with uncertainty-aware confidence thresholds and DME detection.
- **Explainability (Grad-CAM & Lesion Overlays)**: Visual heatmaps and lesion localization overlays for clinical transparency.
- **Clinical Review & Referral Workflow**: Role-based portals for Health Workers, Ophthalmologists, and Admins.
- **Automated PDF & QR Reports**: Printable clinical screening reports with embedded QR verification.
- **Offline-First & Cloud-Ready**: Supports local SQLite (WAL mode) + local storage, with optional PostgreSQL and Google Cloud Storage abstractions.

---

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, PyTorch / ONNX Runtime, OpenCV, ReportLab
- **Frontend**: React, TypeScript, Vite
- **Database**: SQLite (local) / PostgreSQL (production)
- **Containerization**: Docker, Docker Compose

---

## Local Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/VanshAt/RetinaSahayak.git
cd RetinaSahayak
```

### 2. Backend Setup
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 3. Environment-Variable Setup
Copy `.env.example` to `.env` and fill in your own values (never commit `.env` to version control):
```bash
cp .env.example .env
```

Example `.env` placeholders:
```env
SECRET_KEY="YOUR_SECRET_KEY"
DATABASE_URL="YOUR_DATABASE_URL"
GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"
GCS_BUCKET_NAME="YOUR_GCS_BUCKET_NAME"
GOOGLE_APPLICATION_CREDENTIALS="YOUR_GOOGLE_APPLICATION_CREDENTIALS"
```

### 4. Run the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## Screenshots

*Add screenshots of the Health Worker Portal, Doctor Cockpit, and PDF Report here.*
