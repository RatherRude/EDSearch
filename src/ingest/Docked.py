from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.station import Station, StationEconomy
from ..models.eddn.Docked import Docked
from ..models.db.ingestion import DatabaseModels


def convert_docked(docked: Docked, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert a Docked event to a Station model."""
    dbModels = DatabaseModels()
    
    station_economies: list[StationEconomy] = []
    if docked.StationEconomies:
        for economy in docked.StationEconomies:
            station_economies.append(StationEconomy(
                Name=economy.Name,
                Proportion=economy.Proportion
            ))

    station = Station(
        SystemAddress=docked.SystemAddress,
        MarketID=docked.MarketID,
        StationName=docked.StationName,
        StationType=docked.StationType,
        BodyID=None,  # Docked does not have BodyID
        Latitude=None,  # Docked does not have Latitude
        Longitude=None,  # Docked does not have Longitude
        DistFromStarLS=docked.DistFromStarLS,
        StationGovernment=docked.StationGovernment,
        StationAllegiance=docked.StationAllegiance,
        numStationEconomies=len(station_economies) if station_economies else None,
        StationEconomies=station_economies,
        StationFactionName=docked.StationFaction.Name if docked.StationFaction else None,
        StationFactionState=docked.StationFaction.FactionState if docked.StationFaction else None,
        numStationServices=len(docked.StationServices) if docked.StationServices else None,
        StationServices=docked.StationServices,
        StationEconomy=docked.StationEconomy,
        StationState=docked.StationState,
        LandingPadsLarge=docked.LandingPads.Large if docked.LandingPads else None,
        LandingPadsMedium=docked.LandingPads.Medium if docked.LandingPads else None,
        LandingPadsSmall=docked.LandingPads.Small if docked.LandingPads else None
    )
    dbModels.stations.append(station)

    return dbModels
