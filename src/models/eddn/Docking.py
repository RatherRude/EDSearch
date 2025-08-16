from typing import Literal,ClassVar
from pydantic import BaseModel


class DockingDenied(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    event: Literal["DockingDenied"]
    timestamp: str
    SystemAddress: int
    MarketID: str
    StationName: str
    StationType: str
    Reason: str
    
class DockingGranted(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    event: Literal["DockingGranted"]
    timestamp: str
    SystemAddress: int
    MarketID: int
    StationName: str
    StationType: str
    LandingPad: int
    