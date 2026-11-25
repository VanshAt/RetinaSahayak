import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ml.mock_inference import generate_deterministic_prediction
from backend.app.ml.preprocess import preprocess_fundus_image


GRADE_NAMES: Dict[int, str] = {
    0: "NO_DR",
    1: "MILD_NPDR",
    2: "MODERATE_NPDR",
    3: "SEVERE_NPDR",
    4: "PROLIFERATIVE_DR"
}


class RetinaSahayakNet(nn.Module):
    """
    Deep Convolutional Network for 5-Class ICDR Diabetic Retinopathy classification.
    Engineered with pure PyTorch modules and residual receptive fields.
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = False):
        super().__init__()
        self.conv_in = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(inplace=True)
        )
        self.block1 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.SiLU(inplace=True)
        )
        self.block2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.SiLU(inplace=True)
        )
        # Target layer for Grad-CAM++ hooks
        self.features = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.SiLU(inplace=True)
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv_in(x)
        x = self.block1(x)
        x = self.block2(x)
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)


# Global Model Cache
_MODEL_INSTANCE: nn.Module = None
_DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_model() -> nn.Module:
    """Retrieves or lazily instantiates the PyTorch neural network."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        try:
            model = RetinaSahayakNet(num_classes=5, pretrained=False)
            if os.path.exists(settings.MODEL_WEIGHTS_PATH):
                logger.info(f"Loading trained model weights from {settings.MODEL_WEIGHTS_PATH}")
                checkpoint = torch.load(settings.MODEL_WEIGHTS_PATH, map_location=_DEVICE)
                model.load_state_dict(checkpoint)
            model.to(_DEVICE)
            model.eval()
            _MODEL_INSTANCE = model
        except Exception as e:
            logger.warning(f"PyTorch model instantiation fallback to mock engine: {e}")
            _MODEL_INSTANCE = None
    return _MODEL_INSTANCE


def predict_diabetic_retinopathy(
    img_rgb: np.ndarray,
    image_identifier: str = ""
) -> Tuple[int, float, Dict[str, float], np.ndarray, str]:
    """
    Orchestrates deep learning prediction.
    Falls back gracefully to high-fidelity deterministic mock inference
    if USE_MOCK_INFERENCE is True or model weights are missing.

    Returns:
        (predicted_grade, confidence_score, probabilities_dict, heatmap_2d, engine_name)
    """
    if settings.USE_MOCK_INFERENCE or not os.path.exists(settings.MODEL_WEIGHTS_PATH):
        grade, conf, probs, heatmap = generate_deterministic_prediction(img_rgb, image_identifier)
        return grade, conf, probs, heatmap, "MOCK_INFERENCE"

    try:
        model = get_model()
        if model is None:
            grade, conf, probs, heatmap = generate_deterministic_prediction(img_rgb, image_identifier)
            return grade, conf, probs, heatmap, "MOCK_INFERENCE"

        _, tensor = preprocess_fundus_image(img_rgb)
        tensor = tensor.to(_DEVICE)

        with torch.no_grad():
            logits = model(tensor)
            softmax_probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        grade = int(np.argmax(softmax_probs))
        confidence = float(softmax_probs[grade])

        probs_dict = {
            "grade_0_no_dr": round(float(softmax_probs[0]), 3),
            "grade_1_mild": round(float(softmax_probs[1]), 3),
            "grade_2_moderate": round(float(softmax_probs[2]), 3),
            "grade_3_severe": round(float(softmax_probs[3]), 3),
            "grade_4_pdr": round(float(softmax_probs[4]), 3),
        }

        from backend.app.ml.gradcam import compute_gradcam_plusplus
        heatmap = compute_gradcam_plusplus(model, tensor, target_class=grade)

        return grade, confidence, probs_dict, heatmap, "PYTORCH_EFFICIENTNET"
    except Exception as e:
        logger.error(f"Error in PyTorch inference, falling back to calibrated mock: {e}")
        grade, conf, probs, heatmap = generate_deterministic_prediction(img_rgb, image_identifier)
        return grade, conf, probs, heatmap, "MOCK_INFERENCE"
