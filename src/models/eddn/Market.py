from typing import Literal,ClassVar
from pydantic import BaseModel

class MarketCommodity(BaseModel):
    name: str
    category: str | None = None
    stock: int = 0
    demand: int = 0
    supply: int = 0
    buyPrice: int = 0
    sellPrice: int = 0

class Market(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId"]
    event: Literal["Market"] = "Market"
    timestamp: str
    marketId: int
    #stationName: str
    #starSystem: str
    commodities: list[MarketCommodity]
    prohibited: list[str] = [] # TODO does left out mean empty or not known?