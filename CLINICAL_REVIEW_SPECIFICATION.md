# Clinical Review Specification & Protocol

**System:** RetinaSahayak (रेटिना सहायक)  
**Version:** 1.0 (Phase 4 Verified)  
**Standard:** Clinical Decision Support System (CDSS) Tele-Ophthalmology Review Protocol

---

## 1. Review Data Model

| Field | Type | Description | Mandatory / Constraint |
| :--- | :--- | :--- | :--- |
| `review_id` | UUID (36) | Primary Key | Generated |
| `referral_id` | UUID (36) | Foreign Key to `referrals` | Indexed |
| `screening_id` | UUID (36) | Foreign Key to `screenings` | Unique |
| `ophthalmologist_id` | UUID (36) | Foreign Key to reviewing doctor | Indexed |
| `ai_predicted_grade` | Integer | Original model prediction (0–4) | Stored at review time |
| `ai_confidence` | Float | Model confidence score (0.0–1.0) | Stored at review time |
| `final_grade` | Integer | Doctor confirmed grade (0–4) | Mandatory if `MODIFY_GRADE` |
| `clinical_decision` | Enum | Formal clinical decision | One of 7 valid options |
| `clinical_notes` | Text | Clinical observations and rationale | Mandatory for specified decisions |
| `agrees_with_ai` | Boolean | Concordance flag (`final_grade == ai_predicted_grade`) | Automatic calculation |
| `digital_signature_hash` | String (64) | SHA-256 cryptographic signature | Generated |
| `reviewed_at` | DateTime (UTC)| Timestamp of review signature | Automatic |
| `review_status` | Enum | `COMPLETED` or `AMENDED` | Default `COMPLETED` |

---

## 2. Decision Options & Validation Rules

```
Decision Enum                     Mandates final_grade?    Mandates clinical_notes?    Referral Status Transition
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
AGREE_WITH_AI                     No (Defaults to AI)      Optional                    REVIEWED
MODIFY_GRADE                      YES (0, 1, 2, 3, or 4)   YES (Min 3 chars)           REVIEWED
REQUEST_REPEAT_IMAGING            No                       YES (Min 3 chars)           REVIEWED
MARK_NON_REFERABLE                No                       YES (Min 3 chars)           CLOSED
MARK_REFERABLE                    No                       YES (Min 3 chars)           REVIEWED
MARK_FOLLOW_UP_REQUIRED           No                       YES (Min 3 chars)           REVIEWED
CLOSE_CASE                        No                       YES (Min 3 chars)           CLOSED
```

---

## 3. Review Single-Submission Guarantee

- A referral can be reviewed only **once** by an ophthalmologist.
- Any subsequent attempt to submit a review returns **`400 Bad Request`**:
  `"A clinical review has already been submitted and signed for this referral."`
- Administrative corrections or reopenings require explicit administrative oversight and generate an `AMENDED` status with audit trail logging.

---

## 4. Digital Signature & Non-Repudiation

When a clinical review is submitted, a SHA-256 digital signature is calculated over:
```python
sig_entropy = (
    f"DOCTOR:{doctor_user.id}|REF:{ref.id}|SCR:{ref.screening_id}|"
    f"GRADE:{final_grade}|DECISION:{decision}|NOTES:{notes}|TIME:{now.isoformat()}"
)
signature_hash = hashlib.sha256(sig_entropy.encode("utf-8")).hexdigest()
```
The signature is stored on the `ClinicalReview` record and can be independently verified by the administrative oversight console or export reports.
