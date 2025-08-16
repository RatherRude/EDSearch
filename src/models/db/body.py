from typing import ClassVar
from pydantic import BaseModel
import psycopg
from psycopg import sql
from psycopg.rows import DictRow

class Atmospherecomposition(BaseModel):
    sources: ClassVar[list[str]] = ["Scan"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "Name"]
    SystemAddress: int # Scan
    BodyID: int # Scan
    
    Percent: float # Scan.AtmosphereComposition[]
    Name: str # Scan.AtmosphereComposition[]
class Material(BaseModel):
    sources: ClassVar[list[str]] = ["Scan"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "Name"]
    SystemAddress: int # Scan
    BodyID: int # Scan
    
    Percent: float # Scan.Materials[]
    Name: str # Scan.Materials[]

class Ring(BaseModel):
    sources: ClassVar[list[str]] = ["Scan"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID", "Name"]
    SystemAddress: int # Scan
    BodyID: int # Scan
    
    OuterRad: float # Scan.Rings[]
    InnerRad: float # Scan.Rings[]
    RingClass: str # Scan.Rings[]
    Name: str # Scan.Rings[]
    MassMT: float # Scan.Rings[]

# None fields should be considered "unknown", meaning that no event has reported this field yet, e.g only FSDJump reported, all other fields are None
class Body(BaseModel): 
    sources: ClassVar[list[str]] = ["FSDJump", "ScanBaryCentre", "Scan"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "BodyID"]
    SystemAddress: int
    
    BodyID: int # JSDJump, ScanBaryCentre, Scan
    BodyType: str # JSDJump, ScanBaryCentre."BaryCentre", Scan.StarType ? 'Star' : 'Planet'
    BodyName: str # JSDJump.Body, ScanBaryCentre.StarSystem + " BaryCentre", Scan
    
    DistanceFromArrivalLS: float | None # Scan

    MeanAnomaly: float | None # ScanBaryCentre, Scan
    Eccentricity: float | None # ScanBaryCentre, Scan
    AscendingNode: float | None # ScanBaryCentre, Scan
    Periapsis: float | None # ScanBaryCentre, Scan
    SemiMajorAxis: float | None # ScanBaryCentre, Scan
    OrbitalPeriod: float | None # ScanBaryCentre, Scan
    OrbitalInclination: float | None # ScanBaryCentre, Scan
    
    TidalLock: bool | None # Scan
    RotationPeriod: float | None # Scan
    AxialTilt: float | None # Scan
    Radius: float | None # Scan
    MassEM: float | None # Scan
    StellarMass: float | None # Scan
    Age_MY: int | None # Scan
    
    StarType: str | None # Scan
    PlanetClass: str | None # Scan
    Subclass: int | None # Scan
    Parent: int | None # Scan.Parents[0][any]
    
    AtmosphereType: str | None # Scan
    AbsoluteMagnitude: float | None # Scan
    Luminosity: str | None # Scan
    SurfaceTemperature: float | None # Scan
    SurfaceGravity: float | None # Scan
    SurfacePressure: float | None # Scan
    Volcanism: str | None # Scan
    TerraformState: str | None # Scan
    Landable: bool | None # Scan
    Atmosphere: str | None # Scan
    ReserveLevel: str | None # Scan
    CompositionIce: float | None # Scan
    CompositionMetal: float | None # Scan
    CompositionRock: float | None # Scan
    
    # Foreign models
    numMaterials: int | None  # Indicates how many materials are associated with this body
    Materials: list[Material] | None # Scan
    numAtmosphereComposition: int | None  # Indicates how many atmosphere compositions are associated with this body
    AtmosphereComposition: list[Atmospherecomposition] | None # Scan
    numRings: int | None  # Indicates how many rings are associated with this body
    Rings: list[Ring] | None # Scan

def create_body_tables() -> str:
    """Create the body table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS body (
        SystemAddress BIGINT NOT NULL,
        BodyID INT NOT NULL,
        BodyType TEXT NOT NULL,
        BodyName TEXT NOT NULL,
        DistanceFromArrivalLS DOUBLE PRECISION,
        MeanAnomaly DOUBLE PRECISION,
        Eccentricity DOUBLE PRECISION,
        AscendingNode DOUBLE PRECISION,
        Periapsis DOUBLE PRECISION,
        SemiMajorAxis DOUBLE PRECISION,
        OrbitalPeriod DOUBLE PRECISION,
        OrbitalInclination DOUBLE PRECISION,
        TidalLock BOOLEAN,
        RotationPeriod DOUBLE PRECISION,
        AxialTilt DOUBLE PRECISION,
        Radius DOUBLE PRECISION,
        MassEM DOUBLE PRECISION,
        StellarMass DOUBLE PRECISION,
        Age_MY INT,
        StarType TEXT,
        PlanetClass TEXT,
        Subclass INT,
        Parent INT,
        AtmosphereType TEXT,
        AbsoluteMagnitude DOUBLE PRECISION,
        Luminosity TEXT,
        SurfaceTemperature DOUBLE PRECISION,
        SurfaceGravity DOUBLE PRECISION,
        SurfacePressure DOUBLE PRECISION,
        Volcanism TEXT,
        TerraformState TEXT,
        Landable BOOLEAN,
        Atmosphere TEXT,
        ReserveLevel TEXT,
        CompositionIce DOUBLE PRECISION,
        CompositionMetal DOUBLE PRECISION,
        CompositionRock DOUBLE PRECISION,
        numMaterials INT,
        numAtmosphereComposition INT,
        numRings INT,
        PRIMARY KEY (SystemAddress, BodyID)
    );

    CREATE TABLE IF NOT EXISTS body_atmosphere_composition (
        SystemAddress BIGINT NOT NULL,
        BodyID INT NOT NULL,
        Name TEXT NOT NULL,
        Percent DOUBLE PRECISION NOT NULL,
        PRIMARY KEY (SystemAddress, BodyID, Name),
        FOREIGN KEY (SystemAddress, BodyID) REFERENCES body (SystemAddress, BodyID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS body_material (
        SystemAddress BIGINT NOT NULL,
        BodyID INT NOT NULL,
        Name TEXT NOT NULL,
        Percent DOUBLE PRECISION NOT NULL,
        PRIMARY KEY (SystemAddress, BodyID, Name),
        FOREIGN KEY (SystemAddress, BodyID) REFERENCES body (SystemAddress, BodyID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS body_ring (
        SystemAddress BIGINT NOT NULL,
        BodyID INT NOT NULL,
        Name TEXT NOT NULL,
        OuterRad DOUBLE PRECISION NOT NULL,
        InnerRad DOUBLE PRECISION NOT NULL,
        RingClass TEXT NOT NULL,
        MassMT DOUBLE PRECISION NOT NULL,
        PRIMARY KEY (SystemAddress, BodyID, Name),
        FOREIGN KEY (SystemAddress, BodyID) REFERENCES body (SystemAddress, BodyID) ON DELETE CASCADE
    );
    """

def upsert_body(conn: psycopg.Cursor[DictRow], body: Body) -> None:
    """Upsert a body into the database, including its materials, atmosphere composition, and rings."""
    # Upsert the body
    body_dict = body.model_dump(exclude={'Materials', 'AtmosphereComposition', 'Rings'})
    
    columns = sql.SQL(', ').join(map(sql.SQL, body_dict.keys()))
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(body_dict))
    
    # ON CONFLICT DO UPDATE
    update_columns = sql.SQL(', ').join(
        sql.SQL("{} = EXCLUDED.{}").format(sql.SQL(k), sql.SQL(k)) for (k, v) in body_dict.items() if k not in ['SystemAddress', 'BodyID'] and v is not None
    )

    query = sql.SQL("""
        INSERT INTO body ({columns}) VALUES ({placeholders})
        ON CONFLICT (SystemAddress, BodyID) DO UPDATE SET {update_columns}
    """).format(
        columns=columns,
        placeholders=placeholders,
        update_columns=update_columns
    )
    
    conn.execute(query, tuple(body_dict.values()))

    # Insert materials
    if body.Materials is not None:
        conn.execute("DELETE FROM body_material WHERE SystemAddress = %s AND BodyID = %s;", (body.SystemAddress, body.BodyID))
        for material in body.Materials:
            conn.execute("""
                INSERT INTO body_material (SystemAddress, BodyID, Name, Percent) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (SystemAddress, BodyID, Name) DO NOTHING
            """, (body.SystemAddress, body.BodyID, material.Name, material.Percent))

    # Insert atmosphere composition
    if body.AtmosphereComposition is not None:
        conn.execute("DELETE FROM body_atmosphere_composition WHERE SystemAddress = %s AND BodyID = %s;", (body.SystemAddress, body.BodyID))
        for comp in body.AtmosphereComposition:
            conn.execute("""
                INSERT INTO body_atmosphere_composition (SystemAddress, BodyID, Name, Percent)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (SystemAddress, BodyID, Name) DO NOTHING
            """, (body.SystemAddress, body.BodyID, comp.Name, comp.Percent))

    # Insert rings
    if body.Rings is not None:
        conn.execute("DELETE FROM body_ring WHERE SystemAddress = %s AND BodyID = %s;", (body.SystemAddress, body.BodyID))
        for ring in body.Rings:
            conn.execute("""
                INSERT INTO body_ring (SystemAddress, BodyID, Name, OuterRad, InnerRad, RingClass, MassMT)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (SystemAddress, BodyID, Name) DO NOTHING
            """, (body.SystemAddress, body.BodyID, ring.Name, ring.OuterRad, ring.InnerRad, ring.RingClass, ring.MassMT))


def get_body(conn: psycopg.Cursor[DictRow], system_address: int, body_id: int) -> Body | None:
    """Retrieve a body by its system address and body ID."""
    conn.execute("""
        SELECT * FROM body WHERE SystemAddress = %s AND BodyID = %s;
    """, (system_address, body_id))
    row = conn.fetchone()
    if not row:
        return None
    
    body = Body(**row)

    # Retrieve materials
    conn.execute("""
        SELECT Name, Percent FROM body_material WHERE SystemAddress = %s AND BodyID = %s;
    """, (system_address, body_id))
    materials = conn.fetchall()
    body.Materials = [Material(SystemAddress=system_address, BodyID=body_id, **m) for m in materials]

    # Retrieve atmosphere composition
    conn.execute("""
        SELECT Name, Percent FROM body_atmosphere_composition WHERE SystemAddress = %s AND BodyID = %s;
    """, (system_address, body_id))
    atm_comp = conn.fetchall()
    body.AtmosphereComposition = [Atmospherecomposition(SystemAddress=system_address, BodyID=body_id, **ac) for ac in atm_comp]

    # Retrieve rings
    conn.execute("""
        SELECT Name, OuterRad, InnerRad, RingClass, MassMT FROM body_ring WHERE SystemAddress = %s AND BodyID = %s;
    """, (system_address, body_id))
    rings = conn.fetchall()
    body.Rings = [Ring(SystemAddress=system_address, BodyID=body_id, **r) for r in rings]

    return body
