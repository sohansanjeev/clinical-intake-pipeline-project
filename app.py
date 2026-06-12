"""
Streamlit dashboard — browse and filter batch-extracted clinical intake data.

Displays processed notes in a card layout with triage badges. Supports
filtering by triage priority, searching notes, and viewing individual
extractions side by side with the raw note text.
"""

import streamlit as st


def main() -> None:
    """Render the dashboard."""
    st.set_page_config(page_title="Clinical Intake Dashboard", layout="wide")
    st.title("🏥 Clinical Intake Dashboard")
    st.caption("LLM-extracted structured data from MIMIC-IV admission notes")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Controls")
        triage_filter = st.selectbox(
            "Triage filter",
            ["All", "Low", "Medium", "High"],
        )

    # --- Main area ---
    st.info("Pipeline results will render here once processing is implemented.")


if __name__ == "__main__":
    main()
