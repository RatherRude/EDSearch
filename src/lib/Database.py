import json
import os
from typing import TypedDict

import psycopg
import numpy as np
from pgvector.psycopg import register_vector
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool


class Coords(TypedDict):
    x: float
    y: float
    z: float


class Commodity(TypedDict):
    name: str
    symbol: str
    category: str
    commodityId: int
    demand: int
    supply: int
    buyPrice: int
    sellPrice: int


create_stations_market_commodities_table = """
CREATE TABLE IF NOT EXISTS stations_market_commodities (
    stationId BIGINT NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    category TEXT NOT NULL,
    commodityId BIGINT NOT NULL,
    demand REAL NOT NULL,
    supply REAL NOT NULL,
    buyPrice REAL NOT NULL,
    sellPrice REAL NOT NULL,
    PRIMARY KEY (stationId, commodityId),
    FOREIGN KEY (stationId) REFERENCES stations (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS name_idx
    ON public.stations_market_commodities USING btree
    (name COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (deduplicate_items=True);
    
CREATE INDEX IF NOT EXISTS buy_idx
    ON public.stations_market_commodities USING btree
    (name COLLATE pg_catalog."default" ASC NULLS LAST, supply ASC NULLS LAST, buyprice ASC NULLS LAST)
    WITH (deduplicate_items=True);

CREATE INDEX IF NOT EXISTS sell_idx
    ON public.stations_market_commodities USING btree
    (name COLLATE pg_catalog."default" ASC NULLS LAST, demand ASC NULLS LAST, sellprice ASC NULLS LAST)
    WITH (deduplicate_items=True);
"""


class Ship(TypedDict):
    name: str
    symbol: str
    shipId: int


create_stations_shipyard_ships_table = """
CREATE TABLE IF NOT EXISTS stations_shipyard_ships (
    stationId BIGINT NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    shipId BIGINT NOT NULL,
    PRIMARY KEY (stationId, shipId),
    FOREIGN KEY (stationId) REFERENCES stations (id) ON DELETE CASCADE
);
"""


class Module(TypedDict):
    name: str
    symbol: str
    moduleId: int
    class_: int
    rating: str
    category: str


create_stations_outfitting_modules_table = """
CREATE TABLE IF NOT EXISTS stations_outfitting_modules (
    stationId BIGINT NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    moduleId BIGINT NOT NULL,
    class INTEGER NOT NULL,
    rating TEXT NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (stationId, moduleId),
    FOREIGN KEY (stationId) REFERENCES stations (id) ON DELETE CASCADE
);
"""


class Market(TypedDict):
    commodities: list[Commodity]
    prohibitedCommodities: list  # ?
    updateTime: str


class Shipyard(TypedDict):
    ships: list[Ship]
    updateTime: str


class Outfitting(TypedDict):
    modules: list[Module]
    updateTime: str


class Station(TypedDict):
    name: str
    id: int
    systemId: int
    systemName: str
    bodyId: int
    coords: Coords
    updateTime: str
    controllingFaction: str
    distanceToArrival: float
    primaryEconomy: str
    economies: dict[str, float]
    type: str
    landingPads: dict[str, int]
    services: list[str]
    market: Market
    shipyard: Shipyard
    outfitting: Outfitting


create_stations_table = """
CREATE TABLE IF NOT EXISTS stations (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    systemId BIGINT NOT NULL,
    bodyId BIGINT,
    name TEXT NOT NULL,
    systemName TEXT NOT NULL,
    coords vector(3) NOT NULL,
    updateTime TEXT NOT NULL,
    controllingFaction TEXT,
    distanceToArrival REAL NOT NULL,
    primaryEconomy TEXT,
    type TEXT NOT NULL,
    landingPads_small INTEGER NOT NULL,
    landingPads_medium INTEGER NOT NULL,
    landingPads_large INTEGER NOT NULL,
    market_updateTime TEXT,
    shipyard_updateTime TEXT,
    outfitting_updateTime TEXT,
    FOREIGN KEY (systemId) REFERENCES systems (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS stations_coords_idx
    ON public.stations USING hnsw
    (coords vector_l2_ops);

CREATE INDEX IF NOT EXISTS type_idx
    ON public.stations USING btree
    (type COLLATE pg_catalog."default" ASC NULLS LAST)
    WITH (deduplicate_items=True);
    
CREATE TABLE IF NOT EXISTS stations_services (
    stationId BIGINT NOT NULL,
    service TEXT NOT NULL,
    PRIMARY KEY (stationId, service),
    FOREIGN KEY (stationId) REFERENCES stations (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS stations_economies (
    stationId BIGINT NOT NULL,
    economy TEXT NOT NULL,
    proportion REAL NOT NULL,
    PRIMARY KEY (stationId, economy),
    FOREIGN KEY (stationId) REFERENCES stations (id) ON DELETE CASCADE
);
"""


class Body(TypedDict):
    id64: int
    bodyId: int
    systemId: int
    name: str
    systemName: str
    coords: Coords
    type: str
    subType: str
    distanceToArrival: float
    mainStar: bool
    age: int
    spectralClass: str
    luminosity: str
    absoluteMagnitude: float
    solarMasses: float
    solarRadius: float
    surfaceTemperature: float
    rotationalPeriod: float
    rotationalPeriodTidallyLocked: bool
    axialTilt: float
    parents: list
    orbitalPeriod: float
    semiMajorAxis: float
    orbitalEccentricity: float
    orbitalInclination: float
    argOfPeriapsis: float
    meanAnomaly: float
    ascendingNode: float
    timestamps: dict
    updateTime: str
    station_ids: list[int]


create_bodies_table = """
CREATE TABLE IF NOT EXISTS bodies (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    systemId BIGINT NOT NULL,
    name TEXT NOT NULL,
    systemName TEXT NOT NULL,
    coords vector(3) NOT NULL,
    type TEXT NOT NULL,
    subType TEXT,
    distanceToArrival REAL NOT NULL,
    mainStar BOOLEAN NOT NULL,
    age INTEGER,
    spectralClass TEXT,
    luminosity TEXT,
    absoluteMagnitude REAL,
    solarMasses REAL,
    solarRadius REAL,
    surfaceTemperature REAL,
    rotationalPeriod REAL,
    rotationalPeriodTidallyLocked BOOLEAN,
    axialTilt REAL,
    parents JSON,
    orbitalPeriod REAL,
    semiMajorAxis REAL,
    orbitalEccentricity REAL,
    orbitalInclination REAL,
    argOfPeriapsis REAL,
    meanAnomaly REAL,
    ascendingNode REAL,
    timestamps JSON NOT NULL,
    updateTime TEXT NOT NULL,
    FOREIGN KEY (systemId) REFERENCES systems (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS bodies_coords_idx
    ON public.bodies USING hnsw
    (coords vector_l2_ops);
"""


class SystemFaction(TypedDict):
    name: str
    allegiance: str
    government: str
    influence: float
    state: str


create_systems_factions_table = """
CREATE TABLE IF NOT EXISTS systems_factions (
    systemId BIGINT NOT NULL,
    name TEXT NOT NULL,
    allegiance TEXT NOT NULL,
    government TEXT NOT NULL,
    influence REAL NOT NULL,
    state TEXT NOT NULL,
    PRIMARY KEY (systemId, name),
    FOREIGN KEY (systemId) REFERENCES systems (id) ON DELETE CASCADE
);
"""


class System(TypedDict):
    _id: int
    id64: int
    name: str
    coords: Coords
    # allegiance: str
    # government: str
    primaryEconomy: str
    secondaryEconomy: str
    security: str
    population: int
    bodyCount: int
    controllingFaction: SystemFaction
    factions: list[SystemFaction]
    controllingPower: str
    powers: list[str]
    powerState: str
    timestamps: dict[str, str]
    date: str
    station_ids: list[int]
    body_ids: list[int]


create_systems_table = """
CREATE TABLE IF NOT EXISTS systems (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    coords vector(3) NOT NULL,
    controllingPower TEXT,
    power_state TEXT,
    -- allegiance TEXT, -- redundant with controllingFaction_allegiance
    -- government TEXT, -- redundant with controllingFaction_government
    primaryEconomy TEXT,
    secondaryEconomy TEXT,
    security TEXT,
    population BIGINT NOT NULL,
    bodyCount INTEGER NOT NULL,
    controllingFaction TEXT,
    -- controllingFaction_allegiance TEXT, -- redundant with systems_factions by controllingFaction_name
    -- controllingFaction_government TEXT, -- redundant with systems_factions by controllingFaction_name
    -- controllingFaction_influence REAL, -- redundant with systems_factions by controllingFaction_name
    -- controllingFaction_state TEXT, -- redundant with systems_factions by controllingFaction_name
    -- date TEXT,
    timestamps JSON
);
CREATE INDEX IF NOT EXISTS systems_coords_idx
    ON public.systems USING hnsw
    (coords vector_l2_ops);
    
CREATE TABLE IF NOT EXISTS systems_powers (
    systemId BIGINT NOT NULL,
    power TEXT NOT NULL,
    PRIMARY KEY (systemId, power),
    FOREIGN KEY (systemId) REFERENCES systems (id) ON DELETE CASCADE
);
"""

pool = ConnectionPool(
    os.getenv(
        "DATABASE_URL",
        "dbname=edsearch user=postgres password=password host=localhost",
    ),
    open=True,
)


def get_pg_connection():
    conn = pool.getconn()
    register_vector(conn)
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SET hnsw.ef_search = 100;")
    return conn, cur


# self closing get_pg_connection using with statement
class pg_connection(object):
    def __init__(self) -> None:
        self.conn: psycopg.Connection = (
            None  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.cur: psycopg.Cursor[DictRow] = (
            None  # pyright: ignore[reportAttributeAccessIssue]
        )
        pass

    def __enter__(self):
        self.conn = pool.getconn()
        register_vector(self.conn)
        self.cur = self.conn.cursor(row_factory=dict_row)
        self.cur.execute("SET hnsw.ef_search = 1000;")
        return self.conn, self.cur

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.commit()
        if pool and self.conn:
            pool.putconn(self.conn)  # pyright: ignore[reportArgumentType]
        self.conn = None  # pyright: ignore[reportAttributeAccessIssue]
        self.cur = None  # pyright: ignore[reportAttributeAccessIssue]
        return False


def create_tables():
    conn = psycopg.connect(
        os.getenv(
            "DATABASE_URL",
            "dbname=edsearch user=postgres password=password host=localhost",
        ),
    )
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)
    cur.execute(create_systems_table)  # pyright: ignore[reportArgumentType]
    cur.execute(create_systems_factions_table)  # pyright: ignore[reportArgumentType]
    cur.execute(create_bodies_table)  # pyright: ignore[reportArgumentType]
    cur.execute(create_stations_table)  # pyright: ignore[reportArgumentType]
    cur.execute(
        create_stations_market_commodities_table  # pyright: ignore[reportArgumentType]
    )
    cur.execute(
        create_stations_shipyard_ships_table  # pyright: ignore[reportArgumentType]
    )
    cur.execute(
        create_stations_outfitting_modules_table  # pyright: ignore[reportArgumentType]
    )
    conn.commit()
    cur.close()
    conn.close()


def station_to_tables(station: Station):
    return {
        "stations": [
            {
                "id": station["id"],
                "systemId": station["systemId"],
                "systemName": station["systemName"],
                "bodyId": station.get("bodyId"),
                "name": station["name"],
                "type": station.get("type", "Unknown"),
                "coords": np.array(
                    [
                        station["coords"]["x"],
                        station["coords"]["y"],
                        station["coords"]["z"],
                    ]
                ),
                "updateTime": station["updateTime"],
                "controllingFaction": station.get("controllingFaction"),
                # "controllingFactionState": station.get("controllingFactionState"),
                "distanceToArrival": station.get("distanceToArrival", 0),
                "primaryEconomy": station.get("primaryEconomy"),
                # "government": station.get("government"),
                "landingPads_small": station["landingPads"]["small"],
                "landingPads_medium": station["landingPads"]["medium"],
                "landingPads_large": station["landingPads"]["large"],
                "market_updateTime": (
                    station["market"]["updateTime"] if "market" in station else None
                ),
                "shipyard_updateTime": (
                    station["shipyard"]["updateTime"] if "shipyard" in station else None
                ),
                "outfitting_updateTime": (
                    station["outfitting"]["updateTime"]
                    if "outfitting" in station
                    else None
                ),
            }
        ],
        "stations_services": (
            [
                {"stationId": station["id"], "service": service}
                for service in station["services"]
            ]
            if "services" in station
            else []
        ),
        "stations_economies": (
            [
                {
                    "stationId": station["id"],
                    "economy": economy,
                    "proportion": proportion,
                }
                for economy, proportion in station["economies"].items()
            ]
            if "economies" in station
            else []
        ),
        "stations_market_commodities": (
            [
                {
                    "stationId": station["id"],
                    "name": commodity["name"],
                    "symbol": commodity["symbol"],
                    "category": commodity["category"],
                    "commodityId": commodity["commodityId"],
                    "demand": commodity["demand"],
                    "supply": commodity["supply"],
                    "buyPrice": commodity["buyPrice"],
                    "sellPrice": commodity["sellPrice"],
                }
                for commodity in station["market"]["commodities"]
            ]
            if "market" in station
            else []
        ),
        "stations_shipyard_ships": (
            [
                {
                    "stationId": station["id"],
                    "name": ship["name"],
                    "symbol": ship["symbol"],
                    "shipId": ship["shipId"],
                }
                for ship in station["shipyard"]["ships"]
            ]
            if "shipyard" in station
            else []
        ),
        "stations_outfitting_modules": (
            [
                {
                    "stationId": station["id"],
                    "name": module["name"],
                    "symbol": module["symbol"],
                    "moduleId": module["moduleId"],
                    "class": module[
                        "class"
                    ],  # pyright: ignore[reportGeneralTypeIssues]
                    "rating": module["rating"],
                    "category": module["category"],
                }
                for module in station["outfitting"]["modules"]
            ]
            if "outfitting" in station
            else []
        ),
    }


def body_to_tables(body: Body):
    return {
        "bodies": [
            {
                "id": body["id64"],
                "systemId": body["systemId"],
                "name": body["name"],
                "systemName": body["systemName"],
                "coords": np.array(
                    [body["coords"]["x"], body["coords"]["y"], body["coords"]["z"]]
                ),
                "type": body["type"],
                "subType": body.get("subType"),
                "distanceToArrival": body.get("distanceToArrival", 0),
                "mainStar": body.get("mainStar", False),
                "age": body.get("age"),
                "spectralClass": body.get("spectralClass"),
                "luminosity": body.get("luminosity"),
                "absoluteMagnitude": body.get("absoluteMagnitude"),
                "solarMasses": body.get("solarMasses"),
                "solarRadius": body.get("solarRadius"),
                "surfaceTemperature": body.get("surfaceTemperature"),
                "rotationalPeriod": body.get("rotationalPeriod"),
                "rotationalPeriodTidallyLocked": body.get(
                    "rotationalPeriodTidallyLocked"
                ),
                "axialTilt": body.get("axialTilt"),
                "parents": json.dumps(body.get("parents", [])),
                "orbitalPeriod": body.get("orbitalPeriod"),
                "semiMajorAxis": body.get("semiMajorAxis"),
                "orbitalEccentricity": body.get("orbitalEccentricity"),
                "orbitalInclination": body.get("orbitalInclination"),
                "argOfPeriapsis": body.get("argOfPeriapsis"),
                "meanAnomaly": body.get("meanAnomaly"),
                "ascendingNode": body.get("ascendingNode"),
                "timestamps": json.dumps(body.get("timestamps", {})),
                "updateTime": body["updateTime"],
            }
        ]
    }


def system_to_tables(system: System):
    return {
        "systems": [
            {
                "id": system["id64"],
                "name": system["name"],
                "coords": np.array(
                    [
                        system["coords"]["x"],
                        system["coords"]["y"],
                        system["coords"]["z"],
                    ]
                ),
                # "allegiance": system.get("allegiance"),
                # "government": system.get("government"),
                "primaryEconomy": system.get("primaryEconomy"),
                "secondaryEconomy": system.get("secondaryEconomy"),
                "security": system.get("security"),
                "population": system.get("population", 0),
                "bodyCount": system.get("bodyCount", 0),
                "controllingFaction": system.get("controllingFaction", {}).get("name"),
                # "controllingFaction_allegiance": system.get("controllingFaction").get("allegiance"),
                # "controllingFaction_government": system.get("controllingFaction").get("government"),
                # "controllingFaction_influence": system.get("controllingFaction",{}).get("influence"),
                # "controllingFaction_state": system.get("controllingFaction").get("state"),
                "controllingPower": system.get("controllingPower"),
                "power_state": system.get("powerState"),
                "timestamps": json.dumps(system.get("timestamps", {})),
                # "date": system["date"] # TODO find value
            }
        ],
        "systems_factions": [
            {
                "systemId": system["id64"],
                "name": faction["name"],
                "allegiance": faction["allegiance"],
                "government": faction["government"],
                "influence": faction["influence"],
                "state": faction["state"],
            }
            for faction in system.get("factions", [])
        ],
    }
