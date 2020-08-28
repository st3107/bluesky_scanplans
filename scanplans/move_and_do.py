"""Conduct the plans for the samples one by one."""
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.beamtime import Beamtime
from xpdacq.beamtime import xpd_configuration
from scanplans.mdgetters import translate_to_plan, translate_to_sample
from scanplans.mdgetters import get_from_sample
import typing as tp
import bluesky.plan_stubs as bps


def move_and_do_many(
        bt: Beamtime, sps: tp.List[tp.Tuple[int, int]], wait_times: tp.Union[float, tp.List[float]] = 0.,
        wait_at_first: bool = False,
        sample_x: str = "sample_x", sample_y: str = "sample_y",
        x_controller: str = "x_controller",
        y_controller: str = "y_controller",
) -> tp.List[tp.Generator]:
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
        bt: Beamtime, sample_ind: int, plan_ind: int, wait_time: float = 0., sample_x: str = "sample_x",
        sample_y: str = "sample_y", x_controller: str = "x_controller", y_controller: str =
        "y_controller"
) -> tp.Generator:
    sample = translate_to_sample(bt, sample_ind)
    plan = translate_to_plan(bt, plan_ind, sample)
    xc = xpd_configuration[x_controller]
    yc = xpd_configuration[y_controller]
    x = get_from_sample(sample, sample_x)
    y = get_from_sample(sample, sample_y)
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
