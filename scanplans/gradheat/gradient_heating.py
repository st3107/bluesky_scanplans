import time
import uuid
import numpy as np
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.callbacks import LiveTable

from xpdacq.beamtime import (
    close_shutter_stub,
    open_shutter_stub,
    _check_mini_expo
)
from xpdacq.xpdacq_conf import xpd_configuration
from xpdacq.glbl import glbl


def configure_area_det_expo(exposure):
    det = xpd_configuration["area_det"]
    yield from bps.abs_set(
        det.cam.acquire_time, glbl["frame_acq_time"], wait=True
    )
    acq_time = det.cam.acquire_time.get()
    _check_mini_expo(exposure, acq_time)
    # compute number of frames
    num_frame = np.ceil(exposure / acq_time)
    yield from bps.abs_set(det.images_per_set, num_frame, wait=True)
    computed_exposure = num_frame * acq_time
    # print exposure time
    print(
        "INFO: requested exposure time = {} - > computed exposure time"
        "= {}".format(exposure, computed_exposure)
    )
    return num_frame, acq_time, computed_exposure


def gradient_heating_plan(dets, expo_time, calib_map,
                          x_motor, x_pos_interval,
                          y_motor, y_pos_interval,
                          num_pos,
                          num_loops=1):
    """
    gradient heating scan; setting calibration info at each location

    The x/y-movement is used to compensate the small tilting of the
    sample (so that beam will hit the center of capillary). If it
    is not needed, please pass argument `x_pos_interval` or
    `y_post_interval` as 0 and the scan will only go through one
    dimension.

    Example:
    --------
    gradient heating scan over 15 points along sample,
    with 1 unit (depends on motor) between points for 2 loops;
    exposure time = 5s for each point and recording

       1. area detector image

       2. x- and y-motor position

       3. thermal coupler readback
    at each position

    Example syntax of this scan plan
    >>> plan = gradient_heating_plan([pe1c, eurotherm],
                                     5, {},
                                     ss_stg_x, 1.25, 
                                     ss_stg_y, 1.75,
                                     17, 1
                                     )
    >>> xrun(<sample_ind>, plan)
    """
    _dets = list(dets) + [x_motor, y_motor]
    print("This scan will collect data with interval = {} along"
          " x-direction and interval = {} along y-direction"
          " with total {} points".format(x_pos_interval,
                                         y_pos_interval,
                                         num_pos)
          )
    rv = yield from configure_area_det_expo(expo_time)
    num_frame, acq_time, computed_exposure = rv
    # scan md
    _md = {"sp_time_per_frame": acq_time,
           "sp_num_frames": num_frame,
           "sp_requested_exposure": expo_time,
           "sp_computed_exposure": computed_exposure,
           "sp_type": "gradient_heating",
           "sp_plan_name": "gradient_heating",
           "sp_uid": str(uuid.uuid4()),
           }
    # motor hints
    x_fields = []
    for motor in (x_motor, y_motor):
        x_fields.extend(getattr(motor, 'hints', {}).get('fields', []))
    default_dimensions = [(x_fields, 'primary')]
    default_hints = {}
    if len(x_fields) > 0:
        default_hints.update(dimensions=default_dimensions)
    _md['hints'] = default_hints

    if calib_map is None:
        print('WARNING: no calib info is found')
        print("Ignore if this is a calibration run")
    print("INFO: this plan is going to be run {} times".format(num_loops))
    # FIXME: check this at beamline
    x_pos_0 = x_motor.position
    y_pos_0 = y_motor.position
    for i in range(num_loops):
        for j in range(num_pos):
            yield from bps.mvr(x_motor, x_pos_interval,
                               y_motor, y_pos_interval)
            yield from bps.checkpoint()  # check point for revert
            calib_md = calib_map.get(j, None)
            if calib_md:
                _md["calibration_md"] = calib_md
            elif not calib_md and calib_map:
                e = "No calibration info at {}-th position".format(j)
                raise RuntimeError(e)
            plan = bp.count(_dets, num=1, md=_md)
            plan = bpp.subs_wrapper(plan, LiveTable(_dets))
            yield from plan
        yield from bps.mv(x_motor, x_pos_0,
                          y_motor, y_pos_0)  # move back to origin
        yield from bps.checkpoint()
    print("END of gradient heating scan")
