# MEDICAL REPORT SPECIFICATION
RetinaSahayak — 2-Page A4 Clinical Screening Report

## 1. Document Architecture & Dimensions
- **Page Size:** Standard ISO A4 ($210 \times 297\text{ mm}$ or $595.27 \times 841.89\text{ pt}$).
- **Margins:** Top 32 pt, Bottom 32 pt, Left 36 pt, Right 36 pt.
- **Page Count:** Exactly 2 Pages (Strictly structured with ReportLab flowables and `PageBreak`).
- **Typography:** Primary font `Helvetica` / `Helvetica-Bold`. Optional Devanagari fallback: `Nirmala.ttc`.

---

## 2. Layout & Content by Page

### Page 1: Patient Demographics, Fundus Photography & IQA Gate
1. **Header Banner**:
   - Organization Title: `RetinaSahayak`
   - Document Title: `AI-Assisted Diabetic Retinopathy Screening Report`
   - Program Subtitle: `Community Health Mission • Primary Eye Care Tele-Screening Network`
   - Metadata: Unique Report ID, Screening Encounter Timestamp, PHC Location Name.
2. **Patient Demographics Table**:
   - Anonymized Patient ID (e.g., `PAT-VNS-7521`)
   - Age Group & Gender (e.g., `51-65 / FEMALE`)
   - Known Diabetes Duration (e.g., `8 years`)
   - Screened Eye & Dilation Status (e.g., `Right Eye (OD) • UNDILATED`)
3. **Dual Fundus Image Gallery**:
   - Original Fundus Photograph (High-resolution raw upload)
   - Enhanced Fundus Photograph (CLAHE & Ben Graham illumination correction, if applied)
4. **Image Quality Assessment (IQA Gate)**:
   - Evaluated 3-Tier Quality Status: `GOOD`, `BORDERLINE`, or `REJECT`
   - Laplacian Sharpness Score
   - Quality Assessment & Issues Detected
   - Actionable Recapture Guidance
   - *Special Case (REJECT):* Prominent callout box stating that AI diagnostic grading was suspended due to inadequate image quality, providing clear instructions for stabilization and recapture.

---

### Page 2: Diagnostic Evaluation, Explainable AI & Care Plan
1. **Header Banner**:
   - Title: `RetinaSahayak | Diagnostic Evaluation & Explainable AI Verification`
2. **Diagnostic Evaluation Panel**:
   - Predicted Diabetic Retinopathy Grade (ICDR Grade 0 through 4 with color coding)
   - Quantitative Model Confidence Percentage (e.g., `87.4%`)
   - Referral Status (`NON_REFERABLE` or `REFERABLE`)
   - Uncertainty Status (`CERTAIN` or `UNCERTAIN`)
   - 5-Class Categorical Softmax Probabilities (`G0:0.01, G1:0.08, G2:0.87, G3:0.03, G4:0.00`)
   - Inference Engine Attribution (`MOCK_INFERENCE_SERVICE` vs. `PYTORCH_EFFICIENTNET`)
3. **Grad-CAM++ Visual Explainability Panel**:
   - Standalone Attention Heatmap (JET/TURBO representation)
   - Heatmap Blended Overlay on Fundus Photograph
   - Transparent Explanation Label & Disclaimer Banner differentiating simulated from trained activations.
4. **Clinical Rationale & Recommended Action**:
   - Plain-language clinical explanation detailing features that influenced the model's prediction.
   - Recommended next clinical steps (follow-up timeline or referral window).
5. **Digital Verification QR Code & Audit Panel**:
   - High-density verification QR code linking to the official tele-screening record.
   - Model version and generation timestamp.
   - Tamper-evident verification hash.
6. **CDSS Legal Disclaimer**:
   - Prominent statement that this is a presumptive screening observation requiring licensed ophthalmologist review prior to clinical intervention.

---

## 3. Supported Report Scenarios
1. **Grade 0 Normal Case**: Non-referable, annual routine follow-up advice.
2. **Grade 1 Mild NPDR Case**: Non-referable, follow-up in 6 to 12 months with blood sugar control advice.
3. **Grade 2 Moderate NPDR Case**: Referable, tele-ophthalmology referral within 30 days.
4. **Grade 3 Severe NPDR Case**: High-priority referable, ophthalmology evaluation within 7 days.
5. **Grade 4 Proliferative DR Case**: Emergency tertiary referral (< 48 hours).
6. **Uncertain Case**: Routed to tele-ophthalmology queue for specialist review due to confidence below 0.65.
7. **Rejected Image Case**: States that AI grading was not performed, with actionable recapture guidance.

---

## 4. Multi-Tenant Access Control & Audit Rules
- **Authorized Personas**:
  - The PHC Worker who created the screening record (restricted to their designated health centre).
  - Ophthalmologists assigned to review or triage cases.
  - System Administrators.
- **Worker Isolation**: Requests by a worker to download reports for patients from another health center return `403 Forbidden`.
- **Tamper-Evident Audit Logging**: Every download generates a `REPORT_DOWNLOADED` audit log entry with user ID, user role, resource ID, timestamp, status, and SHA-256 cryptographic hash.
- **Database Metadata**: Persisted in table `report_metadata` tracking `report_id`, `screening_id`, `generated_by`, `generated_at`, `report_file_path`, and `model_version`.
