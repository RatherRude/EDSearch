from pydantic import BaseModel
from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.system import SystemPower, Faction, FactionStateT, Conflict, System
from ..models.db.body import Body
from ..models.eddn.FSDJump import FSDJump
from ..models.db.ingestion import DatabaseModels

def convert_fsd_jump(fsdJump: FSDJump, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    powers: list[SystemPower] = []
    if fsdJump.Powers:
        for power in fsdJump.Powers:
            powers.append(SystemPower(
                SystemAddress=fsdJump.SystemAddress,
                Power=power
            ))
    
    factions: list[Faction] = []
    if fsdJump.Factions:
        for f in fsdJump.Factions:
            states: list[FactionStateT] = []
            if f.ActiveStates:
                for s in f.ActiveStates:
                    states.append(FactionStateT(SystemAddress=fsdJump.SystemAddress, FactionName=f.Name, Type='Active', State=s.State))

            if f.PendingStates:
                for s in f.PendingStates:
                    states.append(FactionStateT(SystemAddress=fsdJump.SystemAddress, FactionName=f.Name, Type='Pending', State=s.State, Trend=s.Trend))

            if f.RecoveringStates:
                for s in f.RecoveringStates:
                    states.append(FactionStateT(SystemAddress=fsdJump.SystemAddress, FactionName=f.Name, Type='Recovering', State=s.State, Trend=s.Trend))

            factions.append(Faction(
                SystemAddress=fsdJump.SystemAddress,
                Name=f.Name,
                Influence=f.Influence,
                Happiness=f.Happiness,
                Allegiance=f.Allegiance,
                SquadronFaction=f.SquadronFaction if f.SquadronFaction is not None else False,
                FactionState=f.FactionState,
                Government=f.Government,
                States=states
            ))

    conflicts: list[Conflict] = []
    if fsdJump.Conflicts:
        for c in fsdJump.Conflicts:
            conflicts.append(Conflict(
                SystemAddress=fsdJump.SystemAddress,
                Status=c.Status,
                WarType=c.WarType,
                Faction1Name=c.Faction1.Name,
                Faction1Stake=c.Faction1.Stake,
                Faction1WonDays=c.Faction1.WonDays,
                Faction2Name=c.Faction2.Name,
                Faction2Stake=c.Faction2.Stake,
                Faction2WonDays=c.Faction2.WonDays
            ))

    system = System(
        SystemAddress=fsdJump.SystemAddress,
        StarPos=fsdJump.StarPos,
        StarSystem=fsdJump.StarSystem,
        PrimaryBodyID=fsdJump.BodyID,
        PrimaryBodyType=fsdJump.BodyType,
        PrimaryBodyName=fsdJump.Body,
        Population=fsdJump.Population,
        Allegiance=fsdJump.SystemAllegiance,
        Economy=fsdJump.SystemEconomy,
        SecondEconomy=fsdJump.SystemSecondEconomy,
        FactionName=fsdJump.SystemFaction.Name if fsdJump.SystemFaction else '',
        FactionState=fsdJump.SystemFaction.State if fsdJump.SystemFaction and fsdJump.SystemFaction.State else '',
        Security=fsdJump.SystemSecurity,
        PowerplayState=fsdJump.PowerplayState if fsdJump.PowerplayState else '',
        Government=fsdJump.SystemGovernment,
        numPowers=len(powers),
        Powers=powers,
        numFactions=len(factions),
        Factions=factions,
        numConflicts=len(conflicts),
        Conflicts=conflicts
    )
    dbModels.systems.append(system)
    
    body = Body(
        SystemAddress=fsdJump.SystemAddress,
        BodyID=fsdJump.BodyID,
        BodyName=fsdJump.Body,
        BodyType=fsdJump.BodyType,
        DistanceFromArrivalLS=None,
        MeanAnomaly=None,
        Eccentricity=None,
        AscendingNode=None,
        Periapsis=None,
        SemiMajorAxis=None,
        OrbitalPeriod=None,
        OrbitalInclination=None,
        TidalLock=None,
        RotationPeriod=None,
        AxialTilt=None,
        Radius=None,
        MassEM=None,
        StellarMass=None,
        Age_MY=None,
        StarType=None,
        PlanetClass=None,
        Subclass=None,
        Parent=None,
        AtmosphereType=None,
        AbsoluteMagnitude=None,
        Luminosity=None,
        SurfaceTemperature=None,
        SurfaceGravity=None,
        SurfacePressure=None,
        Volcanism=None,
        TerraformState=None,
        Landable=None,
        Atmosphere=None,
        ReserveLevel=None,
        CompositionIce=None,
        CompositionMetal=None,
        CompositionRock=None,
        numMaterials=None,
        Materials=None,
        numAtmosphereComposition=None,
        AtmosphereComposition=None,
        numRings=None,
        Rings=None
    )
    dbModels.bodies.append(body)

    return dbModels