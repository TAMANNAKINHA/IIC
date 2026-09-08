# 👁️ Offline Retina Screening — Explainable AI for DR Screening in Rural India

**MathWorks Hackathon Problem Statement:** Explainable AI for Diabetic Retinopathy Screening in Rural India
**Category:** Software · **Domain:** MedTech / BioTech / HealthTech

A fully offline app that lets a health worker with no medical training photograph a patient's retina, get an instant AI screening result, and generate a bilingual (English/Hindi) report — one version for a doctor, one for the patient/health worker — without needing internet access at the point of care.

---

## 🖥️ What the app looks like and does

The app has exactly **three screens**, navigated from a sidebar on the left. Every label — buttons, fields, report wording — comes from one language dictionary, so the whole app *and* both PDF reports switch between **English and Hindi** from a single dropdown. Nothing is duplicated into separate language files or pages.

### Sidebar (always visible)

| Element | What it does |
|---|---|
| Report language dropdown | English or हिन्दी — changes every label and both PDF languages instantly |
| Health worker name field | Pre-fills "Attending Nurse" on new entries |
| Navigation buttons | Switch between "Patient history" and "New patient entry" |
| Offline indicator | "● Working offline" — constant reminder no data leaves the device |

### Screen 1 — Patient History (home screen)

A scrollable list, most recent patient first. Each row shows:
- 🔴 🟢 ⚪ A status dot — red = flagged for doctor, green = cleared, gray = not analyzed yet
- Patient name + auto-generated ID (e.g. `PHC1-0001`)
- Date screened
- Plain-language result
- An **Open** button → jumps to that patient's report screen

Empty state shows a friendly prompt instead of a blank page.

### Screen 2 — New Patient Entry (intake form)

Top of screen previews the **next sequential ID** (e.g. `PHC1-0007`) — assigned in order, never random.

Fields:
- Name of patient
- Age
- Gender (dropdown)
- Attending Nurse (pre-filled)
- Medical History (free text)
- **Retina photo** — toggle between:
  - **Upload a photo** *(default)* — used for the hackathon demo
  - **Use camera** — opens the device camera directly; ready for when real capture hardware exists
- **Save patient** button → saves everything, assigns the real ID, and opens the new patient's report screen

### Screen 3 — Patient Detail & Report

**Left side:** the retina photo + a **Run AI analysis** button (becomes "Re-run" after first use).

**Right side:** patient details, and once analyzed:
- A clear banner: 🔴 **Flagged for doctor review** or 🟢 **No referral needed**
- DR severity grade (No DR → Proliferative DR)
- Model confidence %
- Two download buttons: **Doctor report (PDF)** and **Health worker report (PDF)**, both in the currently selected language

### The two PDF reports

Both come from the *same* saved patient data — nobody retypes anything:

- **Doctor's report** — full clinical detail: lesion-by-lesion breakdown (microaneurysms, haemorrhages, hard exudates, soft exudates), severity grade, confidence, recommendation.
- **Health worker / patient report** — simplified: severity grade + plain recommendation only, no clinical jargon.

---

## 🧭 Why it's designed this way

| Design choice | Maps to |
|---|---|
| Sequential, not random, patient IDs | Village camp workflow — patients logged in order seen |
| One JSON file per patient (`patient_data_input.json`) | No duplicate data entry between doctor/worker reports |
| Two report audiences, one dataset | Problem statement's "ophthalmologist validation" requirement |
| Fully offline, local files only | Rural India's unreliable connectivity constraint |

---

## ⚠️ Current known limitation

The AI step (`utils/analyze.py`) is currently a **mock** — it doesn't run a trained model yet, so the full app flow (entry → capture → analysis → bilingual report) can be built and demoed first. Swapping in the real trained YOLO11n model only requires editing this one file.

---

## 📁 Project structure
Dhrishti/
├── app.py ← Streamlit app (run this)
├── requirements.txt
├── fonts/ ← add a Hindi-capable font here (see fonts/README.txt)
├── data/ ← created automatically, holds patient records (gitignored)
└── utils/
├── storage.py ← local JSON/image storage, sequential IDs
├── translations.py ← English + Hindi label dictionary
├── analyze.py ← AI analysis (MOCK — replace with real YOLO11n)
└── report.py ← bilingual PDF generation

---

## 🚀 Running it locally

```bash
# one-time setup (needs internet)
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# run it (works offline from here on)
streamlit run app.py
```

Opens at `http://localhost:8501`. For correct Hindi PDF text, add `NotoSansDevanagari-Regular.ttf` to the `fonts/` folder — see `fonts/README.txt`.

---

## 🔌 Wiring in the real YOLO11n model

Open `utils/analyze.py` and replace the mock body of `run_model()` with your Ultralytics inference call, keeping the same returned dictionary shape (`severity_level`, `confidence`, `flagged`, `detected{...}`). Nothing else in the app needs to change.

---

## 👥 Team

*EKTA,SANSKAR,TAMANNA.*