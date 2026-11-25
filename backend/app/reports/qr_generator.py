import io
import qrcode
from typing import Optional


def generate_verification_qr_bytes(
    screening_id: str,
    patient_code: str,
    grade: int,
    verification_hash: Optional[str] = None
) -> bytes:
    """
    Generates a secure verification QR code in PNG format for embedding into PDF reports.
    Allows rural patients and referral doctors to instantly scan and verify screening authenticity.
    """
    short_hash = (verification_hash or "PENDING_VERIFICATION")[:16]
    verify_url = (
        f"https://retinasahayak.in/verify"
        f"?sid={screening_id}&pid={patient_code}&g={grade}&vh={short_hash}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
