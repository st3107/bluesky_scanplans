"""
This script contains the plan for cryostat measurement. How to use it:
(1) Download the script to userScript.
(2) Run the script in ipython interface.

    '%run userScript/cryostat.py'

(3) Instantiate a python generator as the plan. Here is an example where the beamtime object is 'bt',
the temperature controller is 'cryostat_T', the position controller is 'ss_stage_x' and the plan is to set
temperature to 295 K and 300 K and take a single shot for two samples at each temperature. The samples are
loaded at x-positions: 10 mm and 10.2 mm. Their corresponding index in bt is 1 and 2. The exposure time is 30 s
and 60 s respectively.

    'plan = cryostat_plan(bt, cryostat_T, [295, 300], ss_stage_x, [10, 10.2], [1, 2], [30, 60])'

(4) Let 'xrun' rxecute the plan.

    'xrun({}, plan)'

    We don't need to worry about the samples information because it will be added into metadata by this plan so
    the first positional argument of 'xrun' is given a empty dictionary. """
import uuid
from typing import List

from bluesky.callbacks import LiveTable
from bluesky.plan_stubs import mv, abs_set, checkpoint
from bluesky.plans import count
from bluesky.preprocessors import subs_wrapper
from xpdacq.beamtime import _configure_area_det
from xpdacq.xpdacq_conf import xpd_configuration

from scanplans.tools import translate_to_sample


def cryostat_plan(bt: object, temp_motor: object, temperatures: List[float], posi_motor: object,
                  positions: List[float],
                  samples: List[int], exposures: List[float], temp_to_power: dict = None):
    """
    The scanplan of cryostat measurement.

    Parameters
    -------
        bt : beamtime object
            The beamtime object.

        temp_motor : motor object
            The controller of temperature.

        temperatures : List[float]
            A list of temperature setpoints.

        posi_motor : motor object
            The controller of positions.

        positions : List[float]
            A list of positions.

        samples : List[int]
            A list of index of samples in bt.

        exposures : List[float]
            A list of exposure time.

        temp_to_power : dict
            A mapping from temperature range to power. The range is open at left and close at right. If None,
            default setting (see function 'get_heater_range') is used. Default None.

    Yields
    -------
        Message of the plan
    """
    samples = translate_to_sample(bt, samples)
    for temperature in temperatures:
        yield from set_power(temp_motor, temperature, temp_to_power)
        yield from checkpoint()
        yield from mv(temp_motor, temperature)
        yield from checkpoint()
        if not (len(positions) == len(samples) and len(samples) == len(exposures)):
            raise ValueError("Unmatched length of positions, samples and exposures: "
                             f"{len(positions)}, {len(samples)}, {len(exposures)}.")
        for position, sample, exposure in zip(positions, samples, exposures):
            yield from mv(posi_motor, position)
            yield from checkpoint()
            yield from config_det_and_count([temp_motor, posi_motor], sample, exposure)
            yield from checkpoint()


def set_power(temp_motor: object, temperature: float, temp_to_power: dict = None):
    """
    Set powder of heater according to the temperature.

    Parameters
    ----------
    temp_motor : object
        The controller of temperature.
    temperature : float
        The temperature setpoint.
    temp_to_power : dict
        A mapping from temperature range to power. The range is open at left and close at right. If None, default
        setting (see function 'get_heater_range') is used. Default None.

    Yields
    -------
        Message to set the heater range.

    """
    heater_value = get_heater_range(temperature, temp_to_power)
    if hasattr(temp_motor, 'heater_range'):
        yield from abs_set(temp_motor.heater_range, heater_value)
    else:
        raise AttributeError(f"The temp_motor {temp_motor.name} does not have attribute 'heater_range'.")


def get_heater_range(temperature: float, temp_to_power: dict = None):
    """
    Decide the heater range from the temperature.

    Parameters
    ----------
    temperature : float
        The temperature setpoint.
    temp_to_power : dict
        A mapping from temperature range to power. The range is open at left and close at right. If None, default
        setting (see function 'get_heater_range') is used. Default None.

    Returns
    -------
    heater_value
        The value of heater range. For cryostat, it is 1, 2, 3.

    """
    default_setting = {
        (0., 30.): 1,
        (30., 100.): 2,
        (100., float("inf")): 3
    }
    temp_to_power = temp_to_power if temp_to_power else default_setting
    for temp_range, heater_value in temp_to_power.items():
        if temp_range[0] < temperature <= temp_range[1]:
            return heater_value
    else:
        raise ValueError(f'Cannot find the heater range setting for the temperature {temperature} K.')


def config_det_and_count(motors: List[object], sample_md: dict, exposure: float):
    """
    Take one reading from area detector with given exposure time and motors. Save the motor reading results in
    the start document.

    Parameters
    ----------
    motors : List[float]
        A list of readable motors.
    sample_md
        The metadata of the sample.
    exposure
        The exposure time in seconds.

    Yields
    -------
        Message to configure the detector and run the scan.

    """
    # setting up area_detector
    _md = {}
    num_frame, acq_time, computed_exposure = yield from _configure_area_det(exposure)
    area_det = xpd_configuration["area_det"]
    # update md
    _md.update(**sample_md)
    plan_md = {
        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exposure,
        "sp_computed_exposure": computed_exposure,
        "sp_type": "cryostat",
        "sp_uid": str(uuid.uuid4()),
        "sp_plan_name": "cryostat"
    }
    _md.update(**plan_md)
    motor_md = {motor.name: dict(motor.read()) for motor in motors}
    _md.update(**motor_md)
    # yield plan
    dets = [area_det] + motors
    plan = count(dets, md=_md)
    plan = subs_wrapper(plan, LiveTable([]))
    yield from plan


if __name__ == "__main__":
    print(__doc__)
