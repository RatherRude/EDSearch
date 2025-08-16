from sre_parse import State
from typing import Literal,ClassVar
from pydantic import BaseModel

class FactionPendingstate(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Faction"]
    State: str
    Trend: int
class FactionActivestate(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Faction"]
    State: str
class FactionRecoveringstate(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Faction"]
    State: str
    Trend: int
class Faction(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "Name"]
    SystemAddress: int
    Influence: float
    Happiness: str
    PendingStates: list[FactionPendingstate] | None = None
    ActiveStates: list[FactionActivestate] | None = None
    Allegiance: str
    SquadronFaction: bool | None = None
    MyReputation: float
    Name: str
    FactionState: str
    RecoveringStates: list[FactionRecoveringstate] | None = None
    Government: str
class Thargoidwar(BaseModel):   
    foreign_ref: ClassVar[list[str]] = ["Location"]
    SuccessStateReached: bool
    EstimatedRemainingTime: str | None = None
    CurrentState: str
    RemainingPorts: int
    NextStateFailure: str
    WarProgress: float
    NextStateSuccess: str
class ConflictFaction(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Conflict"]
    Name: str
    Stake: str
    WonDays: int
class Conflict(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Location"]
    Status: str
    WarType: str
    Faction1: ConflictFaction
    Faction2: ConflictFaction

class Stationeconomy(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Location"]
    Proportion: float
    Name: str

class StationFaction(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Location"]
    Name: str
    FactionState: str | None = None
class SystemFaction(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["Location"]
    Name: str
    State: str | None = None
    
class Location(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "MarketID", "BodyID"]
    event: Literal["Location"]
    timestamp: str
    SystemAddress: int | None = None
    MarketID: int | None = None
    BodyID: int | None = None
    StationAllegiance: str | None = None
    SystemAllegiance: str
    SystemEconomy: str
    DistFromStarLS: float | None = None
    SystemFaction: None | SystemFaction = None  # pyright: ignore[reportGeneralTypeIssues, reportInvalidTypeForm]
    SystemSecurity: str
    StarPos: list[float]
    Longitude: float | None = None
    InSRV: bool | None = None
    Factions: list[Faction] | None = None
    PowerplayState: str | None = None
    Multicrew: bool | None = None
    StationEconomy: str | None = None
    Taxi: bool | None = None
    StationGovernment: str | None = None
    StationName: str | None = None
    SystemSecondEconomy: str | None = None
    StationType: str | None = None
    Latitude: float | None = None
    Population: int | None = None
    BodyType: str | None = None
    Body: str | None = None
    Powers: list[str] | None = None
    StationEconomies: list[Stationeconomy] | None = None
    Docked: bool | None = None
    StationServices: list[str] | None = None
    OnFoot: bool | None = None
    StationFaction: StationFaction | None = None  # pyright: ignore[reportGeneralTypeIssues, reportInvalidTypeForm]
    StarSystem: str | None = None
    ThargoidWar: Thargoidwar | None = None
    Conflicts: list[Conflict] | None = None
    SystemGovernment: str | None = None
    