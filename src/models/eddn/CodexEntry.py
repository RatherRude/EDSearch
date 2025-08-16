from typing import Literal,ClassVar
from pydantic import BaseModel
    
class CodexEntry(BaseModel):
    primary_keys: ClassVar[list[str]] = ["EntryID"]
    event: Literal["CodexEntry"]
    timestamp: str
    EntryID: int
    SystemAddress: int
    BodyID: int
    BodyName: str
    Latitude: float
    Longitude: float
    Name: str
    Region: str
    Category: str
    SubCategory: str
    NearestDestination: str
    VoucherAmount: int
    Traits: list[str]
    