from pydantic import BaseModel

from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.ingestion import DatabaseModels
from ..models.eddn.ScanBaryCentre import ScanBaryCentre
from ..models.db.body import Body


def convert_scanbarycentre(scan: ScanBaryCentre, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    # Determine body type based on scan type and star/planet class
    body_type = 'Barycentre'
    
    # Create the Body model
    body = Body(
        SystemAddress=scan.SystemAddress,
        BodyID=scan.BodyID,
        BodyType=body_type,
        BodyName=scan.StarSystem+ " Barycentre",
        DistanceFromArrivalLS=None,
        MeanAnomaly=scan.MeanAnomaly,
        Eccentricity=scan.Eccentricity,
        AscendingNode=scan.AscendingNode,   
        Periapsis=scan.Periapsis,
        SemiMajorAxis=scan.SemiMajorAxis,
        OrbitalPeriod=scan.OrbitalPeriod,
        OrbitalInclination=scan.OrbitalInclination,
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
