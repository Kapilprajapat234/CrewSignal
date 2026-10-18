import streamlit as st
from datetime import datetime, timezone
from db.database import save_workflow_action


def show(flags):
    st.subheader("Decision Support Workflow")
    st.caption("Human-reviewed actions. Not a diagnosis.")

    if not flags:
        st.info("No active flags. Workflow actions appear when a monitoring flag is present.")
        return

    flag_list = list(flags.values()) if isinstance(flags, dict) else list(flags)
    active = []
    for f in flag_list:
        status = f.get("status") if isinstance(f, dict) else getattr(f, "status", "")
        if status not in ("NORMAL", ""):
            active.append(f)

    if not active:
        st.info("No active flags requiring action.")
        return

    for i, flag in enumerate(active):
        status = flag.get("status") if isinstance(flag, dict) else getattr(flag, "status", "UNKNOWN")
        st.markdown(f"**Active flag:** {status}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Repeat measurement", key=f"repeat_{i}"):
                save_workflow_action(
                    action="repeat_measurement",
                    flag_status=status,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                # FIX 6: rerun() hata diya — ab message dikhta hai
                st.toast("New measurement requested.")
                st.success("New measurement requested.")

        with col2:
            if st.button("Log symptom", key=f"log_{i}"):
                st.info("Use the symptom form above to record a symptom.")

        with col3:
            if st.button("Escalate", key=f"escalate_{i}"):
                st.session_state[f"confirm_escalate_{i}"] = True

        if st.session_state.get(f"confirm_escalate_{i}"):
            st.warning("Approved protocol: Notify flight surgeon and log the escalation.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm escalation", key=f"confirm_{i}"):
                    save_workflow_action(
                        action="escalate",
                        flag_status=status,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                    st.session_state[f"confirm_escalate_{i}"] = False
                    st.toast("Escalation recorded.")
                    st.success("Escalation recorded.")
            with c2:
                if st.button("Cancel", key=f"cancel_{i}"):
                    st.session_state[f"confirm_escalate_{i}"] = False
                    st.rerun()

        st.divider()