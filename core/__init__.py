from dataclasses import dataclass
from datetime import datetime


# Health Metrics

METRICS = [
    "heart_rate",
    "spo2",
    "sleep_hours",
    "systolic_bp",
    "diastolic_bp",
    "activity"
]


# Health Status Constants

NORMAL = "NORMAL"
WATCH = "WATCH"
SUSPECTED_CONCERN = "SUSPECTED_CONCERN"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# Reading Dataclass

@dataclass
class Reading:
    astronaut_id: str
    metric: str
    value: float
    measured_at: datetime
    recorded_at: datetime
    source: str


# Flag Dataclass

@dataclass
class Flag:
    astronaut_id: str
    status: str
    metrics: list[str]
    evidence: list[str]
    confidence: float
    created_at: datetime