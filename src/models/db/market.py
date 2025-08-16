from typing import ClassVar, Literal
from pydantic import BaseModel
import psycopg
from psycopg import sql
from psycopg.rows import DictRow

class MarketCommodity(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId", "name"]
    marketId: int # Market.marketId
    name: str # Market.commodities[]
    category: str | None = None # Market.commodities[]
    stock: int
    demand: int
    supply: int
    buyPrice: int
    sellPrice: int

class Market(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId"]
    timestamp: str # Market
    marketId: int # Market
    commodities: list[MarketCommodity] # Market
    #prohibited: list[str] = [] # TODO does left out mean empty or not known?

def create_market_tables() -> str:
    """Create the market table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS market (
        marketId BIGINT NOT NULL,
        timestamp TEXT NOT NULL,
        PRIMARY KEY (marketId)
    );

    CREATE TABLE IF NOT EXISTS market_commodity (
        marketId BIGINT NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        stock INT,
        demand INT,
        supply INT,
        buyPrice INT,
        sellPrice INT,
        PRIMARY KEY (marketId, name),
        FOREIGN KEY (marketId) REFERENCES market (marketId) ON DELETE CASCADE
    );
    """

def upsert_market(conn: psycopg.Cursor[DictRow], market: Market) -> None:
    """Upsert a market into the database, including its commodities."""
    market_dict = market.model_dump(exclude={'commodities'})
    columns = sql.SQL(', ').join(map(sql.SQL, market_dict.keys()))
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(market_dict))
    update_columns = sql.SQL(', ').join(
        sql.SQL("{} = EXCLUDED.{}" ).format(sql.SQL(k), sql.SQL(k)) for (k, v) in market_dict.items() if k != 'marketId' and v is not None
    )
    query = sql.SQL("""
        INSERT INTO market ({columns}) VALUES ({placeholders})
        ON CONFLICT (marketId) DO UPDATE SET {update_columns}
    """).format(
        columns=columns,
        placeholders=placeholders,
        update_columns=update_columns
    )
    conn.execute(query, tuple(market_dict.values()))

    # Insert commodities
    if market.commodities is not None:
        conn.execute("DELETE FROM market_commodity WHERE marketId = %s;", (market.marketId,))
        for commodity in market.commodities:
            conn.execute("""
                INSERT INTO market_commodity (marketId, name, category, stock, demand, supply, buyPrice, sellPrice)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (marketId, name) DO NOTHING
            """, (market.marketId, commodity.name, commodity.category, commodity.stock, commodity.demand, commodity.supply, commodity.buyPrice, commodity.sellPrice))

def get_market(conn: psycopg.Cursor[DictRow], market_id: int) -> Market | None:
    """Retrieve a market by its marketId."""
    conn.execute("""
        SELECT * FROM market WHERE marketId = %s;
    """, (market_id,))
    row = conn.fetchone()
    if not row:
        return None
    market = Market(**row, commodities=[])

    # Retrieve commodities
    conn.execute("""
        SELECT name, category, stock, demand, supply, buyPrice, sellPrice FROM market_commodity WHERE marketId = %s;
    """, (market_id,))
    commodities = conn.fetchall()
    market.commodities = [MarketCommodity(marketId=market_id, **c) for c in commodities]
    return market