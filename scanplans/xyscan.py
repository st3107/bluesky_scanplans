"""A function to measure a series of samples automatically."""
from bluesky.plan_stubs import mv, sleep, checkpoint
from xpdacq.beamtime import xpd_configuration, Beamtime, Sample
from scanplans.mdgetters import *
from typing import List


def xyscan(bt, sample_index):
    """
    Yield messages to count the predefined measurement plan on the a list of samples on a sample rack. It requires
    the following information to be added for each sample.
        position_x The x position of the sample in mm.
        position_y The y position of the sample in mm.
        plan_ind The index of the plan in the Beamtime.
        wait_time The waiting time between the end of the former plan and the start of the latter plan in second.

    Parameters
    ----------
    bt: Beamtime
        The Beamtime instance that contains the sample information.
    sample_index : List[int]
        A list of sample index in the BeamTime instance.

    Yields
    ------
    Msg
        Messages of the plan.

    Examples
    --------
    Add position controller to the xpd_configuration.
        >>> xpd_configuration["posx_controller"] = Grid_X
        >>> xpd_configuration["posy_controller"] = Grid_Y
    Register the scan plan to the beamtime.
        >>> ScanPlan(bt, ct, 30)
    Add the information of 'position_x', 'position_y', 'plan_indice' and 'wait_time' to the excel and import.
    Automatically conduct the scan plan for sample No.0 and No.1
        >>> plan = xyscan(bt, [0, 1])
        >>> xrun({}, plan)
    """
    posx_controller = xpd_configuration["posx_controller"]
    posy_controller = xpd_configuration["posy_controller"]

    for sample_ind in sample_index:
        sample = translate_to_sample(bt, int(sample_ind))
        posx = get_from_sample(sample, "position_x")
        posy = get_from_sample(sample, "position_y")
        plan_ind = get_from_sample(sample, "plan_indice")
        wait_time = get_from_sample(sample, "wait_time")
        count_plan = translate_to_plan(bt, int(plan_ind), sample)
        if posx and posy and wait_time and count_plan:
            yield from checkpoint()
            yield from mv(posx_controller, float(posx))
            yield from checkpoint()
            yield from mv(posy_controller, float(posy))
            yield from checkpoint()
            yield from count_plan
            yield from checkpoint()
            yield from sleep(float(wait_time))
