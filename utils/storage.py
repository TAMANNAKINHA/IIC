"""
storage.py
----------
Everything here reads/writes plain files on the local disk.
No network calls anywhere in this file - this is what makes the
app work fully offline.

Folder layout created at runtime:

  data/
    counter.json                          <- last used sequential number
    patients/
      PHC1-0001/
        patient_data_input.json           <- all data for this patient
        retina.jpg                        <- the saved image
      PHC1-0002/
        ...
"""

import os
import json
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PATIENTS_DIR = os.path.join(DATA_DIR, "patients")
COUNTER_FILE = os.path.join(DATA_DIR, "counter.json")

# Change this per device/health-worker so IDs from different phones/laptops
# never collide once records are eventually merged centrally.
DEVICE_PREFIX = "PHC1"

PATIENT_JSON_NAME = "patient_data_input.json"


def ensure_dirs():
    os.makedirs(PATIENTS_DIR, exist_ok=True)
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"last": 0}, f)


def peek_next_id() -> str:
    """Show what the next ID will be, without consuming it."""
    ensure_dirs()
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        counter = json.load(f)
    next_n = counter["last"] + 1
    return f"{DEVICE_PREFIX}-{next_n:04d}"


def _consume_next_id() -> str:
    """Actually increment and return the new ID. Called only on save."""
    ensure_dirs()
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        counter = json.load(f)
    next_n = counter["last"] + 1
    counter["last"] = next_n
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump(counter, f)
    return f"{DEVICE_PREFIX}-{next_n:04d}"


def save_patient(name: str, age: int, gender: str, nurse: str,
                  history: str, image_bytes: bytes, image_ext: str) -> dict:
    """
    Saves a new patient record + image locally, assigns the next
    sequential ID, and writes patient_data_input.json.
    Returns the full record dict.
    """
    ensure_dirs()
    patient_id = _consume_next_id()
    patient_dir = os.path.join(PATIENTS_DIR, patient_id)
    os.makedirs(patient_dir, exist_ok=True)

    image_filename = None
    if image_bytes is not None:
        image_filename = f"retina{image_ext}"
        with open(os.path.join(patient_dir, image_filename), "wb") as f:
            f.write(image_bytes)

    record = {
        "patient_id": patient_id,
        "name": name,
        "age": age,
        "gender": gender,
        "nurse": nurse,
        "history": history,
        "date_captured": datetime.now().isoformat(timespec="seconds"),
        "image_file": image_filename,
        "analysis": None,  # filled in by run_analysis() later
    }

    with open(os.path.join(patient_dir, PATIENT_JSON_NAME), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return record


def list_patients() -> list:
    """Returns all patient records, most recently captured first."""
    ensure_dirs()
    records = []
    for patient_id in os.listdir(PATIENTS_DIR):
        patient_dir = os.path.join(PATIENTS_DIR, patient_id)
        json_path = os.path.join(patient_dir, PATIENT_JSON_NAME)
        if os.path.isfile(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                records.append(json.load(f))
    records.sort(key=lambda r: r.get("date_captured", ""), reverse=True)
    return records


def load_patient(patient_id: str) -> dict:
    """Returns one patient's record, plus the absolute path to their image."""
    patient_dir = os.path.join(PATIENTS_DIR, patient_id)
    json_path = os.path.join(patient_dir, PATIENT_JSON_NAME)
    if not os.path.isfile(json_path):
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        record = json.load(f)
    if record.get("image_file"):
        record["image_abs_path"] = os.path.join(patient_dir, record["image_file"])
    return record


def update_analysis(patient_id: str, analysis: dict) -> dict:
    """Writes AI results back into the same patient_data_input.json file."""
    patient_dir = os.path.join(PATIENTS_DIR, patient_id)
    json_path = os.path.join(patient_dir, PATIENT_JSON_NAME)
    with open(json_path, "r", encoding="utf-8") as f:
        record = json.load(f)
    record["analysis"] = analysis
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return record
