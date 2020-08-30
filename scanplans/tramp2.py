"""An advanced temperature ramping plan."""
import bluesky.plan_stubs as bps
from ophyd.sim import SynAxis
from xpdacq.beamtime import Tramp
from xpdacq.xpdacq import xpd_configuration

__all__ = [
    "Tramp2"
]


def Tramp2(dets: list, exposure: float, Tstart: float, Tstop: float, Tstep: float, *, ramp_rate: float = None):
    """A temperature ramping plan with ramping rate configuration.

    The ramping rate will be configured before the ramping start. The ramping will be done continuously
    without holding temperature at exposure.

    Parameters
    ----------
    dets : list
        A list of detectors. Dummy. Not used.

    exposure : float
        The exposure time in second.

    Tstart : float
        The start temperature in K (included).

    Tstop : float
        The stop temperature in K (incldued)

    Tstep : float
        The temperature step in K.

    ramp_rate : float
        The temperature ramping rate. Make sure the temperature controller has the `velocity` configuration.

    Yields
    ------
    Bluesky plan.
    """
    temp_controller: SynAxis = xpd_configuration["temp_controller"]
    if ramp_rate is not None:
        yield from bps.configure(temp_controller, {"velocity": ramp_rate})
    yield from Tramp(dets, exposure, Tstart, Tstop, Tstep)
