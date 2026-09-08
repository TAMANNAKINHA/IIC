"""
report.py
---------
Builds the PDF report entirely offline using fpdf2 (pure Python,
no system dependencies, no internet needed once installed).

IMPORTANT - HINDI TEXT IN PDFS:
fpdf2's built-in core fonts (Arial/Helvetica/etc.) cannot render
Devanagari script. To get correct Hindi PDF output you must supply
a Unicode TTF font that includes Devanagari, such as Google's
"Noto Sans Devanagari":

  1. Download "NotoSansDevanagari-Regular.ttf"
     (search "Noto Sans Devanagari" - it's a free Google font)
  2. Place the file in:  fonts/NotoSansDevanagari-Regular.ttf

If that file is missing and you generate a Hindi report, this
module falls back to a core font and the Hindi characters will not
render correctly - the app will warn you in the UI when this happens.
"""

import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
HINDI_FONT_PATH = os.path.join(FONTS_DIR, "NotoSansDevanagari-Regular.ttf")
LATIN_FONT_PATH = os.path.join(FONTS_DIR, "NotoSans-Regular.ttf")  # optional, better unicode coverage than core Arial


def _severity_label(labels: dict, severity_level: int) -> str:
    return labels["SEVERITY_LEVELS"].get(severity_level, str(severity_level))


def _findings_lines(labels: dict, analysis: dict) -> list:
    """Builds the list of finding lines, matching the phrasing you specified."""
    if analysis is None:
        return [labels["NONE"]]

    detected = analysis.get("detected", {})
    lines = []

    lines.append(labels["MICROANEURYSMS"] if detected.get("microaneurysms") else labels["MICROANEURYSMS_NEG"])
    lines.append(labels["HAEMORRHAGES"] if detected.get("haemorrhages") else labels["HAEMORRHAGES_NEG"])
    lines.append(labels["HARD_EXUDATES"] if detected.get("hard_exudates") else labels["HARD_EXUDATES_NEG"])
    lines.append(labels["SOFT_EXUDATES"] if detected.get("soft_exudates") else labels["SOFT_EXUDATES_NEG"])

    if not any(detected.values()):
        lines = [labels["NONE"]]

    return lines


def _setup_font(pdf: FPDF, lang_code: str) -> str:
    """
    Registers the right font for the language and returns its family
    name to use in pdf.set_font(). Falls back safely if the Devanagari
    font file hasn't been added yet.
    """
    if lang_code == "hi" and os.path.isfile(HINDI_FONT_PATH):
        pdf.add_font("Devanagari", "", HINDI_FONT_PATH, uni=True)
        return "Devanagari"
    if os.path.isfile(LATIN_FONT_PATH):
        pdf.add_font("NotoSans", "", LATIN_FONT_PATH, uni=True)
        return "NotoSans"
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

    # ---- Retina image, if present ----
    image_path = record.get("image_abs_path")
    if image_path and os.path.isfile(image_path):
        try:
            pdf.image(image_path, w=70)
            pdf.ln(3)
        except Exception:
            pass  # unsupported image format - skip rather than crash the report

    # ---- Findings (doctor gets full lesion detail; worker gets plain summary) ----
    pdf.set_font(font_family, size=13)
    pdf.multi_cell(0, 8, labels["FINDINGS"])
    pdf.set_font(font_family, size=11)

    if audience == "doctor":
        for line in _findings_lines(labels, analysis):
            pdf.multi_cell(0, 7, f"- {line}")
    else:
        # Health worker report stays simple: severity + one recommendation line
        pass

    if analysis:
        pdf.ln(2)
        pdf.multi_cell(0, 7, f"{labels['SEVERITY']}: {_severity_label(labels, analysis['severity_level'])}")
        if audience == "doctor":
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
