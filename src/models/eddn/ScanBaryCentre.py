from typing import Literal,ClassVar
from pydantic import BaseModel

class ScanBaryCentre(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID"]
    event: Literal["ScanBaryCentre"]
    timestamp: str
    SystemAddress: int
    StarSystem: str
    BodyID: int
    
    MeanAnomaly: float
    Eccentricity: float
    AscendingNode: float
    Periapsis: float
    SemiMajorAxis: float
    OrbitalPeriod: float
    OrbitalInclination: float