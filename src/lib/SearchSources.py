import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from .queries.Station import SearchStationsArgs, api_search_stations
from .queries.StationCommodities import (
    SearchMarketCommoditiesArgs,
    api_search_market_commodities,
)
from .queries.StationModules import SearchMarketModulesArgs, api_search_market_module
from .queries.StationShips import SearchMarketShipsArgs, api_search_market_ships

if TYPE_CHECKING:
    from openai import OpenAI
    from .SearchManager import SearchManager

llm_client: "OpenAI" = None  # pyright: ignore[reportAssignmentType]
llm_model_name: str = None  # pyright: ignore[reportAssignmentType]


def parse_arguments(
    tool_name: str,
    tool_parameters: type[BaseModel],
    query: str,
    context: list[dict],
    state: dict[str, dict],
    found_entities: list[dict],
    strict: bool = False,
) -> Any:
    response = llm_client.chat.completions.create(
        model=llm_model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a search engine for the Game Elite Dangerous.",
            },
            {
                "role": "user",
                "content": "\n".join(
                    [
                        "<status>",
                        json.dumps(state),
                        "</status>",
                        "<entities>",
                        "\n".join([json.dumps(item) for item in found_entities]),
                        "</entities>",
                        "<context>",
                        "\n".join([json.dumps(item) for item in context]),
                        "</context>",
                        "<query>",
                        query,
                        "</query>",
                    ]
                ),
            },
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "parameters": tool_parameters.model_json_schema(),
                    "strict": strict,
                },
            }
        ],
        tool_choice="required",
    )
    if not response.choices[0]:
        print(response)
        return {"error": "no_response"}
    if not response.choices[0].message.tool_calls:
        print(response.choices[0].message)
        return {"error": "no_tool_calls"}

    return json.loads(response.choices[0].message.tool_calls[0].function.arguments)


def search_systems(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_stations(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    arguments = parse_arguments(
        "api_search_market_modules",
        SearchStationsArgs,
        query,
        context,
        state,
        found_entities,
    )

    if arguments.get("station_name") == state.get("Location", {}).get("Station", None):
        del arguments["station_name"]

    defaults = SearchStationsArgs(
        reference_system=state.get("Location", {}).get("StarSystem", None),
        system_name=None,
        station_name=None,
        station_type=None,
        services=None,
        economy=None,
        faction_allegiance=None,
        faction_name=None,
        faction_government=None,
        faction_state=None,
    )

    result = api_search_stations(
        SearchStationsArgs.model_validate({**defaults.model_dump(), **arguments})
    )
    return result


def search_stars(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_planets(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_landmarks(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_news(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_logbook(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_engineering_materials(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def search_market_modules(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    arguments = parse_arguments(
        "api_search_market_modules",
        SearchMarketModulesArgs,
        query,
        context,
        state,
        found_entities,
    )
    print(arguments)
    result = api_search_market_module(SearchMarketModulesArgs.model_validate(arguments))
    return result


def search_market_commodities(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    arguments = parse_arguments(
        "api_search_market_commodities",
        SearchMarketCommoditiesArgs,
        query,
        context,
        state,
        found_entities,
    )
    print(arguments, context, state)
    result = api_search_market_commodities(
        SearchMarketCommoditiesArgs.model_validate(arguments)
    )
    return result


def search_market_ships(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    arguments = parse_arguments(
        "api_search_market_ships",
        SearchMarketShipsArgs,
        query,
        context,
        state,
        found_entities,
    )

    result = api_search_market_ships(SearchMarketShipsArgs.model_validate(arguments))
    return result


def search_state_location(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return state.get("Location", {"error": "not_available"})


def search_state_missions(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return state.get("Missions", {"error": "not_available"})


def search_state_status(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return state.get("CurrentStatus", {"error": "not_available"})


def search_state_ship(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return state.get("ShipInfo", {"error": "not_available"})


def not_implemented(
    query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]
) -> dict:
    return {"error": "not_implemented"}


def register_sources(
    search_manager: "SearchManager", _llm_client: "OpenAI", _llm_model_name: str
):
    global llm_client, llm_model_name
    llm_client = _llm_client
    llm_model_name = _llm_model_name

    search_manager.register_source(
        "player.logbook", "Search the Captains Logbook", search_logbook
    )
    search_manager.register_source(
        "player.location", "Current location", search_state_location
    )
    search_manager.register_source(
        "player.missions", "Active missions", search_state_missions
    )
    search_manager.register_source(
        "player.status", "Systems status", search_state_status
    )
    search_manager.register_source(
        "player.ship", "Current Ship info", search_state_ship
    )

    # "with name 'x'" "with neutron star" "with population over x" "with state outbreak" "with power, super-power, faction, minor-faction of x"
    # search_manager.register_source("galaxy.systems", "Search for Systems", search_systems)
    # "with name 'x'" "with service x" "with guardian tech broker" "with raw material trader"  "with power, super-power, faction, minor-faction of x"
    search_manager.register_source(
        "galaxy.stations", "Search for Stations", search_stations
    )
    # "with name 'x'" "scoopable" "type x" "neutron star, black hole"
    search_manager.register_source("galaxy.stars", "Search for Stars", search_stars)
    # "with name 'x'" "landable" "volcanism x" "atmosphere x"
    search_manager.register_source(
        "galaxy.panets", "Search for Planet, Moons and other", search_planets
    )
    # "with name 'x'"
    search_manager.register_source(
        "galaxy.landmarks", "Search for Landmarks", search_landmarks
    )
    # "with material x"
    search_manager.register_source(
        "galaxy.hotspots", "Search for Mining Hotspots", not_implemented
    )

    # search_manager.register_source("people", "Find relevant people", not_implemented)
    search_manager.register_source("news", "Find related news articles", search_news)
    search_manager.register_source(
        "guides", "Find guides on how to get started", not_implemented
    )
    search_manager.register_source(
        "wiki", "Find articles with background information", not_implemented
    )

    search_manager.register_source(
        "market.commodities",
        "Search market for trade commodities",
        search_market_commodities,
    )
    search_manager.register_source(
        "market.modules", "Search market for ship modules", search_market_modules
    )
    search_manager.register_source(
        "market.ships", "Search market for ships", search_market_ships
    )
