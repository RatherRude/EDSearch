import json
from typing import Any, Literal
from difflib import get_close_matches

from pydantic import BaseModel, Field

from .Database import get_pg_connection
from .entities import known_entities


def best_match(v: str, l: list[str], default: Any = None):
    matches = get_close_matches(v, l, n=1)
    if matches:
        return matches[0]
    return default


class SearchMarketModulesArgs(BaseModel):
    reference_system: str
    module: str
    class_: int | None = Field(None, alias="class")
    rating: str | None = None
    jump_range: float
    max_jumps: int = 10


class SearchMarketModulesStation(BaseModel):
    system_name: str
    station_name: str
    station_type: str
    distance: float
    distance_to_arrival: float
    module: str
    # price: int


class SearchMarketModulesResult(BaseModel):
    query: SearchMarketModulesArgs
    closest: SearchMarketModulesStation | None
    # best: dict[str, Any] | None
    # balanced: dict[str, Any] | None


def api_search_market_module(
    reference_system: str,
    module: str,
    class_: int | None,
    rating: str | None,
    jump_range: float,
    max_jumps: int = 10,
):
    known_modules = known_entities["modules"]
    module = best_match(module, known_modules)
    if not module:
        return None

    db, cur = get_pg_connection()

    cur.execute(
        """
        SELECT coords FROM systems WHERE name = %s
    """,
        (reference_system,),
    )
    reference_system_coords = cur.fetchone()
    if not reference_system_coords:
        return None
    coords = reference_system_coords["coords"]

    filter = (module,)
    if class_:
        filter += (class_,)
    if rating:
        filter += (rating,)
    cur.execute(
        f"""
        SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, modules.name, modules.class, modules.rating
        FROM stations_outfitting_modules modules LEFT JOIN stations stations ON modules.stationId = stations.id
        WHERE modules.name = %s {'AND modules.class = %s' if class_ else ''} {'AND modules.rating = %s' if rating else ''} AND stations.type = ANY(%s)
        ORDER BY stations.coords <-> %s
        LIMIT 1
    """,
        (
            coords,
            *filter,
            tuple(known_entities["station_types"]),
            coords,
        ),
    )
    closest_station = cur.fetchone()

    # find best station price
    # cur.execute("""
    #    SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival
    #    FROM stations_modules modules LEFT JOIN stations stations ON modules.stationId = stations.id
    #    WHERE modules.name = %s AND stations.type = ANY(%s)
    #    ORDER BY modules.price ASC
    #    LIMIT 1
    # """, (coords,module,tuple(known_entities['station_types']),))
    # best_station = cur.fetchone()

    # find the cheapest station within a given jump count
    # cur.execute("""
    #    SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival
    #    FROM stations_modules modules LEFT JOIN stations stations ON modules.stationId = stations.id
    #    WHERE modules.name = %s AND stations.type = ANY(%s) AND stations.coords <-> %s <= %s
    #    ORDER BY modules.price ASC
    #    LIMIT 1
    # """, (coords,module,tuple(known_entities['station_types']),coords,jump_range*max_jumps,))
    # balanced_station = cur.fetchone()

    return SearchMarketModulesResult.model_validate(
        {
            "query": {
                "reference_system": reference_system,
                "module": module,
                "class": class_,
                "rating": rating,
                "jump_range": jump_range,
                "max_jumps": max_jumps,
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
            # "best": filter_market_module_result(results['best'], module, class_, rating),
            # "balanced": filter_market_module_result(results['balanced'], module, class_, rating),
        }
    )


class SearchMarketCommoditiesArgs(BaseModel):
    reference_system: str
    commodity: str
    transaction: Literal["buy", "sell"]
    amount: int
    jump_range: float
    max_jumps: int = 10
    # min_landing_pad
    # station type (orbital, planetary, fleet carrier, stronghold carrier)


class SearchMarketCommoditiesStationBuy(BaseModel):
    systemname: str
    name: str
    type: str
    distance: float
    distancetoarrival: float
    buyprice: float
    supply: int
    market_updatetime: str


class SearchMarketCommoditiesStationSell(BaseModel):
    systemname: str
    name: str
    type: str
    distance: float
    distancetoarrival: float
    sellprice: float
    demand: int
    market_updatetime: str


class SearchMarketCommoditiesResult(BaseModel):
    query: SearchMarketCommoditiesArgs
    closest: (
        SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    )
    best: SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    balanced: (
        SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    )


def api_search_market_commodities(
    reference_system: str,
    commodity: str,
    transaction: Literal["buy", "sell"],
    amount: int,
    jump_range: float,
    max_jumps: int = 10,
):
    known_commodities = known_entities["commodities"]
    known_station_types = [
        e for e in known_entities["station_types"] if e != "Drake-Class Carrier"
    ]
    commodity = best_match(commodity, known_commodities)
    if not commodity:
        return None

    db, cur = get_pg_connection()

    cur.execute(
        """
        SELECT coords FROM systems WHERE name = %s
    """,
        (reference_system,),
    )
    reference_system_coords = cur.fetchone()
    if not reference_system_coords:
        return None
    coords = reference_system_coords["coords"]

    # find closest station price
    cur.execute(
        f"""
        SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
        FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
        WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'}
        ORDER BY stations.coords <-> %s ASC, distanceToArrival ASC
        LIMIT 1
    """,
        (
            coords,
            commodity,
            tuple(known_station_types),
            amount,
            coords,
        ),
    )
    closest_station = cur.fetchone()
    print("closest", closest_station)

    # find best station price
    cur.execute(
        f"""
        SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
        FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
        WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'}
        ORDER BY {'commodities.buyPrice ASC' if transaction == 'buy' else 'commodities.sellPrice DESC'}, stations.coords <-> %s ASC
        LIMIT 1
    """,
        (
            coords,
            commodity,
            tuple(known_station_types),
            amount,
            coords,
        ),
    )
    best_station = cur.fetchone()
    print("best", best_station)

    # find best station price within 10 jumps
    cur.execute(
        f"""
        SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
        FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
        WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'} AND stations.coords <-> %s <= %s
        ORDER BY {'commodities.buyPrice ASC' if transaction == 'buy' else 'commodities.sellPrice DESC'}, stations.coords <-> %s ASC
        LIMIT 1
    """,
        (
            coords,
            commodity,
            tuple(known_station_types),
            amount,
            coords,
            jump_range * max_jumps,
            coords,
        ),
    )
    balanced_station = cur.fetchone()
    print("balanced", balanced_station)

    def station_mapping(
        station_result,
    ) -> SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell:
        if transaction == "buy":
            return SearchMarketCommoditiesStationBuy.model_validate({**station_result})
        else:
            return SearchMarketCommoditiesStationSell.model_validate({**station_result})

    return SearchMarketCommoditiesResult.model_validate(
        {
            "query": {
                "reference_system": reference_system,
                "allow_planetary": True,
                "allow_carrier": True,
                "require_large_pad": False,
                "commodity": commodity,
                "transaction": transaction,
                "amount": amount,
                "jump_range": jump_range,
                "max_jumps": max_jumps,
            },
            "closest": station_mapping(closest_station),
            "best": station_mapping(best_station),
            "balanced": station_mapping(balanced_station),
        }
    )


class SearchMarketShipsArgs(BaseModel):
    reference_system: str
    ship: str
    jump_range: float
    max_jumps: int = 10


class SearchMarketShipsStation(BaseModel):
    system_name: str
    station_name: str
    station_type: str
    distance: float
    distance_to_arrival: float
    ship: str
    # price: int


class SearchMarketShipsResult(BaseModel):
    query: SearchMarketShipsArgs
    closest: SearchMarketShipsStation | None


def api_search_market_ships(
    reference_system: str, ship: str, jump_range: float, max_jumps: int = 10
):
    known_ships = known_entities["ships"]
    known_station_types = [
        e for e in known_entities["station_types"] if e != "Drake-Class Carrier"
    ]

    ship = best_match(ship, known_ships)
    if not ship:
        return None

    db, cur = get_pg_connection()

    cur.execute(
        """
        SELECT coords FROM systems WHERE name = %s
    """,
        (reference_system,),
    )
    reference_system_coords = cur.fetchone()
    if not reference_system_coords:
        return None
    coords = reference_system_coords["coords"]

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
            tuple(known_station_types),
            coords,
        ),
    )
    closest_station = cur.fetchone()
    if not closest_station:
        return None
    print("closest", closest_station)

    return SearchMarketShipsResult.model_validate(
        {
            "query": {
                "reference_system": reference_system,
                "ship": ship,
                "jump_range": jump_range,
                "max_jumps": max_jumps,
            },
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


class SearchStationsArgs(BaseModel):
    reference_system: str
    station_name: str | None = None
    station_type: str | None = None
    services: list[str] | None = None
    faction_name: str | None = None
    faction_allegiance: str | None = None
    faction_government: str | None = None
    faction_state: str | None = None
    economy: str | None = None


class SearchStationsStation(BaseModel):
    systemname: str
    name: str
    type: str
    distance: float
    distancetoarrival: float
    faction_name: str
    faction_allegiance: str
    faction_government: str
    faction_state: str
    # power: str | None
    # powerstate: str | None
    economy: str | None
    services: list[str]
    economies: list[str]


class SearchStationsResult(BaseModel):
    query: SearchStationsArgs
    results: list[SearchStationsStation]


def api_search_stations(
    reference_system: str,
    station_name: str | None,
    station_type: str | None,
    services: list[str] | None,
    faction_state: str | None,
    faction_allegiance: str | None,
    faction_government: str | None,
    faction_name: str | None,
    economy: str | None,
):
    known_station_types = known_entities["station_types"]
    known_services = known_entities["services"]
    known_allegiances = known_entities["allegiances"]
    # known_power_states = known_entities['power_states']
    # known_powers = known_entities['powers']
    known_economies = known_entities["economies"]

    station_type = (
        best_match(station_type, known_station_types) if station_type else None
    )
    services = (
        [
            service
            for service in [best_match(service, known_services) for service in services]
            if service is not None
        ]
        if services
        else None
    )
    faction_allegiance = (
        best_match(faction_allegiance, known_allegiances)
        if faction_allegiance
        else None
    )
    # power = best_match(power, known_powers) if power else None
    # power_state = best_match(power_state, known_power_states) if power_state else None
    economy = best_match(economy, known_economies) if economy else None

    db, cur = get_pg_connection()

    cur.execute(
        """
        SELECT coords FROM systems WHERE name = %s
    """,
        (reference_system,),
    )
    reference_system_coords = cur.fetchone()
    if not reference_system_coords:
        return None
    coords = reference_system_coords["coords"]

    # services: list[str] | None, allegiance: str | None, faction: str | None, power: str | None, power_state: str | None, economy: str | None
    filter = []
    filter_values = ()
    if station_name:
        filter.append("stations.name = %s")
        filter_values += (station_name,)
    if station_type:
        filter.append("stations.type = %s")
        filter_values += (station_type,)
    if economy:
        filter.append(
            "(stations.primaryeconomy = %s OR stations_economies.economy = %s)"
        )
        filter_values += (economy,)

    if faction_name:
        filter.append("stations.controllingfaction = %s")
        filter_values += (faction_name,)
    if faction_allegiance:
        filter.append("factions.allegiance = %s")
        filter_values += (faction_allegiance,)
    if faction_state:
        filter.append("factions.state = %s")
        filter_values += (faction_state,)
    if faction_government:
        filter.append("factions.government = %s")
        filter_values += (faction_government,)
    # if power:
    #    filter.append("systems.controllingPower = %s")
    #    filter_values += (power,)
    # if power_state:
    #    filter.append("systems.power_state = %s")
    #    filter_values += (power_state,)

    if services:
        filter.append("services.service = ANY(%s)")
        filter_values += (tuple(services),)

    if not filter:
        return None

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
                "reference_system": reference_system,
                "station_name": station_name,
                "station_type": station_type,
                "services": services,
                "faction": faction_name,
                "faction_allegiance": faction_allegiance,
                "faction_government": faction_government,
                "faction_state": faction_state,
                "economy": economy,
            },
            "results": [
                SearchStationsStation.model_validate({**result}) for result in results
            ],
        }
    )


if __name__ == "__main__":
    # res = api_search_market_ships("Sirius", "Anaconda", 50, 10)
    # res = api_search_market_module("Sirius", "AX Missile Rack", 3, None, 50, 10)
    # res = api_search_market_commodities("Sol", "Gold", 'sell', 10, 50, 10)
    res = api_search_stations(
        "Sol", None, None, ["Tech Broker"], None, None, None, None, None
    )
    print(json.dumps(res, indent=2))
