"""
analyze.py
----------
Runs the trained YOLO model locally (offline, in-process). Replaces the
old mock. Flow: preprocess_pipeline() quality-gates + enhances the raw
image -> YOLO detects lesions on the processed image -> severity is
derived from which lesion classes were found -> an annotated image
(boxes drawn) is saved alongside the patient record and surfaced in
both the Streamlit UI and the PDF reports.

ADJUST CLASS_MAP below to match your model's actual class names
(check `model.names` after loading) - these are placeholders based on
standard DR lesion categories.
"""

import os
from pathlib import Path

import cv2
from ultralytics import YOLO

from image_preprocessor import preprocess_pipeline

MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "yolo26.pt")
_model = None  # loaded lazily, once per process

# raw YOLO class name -> internal lesion key. EDIT to match model.names.
CLASS_MAP = {
    "microaneurysm": "microaneurysms",
    "haemorrhage": "haemorrhages",
    "hard_exudate": "hard_exudates",
    "soft_exudate": "soft_exudates",
    "neovascularization": "neovascularization",
}

CONF_THRESHOLD = 0.10


def _get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def _derive_severity(detected: dict) -> int:
    """Rule-based ICDR-style grade from which lesion types were found.
    If your model/labels give lesion counts rather than just
    presence/absence, tighten these rules for more accurate grading."""
    if detected.get("neovascularization"):
        return 4  # Proliferative DR
    if detected.get("haemorrhages"):
        return 3  # Severe NPDR
    if detected.get("hard_exudates") or detected.get("soft_exudates"):
        return 2  # Moderate NPDR
    if detected.get("microaneurysms"):
        return 1  # Mild NPDR
    return 0  # No DR


def run_model(image_path: str) -> dict:
    """
    Returns a dict with the same shape the rest of the app expects,
    plus two new fields: `quality_ok` and `annotated_image_path`.
    """
    success, processed_path = preprocess_pipeline(image_path)
    if not success:
        return {
            "quality_ok": False,
            "severity_level": None,
            "confidence": None,
            "flagged": None,
            "detected": {},
            "annotated_image_path": None,
            "model_source": "REJECTED at quality gate - recapture required",
        }

    model = _get_model()
    results = model(str(processed_path), conf=CONF_THRESHOLD)[0]

    detected = {v: False for v in CLASS_MAP.values()}
    confidences = []
    for box in results.boxes:
        cls_name = results.names.get(int(box.cls[0]), "")
        mapped = CLASS_MAP.get(cls_name)
        if mapped:
            detected[mapped] = True
            confidences.append(float(box.conf[0]))

    severity = _derive_severity(detected)
    confidence = round(max(confidences), 4) if confidences else 0.0
    flagged = severity >= 2 or (bool(confidences) and confidence < 0.80)

    # Save the boxes-drawn image next to the source image so it can be
    # shown in the UI and embedded in the PDF report.
    annotated_path = str(Path(image_path).parent / "annotated.jpg")
    cv2.imwrite(annotated_path, results.plot())

    return {
        "quality_ok": True,
        "severity_level": severity,
        "confidence": confidence,
        "flagged": bool(flagged),
        "detected": {k: v for k, v in detected.items() if k != "neovascularization"},
        "annotated_image_path": annotated_path,
        "model_source": str(MODEL_PATH),
    }