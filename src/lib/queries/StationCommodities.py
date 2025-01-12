from typing import Any, Literal
from pydantic import BaseModel

from .Settings import SearchContext, SearchPreferences

from ..Database import pg_connection
from ..entities import known_entities, autocorrect


class SearchMarketCommoditiesArgs(BaseModel):
    transaction: Literal["buy", "sell"]
    commodity: str
    amount: int
    # min_landing_pad
    # station type (orbital, planetary, fleet carrier, stronghold carrier)

    model_config = {
        "json_schema_extra": {
            "example": {
                "transaction": "buy",
                "commodity": "gold",
                "amount": 20,
            }
        }
    }


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
    query: dict
    closest: (
        SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    )
    best: SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    balanced: (
        SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell | None
    )


def api_search_market_commodities(
    args: SearchMarketCommoditiesArgs,
    preferences: SearchPreferences,
    context: SearchContext,
):
    known_commodities = known_entities["commodities"]
    known_station_types = [
        e for e in known_entities["station_types"] if e != "Drake-Class Carrier"
    ]
    commodity = autocorrect("commodities", args.commodity)
    if not commodity:
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

    # find closest station price

    with pg_connection() as (db, cur):
        cur.execute(
            f"""
            SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if args.transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
            FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
            WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if args.transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'}
            ORDER BY stations.coords <-> %s ASC, distanceToArrival ASC
            LIMIT 1
        """,
            (
                coords,
                commodity,
                known_station_types,
                args.amount,
                coords,
            ),
        )
        closest_station = cur.fetchone()
    print("closest", closest_station)

    # find best station price
    with pg_connection() as (db, cur):
        cur.execute(
            f"""
            SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if args.transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
            FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
            WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if args.transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'}
            ORDER BY {'commodities.buyPrice ASC' if args.transaction == 'buy' else 'commodities.sellPrice DESC'}, stations.coords <-> %s ASC
            LIMIT 1
        """,
            (
                coords,
                commodity,
                known_station_types,
                args.amount,
                coords,
            ),
        )
        best_station = cur.fetchone()
    print("best", best_station)

    # find best station price within 10 jumps
    with pg_connection() as (db, cur):
        cur.execute(
            f"""
            SELECT stations.systemName, stations.name, stations.type, stations.coords <-> %s as distance, stations.distanceToArrival, {'commodities.buyPrice, commodities.supply' if args.transaction == 'buy' else 'commodities.sellPrice, commodities.demand'}, stations.market_updatetime
            FROM stations_market_commodities commodities LEFT JOIN stations stations ON commodities.stationId = stations.id
            WHERE commodities.name = %s AND stations.type = ANY(%s) AND {'commodities.supply >= %s AND commodities.buyprice > 0' if args.transaction == 'buy' else 'commodities.demand >= %s AND commodities.sellprice > 0'} AND stations.coords <-> %s <= %s
            ORDER BY {'commodities.buyPrice ASC' if args.transaction == 'buy' else 'commodities.sellPrice DESC'}, stations.coords <-> %s ASC
            LIMIT 1
        """,
            (
                coords,
                commodity,
                known_station_types,
                args.amount,
                coords,
                context.jump_range * preferences.max_jumps,
                coords,
            ),
        )
        balanced_station = cur.fetchone()
    print("balanced", balanced_station)

    def station_mapping(
        station_result: Any,
    ) -> SearchMarketCommoditiesStationBuy | SearchMarketCommoditiesStationSell:
        if args.transaction == "buy":
            return SearchMarketCommoditiesStationBuy.model_validate({**station_result})
        else:
            return SearchMarketCommoditiesStationSell.model_validate({**station_result})

    return SearchMarketCommoditiesResult.model_validate(
        {
            "query": {
                "reference_system": context.reference_system,
                "allow_planetary": True,
                "allow_carrier": True,
                "require_large_pad": False,
                "commodity": commodity,
                "transaction": args.transaction,
                "amount": args.amount,
                "jump_range": context.jump_range,
                "max_jumps": preferences.max_jumps,
            },
            "closest": station_mapping(closest_station),
            "best": station_mapping(best_station),
            "balanced": station_mapping(balanced_station),
        }
    )
