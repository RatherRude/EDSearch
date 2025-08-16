from typing import Literal,ClassVar
from pydantic import BaseModel

class FSSBodySignal(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["FSSBodySignals"]
    Type: str
    Count: int

class FSSBodySignals(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID"]
    event: Literal["FSSBodySignals"]
    timestamp: str
    SystemAddress: int
    BodyID: int
    BodyName: str
    Signals: list[FSSBodySignal]
