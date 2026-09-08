

import streamlit as st
from utils import storage, analyze, report
from utils.translations import get_labels

st.set_page_config(page_title="Dhrishti", layout="wide")

# ---------------- Sidebar: language + health worker + navigation ----------------
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "page" not in st.session_state:
    st.session_state.page = "history"

with st.sidebar:
    lang_choice = st.selectbox(
        "Report language / रिपोर्ट भाषा",
        options=["en", "hi"],
        format_func=lambda c: "English" if c == "en" else "हिन्दी (Hindi)",
        index=0 if st.session_state.lang == "en" else 1,
    )
    st.session_state.lang = lang_choice
    labels = get_labels(st.session_state.lang)

    st.text_input(labels["WORKER_LABEL"], value="Health Worker", key="worker_name")

    st.divider()
    st.caption(labels["SIDEBAR_NAV"])
    if st.button(labels["NAV_HISTORY"], use_container_width=True):
        st.session_state.page = "history"
        st.session_state.selected_patient = None
    if st.button(labels["NAV_NEW"], use_container_width=True):
        st.session_state.page = "new_patient"

    st.divider()
    st.caption("● Working offline — no data leaves this device")

labels = get_labels(st.session_state.lang)
st.title(labels["APP_TITLE"])


# ================= PAGE: NEW PATIENT ENTRY =================
def render_new_patient_page():
    st.header(labels["FORM_HEADER"])
    st.caption(f"{labels['FORM_ID_PREVIEW']}: **{storage.peek_next_id()}**")

    with st.form("new_patient_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(labels["NAME"])
            age = st.number_input(labels["AGE"], min_value=1, max_value=120, step=1)
        with col2:
            gender = st.selectbox(labels["GENDER"], ["Male", "Female", "Other"])
            nurse = st.text_input(labels["NURSE"], value=st.session_state.get("worker_name", ""))

        history = st.text_area(labels["HISTORY"], placeholder=labels["HISTORY_PLACEHOLDER"])

        st.markdown(f"**{labels['UPLOAD_LABEL']}**")
        capture_mode = st.radio(
            labels["UPLOAD_LABEL"],
            options=["upload", "camera"],
            format_func=lambda v: labels["UPLOAD_OPTION"] if v == "upload" else labels["CAMERA_OPTION"],
            index=0,  # upload stays the default choice for now
            horizontal=True,
            label_visibility="collapsed",
        )

        if capture_mode == "upload":
            image_file = st.file_uploader(
                labels["UPLOAD_LABEL"], type=["jpg", "jpeg", "png"],
                help=labels["UPLOAD_HELP"], label_visibility="collapsed",
            )
        else:
            image_file = st.camera_input(
                labels["UPLOAD_LABEL"], help=labels["CAMERA_HELP"], label_visibility="collapsed",
            )

        submitted = st.form_submit_button(labels["SAVE_BUTTON"], type="primary")

        if submitted:
            image_bytes = image_file.getvalue() if image_file else None
            if capture_mode == "camera":
                image_ext = ".jpg"  # st.camera_input always returns JPEG
            else:
                image_ext = ("." + image_file.name.split(".")[-1].lower()) if image_file else ".jpg"
            record = storage.save_patient(
                name=name, age=int(age), gender=gender, nurse=nurse,
                history=history, image_bytes=image_bytes, image_ext=image_ext,
            )
            st.success(f"{labels['SAVE_SUCCESS']}: {record['patient_id']}")
            st.session_state.selected_patient = record["patient_id"]
            st.session_state.page = "detail"
            st.rerun()


# ================= PAGE: HISTORY =================
def render_history_page():
    st.header(labels["HISTORY_HEADER"])
    st.caption(labels["HISTORY_SUB"])

    records = storage.list_patients()
    if not records:
        st.info(labels["HISTORY_EMPTY"])
        return

    for record in records:
        analysis = record.get("analysis")
        if analysis is None:
            status_color = "gray"
            status_text = "—"
        elif analysis.get("flagged"):
            status_color = "red"
            status_text = labels["FLAGGED_BANNER"]
        else:
            status_color = "green"
            status_text = labels["CLEAR_BANNER"]

        cols = st.columns([1, 3, 2, 2, 2])
        cols[0].markdown(f":{status_color}[●]")
        cols[1].write(f"**{record['name']}**  \n{record['patient_id']}")
        cols[2].write(record.get("date_captured", "")[:10])
        cols[3].write(status_text)
        if cols[4].button("Open", key=f"open_{record['patient_id']}"):
            st.session_state.selected_patient = record["patient_id"]
            st.session_state.page = "detail"
            st.rerun()
        st.divider()


# ================= PAGE: PATIENT DETAIL / REPORT =================
def render_detail_page():
    patient_id = st.session_state.selected_patient
    record = storage.load_patient(patient_id)
    if record is None:
        st.error("Patient not found.")
        return

    if st.button("← " + labels["NAV_HISTORY"]):
        st.session_state.page = "history"
        st.session_state.selected_patient = None
        st.rerun()

    st.subheader(f"{record['name']}  ·  {record['patient_id']}")

    col_img, col_info = st.columns([1, 1])

    with col_img:
        if record.get("image_abs_path"):
            st.image(record["image_abs_path"], use_container_width=True)

        run_label = labels["DETAIL_RERUN_ANALYSIS"] if record.get("analysis") else labels["DETAIL_RUN_ANALYSIS"]
        if st.button(run_label, type="primary", use_container_width=True):
            with st.spinner(labels["ANALYSIS_RUNNING"]):
                if not record.get("image_abs_path"):
                    st.error("No image on file for this patient.")
                else:
                    analysis = analyze.run_model(record["image_abs_path"])
                    record = storage.update_analysis(patient_id, analysis)
            st.rerun()

    with col_info:
        st.write(f"**{labels['AGE']}:** {record.get('age', '')}")
        st.write(f"**{labels['GENDER']}:** {record.get('gender', '')}")
        st.write(f"**{labels['NURSE']}:** {record.get('nurse', '')}")
        st.write(f"**{labels['DATE']}:** {record.get('date_captured', '')}")
        st.write(f"**{labels['HISTORY']}:** {record.get('history') or '-'}")

        analysis = record.get("analysis")
        if analysis:
            st.divider()
            if analysis.get("flagged"):
                st.error(labels["FLAGGED_BANNER"])
            else:
                st.success(labels["CLEAR_BANNER"])

            sev_text = labels["SEVERITY_LEVELS"].get(analysis["severity_level"], analysis["severity_level"])
            st.write(f"**{labels['SEVERITY']}:** {sev_text}")
            st.write(f"**{labels['CONFIDENCE']}:** {round(analysis['confidence'] * 100)}%")

            if st.session_state.lang == "hi":
                import os
                if not os.path.isfile(report.HINDI_FONT_PATH):
                    st.warning(
                        "Hindi PDF font not found. Add fonts/NotoSansDevanagari-Regular.ttf "
                        "for correctly rendered Hindi PDFs (see fonts/README.txt)."
                    )

            doctor_pdf = report.build_pdf(record, labels, st.session_state.lang, audience="doctor")
            worker_pdf = report.build_pdf(record, labels, st.session_state.lang, audience="worker")

            st.download_button(
                labels["DOWNLOAD_DOCTOR_PDF"], data=doctor_pdf,
                file_name=f"{record['patient_id']}_doctor_{st.session_state.lang}.pdf",
                mime="application/pdf", use_container_width=True,
            )
            st.download_button(
                labels["DOWNLOAD_WORKER_PDF"], data=worker_pdf,
                file_name=f"{record['patient_id']}_worker_{st.session_state.lang}.pdf",
                mime="application/pdf", use_container_width=True,
            )


# ================= ROUTER =================
if st.session_state.page == "new_patient":
    render_new_patient_page()
elif st.session_state.page == "detail" and st.session_state.selected_patient:
    render_detail_page()
else:
    render_history_page()
