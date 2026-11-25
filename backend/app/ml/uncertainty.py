import math
from typing import Dict, Any, List
from backend.app.core.config import settings


def calculate_predictive_uncertainty(
    probabilities: Dict[str, float],
    confidence_threshold: float = None
) -> Dict[str, Any]:
    """
    Computes Shannon entropy and softmax margin to quantify predictive uncertainty.
    Flags low-confidence or high-entropy predictions for human-in-the-loop review.
    """
    threshold = confidence_threshold or settings.UNCERTAINTY_CONFIDENCE_THRESHOLD
    probs: List[float] = list(probabilities.values())

    # Sort probabilities in descending order
    sorted_probs = sorted(probs, reverse=True)
    top1 = sorted_probs[0]
    top2 = sorted_probs[1] if len(sorted_probs) > 1 else 0.0

    # 1. Softmax probability margin
    margin = float(top1 - top2)

    # 2. Shannon Entropy: H = -sum(p * log2(p)) / log2(K)
    k = len(probs)
    max_entropy = math.log2(k) if k > 1 else 1.0
    epsilon = 1e-9

    entropy_val = 0.0
    for p in probs:
        if p > 0:
            entropy_val -= p * math.log2(max(p, epsilon))

    normalized_entropy = float(entropy_val / max_entropy) if max_entropy > 0 else 0.0

    # 3. Decision Rule for Uncertainty
    is_uncertain = False
    reasons = []

    if top1 < threshold:
        is_uncertain = True
        reasons.append(f"Top class confidence ({round(top1 * 100, 1)}%) is below diagnostic certainty threshold ({round(threshold * 100, 1)}%).")

    if normalized_entropy > 0.80:
        is_uncertain = True
        reasons.append("High predictive entropy across adjacent DR grades.")

    if margin < 0.22 and top1 < 0.75:
        is_uncertain = True
        reasons.append("Narrow probability margin between top two predicted diagnoses.")

    routing_reason = " ".join(reasons) if is_uncertain else "Prediction confidence is within diagnostic threshold."

    return {
        "is_uncertain": is_uncertain,
        "uncertainty_score": round(normalized_entropy, 3),
        "margin": round(margin, 3),
        "entropy": round(entropy_val, 3),
        "routing_reason": routing_reason
    }
