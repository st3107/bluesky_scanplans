import bluesky.plan_stubs as bps
import bluesky.plans as bp
from xpdacq.beamtime import _configure_area_det
from xpdacq.glbl import glbl
from xpdacq.xpdacq import open_shutter_stub, close_shutter_stub
from xpdacq.xpdacq_conf import xpd_configuration


def acq_rel_grid_scan(
    dets: list,
    exposure: float,
    wait: float,
    start0: float, stop0: float, num0: int,
    start1: float, stop1: float, num1: int
):
    """Make a plan of two dimensional grid scan."""
    area_det = xpd_configuration["area_det"]
    x_controller = xpd_configuration["x_controller"]
    y_controller = xpd_configuration["y_controller"]

    def per_step(detectors, step: dict, pos_cache):
        """ customized step to ensure shutter is open before
        reading at each motor point and close shutter after reading
        """
        yield from bps.checkpoint()
        for motor, pos in step.items():
            yield from bps.mv(motor, pos)
        yield from bps.sleep(wait)
        yield from open_shutter_stub()
        yield from bps.sleep(glbl["shutter_sleep"])
        yield from bps.trigger_and_read(list(detectors) + list(step.keys()))
        yield from close_shutter_stub()

    plan = bp.rel_grid_scan(
        [area_det],
        x_controller, start0, stop0, num0,
        y_controller, start1, stop1, num1,
        snake_axes=True,
        per_step=per_step
    )
    yield from _configure_area_det(exposure)
    yield from plan

# below is the code to run at the beamtime
# register the scanplan
# ScanPlan(bt, acq_rel_grid_scan, 60, 30, -5, 5, 10, -5, 5, 10)
# use bt.list() to see the index of the scanplan and use it in xrun
