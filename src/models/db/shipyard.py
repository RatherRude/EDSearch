from typing import ClassVar
from pydantic import BaseModel

class ShipyardShip(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId", "name"]
    marketId: int
    name: str

class Shipyard(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId"]
    timestamp: str
    marketId: int
    numShips: int
    ships: list[ShipyardShip]

def create_shipyard_tables() -> str:
    """Create the shipyard table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS shipyard (
        marketId BIGINT NOT NULL,
        timestamp TEXT NOT NULL,
        numShips INT NOT NULL,
        PRIMARY KEY (marketId)
    );

    CREATE TABLE IF NOT EXISTS shipyard_ship (
        marketId BIGINT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (marketId, name),
        FOREIGN KEY (marketId) REFERENCES shipyard (marketId) ON DELETE CASCADE
    );
    """

def upsert_shipyard(conn, shipyard: Shipyard) -> None:
    """Upsert a shipyard into the database, including its ships."""
    shipyard_dict = shipyard.model_dump(exclude={'ships'})
    columns = ', '.join(shipyard_dict.keys())
    placeholders = ', '.join(['%s'] * len(shipyard_dict))
    update_columns = ', '.join(f"{k} = EXCLUDED.{k}" for k in shipyard_dict.keys() if k != 'marketId')
    query = f"""
        INSERT INTO shipyard ({columns}) VALUES ({placeholders})
        ON CONFLICT (marketId) DO UPDATE SET {update_columns}
    """
    conn.execute(query, tuple(shipyard_dict.values()))

    # Insert ships
    if shipyard.ships is not None:
        conn.execute("DELETE FROM shipyard_ship WHERE marketId = %s;", (shipyard.marketId,))
        for ship in shipyard.ships:
            conn.execute("""
                INSERT INTO shipyard_ship (marketId, name)
                VALUES (%s, %s)
                ON CONFLICT (marketId, name) DO NOTHING
            """, (shipyard.marketId, ship.name))

def get_shipyard(conn, market_id: int) -> Shipyard | None:
    """Retrieve a shipyard by its marketId."""
    conn.execute("SELECT * FROM shipyard WHERE marketId = %s;", (market_id,))
    row = conn.fetchone()
    if not row:
        return None
    shipyard = Shipyard(**row, ships=[])

    # Retrieve ships
    conn.execute("SELECT name FROM shipyard_ship WHERE marketId = %s;", (market_id,))
    ships = conn.fetchall()
    shipyard.ships = [ShipyardShip(marketId=market_id, **s) for s in ships]
    return shipyard
