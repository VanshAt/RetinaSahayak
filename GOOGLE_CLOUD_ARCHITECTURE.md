# RetinaSahayak: Google Cloud Platform Architecture & Provider Abstraction

**Problem Statement ID:** SIH26038 | **Project:** RetinaSahayak  
**Cloud Strategy:** Hybrid Architecture with Zero-Cloud Local Fallback (Google Cloud Bonus Alignment)  
**Security & Compliance:** HIPAA, DISHA & ABDM (Ayushman Bharat Digital Mission) Interoperability

---

## 1. Executive Summary & Google Cloud Strategy

To maximize hackathon bonus points while guaranteeing that the live demonstration **never fails** due to network outages or missing cloud credentials, RetinaSahayak adopts a **Provider Abstraction Layer**.

The application operates in two distinct modes configured via environment variables:
1. **Local Mode (Default / Offline-First):** Uses SQLite, local disk storage (`/storage/`), local PyTorch/Mock ML inference, and local JWT authentication. Requires **zero** GCP credentials or internet access.
2. **Google Cloud Mode (Production / Cloud-Enabled):** Connects seamlessly to Google Cloud Run, Google Cloud Storage, Cloud SQL/Firestore, Vertex AI, Google Cloud Healthcare API, Secret Manager, and Cloud Logging.

```mermaid
graph TB
    subgraph Client["Frontend Client (React 18 / PWA)"]
        CLIENT_UI[Client UI & Offline Queue]
    end

    subgraph GCP_Gateway["Google Cloud Run (Compute Layer)"]
        CONTAINER[Docker Container: FastAPI ASGI App]
        SECRETS[Google Secret Manager: JWT & DB Keys]
        LOGGING[Google Cloud Logging: Structured Telemetry]
    end

    subgraph Provider_Interface["Provider Abstraction Layer"]
        STORAGE_CTRL[StorageProvider Interface]
        DB_CTRL[DatabaseProvider Interface]
        ML_CTRL[InferenceProvider Interface]
    end

    subgraph Local_Fallbacks["Local Mode (Offline-First Fallback)"]
        LOCAL_DIR[Local Disk: /backend/storage/]
        SQLITE_DB[(SQLite 3 WAL Database)]
        LOCAL_MODEL[PyTorch / Mock Inference Engine]
    end

    subgraph GCP_Services["Google Cloud Platform Services"]
        GCS_BUCKET[Google Cloud Storage Buckets]
        CLOUD_SQL[(Cloud SQL PostgreSQL / Firestore)]
        VERTEX_AI[Vertex AI Model Endpoint]
        HC_API[Google Cloud Healthcare API: DICOM / FHIR]
        VISION_API[Cloud Vision API: Quality Experiments]
    end

    CLIENT_UI --> CONTAINER
    CONTAINER --> SECRETS & LOGGING
    CONTAINER --> STORAGE_CTRL & DB_CTRL & ML_CTRL

    STORAGE_CTRL -->|Default| LOCAL_DIR
    STORAGE_CTRL -.->|GCP Enabled| GCS_BUCKET

    DB_CTRL -->|Default| SQLITE_DB
    DB_CTRL -.->|GCP Enabled| CLOUD_SQL

    ML_CTRL -->|Default| LOCAL_MODEL
    ML_CTRL -.->|GCP Enabled| VERTEX_AI

    CONTAINER -.->|DICOM Export| HC_API
    CONTAINER -.->|Metadata Experiments| VISION_API
```

---

## 2. Google Cloud Services Mapping & Utilization

| Google Cloud Service | Role in RetinaSahayak | Production Integration | Local Fallback Mechanism |
| :--- | :--- | :--- | :--- |
| **Google Cloud Run** | Application Hosting | Hosts containerized FastAPI backend and compiled React SPA with serverless auto-scaling ($0 \rightarrow N$). | Local Uvicorn server (`localhost:8000`) and Vite dev server (`localhost:5173`). |
| **Google Cloud Storage (GCS)** | Medical Asset Storage | Stores raw fundus images, CLAHE enhanced photos, Grad-CAM overlays, and compiled bilingual PDF reports in encrypted regional buckets. | Local file system storage in `backend/storage/raw_images`, `enhanced/`, `overlays/`, `reports/`. |
| **Cloud SQL / Firestore** | Relational & Document Metadata | Cloud SQL (PostgreSQL 15) for relational referral queues and doctor reviews; Firestore for rapid document sync. | Local SQLite 3 database with WAL mode and foreign key constraints enabled. |
| **Vertex AI** | Model Hosting & Registry | Hosts containerized PyTorch EfficientNet-B4 endpoints with auto-scaling GPU acceleration for high-volume district batch runs. | Local PyTorch CPU runtime or deterministic high-fidelity `MOCK_INFERENCE_SERVICE`. |
| **Google Cloud Healthcare API** | DICOM & FHIR Interoperability | Provides standards-based DICOMweb and FHIR R4 store integration for Ayushman Bharat Digital Mission (ABDM) compliance. | Internal JSON schemas structured in accordance with FHIR `DiagnosticReport` specifications. |
| **Cloud Secret Manager** | Secure Secret Management | Houses database passwords, JWT private keys, and API tokens securely without `.env` exposure. | Local `.env` file reading via Pydantic `BaseSettings` (`backend/app/core/config.py`). |
| **Google Cloud Logging** | Audit & Diagnostic Logging | Ingests real-time audit logs, IQA failure events, and doctor override transactions into Cloud Logging. | Local Python structured logger writing to console and local `audit_logs` table. |
| **Cloud Vision API** | Supporting Quality Verification | Used strictly for experimental OCR validation of physical camera labels and image metadata (NOT as the primary DR model). | OpenCV mathematical algorithms (Laplacian variance, Green CLAHE, Tenengrad criterion). |

---

## 3. Provider Abstraction Implementation Architecture

### 3.1 Storage Provider Interface (`backend/app/services/storage/base.py`)
```python
from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, destination_path: str, content_type: str) -> str:
        """Saves file bytes and returns the accessible URI or public path."""
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def get_url(self, file_path: str) -> str:
        """Returns browser-accessible URL for the asset."""
        pass
```

### 3.2 Local Storage Provider (`backend/app/services/storage/local_provider.py`)
- Writes files to disk under `backend/storage/`.
- Serves files through FastAPI static mount: `/api/v1/storage/...`.

### 3.3 GCS Storage Provider (`backend/app/services/storage/gcs_provider.py`)
- Leverages `google-cloud-storage` Python SDK.
- Reads credentials via Google Application Default Credentials (ADC) or `GOOGLE_APPLICATION_CREDENTIALS` path.
- Uploads blobs to bucket specified in `GCS_BUCKET_NAME`.
- Generates signed URLs with 60-minute expiration for secure asset viewing.

### 3.4 Storage Factory (`backend/app/services/storage/factory.py`)
```python
from backend.app.core.config import settings
from .local_provider import LocalStorageProvider
from .gcs_provider import GCSStorageProvider

def get_storage_provider():
    if settings.STORAGE_PROVIDER == "GCS" and settings.GCS_BUCKET_NAME:
        try:
            return GCSStorageProvider(bucket_name=settings.GCS_BUCKET_NAME)
        except Exception as e:
            # Graceful fallback to local storage if GCP authentication fails
            print(f"[WARN] Failed to connect to GCS: {e}. Falling back to LocalStorageProvider.")
            return LocalStorageProvider()
    return LocalStorageProvider()
```

---

## 4. Google Cloud Healthcare API & FHIR Interoperability Blueprint

To ensure future integration with India's **Ayushman Bharat Digital Mission (ABDM)** and global electronic health record (EHR) systems, RetinaSahayak formats diagnostic outputs to map directly into the **FHIR R4 `DiagnosticReport`** standard:

```json
{
  "resourceType": "DiagnosticReport",
  "id": "dr-retinasahayak-scr_22a7f8",
  "status": "preliminary",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
      "code": "OPH",
      "display": "Ophthalmology"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "390835002",
      "display": "Diabetic retinopathy screening"
    }]
  },
  "subject": {
    "reference": "Patient/PAT-VNS-8841"
  },
  "effectiveDateTime": "2026-10-13T10:32:00Z",
  "conclusion": "Grade 2: Moderate Non-Proliferative Diabetic Retinopathy (NPDR) with mild macular threat.",
  "conclusionCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "312993005",
      "display": "Moderate nonproliferative diabetic retinopathy"
    }]
  }],
  "presentedForm": [{
    "contentType": "application/pdf",
    "url": "https://storage.googleapis.com/retinasahayak-reports/scr_22a7f8_report.pdf"
  }]
}
```

---

## 5. Deployment & Configuration Modes

### Mode A: Zero-Cloud Local Setup (Hackathon Demo Safe Mode)
In this mode, no Google Cloud account, billing, or credentials are required:
```bash
# In .env file:
ENVIRONMENT=local
STORAGE_PROVIDER=LOCAL
DATABASE_URL=sqlite:///./retinasahayak.db
USE_MOCK_INFERENCE=true
GCP_PROJECT_ID=
GCS_BUCKET_NAME=
```
- Boot with `python -m backend.main` and `npm run dev` in `frontend/`.

### Mode B: Google Cloud Production Mode
```bash
# In .env file:
ENVIRONMENT=production
STORAGE_PROVIDER=GCS
GCP_PROJECT_ID=retinasahayak-sih2026
GCS_BUCKET_NAME=retinasahayak-medical-assets
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/retinasahayak_db
USE_MOCK_INFERENCE=false
```

### Docker Container for Google Cloud Run
```dockerfile
# Multi-stage production build
FROM python:3.11-slim as backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```
Deploy to Cloud Run via single command:
```bash
gcloud run deploy retinasahayak-api \
  --source . \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```
