import plotly.graph_objects as go
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


def _extract(readings, metric):
    sub = readings[readings["metric"] == metric]

    for col in ("timestamp", "time", "datetime", "ts"):
        if col in sub.columns:
            sub = sub.sort_values(col)
            return sub[col], sub["value"]

    sub = sub.sort_index()
    return sub.index, sub["value"]


def trend_chart(readings, baseline, metric=None):
    # FIX: empty readings pe crash nahi hoga (replay day slider se possible)
    if readings is None or readings.empty:
        st.info(
            "No readings available for the selected replay day. "
            "Load a scenario or pick a later day."
        )
        return

    if not baseline:
        st.info("No baseline data available. Load a scenario first.")
        return

    metrics = [metric] if metric else list(baseline.keys())

    for m in metrics:
        stats = baseline.get(m)
        if stats is None:
            st.warning(f"No baseline available for {LABELS.get(m, m)}.")
            continue

        median = _get(stats, "median")
        mad = _get(stats, "mad")
        if median is None or mad is None:
            st.warning(f"Baseline for {LABELS.get(m, m)} lacks median/MAD.")
            continue

        upper, lower = median + 2 * mad, median - 2 * mad
        x, y = _extract(readings, m)

        # FIX: agar is metric ki readings is day-window mein nahi hain
        if y is None or len(y) == 0:
            st.caption(f"No readings for {LABELS.get(m, m)} in the selected day range.")
            continue

        fig = go.Figure()

        # Normal band (median ± 2*MAD)
        fig.add_hrect(
            y0=lower, y1=upper,
            fillcolor="green", opacity=0.12, line_width=0,
        )

        # Trend line
        fig.add_scatter(
            x=x, y=y,
            mode="lines",
            name=LABELS.get(m, m),
            line=dict(width=2),
        )

        # Median line
        fig.add_hline(y=median, line_dash="dash", line_color="green")

        # Points outside the band
        mask = y.notna() & ((y > upper) | (y < lower))
        if mask.any():
            fig.add_scatter(
                x=x[mask], y=y[mask],
                mode="markers",
                name="Outside band",
                marker=dict(color="red", size=8, symbol="x"),
            )

        fig.update_layout(
            title=f"{LABELS.get(m, m)} — normal band {lower:.1f} to {upper:.1f}",
            height=350,
            margin=dict(l=40, r=20, t=50, b=40),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
        )

        st.plotly_chart(fig, use_container_width=True)