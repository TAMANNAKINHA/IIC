# Offline Retina Screening — Streamlit App

A fully offline patient-entry, AI-screening, and bilingual PDF report
app for diabetic retinopathy screening, built for the MathWorks
hackathon problem statement (Explainable AI for DR Screening in
Rural India).

## What it does

- Health worker enters patient details (name, age, gender, history) and
  uploads the retina photo.
- Each patient gets an automatic **sequential** ID (e.g. `PHC1-0001`,
  `PHC1-0002`, ...) — not random — stored locally.
- All patient data + AI results are saved as `patient_data_input.json`
  next to the image, per patient, under `data/patients/<id>/`.
- "Run AI analysis" produces a severity grade, confidence score, and
  per-lesion findings (microaneurysms, haemorrhages, hard exudates,
  soft exudates). This is currently a **mock** (see below) — swap in
  your trained YOLO11n model when it's ready.
- One PDF report can be generated for the **doctor** (full clinical
  detail) and one for the **health worker** (plain summary +
  recommendation), in **English or Hindi**, switchable from a single
  sidebar dropdown — no separate files or pages per language.
- Everything runs locally. Once the Python packages are installed
  (a one-time step that needs internet), the app works with Wi-Fi
  turned off.

## Project structure

```
dr-screening-app/
├── app.py                  <- Streamlit app (run this)
├── requirements.txt
├── fonts/                  <- add a Hindi-capable font here (see fonts/README.txt)
├── data/                   <- created automatically, holds all patient records (gitignored)
└── utils/
    ├── storage.py          <- local JSON/image storage, sequential IDs
    ├── translations.py     <- English + Hindi label dictionary
    ├── analyze.py          <- AI analysis (MOCK — replace with real YOLO11n)
    └── report.py           <- bilingual PDF generation
```

## 1. One-time setup (needs internet, do this once)

```bash
# from inside the dr-screening-app folder
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Then, for correct Hindi PDF text, download **Noto Sans Devanagari**
(free Google font, search "Noto Sans Devanagari download") and place
`NotoSansDevanagari-Regular.ttf` inside the `fonts/` folder. See
`fonts/README.txt` for details. The app still runs without it, but
Hindi PDFs won't render Devanagari script correctly until it's added.

## 2. Run it locally (no internet needed from here on)

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501` —
`localhost` means it's served entirely from your own machine, so you
can turn off Wi-Fi and it keeps working.

## 3. Wiring in your real YOLO11n model

Open `utils/analyze.py` — the mock function `run_model(image_path)`
is clearly marked. Replace its body with your Ultralytics YOLO
inference call, and map its output into the same dict shape:

```python
{
  "severity_level": 0-4,
  "confidence": 0.0-1.0,
  "flagged": True/False,
  "detected": {
     "microaneurysms": True/False,
     "haemorrhages": True/False,
     "hard_exudates": True/False,
     "soft_exudates": True/False,
  },
  "model_source": "..."
}
```

Nothing else in the app needs to change — storage, translations, and
report generation all read from this same shape.

## 4. Pushing to GitHub

```bash
git init
git add .
git commit -m "Offline DR screening app"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

`.gitignore` already excludes the `data/` folder so you never
accidentally commit real or demo patient records to a public repo —
important since this handles patient health information, even in a
hackathon demo.

## Notes on the Hindi translations

The Hindi text in `utils/translations.py` was written to be clear and
medically reasonable for a hackathon demo, but hasn't been reviewed by
a native clinical Hindi speaker. If you're presenting to real
clinicians, have someone check the phrasing in `translations.py`
before relying on it.
