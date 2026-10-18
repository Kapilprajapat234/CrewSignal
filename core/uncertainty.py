

from typing import List, Dict, Any, Tuple
import pandas as pd

from core import Flag, INSUFFICIENT_EVIDENCE, METRICS


def missing_ratio(readings: pd.DataFrame, expected_per_day: int = 6, days: int = None) -> float:
    if readings.empty:
        return 1.0

    if days is None:
        readings = readings.copy()
        readings["measured_at"] = pd.to_datetime(readings["measured_at"])
        days = (readings["measured_at"].max() - readings["measured_at"].min()).days + 1
        days = max(days, 1)

    expected = days * expected_per_day
    actual = len(readings.dropna(subset=["value"]))
    return max(0.0, min(1.0, 1.0 - (actual / expected)))


def confidence_level(n_readings: int, missing: float, persistence: int) -> Tuple[float, str]:
    score = 0.0

    if n_readings >= 10:
        score += 0.4
    elif n_readings >= 5:
        score += 0.25
    else:
        score += 0.1

    if missing < 0.15:
        score += 0.35
    elif missing < 0.30:
        score += 0.20
    else:
        score += 0.05

    if persistence >= 4:
        score += 0.25
    elif persistence >= 3:
        score += 0.15
    else:
        score += 0.05

    score = min(1.0, score)

    if score >= 0.75:
        label = "High"
    elif score >= 0.50:
        label = "Medium"
    else:
        label = "Low"

    return round(score, 2), label


def evaluate(
    flag: Flag,
    readings: pd.DataFrame,
    baselines: Dict[str, Dict[str, Any]],
    missing: float = None
) -> Flag:
    if missing is None:
        missing = missing_ratio(readings)

    # Check baselines
    established = True
    for m in flag.metrics:
        base = baselines.get(m)
        if not base or base.get("status") != "established":
            established = False
            break

    if not established or missing > 0.40:
        flag.status = INSUFFICIENT_EVIDENCE
        flag.confidence = 0.2
        flag.evidence = [
            "Insufficient evidence: baseline not established or too much data missing."
        ]
        return flag

    # Estimate persistence from evidence text
    persistence = 3
    for e in flag.evidence:
        if "4/" in e or "5/" in e:
            persistence = 4
            break
        if "3/" in e:
            persistence = 3

    n_readings = len(readings.dropna(subset=["value"]))
    conf, label = confidence_level(n_readings, missing, persistence)

    flag.confidence = conf

    # Enrich evidence with missing info
    missing_pct = round(missing * 100, 1)
    if missing_pct > 5:
        flag.evidence.append(f"Approximately {missing_pct}% of expected readings are missing.")

    return flag