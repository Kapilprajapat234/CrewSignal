from datetime import datetime, timezone
from typing import List, Optional
import pandas as pd

from db.database import (
    get_connection,
    get_pending_readings,
    mark_synced,
    mark_conflict,
)


def is_offline(session_state) -> bool:
    return session_state.get("offline_mode", False)


def record_reading_offline(
    astronaut_id: str,
    metric: str,
    value: float,
    measured_at: str,
    source: str = "local"
) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    recorded_at = datetime.now(timezone.utc).isoformat()

    try:
        cursor.execute("""
            INSERT INTO readings
            (astronaut_id, metric, value, measured_at, recorded_at, source, synced, conflict)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, (astronaut_id, metric, value, measured_at, recorded_at, source))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def detect_conflicts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    conflict_mask = df.duplicated(
        subset=["astronaut_id", "metric", "measured_at"],
        keep=False
    ) & ~df.duplicated(
        subset=["astronaut_id", "metric", "measured_at", "value"],
        keep=False
    )

    for idx in df[conflict_mask].index:
        rid = df.at[idx, "id"]
        if pd.notna(rid):
            mark_conflict(int(rid))

    df.loc[conflict_mask, "conflict"] = 1
    return df


def sync_pending() -> dict:
    pending = get_pending_readings()

    if pending.empty:
        return {"synced": 0, "conflicts": 0}

    pending = detect_conflicts(pending)

    ids = pending["id"].dropna().astype(int).tolist()
    mark_synced(ids)

    conflict_count = int(pending["conflict"].sum()) if "conflict" in pending.columns else 0

    return {
        "synced": len(ids),
        "conflicts": conflict_count,
        "message": (
            "We keep both values when a conflict is found. "
            "The user decides which one to trust."
        )
    }


def get_sorted_readings(astronaut_id: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if astronaut_id:
        df = pd.read_sql_query(
            """
            SELECT * FROM readings
            WHERE astronaut_id = ?
            ORDER BY measured_at ASC
            """,
            conn,
            params=(astronaut_id,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM readings ORDER BY measured_at ASC",
            conn
        )
    conn.close()
    return df