from typing import Any
from pydantic import BaseModel

from .Settings import SearchContext, SearchPreferences

from ..Database import pg_connection
from ..entities import autocorrect


class SearchStationsArgs(BaseModel):
    system_name: str | None = None
    station_name: str | None = None
    station_type: str | None = None
    services: list[str] | None = None
    faction_name: str | None = None
    faction_allegiance: str | None = None
    faction_government: str | None = None
    faction_state: str | None = None
    economy: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "system_name": "Alpha Centauri",
                "station_name": "Hutton Orbital",
                "station_type": "Outpost",
                "services": ["Shipyard", "Outfitting"],
            }
        }
    }


class SearchStationsStation(BaseModel):
    systemname: str
    name: str
    type: str
    distance: float
    distancetoarrival: float
    faction_name: str | None
    faction_allegiance: str | None
    faction_government: str | None
    faction_state: str | None
    # power: str | None
    # powerstate: str | None
    economy: str | None
    services: list[str]
    economies: list[str]


class SearchStationsResult(BaseModel):
    query: dict
    results: list[SearchStationsStation]


def api_search_stations(
    args: SearchStationsArgs, preferences: SearchPreferences, context: SearchContext
):

    station_type = (
        autocorrect("station_types", args.station_type) if args.station_type else None
    )
    services = (
        [
            service
            for service in [
                autocorrect("services", service) for service in args.services
            ]
            if service is not None
        ]
        if args.services
        else None
    )
    faction_allegiance = (
        autocorrect("allegiances", args.faction_allegiance)
        if args.faction_allegiance
        else None
    )
    economy = autocorrect("economies", args.economy) if args.economy else None

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

    # services: list[str] | None, allegiance: str | None, faction: str | None, power: str | None, power_state: str | None, economy: str | None
    filter = []
    filter_values = ()
    if args.system_name:
        filter.append("stations.systemname = %s")
        filter_values += (args.system_name,)
    if args.station_name:
        filter.append("stations.name = %s")
        filter_values += (args.station_name,)
    if station_type:
        filter.append("stations.type = %s")
        filter_values += (station_type,)
    if economy:
        filter.append("(stations.primaryeconomy = %s OR economies.economy = %s)")
        filter_values += (
            economy,
            economy,
        )

    if args.faction_name:
        filter.append("stations.controllingfaction = %s")
        filter_values += (args.faction_name,)
    if faction_allegiance:
        filter.append("factions.allegiance = %s")
        filter_values += (faction_allegiance,)
    if args.faction_state:
        filter.append("factions.state = %s")
        filter_values += (args.faction_state,)
    if args.faction_government:
        filter.append("factions.government = %s")
        filter_values += (args.faction_government,)
    # if power:
    #    filter.append("systems.controllingPower = %s")
    #    filter_values += (power,)
    # if power_state:
    #    filter.append("systems.power_state = %s")
    #    filter_values += (power_state,)

    if services:
        filter.append("services.service = ANY(%s)")
        filter_values += (services,)

    print(filter, filter_values)

    if not filter:
        return None

    with pg_connection() as (db, cur):
        cur.execute(
            f"""
            SELECT 
                stations.systemName, 
                stations.name,
                stations.type,
                stations.coords <-> %s as distance,
                stations.distanceToArrival,
                stations.primaryeconomy as economy,
                stations.controllingfaction as faction_name,
                factions.allegiance as faction_allegiance,
                factions.state as faction_state,
                factions.government as faction_government,
                array_remove(array_agg(DISTINCT services.service), NULL) as services, 
                array_remove(array_agg(DISTINCT economies.economy), NULL) as economies
            FROM stations 
            LEFT JOIN systems as systems ON stations.systemId = systems.id 
            LEFT JOIN systems_factions as factions ON stations.systemid = factions.systemid and factions.name = stations.controllingfaction
            LEFT JOIN stations_services as services ON stations.id = services.stationId 
            LEFT JOIN stations_economies as economies ON stations.id = economies.stationId
            {'WHERE ' + ' AND '.join(filter) if filter else ''}
            GROUP BY stations.id, systems.id, factions.systemid, factions.name
            ORDER BY stations.coords <-> %s, stations.distanceToArrival
            LIMIT 3
        """,
            (
                coords,
                *(filter_values),
                coords,
            ),
        )
        results = cur.fetchall()

    return SearchStationsResult.model_validate(
        {
            "query": {
                "reference_system": context.reference_system,
                "station_name": args.station_name,
                "station_type": station_type,
                "services": services,
                "faction": args.faction_name,
                "faction_allegiance": faction_allegiance,
                "faction_government": args.faction_government,
                "faction_state": args.faction_state,
                "economy": economy,
            },
            "results": [
                SearchStationsStation.model_validate({**result}) for result in results
            ],
        }
    )
