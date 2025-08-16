from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.body import Body, Material, Atmospherecomposition, Ring
from ..models.eddn.Scan import Scan
from ..models.db.ingestion import DatabaseModels


def convert_scan(scan: Scan, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    # Convert materials
    materials: list[Material] | None = None
    if scan.Materials is not None:
        materials = []
        for m in scan.Materials:
            materials.append(Material(
                SystemAddress=scan.SystemAddress,
                BodyID=scan.BodyID,
                Percent=m.Percent,
                Name=m.Name
            ))
    
    # Convert atmosphere composition
    atmosphere_composition: list[Atmospherecomposition] | None = None
    if scan.AtmosphereComposition is not None:
        atmosphere_composition = []
        for ac in scan.AtmosphereComposition:
            atmosphere_composition.append(Atmospherecomposition(
                SystemAddress=scan.SystemAddress,
                BodyID=scan.BodyID,
                Percent=ac.Percent,
                Name=ac.Name
            ))
    
    # Convert rings
    rings: list[Ring] | None = None
    if scan.Rings is not None:
        rings = []
        for r in scan.Rings:
            rings.append(Ring(
                SystemAddress=scan.SystemAddress,
                BodyID=scan.BodyID,
                OuterRad=r.OuterRad,
                InnerRad=r.InnerRad,
                RingClass=r.RingClass,
                Name=r.Name,
                MassMT=r.MassMT
            ))
    
    # Determine body type based on scan type and star/planet class
    body_type = 'Unknown'
    if scan.StarType:
        body_type = 'Star'
    elif scan.PlanetClass:
        body_type = 'Planet'
    
    # Get parent body ID from the first parent entry
    parent: int | None = None
    if scan.Parents is not None:
        if scan.Parents:   
            first_parent = scan.Parents[0]
            if first_parent.Star is not None:
                parent = first_parent.Star
            elif first_parent.Planet is not None:
                parent = first_parent.Planet
            elif first_parent.Ring is not None:
                parent = first_parent.Ring
            elif first_parent.Null is not None:
                parent = first_parent.Null
        else:
            parent = -1
    
    # Create the Body model
    body = Body(
        SystemAddress=scan.SystemAddress,
        BodyID=scan.BodyID,
        BodyType=body_type,
        BodyName=scan.BodyName,
        DistanceFromArrivalLS=scan.DistanceFromArrivalLS,
        MeanAnomaly=scan.MeanAnomaly,
        Eccentricity=scan.Eccentricity,
        AscendingNode=scan.AscendingNode,
        Periapsis=scan.Periapsis,
        SemiMajorAxis=scan.SemiMajorAxis,
        OrbitalPeriod=scan.OrbitalPeriod,
        OrbitalInclination=scan.OrbitalInclination,
        TidalLock=scan.TidalLock,
        RotationPeriod=scan.RotationPeriod,
        AxialTilt=scan.AxialTilt,
        Radius=scan.Radius,
        MassEM=scan.MassEM,
        StellarMass=scan.StellarMass,
        Age_MY=scan.Age_MY,
        StarType=scan.StarType,
        PlanetClass=scan.PlanetClass,
        Subclass=scan.Subclass,
        Parent=parent,
        AtmosphereType=scan.AtmosphereType,
        AbsoluteMagnitude=scan.AbsoluteMagnitude,
        Luminosity=scan.Luminosity,
        SurfaceTemperature=scan.SurfaceTemperature,
        SurfaceGravity=scan.SurfaceGravity,
        SurfacePressure=scan.SurfacePressure,
        Volcanism=scan.Volcanism,
        TerraformState=scan.TerraformState,
        Landable=scan.Landable,
        Atmosphere=scan.Atmosphere,
        ReserveLevel=scan.ReserveLevel,
        CompositionIce=scan.Composition.Ice if scan.Composition else None,
        CompositionMetal=scan.Composition.Metal if scan.Composition else None,
        CompositionRock=scan.Composition.Rock if scan.Composition else None,
        numMaterials=len(materials) if materials is not None else None,
        Materials=materials,
        numAtmosphereComposition=len(atmosphere_composition) if atmosphere_composition is not None else None,
        AtmosphereComposition=atmosphere_composition,
        numRings=len(rings) if rings is not None else None,
        Rings=rings
    )
    dbModels.bodies.append(body)

    return dbModels
