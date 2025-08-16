from typing import final
import psycopg
from psycopg import sql
from psycopg.rows import DictRow
from datetime import datetime
from collections import OrderedDict

from pydantic import BaseModel



from .body import Body, upsert_body
from .station import Station, upsert_station
from .system import System, upsert_system
from .landmark import Landmark, upsert_landmark
from .market import Market, upsert_market
from .shipyard import Shipyard, upsert_shipyard
from .outfitting import Outfitting, upsert_outfitting
from .signals import Signal, upsert_signal

class DatabaseModels(BaseModel):
    systems: list[System] = []
    stations: list[Station] = []
    bodies: list[Body] = []
    landmarks: list[Landmark] = []
    markets: list[Market] = []
    shipyards: list[Shipyard] = []
    outfittings: list[Outfitting] = []
    signals: list[Signal] = []

    def upsert_all(self, cur: psycopg.Cursor[DictRow]) -> None:
        """Upsert all models in this DatabaseModels instance to the database."""
        for system in self.systems:
            upsert_system(cur, system)
        for station in self.stations:
            upsert_station(cur, station)
        for body in self.bodies:
            upsert_body(cur, body)
        for landmark in self.landmarks:
            upsert_landmark(cur, landmark)
        for market in self.markets:
            upsert_market(cur, market)
        for shipyard in self.shipyards:
            upsert_shipyard(cur, shipyard)
        for outfitting in self.outfittings:
            upsert_outfitting(cur, outfitting)
        for signal in self.signals:
            upsert_signal(cur, signal)

@final
class TimestampCache:
    """In-memory LRU cache for storing the latest timestamps for (model, primary_key, event) combinations."""
    
    def __init__(self, max_size: int = 1024*10):
        self.max_size = max_size
        self._cache: OrderedDict[str, str] = OrderedDict()
    
    def _make_key(self, model_name: str, primary_key: str, event: str) -> str:
        """Create a cache key from model_name, primary_key and event."""
        return f"{model_name}|{primary_key}|{event}"
    
    def is_newer_and_update(self, model_name: str, primary_key: str, event: str, new_timestamp: str) -> bool:
        """
        Check if the new timestamp is newer than the cached one and update if so.
        Returns True if the timestamp is newer (or no cached value exists), False otherwise.
        """
        cache_key = self._make_key(model_name, primary_key, event)
        cached_timestamp = self._cache.get(cache_key)
        
        # If no cached value, consider it newer and cache it
        if cached_timestamp is None:
            self._cache[cache_key] = new_timestamp
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            self._evict_if_needed()
            return True
        
        # Move to end (most recently used) regardless of outcome
        self._cache.move_to_end(cache_key)
        
        try:
            # Parse timestamps for comparison
            new_dt = datetime.fromisoformat(new_timestamp.replace('Z', '+00:00'))
            cached_dt = datetime.fromisoformat(cached_timestamp.replace('Z', '+00:00'))
            
            # If new timestamp is newer, update cache and return True
            if new_dt > cached_dt:
                self._cache[cache_key] = new_timestamp
                return True
            else:
                return False
                
        except (ValueError, AttributeError):
            # If timestamp parsing fails, assume it's newer and update
            self._cache[cache_key] = new_timestamp
            return True
    
    def _evict_if_needed(self):
        """Remove oldest entries if cache exceeds max size."""
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first) item
    
    def get(self, model_name: str, primary_key: str, event: str) -> str | None:
        """Get cached timestamp for (model, primary_key, event) combination."""
        cache_key = self._make_key(model_name, primary_key, event)
        timestamp = self._cache.get(cache_key)
        if timestamp:
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
        return timestamp
    
    def clear(self):
        """Clear all cached timestamps."""
        self._cache.clear()


# Global timestamp cache instance
_timestamp_cache = TimestampCache()


def get_timestamp_cache() -> TimestampCache:
    """Get the global timestamp cache instance."""
    return _timestamp_cache


def create_ingestion_table() -> str:
    """Create the ingestion lock table keyed by model and primary key, tracking latest timestamp per event."""
    return """
    CREATE TABLE IF NOT EXISTS ingestion_lock (
        model_name TEXT NOT NULL,
        primary_key TEXT NOT NULL,
        event TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        PRIMARY KEY (model_name, primary_key, event)
    );
    """


def lock_latest_ingestion_timestamp(cur: psycopg.Cursor[DictRow], model_name: str, primary_key: str, event: str, new_timestamp: str) -> bool:
    """
    Serialize by (model_name, primary_key) using a sentinel row lock, then insert or update the
    timestamp for the specific (model_name, primary_key, event). This prevents concurrent updates to
    the same model instance across different events and avoids deadlocks even when no rows exist yet.

    Returns False if the (model_name, primary_key, event) row exists and the new timestamp is not
    sufficiently newer (10s guard).

    Assumes the caller manages the transaction (BEGIN/COMMIT) and sets appropriate lock timeout.
    """
    
    # First check the in-memory cache to avoid unnecessary database operations
    if not _timestamp_cache.is_newer_and_update(model_name, primary_key, event, new_timestamp):
        return False

    # 1) Ensure a sentinel row exists and lock it to serialize by (model_name, primary_key)
    sentinel_event = "__lock__"
    try:
        cur.execute(
            """
            INSERT INTO ingestion_lock (model_name, primary_key, event, timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (model_name, primary_key, event) DO NOTHING
            """,
            (model_name, primary_key, sentinel_event, "1970-01-01T00:00:00Z"),
        )
    except Exception:
        # Ignore errors here; we'll still attempt to lock
        pass

    cur.execute(
        """
        SELECT 1 FROM ingestion_lock
        WHERE model_name = %s AND primary_key = %s AND event = %s
        FOR UPDATE
        """,
        (model_name, primary_key, sentinel_event),
    )
    # Now we hold a row-level lock that serializes all work for this model/primary_key

    # 2) Upsert the specific (model_name, primary_key, event) timestamp with a 10s update guard
    upsert_query = sql.SQL("""
        WITH upsert AS (
            INSERT INTO ingestion_lock (model_name, primary_key, event, timestamp) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (model_name, primary_key, event) 
            DO UPDATE SET 
                timestamp = EXCLUDED.timestamp
                WHERE EXCLUDED.timestamp::timestamp > ingestion_lock.timestamp::timestamp + interval '10 seconds'
            RETURNING 
                (xmax = 0) AS inserted, 
                (xmax <> 0) AS updated
        )
        SELECT
            COALESCE((SELECT inserted FROM upsert), FALSE) AS inserted,
            COALESCE((SELECT updated  FROM upsert), FALSE) AS updated,
            COALESCE((SELECT TRUE FROM upsert), FALSE)     AS applied;
    """)
    
    cur.execute(upsert_query, (model_name, primary_key, event, new_timestamp))
    result = cur.fetchone()
    
    if not result:
        print('Failed to insert or update ingestion timestamp', flush=True)
        return False
    
    was_applied = result['applied']
    
    if not was_applied:
        # Nothing changed; let caller roll back to release locks
        return False

    return True