from typing import Literal,ClassVar
from pydantic import BaseModel


class CarrierJump(BaseModel):
    # TODO this is incomplete for System and body data
    # TODO figure out why ~1/4 of events have no MarketID
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    event: Literal["CarrierJump"]
    timestamp: str
    SystemAddress: int
    MarketID: int
    StationName: str
    StationType: str
