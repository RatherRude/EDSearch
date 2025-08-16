from typing import Literal,ClassVar
from pydantic import BaseModel


    
class FSSSignal(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "SignalName"] # TODO check if this is correct
    event: Literal["FSSSignalDiscovered"] = "FSSSignalDiscovered"
    timestamp: str
    SystemAddress: int | None = None
    SignalType: str | None = None
    IsStation: bool = False
    SignalName: str
    
class FSSSignalDiscovered(BaseModel):
    # Just a wrapper for batching FSSSignal
    event: Literal["FSSSignalDiscovered"] = "FSSSignalDiscovered"
    timestamp: str
    SystemAddress: int
    signals: list[FSSSignal]
