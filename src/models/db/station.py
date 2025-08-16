from typing import ClassVar
import psycopg
from psycopg import sql
from psycopg.rows import DictRow
from pydantic import BaseModel

class StationEconomy(BaseModel):
    sources: ClassVar[list[str]] = ["Docked"]
    Name: str # Docked.Economies[]
    Proportion: float # Docked.Economies[]
    
class Station(BaseModel):
    sources: ClassVar[list[str]] = ["Docked", "ApproachSettlement"]
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    SystemAddress: int # Docked, ApproachSettlement
    MarketID: int # Docked, ApproachSettlement
    StationName: str # Docked, ApproachSettlement
    StationType: str # Docked, ApproachSettlement="Settlement"
    BodyID: int | None # ApproachSettlement
    Latitude: float | None # ApproachSettlement
    Longitude: float | None # ApproachSettlement
    DistFromStarLS: float | None # Docked
    StationGovernment: str | None # Docked, ApproachSettlement
    StationAllegiance: str | None # Docked, ApproachSettlement
    numStationEconomies: int | None # Docked, ApproachSettlement
    StationEconomies: list[StationEconomy] | None # Docked, ApproachSettlement
    StationFactionName: str | None # Docked, ApproachSettlement
    StationFactionState: str | None # Docked, ApproachSettlement
    numStationServices: int | None # Docked, ApproachSettlement
    StationServices: list[str] | None # Docked, ApproachSettlement
    StationEconomy: str | None # Docked, ApproachSettlement
    StationState: str | None # Docked, ApproachSettlement
    LandingPadsLarge: int | None # Docked
    LandingPadsMedium: int | None # Docked
    LandingPadsSmall: int | None # Docked

def create_station_tables() -> str:
    return """
    CREATE TABLE IF NOT EXISTS station (
        MarketID BIGINT NOT NULL,
        SystemAddress BIGINT NOT NULL,
        StationName TEXT NOT NULL,
        StationType TEXT NOT NULL,
        BodyID BIGINT,
        Latitude DOUBLE PRECISION,
        Longitude DOUBLE PRECISION,
        DistFromStarLS DOUBLE PRECISION,
        StationGovernment TEXT,
        StationAllegiance TEXT,
        StationFactionName TEXT,
        StationFactionState TEXT,
        StationEconomy TEXT,
        StationState TEXT,
        numStationServices INT,
        numStationEconomies INT,
        LandingPadsLarge INT,
        LandingPadsMedium INT,
        LandingPadsSmall INT,
        PRIMARY KEY (MarketID)
    );

    CREATE TABLE IF NOT EXISTS station_economy (
        MarketID BIGINT NOT NULL,
        Name TEXT NOT NULL,
        Proportion DOUBLE PRECISION NOT NULL,
        PRIMARY KEY (MarketID, Name),
        FOREIGN KEY (MarketID) REFERENCES station (MarketID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS station_service (
        MarketID BIGINT NOT NULL,
        Name TEXT NOT NULL,
        PRIMARY KEY (MarketID, Name),
        FOREIGN KEY (MarketID) REFERENCES station (MarketID) ON DELETE CASCADE
    );
    """

def upsert_station(conn: psycopg.Cursor[DictRow], station: Station) -> None:
    """Upsert a station into the database, including its economies and services."""
    station_dict = station.model_dump(exclude={'StationEconomies', 'StationServices'})
    columns = sql.SQL(', ').join(map(sql.SQL, station_dict.keys()))
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(station_dict))
    
    update_columns = sql.SQL(', ').join(
        sql.SQL("{} = EXCLUDED.{}").format(sql.SQL(k), sql.SQL(k)) for (k, v) in station_dict.items() if v is not None
    )

    query = sql.SQL("""
        INSERT INTO station ({columns}) VALUES ({placeholders})
        ON CONFLICT (MarketID) DO UPDATE SET {update_columns}
    """).format(
        columns=columns,
        placeholders=placeholders,
        update_columns=update_columns
    )
    
    conn.execute(query, tuple(station_dict.values()))

    if station.StationEconomies is not None:
        conn.execute("DELETE FROM station_economy WHERE MarketID = %s;", (station.MarketID,))
        for economy in station.StationEconomies:
            conn.execute("""
                INSERT INTO station_economy (MarketID, Name, Proportion) VALUES (%s, %s, %s)
                ON CONFLICT (MarketID, Name) DO NOTHING;
            """, (station.MarketID, economy.Name, economy.Proportion))

    if station.StationServices is not None:
        conn.execute("DELETE FROM station_service WHERE MarketID = %s;", (station.MarketID,))
        for service in station.StationServices:
            conn.execute("""
                INSERT INTO station_service (MarketID, Name) VALUES (%s, %s)
                ON CONFLICT (MarketID, Name) DO NOTHING;
            """, (station.MarketID, service))


def get_station(conn: psycopg.Cursor[DictRow], market_id: int) -> Station | None:
    """Retrieve a station by its market ID."""
    conn.execute("""
        SELECT * FROM station WHERE MarketID = %s;
    """, (market_id,))
    row = conn.fetchone()
    if not row:
        return None
    station = Station(**row)
    
    conn.execute("""
        SELECT Name, Proportion FROM station_economy WHERE MarketID = %s;
    """, (market_id,))
    economies = conn.fetchall()
    station.StationEconomies = [StationEconomy(**economy) for economy in economies]

    conn.execute("""
        SELECT Name FROM station_service WHERE MarketID = %s;
    """, (market_id,))
    services = conn.fetchall()
    station.StationServices = [service["Name"] for service in services]

    return station
