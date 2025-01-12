import json
from typing import TYPE_CHECKING, Any

from .StationFinder import api_search_market_commodities, api_search_market_module, api_search_market_ships, api_search_stations

if TYPE_CHECKING:
    from openai import OpenAI
    from .SearchManager import SearchManager

llm_client: 'OpenAI' = None  # pyright: ignore[reportAssignmentType]
llm_model_name: str = None  # pyright: ignore[reportAssignmentType]

def parse_arguments(tool_name: str, tool_parameters: dict, query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> Any:
    strict = tool_parameters.get("strict", False)
    tool_parameters.pop("strict", None)
    
    response = llm_client.chat.completions.create(
        model=llm_model_name,
        messages=[
            {"role": "system", "content": "You are a search engine for the Game Elite Dangerous."}, 
            {"role": "user", "content": '\n'.join([
                '<status>',
                json.dumps(state),
                '</status>',
                '<entities>',
                '\n'.join([json.dumps(item) for item in found_entities]),
                '</entities>',
                '<context>',
                '\n'.join([json.dumps(item) for item in context]),
                '</context>',
                '<query>',
                query,
                '</query>'
            ])}
        ],
        tools=[{
            "type": "function",
            "function": {
                "name": tool_name,
                "parameters": tool_parameters,
                "strict": strict
            }
        }],
        tool_choice='required'
    )
    if not response.choices[0]:
        print(response)
        return { "error": 'no_response' }
    if not response.choices[0].message.tool_calls:
        print(response.choices[0].message)
        return { "error": 'no_tool_calls' }
    
    return json.loads(response.choices[0].message.tool_calls[0].function.arguments)


def search_systems(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }
    
def search_stations(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    arguments = parse_arguments(
        "api_search_market_modules",
        {
            "type": "object",
            "properties": {
                "reference_system": { "type": "string" },
                "station_name": { "type": ["string", "null"] },
                "station_type": { "type": ["string", "null"],  },
                "services": { "type": ["array", "null"], "items": { "type": "string" }  },
                "allegiance": { "type": ["string", "null"], },
                "faction": { "type": ["string", "null"],  },
                "power": { "type": ["string", "null"], },
                "power_state": { "type": ["string", "null"], },
                "economy": { "type": ["string", "null"],  },
            },  
            "required": ["reference_system", "station_name", "station_type", "services", "allegiance", "faction", "power", "power_state", "economy"],
            "additionalProperties": False,
            "strict": False
        },
        query,
        context,
        state,
        found_entities
    )
    
    if arguments.get("station_name") == state.get("Location", {}).get("Station", None):
        del arguments["station_name"]
    
    defaults = {
        "reference_system": state.get("Location", {}).get("StarSystem", None),
        "station_name": None,
        "station_type": None,
        "services": None,
        "allegiance": None,
        "faction": None,
        "power": None,
        "power_state": None,
        "economy": None,
    }
    
    result = api_search_stations(**{**defaults, **arguments})
    return result

def search_stars(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_planets(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_landmarks(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_news(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_logbook(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_engineering_materials(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def search_market_modules(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    arguments = parse_arguments(
        "api_search_market_modules",
        {
            "type": "object",
            "properties": {
                "reference_system": { "type": "string", "default": state.get("Location", {}).get("StarSystem", None) },
                "module": { "type": "string" },
                "class": { "type": "int", "default": None },
                "rating": { "type": "string", "pattern": "^[A-Z]$", "default": None },
                "jump_range": { "type": "number", "default": state.get("ShipInfo", {}).get("MaximumJumpRange", None) },
                "max_jumps": { "type": "number", "default": 10 },
            },
            "required": ["reference_system", "module", "class", "rating", "jump_range", "max_jumps"],
            "additionalProperties": False,
        },
        query,
        context,
        state,
        found_entities
    )
    print (arguments)
    result = api_search_market_module(**arguments)
    return result

def search_market_commodities(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    arguments = parse_arguments(
        "api_search_market_commodities",
        {
            "type": "object",
            "properties": {
                "reference_system": { "type": "string", "default": state.get("Location", {}).get("StarSystem", None) },
                "commodity": { "type": "string" },
                "transaction": { "type": "string" },
                "amount": { "type": "number", "default": max(state.get("ShipInfo", {}).get("CargoCapacity", 1), 1) }, # TODO cargo capacity?
                "jump_range": { "type": "number", "default": state.get("ShipInfo", {}).get("MaximumJumpRange", None) },
                "max_jumps": { "type": "number", "default": 10 },
            },
            "required": ["reference_system", "commodity", "transaction", "amount", "jump_range", "max_jumps"],
            "additionalProperties": False,
        },
        query,
        context,
        state,
        found_entities
    )
    print (arguments, context, state)
    result = api_search_market_commodities(**arguments)
    return result

def search_market_ships(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    arguments = parse_arguments(
        "api_search_market_ships",
        {
            "type": "object",
            "properties": {
                "reference_system": { "type": "string", "default": state.get("Location", {}).get("StarSystem", None) },
                "ship": { "type": "string" },
                "jump_range": { "type": "number", "default": state.get("ShipInfo", {}).get("MaximumJumpRange", None) },
                "max_jumps": { "type": "number", "default": 10 },
            },
            "required": ["reference_system", "ship", "jump_range", "max_jumps"],
            "additionalProperties": False,
        },
        query,
        context,
        state,
        found_entities
    )

    result = api_search_market_ships(**arguments)
    return result

def search_state_location(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return state.get("Location", { "error": 'not_available' })

def search_state_missions(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return state.get("Missions", { "error": 'not_available' })

def search_state_status(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return state.get("CurrentStatus", { "error": 'not_available' })

def search_state_ship(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return state.get("ShipInfo", { "error": 'not_available' })

def not_implemented(query: str, context: list[dict], state: dict[str, dict], found_entities: list[dict]) -> dict:
    return { "error": 'not_implemented' }

def register_sources(search_manager: "SearchManager", _llm_client: 'OpenAI', _llm_model_name: str):
    global llm_client, llm_model_name
    llm_client = _llm_client
    llm_model_name = _llm_model_name
    
    search_manager.register_source("player.logbook", "Search the Captains Logbook", search_logbook)
    search_manager.register_source("player.location", "Current location", search_state_location)
    search_manager.register_source("player.missions", "Active missions", search_state_missions)
    search_manager.register_source("player.status", "Systems status", search_state_status)
    search_manager.register_source("player.ship", "Current Ship info", search_state_ship)
    
    # "with name 'x'" "with neutron star" "with population over x" "with state outbreak" "with power, super-power, faction, minor-faction of x"
    #search_manager.register_source("galaxy.systems", "Search for Systems", search_systems)
    # "with name 'x'" "with service x" "with guardian tech broker" "with raw material trader"  "with power, super-power, faction, minor-faction of x" 
    search_manager.register_source("galaxy.stations", "Search for Stations", search_stations)
    # "with name 'x'" "scoopable" "type x" "neutron star, black hole"
    search_manager.register_source("galaxy.stars", "Search for Stars", search_stars)
    # "with name 'x'" "landable" "volcanism x" "atmosphere x" 
    search_manager.register_source("galaxy.panets", "Search for Planet, Moons and other", search_planets)
    # "with name 'x'" 
    search_manager.register_source("galaxy.landmarks", "Search for Landmarks", search_landmarks)
    # "with material x"
    search_manager.register_source("galaxy.hotspots", "Search for Mining Hotspots", not_implemented)
    
    #search_manager.register_source("people", "Find relevant people", not_implemented)
    search_manager.register_source("news", "Find related news articles", search_news)
    search_manager.register_source("guides", "Find guides on how to get started", not_implemented)
    search_manager.register_source("wiki", "Find articles with background information", not_implemented)
    
    search_manager.register_source("market.commodities", "Search market for trade commodities", search_market_commodities)
    search_manager.register_source("market.modules", "Search market for ship modules", search_market_modules)
    search_manager.register_source("market.ships", "Search market for ships", search_market_ships)
    
    