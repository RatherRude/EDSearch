from typing import ClassVar
import psycopg
from psycopg import sql
from psycopg.rows import DictRow
from pydantic import BaseModel

    
class Signal(BaseModel):
    sources: ClassVar[list[str]] = ["SAASignals", "FSSBodySignals", "FSSSignalDiscovered"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "Type", "SignalName"]
    SystemAddress: int
    BodyID: int | None
    Type: str
    Count: int
    SignalName: str | None

def create_signal_tables() -> str:
    """Create the signal table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS signal (
        id SERIAL PRIMARY KEY,
        SystemAddress BIGINT NOT NULL,
        BodyID BIGINT,
        Type TEXT NOT NULL,
        Count INT NOT NULL,
        SignalName TEXT
    );

    -- Create unique constraint that handles nulls properly
    DROP INDEX IF EXISTS idx_signal_unique_entries;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_unique_entries
    ON signal (SystemAddress, COALESCE(BodyID, -1), Type, COALESCE(SignalName, ''));
    """

def upsert_signal(conn: psycopg.Cursor[DictRow], signal: Signal) -> None:
    """Upsert a signal into the database."""
    # Upsert the signal
    signal_dict = signal.model_dump()

    columns = list(signal_dict.keys())
    column_names = sql.SQL(', ').join([sql.SQL(col) for col in columns])
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(signal_dict))

    # ON CONFLICT DO UPDATE
    update_columns = sql.SQL(', ').join(
        sql.SQL(k) + sql.SQL(" = EXCLUDED.") + sql.SQL(k) 
        for k, v in signal_dict.items() 
        if k not in ['SystemAddress', 'BodyID', 'Type', 'SignalName'] and v is not None
    )

    query = sql.SQL("""
        INSERT INTO signal ({columns}) VALUES ({placeholders})
        ON CONFLICT (SystemAddress, COALESCE(BodyID, -1), Type, COALESCE(SignalName, '')) DO UPDATE SET {update_columns}
        RETURNING id
    """).format(
        columns=column_names,
        placeholders=placeholders,
        update_columns=update_columns
    )

    conn.execute(query, tuple(signal_dict.values()))
    result = conn.fetchone()
    signal_id = result['id'] if result else None

def get_signal(conn: psycopg.Cursor[DictRow], system_address: int | None, body_id: int | None, type: str | None, signal_name: str | None) -> Signal | None:
    """Retrieve a signal by its system address, body ID, type, and signal name."""
    conn.execute("""
        SELECT * FROM signal 
        WHERE 
            SystemAddress IS NOT DISTINCT FROM %s AND 
            COALESCE(BodyID, -1) IS NOT DISTINCT FROM COALESCE(%s, -1) AND 
            Type IS NOT DISTINCT FROM %s AND
            COALESCE(SignalName, '') IS NOT DISTINCT FROM COALESCE(%s, '');
    """, (system_address, body_id, type, signal_name))
    row = conn.fetchone()
    if not row:
        return None

    signal_data = dict(row)
    signal_id = signal_data.pop('id')  # Remove the primary key from the model data
    signal = Signal(**signal_data)

    return signal
