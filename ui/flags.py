import streamlit as st

STATUS_COLORS = {
    "NORMAL": "#2e7d32",
    "WATCH": "#f9a825",
    "SUSPECTED_CONCERN": "#ef6c00",
    "INSUFFICIENT_EVIDENCE": "#546e7a",
}


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def show(flags):
    st.subheader("Flags & Evidence")
    st.caption("Monitoring flags only. Not a diagnosis.")

    if flags is None:
        st.info("Load a scenario first.")
        return

    flag_list = list(flags.values()) if isinstance(flags, dict) else list(flags)

    if not flag_list:
        st.success("No active monitoring flags for this astronaut.")
        return

    for flag in flag_list:
        status = _get(flag, "status", "UNKNOWN")
        color = STATUS_COLORS.get(status, "#607d8b")
        confidence = _get(flag, "confidence", _get(flag, "confidence_level"))
        evidence = _get(flag, "evidence", []) or []
        metrics = _get(flag, "metrics", _get(flag, "affected_metrics", []))
        timestamp = _get(flag, "timestamp", _get(flag, "detected_at"))

        if isinstance(evidence, str):
            evidence = [evidence]

        # FIX 7: hardcoded light background hata diya — dark theme mein
        # safed card nahi chamkega
        st.markdown(
            f"""
            <div style="border-left:5px solid {color};padding:12px 16px;
                        margin-bottom:12px;background:rgba(128,128,128,0.10);
                        border-radius:4px;">
                <span style="background:{color};color:white;padding:3px 10px;
                             border-radius:10px;font-size:0.8rem;font-weight:600;">
                    {status}
                </span>
                <span style="margin-left:8px;font-size:0.75rem;
                             background:rgba(249,168,37,0.20);padding:4px 8px;
                             border-radius:3px;">Not a diagnosis</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(3)
        if confidence is not None:
            cols[0].markdown(f"**Confidence:** {confidence}")
        if timestamp:
            cols[1].markdown(f"**Detected:** {timestamp}")
        if metrics:
            text = ", ".join(metrics) if isinstance(metrics, (list, tuple)) else str(metrics)
            cols[2].markdown(f"**Metrics:** {text}")

        if evidence:
            st.markdown("**Evidence:**")
            for item in evidence:
                st.markdown(f"- {item}")

        st.divider()