from typing import Literal,ClassVar
from pydantic import BaseModel

class Outfitting(BaseModel):
    primary_keys: ClassVar[list[str]] = ["marketId"]
    event: Literal["Outfitting"] = "Outfitting"
    timestamp: str
    marketId: int
    modules: list[str]