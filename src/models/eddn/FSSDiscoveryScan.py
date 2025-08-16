from typing import Literal,ClassVar
from pydantic import BaseModel


class FSSDiscoveryScan(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    event: Literal["FSSDiscoveryScan"]
    timestamp: str
    SystemAddress: int
    BodyCount: int
    NonBodyCount: int
    