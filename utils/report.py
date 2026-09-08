"""
report.py
---------
Builds the PDF report entirely offline using fpdf2. Now supports all
10 report languages (see translations.py) and embeds the AI-annotated
retina image (boxes drawn by the YOLO model) instead of only the raw
capture.

FONTS: fpdf2's core fonts (Arial/Helvetica) cannot render Indic
scripts. Each non-English language needs a matching Noto Sans TTF in
./fonts (see fonts/README.txt). If the right font file is missing for
the selected language, this module falls back to a Latin font/core
font and the app warns you on-screen.
"""

import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
LATIN_FONT_PATH = os.path.join(FONTS_DIR, "NotoSans-Regular.ttf")

# language code -> Noto font file needed for correct script rendering
FONT_FILES = {
    "en": "NotoSans-Regular.ttf",
    "hi": "NotoSansDevanagari-Regular.ttf",
    "mr": "NotoSansDevanagari-Regular.ttf",
    "bn": "NotoSansBengali-Regular.ttf",
    "te": "NotoSansTelugu-Regular.ttf",
    "ta": "NotoSansTamil-Regular.ttf",
    "gu": "NotoSansGujarati-Regular.ttf",
    "kn": "NotoSansKannada-Regular.ttf",
    "or": "NotoSansOriya-Regular.ttf",
    "ml": "NotoSansMalayalam-Regular.ttf",
}


def font_path_for(lang_code: str) -> str:
    return os.path.join(FONTS_DIR, FONT_FILES.get(lang_code, "NotoSans-Regular.ttf"))


def font_missing(lang_code: str) -> bool:
    return not os.path.isfile(font_path_for(lang_code))


def _severity_label(labels: dict, severity_level) -> str:
    if severity_level is None:
        return "-"
    return labels["SEVERITY_LEVELS"].get(severity_level, str(severity_level))


def _findings_lines(labels: dict, analysis: dict) -> list:
    if not analysis or not analysis.get("quality_ok", True):
        return [labels["NONE"]]

    detected = analysis.get("detected", {})
    lines = [
        labels["MICROANEURYSMS"] if detected.get("microaneurysms") else labels["MICROANEURYSMS_NEG"],
        labels["HAEMORRHAGES"] if detected.get("haemorrhages") else labels["HAEMORRHAGES_NEG"],
        labels["HARD_EXUDATES"] if detected.get("hard_exudates") else labels["HARD_EXUDATES_NEG"],
        labels["SOFT_EXUDATES"] if detected.get("soft_exudates") else labels["SOFT_EXUDATES_NEG"],
    ]
    if not any(detected.values()):
        lines = [labels["NONE"]]
    return lines


def _setup_font(pdf: FPDF, lang_code: str) -> str:
    """Registers the best available font for the language, returns the
    family name to pass to pdf.set_font(). Falls back safely."""
    target_path = font_path_for(lang_code)
    if os.path.isfile(target_path):
        pdf.add_font("ReportFont", "", target_path, uni=True)
        return "ReportFont"
    if os.path.isfile(LATIN_FONT_PATH):
        pdf.add_font("ReportFont", "", LATIN_FONT_PATH, uni=True)
        return "ReportFont"
    return "Helvetica"  # core font, always available, Latin-only


def build_pdf(record: dict, labels: dict, lang_code: str, audience: str) -> bytes:
    """
    audience: "doctor" or "worker"
    Returns raw PDF bytes, ready for st.download_button.
    """
    pdf = FPDF()
    pdf.add_page()
    font_family = _setup_font(pdf, lang_code)

    analysis = record.get("analysis")

    # ---- Title ----
    pdf.set_font(font_family, size=16)
    title = labels["TITLE"] if audience == "doctor" else labels["TITLE_WORKER"]
    pdf.multi_cell(0, 10, title)
    pdf.ln(2)

    # ---- Patient details ----
    pdf.set_font(font_family, size=13)
    pdf.multi_cell(0, 8, labels["PATIENT_DETAILS"])
    pdf.set_font(font_family, size=11)
    pdf.multi_cell(0, 7, f"{labels['NAME']}: {record.get('name', '')}")
    pdf.multi_cell(0, 7, f"{labels['ID']}: {record.get('patient_id', '')}")
    pdf.multi_cell(0, 7, f"{labels['AGE']}: {record.get('age', '')}")
    pdf.multi_cell(0, 7, f"{labels['GENDER']}: {record.get('gender', '')}")
    pdf.multi_cell(0, 7, f"{labels['NURSE']}: {record.get('nurse', '')}")
    pdf.multi_cell(0, 7, f"{labels['DATE']}: {record.get('date_captured', '')}")
    pdf.multi_cell(0, 7, f"{labels['HISTORY']}: {record.get('history', '') or '-'}")
    pdf.ln(3)

    # ---- AI-annotated retina image (falls back to raw image) ----
    image_path = (analysis or {}).get("annotated_image_path") or record.get("image_abs_path")
    if image_path and os.path.isfile(image_path):
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 7, labels["ANNOTATED_IMAGE_LABEL"])
        try:
            pdf.image(image_path, w=90)
            pdf.ln(3)
        except Exception:
            pass  # unsupported image format - skip rather than crash the report

    # ---- Findings ----
    pdf.set_font(font_family, size=13)
    pdf.multi_cell(0, 8, labels["FINDINGS"])
    pdf.set_font(font_family, size=11)

    if analysis and not analysis.get("quality_ok", True):
        pdf.multi_cell(0, 7, labels["QUALITY_REJECTED"])
    else:
        if audience == "doctor":
            for line in _findings_lines(labels, analysis):
                pdf.multi_cell(0, 7, f"- {line}")

        if analysis:
            pdf.ln(2)
            pdf.multi_cell(0, 7, f"{labels['SEVERITY']}: {_severity_label(labels, analysis.get('severity_level'))}")
            if audience == "doctor" and analysis.get("confidence") is not None:
                pdf.multi_cell(0, 7, f"{labels['CONFIDENCE']}: {round(analysis['confidence'] * 100)}%")

            pdf.ln(2)
            pdf.set_font(font_family, size=13)
            pdf.multi_cell(0, 8, labels["RECOMMENDATION"])
            pdf.set_font(font_family, size=11)
            rec_text = labels["REFER_TEXT"] if analysis.get("flagged") else labels["CLEAR_TEXT"]
            pdf.multi_cell(0, 7, rec_text)

    # ---- Footer ----
    pdf.ln(6)
    pdf.set_font(font_family, size=9)
    pdf.multi_cell(0, 6, labels["FOOTER"])

    return bytes(pdf.output(dest="S"))