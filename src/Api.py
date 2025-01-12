from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .lib.StationFinder import *

app = FastAPI(title="EDSearch", version="v0.1")


@app.post("/commodities", response_model=SearchMarketCommoditiesResult)
async def search_market_commodities_endpoint(body: SearchMarketCommoditiesArgs):
    results = api_search_market_commodities(**body.dict())
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=results.model_dump())


@app.post("/modules", response_model=SearchMarketModulesResult)
async def search_market_modules_endpoint(body: SearchMarketModulesArgs):
    results = api_search_market_module(**body.dict())
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=results.model_dump())


@app.post("/ships", response_model=SearchMarketShipsResult)
async def search_market_ships_endpoint(body: SearchMarketShipsArgs):
    results = api_search_market_ships(**body.dict())
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=results.model_dump())


@app.post("/stations", response_model=SearchStationsResult)
async def search_stations_endpoint(body: SearchStationsArgs):
    results = api_search_stations(**body.dict())
    if not results:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=results.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
