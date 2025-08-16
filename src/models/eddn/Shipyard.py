from typing import Literal,ClassVar
from pydantic import BaseModel

class Shipyard(BaseModel):
    # TODO incomplete
    primary_keys: ClassVar[list[str]] = ["marketId"]
    event: Literal["Shipyard"] = "Shipyard"
    timestamp: str
    marketId: int
    ships: list[str]
    