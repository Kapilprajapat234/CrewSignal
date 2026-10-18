import streamlit as st
from datetime import datetime, timezone
from db.database import save_symptom, get_symptoms

SYMPTOM_TYPES = [
    "Fatigue",
    "Headache",
    "Dizziness",
    "Shortness of breath",
    "Nausea",
    "Sleep difficulty",
    "Other",
]


def show(astronaut_id):
    st.subheader("Symptom Log")
    st.caption("Recorded symptoms are used as additional evidence by the monitoring system.")

    with st.form("symptom_form", clear_on_submit=True):
        symptom = st.selectbox("Symptom type", SYMPTOM_TYPES)
        severity = st.slider("Severity", 1, 5, 3)
        note = st.text_area("Note (optional)", height=80)
        submitted = st.form_submit_button("Save symptom")

        if submitted:
            save_symptom(
                astronaut_id=astronaut_id,
                symptom_type=symptom,
                severity=severity,
                description=note or "",
                logged_at=datetime.now(timezone.utc),
            )
            # FIX 5: rerun() hata diya — pehle success message flash hokar
            # gum ho jata tha. Form clear_on_submit khud reset kar deta hai.
            st.toast("Symptom saved.")
            st.success("Symptom saved.")

    st.markdown("### Past symptoms")
    df = get_symptoms(astronaut_id)

    if df.empty:
        st.info("No symptoms recorded yet.")
    else:
        for _, row in df.iterrows():
            logged_at = row.get("logged_at", "")
            st.markdown(
                f"**{row['symptom_type']}**  "
                f"(severity {row['severity']})  ·  {logged_at}"
            )
            if row.get("description"):
                st.caption(row["description"])
            st.divider()