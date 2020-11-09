"""A temperature ramping with waiting."""
import bluesky.plan_stubs as bps
import bluesky.plans as bp
from xpdacq.beamtime import open_shutter_stub, close_shutter_stub, _nstep
from xpdacq.glbl import glbl
from xpdacq.xpdacq_conf import xpd_configuration


def Tramp3(dets: list, wait: float, exposure: float, Tstart: float, Tstop: float, Tstep: float):
    """
    Collect data over a range of temperatures

    This plan sets the sample temperature using a temp_controller device
    and exposes a detector for a set time at each temperature.
    It also has logic for equilibrating the temperature before each
    acquisition. By default it closes the fast shutter at XPD in between
    exposures. This behavior may be overridden, leaving the fast shutter
    open for the entire scan. Please see below.

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to the temperature
        controller and area detector linked to xpdAcq.

    wait : float
        Time to wait at each temperature point.

    exposure : float
        exposure time at each temperature step in seconds.

    Tstart : float
        starting point of temperature sequence.

    Tstop : float
        stoping point of temperature sequence.

    Tstep : float
        step size between Tstart and Tstop of this sequence.

    Notes
    -----
    1. To see which area detector and temperature controller
    will be used, type the following commands:

        >>> xpd_configuration['area_det']
        >>> xpd_configuration['temp_controller']

    2. To change the default behavior to shutter-always-open,
    please pass the argument for ``per_step`` in the ``ScanPlan``
    definition, as follows:

        >>> ScanPlan(bt, Tramp, 10, 5, 300, 250, 10, per_step=None)

    This will create a ``Tramp`` ScanPlan, with shutter always
    open during the ramping.
    """
    area_det = xpd_configuration["area_det"]
    temp_controller = xpd_configuration["temp_controller"]
    Nsteps, _ = _nstep(Tstart, Tstop, Tstep)

    def per_step(detectors, motor, step):
        """ customized step to ensure shutter is open before
        reading at each motor point and close shutter after reading
        """
        yield from bps.checkpoint()
        yield from bps.abs_set(motor, step, wait=True)
        yield from bps.sleep(wait)
        yield from open_shutter_stub()
        yield from bps.sleep(glbl["shutter_sleep"])
        yield from bps.trigger_and_read(list(detectors) + [motor])
        yield from close_shutter_stub()

    plan = bp.scan(
        [area_det],
        temp_controller,
        Tstart,
        Tstop,
        Nsteps,
        per_step=per_step
    )
    yield from _configure_area_det(exposure)
    yield from plan
