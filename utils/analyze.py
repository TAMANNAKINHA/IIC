"""
analyze.py
----------
Runs the full offline inference pipeline:
    raw image -> image_preprocessor.preprocess_pipeline -> local YOLO model
Returns a dict with severity grade (canonical string), confidence,
flagged status, and paths to processed/annotated images.

The grade strings match the canonical grades in pipeline.py:
    NO_DR, MILD, MODERATE, SEVERE, PROLIFERATE_DR
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np

# Add parent directory so we can import image_preprocessor
PARENT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from image_preprocessor import preprocess_pipeline
from ultralytics import YOLO

# Load your local YOLO model once (adjust path to your .pt file)
MODEL_PATH = os.path.join(PARENT_DIR, "yolo26.pt")
_model = YOLO(MODEL_PATH)

# Mapping from YOLO class index to canonical DR grade string + severity level (0-4)
# Ensure this order matches your trained model's class order.
SEVERITY_MAP = {
    0: ("NO_DR", 0),
    1: ("MILD", 1),
    2: ("MODERATE", 2),
    3: ("SEVERE", 3),
    4: ("PROLIFERATE_DR", 4),
}


def run_model(image_path: str) -> dict:
    """
    Runs preprocessing + local YOLO inference.
    Returns dict with:
        - severity_level: int 0-4
        - confidence: float
        - flagged: bool (referable if severity >= 2)
        - raw_grade: str (canonical, e.g. "MODERATE")
        - processed_image_path: str
        - annotated_image_path: str
    """
    # 1. Preprocess (quality gate + enhancement) – offline
    success, processed_image_path = preprocess_pipeline(image_path)
    if not success:
        raise ValueError("Image rejected by quality gate. Recapture required.")

    # 2. Run local YOLO model
    results = _model(processed_image_path, conf=0.10)  # adjust conf threshold

    # 3. Extract severity grade
    probs = results[0].probs  # classification probabilities (if classification model)
    if probs is not None:
        top_idx = int(probs.top1)
        confidence = float(probs.top1conf)
    else:
        # Fallback for detection model: use highest-confidence detection's class
        boxes = results[0].boxes
        if boxes is not None and len(boxes) > 0:
            top_idx = int(boxes[0].cls[0].item())
            confidence = float(boxes[0].conf[0].item())
        else:
            top_idx = 0
            confidence = 0.0

    grade_name, severity_level = SEVERITY_MAP.get(top_idx, ("NO_DR", 0))
    flagged = severity_level >= 2

    # 4. Save annotated image (with YOLO detections)
    annotated_image_path = _save_annotated_image(results, processed_image_path)

    return {
        "severity_level": severity_level,
        "confidence": round(confidence, 4),
        "flagged": flagged,
        "raw_grade": grade_name,        # canonical grade string
        "processed_image_path": str(processed_image_path),
        "annotated_image_path": annotated_image_path,
        "model_source": f"Local YOLO ({MODEL_PATH})",
    }


def _save_annotated_image(results, processed_image_path: str) -> str:
    """Renders YOLO detections on the processed image and saves next to it."""
    annotated_array = results[0].plot()   # RGB numpy array
    annotated_bgr = cv2.cvtColor(annotated_array, cv2.COLOR_RGB2BGR)
    annotated_path = Path(processed_image_path).with_name(
        f"annotated_{Path(processed_image_path).name}"
    )
    cv2.imwrite(str(annotated_path), annotated_bgr)
    return str(annotated_path)