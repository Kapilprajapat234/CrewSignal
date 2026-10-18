import streamlit as st


LABELS = {
    "heart_rate": "Heart Rate",
    "spo2": "SpO2",
    "sleep_hours": "Sleep Hours",
    "systolic_bp": "Systolic BP",
    "diastolic_bp": "Diastolic BP",
    "activity": "Activity",
}


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def show_profile(astronaut):
    st.subheader("Astronaut Profile")

    col1, col2, col3 = st.columns(3)

    # FIX 8: metric() name ko truncate kar deta tha ("ASTRONAUT…")
    name = _get(astronaut, "name", "—")
    col1.markdown(f"**Name**  \n{name}")
    col2.metric("Age", _get(astronaut, "age", "—"))
    col3.metric("Mission Day", _get(astronaut, "mission_day", "—"))

    st.divider()

    st.markdown("### Personal Baselines")
    st.caption("Median ± MAD, computed from this astronaut's own calibration data.")

    baselines = _get(astronaut, "baselines")
    if not baselines:
        st.info("No baseline data available. Load a scenario first.")
        return

    cols = st.columns(len(baselines))
    for col, (metric, stats) in zip(cols, baselines.items()):
        median = _get(stats, "median", stats if isinstance(stats, (int, float)) else "—")
        mad = _get(stats, "mad", None)
        label = LABELS.get(metric, str(metric).replace("_", " ").title())
        if mad is not None:
            col.metric(label=label, value=f"{median:.1f}", delta=f"±{mad:.1f} MAD")
        else:
            col.metric(label=label, value=str(median))

    st.divider()

    st.markdown("### Mission Timeline")
    timeline = _get(astronaut, "timeline") or []

    if not timeline:
        st.caption("No events in this scenario's timeline.")
    else:
        rows = []
        for event in timeline:
            day = _get(event, "day", _get(event, "start_day", "?"))
            desc = _get(event, "description", _get(event, "event", str(event)))
            rows.append({"Mission Day": day, "Event": desc})
        st.dataframe(rows, use_container_width=True, hide_index=True)