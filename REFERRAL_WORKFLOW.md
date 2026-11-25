# Referral Workflow Specification: Tele-Ophthalmology Cockpit

**System:** RetinaSahayak (रेटिना सहायक)  
**Version:** 1.0 (Phase 4 Verified)  
**Purpose:** Standard Operating Procedure (SOP) and technical specification for automated referral generation, clinical prioritization, ophthalmologist review, escalation, and closure.

---

## 1. Automated Referral Creation Rules

Referrals are automatically created during screening analysis when:
1. **Referable Disease:**
   - **Grade 2 (Moderate NPDR):** Confidence $\ge 0.65$
   - **Grade 3 (Severe NPDR):** Confidence $\ge 0.65$
   - **Grade 4 (Proliferative DR):** Confidence $\ge 0.65$
2. **Predictive Uncertainty:**
   - Any grade with confidence $< 0.65$ or Shannon entropy $> 0.85$.

### Non-Referral Rules:
- **Grade 0 (No DR)** with confidence $\ge 0.65$ $\rightarrow$ Non-referable, annual routine screening recommendation, **no referral created**.
- **Grade 1 (Mild NPDR)** with confidence $\ge 0.65$ $\rightarrow$ Non-referable, 6–12 month follow-up recommendation, **no referral created**.

---

## 2. Priority Matrix

| Predicted Condition / Severity | Assigned Priority | Target Review SLA | Queue Display Order |
| :--- | :---: | :---: | :---: |
| **Grade 4 (Proliferative DR)** | `CRITICAL` | $< 24$ hours | 1 (Top of Queue) |
| **Grade 3 (Severe NPDR)** | `HIGH` | $< 72$ hours | 2 |
| **Grade 2 (Moderate NPDR)** | `MEDIUM` | $< 30$ days | 3 |
| **Uncertain Case (< 0.65 Conf / High Entropy)** | `REVIEW_REQUIRED` | $< 48$ hours | 4 |

---

## 3. Referral Lifecycle Statuses

```
              [Screening Analyzed]
                       │
             ┌─────────┴─────────┐
             │ Referable/Uncert? │
             └─────────┬─────────┘
                       │ Yes
                       ▼
                   [PENDING]
                       │
       ┌───────────────┼───────────────┐
       │ Ophthalmologist reviews case  │
       ▼                               ▼
  [IN_REVIEW]                    [ESCALATED] (Tertiary Transfer)
       │                               │
       ├───────────────────────────────┤
       ▼                               ▼
  [REVIEWED]                       [CLOSED]
(Signed Clinical Review)       (Clinically resolved / Mark non-referable)
```

1. **`PENDING`:** Automatically created upon analysis; waiting for ophthalmologist assignment.
2. **`IN_REVIEW`:** Opened and under active examination by an ophthalmologist.
3. **`REVIEWED`:** Formal clinical review submitted and signed.
4. **`ESCALATED`:** Transferred to a tertiary eye hospital or emergency vitreo-retinal unit.
5. **`CLOSED`:** Case resolved or marked non-referable.

---

## 4. Clinical Review Workflow

Ophthalmologists review full multimodal evidence through `GET /api/v1/ophthalmologist/referrals/{referral_id}`:
- Original & enhanced fundus photographs
- Grad-CAM++ decision-support activation map & overlay
- Class probabilities distribution ($P_0$ through $P_4$)
- Model confidence and uncertainty classification
- AI clinical explanation & recommended triage action
- Inference engine attribution (`MOCK_INFERENCE` vs `PYTORCH_EFFICIENTNET`)

### Decision Options (`POST /api/v1/ophthalmologist/referrals/{id}/review`):
- `AGREE_WITH_AI`
- `MODIFY_GRADE` (Mandates `final_grade` and `clinical_notes`)
- `REQUEST_REPEAT_IMAGING` (Mandates `clinical_notes`)
- `MARK_NON_REFERABLE` (Closes case; mandates `clinical_notes`)
- `MARK_REFERABLE` (Mandates `clinical_notes`)
- `MARK_FOLLOW_UP_REQUIRED` (Mandates `clinical_notes`)
- `CLOSE_CASE` (Closes case; mandates `clinical_notes`)

---

## 5. Case Escalation Workflow

When sight-threatening conditions or secondary complications are identified:
- **Endpoint:** `POST /api/v1/ophthalmologist/referrals/{referral_id}/escalate`
- **Supported Reasons:**
  - `REQUIRES_SECOND_OPINION`
  - `SUSPECTED_PROLIFERATIVE_DR`
  - `POSSIBLE_DME_FUTURE_EVALUATION` *(Described strictly as a future clinical evaluation flag, not an AI-detected diagnosis)*
  - `IMAGE_QUALITY_CONCERN`
  - `TECHNICAL_ISSUE`
  - `OTHER`
- **Behavior:** Status updates to `ESCALATED`, target tertiary hospital recorded, audit log action `REFERRAL_ESCALATED` logged.

---

## 6. Case Closure Workflow

- **Endpoint:** `POST /api/v1/ophthalmologist/referrals/{referral_id}/close`
- **Requirements:** Mandatory `close_reason` and detailed `clinical_notes`.
- **Behavior:** Status updates to `CLOSED`, sets `closed_at` and `closed_by`. Preserved under `CLOSED` filter for compliance and quality audit.
- **Audit:** Audit log action `REFERRAL_CLOSED` logged.

---

## 7. Audit Trail & Security Matrix

All actions produce cryptographic SHA-256 payload integrity signatures:
- `REFERRAL_CREATED`
- `REFERRAL_VIEWED`
- `REFERRAL_QUEUE_ACCESSED`
- `CLINICAL_REVIEW_SUBMITTED`
- `CLINICAL_REVIEW_SIGNED`
- `REFERRAL_ESCALATED`
- `REFERRAL_CLOSED`
- `UNAUTHORIZED_ACCESS_ATTEMPT`

### RBAC Matrix:
| Role | Access Queue | View Detail | Review / Sign | Escalate | Close | Cross-Facility Access |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PHC Worker** | ❌ (403) | ❌ (403 if other PHC) | ❌ (403) | ❌ (403) | ❌ (403) | ❌ Blocked & Logged |
| **Ophthalmologist** | ✅ | ✅ | ✅ | ✅ | ✅ | Allowed (District Queue) |
| **Admin** | ✅ | ✅ | Reopen / Correct | ✅ | ✅ | Full Oversight |
