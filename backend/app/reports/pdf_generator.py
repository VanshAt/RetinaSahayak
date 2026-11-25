import io
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.screening import Screening
from backend.app.models.patient import Patient
from backend.app.models.health_center import HealthCenter
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.fundus_image import FundusImage
from backend.app.models.explainability_map import ExplainabilityMap
from backend.app.models.referral import Referral
from backend.app.models.clinical_review import ClinicalReview
from backend.app.services.storage.factory import get_storage_provider
from backend.app.reports.qr_generator import generate_verification_qr_bytes
from backend.app.core.logging import logger


FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

try:
    if os.path.exists("C:/Windows/Fonts/Nirmala.ttc"):
        pdfmetrics.registerFont(TTFont("Nirmala", "C:/Windows/Fonts/Nirmala.ttc", subfontIndex=0))
        pdfmetrics.registerFont(TTFont("Nirmala-Bold", "C:/Windows/Fonts/Nirmala.ttc", subfontIndex=0))
        FONT_REGULAR = "Nirmala"
        FONT_BOLD = "Nirmala-Bold"
except Exception as e:
    logger.warning(f"Could not load Nirmala font: {e}. Falling back to standard Helvetica.")


GRADE_COLORS = {
    0: colors.HexColor("#16A34A"),  # Green
    1: colors.HexColor("#2563EB"),  # Blue
    2: colors.HexColor("#D97706"),  # Amber
    3: colors.HexColor("#EA580C"),  # Orange
    4: colors.HexColor("#DC2626"),  # Red
}

GRADE_LABELS_EN = {
    0: "Grade 0 — No Diabetic Retinopathy (Normal)",
    1: "Grade 1 — Mild Non-Proliferative DR (Mild NPDR)",
    2: "Grade 2 — Moderate Non-Proliferative DR (Moderate NPDR)",
    3: "Grade 3 — Severe Non-Proliferative DR (Severe NPDR)",
    4: "Grade 4 — Proliferative Diabetic Retinopathy (PDR)",
}


def _create_blank_image(width_px: int = 400, height_px: int = 400, text: str = "Image") -> bytes:
    """Generates an in-memory JPEG placeholder if storage image is missing."""
    import cv2
    import numpy as np
    from backend.app.utils.image_utils import numpy_to_jpeg_bytes
    img = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    img[:, :] = [30, 41, 59]  # Dark slate background
    cv2.putText(
        img,
        text,
        (20, height_px // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (203, 213, 225),
        1,
        cv2.LINE_AA
    )
    return numpy_to_jpeg_bytes(img, quality=85)


def generate_screening_pdf(db: Session, screening_id: str) -> bytes:
    """
    Generates a clean, professional 2-page A4 medical report.
    Page 1: Demographics, Screening Info, Original & Enhanced Images, IQA metrics & recapture guidance.
    Page 2: Predicted DR grade, probabilities, confidence, uncertainty & referral status,
            Grad-CAM++ heatmap & overlay, clinical explanation, recommended action,
            engine attribution, QR verification code, and CDSS disclaimer.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening with ID '{screening_id}' not found."
        )

    patient = db.query(Patient).filter(Patient.id == screening.patient_id).first()
    center = db.query(HealthCenter).filter(HealthCenter.id == screening.health_center_id).first()
    ai_ana = db.query(AIAnalysis).filter(AIAnalysis.screening_id == screening.id).first()
    img_entity = db.query(FundusImage).filter(FundusImage.screening_id == screening.id).first()
    xai = db.query(ExplainabilityMap).filter(ExplainabilityMap.ai_analysis_id == ai_ana.id).first() if ai_ana else None
    referral = db.query(Referral).filter(Referral.screening_id == screening.id).first()
    review = db.query(ClinicalReview).filter(ClinicalReview.screening_id == screening.id).first()

    storage = get_storage_provider()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#1E3A8A")
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=5,
        spaceAfter=3
    )
    cell_label = ParagraphStyle(
        "CellLabel",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#64748B")
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )
    cell_val_bold = ParagraphStyle(
        "CellValBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )
    body_text = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )
    caption_style = ParagraphStyle(
        "ImgCaption",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=8.5,
        alignment=1,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # ================= PAGE 1 =================
    # 1. Header
    report_title = "AI-Assisted Diabetic Retinopathy Screening Report"
    header_data = [
        [
            Paragraph(f"<b>RetinaSahayak</b> | {report_title}", title_style),
            Paragraph(f"<b>Report ID:</b> {screening.id[:8].upper()}<br/><b>Date:</b> {screening.created_at.strftime('%d-%b-%Y %H:%M')}", cell_val)
        ],
        [
            Paragraph("Community Health Mission • Primary Eye Care Tele-Screening Network", subtitle_style),
            Paragraph(f"<b>PHC Location:</b> {center.name if center else (screening.patient.phc_location if screening.patient else 'Primary Health Centre')}", cell_val)
        ]
    ]
    header_table = Table(header_data, colWidths=[370, 150])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=4, spaceAfter=6))

    # 2. Patient Demographics & Encounter Info
    pat_code = patient.patient_code if patient else "N/A"
    age_grp = patient.age_group if patient else "N/A"
    gender = patient.gender if patient else "N/A"
    diab_dur = f"{patient.diabetes_duration_years} years" if (patient and patient.diabetes_duration_years is not None) else "N/A"
    eye = "Right Eye (OD)" if screening.eye_side == "OD" else "Left Eye (OS)"
    dilation = screening.dilation_status or "UNDILATED"

    demographics_data = [
        [
            Paragraph("Anonymized Patient ID", cell_label),
            Paragraph("Age Group & Gender", cell_label),
            Paragraph("Diabetes Duration", cell_label),
            Paragraph("Eye Side & Dilation", cell_label),
        ],
        [
            Paragraph(f"<b>{pat_code}</b>", cell_val_bold),
            Paragraph(f"{age_grp} / {gender}", cell_val),
            Paragraph(f"{diab_dur}", cell_val),
            Paragraph(f"<b>{eye}</b> ({dilation})", cell_val_bold),
        ]
    ]
    demo_table = Table(demographics_data, colWidths=[130, 130, 130, 130])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 6))

    # 3. Fundus Photographs Panel (Page 1)
    story.append(Paragraph("Retinal Fundus Photography", heading_style))

    img_w, img_h = 245, 175

    def load_rl_image(rel_path: Optional[str], fallback_label: str) -> RLImage:
        data = None
        if rel_path:
            try:
                data = storage.get_file(rel_path)
            except Exception:
                data = None
        if not data:
            data = _create_blank_image(width_px=300, height_px=220, text=fallback_label)
        return RLImage(io.BytesIO(data), width=img_w, height=img_h)

    orig_img_flow = load_rl_image(img_entity.original_file_path if img_entity else None, "Original Fundus")
    enh_img_flow = load_rl_image(img_entity.enhanced_file_path if img_entity and img_entity.enhanced_file_path else None, "No Enhancement Applied")

    images_row = [
        [orig_img_flow, enh_img_flow],
        [
            Paragraph("<b>Original Fundus Photograph</b>", caption_style),
            Paragraph("<b>Enhanced Fundus Photograph (CLAHE)</b>" if (img_entity and img_entity.enhanced_file_path) else "<b>Enhanced Fundus Photograph (N/A)</b>", caption_style),
        ]
    ]
    img_table = Table(images_row, colWidths=[260, 260])
    img_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(img_table)
    story.append(Spacer(1, 6))

    # 4. Image Quality Assessment (IQA) Details
    story.append(Paragraph("Image Quality Assessment (IQA Gate)", heading_style))
    iqa_status = img_entity.iqa_status if img_entity else "UNKNOWN"
    quality_score = getattr(img_entity, "sharpness_score", 85.0) or 85.0
    quality_issues = img_entity.actionable_feedback if (img_entity and img_entity.iqa_status != "GOOD") else "None detected."
    recapture_guidance = img_entity.actionable_feedback if (img_entity and img_entity.iqa_status != "GOOD") else "Image quality is optimal for clinical screening."

    if iqa_status == "REJECT":
        iqa_badge_color = "#DC2626"
    elif iqa_status == "BORDERLINE":
        iqa_badge_color = "#D97706"
    else:
        iqa_badge_color = "#16A34A"

    iqa_data = [
        [
            Paragraph("IQA Status", cell_label),
            Paragraph(f"<b><font color='{iqa_badge_color}'>{iqa_status}</font></b>", cell_val),
            Paragraph("Sharpness Score", cell_label),
            Paragraph(f"{quality_score:.1f}", cell_val),
        ],
        [
            Paragraph("Quality Assessment", cell_label),
            Paragraph(f"{quality_issues}", cell_val),
            Paragraph("Recapture Guidance", cell_label),
            Paragraph(f"{recapture_guidance}", cell_val),
        ]
    ]
    iqa_table = Table(iqa_data, colWidths=[110, 150, 110, 150])
    iqa_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(iqa_table)

    if iqa_status == "REJECT":
        story.append(Spacer(1, 6))
        reject_notice = Table([[
            Paragraph(
                "<b>NOTICE: IMAGE REJECTED BY CLINICAL QUALITY GATE.</b><br/>"
                "AI diagnostic grading was NOT performed due to excessive blur, extreme underexposure, "
                "or poor field coverage. Immediate fundus recapture is required following the guidance above.",
                cell_val_bold
            )
        ]], colWidths=[520])
        reject_notice.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEE2E2")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#EF4444")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(reject_notice)

    # Footer note for Page 1
    story.append(Spacer(1, 6))
    story.append(Paragraph("<i>Page 1 of 2 • Diagnostic Evaluation, Grad-CAM++ Visual Explanation & Tele-Referral continue on Page 2</i>", caption_style))

    # ================= PAGE 2 =================
    story.append(PageBreak())

    # Page 2 Header
    story.append(Paragraph(f"<b>RetinaSahayak</b> | Diagnostic Evaluation & Explainable AI Verification", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E3A8A"), spaceBefore=3, spaceAfter=6))

    # Case: Rejected Image without AI analysis
    if not ai_ana or iqa_status == "REJECT":
        reject_p2 = [
            [
                Paragraph("<b>Diagnostic Status:</b>", cell_label),
                Paragraph("<b>AI Grading Not Performed (Image Rejected)</b>", cell_val)
            ],
            [
                Paragraph("<b>Clinical Reason:</b>", cell_label),
                Paragraph("Input photograph did not meet the mandatory sharpness or exposure criteria. Automated grading was suspended to prevent diagnostic error.", cell_val)
            ],
            [
                Paragraph("<b>Recommended Action:</b>", cell_label),
                Paragraph("Recapture fundus image using proper camera alignment, patient headrest fixation, and Level 3 illumination.", cell_val_bold)
            ]
        ]
        p2_table = Table(reject_p2, colWidths=[130, 390])
        p2_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#F87171")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(p2_table)
        story.append(Spacer(1, 10))

    else:
        # Diagnostic Assessment Table
        grade = ai_ana.predicted_grade
        conf = ai_ana.confidence_score
        conf_pct = f"{conf * 100:.1f}%"
        is_referable = ai_ana.is_referable
        is_uncertain = ai_ana.is_uncertain
        referable_str = "REFERABLE" if is_referable else "NON_REFERABLE"
        uncertain_str = "UNCERTAIN" if is_uncertain else "CERTAIN"
        engine_name = ai_ana.inference_engine or "MOCK_INFERENCE"
        is_mock = "MOCK" in engine_name.upper()

        grade_badge_color = GRADE_COLORS.get(grade, colors.gray)

        # Parse probabilities
        probs_text = "N/A"
        if ai_ana.probabilities_json:
            try:
                pj = json.loads(ai_ana.probabilities_json)
                probs_text = ", ".join([f"G{k.split('_')[1]}:{v:.2f}" for k, v in pj.items()])
            except Exception:
                probs_text = ai_ana.probabilities_json

        ai_diag_data = [
            [
                Paragraph("Predicted DR Grade", cell_label),
                Paragraph(f"<b><font color='{grade_badge_color.hexval()}'>{GRADE_LABELS_EN.get(grade, 'N/A')}</font></b>", cell_val),
                Paragraph("Model Confidence", cell_label),
                Paragraph(f"<b>{conf_pct}</b>", cell_val),
            ],
            [
                Paragraph("Referral Status", cell_label),
                Paragraph(f"<b>{referable_str}</b>", cell_val),
                Paragraph("Uncertainty Status", cell_label),
                Paragraph(f"<b>{uncertain_str}</b>", cell_val),
            ],
            [
                Paragraph("Class Probabilities", cell_label),
                Paragraph(f"<font size='6.5'>{probs_text}</font>", cell_val),
                Paragraph("Inference Engine", cell_label),
                Paragraph(f"<b>{engine_name}</b>", cell_val),
            ]
        ]
        diag_table = Table(ai_diag_data, colWidths=[110, 160, 100, 150])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(diag_table)
        story.append(Spacer(1, 6))

        # Explainability Visual Artifacts (Heatmap & Overlay)
        story.append(Paragraph("Visual Explainability: Grad-CAM++ Attention Maps", heading_style))

        xai_heatmap_flow = load_rl_image(xai.heatmap_file_path if xai else None, "Grad-CAM++ Heatmap")
        xai_overlay_flow = load_rl_image(xai.overlay_file_path if xai else None, "Grad-CAM++ Overlay")

        xai_images_row = [
            [xai_heatmap_flow, xai_overlay_flow],
            [
                Paragraph("<b>Grad-CAM++ Attention Heatmap</b><br/>Visual activation representation", caption_style),
                Paragraph("<b>Heatmap Overlay on Fundus</b><br/>Regions that influenced model prediction", caption_style),
            ]
        ]
        xai_table = Table(xai_images_row, colWidths=[260, 260])
        xai_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(xai_table)
        story.append(Spacer(1, 4))

        # Explainability Transparency Label
        if is_mock:
            exp_note = "<b>Simulated visual explanation generated by deterministic mock inference. Does not reflect trained model activations.</b>"
            note_bg = "#FEF3C7"
            note_border = "#F59E0B"
        else:
            exp_note = "<b>Grad-CAM++ activation map generated from trained EfficientNet convolutional feature maps. Requires ophthalmologist clinical verification.</b>"
            note_bg = "#EFF6FF"
            note_border = "#3B82F6"

        exp_note_table = Table([[Paragraph(exp_note, cell_val)]], colWidths=[520])
        exp_note_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(note_bg)),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(note_border)),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(exp_note_table)
        story.append(Spacer(1, 5))

        # Clinical Explanation & Recommended Action
        story.append(Paragraph("Clinical Explanation & Recommended Action", heading_style))

        explanation_str = ai_ana.clinical_explanation
        rec_action = getattr(ai_ana, "recommended_action", None) or (
            "Refer to tele-ophthalmologist for confirmatory examination within 30 days." if is_referable else
            "Follow-up eye check at Primary Health Centre in 6 to 12 months. Maintain strict blood sugar control."
        )

        rationale_data = [
            [Paragraph(f"<b>Clinical Explanation:</b> {explanation_str}", body_text)],
            [Paragraph(f"<b>Recommended Action:</b> {rec_action}", body_text)],
        ]
        rat_table = Table(rationale_data, colWidths=[520])
        rat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#93C5FD")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(rat_table)
        story.append(Spacer(1, 5))

    # QR Code & Digital Verification Panel
    qr_grade = ai_ana.predicted_grade if ai_ana else 0
    qr_hash = review.digital_signature_hash if review else "PRESUMPTIVE_AI_SCREENING"
    qr_bytes = generate_verification_qr_bytes(
        screening_id=screening.id,
        patient_code=pat_code,
        grade=qr_grade,
        verification_hash=qr_hash
    )
    qr_img = RLImage(io.BytesIO(qr_bytes), width=0.9 * inch, height=0.9 * inch)

    qr_panel_data = [
        [
            qr_img,
            Paragraph(
                f"<b>Digital Verification & Tele-Referral Record:</b><br/>"
                f"• Authenticated screening record for tertiary vitreoretinal specialist access.<br/>"
                f"• Model Version: <b>{ai_ana.model_version if ai_ana else 'RetinaSahayak-EfficientNet-v2.1'}</b> • Generated: {datetime.now(timezone.utc).strftime('%d-%b-%Y %H:%M UTC')}<br/>"
                f"• Screening ID: {screening.id} | Patient ID: {pat_code}",
                cell_val
            )
        ]
    ]
    qr_table = Table(qr_panel_data, colWidths=[80, 440])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(qr_table)
    story.append(Spacer(1, 5))

    # Prominent CDSS Medical Disclaimer
    disclaimer_text = (
        "<b>MEDICAL DISCLAIMER:</b> Presumptive AI screening observation. Not an autonomous medical diagnosis. "
        "Must be reviewed and verified by a licensed ophthalmologist before any clinical treatment. "
        "Grad-CAM visual outputs reflect regions that influenced the model's prediction and do not constitute confirmed lesion diagnoses."
    )
    disclaimer_table = Table([[Paragraph(disclaimer_text, cell_val)]], colWidths=[520])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(disclaimer_table)

    # Build PDF document
    doc.build(story)
    return buffer.getvalue()
