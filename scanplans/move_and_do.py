"""Conduct the plans for the samples one by one."""
import typing as tp

import bluesky.plan_stubs as bps
from xpdacq.beamtime import Beamtime
from xpdacq.beamtime import xpd_configuration

from scanplans.mdgetters import get_from_sample
from scanplans.mdgetters import translate_to_plan, translate_to_sample


def move_and_do_many(
        bt: Beamtime,
        sps: tp.List[tp.Tuple[tp.Union[int, str], tp.Union[int, str, tp.Generator]]],
        wait_times: tp.Union[float, tp.List[float]] = 0.,
        wait_at_first: bool = False,
        sample_x: str = "sample_x", sample_y: str = "sample_y",
        x_controller: str = "x_controller",
        y_controller: str = "y_controller",
) -> tp.List[tp.Generator]:
    """Move to the sample and conduct the bluesky plan on the sample one by one.

    Parameters
    ----------
    bt : Beamtime
        The beamtime object.

    sps : list
        A list of (sample index, plan index). The index is shown in the 'bt.list()'.

    wait_times : float or list of float
        The wait time for all the samples.

    wait_at_first : bool
        Whether to wait before the plan is conducted for the first samples. If False, the plan will be conducted
        immediately to the first sample no matter how wait_time is set.

    sample_x : str
        The key to the x position of the sample in the sample information. Default 'sample_y'.

    sample_y : str
        The key to the y position of the sample in the sample information. Default 'sample_x'.

    x_controller : str
        The key to the x position controller in `~xpdacq.beamtime.xqd_configuration`.

    y_controller : str
        The key to the x position controller in `~xpdacq.beamtime.xqd_configuration`.

    Returns
    -------
    plans : list
        A list of the bluesky plans. Each plan is a generator.
    """
    if isinstance(wait_times, (int, float)):
        wait_times = [wait_times] * len(sps)
    else:
        wait_times = wait_times[:]
    if not wait_at_first:
        wait_times[0] = 0
    return [
        move_and_do_one(
            bt, s, p,
            wait_time=wt,
            sample_x=sample_x, sample_y=sample_y,
            x_controller=x_controller, y_controller=y_controller,
        )
        for (s, p), wt in zip(sps, wait_times)
    ]


def move_and_do_one(
        bt: Beamtime, sample_ind: tp.Union[int, str], plan_ind: tp.Union[int, str, tp.Generator],
        wait_time: float = 0., sample_x: str = "sample_x",
        sample_y: str = "sample_y", x_controller: str = "x_controller", y_controller: str =
        "y_controller"
) -> tp.Generator:
    """Move to the sample and conduct the plan."""
    sample = translate_to_sample(bt, sample_ind)
    plan = translate_to_plan(bt, plan_ind, sample)
    xc = xpd_configuration[x_controller]
    yc = xpd_configuration[y_controller]
    x = float(get_from_sample(sample, sample_x))
    y = float(get_from_sample(sample, sample_y))
    yield from bps.checkpoint()
    print("Start moving to sample {} at ({}, {}).".format(sample_ind, x, y))
    yield from bps.mv(xc, x, yc, y)
    print("Finish. ")
    yield from bps.checkpoint()
    print("Start sleeping for {} s.".format(wait_time))
    yield from bps.sleep(wait_time)
    print("Wake up.")
    yield from bps.checkpoint()
    print("Start plan {} for sample {}".format(plan_ind, sample_ind))
    yield from plan
    print("Finish.")
