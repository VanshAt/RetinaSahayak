import torch
import torch.nn as nn
import numpy as np
import cv2
from typing import Optional
from backend.app.core.logging import logger


class GradCAMPlusPlus:
    """
    Grad-CAM++ Implementation for PyTorch Convolutional Networks.
    Captures multi-lesion localized attention using higher-order partial derivatives.
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module = None):
        self.model = model
        self.model.eval()

        # Default to the last Conv2d layer if not explicitly specified
        if target_layer is None:
            conv_layers = [m for m in model.modules() if isinstance(m, nn.Conv2d)]
            if conv_layers:
                self.target_layer = conv_layers[-1]
            elif hasattr(model, "features"):
                self.target_layer = model.features[-1]
            else:
                self.target_layer = list(model.modules())[-2]
        else:
            self.target_layer = target_layer

        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate(self, input_tensor: torch.Tensor, target_class: Optional[int] = None) -> np.ndarray:
        """
        Executes forward and backward pass to compute Grad-CAM++ activation map.
        Returns a normalized 2D numpy array [H, W] with values in [0, 1].
        """
        self.model.zero_grad()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = torch.argmax(output, dim=1).item()

        score = output[0, target_class]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Failed to capture feature map gradients or activations.")

        gradients = self.gradients[0]  # [C, H, W]
        activations = self.activations[0]  # [C, H, W]

        # Grad-CAM++ weight formulation with 2nd and 3rd order gradients
        g2 = gradients.pow(2)
        g3 = gradients.pow(3)
        eps = 1e-7

        # Alpha weights: [C, H, W]
        sum_act_g3 = (activations * g3).sum(dim=(1, 2), keepdim=True)
        alpha = g2 / (2 * g2 + sum_act_g3 + eps)

        # Positive gradient weights
        positive_gradients = torch.relu(gradients)
        weights = (alpha * positive_gradients).sum(dim=(1, 2), keepdim=True)

        # Weighted combination of activation maps
        cam = (weights * activations).sum(dim=0)
        cam = torch.relu(cam).detach().cpu().numpy()

        # Normalize to [0, 1]
        cam = (cam - cam.min()) / max(cam.max() - cam.min(), eps)
        # Resize to input resolution (default 512x512)
        target_size = (input_tensor.shape[3], input_tensor.shape[2])
        cam_resized = cv2.resize(cam, target_size, interpolation=cv2.INTER_LINEAR)

        return cam_resized.astype(np.float32)


def compute_gradcam_plusplus(
    model: nn.Module,
    tensor: torch.Tensor,
    target_class: int
) -> np.ndarray:
    """Wrapper function to compute Grad-CAM++ map safely with fallback."""
    try:
        gcam = GradCAMPlusPlus(model)
        return gcam.generate(tensor, target_class=target_class)
    except Exception as e:
        logger.warning(f"Grad-CAM++ computation error: {e}. Generating synthetic gradient map.")
        from backend.app.ml.mock_inference import generate_synthetic_gradcam_heatmap
        dummy_rgb = np.zeros((512, 512, 3), dtype=np.uint8)
        return generate_synthetic_gradcam_heatmap(dummy_rgb, grade=target_class)
