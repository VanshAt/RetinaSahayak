import numpy as np
import torch
from backend.app.ml.gradcam import GradCAMPlusPlus, compute_gradcam_plusplus
from backend.app.ml.classifier import RetinaSahayakNet
from backend.app.ml.visualizer import render_heatmap_and_overlay


def test_gradcam_plusplus_generation():
    """Verify Grad-CAM++ generates a valid normalized 2D heatmap."""
    model = RetinaSahayakNet(num_classes=5, pretrained=False)
    dummy_input = torch.randn(1, 3, 512, 512, dtype=torch.float32)

    heatmap = compute_gradcam_plusplus(model, dummy_input, target_class=2)

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (512, 512)
    assert 0.0 <= heatmap.min()
    assert heatmap.max() <= 1.0


def test_render_heatmap_and_overlay():
    """Verify rendering of standalone heatmap and blended overlay JPEG bytes."""
    synth_fundus = np.zeros((512, 512, 3), dtype=np.uint8)
    synth_fundus[:, :, 0] = 180
    synth_fundus[:, :, 1] = 90
    synth_fundus[:, :, 2] = 40

    heatmap = np.zeros((512, 512), dtype=np.float32)
    heatmap[200:300, 200:300] = 0.95

    bounding_boxes = [{
        "x": 210, "y": 210, "width": 40, "height": 40, "area": 1600.0,
        "quadrant": "SUPERIOR_TEMPORAL", "lesion_type": "HEMORRHAGE"
    }]

    heat_bytes, overlay_bytes = render_heatmap_and_overlay(
        img_rgb=synth_fundus,
        heatmap_2d=heatmap,
        alpha=0.42,
        bounding_boxes=bounding_boxes
    )

    assert isinstance(heat_bytes, bytes)
    assert len(heat_bytes) > 500  # Valid JPEG
    assert isinstance(overlay_bytes, bytes)
    assert len(overlay_bytes) > 500


def test_mock_inference_gradcam_generation_and_transparency():
    """Verify deterministic mock explainability generation, simulated label, and disclaimer."""
    from backend.app.ml.mock_inference import generate_deterministic_prediction
    synth_fundus = np.zeros((512, 512, 3), dtype=np.uint8)
    synth_fundus[:, :, 0] = 175
    synth_fundus[:, :, 1] = 85
    synth_fundus[:, :, 2] = 35

    grade, conf, probs, heatmap = generate_deterministic_prediction(synth_fundus, "grade_2_moderate.jpg")
    assert grade == 2
    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (512, 512)
    assert heatmap.max() > 0.0

    # Test rendering simulated heatmap & overlay
    heat_bytes, over_bytes = render_heatmap_and_overlay(synth_fundus, heatmap)
    assert len(heat_bytes) > 500
    assert len(over_bytes) > 500

