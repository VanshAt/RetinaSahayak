from typing import Dict, Any, List


def generate_clinical_rationale(
    grade: int,
    lesion_evidence: Dict[str, Any],
    dme_risk: Dict[str, Any],
    is_uncertain: bool = False
) -> tuple[str, str]:
    """
    Generates plain-language clinical explanation and recommended action
    conforming to clinical decision support standards.

    Returns:
        (clinical_explanation, recommended_action)
    """
    quads = lesion_evidence.get("suspicious_quadrants", [])
    quad_str = ", ".join([q.replace("_", " ").title() for q in quads[:2]]) if quads else "posterior retina"

    # Base Rationale by ICDR Grade per Phase 3 Clinical Rules:
    if grade == 0:
        explanation = (
            "No high-confidence features associated with referable diabetic retinopathy were identified. "
            "Grad-CAM visual explanation reflects regions that influenced the model's prediction."
        )
        recommendation = "Continue annual routine diabetic eye screening at Primary Health Centre."

    elif grade == 1:
        explanation = (
            "The model identified limited features consistent with mild non-proliferative diabetic retinopathy. "
            "This grade is non-referable under the current screening policy. "
            "Visual explanation highlights regions that influenced the model's prediction."
        )
        recommendation = "Follow-up eye check at Primary Health Centre in 6 to 12 months. Maintain strict blood sugar control."

    elif grade == 2:
        explanation = (
            "The model identified features consistent with moderate non-proliferative diabetic retinopathy. "
            "This case is referable for ophthalmologist review. "
            "Visual explanation highlights regions that influenced the model's prediction."
        )
        recommendation = "Refer to tele-ophthalmologist for confirmatory examination within 30 days."

    elif grade == 3:
        explanation = (
            "The model identified features consistent with severe non-proliferative diabetic retinopathy. "
            "Urgent ophthalmologist review is recommended. "
            "Visual explanation highlights regions that influenced the model's prediction."
        )
        recommendation = "Urgent referral to ophthalmologist within 7 days for dilated evaluation and possible laser assessment."

    elif grade == 4:
        explanation = (
            "The model identified features consistent with proliferative diabetic retinopathy. "
            "Urgent ophthalmologist review is required. "
            "Visual explanation highlights regions that influenced the model's prediction."
        )
        recommendation = "Emergency tertiary hospital referral (< 48 hours). Immediate specialist evaluation required to prevent vision loss."

    else:
        explanation = "Preliminary automated screening evaluation completed."
        recommendation = "Consult an eye specialist for comprehensive examination."

    # Incorporate Uncertainty notice (Safe screening threshold rule)
    if is_uncertain:
        explanation = (
            "The model confidence is below the safe screening threshold. "
            "This case has been routed for ophthalmologist review. "
            "Visual explanation highlights regions that influenced the model's prediction."
        )
        recommendation = "Priority tele-ophthalmologist review required due to model predictive uncertainty."

    return explanation, recommendation


def get_clinical_rationale(grade: int, is_uncertain: bool = False) -> str:
    explanation, _ = generate_clinical_rationale(grade, {}, {}, is_uncertain=is_uncertain)
    return explanation


def get_recommended_action(grade: int, is_uncertain: bool = False) -> str:
    _, recommendation = generate_clinical_rationale(grade, {}, {}, is_uncertain=is_uncertain)
    return recommendation


