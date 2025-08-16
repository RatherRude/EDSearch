from pydantic import BaseModel
from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.market import Market, MarketCommodity
from ..models.eddn.Market import Market as EDDNMarket
from ..models.db.ingestion import DatabaseModels

def convert_market(market_event: EDDNMarket, envelope: EDDNEnvelope) -> DatabaseModels:
    dbModels = DatabaseModels()
    commodities: list[MarketCommodity] = []
    if market_event.commodities:
        for c in market_event.commodities:
            commodities.append(MarketCommodity(
                marketId=market_event.marketId,
                name=c.name,
                category=c.category,
                stock=c.stock,
                demand=c.demand,
                supply=c.supply,
                buyPrice=c.buyPrice,
                sellPrice=c.sellPrice
            ))
    market = Market(
        timestamp=market_event.timestamp,
        marketId=market_event.marketId,
        commodities=commodities
    )
    dbModels.markets.append(market)
    return dbModels
