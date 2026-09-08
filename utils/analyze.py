"""
analyze.py
----------
Runs entirely offline, in-process (no subprocess, no network).

Right now this returns a MOCKED result so the rest of the app -
history, report generation, flagging logic - can be built and
demoed before your trained YOLO11n model is exported.

TO WIRE IN THE REAL MODEL, replace the body of run_model() with:

    from ultralytics import YOLO
    _model = YOLO("path/to/your/best.pt")   # load once, outside the function ideally

    def run_model(image_path: str) -> dict:
        results = _model(image_path)[0]
        # translate results.boxes (class ids + confidences) into the
        # exact same dict shape returned below, then return it.
        ...

Keep the returned dict shape identical to the mock below - nothing
else in the app needs to change if you do.
"""

import random


def run_model(image_path: str) -> dict:
    # Deterministic-ish mock so re-analyzing the same image gives a
    # stable result during your demo, instead of a new random answer
    # every time you click "Run AI analysis".
    seed = sum(bytearray(image_path.encode("utf-8"))) % 5
    severity = seed
    confidence = round(random.uniform(0.78, 0.97), 2)

    detected = {
        "microaneurysms": severity >= 1,
        "haemorrhages": severity >= 3,
        "hard_exudates": severity >= 2,
        "soft_exudates": severity >= 3,
    }

    flagged = severity >= 2 or confidence < 0.80

    return {
        "severity_level": severity,
        "confidence": confidence,
        "flagged": flagged,
        "detected": detected,
        "model_source": "MOCK - replace utils/analyze.py with trained YOLO11n before submission",
    }
