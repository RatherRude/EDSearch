from ..models.db.signals import Signal
from ..models.eddn.SAASignalsFound import SAASignalsFound

from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.ingestion import DatabaseModels


def convert_saa_signals_found(saa: SAASignalsFound, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert an SAA Signals Found event to a Station model or a landmark."""
    dbModels = DatabaseModels()

    for signal in saa.Signals:
        dbModels.signals.append(Signal(
            BodyID=saa.BodyID,
            SystemAddress=saa.SystemAddress,
            Type=signal.Type,
            Count=signal.Count,
            SignalName=None,
        ))
    for genus in saa.Genuses:
        dbModels.signals.append(Signal(
            BodyID=saa.BodyID,
            SystemAddress=saa.SystemAddress,
            Type=genus.Genus,
            Count=1,
            SignalName=None,
        ))

    return dbModels
