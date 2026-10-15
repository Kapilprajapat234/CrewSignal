from dataclasses import dataclass
from datetime import datetime

# ==========================================
# 1. Health Metrics
# ==========================================

METRICS = [
    "heart_rate",
    "spo2",
    "sleep_hours",
    "systolic_bp",
    "diastolic_bp",
    "activity"
]


# ==========================================
# 2. Health Status Constants
# ==========================================

NORMAL = "NORMAL"
WATCH = "WATCH"
SUSPECTED_CONCERN = "SUSPECTED_CONCERN"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# ==========================================
# 3. Reading Dataclass
# ==========================================

@dataclass
class Reading:
    astronaut_id: str
    metric: str
    value: float
    measured_at: datetime
    recorded_at: datetime
    source: str


# ==========================================
# 4. Flag Dataclass
# ==========================================

@dataclass
class Flag:
    astronaut_id: str
    status: str
    metrics: list[str]
    evidence: list[str]
    confidence: float
    created_at: datetime