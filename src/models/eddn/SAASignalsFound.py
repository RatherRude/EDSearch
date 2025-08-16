from typing import Literal,ClassVar
from pydantic import BaseModel

class SAASignalsFoundSignalsItem(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["SAASignalsFound"]
    Type: str
    Count: int
class SAASignalsFoundGenusesItem(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["SAASignalsFound"]
    Genus: str
class SAASignalsFound(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "Type", "Genus"]
    event: Literal["SAASignalsFound"]
    BodyID: int
    Signals: list[SAASignalsFoundSignalsItem]
    Genuses: list[SAASignalsFoundGenusesItem] = []
    SystemAddress: int
    timestamp: str
    BodyName: str