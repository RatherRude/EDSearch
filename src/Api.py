from typing import Generic, TypeVar
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .lib.queries.Settings import SearchContext, SearchPreferences

from .lib.queries.Station import (
    SearchStationsArgs,
    SearchStationsResult,
    api_search_stations,
)
from .lib.queries.StationModules import (
    SearchMarketModulesArgs,
    SearchMarketModulesResult,
    api_search_market_module,
)
from .lib.queries.StationShips import (
    SearchMarketShipsArgs,
    SearchMarketShipsResult,
    api_search_market_ships,
)
from .lib.queries.StationCommodities import (
    SearchMarketCommoditiesArgs,
    SearchMarketCommoditiesResult,
    api_search_market_commodities,
)

app = FastAPI(title="EDSearch", version="v0.1")

T = TypeVar(
    "T",
    SearchMarketCommoditiesArgs,
    SearchMarketModulesArgs,
    SearchMarketShipsArgs,
    SearchStationsArgs,
)


class APIRequest(BaseModel, Generic[T]):
    query: T
    preferences: SearchPreferences
    context: SearchContext


@app.post("/commodities", response_model=SearchMarketCommoditiesResult)
async def search_market_commodities_endpoint(
    body: APIRequest[SearchMarketCommoditiesArgs],
):
    results = api_search_market_commodities(body.query, body.preferences, body.context)
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return results


@app.post("/modules", response_model=SearchMarketModulesResult)
async def search_market_modules_endpoint(body: APIRequest[SearchMarketModulesArgs]):
    results = api_search_market_module(body.query, body.preferences, body.context)
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return results


@app.post("/ships", response_model=SearchMarketShipsResult)
async def search_market_ships_endpoint(body: APIRequest[SearchMarketShipsArgs]):
    results = api_search_market_ships(body.query, body.preferences, body.context)
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return results


@app.post("/stations", response_model=SearchStationsResult)
async def search_stations_endpoint(body: APIRequest[SearchStationsArgs]):
    results = api_search_stations(body.query, body.preferences, body.context)
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
