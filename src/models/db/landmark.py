from typing import ClassVar
import psycopg
from psycopg import sql
from psycopg.rows import DictRow
from pydantic import BaseModel

    
class Landmark(BaseModel):
    sources: ClassVar[list[str]] = ["CodexEntry", "ApproachSettlement"]
    primary_keys: ClassVar[list[str]] = ["EntryID", "AuxiliaryID"]
    EntryID: int | None
    AuxiliaryID: str | None
    SystemAddress: int
    BodyID: int
    Latitude: float
    Longitude: float
    Name: str

    Region: str | None
    Category: str | None
    SubCategory: str | None
    NearestDestination: str | None
    VoucherAmount: int | None
    numTraits: int | None
    Traits: list[str] | None

def create_landmark_tables() -> str:
    """Create the landmark table and related tables."""
    return """
    CREATE TABLE IF NOT EXISTS landmark (
        id SERIAL PRIMARY KEY,
        EntryID BIGINT,
        AuxiliaryID TEXT,
        SystemAddress BIGINT NOT NULL,
        BodyID INT NOT NULL,
        Latitude DOUBLE PRECISION NOT NULL,
        Longitude DOUBLE PRECISION NOT NULL,
        Name TEXT NOT NULL,
        Region TEXT,
        Category TEXT,
        SubCategory TEXT,
        NearestDestination TEXT,
        VoucherAmount INT,
        numTraits INT
    );

    -- Create unique constraint that handles nulls properly
    CREATE UNIQUE INDEX IF NOT EXISTS idx_landmark_unique_entries 
    ON landmark (COALESCE(EntryID, -1), COALESCE(AuxiliaryID, ''));

    CREATE TABLE IF NOT EXISTS landmark_trait (
        id SERIAL PRIMARY KEY,
        landmark_id INT NOT NULL,
        Trait TEXT NOT NULL,
        UNIQUE (landmark_id, Trait),
        FOREIGN KEY (landmark_id) REFERENCES landmark (id) ON DELETE CASCADE
    );
    """

def upsert_landmark(conn: psycopg.Cursor[DictRow], landmark: Landmark) -> None:
    """Upsert a landmark into the database, including its traits."""
    # Upsert the landmark
    landmark_dict = landmark.model_dump(exclude={'Traits'})
    
    columns = list(landmark_dict.keys())
    column_names = sql.SQL(', ').join([sql.SQL(col) for col in columns])
    placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(landmark_dict))
    
    # ON CONFLICT DO UPDATE
    update_columns = sql.SQL(', ').join(
        sql.SQL(k) + sql.SQL(" = EXCLUDED.") + sql.SQL(k) 
        for k, v in landmark_dict.items() 
        if k not in ['EntryID', 'AuxiliaryID'] and v is not None
    )

    query = sql.SQL("""
        INSERT INTO landmark ({columns}) VALUES ({placeholders})
        ON CONFLICT (COALESCE(EntryID, -1), COALESCE(AuxiliaryID, '')) DO UPDATE SET {update_columns}
        RETURNING id
    """).format(
        columns=column_names,
        placeholders=placeholders,
        update_columns=update_columns
    )
    
    conn.execute(query, tuple(landmark_dict.values()))
    result = conn.fetchone()
    landmark_id = result['id'] if result else None

    # Insert traits
    if landmark.Traits is not None and landmark_id is not None:
        conn.execute("DELETE FROM landmark_trait WHERE landmark_id = %s;", (landmark_id,))
        for trait in landmark.Traits:
            conn.execute("""
                INSERT INTO landmark_trait (landmark_id, Trait) 
                VALUES (%s, %s)
                ON CONFLICT (landmark_id, Trait) DO NOTHING
            """, (landmark_id, trait))

def get_landmark(conn: psycopg.Cursor[DictRow], entry_id: int | None, auxiliary_id: str | None) -> Landmark | None:
    """Retrieve a landmark by its entry ID and auxiliary ID."""
    conn.execute("""
        SELECT * FROM landmark WHERE EntryID IS NOT DISTINCT FROM %s AND AuxiliaryID IS NOT DISTINCT FROM %s;
    """, (entry_id, auxiliary_id))
    row = conn.fetchone()
    if not row:
        return None
    
    landmark_data = dict(row)
    landmark_id = landmark_data.pop('id')  # Remove the primary key from the model data
    landmark = Landmark(**landmark_data)

    # Retrieve traits
    conn.execute("""
        SELECT Trait FROM landmark_trait WHERE landmark_id = %s;
    """, (landmark_id,))
    traits = conn.fetchall()
    landmark.Traits = [t['trait'] for t in traits] if traits else None

    return landmark
