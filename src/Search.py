from fastapi import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from typing import Any, final

from .Api import app

from .lib.SearchManager import SearchManager
from .lib.SearchSources import register_sources


def init() -> SearchManager:
    llm_client = OpenAI()
    llm_model_name = "gpt-4o-mini"
    embed_client = OpenAI()
    embed_model_name = "text-embed-large-v3"

    search = SearchManager(llm_client, llm_model_name, embed_client, embed_model_name)
    register_sources(search, llm_client, llm_model_name)

    return search


search = init()

# Mount the static files directory
app.mount("/ui", StaticFiles(directory="./src/ui"), name="ui")


@app.get("/")
def index():
    return RedirectResponse("/ui/index.html")


class SearchInput(BaseModel):
    query: str
    state: dict[str, Any]
    context: list[Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "sell 20 tons of gold",
                "context": [],
                "state": {
                    "Location": {"StarSystem": "Ochosi", "Station": "Perry's Folly"},
                    "ShipInfo": {
                        "Name": "Jenny",
                        "Type": "empire_courier",
                        "Cargo": 30.2,
                        "CargoCapacity": 100,
                        "MaximumJumpRange": 50.628967,
                        "LandingPadSize": "S",
                    },
                },
            }
        }
    }


class SearchOutput(BaseModel):
    context: list[Any]
    possible_entities: list[Any]
    query: str
    sources: dict[str, bool]
    results: dict[str, Any]


@app.post("/search", response_model=SearchOutput)
async def search_endpoint(body: SearchInput):
    results = search.run(**body.dict())
    if not results:
        raise HTTPException(status_code=404, detail="No Results")
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
