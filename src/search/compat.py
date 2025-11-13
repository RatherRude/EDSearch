from fastapi import APIRouter
from pydantic import BaseModel

from Database import pg_connection

router = APIRouter()

class StationSearchRequest(BaseModel):
    coords: tuple[float, float, float]

class StationSearchResponse(BaseModel):
    stations: list[str]

@router.post("/stations")
async def post_stations(request: StationSearchRequest) -> StationSearchResponse:
    with pg_connection() as (conn, cur):
        # Start a transaction and set a modest lock timeout
        cur.execute("""
            SELECT 
                stations.name as station_name, 
                systems.name AS system_name,
                systems.coords <-> %s AS distance
            FROM stations 
            LEFT JOIN systems on stations.system_id = systems.id
            ORDER BY systems.coords <-> %s ASC
            LIMIT 5
        """, (request.coords, request.coords))
        rows = cur.fetchall()
        return {"stations": [row.get('name') for row in rows]}