from ..models.db.signals import Signal
from ..models.eddn.FSSBodySignals import FSSBodySignals

from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.ingestion import DatabaseModels


def convert_fss_body_signals(fss: FSSBodySignals, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert an FSS Body Signals event to a Station model or a landmark."""
    dbModels = DatabaseModels()

    for signal in fss.Signals:
        dbModels.signals.append(Signal(
            BodyID=fss.BodyID,
            SystemAddress=fss.SystemAddress,
            Type=signal.Type,
            Count=signal.Count,
            SignalName=None
        ))

    return dbModels
