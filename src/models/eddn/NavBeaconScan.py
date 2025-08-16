from typing import Literal,ClassVar
from pydantic import BaseModel


class NavBeaconScan(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    event: Literal["NavBeaconScan"]
    timestamp: str
    SystemAddress: int
    NumBodies: int
    
