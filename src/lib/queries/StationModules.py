from typing import Any
from pydantic import BaseModel, Field

from .Settings import SearchPreferences, SearchContext

from ..Database import pg_connection
from ..entities import known_entities, autocorrect


class SearchMarketModulesArgs(BaseModel):
    module: str
    class_: int | None = Field(None, alias="class")
    rating: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "module": "Missile rack",
                "class": 3,
                "rating": "A",
            }
        }
    }


class SearchMarketModulesStation(BaseModel):
    system_name: str
    station_name: str
    station_type: str
    distance: float
    distance_to_arrival: float
    module: str
    # price: int


class SearchMarketModulesResult(BaseModel):
    query: dict
    closest: SearchMarketModulesStation | None
    # best: dict[str, Any] | None
    # balanced: dict[str, Any] | None


def api_search_market_module(
    args: SearchMarketModulesArgs,
    preferences: SearchPreferences,
    context: SearchContext,
):
    module = autocorrect("modules", args.module)
    if not module:
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

    filter = (module,)
    if args.class_:
        filter += (args.class_,)
    if args.rating:
        filter += (args.rating,)

    with pg_connection() as (db, cur):
        cur.execute(
            f"""
            SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, modules.name, modules.class, modules.rating
            FROM stations_outfitting_modules modules LEFT JOIN stations stations ON modules.stationId = stations.id
            WHERE modules.name = %s {'AND modules.class = %s' if args.class_ else ''} {'AND modules.rating = %s' if args.rating else ''} AND stations.type = ANY(%s)
            ORDER BY stations.coords <-> %s
            LIMIT 1
        """,
            (
                coords,
                *filter,
                known_entities["station_types"],
                coords,
            ),
        )
        closest_station = cur.fetchone()

    return SearchMarketModulesResult.model_validate(
        {
            "query": {
                "reference_system": context.reference_system,
                "module": module,
                "class": args.class_,
                "rating": args.rating,
            },
            "closest": (
                {
                    "system_name": closest_station["systemname"],
                    "station_name": closest_station["name"],
                    "station_type": closest_station["type"],
                    "distance": closest_station["distance"],
                    "distance_to_arrival": closest_station["distancetoarrival"],
                    "module": f'{closest_station["name"]} {closest_station["class"]} {closest_station["rating"]}',
                    # "price": closest_station['price'] if 'price' in closest_station else 0,
                }
                if closest_station
                else None
            ),
        }
    )
