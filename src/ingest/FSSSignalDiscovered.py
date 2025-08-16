from ..models.db.signals import Signal
from ..models.eddn.FSSSignalDiscovered import FSSSignalDiscovered

from ..models.eddn.EDDNEnvelope import EDDNEnvelope
from ..models.db.ingestion import DatabaseModels


def convert_fss_signal_discovered(fss: FSSSignalDiscovered, envelope: EDDNEnvelope) -> DatabaseModels:
    """Convert an FSS Signal Discovered event to a Station model or a landmark."""
    dbModels = DatabaseModels()

    for signal in fss.signals:
        if not signal.SignalType or signal.SignalType == 'FleetCarrier':
            continue
        
        dbModels.signals.append(Signal(
            SystemAddress=signal.SystemAddress or fss.SystemAddress,
            BodyID=None,
            Type=signal.SignalType,
            Count=1,
            SignalName=signal.SignalName
        ))

    return dbModels
