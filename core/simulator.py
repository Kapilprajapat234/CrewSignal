import json
import random
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from core import METRICS, Reading

# Find the scenarios directory (CrewSignal/scenarios)
SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"

# Physical limits (low, high). None means no limit on that side.
PHYSICAL_LIMITS = {
    "heart_rate": (30, 220),
    "spo2": (0, 100),
    "sleep_hours": (0, 24),
    "systolic_bp": (60, 250),
    "diastolic_bp": (30, 150),
    "activity": (0, None),
}

# Validate + Load Scenario


def validate_scenario(scenario, name="scenario"):
    """Fail early with a clear message instead of a confusing KeyError later."""
    for key in ("astronaut_id", "days", "baseline", "noise"):
        if key not in scenario:
            raise ValueError(f"{name}: missing required key '{key}'")

    if scenario["days"] < 1:
        raise ValueError(f"{name}: 'days' must be at least 1")

    for metric in METRICS:
        if metric not in scenario["baseline"]:
            raise ValueError(f"{name}: no baseline value for '{metric}'")
        if metric not in scenario["noise"]:
            raise ValueError(f"{name}: no noise value for '{metric}'")

    # Catch typos like "spo_2" instead of "spo2"
    for metric in scenario.get("changes", {}):
        if metric not in METRICS:
            raise ValueError(f"{name}: unknown metric '{metric}' in 'changes'")

    for c in scenario.get("conflicts", []):
        if c["metric"] not in METRICS:
            raise ValueError(f"{name}: unknown metric '{c['metric']}' in 'conflicts'")

    for gap in scenario.get("connectivity_gaps", []):
        if gap["start_day"] > gap["end_day"]:
            raise ValueError(f"{name}: connectivity gap start_day is after end_day")

    if not 0 <= scenario.get("dropout_rate", 0.0) < 1:
        raise ValueError(f"{name}: 'dropout_rate' must be between 0 and 1")


def load_scenario(name):
    
    file_path = SCENARIOS_DIR / f"{name}.json"

    if not file_path.is_file():
        raise FileNotFoundError(f"Scenario '{name}' not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        scenario = json.load(file)

    validate_scenario(scenario, name)
    return scenario


# Small helpers


def clamp(value, limits):
    
    low, high = limits
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value


def find_gap(current_day, gaps):
    """Return the connectivity gap that covers this day, or None."""
    for gap in gaps:
        if gap["start_day"] <= current_day <= gap["end_day"]:
            return gap
    return None



# Generate Sensor Readings


def generate_readings(scenario):
    
    astronaut_id = scenario["astronaut_id"]
    days = scenario["days"]
    baseline = scenario["baseline"]
    noise = scenario["noise"]
    changes = scenario.get("changes", {})
    gaps = scenario.get("connectivity_gaps", [])
    conflicts = scenario.get("conflicts", [])
    dropout_rate = scenario.get("dropout_rate", 0.0)
    per_day = scenario.get("readings_per_day", 1)

    # Two separate generators: adding dropouts does not change the other values
    seed = scenario.get("seed", 42)
    rng = random.Random(seed)
    drop_rng = random.Random(seed + 1)

    if "start_date" in scenario:
        start_time = datetime.fromisoformat(scenario["start_date"]).replace(tzinfo=timezone.utc)
    else:
        start_time = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)

    readings = []

    for day in range(days):
        current_day = day + 1  # days are counted from 1
        day_start = start_time + timedelta(days=day)
        gap = find_gap(current_day, gaps)

        for metric in METRICS:
            n = 1 if metric == "sleep_hours" else per_day

            for k in range(n):
                measured_at = day_start + timedelta(hours=k * 24 / n)

                # Normal value + random sensor noise
                value = baseline[metric] + rng.gauss(0, noise[metric])

                # Scenario-specific drift
                if metric in changes:
                    change = changes[metric]
                    if current_day >= change["start_day"]:
                        days_since_change = current_day - change["start_day"] + 1
                        value += days_since_change * change["change_per_day"]

                # Keep within physical limits, then round
                limits = PHYSICAL_LIMITS.get(metric, (None, None))
                value = round(clamp(value, limits), 2)

                # Dropout: reading never made it
                if drop_rng.random() < dropout_rate:
                    continue

                # Recording time
                if gap:
                    # Offline: arrives only after the link comes back
                    recorded_at = start_time + timedelta(days=gap["end_day"], minutes=5)
                else:
                    recorded_at = measured_at + timedelta(minutes=5)

                readings.append(
                    Reading(
                        astronaut_id=astronaut_id,
                        metric=metric,
                        value=value,
                        measured_at=measured_at,
                        recorded_at=recorded_at,
                        source="simulator",
                    )
                )

                # Conflict: a second, disagreeing reading from a backup sensor
                if k == 0:
                    for c in conflicts:
                        if c["day"] == current_day and c["metric"] == metric:
                            other = round(clamp(value + c["offset"], limits), 2)
                            readings.append(
                                Reading(
                                    astronaut_id=astronaut_id,
                                    metric=metric,
                                    value=other,
                                    measured_at=measured_at,  # same time, different value
                                    recorded_at=recorded_at + timedelta(hours=2),
                                    source="backup_sensor",
                                )
                            )

    df = pd.DataFrame([asdict(r) for r in readings])
    return df.sort_values(["measured_at", "metric", "source"]).reset_index(drop=True)




if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "sleep_decline"
    scenario = load_scenario(name)
    df = generate_readings(scenario)

    print(f"\n===== {name.upper()} : first 12 rows =====")
    print(df.head(12).to_string(index=False))

    print("\n===== TOTAL READINGS =====")
    print(len(df))

    
    day_no = (df["measured_at"] - df["measured_at"].min()).dt.days + 1
    first = df[day_no <= 5].groupby("metric")["value"].mean()
    last = df[day_no > scenario["days"] - 5].groupby("metric")["value"].mean()
    summary = pd.DataFrame({"first_5_days": first, "last_5_days": last})
    summary["change"] = summary["last_5_days"] - summary["first_5_days"]
    print("\n===== FIRST vs LAST 5 DAYS =====")
    print(summary.round(2))

    
    late = (
        (df["source"] == "simulator")
        & ((df["recorded_at"] - df["measured_at"]) > timedelta(hours=1))
    )
    conflicts = df.duplicated(["metric", "measured_at"], keep=False).sum() // 2
    print(f"\nLate (offline) readings : {late.sum()}")
    print(f"Conflicting pairs       : {conflicts}")