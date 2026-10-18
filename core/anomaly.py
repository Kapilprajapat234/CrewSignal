from datetime import datetime, timezone
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from core import Flag, NORMAL, WATCH, SUSPECTED_CONCERN, INSUFFICIENT_EVIDENCE, METRICS


MODERATE = 2.0
STRONG = 3.5
PERSIST_WINDOW = 5
PERSIST_MIN = 3


def deviation_score(value: float, median: float, mad: float, metric: str = None) -> float:
    
    min_mad = {
        "spo2": 0.4,          # SpO2 normally varies ±0.3–0.5
        "heart_rate": 3.0,
        "sleep_hours": 0.4,
        "systolic_bp": 4.0,
        "diastolic_bp": 3.0,
        "activity": 500.0
    }.get(metric, 1e-6)

    mad = max(mad, min_mad)
    return (value - median) / mad


def detect(readings: pd.DataFrame, baselines: Dict[str, Dict[str, Any]], astronaut_id: str) -> List[Flag]:
    flags = []
    if readings.empty:
        return flags

    df = readings[readings["astronaut_id"] == astronaut_id].copy()
    if df.empty:
        return flags

    df["measured_at"] = pd.to_datetime(df["measured_at"])
    df = df.sort_values("measured_at")

    now = datetime.now(timezone.utc)
    deviant_metrics = []
    evidence = []

    for metric in METRICS:
        base = baselines.get(metric)
        if not base or base["status"] != "established":
            continue

        metric_df = df[df["metric"] == metric].dropna(subset=["value"]).tail(PERSIST_WINDOW)
        if len(metric_df) < PERSIST_MIN:
            continue

        scores = []
        for val in metric_df["value"]:
            scores.append(deviation_score(val, base["median"], base["mad"], metric=metric))

        strong_count = sum(1 for s in scores if abs(s) >= STRONG)
        moderate_count = sum(1 for s in scores if abs(s) >= MODERATE)

        if strong_count >= PERSIST_MIN:
            deviant_metrics.append(metric)
            direction = "increased" if np.mean(scores) > 0 else "decreased"
            evidence.append(
                f"{metric} {direction} strongly "
                f"({strong_count}/{len(scores)} recent readings)"
            )
        elif moderate_count >= PERSIST_MIN:
            deviant_metrics.append(metric)
            direction = "increased" if np.mean(scores) > 0 else "decreased"
            evidence.append(
                f"{metric} {direction} moderately "
                f"({moderate_count}/{len(scores)} recent readings)"
            )

    # Fixed threshold demo (SpO2)
    spo2_df = df[df["metric"] == "spo2"].dropna(subset=["value"]).tail(1)
    fixed_triggered = False
    if not spo2_df.empty and spo2_df["value"].iloc[0] < 92:
        fixed_triggered = True
        evidence.append("Fixed rule: SpO2 < 92")

    if not deviant_metrics and not fixed_triggered:
        return flags

    # Decide status
    has_strong = any("strongly" in e for e in evidence)

    if has_strong and len(deviant_metrics) >= 2:
        status = SUSPECTED_CONCERN
        confidence = 0.85
        if "Multiple metrics showing persistent deviation" not in evidence:
            evidence.append("Multiple metrics showing persistent deviation")
    elif has_strong:
        # Strong persistent deviation alone → SUSPECTED_CONCERN
        status = SUSPECTED_CONCERN
        confidence = 0.80
    elif len(deviant_metrics) >= 2:
        status = SUSPECTED_CONCERN
        confidence = 0.75
        evidence.append("Multiple metrics showing persistent deviation")
    elif deviant_metrics:
        status = WATCH
        confidence = 0.70
    else:
        status = WATCH
        confidence = 0.55

    flags.append(Flag(
        astronaut_id=astronaut_id,
        status=status,
        metrics=deviant_metrics if deviant_metrics else ["spo2"],
        evidence=evidence,
        confidence=confidence,
        created_at=now
    ))

    return flags