from typing import Literal,ClassVar
from pydantic import BaseModel

class FSSAllBodiesFound(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    event: Literal["FSSAllBodiesFound"]
    timestamp: str
    SystemAddress: int
    Count: int
