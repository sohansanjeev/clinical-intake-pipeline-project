"""
Clinical Intake Dashboard — Browse and explore extraction results.

Upload a processed CSV to view the data with paginated tables,
triage filtering, and detailed patient cards.
"""

from io import StringIO
from typing import Any

import pandas as pd
import streamlit as st

from clinical_intake.utils import normalize_age, normalize_sex

st.set_page_config(page_title="Clinical Intake Dashboard", layout="wide")

# ── Session state ─────────────────────────────────────────────────────────

if "data" not in st.session_state:
    st.session_state.data = None
if "page" not in st.session_state:
    st.session_state.page = 1
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0

ROWS_PER_PAGE = 50
TABLE_COLS = [
    "patient_id",
    "triage_priority",
    "demographics_sex",
    "demographics_age",
    "admission_service",
    "clinical_context_chief_complaint",
    "error",
]


# ── Helpers ───────────────────────────────────────────────────────────────

def _read_csv(contents: bytes) -> pd.DataFrame:
    df = pd.read_csv(StringIO(contents.decode("utf-8")), keep_default_na=False)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("")
    return df


def _format_sex(val: Any) -> str:
    """Format sex for display. Thin wrapper around normalize_sex."""
    result = normalize_sex(val)
    return result if result else "—"


def _format_age(val: Any) -> str:
    """Format age for display. Delegates to normalize_age."""
    return normalize_age(val)


def _filter_data(df: pd.DataFrame, triage: str) -> pd.DataFrame:
    if triage == "All":
        return df.copy()
    return df[df["triage_priority"] == triage.lower()].copy()


def _paginate(df: pd.DataFrame, page: int) -> pd.DataFrame:
    start = (page - 1) * ROWS_PER_PAGE
    return df.iloc[start:start + ROWS_PER_PAGE]


def _format_patient_id(x: Any) -> str:
    """Format a patient ID as a zero-padded 6-digit string."""
    try:
        return f"{int(float(x)):06d}"
    except (ValueError, TypeError):
        return str(x).zfill(6) if x else ""


# ── Dialogs ───────────────────────────────────────────────────────────────

@st.dialog("Patient Details", width="large")
def show_patient_detail(row: dict[str, Any]) -> None:
    triage = row.get("triage_priority", "")
    pid = row.get("patient_id", "???")
    badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(triage, "")
    st.markdown(f"### {badge} {triage.upper()}  —  Patient **#{pid}**")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Demographics**")
        st.write(f"Age: {_format_age(row.get('demographics_age', ''))}")
        st.write(f"Sex: {_format_sex(row.get('demographics_sex', ''))}")
    with col2:
        st.markdown("**Admission**")
        st.write(f"Service: {row.get('admission_service', '—') or '—'}")
        st.write(f"Admitted: {row.get('admission_admission_date', '—') or '—'}")
        st.write(f"Discharged: {row.get('admission_discharge_date', '—') or '—'}")

    st.divider()
    st.markdown("**Chief Complaint**")
    st.write(row.get("clinical_context_chief_complaint", "") or "—")

    hpi = row.get("clinical_context_history_of_present_illness", "") or "—"
    if hpi and hpi != "—":
        with st.expander("History of Present Illness"):
            st.write(hpi)

    col1, col2 = st.columns(2)
    with col1:
        pmh = str(row.get("clinical_context_past_medical_history", "") or "")
        items = [x.strip() for x in pmh.split(";") if x.strip()]
        st.markdown("**Past Medical History**")
        if items:
            with st.expander(f"View {len(items)} conditions"):
                for item in items:
                    st.write(f"- {item}")
        else:
            st.write("None")

        allergies = str(row.get("clinical_context_allergies", "") or "")
        allergy_items = [x.strip() for x in allergies.split(";") if x.strip()]
        st.markdown("**Allergies**")
        if allergy_items:
            with st.expander(f"View {len(allergy_items)} allergies"):
                for item in allergy_items:
                    st.write(f"- {item}")
        else:
            st.write("None")

    with col2:
        meds = str(row.get("clinical_context_medications", "") or "")
        med_items = [x.strip() for x in meds.split(";") if x.strip()]
        st.markdown("**Medications**")
        if med_items:
            with st.expander(f"View {len(med_items)} medications"):
                for item in med_items:
                    st.write(f"- {item}")
        else:
            st.write("None")

    raw = row.get("text", "") or ""
    if raw:
        with st.expander("View Raw Note"):
            st.text(raw)


# ── LANDING PAGE (no data) ────────────────────────────────────────────────

if st.session_state.data is None:
    st.markdown("<h1 style='text-align: center;'>Clinical Intake Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>LLM-extracted structured data from MIMIC-IV admission notes</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded = st.file_uploader("Upload a processed CSV to begin", type="csv")
        if uploaded is not None:
            st.session_state.data = _read_csv(uploaded.getvalue())
            st.session_state.page = 1
            st.rerun()


# ── DASHBOARD (data loaded) ──────────────────────────────────────────────

else:
    df = st.session_state.data

    with st.sidebar:
        st.header("Controls")

        if st.button("← Load New File"):
            st.session_state.data = None
            st.session_state.upload_key += 1
            st.rerun()

        triage_filter = st.selectbox(
            "Triage filter", ["All", "Low", "Medium", "High"],
        )

        if st.button("Reset Dashboard", use_container_width=True):
            st.session_state.data = None
            st.session_state.upload_key += 1
            st.session_state.page = 1
            st.rerun()

        st.divider()
        st.subheader("Stats")
        st.metric("Total Patients", len(df))
        for level in ["high", "medium", "low"]:
            count = len(df[df["triage_priority"] == level])
            st.metric(level.capitalize(), count)

        st.divider()

    # Main area
    filtered = _filter_data(df, triage_filter)

    if filtered.empty:
        st.info("No patients match the current filter.")
    else:
        total_pages = max(1, (len(filtered) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Prev") and st.session_state.page > 1:
                st.session_state.page -= 1
                st.rerun()
        with col2:
            st.markdown(
                f"<div style='text-align: center'>Page <b>{st.session_state.page}</b> of <b>{total_pages}</b> ({len(filtered)} patients)</div>",
                unsafe_allow_html=True,
            )
        with col3:
            if st.button("Next ▶") and st.session_state.page < total_pages:
                st.session_state.page += 1
                st.rerun()

        page_df = _paginate(filtered, st.session_state.page)
        display_df = page_df[TABLE_COLS].copy()
        display_df["demographics_sex"] = display_df["demographics_sex"].apply(_format_sex)
        display_df["demographics_age"] = display_df["demographics_age"].apply(_format_age)
        display_df["patient_id"] = display_df["patient_id"].apply(_format_patient_id)

        display_df.columns = ["ID", "Triage", "Sex", "Age", "Service", "Chief Complaint", "Errors"]
        icons = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}
        display_df["Triage"] = display_df["Triage"].map(lambda v: icons.get(v.lower(), v))

        page_idx = (st.session_state.page - 1) * ROWS_PER_PAGE
        header_cols = st.columns([1.5, 1.5, 0.8, 0.8, 1.5, 4, 1.2])
        for col, label in zip(header_cols, ["ID", "Triage", "Sex", "Age", "Service", "Chief Complaint", ""]):
            col.markdown(f"**{label}**")

        for i in range(len(display_df)):
            row = display_df.iloc[i]
            orig_idx = page_idx + i
            row_data = filtered.iloc[orig_idx]
            with st.container():
                rc = st.columns([1.5, 1.5, 0.8, 0.8, 1.5, 4, 1.2])
                rc[0].write(row["ID"])
                rc[1].write(row["Triage"])
                rc[2].write(row["Sex"])
                rc[3].write(row["Age"])
                rc[4].write(row["Service"])
                cc = str(row["Chief Complaint"])
                rc[5].write(cc[:80] + "..." if len(cc) > 80 else cc)
                if rc[6].button("View", key=f"v_{orig_idx}", use_container_width=True):
                    show_patient_detail(row_data.to_dict())
