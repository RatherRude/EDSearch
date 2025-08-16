from typing import ClassVar, Literal
import psycopg
from psycopg import sql
from psycopg.rows import DictRow
from pydantic import BaseModel

class Conflict(BaseModel):
    sources: ClassVar[list[str]] = ["FSDJump"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "Faction1Name", "Faction2Name"]
    SystemAddress: int # FSDJump
    
    Status: str # FSDJump.Conflicts[]
    WarType: str # FSDJump.Conflicts[]
    Faction1Name: str # FSDJump.Conflicts[]
    Faction1Stake: str # FSDJump.Conflicts[]
    Faction1WonDays: int # FSDJump.Conflicts[]
    Faction2Name: str # FSDJump.Conflicts[]
    Faction2Stake: str # FSDJump.Conflicts[]
    Faction2WonDays: int # FSDJump.Conflicts[]
    
class FactionStateT(BaseModel):
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "FactionName", "Type", "State"]
    SystemAddress: int # FSDJump
    FactionName: str # FSDJump.Factions[]
    
    Type: Literal["Active", "Recovering", "Pending"]
    State: str  # FSDJump.Factions[].ActiveStates[], FSDJump.Factions[].PendingStates[], FSDJump.Factions[].RecoveringStates[]
    Trend: int = 0 # FSDJump.Factions[].PendingStates[], FSDJump.Factions[].RecoveringStates[]
class Faction(BaseModel):
    sources: ClassVar[list[str]] = ["FSDJump"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "Name"]
    SystemAddress: int # FSDJump
    Name: str # FSDJump
    
    Influence: float # FSDJump.Factions[]
    Happiness: str # FSDJump.Factions[]
    Allegiance: str # FSDJump.Factions[]
    SquadronFaction: bool # FSDJump.Factions[]
    FactionState: str # FSDJump.Factions[]
    Government: str # FSDJump.Factions[]
    
    # Foreign models
    States: list[FactionStateT] # FSDJump.Factions[]
    
class SystemPower(BaseModel):
    sources: ClassVar[list[str]] = ["FSDJump"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress", "Power"]
    SystemAddress: int  # FSDJump
    Power: str # FSDJump.Power[]

# None fields should be considered "unknown", meaning that no event has reported this field yet
class System(BaseModel): 
    sources: ClassVar[list[str]] = ["FSDJump"]
    primary_keys: ClassVar[list[str]] = ["SystemAddress"]
    SystemAddress: int # FSDJump
    StarPos: list[float] # FSDJump
    StarSystem: str # FSDJump
    
    PrimaryBodyID: int | None # FSDJump
    PrimaryBodyType: str | None # FSDJump
    PrimaryBodyName: str | None # FSDJump.Body
    
    Population: int | None # FSDJump
    
    Allegiance: str | None # FSDJump
    Economy: str | None # FSDJump
    SecondEconomy: str | None # FSDJump
    FactionName: str | None # FSDJump
    FactionState: str | None # FSDJump
    Security: str | None # FSDJump
    PowerplayState: str | None # FSDJump
    Government: str | None # FSDJump
    
    # Foreign models
    numPowers: int | None  # Indicates how many powers are associated with this system
    Powers: list[SystemPower] # FSDJump.Power
    numFactions: int | None  # Indicates how many factions are associated with this system
    Factions: list[Faction]  # FSDJump.Factions
    numConflicts: int | None  # Indicates how many conflicts are associated with this system
    Conflicts: list[Conflict]  # FSDJump.Conflicts
    

def create_system_tables() -> str:
    return """
    CREATE TABLE IF NOT EXISTS system (
        SystemAddress BIGINT NOT NULL,
        StarPos vector(3) NOT NULL,
        StarSystem TEXT NOT NULL,
        PrimaryBodyID BIGINT,
        PrimaryBodyType TEXT,
        PrimaryBodyName TEXT,
        Population BIGINT,
        Allegiance TEXT,
        Economy TEXT,
        SecondEconomy TEXT,
        FactionName TEXT,
        FactionState TEXT,
        Security TEXT,
        PowerplayState TEXT,
        Government TEXT,
        numPowers INT,
        numFactions INT,
        numConflicts INT,
        PRIMARY KEY (SystemAddress)
    );
    
    -- Create HNSW index for vector search on StarPos
    CREATE INDEX IF NOT EXISTS idx_system_star_pos
        ON system USING hnsw
        (StarPos vector_l2_ops);
    -- Create B-tree index for text search on StarSystem
    CREATE INDEX IF NOT EXISTS idx_system_star_system
        ON system USING btree
        (StarSystem COLLATE pg_catalog."default" ASC NULLS LAST);


    CREATE TABLE IF NOT EXISTS system_power (
        SystemAddress BIGINT NOT NULL,
        Power TEXT NOT NULL,
        PRIMARY KEY (SystemAddress, Power),
        FOREIGN KEY (SystemAddress) REFERENCES system (SystemAddress) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS system_faction (
        SystemAddress BIGINT NOT NULL,
        Name TEXT NOT NULL,
        Influence DOUBLE PRECISION NOT NULL,
        Happiness TEXT NOT NULL,
        Allegiance TEXT NOT NULL,
        SquadronFaction BOOLEAN,
        FactionState TEXT NOT NULL,
        Government TEXT NOT NULL,
        PRIMARY KEY (SystemAddress, Name),
        FOREIGN KEY (SystemAddress) REFERENCES system (SystemAddress) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS system_faction_state (
        SystemAddress BIGINT NOT NULL,
        FactionName TEXT NOT NULL,
        Type TEXT NOT NULL,
        State TEXT NOT NULL,
        Trend INT NOT NULL,
        PRIMARY KEY (SystemAddress, FactionName, Type, State),
        FOREIGN KEY (SystemAddress, FactionName) REFERENCES system_faction (SystemAddress, Name) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS system_conflict (
        SystemAddress BIGINT NOT NULL,
        Status TEXT NOT NULL,
        WarType TEXT NOT NULL,
        Faction1Name TEXT NOT NULL,
        Faction1Stake TEXT NOT NULL,
        Faction1WonDays INT NOT NULL,
        Faction2Name TEXT NOT NULL,
        Faction2Stake TEXT NOT NULL,
        Faction2WonDays INT NOT NULL,
        PRIMARY KEY (SystemAddress, Faction1Name, Faction2Name),
        FOREIGN KEY (SystemAddress) REFERENCES system (SystemAddress) ON DELETE CASCADE
    );
    """

def upsert_system(conn: psycopg.Cursor[DictRow], system: System) -> None:
    """Upsert a system into the database, including its power."""
    # Upsert the system
    system_dict = system.model_dump(exclude={'Powers', 'Factions', 'Conflicts'})
    columns = sql.SQL(', ').join(map(sql.SQL, system_dict.keys()))
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(system_dict))
    
    # ON CONFLICT DO UPDATE
    update_columns = sql.SQL(', ').join(
        sql.SQL("{} = EXCLUDED.{}").format(sql.SQL(k), sql.SQL(k)) for (k, v) in system_dict.items() if v is not None
    )

    query = sql.SQL("""
        INSERT INTO system ({columns}) VALUES ({placeholders})
        ON CONFLICT (SystemAddress) DO UPDATE SET {update_columns}
    """).format(
        columns=columns,
        placeholders=placeholders,
        update_columns=update_columns
    )
    
    conn.execute(query, tuple(system_dict.values()))

    # Insert the system's powers
    if system.Powers is not None:
        conn.execute("DELETE FROM system_power WHERE SystemAddress = %s;", (system.SystemAddress,))
        for power in system.Powers:
            conn.execute("""
                INSERT INTO system_power (SystemAddress, Power) VALUES (%s, %s)
                ON CONFLICT (SystemAddress, Power) DO NOTHING;
            """, (system.SystemAddress, power.Power))

    # Insert factions and their states
    if system.Factions is not None:
        conn.execute("DELETE FROM system_faction WHERE SystemAddress = %s;", (system.SystemAddress,))
        for faction in system.Factions:
            faction_dict = faction.model_dump(exclude={'States'})
            faction_columns = sql.SQL(', ').join(map(sql.SQL, faction_dict.keys()))
            faction_placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(faction_dict))
            faction_query = sql.SQL("INSERT INTO system_faction ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(faction_columns, faction_placeholders)
            conn.execute(faction_query, tuple(faction_dict.values()))

            if faction.States:
                for state in faction.States:
                    state_dict = state.model_dump()
                    state_dict['FactionName'] = faction.Name # Add FactionName for the foreign key
                    state_columns = sql.SQL(', ').join(map(sql.SQL, state_dict.keys()))
                    state_placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(state_dict))
                    state_query = sql.SQL("INSERT INTO system_faction_state ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(state_columns, state_placeholders)
                    conn.execute(state_query, tuple(state_dict.values()))

    # Insert conflicts
    if system.Conflicts is not None:
        conn.execute("DELETE FROM system_conflict WHERE SystemAddress = %s;", (system.SystemAddress,))
        for conflict in system.Conflicts:
            conflict_dict = conflict.model_dump()
            conflict_columns = sql.SQL(', ').join(map(sql.SQL, conflict_dict.keys()))
            conflict_placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(conflict_dict))
            conflict_query = sql.SQL("INSERT INTO system_conflict ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(conflict_columns, conflict_placeholders)
            conn.execute(conflict_query, tuple(conflict_dict.values()))


def get_system(conn: psycopg.Cursor[DictRow], system_address: int) -> System | None:
    """Retrieve a system by its address."""
    conn.execute("""
        SELECT * FROM system WHERE SystemAddress = %s;
    """, (system_address,))
    row = conn.fetchone()
    if not row:
        return None
    system = System(**row)
    
    # Retrieve powers associated with the system
    conn.execute("""
        SELECT Power FROM system_power WHERE SystemAddress = %s;
    """, (system_address,))
    powers = conn.fetchall()
    system.Powers = [SystemPower(SystemAddress=system_address, Power=power["Power"]) for power in powers]

    # Retrieve factions and their states
    conn.execute("""
        SELECT * FROM system_faction WHERE SystemAddress = %s;
    """, (system_address,))
    factions_rows = conn.fetchall()
    factions = []
    for faction_row in factions_rows:
        faction = Faction(**faction_row)
        conn.execute("""
            SELECT Type, State, Trend FROM system_faction_state WHERE SystemAddress = %s AND FactionName = %s;
        """, (system_address, faction.Name))
        states_rows = conn.fetchall()
        faction.States = [FactionStateT(SystemAddress=system_address, FactionName=faction.Name, **state_row) for state_row in states_rows]
        factions.append(faction)
    system.Factions = factions

    # Retrieve conflicts
    conn.execute("""
        SELECT * FROM system_conflict WHERE SystemAddress = %s;
    """, (system_address,))
    conflicts_rows = conn.fetchall()
    system.Conflicts = [Conflict(**conflict_row) for conflict_row in conflicts_rows]

    return system