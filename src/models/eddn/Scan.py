from typing import Literal,ClassVar
from pydantic import BaseModel
    

class Atmospherecomposition(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Scan"]
    Percent: float
    Name: str
class ScanMaterial(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Scan"]
    Percent: float
    Name: str
class ScanParent(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Scan"]
    Star: int | None = None
    Null: int | None = None
    Ring: int | None = None
    Planet: int | None = None
class ScanComposition(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Scan"]
    Ice: float
    Metal: float
    Rock: float
class ScanRing(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Scan"]
    OuterRad: float
    InnerRad: float
    RingClass: str
    Name: str
    MassMT: float
    
class Scan(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "ScanType"]
    event: Literal["Scan"]
    timestamp: str
    ScanType: str
    SystemAddress: int
    StarSystem: str
    BodyID: int
    BodyName: str
    
    DistanceFromArrivalLS: float
    
    MeanAnomaly: float | None = None
    Eccentricity: float | None = None
    AscendingNode: float | None = None
    Periapsis: float | None = None
    SemiMajorAxis: float | None = None
    OrbitalPeriod: float | None = None
    OrbitalInclination: float | None = None
    
    TidalLock: bool | None = None
    RotationPeriod: float | None = None
    AxialTilt: float | None = None
    Radius: float | None = None
    MassEM: float | None = None
    StellarMass: float | None = None
    Age_MY: int | None = None
    
    StarType: str | None = None
    PlanetClass: str | None = None
    Subclass: int | None = None
    Parents: list[ScanParent] | None = None
    
    AtmosphereType: str | None = None
    AbsoluteMagnitude: float | None = None
    Luminosity: str | None = None
    SurfaceTemperature: float | None = None
    SurfaceGravity: float | None = None
    SurfacePressure: float | None = None
    Volcanism: str | None = None
    TerraformState: str | None = None
    Landable: bool | None = None
    Atmosphere: str | None = None
    ReserveLevel: str | None = None
    Composition: ScanComposition | None = None
    Materials: list[ScanMaterial] | None = None
    AtmosphereComposition: list[Atmospherecomposition] | None = None
    Rings: list[ScanRing] | None = None