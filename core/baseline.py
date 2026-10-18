

from typing import Dict, Any
import numpy as np
import pandas as pd


CALIBRATION_DAYS = 5
MIN_READINGS = 3


def compute_baseline(readings: pd.DataFrame, metric: str) -> Dict[str, Any]:
    if readings.empty:
        return {
            "metric": metric,
            "median": None,
            "mad": None,
            "n_readings": 0,
            "status": "not_established"
        }

    df = readings[readings["metric"] == metric].copy()
    if df.empty:
        return {
            "metric": metric,
            "median": None,
            "mad": None,
            "n_readings": 0,
            "status": "not_established"
        }

    df["measured_at"] = pd.to_datetime(df["measured_at"])

    start = df["measured_at"].min()
    end = start + pd.Timedelta(days=CALIBRATION_DAYS)
    window = df[(df["measured_at"] >= start) & (df["measured_at"] < end)]

    values = window["value"].dropna().values
    n = len(values)

    if n < MIN_READINGS:
        return {
            "metric": metric,
            "median": None,
            "mad": None,
            "n_readings": n,
            "status": "not_established"
        }

    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad < 1e-6:
        mad = 1e-6

    return {
        "metric": metric,
        "median": round(median, 2),
        "mad": round(mad, 2),
        "n_readings": n,
        "status": "established"
    }


def compute_all_baselines(readings: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    metrics = readings["metric"].unique()
    return {m: compute_baseline(readings, m) for m in metrics}