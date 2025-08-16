from typing import Literal,ClassVar
from pydantic import BaseModel

class StationEconomy(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Docked"]
    Name: str
    Proportion: float

class StationFaction(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Docked"]
    Name: str
    FactionState: str = 'None'
    
class LandingPads(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Docked"]
    Small: int
    Medium: int
    Large: int

class Docked(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    event: Literal["Docked"]
    timestamp: str
    SystemAddress: int
    MarketID: int
    StationName: str
    StationType: str
    DistFromStarLS: float
    StationGovernment: str
    StationAllegiance: str = 'Independent'
    StationEconomies: list[StationEconomy]
    StationFaction: StationFaction
    StationServices: list[str]
    StationEconomy: str
    StationState: str = 'None'
    LandingPads: LandingPads
