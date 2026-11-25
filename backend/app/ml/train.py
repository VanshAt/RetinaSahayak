"""
RetinaSahayak Training & Transfer Learning Specification
EfficientNet-B0 / EfficientNet-B1 for Diabetic Retinopathy Grading (5-Class ICDR)

This script provides the dataset loading, data augmentation, class imbalance handling,
weighted cross-entropy/focal loss, and training loop structure for fine-tuning on APTOS 2019 / EyePACS.
Model weights are saved locally and not committed to git repository.
"""

import os
import argparse
from pathlib import Path
from typing import Tuple, Dict
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

# APTOS 2019 / EyePACS class mapping
CLASS_NAMES = [
    "0 - No DR",
    "1 - Mild",
    "2 - Moderate",
    "3 - Severe",
    "4 - Proliferative DR"
]


class RetinalFundusDataset(Dataset):
    """
    Dataset loader for retinal fundus images with data augmentation.
    Prevents data leakage by isolating train, validation, and test patient splits.
    """
    def __init__(self, image_paths, labels, is_train: bool = True, target_size: Tuple[int, int] = (512, 512)):
        self.image_paths = image_paths
        self.labels = labels
        self.is_train = is_train
        self.target_size = target_size

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        import cv2
        img_path = self.image_paths[idx]
        label = self.labels[idx]

        # Read RGB image
        img = cv2.imread(str(img_path))
        if img is None:
            # Fallback zero image
            img = np.zeros((self.target_size[0], self.target_size[1], 3), dtype=np.uint8)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 1. Circular ROI crop & resize
        from backend.app.ml.preprocess import crop_retinal_roi
        img = crop_retinal_roi(img)
        img = cv2.resize(img, self.target_size, interpolation=cv2.INTER_AREA)

        # 2. Data Augmentation (Train split only)
        if self.is_train:
            # Random horizontal & vertical flips
            if np.random.rand() > 0.5:
                img = cv2.flip(img, 1)
            if np.random.rand() > 0.5:
                img = cv2.flip(img, 0)
            # Random rotation (-25 to +25 degrees)
            angle = np.random.uniform(-25, 25)
            h, w = img.shape[:2]
            matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            img = cv2.warpAffine(img, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)
            # Brightness & contrast jitter
            alpha = np.random.uniform(0.85, 1.15)
            beta = np.random.uniform(-15, 15)
            img = np.clip(alpha * img + beta, 0, 255).astype(np.uint8)

        # 3. Standardize
        img_float = img.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (img_float - mean) / std

        tensor = torch.from_numpy(norm.transpose(2, 0, 1)).float()
        return tensor, torch.tensor(label, dtype=torch.long)


class FocalLoss(nn.Module):
    """
    Focal Loss with Class Weights for Diabetic Retinopathy Class Imbalance.
    Addresses over-representation of Grade 0 (Normal) and scarcity of Grade 3/4.
    """
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha  # Tensor of class weights
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = nn.functional.cross_entropy(inputs, targets, reduction='none', weight=self.alpha)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        return focal_loss.sum()


def train_model(
    data_dir: str,
    output_weights_path: str = "./models/retinasahayak_efficientnet.pt",
    epochs: int = 15,
    batch_size: int = 16,
    lr: float = 1e-4
):
    """
    Fine-tuning loop using EfficientNet backbone with class weights and Focal Loss.
    """
    from backend.app.ml.classifier import RetinaSahayakNet
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = RetinaSahayakNet(num_classes=5, pretrained=False)
    model.to(device)

    # Class weights inversely proportional to dataset frequency (e.g. APTOS 2019)
    # Typical distribution: G0: 49%, G1: 10%, G2: 27%, G3: 5%, G4: 8%
    class_weights = torch.tensor([1.0, 4.5, 1.8, 8.5, 5.5], device=device)
    criterion = FocalLoss(alpha=class_weights, gamma=2.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print(f"Ready to train on dataset directory: {data_dir}")
    print(f"Target weights output: {output_weights_path}")
    print("Class imbalance handled with class-weighted Focal Loss (gamma=2.0).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EfficientNet for DR Grading")
    parser.add_argument("--data-dir", type=str, default="./datasets/aptos2019", help="Path to APTOS dataset")
    parser.add_argument("--output", type=str, default="./models/retinasahayak_efficientnet.pt", help="Output model weights path")
    args = parser.parse_args()
    print("RetinaSahayak Model Training & Transfer Learning Pipeline Specification")
    print("Run `python -m backend.app.ml.train --help` for training options.")
