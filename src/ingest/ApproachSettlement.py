from pydantic import BaseModel


from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.ingestion import DatabaseModels
from ..models.db.station import Station, StationEconomy
from ..models.eddn.ApproachSettlement import ApproachSettlement
from ..models.db.landmark import Landmark


def convert_approach_settlement(settlement: ApproachSettlement, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert an ApproachSettlement event to a Station model or a landmark."""
    dbModels = DatabaseModels()
    
    if settlement.MarketID:
        station_economies: list[StationEconomy] = []
        if settlement.StationEconomies:
            for economy in settlement.StationEconomies:
                station_economies.append(StationEconomy(
                    Name=economy.Name,
                    Proportion=economy.Proportion
                ))

        station = Station(
            SystemAddress=settlement.SystemAddress,
            MarketID=settlement.MarketID,
            StationName=settlement.Name,
            StationType='Settlement',
            BodyID=settlement.BodyID,
            Latitude=settlement.Latitude,
            Longitude=settlement.Longitude,
            DistFromStarLS=None,
            StationGovernment=settlement.StationGovernment,
            StationAllegiance=settlement.StationAllegiance,
            numStationEconomies=len(station_economies) if station_economies else None,
            StationEconomies=station_economies,
            StationFactionName=settlement.StationFaction.Name if settlement.StationFaction else None,
            StationFactionState=settlement.StationFaction.FactionState if settlement.StationFaction else None,
            numStationServices=len(settlement.StationServices) if settlement.StationServices else None,
            StationServices=settlement.StationServices,
            StationEconomy=settlement.StationEconomy,
            StationState=None,
            LandingPadsLarge=None,
            LandingPadsMedium=None,
            LandingPadsSmall=None
        )
        dbModels.stations.append(station)
    else:
        landmark = Landmark(
            SystemAddress=settlement.SystemAddress,
            EntryID=None,
            AuxiliaryID=','.join([str(settlement.SystemAddress), '-', str(settlement.BodyID), '-', str(settlement.Name)]),
            BodyID=settlement.BodyID,
            Latitude=settlement.Latitude,
            Longitude=settlement.Longitude,
            Name=settlement.Name,
            Region=None,
            Category=None,
            SubCategory=None,
            NearestDestination=None,
            VoucherAmount=None,
            numTraits=None,
            Traits=None
        )
        dbModels.landmarks.append(landmark)

    return dbModels
