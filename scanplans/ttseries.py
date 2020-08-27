"""The function for Rohan's insitu measurement."""
import uuid

from bluesky.callbacks import LiveTable
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.preprocessors import subs_wrapper, plan_mutator
from xpdacq.xpdacq_conf import xpd_configuration

import scanplans.tools as tl

__all__ = ["ttseries"]


def ttseries(dets, temp_setpoint, exposure, delay, num, auto_shutter=True, manual_set=False):
    """
    Set a target temperature. Make time series scan with area detector during the ramping and holding. Since
    abs_set is used, please do not set the temperature through CSstudio when the plan is running.

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to area detector
        linked to xpdAcq.
    temp_setpoint: float
        A temperature set point. If None, do not set the temperature.
    exposure : float
        The exposure time at each reading from area detector in seconds
    delay : float
        The period of time between the starting points of two consecutive readings from area detector in seconds
    num : int
        The total number of readings
    auto_shutter: bool
        Option on whether delegates shutter control to ``xpdAcq``. If True,
        following behavior will take place:

        `` open shutter - collect data - close shutter ``

        To make shutter stay open during ``tseries`` scan,
        pass ``False`` to this argument. See ``Notes`` below for more
        detailed information.
    manual_set : bool
        Option on whether to manual set the temperature set point outside the plan. If True, no temperature
        will be set in plan.

    Examples
    --------
    To see which area detector and shutter will be used, type the
    following commands:

        >>> xpd_configuration['area_det']
        >>> xpd_configuration['shutter']
        >>> xpd_configuration['temp_controller']

    To override default behavior and keep the shutter open throughout
    scan, create ScanPlan with following syntax:

        >>> ScanPlan(bt, ttseries, 300, 10, 20, 10, False)
    """
    area_det = xpd_configuration["area_det"]
    temp_controller = xpd_configuration["temp_controller"]
    md = {
        "sp_type": "ttseries",
        "sp_uid": str(uuid.uuid4()),
        "sp_plan_name": "ttseries",
        "temp_setpoint": temp_setpoint
    }
    # calculate number of frames
    exposure_md = tl.calc_exposure(area_det, exposure)
    md.update(exposure_md)
    # calculate the real delay and period
    computed_exposure = exposure_md.get("sp_computed_exposure")
    delay_md = tl.calc_delay(delay, computed_exposure, num)
    md.update(delay_md)
    # make the count plan
    real_delay = delay_md.get('sp_computed_delay')
    plan = count([area_det, temp_controller], num, real_delay, md=md)
    plan = subs_wrapper(plan, LiveTable([temp_controller]))
    # open and close the shutter for each count
    if auto_shutter:
        plan = plan_mutator(plan, tl.inner_shutter_control)
    # yield messages
    yield from tl.configure_area_det(area_det, md)
    if not manual_set:
        yield from abs_set(temp_controller, temp_setpoint, wait=False)
    yield from plan
