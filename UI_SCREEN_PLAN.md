# RetinaSahayak: UI/UX Screen Plan & Design Specification

**Problem Statement ID:** SIH26038 | **Framework:** React 18 + TypeScript + Tailwind CSS  
**Target Personas:** 1. PHC Health Worker (Rural), 2. Tele-Ophthalmologist, 3. Public Health Admin  
**Judging Weight:** **20% (User Experience)** | **Accessibility:** WCAG 2.1 AA & Mobile/Tablet Optimized

---

## 1. Clinical Design System & Traffic-Light Color Tokens

To ensure immediate cognitive clarity for rural health workers in bright primary healthcare centers, the interface enforces a strict **Traffic-Light Color Hierarchy**:

| State / Meaning | Semantic Color | Tailwind Tokens | Usage in UI |
| :--- | :--- | :--- | :--- |
| **Good / Safe / Non-Referable** | **Vibrant Green** | `bg-emerald-600`, `text-emerald-700`, `border-emerald-500` | Optimal image quality, Grade 0 (Normal), Grade 1 (Mild), System Online. |
| **Borderline / Warning / Uncertain** | **Warm Amber / Yellow** | `bg-amber-500`, `text-amber-800`, `border-amber-400` | Borderline IQA (enhanced via CLAHE), Low-confidence uncertain AI predictions, Pending queue. |
| **Reject / High Risk / Referable** | **Urgent Red** | `bg-rose-600`, `text-rose-700`, `border-rose-500` | IQA Reject (retake required), Grade 2 (Moderate), Grade 3 (Severe), Grade 4 (PDR). |
| **Primary Clinical Blue** | **Trust Blue** | `bg-sky-600`, `text-sky-700`, `bg-sky-50` | Primary buttons, active navigation rails, branding headers. |
| **Dark Examination Canvas** | **Midnight Slate** | `bg-slate-950`, `text-slate-100` | High-contrast deep zoom diagnostic canvas for ophthalmologists. |

### Accessibility & Cognitive Ergonomics
- **Zero Medical Jargon for Health Workers:** Terms like *"Microaneurysms"* or *"Intraretinal Microvascular Abnormalities"* are abstracted into simple visual indicators: *"Small Blood Leaks Detected"*, *"Swelling Near Vision Center"*.
- **Touch-Friendly Hit Targets:** All buttons have a minimum dimension of $48\text{px} \times 48\text{px}$ for tablet tap accuracy.
- **Mandatory Medical Disclaimer:** Displayed prominently on every screening view:  
  > *"AI-generated screening support only. Final diagnosis must be made by a qualified ophthalmologist."*

---

## 2. Persona 1: PHC Health Worker Experience (`/worker`)

### Screen 1.1: 3-Step Guided Screening Wizard
The screening interface is laid out as a single linear, zero-friction 3-step progress wizard:

```
[ Step 1: Patient Details (Done) ] ---> [ Step 2: Camera Capture (Active) ] ---> [ Step 3: Screening Result ]
```

#### Step 1: Anonymized Patient Intake (30 Seconds)
- **Zero Direct PII:** No Aadhaar, no patient names, no phone numbers.
- Fields:
  - `Patient Code`: Auto-generated (e.g. `PAT-VNS-8841`) with 1-click re-generate.
  - `Age Group`: 4 large segmented buttons: `[ 18-35 ]`, `[ 36-50 ]`, `[ 51-65 ]`, `[ 65+ ]`.
  - `Sex`: 3 segmented buttons: `[ Male ]`, `[ Female ]`, `[ Other ]`.
  - `Diabetes Duration`: Interactive slider (0 to 30 years).
  - `Known High Blood Pressure`: Big toggle switch: `[ NO ]` / `[ YES ]`.
  - Primary Action Button: `[ Continue to Eye Photo ]` (Height: 52px, Sky-600).

#### Step 2: Fundus Image Acquisition & Instant IQA Gate
- Drag-and-drop dropzone or direct USB camera trigger.
- **1-Click Test Sample Dropdown:** Health worker can select preloaded sample fundus images (Normal, Mild, Moderate, Severe, Blurry Reject, Dark Borderline) for rapid demonstration.
- Instant IQA Assessment Cards:
  - **Case A: REJECT (Red Card):**
    - Large icon: AlertTriangle.
    - Clear Headline: *"Image Not Clear — Please Retake"*
    - Actionable Tip: *"The photo is blurry because the patient moved. Rest patient's chin on the headrest and ask them to look at the green light."*
    - Big Button: `[ Retake Photograph ]`.
  - **Case B: BORDERLINE (Yellow Card):**
    - Headline: *"Low Light Detected — Photo Enhanced Automatically"*
    - Shows side-by-side thumbnail: Original (Dark) vs Enhanced (CLAHE Crisp).
    - Status: *"Photo quality improved. Proceeding with enhanced image."*
  - **Case C: GOOD (Green Card):**
    - Headline: *"Photo Quality is Excellent!"*
    - Status: *"All retina details are clearly visible."*

#### Step 3: AI Result & Explainability View
- **Top Severity Card:**
  - If Grade 0/1: **Large Green Banner** $\rightarrow$ *"Low Risk (Grade 0: Normal Retina) — No immediate doctor referral required."*
  - If Grade 2–4: **Large Red Banner** $\rightarrow$ *"Referral Needed (Grade 2: Moderate Signs) — Sent to Eye Specialist for Review."*
  - If Uncertain: **Large Yellow Banner** $\rightarrow$ *"Uncertain Prediction — Sent to Eye Specialist for Confirmation."*
- **Interactive Split Slider (`SplitCompareSlider.tsx`):**
  - Smooth slider revealing the Original Fundus on the left and the Grad-CAM++ Heatmap Overlay on the right.
- **Plain-Language Evidence Breakdown:**
  - `[✓] Tiny blood vessel spots detected`
  - `[✓] Mild lipid deposits observed`
  - `[ ] No dangerous new blood vessels`
- **Actions Bar:**
  - Button 1: `[ Download Bilingual PDF Report (English + Hindi) ]`
  - Button 2: `[ View Referral Status (Assigned to Dr. Verma) ]`
  - Button 3: `[ Start Next Patient Screening ]`

---

## 3. Persona 2: Tele-Ophthalmology Cockpit (`/doctor`)

### Screen 2.1: Prioritized Tele-Triage Worklist
- Sorted automatically by clinical urgency:
  1. `EMERGENCY` (Grade 4 PDR / Severe DME) — Flashing red pill
  2. `URGENT` (Grade 3 Severe NPDR) — Solid red pill
  3. `UNCERTAIN_REVIEW` (Low-confidence AI prediction) — Amber pill
  4. `ROUTINE` (Grade 2 Moderate NPDR) — Orange pill
- Summary statistics bar: `Pending Referrals: 14` | `Reviewed Today: 22` | `Average Wait Time: 2.4 hrs`.
- Single click opens the deep-zoom examination workstation.

---

### Screen 2.2: Deep-Zoom Examination Workstation
```
+----------------------------------------------------------------------------------------------------+
| Patient: PAT-VNS-8841 | Age: 51-65 M | Origin: Ramnagar PHC | AI Prediction: Grade 2 (87% conf)   |
+----------------------------------------------------------------------------------------------------+
| TOOLBAR: [Zoom In +] [Zoom Out -] [Reset] [Pan Tool]                                               |
| FILTERS: [• Natural Fundus] [Red-Free Green] [CLAHE Enhanced]                                      |
| HEATMAP OPACITY: 0% [-----------------●-----------------] 100%                                     |
+---------------------------------------------------+------------------------------------------------+
| DIAGNOSTIC CANVAS (Midnight Slate #0F172A)        | CLINICAL DECISION & SIGN-OFF PANEL             |
|                                                   |                                                |
| - High-resolution canvas pan and zoom (up to 400%)| 1. Doctor Decision:                            |
| - Green-channel vascular enhancement toggle       |    (•) Agree with AI (Grade 2)                 |
| - Interactive Grad-CAM++ heatmap overlay          |    ( ) Modify Grade [Dropdown v]               |
| - Candidate lesion pins in temporal arcade        |    ( ) Request Repeat Imaging                  |
| - Foveal center marker and 1-disc-diameter ring   |    ( ) Mark Case as Closed / Non-referable     |
|                                                   |                                                |
|                                                   | 2. Clinical Findings & Prescription:           |
|                                                   |    [Textarea: Scattered blot hemorrhages in    |
|                                                   |    temporal arcade. Advise HbA1c control.]     |
|                                                   |                                                |
|                                                   | 3. Follow-up Interval: [ 3 Months v ]          |
|                                                   |                                                |
|                                                   | [ Sign with Digital Signature & Dispatch ]     |
+---------------------------------------------------+------------------------------------------------+
```

---

## 4. Persona 3: Public Health Admin & District Simulation (`/admin`)

### Screen 3.1: Public Health Surveillance & KPIs
- KPI Cards:
  - `Total Screenings Completed`: `1,420`
  - `Good Quality Rate`: `84.2%` | `Borderline (Enhanced)`: `9.4%` | `Rejected (Retaken)`: `6.4%`
  - `Referable DR Prevalence`: `28.4%` (Grade 2 to 4)
  - `AI-Doctor Concordance Rate`: `94.8%` ($\kappa = 0.912$)
  - `Uncertain Cases Routed`: `3.8%`
- Interactive Visualizations:
  - **Severity Bar Chart:** Grade 0 (680), Grade 1 (336), Grade 2 (218), Grade 3 (124), Grade 4 (62).
  - **AI vs Doctor Confusion Matrix:** Interactive heatmap displaying exact agreement cells.

---

### Screen 3.2: 100,000-Patient District Deployment Simulator
An interactive simulation engine allowing hackathon judges to stress-test district-scale rural operations:

- **Interactive Simulation Sliders:**
  1. `Number of Rural PHCs`: Slider `[ 1 - 100 ]` (Default: 50 PHCs)
  2. `Patients Screened per PHC per Day`: Slider `[ 1 - 30 ]` (Default: 8 patients)
  3. `Poor-Quality Image Rate (%)`: Slider `[ 0% - 50% ]` (Default: 15%)
  4. `Internet Bandwidth per PHC (Mbps)`: Slider `[ 0.5 - 20 Mbps ]` (Default: 4.0 Mbps)
  5. `Cloud Inference Latency (ms)`: Slider `[ 100 - 1000 ms ]` (Default: 320 ms)
  6. `Local Edge Inference Latency (ms)`: Slider `[ 50 - 500 ms ]` (Default: 110 ms)
  7. `Number of Available Ophthalmologists`: Slider `[ 1 - 10 ]` (Default: 3 doctors)
  8. `Average Doctor Review Time (mins)`: Slider `[ 1 - 10 mins ]` (Default: 4.0 mins)
  9. `Expected DR Referral Rate (%)`: Slider `[ 10% - 50% ]` (Default: 28%)

- **Real-Time Dynamic Output Metrics:**
  - `Daily Image Volume`: `400 images/day` $\rightarrow$ `Annual Capacity: 104,000 patients`
  - `Daily Rejections Filtered at PHC`: `60 images/day` (Saved doctor from viewing ungradable photos)
  - `Daily Borderline Photos Enhanced`: `80 images/day`
  - `Daily Referrals Dispatched to Doctors`: `95 cases/day`
  - `Total Doctor Review Capacity`: `135 cases/day` (Surplus capacity: queue backlog = 0)
  - `Average Patient Turnaround Time`: `3.2 hours`
  - `Cloud Storage Requirement`: `42.5 GB / month`
  - `PHC Daily Upload Bandwidth`: `36.4 MB / PHC / day`
  - `System Health Status Pill`: **`SUSTAINABLE & BALANCED (Optimal)`**

---

## 5. UI Interaction States & Responsive Breakpoints

| UI Component | Desktop Layout ($\ge 1024\text{px}$) | Tablet / Mobile Layout ($< 1024\text{px}$) | Offline Network State |
| :--- | :--- | :--- | :--- |
| **Worker Wizard** | Side-by-side Form & Dropzone | Vertical stacked cards with sticky progress footer | Top banner: *"Working Offline — Images will sync when reconnected"* |
| **IQA Feedback** | Modal dialog with high-res side-by-side | Full-screen alert sheet with large retake button | Operates locally without network dependency |
| **Doctor Cockpit** | Two-column layout: Canvas (65%) + Decision Panel (35%) | Single-column tabbed view: [View Fundus] / [Decision Form] | Queued review stored locally in IndexedDB |
| **Simulator** | Left slider rail + Right multi-chart grid | Collapsible drawer for sliders + vertical KPI stack | Simulation runs locally via client-side/Python engine |
