import os
from pathlib import Path
import torch
from backend.app.ml.classifier import RetinaSahayakNet
from backend.app.core.logging import logger


def export_model_to_onnx(output_path: str = "simulink/retinasahayak_efficientnet.onnx") -> str:
    """
    Exports the RetinaSahayak PyTorch classification model to standard ONNX format
    for direct import into the MathWorks MATLAB Deep Learning Toolbox.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    model = RetinaSahayakNet(num_classes=5)
    model.eval()

    dummy_input = torch.randn(1, 3, 512, 512, dtype=torch.float32)

    torch.onnx.export(
        model,
        dummy_input,
        str(out_file),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["fundus_tensor"],
        output_names=["grade_logits"],
        dynamic_axes={"fundus_tensor": {0: "batch_size"}, "grade_logits": {0: "batch_size"}},
        dynamo=False
    )

    logger.info(f"Model exported to ONNX format at: {out_file}")
    return str(out_file)


if __name__ == "__main__":
    export_model_to_onnx()
