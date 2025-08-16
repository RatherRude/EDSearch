from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.shipyard import Shipyard, ShipyardShip
from ..models.eddn.Shipyard import Shipyard as EDDNShipyard
from ..models.db.ingestion import DatabaseModels

def convert_shipyard(shipyard_event: EDDNShipyard, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    if envelope.header.gameversion != 'CAPI-Live-shipyard':
        return dbModels
    ships: list[ShipyardShip] = []
    if shipyard_event.ships:
        for ship_name in shipyard_event.ships:
            ships.append(ShipyardShip(
                marketId=shipyard_event.marketId,
                name=ship_name,
            ))
    shipyard = Shipyard(
        timestamp=shipyard_event.timestamp,
        marketId=shipyard_event.marketId,
        numShips=len(ships),
        ships=ships
    )
    dbModels.shipyards.append(shipyard)
    return dbModels
