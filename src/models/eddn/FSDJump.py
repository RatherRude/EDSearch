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
    Influence: float
    Happiness: str
    PendingStates: list[FactionPendingstate] | None = None
    ActiveStates: list[FactionActivestate] | None = None
    Allegiance: str
    SquadronFaction: bool | None = None
    Name: str
    FactionState: str
    RecoveringStates: list[FactionRecoveringstate] | None = None
    Government: str
class Thargoidwar(BaseModel):   
    foreign_ref: ClassVar[list[str]] = ["FSDJump"]
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
    foreign_ref: ClassVar[list[str]] = ["FSDJump"]
    Status: str
    WarType: str
    Faction1: ConflictFaction
    Faction2: ConflictFaction
class SystemFactionT(BaseModel):
    foreign_ref: ClassVar[list[str]] = ["FSDJump"]
    Name: str
    State: str | None = None
class FSDJump(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    event: Literal["FSDJump"]
    timestamp: str
    SystemAddress: int
    BodyID: int
    SystemAllegiance: str
    SystemFaction: SystemFactionT | None = None
    SystemSecurity: str
    StarPos: list[float]
    PowerplayState: str | None = None
    Factions: list[Faction] | None = None
    SystemEconomy: str
    SystemSecondEconomy: str
    Population: int
    BodyType: str
    Body: str
    Powers: list[str] | None = None
    StarSystem: str
    ThargoidWar: Thargoidwar | None = None
    Conflicts: list[Conflict] | None = None
    SystemGovernment: str
