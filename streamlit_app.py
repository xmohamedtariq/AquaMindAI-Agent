from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from web_app import (
    UPLOAD_ROOT,
    _build_runtime,
    _call_runtime,
    _dataset_summary,
    _demo_csv_files,
    _safe_filename,
    _simplify_result,
)


st.set_page_config(
    page_title="AquaMind AI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(120, 120, 120, 0.16);
    }

    .hero {
        padding: 2.1rem 2.3rem;
        border-radius: 22px;
        border: 1px solid rgba(120, 120, 120, 0.16);
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.5rem;
        letter-spacing: -0.04em;
    }

    .hero p {
        margin-top: .7rem;
        margin-bottom: 0;
        font-size: 1.05rem;
        opacity: .72;
        max-width: 800px;
    }

    .section-label {
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .09em;
        opacity: .55;
        margin-bottom: .35rem;
    }

    .feature-card {
        padding: 1.3rem;
        border: 1px solid rgba(120, 120, 120, 0.16);
        border-radius: 18px;
        min-height: 145px;
    }

    .feature-card h3 {
        margin-top: .25rem;
        margin-bottom: .45rem;
    }

    .feature-card p {
        opacity: .68;
        margin-bottom: 0;
    }

    .result-card {
        padding: 1.5rem 1.6rem;
        border: 1px solid rgba(120, 120, 120, 0.16);
        border-radius: 18px;
        margin-bottom: 1rem;
    }

    .result-card h3 {
        margin-top: 0;
    }

    .status-pill {
        display: inline-block;
        padding: .35rem .7rem;
        border-radius: 999px;
        font-size: .82rem;
        font-weight: 650;
        background: rgba(30, 180, 110, .12);
        border: 1px solid rgba(30, 180, 110, .22);
        margin-bottom: .8rem;
    }

    .footer {
        margin-top: 3rem;
        padding-top: 1.4rem;
        border-top: 1px solid rgba(120, 120, 120, 0.14);
        opacity: .55;
        font-size: .88rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px;
        min-height: 44px;
        font-weight: 650;
    }

    div[data-testid="stFileUploader"] {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def save_uploaded_csv(uploaded_file) -> Path:
    payload = uploaded_file.getvalue()
    digest = hashlib.sha256(payload).hexdigest()[:12]
    destination = UPLOAD_ROOT / f"{digest}-{_safe_filename(uploaded_file.name)}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def diagnosis_label(data: dict[str, Any]) -> str | None:
    diagnosis = (
        data.get("primary_hypothesis")
        or data.get("diagnosis")
        or {}
    )

    if isinstance(diagnosis, str):
        return diagnosis

    if isinstance(diagnosis, dict):
        return (
            diagnosis.get("label")
            or diagnosis.get("name")
            or diagnosis.get("id")
        )

    return None


def extract_recommendations(data: dict[str, Any]) -> list[str]:
    report = as_dict(data.get("report"))

    values = (
        report.get("recommendations")
        or data.get("recommendations")
        or []
    )

    return [
        str(item)
        for item in as_list(values)
        if str(item).strip()
    ]


def extract_sources(data: dict[str, Any]) -> list[str]:
    report = as_dict(data.get("report"))

    grounding = as_dict(
        report.get("source_grounding")
        or data.get("source_grounding")
    )

    sources = grounding.get("source_ids") or data.get("source_ids") or []

    return [
        str(item)
        for item in as_list(sources)
        if str(item).strip()
    ]


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="section-label">Desalination Operations Intelligence</div>
        <h1>🌊 AquaMind AI</h1>
        <p>
            Investigate reverse-osmosis performance issues using plant data
            and receive clear, evidence-based operational guidance.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

demo_files = _demo_csv_files()
demo_options = {path.name: path for path in demo_files}

with st.sidebar:
    st.header("New Investigation")

    st.caption(
        "Select plant data and describe what you want AquaMind to investigate."
    )

    source_mode = st.radio(
        "Data source",
        ["Demo dataset", "Upload CSV"],
        horizontal=True,
    )

    dataset_path: Path | None = None

    if source_mode == "Demo dataset":
        selected_name = st.selectbox(
            "Dataset",
            options=[""] + sorted(demo_options.keys()),
            format_func=lambda value: value or "Choose plant data",
        )

        if selected_name:
            dataset_path = demo_options[selected_name]

    else:
        uploaded_file = st.file_uploader(
            "Upload plant CSV",
            type=["csv"],
        )

        if uploaded_file is not None:
            dataset_path = save_uploaded_csv(uploaded_file)

    plant_id = st.text_input(
        "Plant / Train",
        value="aquamind-demo-plant",
    )

    user_request = st.text_area(
        "What would you like to investigate?",
        value=(
            "Investigate the RO performance decline, identify the most "
            "likely cause, explain the evidence, and recommend safe "
            "verification steps."
        ),
        height=150,
    )

    run_clicked = st.button(
        "Run Investigation",
        type="primary",
        width="stretch",
    )


# -------------------------------------------------------------------
# Welcome state
# -------------------------------------------------------------------

if "aquamind_simplified" not in st.session_state:
    st.subheader("Operational intelligence for RO systems")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="section-label">Analyze</div>
                <h3>Performance</h3>
                <p>
                    Review operating data and identify meaningful changes
                    in plant behavior.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="section-label">Understand</div>
                <h3>Likely Causes</h3>
                <p>
                    Connect operating symptoms with relevant desalination
                    engineering evidence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="section-label">Act</div>
                <h3>Next Steps</h3>
                <p>
                    Receive practical verification recommendations before
                    making operational decisions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    st.info(
        "Choose a dataset from the left panel, describe the issue, "
        "and start an investigation."
    )


# -------------------------------------------------------------------
# Dataset preview
# -------------------------------------------------------------------

if dataset_path is not None:
    with st.expander("Preview selected plant data"):
        try:
            summary = _dataset_summary(dataset_path)

            rows = summary.get("rows") or summary.get("row_count")
            columns = summary.get("columns") or summary.get("column_count")

            m1, m2, m3 = st.columns(3)

            m1.metric(
                "Dataset",
                dataset_path.name,
            )

            if rows is not None:
                m2.metric("Records", str(rows))

            if columns is not None:
                if isinstance(columns, list):
                    m3.metric("Parameters", str(len(columns)))
                else:
                    m3.metric("Parameters", str(columns))

            preview = pd.read_csv(dataset_path, nrows=15)
            st.dataframe(
                preview,
                width="stretch",
                hide_index=True,
            )

        except Exception:
            st.caption("Preview is unavailable for this dataset.")


# -------------------------------------------------------------------
# Run investigation
# -------------------------------------------------------------------

if run_clicked:
    if dataset_path is None:
        st.error("Please select or upload plant data first.")

    elif not user_request.strip():
        st.error("Please describe what you would like to investigate.")

    else:
        task_id = f"streamlit-{uuid.uuid4().hex[:12]}"

        try:
            with st.spinner("Analyzing plant performance..."):
                runtime = _build_runtime(dataset_path)

                result = _call_runtime(
                    runtime,
                    request=user_request.strip(),
                    plant_id=plant_id.strip() or "aquamind-demo-plant",
                    task_id=task_id,
                )

                simplified = _simplify_result(
                    result,
                    dataset_path,
                    task_id,
                )

            st.session_state["aquamind_runtime"] = runtime
            st.session_state["aquamind_result"] = result
            st.session_state["aquamind_simplified"] = simplified
            st.session_state["aquamind_task_id"] = task_id

            st.rerun()

        except Exception:
            st.error(
                "AquaMind could not complete this investigation. "
                "Please verify the dataset and try again."
            )


# -------------------------------------------------------------------
# Results
# -------------------------------------------------------------------

simplified = st.session_state.get("aquamind_simplified")
result = st.session_state.get("aquamind_result")
runtime = st.session_state.get("aquamind_runtime")

if isinstance(simplified, dict):
    st.markdown("---")

    st.markdown(
        '<span class="status-pill">✓ Investigation complete</span>',
        unsafe_allow_html=True,
    )

    st.header("Investigation Summary")

    final_answer = (
        simplified.get("final_answer")
        or simplified.get("executive_summary")
        or "The investigation has been completed."
    )

    st.markdown(
        f"""
        <div class="result-card">
            <div class="section-label">Summary</div>
            <h3>What AquaMind found</h3>
            <p>{final_answer}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    label = diagnosis_label(simplified)

    if label:
        st.subheader("Likely Cause")
        st.success(label)

    recommendations = extract_recommendations(simplified)

    if recommendations:
        st.subheader("Recommended Next Steps")

        for index, recommendation in enumerate(recommendations, start=1):
            st.markdown(
                f"**{index}.** {recommendation}"
            )

    sources = extract_sources(simplified)

    if sources:
        with st.expander("Evidence used in this investigation"):
            for source in sources:
                st.markdown(f"- `{source}`")

    st.write("")
    st.subheader("Save to Case History")

    st.caption(
        "Save this investigation so it can be referenced in future cases."
    )

    approved = st.checkbox(
        "I confirm that this case may be saved.",
        key="save_approval",
    )

    if st.button(
        "Save Case",
        disabled=not approved,
    ):
        state = result.get("state") if isinstance(result, dict) else None

        if state is None or runtime is None:
            st.warning("This investigation cannot be saved right now.")
        else:
            try:
                runtime.save_incident(
                    state,
                    approved=True,
                )
                st.success("Case saved successfully.")

            except Exception:
                st.error(
                    "The case could not be saved. Please try again."
                )

    st.write("")

    if st.button("Start New Investigation"):
        for key in (
            "aquamind_runtime",
            "aquamind_result",
            "aquamind_simplified",
            "aquamind_task_id",
            "save_approval",
        ):
            st.session_state.pop(key, None)

        st.rerun()


# -------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------

st.markdown(
    """
    <div class="footer">
        AquaMind AI · Decision support for reverse-osmosis desalination operations
        <br>
        Operational recommendations should be verified by qualified plant personnel.
    </div>
    """,
    unsafe_allow_html=True,
)
