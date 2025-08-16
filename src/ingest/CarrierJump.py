from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.station import Station
from ..models.eddn.CarrierJump import CarrierJump
from ..models.db.ingestion import DatabaseModels


def convert_carrier_jump(carrier_jump: CarrierJump, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert a CarrierJump event to a Station model."""
    # TODO this can be used for system and body updates as well
    dbModels = DatabaseModels()

    station = Station(
        SystemAddress=carrier_jump.SystemAddress,
        MarketID=carrier_jump.MarketID,
        StationName=carrier_jump.StationName,
        StationType=carrier_jump.StationType,
        BodyID=None,
        Latitude=None,
        Longitude=None,
        DistFromStarLS=None,
        StationGovernment=None,
        StationAllegiance=None,
        numStationEconomies=None,
        StationEconomies=[],
        StationFactionName=None,
        StationFactionState=None,
        numStationServices=None,
        StationServices=[],
        StationEconomy=None,
        StationState=None,
        LandingPadsLarge=None,
        LandingPadsMedium=None,
        LandingPadsSmall=None
    )
    dbModels.stations.append(station)

    return dbModels
