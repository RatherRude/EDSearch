from typing import Any
from pydantic import BaseModel

from .Settings import SearchPreferences, SearchContext

from ..Database import pg_connection
from ..entities import autocorrect, known_entities


class SearchMarketShipsArgs(BaseModel):
    ship: str

    model_config = {"json_schema_extra": {"example": {"ship": "Anaconda"}}}


class SearchMarketShipsStation(BaseModel):
    system_name: str
    station_name: str
    station_type: str
    distance: float
    distance_to_arrival: float
    ship: str
    # price: int


class SearchMarketShipsResult(BaseModel):
    query: dict
    closest: SearchMarketShipsStation | None


def api_search_market_ships(
    args: SearchMarketShipsArgs,
    preferences: SearchPreferences,
    context: SearchContext,
):
    known_station_types = [
        e for e in known_entities["station_types"] if e != "Drake-Class Carrier"
    ]

    ship = autocorrect("ships", args.ship)
    if not ship:
        return None

    with pg_connection() as (db, cur):
        cur.execute(
            """
            SELECT coords FROM systems WHERE name = %s
        """,
            (context.reference_system,),
        )
        reference_system_coords = cur.fetchone()
    if not reference_system_coords:
        return None
    coords = reference_system_coords["coords"]

    with pg_connection() as (db, cur):
        cur.execute(
            """
            SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival
            FROM stations_shipyard_ships ships LEFT JOIN stations stations ON ships.stationId = stations.id  
            WHERE ships.name = %s AND stations.type = ANY(%s)
            ORDER BY stations.coords <-> %s
            LIMIT 1
        """,
            (
                coords,
                ship,
                known_station_types,
                coords,
            ),
        )
        closest_station = cur.fetchone()
    if not closest_station:
        return None
    print("closest", closest_station)

    return SearchMarketShipsResult.model_validate(
        {
            "query": {"reference_system": context.reference_system, "ship": ship},
            "closest": SearchMarketShipsStation.model_validate(
                {
                    "system_name": closest_station["systemname"],
                    "station_name": closest_station["name"],
                    "station_type": closest_station["type"],
                    "distance": closest_station["distance"],
                    "distance_to_arrival": closest_station["distancetoarrival"],
                    "ship": ship,
                    # "price": match, # TODO get price and add discount options
                }
            ),
        }
    )
