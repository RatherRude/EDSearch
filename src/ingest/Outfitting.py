from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.outfitting import Outfitting, OutfittingItem
from ..models.eddn.Outfitting import Outfitting as EDDNOutfitting
from ..models.db.ingestion import DatabaseModels

def convert_outfitting(outfitting_event: EDDNOutfitting, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    items: list[OutfittingItem] = []
    if outfitting_event.modules:
        for module_name in outfitting_event.modules:
            items.append(OutfittingItem(
                marketId=outfitting_event.marketId,
                name=module_name,
            ))
    outfitting = Outfitting(
        timestamp=outfitting_event.timestamp,
        marketId=outfitting_event.marketId,
        numItems=len(items),
        items=items
    )
    dbModels.outfittings.append(outfitting)
    return dbModels
