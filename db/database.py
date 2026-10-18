"""
CrewSignal - Local SQLite Database Module
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Any

import pandas as pd

DB_PATH = Path(__file__).parent / "crewsignal.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS astronauts (
            astronaut_id TEXT PRIMARY KEY,
            name         TEXT,
            age          INTEGER,
            created_at   TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id TEXT NOT NULL,
            metric       TEXT NOT NULL,
            value        REAL,
            measured_at  TEXT NOT NULL,
            recorded_at  TEXT NOT NULL,
            source       TEXT NOT NULL,
            synced       INTEGER DEFAULT 1,
            conflict     INTEGER DEFAULT 0,
            UNIQUE(astronaut_id, metric, measured_at, source)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptoms (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id TEXT NOT NULL,
            symptom_type TEXT NOT NULL,
            severity     INTEGER CHECK(severity BETWEEN 1 AND 5),
            description  TEXT,
            logged_at    TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flags (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id TEXT NOT NULL,
            status       TEXT NOT NULL,
            metrics      TEXT NOT NULL,
            evidence     TEXT NOT NULL,
            confidence   REAL,
            created_at   TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_actions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            action       TEXT NOT NULL,
            flag_status  TEXT,
            timestamp    TEXT NOT NULL,
            astronaut_id TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized → {DB_PATH}")


def save_readings(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    required = {"astronaut_id", "metric", "value", "measured_at", "recorded_at", "source"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns: {required - set(df.columns)}")

    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO readings
                (astronaut_id, metric, value, measured_at, recorded_at, source, synced, conflict)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0)
            """, (
                str(row["astronaut_id"]),
                str(row["metric"]),
                float(row["value"]) if pd.notna(row["value"]) else None,
                str(row["measured_at"]),
                str(row["recorded_at"]),
                str(row["source"])
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    return inserted


def get_readings(
    astronaut_id: Optional[str] = None,
    metric: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None
) -> pd.DataFrame:
    conn = get_connection()

    query = """
        SELECT astronaut_id, metric, value, measured_at, recorded_at, source, synced, conflict
        FROM readings
        WHERE 1=1
    """
    params: List[Any] = []

    if astronaut_id:
        query += " AND astronaut_id = ?"
        params.append(astronaut_id)
    if metric:
        query += " AND metric = ?"
        params.append(metric)
    if start:
        query += " AND measured_at >= ?"
        params.append(start)
    if end:
        query += " AND measured_at <= ?"
        params.append(end)

    query += " ORDER BY measured_at ASC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def save_symptom(
    astronaut_id: str,
    symptom_type: str,
    severity: int,
    description: str = "",
    logged_at: Optional[datetime] = None
) -> None:
    if not 1 <= severity <= 5:
        raise ValueError("Severity must be between 1 and 5")

    if logged_at is None:
        logged_at = datetime.now(timezone.utc)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO symptoms (astronaut_id, symptom_type, severity, description, logged_at)
        VALUES (?, ?, ?, ?, ?)
    """, (astronaut_id, symptom_type, severity, description, logged_at.isoformat()))
    conn.commit()
    conn.close()


def get_symptoms(astronaut_id: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if astronaut_id:
        df = pd.read_sql_query(
            "SELECT * FROM symptoms WHERE astronaut_id = ? ORDER BY logged_at DESC",
            conn, params=(astronaut_id,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM symptoms ORDER BY logged_at DESC", conn
        )
    conn.close()
    return df


def save_flag(
    astronaut_id: str,
    status: str,
    metrics: List[str],
    evidence: List[str],
    confidence: float,
    created_at: Optional[datetime] = None
) -> None:
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO flags (astronaut_id, status, metrics, evidence, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        astronaut_id,
        status,
        ",".join(metrics),
        " | ".join(evidence),
        confidence,
        created_at.isoformat()
    ))
    conn.commit()
    conn.close()


def get_flags(astronaut_id: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if astronaut_id:
        df = pd.read_sql_query(
            "SELECT * FROM flags WHERE astronaut_id = ? ORDER BY created_at DESC",
            conn, params=(astronaut_id,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM flags ORDER BY created_at DESC", conn
        )
    conn.close()
    return df


def save_workflow_action(
    action: str,
    flag_status: str,
    timestamp: Optional[str] = None,
    astronaut_id: Optional[str] = None
) -> None:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workflow_actions (action, flag_status, timestamp, astronaut_id)
        VALUES (?, ?, ?, ?)
    """, (action, flag_status, timestamp, astronaut_id))
    conn.commit()
    conn.close()


def get_workflow_actions(astronaut_id: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if astronaut_id:
        df = pd.read_sql_query(
            "SELECT * FROM workflow_actions WHERE astronaut_id = ? ORDER BY timestamp DESC",
            conn, params=(astronaut_id,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM workflow_actions ORDER BY timestamp DESC", conn
        )
    conn.close()
    return df


def mark_synced(reading_ids: List[int]) -> None:
    if not reading_ids:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE readings SET synced = 1 WHERE id = ?",
        [(rid,) for rid in reading_ids]
    )
    conn.commit()
    conn.close()


def get_pending_readings() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM readings WHERE synced = 0 ORDER BY measured_at ASC",
        conn
    )
    conn.close()
    return df


def mark_conflict(reading_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE readings SET conflict = 1 WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    test_df = pd.DataFrame([
        {
            "astronaut_id": "ASTRONAUT_01",
            "metric": "heart_rate",
            "value": 72.0,
            "measured_at": "2025-01-01T08:00:00",
            "recorded_at": "2025-01-01T08:00:00",
            "source": "simulator"
        },
        {
            "astronaut_id": "ASTRONAUT_01",
            "metric": "spo2",
            "value": 97.5,
            "measured_at": "2025-01-01T08:00:00",
            "recorded_at": "2025-01-01T08:00:00",
            "source": "simulator"
        }
    ])

    print("\nSaving first time...")
    print(f"Inserted: {save_readings(test_df)}")

    print("\nSaving again (should be 0)...")
    print(f"Inserted: {save_readings(test_df)}")

    print("\nReading back:")
    print(get_readings())
    print("\nDatabase ready.")