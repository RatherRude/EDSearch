from typing import Literal,ClassVar
from pydantic import BaseModel


class NavRouteItem(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["NavRoute"]
    StarSystem: str
    StarPos: list[float]
    SystemAddress: int
    StarClass: str

class NavRoute(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    event: Literal["NavRoute"]
    timestamp: str
    SystemAddress: int
    Route: list[NavRouteItem]
    