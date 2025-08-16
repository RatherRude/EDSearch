from typing import Any, Literal,ClassVar
from pydantic import BaseModel

class StationEconomy(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["ApproachSettlement"]
    Name: str
    Proportion: float
    
class StationFactionT(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["ApproachSettlement"]
    Name: str = 'None'
    FactionState: str = 'None'

class ApproachSettlement(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID", "SystemAddress", "BodyID", "Name"]
    event: Literal["ApproachSettlement"]
    timestamp: str
    SystemAddress: int
    MarketID: int | None = None
    Name: str
    BodyID: int
    BodyName: str
    Latitude: float
    Longitude: float
    StationGovernment: str = 'None'
    StationAllegiance: str = 'Independent'
    StationEconomies: list[StationEconomy] = []
    StationFaction: StationFactionT = StationFactionT()
    StationServices: list[str] = []
    StationEconomy: str = 'None'
