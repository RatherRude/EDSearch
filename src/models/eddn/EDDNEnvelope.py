from pydantic import BaseModel
from typing import Any, Generic, Literal, ClassVar, TypeVar


class EDDNHeader(BaseModel):
    uploaderID: str
    gameversion: str | None = None
    gamebuild: str | None = None
    softwareName: str
    softwareVersion: str
    gatewayTimestamp: str | None = None
    
class EDDNMessage(BaseModel):
    #event: str | None = None
    horizons: bool = False
    odyssey: bool = False
    timestamp: str
    
    # allow extra fields for casting into the specific event models
    class Config:
        extra: str = "allow"

class EDDNEnvelope(BaseModel):
    header: EDDNHeader
    message: EDDNMessage
    