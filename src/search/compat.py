from fastapi import APIRouter

from Database import pg_connection

router = APIRouter()

@router.get("/stations")
async def get_stations():
    with pg_connection() as (conn, cur):
        # Start a transaction and set a modest lock timeout
        cur.execute("SELECT * FROM stations LIMIT 10;")
        rows = cur.fetchall()
        return {"stations": rows}