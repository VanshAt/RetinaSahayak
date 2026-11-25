import cv2
import numpy as np
import torch


def crop_retinal_roi(img_rgb: np.ndarray, tol: int = 10) -> np.ndarray:
    """
    Detects the luminous circular retinal fundus boundary and crops away
    excess black outer margins.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    mask = gray > tol

    # If mask has valid foreground pixels, compute bounding box
    if np.any(mask):
        row_indices, col_indices = np.where(mask)
        ymin, ymax = row_indices.min(), row_indices.max()
        xmin, xmax = col_indices.min(), col_indices.max()
        # Ensure minimum aspect
        if ymax > ymin and xmax > xmin:
            cropped = img_rgb[ymin:ymax, xmin:xmax]
            return cropped

    return img_rgb


def preprocess_fundus_image(
    img_rgb: np.ndarray,
    target_size: tuple[int, int] = (512, 512)
) -> tuple[np.ndarray, torch.Tensor]:
    """
    Full preprocessing pipeline for neural network ingestion:
    1. Crops away black margins around fundus disc.
    2. Resizes to target dimension (default 512x512).
    3. Normalizes to PyTorch tensor [1, 3, H, W] with standard ImageNet statistics.

    Returns:
        (preprocessed_rgb_numpy, normalized_tensor)
    """
    cropped = crop_retinal_roi(img_rgb)
    resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)

    # Convert to float32 [0, 1]
    norm_float = resized.astype(np.float32) / 255.0

    # ImageNet Mean & Std normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    standardized = (norm_float - mean) / std

    # Reshape to [1, 3, H, W] tensor
    tensor = torch.from_numpy(standardized.transpose(2, 0, 1)).unsqueeze(0).float()

    return resized, tensor
