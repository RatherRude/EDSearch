from typing import ClassVar
from pydantic import BaseModel

class OutfittingItem(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId", "name"]
    marketId: int
    name: str

class Outfitting(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId"]
    timestamp: str
    marketId: int
    numItems: int
    items: list[OutfittingItem]

def create_outfitting_tables() -> str:
    """Create the outfitting table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS outfitting (
        marketId BIGINT NOT NULL,
        timestamp TEXT NOT NULL,
        numItems INT NOT NULL,
        PRIMARY KEY (marketId)
    );

    CREATE TABLE IF NOT EXISTS outfitting_item (
        marketId BIGINT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (marketId, name),
        FOREIGN KEY (marketId) REFERENCES outfitting (marketId) ON DELETE CASCADE
    );
    """

def upsert_outfitting(conn, outfitting: Outfitting) -> None:
    """Upsert an outfitting into the database, including its items."""
    outfitting_dict = outfitting.model_dump(exclude={'items'})
    columns = ', '.join(outfitting_dict.keys())
    placeholders = ', '.join(['%s'] * len(outfitting_dict))
    update_columns = ', '.join(f"{k} = EXCLUDED.{k}" for k in outfitting_dict.keys() if k != 'marketId')
    query = f"""
        INSERT INTO outfitting ({columns}) VALUES ({placeholders})
        ON CONFLICT (marketId) DO UPDATE SET {update_columns}
    """
    conn.execute(query, tuple(outfitting_dict.values()))

    # Insert items
    if outfitting.items is not None:
        conn.execute("DELETE FROM outfitting_item WHERE marketId = %s;", (outfitting.marketId,))
        for item in outfitting.items:
            conn.execute("""
                INSERT INTO outfitting_item (marketId, name)
                VALUES (%s, %s)
                ON CONFLICT (marketId, name) DO NOTHING
            """, (outfitting.marketId, item.name))

def get_outfitting(conn, market_id: int) -> Outfitting | None:
    """Retrieve an outfitting by its marketId."""
    conn.execute("SELECT * FROM outfitting WHERE marketId = %s;", (market_id,))
    row = conn.fetchone()
    if not row:
        return None
    outfitting = Outfitting(**row, items=[])

    # Retrieve items
    conn.execute("SELECT name FROM outfitting_item WHERE marketId = %s;", (market_id,))
    items = conn.fetchall()
    outfitting.items = [OutfittingItem(marketId=market_id, **i) for i in items]
    return outfitting
