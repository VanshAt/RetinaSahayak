# RetinaSahayak: Clinical, Technical & Operational Risks and Assumptions

**Problem Statement ID:** SIH26038 | **Project:** RetinaSahayak  
**Regulatory Framework:** CDSCO / DISHA (Digital Information Security in Healthcare Act) / IEC 62304 Medical Device Software Life Cycle  
**Clinical Scope:** Clinical Decision Support System (CDSS) — Human-in-the-Loop Screening Triage

---

## 1. Core Operating Assumptions

1. **Screening-Only Boundary:** RetinaSahayak is deployed strictly as a **screening-support and tele-triage tool**, not as an autonomous medical diagnostic device. It never claims to replace an ophthalmologist. All diagnostic classifications are designated as *"Presumptive Screening Findings"* requiring confirmation by a licensed medical practitioner.
2. **Dual-Mode Operational Independence:** The system operates in two independent modes:
   - **Local Mode:** 100% functional without external internet connectivity, utilizing SQLite, local disk storage, and local PyTorch / Mock ML.
   - **Google Cloud Mode:** Pluggable cloud scaling utilizing Google Cloud Run, Google Cloud Storage, Cloud SQL/Firestore, and Vertex AI.
3. **Zero Direct PII Collection:** To ensure complete privacy compliance under DISHA and HIPAA, patient records collect only anonymized codes (`PAT-XXXX`), age groups, gender, and diabetes duration. No real names, phone numbers, or Aadhaar numbers are recorded.
4. **Fundus Camera Specifications:** Images are acquired via standard commercial tabletop or portable handheld fundus cameras (e.g., Remidio NM-FOP, Forus 3nethra, Volk iNview) with a minimum optical resolution of $800 \times 800$ pixels and minimum 45-degree field-of-view.
5. **MathWorks Edge Co-Design:** In the absence of physical embedded edge hardware during the hackathon demonstration, edge deployment on ARM Cortex-A76 / NVIDIA Jetson is simulated via MathWorks Simulink (`RetinaSahayak_Edge.slx`) using Software-in-the-Loop (SIL) profiling and synthetic test vector streams.

---

## 2. Risk Categorization & Clinical Safeguards

### 2.1 Clinical & Patient Safety Risks

#### Risk C-1: False Negatives (Missed Early Diabetic Retinopathy or DME)
- **Clinical Consequence:** A patient with early Moderate NPDR or subtle macular edema is misclassified as Grade 0 (Normal), leading to false reassurance and delayed intervention until irreversible visual impairment occurs.
- **Safeguards:**
  1. **Asymmetric Clinical Loss:** Model optimization prioritizes sensitivity over specificity for referable grades ($\text{Grade} \ge 2$), achieving $> 96\%$ target sensitivity.
  2. **Conservative Uncertainty Thresholds:** Predictions with confidence $< 0.65$ or high entropy are tagged **`UNCERTAIN`** and automatically routed for tele-ophthalmologist review regardless of predicted grade.
  3. **Universal Recurrence Advisory:** The bilingual report explicitly states: *"This is a preliminary screening. If experiencing sudden visual changes, dark spots, or flashes, visit an eye specialist immediately regardless of screening grade."*

#### Risk C-2: "Automation Bias" & Ophthalmologist Complacency
- **Clinical Consequence:** Overworked tele-ophthalmologists facing heavy screening backlogs may rubber-stamp AI classifications without independently inspecting raw retinal features.
- **Safeguards:**
  1. The tele-ophthalmology cockpit defaults to **Raw Fundus First** with the Grad-CAM heatmap opacity set to 0% or toggled via an explicit slider.
  2. The review form requires the doctor to actively confirm lesion quadrants and sign with their medical registration number and digital signature hash.

#### Risk C-3: Demographic & Retinal Melanin Pigmentation Variation
- **Clinical Consequence:** High pigmentation variation across diverse Indian states could skew classification accuracy.
- **Safeguards:**
  - **Ben Graham Color Normalization:** Subtracts local Gaussian background luminance ($4I - 4\text{Gauss}(I) + 128$) to eliminate variations in retinal pigmentation while accentuating vascular lesions.

---

### 2.2 Technical & Computational Risks

#### Risk T-1: Poor-Quality / Blurry Fundus Captures in Rural Camps
- **Technical Consequence:** Low-cost handheld cameras in rural outreach camps produce motion blur, uneven illumination, or eyelid obstruction.
- **Safeguards:**
  - **Deterministic 3-Tier IQA Gate:** Classifies images into **`GOOD`**, **`BORDERLINE`**, or **`REJECT`** before AI grading.
  - **Actionable Guidance:** Instead of a generic error, the UI displays specific guidance: *"Patient moved. Stabilize camera against headrest and instruct patient to fixate on the green light."*
  - **Auto-Enhancement:** Borderline images are automatically restored using Green-channel CLAHE and contrast normalization, retaining both original and enhanced images.

#### Risk T-2: Google Cloud Credential or Network Disconnection During Live Demo
- **Technical Consequence:** Network loss or invalid cloud credentials cause the application to crash or stall during a live jury pitch.
- **Safeguards:**
  - **Provider Abstraction Layer:** If Google Cloud Storage or Cloud SQL fails to connect, the system automatically falls back to `LocalStorageProvider` and local SQLite with zero downtime.
  - **Deterministic `MOCK_INFERENCE` Fallback:** If GPU/PyTorch weights are absent on the host machine, the system switches seamlessly to a calibrated mock inference engine.

#### Risk T-3: Precision Discrepancies between PyTorch and MATLAB ONNX Runtime
- **Technical Consequence:** Slight numerical divergence between Python server predictions and Simulink edge simulation blocks.
- **Safeguards:**
  - Standard ONNX Opset 14 export with fixed FP32 precision.
  - Numerical parity test script (`simulink/import_onnx_verify.m`) ensuring maximum absolute error $\epsilon < 10^{-5}$ across synthetic tensors.

---

### 2.3 Operational & Human-Factors Risks

#### Risk O-1: Rural Health Worker Digital Literacy Barrier
- **Operational Consequence:** Complex clinical terminology confuses grassroots workers (ASHAs/ANMs), resulting in user errors or skipped fields.
- **Safeguards:**
  - Simplified **3-step linear wizard** with large touch-friendly buttons and traffic-light color coding (Green: Normal, Yellow: Borderline, Red: Referral).
  - Jargon-free labels and 1-click test sample loader for rapid training and demonstration.

#### Risk O-2: Patient Referral Dropout in Remote Villages
- **Operational Consequence:** Patients identified with Grade 3/4 DR fail to travel to district tertiary hospitals due to travel costs or fear.
- **Safeguards:**
  - Printed vernacular (Hindi + English) PDF report featuring pictorial risk diagrams and a verification QR code linking directly to their tele-consultation record.
  - Public health tracking list of unreviewed referrals for ASHA home follow-ups.

---

## 3. Comprehensive Risk Mitigation Matrix

| ID | Category | Severity | Likelihood | Risk Description | Mitigation Strategy | Fallback / Recovery Plan |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **C-1** | Clinical | **Critical** | Low | False Negative in Severe DR | Asymmetric loss weighting, $>96\%$ sensitivity target, conservative referral threshold ($>0.35$). | Universal 6-month safety re-screening advisory on all reports. |
| **C-2** | Clinical | **High** | Med | Misleading Grad-CAM heatmaps on lens artifacts | Dual verification: Grad-CAM++ combined with rule-based lesion quadrant bounding boxes. | Doctor inspection cockpit with raw red-free filter toggle. |
| **T-1** | Technical | **High** | High | Blur / Poor illumination in rural field | Deterministic mathematical IQA gate with actionable recapture guidance. | Manual doctor review flag if image cannot be retaken due to patient condition. |
| **T-2** | Technical | **High** | Med | Cloud disconnect during hackathon demo | Pluggable Provider Abstraction layer with instant local fallback to SQLite & local disk. | Offline-ready mode with zero external cloud dependencies. |
| **T-3** | Technical | **Med** | Low | High CPU latency on cheap PHC laptops | Lightweight EfficientNet-B4 backbone optimized for $<250\text{ms}$ CPU inference. | High-fidelity deterministic mock inference engine toggle. |
| **O-1** | Operational| **Med** | Med | Health worker digital barrier | Zero-friction guided wizard with high-contrast UI and vernacular text. | Built-in sample test cases for health worker training. |
| **O-2** | Operational| **High** | Med | Patient referral non-adherence | Culturally adapted bilingual PDF with pictorial risk icons and tele-referral QR code. | PHC tracking list of unreviewed referrals for ASHA home visits. |
| **S-1** | MathWorks | **Med** | Low | Hardware unavailability for edge demo | High-fidelity Simulink Stateflow simulation model (`RetinaSahayak_Edge.slx`) with SIL profiling. | Real-time simulated frame rate and power telemetry graphs. |

---

## 4. Ethical & Regulatory Declarations

1. **Non-Diagnostic Notice:** All API payloads and UI views enforce the disclaimer:
   > *"RetinaSahayak is a screening support system. All findings must be clinically validated by a qualified ophthalmologist."*
2. **Data Privacy (DISHA / Ayushman Bharat):**
   - Zero direct PII collected in prototype databases.
   - All doctor review modifications are sealed with cryptographic SHA-256 digital signatures in an immutable audit table.
