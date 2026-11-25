import io
from PIL import Image
import numpy as np


def validate_image_file(file_bytes: bytes, filename: str) -> tuple[bool, str, int, int]:
    """
    Validates file format, attempts PIL decode, and returns (is_valid, error_msg, width, height).
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        return False, f"Unsupported file format '{ext}'. Supported: JPG, PNG, TIFF.", 0, 0

    if len(file_bytes) > 15 * 1024 * 1024:  # 15MB limit per non-functional requirements
        return False, "File size exceeds 15MB maximum limit.", 0, 0

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
        with Image.open(io.BytesIO(file_bytes)) as img:
            w, h = img.size
            if w < 400 or h < 400:
                return False, f"Image resolution ({w}x{h}) is too low for retinal diagnosis. Minimum is 400x400.", w, h
            return True, "", w, h
    except Exception as e:
        return False, f"Corrupted or invalid image file: {str(e)}", 0, 0


def bytes_to_numpy(file_bytes: bytes) -> np.ndarray:
    """Decodes image bytes to RGB numpy array."""
    with Image.open(io.BytesIO(file_bytes)) as img:
        return np.array(img.convert("RGB"))


def numpy_to_jpeg_bytes(img_arr: np.ndarray, quality: int = 92) -> bytes:
    """Encodes RGB numpy array to JPEG bytes."""
    pil_img = Image.fromarray(img_arr.astype(np.uint8))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
