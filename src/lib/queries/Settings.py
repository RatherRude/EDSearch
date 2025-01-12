from pydantic import BaseModel


class SearchPreferences(BaseModel):
    max_jumps: int = 10
    include_planetary: bool = True
    include_orbital: bool = True
    include_fleet_carrier: bool = False
    max_distance_to_star: float = 100_000


class SearchContext(BaseModel):
    reference_system: str
    jump_range: float
    cargo_capacity: int
    require_large_pad: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "reference_system": "Sol",
                "jump_range": 50.628967,
                "cargo_capacity": 100,
                "require_large_pad": False,
            }
        }
    }
