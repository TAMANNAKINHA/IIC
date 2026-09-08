"""
report.py
---------
Builds the PDF report using lingual.py's generate_pdf function.
This ensures 10‑language support and consistent formatting.
"""

import sys
from pathlib import Path

# Add parent directory (where lingual.py lives) to sys.path
PARENT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from lingual import generate_pdf  # import the function from lingual.py


def build_pdf(record: dict, labels: dict, lang_code: str, audience: str) -> bytes:
    """
    `audience` is kept for compatibility but not used – lingual.py
    produces one report per language, including both doctor and worker
    levels of detail (actually it's a single report format).
    We map the frontend record to the data shape expected by lingual.py.
    """
    # Convert record to lingual.py's expected patient_data format
    analysis = record.get("analysis")
    if analysis:
        dr_grade = analysis.get("raw_grade", "UNKNOWN")
        dr_grade_confidence = analysis.get("confidence")
        referable = analysis.get("flagged", False)
    else:
        dr_grade = "UNKNOWN"
        dr_grade_confidence = None
        referable = False

    data = {
        "nurse_name": record.get("nurse", ""),
        "patient_name": record.get("name", ""),
        "patient_id": record.get("patient_id", ""),
        "previous_diseases": [record.get("history", "")],  # lingual expects a list
        "dr_grade_raw": dr_grade,
        "dr_grade": dr_grade,  # canonical grade string
        "dr_grade_index": _grade_to_index(dr_grade),
        "dr_grade_confidence": dr_grade_confidence,
        "referable": referable,
        "is_demo_data": False,  # set as needed
        "image_path": record.get("image_abs_path"),
        "annotated_image_path": analysis.get("annotated_image_path") if analysis else None,
    }

    # Call lingual.py's generate_pdf (returns BytesIO)
    pdf_buffer = generate_pdf(data, lang_code)
    return pdf_buffer.getvalue()


def _grade_to_index(grade: str) -> int:
    mapping = {
        "NO_DR": 0,
        "MILD": 1,
        "MODERATE": 2,
        "SEVERE": 3,
        "PROLIFERATE_DR": 4,
        "UNKNOWN": -1,
    }
    return mapping.get(grade, -1)