from typing import Literal,ClassVar
from pydantic import BaseModel

    
class FCMaterial(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID", "id"]
    foreign_ref: ClassVar[list[str]] = ["FCMaterials"]
    id: int
    Name: str
    Price: int
    Stock: int
    Demand: int
    
class FCMaterials(BaseModel):
    primary_keys: ClassVar[list[str]] = ["MarketID"]
    event: Literal["FCMaterials"]
    timestamp: str
    SystemAddress: int
    MarketID: int
    CarrierID: str
    CarrierName: str
    Items: list[FCMaterial]
    